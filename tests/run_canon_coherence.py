"""
Canon Coherence Harness — single runner for all canon-vs-code/data tests.

Discovers tests, classifies results into three failure classes, emits one JSON
artifact, and prints one terminal summary.

Failure classes:
  CANON_VS_DATA  — canon rule disagrees with data file.
  CANON_VS_CODE  — canon formula disagrees with computed code output.
  MISSING_CANON  — code/canon references a metric/rule with no fixture/test.

Run from repo root:
    python tests/run_canon_coherence.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO / "tests"
CANON_DIRS = [
    REPO / "interdependent_lib/edcm/data",
    REPO / "interdependent_lib/edcmbone/canon",
]
ARTIFACT_PATH = TESTS_DIR / "_artifacts/canon_coherence_report.json"

# Heuristic classifier. Tests can override by embedding a header comment:
#   # CLASS: CANON_VS_DATA
# on line 1-20.
CLASS_FROM_NAME = [
    (re.compile(r"collision|priority|carve", re.I), "CANON_VS_DATA"),
    (re.compile(r"contraction|affix|placement", re.I), "CANON_VS_DATA"),
    (re.compile(r"formula|metric_[a-z]|_golden", re.I), "CANON_VS_CODE"),
    (re.compile(r"missing|gap|coverage", re.I), "MISSING_CANON"),
]
DEFAULT_CLASS = "CANON_VS_CODE"


@dataclass
class TestResult:
    test_id: str
    path: str
    class_: str
    passed: bool
    skipped: bool
    duration_s: float
    summary: str
    stdout_tail: str = ""


@dataclass
class CoverageGap:
    metric_or_rule: str
    kind: str
    detail: str


@dataclass
class Report:
    started_at: str
    duration_s: float
    repo_root: str
    totals: dict
    by_class: dict
    results: list = field(default_factory=list)
    coverage_gaps: list = field(default_factory=list)


def classify(path: Path) -> str:
    try:
        head = "\n".join(path.read_text(encoding="utf-8", errors="ignore").splitlines()[:20])
    except OSError:
        head = ""
    m = re.search(r"#\s*CLASS\s*:\s*(\w+)", head)
    if m:
        return m.group(1).upper()
    name = path.name
    for rx, cls in CLASS_FROM_NAME:
        if rx.search(name):
            return cls
    return DEFAULT_CLASS


def discover_tests() -> list[Path]:
    return sorted(
        p
        for p in TESTS_DIR.rglob("test_*.py")
        if "_artifacts" not in p.parts
    )


def discover_coverage_gaps() -> list[CoverageGap]:
    """Surface canon-declared metrics/rules with no fixture or test reference."""
    gaps: list[CoverageGap] = []

    declared: set[str] = set()
    for canon_dir in CANON_DIRS:
        if not canon_dir.exists():
            continue
        for cf in canon_dir.rglob("*.json"):
            try:
                data = json.loads(cf.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(data, dict):
                for key in ("metric_id", "rule_id"):
                    if key in data:
                        declared.add(str(data[key]))
                for value in data.values():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                for key in ("metric_id", "rule_id"):
                                    if key in item:
                                        declared.add(str(item[key]))

    fixture_text = ""
    fixtures_dir = TESTS_DIR / "fixtures"
    if fixtures_dir.exists():
        for fx in fixtures_dir.rglob("*.json"):
            try:
                fixture_text += fx.read_text(encoding="utf-8") + "\n"
            except OSError:
                pass

    test_text_parts: list[str] = []
    for test_path in discover_tests():
        try:
            test_text_parts.append(test_path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    test_text = "\n".join(test_text_parts)

    for ident in sorted(declared):
        if ident not in fixture_text and ident not in test_text:
            gaps.append(
                CoverageGap(
                    metric_or_rule=ident,
                    kind="MISSING_CANON",
                    detail="declared in canon, no fixture or test references it",
                )
            )
    return gaps


def run_one(test_path: Path) -> TestResult:
    rel = test_path.relative_to(REPO).as_posix()
    cls = classify(test_path)
    start = time.time()
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(test_path),
            "-q",
            "--no-header",
            "--tb=line",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=120,
    )
    duration = time.time() - start
    combined = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    tail = combined[-800:]
    passed = proc.returncode == 0
    skipped = "no tests ran" in combined.lower()
    summary_line = next(
        (line for line in reversed(combined.splitlines()) if line.strip()),
        "(no output)",
    )
    return TestResult(
        test_id=test_path.stem,
        path=rel,
        class_=cls,
        passed=passed,
        skipped=skipped,
        duration_s=round(duration, 3),
        summary=summary_line.strip(),
        stdout_tail=tail,
    )


def main() -> int:
    started = time.time()
    tests = discover_tests()
    results = [run_one(t) for t in tests]
    gaps = discover_coverage_gaps()

    by_class: dict[str, dict] = {}
    for result in results:
        bucket = by_class.setdefault(
            result.class_,
            {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
        )
        bucket["total"] += 1
        if result.skipped:
            bucket["skipped"] += 1
        elif result.passed:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1

    totals = {
        "tests_discovered": len(results),
        "passed": sum(1 for r in results if r.passed and not r.skipped),
        "failed": sum(1 for r in results if not r.passed and not r.skipped),
        "skipped": sum(1 for r in results if r.skipped),
        "coverage_gaps": len(gaps),
    }

    report = Report(
        started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
        duration_s=round(time.time() - started, 3),
        repo_root=str(REPO),
        totals=totals,
        by_class=by_class,
        results=[asdict(r) for r in results],
        coverage_gaps=[asdict(g) for g in gaps],
    )
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(
        json.dumps(asdict(report), indent=2) + "\n",
        encoding="utf-8",
    )

    print("=" * 60)
    print("CANON COHERENCE REPORT")
    print("=" * 60)
    print(f"Discovered:       {totals['tests_discovered']} tests")
    print(f"Passed:           {totals['passed']}")
    print(f"Failed:           {totals['failed']}")
    print(f"Skipped:          {totals['skipped']}")
    print(f"Coverage gaps:    {totals['coverage_gaps']}")
    print(f"Duration:         {report.duration_s}s")
    print("-" * 60)
    print("By class:")
    for cls, bucket in sorted(by_class.items()):
        print(
            f"  {cls:16s} total={bucket['total']:3d} "
            f"passed={bucket['passed']:3d} failed={bucket['failed']:3d} "
            f"skipped={bucket['skipped']:3d}"
        )
    if any((not r.passed and not r.skipped) for r in results):
        print("-" * 60)
        print("Failures:")
        for result in results:
            if not result.passed and not result.skipped:
                print(f"  [{result.class_}] {result.test_id}  ({result.path})")
                print(f"    {result.summary}")
    if gaps:
        print("-" * 60)
        print("MISSING_CANON (declared, no fixture/test):")
        for gap in gaps:
            print(f"  {gap.metric_or_rule:20s}  {gap.detail}")
    print("-" * 60)
    print(f"JSON artifact:    {ARTIFACT_PATH.relative_to(REPO)}")
    print("=" * 60)
    return 0 if totals["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
