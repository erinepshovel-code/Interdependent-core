"""
Canon Coherence Harness — single runner for all canon-vs-code/data tests.

Discovers tests, classifies results into three failure classes, emits one
JSON artifact, prints one terminal summary.

Failure classes (per pivot doc — golden drift is the primary freeze enforcer):
  CANON_VS_DATA  — canon rule disagrees with data file (e.g., collision priority
                   violations in bones_words_v1.json without carve-outs).
  CANON_VS_CODE  — canon formula disagrees with computed code output (e.g., R
                   golden mismatch).
  MISSING_CANON  — code or canon references a metric/rule with no canon entry
                   (e.g., D/L/O/I implementation gap, Progress/Basin without
                   canon counterpart).

Run from repo root:
    python tests/run_canon_coherence.py
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO / "tests"
CANON_DIR = REPO / "interdependent_lib/edcmbone/canon"
ARTIFACT_PATH = TESTS_DIR / "_artifacts/canon_coherence_report.json"

# Heuristic — class is inferred from test filename. Tests can override by
# embedding a "# CLASS: <name>" header comment on line 1-20.
CLASS_FROM_NAME = [
    (re.compile(r"collision|priority|carve", re.I),       "CANON_VS_DATA"),
    (re.compile(r"contraction|affix|placement", re.I),    "CANON_VS_DATA"),
    (re.compile(r"formula|metric_[a-z]|_golden", re.I),   "CANON_VS_CODE"),
    (re.compile(r"missing|gap|coverage", re.I),           "MISSING_CANON"),
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
        head = path.read_text(encoding="utf-8", errors="ignore")[:1024]
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
    return sorted(p for p in TESTS_DIR.rglob("test_*.py")
                  if "_artifacts" not in p.parts)


def discover_coverage_gaps() -> list[CoverageGap]:
    """Surface canon files that name metrics/rules with no test fixture."""
    gaps: list[CoverageGap] = []
    if not CANON_DIR.exists():
        return gaps
    declared: set[str] = set()
    for cf in CANON_DIR.rglob("*.json"):
        try:
            data = json.loads(cf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for key in ("metric_id", "rule_id"):
            if isinstance(data, dict) and key in data:
                declared.add(str(data[key]))
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict) and key in item:
                                declared.add(str(item[key]))
    fixture_text = ""
    fixtures_dir = TESTS_DIR / "fixtures"
    if fixtures_dir.exists():
        for fx in fixtures_dir.rglob("*.json"):
            try:
                fixture_text += fx.read_text(encoding="utf-8") + "\n"
            except OSError:
                pass
    test_text = "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                         for p in discover_tests())
    for ident in sorted(declared):
        if ident not in fixture_text and ident not in test_text:
            gaps.append(CoverageGap(
                metric_or_rule=ident, kind="MISSING_CANON",
                detail=f"declared in canon, no fixture or test references it",
            ))
    return gaps


def run_one(test_path: Path) -> TestResult:
    rel = test_path.relative_to(REPO).as_posix()
    cls = classify(test_path)
    start = time.time()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_path), "-q",
         "--no-header", "--tb=line"],
        cwd=REPO, capture_output=True, text=True, timeout=120,
    )
    duration = time.time() - start
    tail = (proc.stdout or "")[-800:].strip()
    passed = proc.returncode == 0
    skipped = "no tests ran" in (proc.stdout or "").lower()
    summary_line = next(
        (line for line in reversed((proc.stdout or "").splitlines())
         if line.strip()), "(no output)",
    )
    return TestResult(
        test_id=test_path.stem, path=rel, class_=cls,
        passed=passed, skipped=skipped,
        duration_s=round(duration, 3),
        summary=summary_line.strip(), stdout_tail=tail,
    )


def main() -> int:
    started = time.time()
    tests = discover_tests()
    results = [run_one(t) for t in tests]
    gaps = discover_coverage_gaps()

    by_class: dict[str, dict] = {}
    for r in results:
        b = by_class.setdefault(r.class_, {"total": 0, "passed": 0,
                                           "failed": 0, "skipped": 0})
        b["total"] += 1
        if r.skipped:
            b["skipped"] += 1
        elif r.passed:
            b["passed"] += 1
        else:
            b["failed"] += 1

    totals = {
        "tests_discovered": len(results),
        "passed":  sum(1 for r in results if r.passed and not r.skipped),
        "failed":  sum(1 for r in results if not r.passed and not r.skipped),
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
    ARTIFACT_PATH.write_text(json.dumps(asdict(report), indent=2) + "\n",
                             encoding="utf-8")

    # Terminal summary — boring on purpose, Termux-friendly
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
    for cls, b in sorted(by_class.items()):
        print(f"  {cls:16s} total={b['total']:3d} "
              f"passed={b['passed']:3d} failed={b['failed']:3d} "
              f"skipped={b['skipped']:3d}")
    if any(not r.passed and not r.skipped for r in results):
        print("-" * 60)
        print("Failures:")
        for r in results:
            if not r.passed and not r.skipped:
                print(f"  [{r.class_}] {r.test_id}  ({r.path})")
                print(f"    {r.summary}")
    if gaps:
        print("-" * 60)
        print("MISSING_CANON (declared, no fixture/test):")
        for g in gaps:
            print(f"  {g.metric_or_rule:20s}  {g.detail}")
    print("-" * 60)
    print(f"JSON artifact:    {ARTIFACT_PATH.relative_to(REPO)}")
    print("=" * 60)
    return 0 if totals["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
