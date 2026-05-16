# GPT/Claude generated; context, prompt Erin Spencer
# Date: 2026-04-06

"""interdependent-lib — unified PCNA/PCTA/PTCA/PCEA/EDCM library."""

from . import edcm, pcna, pcta, ptca

__version__ = "0.1.0"
__all__ = ["edcm", "pcna", "pcta", "ptca"]

# pcea depends on the third-party `cryptography` package. Import it lazily so
# environments without a working `cryptography` install can still use the
# stdlib-only subpackages.
try:
    from . import pcea  # noqa: F401
except Exception:  # pragma: no cover - import guard
    pcea = None  # type: ignore[assignment]
else:
    __all__.append("pcea")
