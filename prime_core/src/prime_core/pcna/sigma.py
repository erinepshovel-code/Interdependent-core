"""Sigma → Psi coherence-injection bound (canon C10).

Sigma is the filesystem observer; it sits outside the
:data:`prime_core.invariants.COHERENCE_WEIGHTS` vector and does not
receive its own score weight. Sigma may inject coherence into Psi,
but the injection magnitude is bounded by
:data:`prime_core.invariants.SIGMA_PSI_MAX`.
"""

from __future__ import annotations

from prime_core.invariants import SIGMA_PSI_MAX


def inject_sigma_to_psi(strength: float) -> float:
    """Validate a Sigma → Psi coherence injection and return its strength.

    Parameters
    ----------
    strength:
        Injection magnitude. Must lie in ``[0.0, SIGMA_PSI_MAX]``.

    Raises
    ------
    ValueError
        If ``strength`` is outside the canonical bound.
    """
    if not (0.0 <= strength <= SIGMA_PSI_MAX):
        raise ValueError(
            f"sigma_injection_strength={strength!r} outside canonical bound "
            f"[0.0, {SIGMA_PSI_MAX}]"
        )
    return strength
