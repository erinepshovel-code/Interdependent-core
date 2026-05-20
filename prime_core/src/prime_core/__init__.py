"""prime_core — the Pxxx quartet (PCNA, PCTA, PTCA, PCEA).

See ``docs/canon.md`` for the v0.1.0 frozen canon decisions.
"""

PRIME_CORE_SIZE = 53

from . import pcna, pcta, ptca, pcea, guardian

__version__ = "0.1.0"
__all__ = ["pcna", "pcta", "ptca", "pcea", "guardian", "PRIME_CORE_SIZE"]
