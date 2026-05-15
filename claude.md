# CLAUDE.md — interdependent-lib Buildability Fix

Claude generated; context and prompt Erin Spencer.

**Repo:** `erinepshovel-code/interdependent-lib`, branch `main`
**Author:** Erin Patrick Spencer / wayseer@interdependentway.org
**Date:** May 15, 2026

---

## Mission

Restore buildability of `interdependent-lib` so it installs cleanly via `pip install -e .`, imports without error, and passes its existing test suite. Four interlocking bugs gate buildability. Fix them as a single coherent batch.

Do not push to `wayseer00`. Do not modify canon. Do not resolve architectural questions about `edcm_metrics.py`. Those are author-held.

---

## Scope

### In scope

- `pyproject.toml` package include path correction
- PCEA module imports updated to new in-package locations
- Missing `pcea/__init__.py`
- Population of missing subpackages (pcna, pcta, edcmbone) into the unified `interdependent_lib/` directory
- Build + import + existing test verification

### Out of scope (do not touch)

- Canon JSON files (`bones_words_v1.json`, `bones_affixes_v1.json`, `bones_punct_v1.json`, `markers_v1.json`) — frozen
- The 15 collision priority violations — separate work item
- `edcm_metrics.py` architectural inversion (operator vs behavioral layer) — author decision pending
- Push to `wayseer00/interdependent-lib` — author manually authorizes the mirror
- `aimmh-lib` — separate PyPI package, not part of this work

### Stop gates

Before any of the following, halt and produce a report instead of proceeding:

- A canon JSON file appears to need modification to make a test pass
- A subpackage source isn't obviously available (no standalone repo, no loose files, ambiguous origin)
- A bug requires an architectural call rather than a mechanical fix
- Tests fail in ways that aren't import errors or path resolution

---

## The four bugs

1. **`pyproject.toml` include path** — currently `ptca*`, should be `interdependent_lib*`. The unified package's directory needs to match.
2. **PCEA imports** — files reference old `guardian_state` paths from when PCEA was standalone. Must be updated to the new in-package location.
3. **Missing `pcea/__init__.py`** — package can't expose PCEA without it.
4. **Missing subpackages** — pcna, pcta, edcmbone are not yet present in the unified repo. They must be brought in from their source repos or loose files.

These interlock: fixing #1 alone doesn't help if #4 isn't done; #2 produces import errors regardless; #3 means `from interdependent_lib import pcea` fails. Batch them.

---

## Fix order

Driven by the build system, not pre-specified. Start with:

```bash
python -m build
```

The first traceback tells you which bug surfaces first. The likely sequence:

### Step 1 — Subpackage population (bug #4)

Without source code present, nothing else can succeed. Discover where pcna, pcta, edcmbone currently live. Most likely: standalone repos under `erinepshovel-code` (the dev account). Look for:

- `erinepshovel-code/pcna`
- `erinepshovel-code/pcta`
- `erinepshovel-code/edcmbone`

For each, copy the inner package directory into `interdependent_lib/<name>/`, preserving internal structure. Confirm with the existing `ptca/` and `pcea/` directories as the layout reference.

If any source repo cannot be located: **stop gate.** Report and ask.

### Step 2 — pyproject.toml fix (bug #1)

Once code is present, fix the include path. The exact syntax depends on whether the file uses `setuptools.packages.find` or explicit lists. Preserve the existing style. Pattern:

```diff
- packages = ["ptca*"]
+ packages = ["interdependent_lib*"]
```

Or, if using `find` directive:

```diff
- include = ["ptca*"]
+ include = ["interdependent_lib*"]
```

### Step 3 — `pcea/__init__.py` (bug #3)

Derive exports from the existing PCEA module structure. If the standalone PCEA repo has a working `__init__.py`, base the unified one on it. Minimum requirement: re-export the public API surface (the encryption algorithm functions / classes).

### Step 4 — PCEA import migration (bug #2)

Sweep all PCEA files for imports referencing `guardian_state` or the old standalone-package path. Update to the unified package's path.

If `guardian_state` doesn't yet exist anywhere in the unified repo: **stop gate.** This is an architectural question (where does it live now?), not a mechanical fix. Report and ask.

---

## Verification

After each step:

```bash
python -m build
pip install -e .
python -c "import interdependent_lib"
python -c "from interdependent_lib import pcna, pcta, ptca, pcea, edcmbone"
```

After all four:

```bash
# Whichever test runner the repo uses; check pyproject.toml or setup.cfg
pytest
```

Existing tests must continue to pass. If they fail, **report what failed and why before making further changes** — do not modify tests to make them pass.

---

## Reporting back

After successful build, import, and test pass — or after hitting a stop gate — produce a short report containing:

- Files created (full paths)
- Files modified (full paths, with diff summaries for non-trivial changes)
- Any decisions made during execution (with reasoning)
- Any stop-gate triggers encountered
- Final build artifact paths (the `.whl` and `.tar.gz` under `dist/`)
- Test suite result (pass/fail count, names of any new failures)

Format: plain markdown, copy-pasteable. Erin will bring the report back for canon validation before the mirror to `wayseer00` is authorized.

---

## What stays with Erin (do not action)

- Authorizing the push to `wayseer00/interdependent-lib`
- The `edcm_metrics.py` operator-vs-behavioral architectural decision
- Resolution of the 15 collision priority violations in canon
- Any modification to frozen canon data files
- Any decision that changes the meaning of a module rather than its location

---

hmmm
