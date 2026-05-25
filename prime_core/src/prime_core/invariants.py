"""Canonical constants shared across the Pxxx quartet.

These constants encode the v0.1.0 frozen canon. The three "53"s — PCNA core
ring size, PTCA prime-node count, PCEA prime-circle schedule length — all
reference :data:`PRIME_CORE_SIZE` here so they cannot drift independently
(canon decision C8).
"""

from __future__ import annotations

PRIME_CORE_SIZE: int = 53

TOPOLOGY: dict[str, int] = {
    "global_router": 1,
    "meta_routers": 7,
    "sentinels": 4,
    "compute_seeds": 49,
    "total": 61,
    "core_ring": 53,
}

COHERENCE_WEIGHTS: dict[str, float] = {
    "Phi": 0.30,
    "Theta": 0.20,
    "Psi": 0.15,
    "Omega": 0.15,
    "Memory-L": 0.12,
    "Memory-S": 0.08,
}

RING_ROLES: dict[str, str] = {
    "Phi": "cognitive_substrate",
    "Psi": "self_model",
    "Omega": "autonomy",
    "Theta": "microkernel_gate",
    "Sigma": "filesystem_observer",
}

SIGMA_PSI_MAX: float = 0.10

TENSOR_SHAPE: tuple[int, int, int, int] = (53, 9, 8, 7)
