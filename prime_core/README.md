# prime_core

The Pxxx quartet — **PCNA**, **PCTA**, **PTCA**, **PCEA** — packaged as a single
library. Replaces the prime-architecture layers from the monolithic
`interdependent-lib`. EDCM lives separately.

```
PCNA  ←  back-propagating neural network (base tensor)
PCTA  ←  circle: 7 PCNA tensors, audited as one tensor
PTCA  ←  seed: 7 PCTA circles → core: 53 seeds (4 sentinel seeds → 9 S-channels)
PCEA  ←  bijective base-p cipher over the 53-prime circle
```

## Install

```bash
pip install -e .[dev]
```

Optional AES envelope (not required for v0.1.0):

```bash
pip install -e .[envelope]
```

Requires Python ≥ 3.9. Core has no third-party dependencies.

## Quickstart

```python
from prime_core import PRIME_CORE_SIZE
from prime_core.pcea import PCEAInstance

assert PRIME_CORE_SIZE == 53

enc = PCEAInstance(seed=[11, 13, 17, 19, 23])
dec = PCEAInstance(seed=[11, 13, 17, 19, 23])
ciphertext = enc.encrypt([42, 99, 7, 1, 100])
assert dec.decrypt(ciphertext) == [42, 99, 7, 1, 100]
```

## Canon

The v0.1.0 frozen canon — eleven decisions covering topology, weights,
sentinel channels, tensor shape, scoring, and audit asymmetry — is recorded
in [`docs/canon.md`](docs/canon.md). Any subsequent revision bumps to v0.1.1+
rather than mutating the v0.1.0 freeze.

## Tests

```bash
pytest
```

`tests/test_invariants.py` is the acceptance contract; if any assertion
there fails, the scaffold is not v0.1.0.

## License

MIT — see [`LICENSE`](LICENSE).
