"""Guardian — placeholder for the prime_core guardian module.

The monolith ``interdependent_lib`` did not actually contain a top-level
``guardian.py`` — its guardian helpers live inside ``pcea/guardian.py`` and
``theta.py``, both of which depend on the AES/HKDF/Shamir PCEA envelope
that is explicitly excluded from v0.1.0 (canon C7).

For v0.1.0 we ship this stub so ``from prime_core import guardian`` works.
A real guardian extraction can be done once the optional ``pcea/envelope.py``
envelope lands, at which point the seal/unseal helpers can be carried
forward and rewired to the bijective base-p core (or kept as a separate
transport layer).
"""

from __future__ import annotations

__all__: list[str] = []
