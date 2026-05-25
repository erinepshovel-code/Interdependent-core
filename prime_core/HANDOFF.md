# prime_core — Handoff (continuation)

Point-in-time handoff for the next session. The durable spec is in
`docs/canon.md`; this file is the *working state* on top of it.

## Where things live

- **Repo**: `erinepshovel-code/interdependent-lib` (the remote now reports a
  move to `erinepshovel-code/Interdependent-core` — pushes still succeed via
  redirect; confirm the canonical name before any remote surgery).
- **Branch**: `claude/scaffold-prime-core-kfNhl`
- **PR**: #12 (draft) into `main`
- **Package location**: top-level `prime_core/` subdirectory of the monolith.
  Per decision below, **everything stays in the org repo for now** — no
  extraction to a standalone `prime_core` repo yet.

## Resolved decisions (were open questions)

1. **Repo owner / extraction** — "everything goes to the org right now."
   Keep prime_core as a subdirectory in the org's repo; do not split it out
   yet.
2. **License** — **Apache-2.0** (matches the monolith). `LICENSE` is the
   Apache text; `pyproject.toml` uses the PEP 639 `license = "Apache-2.0"` +
   `license-files` expression (needs `setuptools>=77`).
3. **Legacy AES envelope** — *not* the direction. See PCEA security model
   below. The old `cryptography`-based PCEA stays excluded.

## What is built and green

- Carried `pcna`, `pcta`, `ptca` from the monolith with imports rewritten to
  `prime_core.*`.
- Canon constants centralized in `src/prime_core/invariants.py`
  (`PRIME_CORE_SIZE`, `TOPOLOGY`, `COHERENCE_WEIGHTS`, `RING_ROLES`,
  `SIGMA_PSI_MAX`, `TENSOR_SHAPE`) and re-exported through the layer packages.
- **PCEA core** (`src/prime_core/pcea/core.py`): fresh bijective base-p cipher
  over the 53-prime circle. `PRIME_CIRCLE` computed via a sieve at import.
  Stateless `encrypt`/`decrypt` and stateful `PCEAInstance`.
- **theta bridge** (`src/prime_core/theta.py`): seals PTCA snapshots through
  the PCEA core — `pack → encrypt → decrypt → unpack`. Deterministic,
  seed-keyed, round-trippable. This replaces the monolith's AES-based theta.
- **guardian** (`src/prime_core/guardian.py`): deprecation shim re-exporting
  theta and warning on import. Top-level package exposes `theta`, not
  `guardian`.
- **Tests**: `tests/` — invariants, pcea core, ported pcna/pcta/ptca/
  composition, and theta. **170 passing locally.**
- **CI**: `.github/workflows/tests.yml` has a second `prime-core` matrix job
  (3.9–3.13) that installs from `prime_core/` and runs its own pytest. The
  monolith `test` job was scoped to `tests/` (root `pyproject.toml`
  `testpaths`) so it no longer recurses into `prime_core/tests/`.

## Known discrepancies (already handled, noted for the record)

- CLAUDE.md prose says the tensor has 26,796 cells; `53*9*8*7 = 26,712`. The
  test asserts the correct product; the canonical shape `(53,9,8,7)` stands.
- `compute_score` returns `(float, dict)`; `exchange_score` wraps it to return
  just the scalar for the canon C6 contract.
- No top-level `guardian.py` existed in the monolith; the new one is the
  deprecation shim described above.
- `twine check` of the built wheel fails under this sandbox's system
  `packaging` 24.0 (PEP 639 metadata needs `packaging>=24.2`). A current CI
  runner is unaffected; nothing in CI runs twine on prime_core yet.

## NEW design direction — PCEA security model (DESIGN, not yet built)

Direction from the maintainer, to be designed before implementing:

- **PCEA is mainly a defense against penetration testing** — active probing /
  attack resistance — rather than confidentiality-at-rest (which would be an
  envelope's job).
- **The security metric is bits of entropy.**
- **The primary defense is entropy acquired from nested UCNS objects.**
  UCNS = **Unit Circle Number System**. This entropy feeds the cipher's key
  material (the `seed` / `last_state` driving the bijective base-p transform).

### Open design questions to resolve first (do NOT implement blind)

1. **Concrete UCNS object.** Is "Unit Circle Number System" a representation
   of values as angular positions / phases on the unit circle (value ↔ point
   on the circle)? Does "nested" reuse the existing circle hierarchy
   (PCNA → PCTA circle of 7 → PTCA seed of 7 circles → 53-seed core), or is it
   a new structure of its own? No `ucn`/`ucns` symbol exists in the repo yet.
2. **"Acquired" entropy — measure, extract, or both?** Likely a pair:
   `entropy_bits(ucns) -> float` (the security metric) and
   `harvest_entropy(ucns) -> seed` (key material for `PCEAInstance`).
3. **Threat model specifics.** What pen-test attacks must PCEA resist
   (known-plaintext, chosen-plaintext, replay across epochs, side channels)?
   This determines whether the base-p transform alone suffices or needs
   diffusion/whitening on top.

### Proposed module shape (for sign-off, unwritten)

- `src/prime_core/pcea/ucns.py` — the Unit Circle Number System representation
  and its nesting.
- `src/prime_core/pcea/entropy.py` — `entropy_bits(...)` and
  `harvest_entropy(...) -> list[int]` seeding `PCEAInstance`.
- Keep `core.py` as the pure transform; entropy/UCNS layer sits above it.

## Roadmap to v0.5.0

- [x] prime_core exercised in CI
- [x] PTCA↔PCEA bridge (theta) implemented + tested
- [x] guardian deprecated to theta
- [x] layer tests ported
- [x] Apache-2.0 license
- [ ] **PCEA UCNS-entropy defense** — resolve the three design questions above,
      get module-shape sign-off, then implement `ucns.py` + `entropy.py` with
      a bits-of-entropy metric and pen-test-oriented tests.
- [ ] Decide whether C11 audit asymmetry needs real implementation vs. only
      documentation.
- [ ] CHANGELOG + (eventual) release pipeline once/if the package is extracted.

## How to run

```bash
cd prime_core
pip install -e .[dev]
pytest -q
```
