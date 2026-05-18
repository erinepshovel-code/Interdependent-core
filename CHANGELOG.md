# Changelog

All notable changes to `interdependent-lib` are recorded here.  Format
loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [SemVer](https://semver.org/).

## [0.2.0] — 2026-05-17

### Added

#### PTCA composition layer
- `PTCASeed` — holds exactly 7 `PCTACircle`s, indexed by a prime node,
  with an optional `SentinelState` when upgraded to a sentinel seed.
- `PTCACore` — 53 prime-indexed seeds with 4 designated sentinel seeds
  whose 9 sentinel channels (S1-S9) round-robin across the sentinels.
  Owns one routing `PTCATensor` and `Exchange` router so structural
  weights and exchange scores live on one object.
- `PTCACore.from_layer_sizes([...])` factory that builds the whole
  53 × 7 × 7-network core in one call.

#### Guardian PCEA bridge
- New top-level module `interdependent_lib.guardian` packs a
  `PTCAInstance.snapshot()` (or any dict) into a `LiveState`, derives a
  fresh live key from caller-supplied IKM, and seals it via PCEA.
- `seal_snapshot` / `unseal_snapshot` / `seal_instance` /
  `unseal_instance` / `pack_snapshot` / `unpack_snapshot`.

#### PTCAInstance hosts a PTCACore
- `PTCAInstance(..., core=core)` accepts an optional core; instance
  then routes exchanges through the core's tensor so structural
  weights and per-exchange scores share one object.
- `attach_core()`, `audit_core()`, `as_core_tensor()`, and a `CORE`
  block in `snapshot()` when a core is attached.

#### EDCM 9-metric scorer
- `EDCMScorer.score(parsed)` returns a `MetricScore` for each of
  C / R / D / N / L / O / F / E / I.
- R, N, L, E implemented lexically (canon flagged
  `requires_embeddings: False`).
- C, D, O, F, I return `value=None`, `requires_embeddings=True`, and
  the raw marker counts so an embedding-aware host can finish them
  without re-parsing.
- `MetricScore(value, marker_counts, requires_embeddings, notes)`.
- Module helpers: `score_transcript`, `EDCMScorer.score_text`.

#### a0 `UI_META` + `DATA_SCHEMA` convention
- Every subsystem (`pcna`, `pcta`, `ptca`, `pcea`, `edcm`, `guardian`)
  declares the two constants matching a0's
  `/api/v1/ui/structure` aggregation contract.
- New top-level helper `interdependent_lib.ui_structure()` returns
  `{"modules": [...]}` ordered by `UI_META["order"]`.

#### Test-suite hardening
- GitHub Actions matrix runs pytest on Python 3.9 / 3.10 / 3.11 / 3.12
  / 3.13 for every push to `main` and every PR.
- `tests/run_canon_coherence.py` — local triage harness that
  classifies tests into `CANON_VS_DATA` / `CANON_VS_CODE` /
  `MISSING_CANON` and emits a JSON artifact.

### Changed

- Top-level `interdependent_lib/__init__.py` now re-exports `pcna`,
  `pcta`, `ptca`, `edcm`, and (when `cryptography` is importable)
  `pcea` and `guardian`.
- `conftest.py` cryptography skip now also covers `test_guardian.py`
  and writes a stderr line when it triggers, so the silent test-count
  drop you used to see is now loud.

### Fixed

- Canon-coherence harness `CANON_DIR` pointed at
  `interdependent_lib/edcmbone/canon` (which doesn't exist in this
  layout).  Repointed at `interdependent_lib/edcm/data`.

## [0.1.0] — 2026-05-15

Initial release.  PCNA / PCTA / PTCA / PCEA / EDCM as standalone
subsystems with a unified package surface.
