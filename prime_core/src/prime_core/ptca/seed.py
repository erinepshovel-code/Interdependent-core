# GPT/Claude generated; context, prompt Erin Spencer
"""
PTCASeed — one prime-indexed seed holding exactly 7 PCTA circles.

A seed is the next composition layer above a PCTA circle:

    PCNA network  ->  base tensor
    PCTA circle   ->  7 PCNA tensors, audited as one tensor
    PTCA seed     ->  7 PCTA circles, indexed by a prime node
    PTCA core     ->  53 seeds (4 of them upgraded to sentinel seeds)

A sentinel seed additionally carries a :class:`SentinelState`, exposing the
S1-S9 channels that gate exchanges routed through the core.
"""

from __future__ import annotations

from typing import Any

from prime_core.pcta.circle import PCTACircle
from prime_core.ptca.sentinels import SentinelState

SEED_CIRCLES = 7


class PTCASeed:
    """
    A PTCA seed: exactly 7 PCTA circles, optionally upgraded to a sentinel
    seed by attaching a :class:`SentinelState`.

    Parameters
    ----------
    circles:
        Exactly 7 :class:`~prime_core.pcta.circle.PCTACircle` members.
    node_index:
        Position of this seed within the 53-seed core (0-based).
    prime:
        The prime number assigned to this seed (from PRIME_NODES).
    is_sentinel:
        If True, ``sentinel_state`` is auto-created and the seed counts as
        one of the four sentinel seeds in the core.
    """

    def __init__(
        self,
        circles: list[PCTACircle],
        *,
        node_index: int = 0,
        prime: int = 0,
        is_sentinel: bool = False,
    ) -> None:
        if len(circles) != SEED_CIRCLES:
            raise ValueError(
                f"A PTCASeed requires exactly {SEED_CIRCLES} PCTA circles, "
                f"got {len(circles)}"
            )
        self.circles: list[PCTACircle] = circles
        self.node_index = node_index
        self.prime = prime
        self.is_sentinel = is_sentinel
        self.sentinel_state: SentinelState | None = (
            SentinelState() if is_sentinel else None
        )

    def as_tensor(self) -> list[float]:
        """Flat concatenation of all 7 PCTA-circle tensors."""
        result: list[float] = []
        for circle in self.circles:
            result.extend(circle.as_tensor())
        return result

    @property
    def tensor_size(self) -> int:
        return sum(c.tensor_size for c in self.circles)

    def audit(self) -> dict[str, Any]:
        """Audit each member circle and aggregate seed-level stats."""
        circle_audits = [c.audit() for c in self.circles]
        means = [a["weight_mean"] for a in circle_audits]
        spreads = [a["weight_spread"] for a in circle_audits]
        return {
            "node_index": self.node_index,
            "prime": self.prime,
            "is_sentinel": self.is_sentinel,
            "circles": circle_audits,
            "mean_of_means": sum(means) / len(means),
            "max_spread": max(spreads),
            "total_params": sum(a["total_params"] for a in circle_audits),
        }

    def __len__(self) -> int:
        return SEED_CIRCLES

    def __repr__(self) -> str:
        kind = "sentinel" if self.is_sentinel else "regular"
        return (
            f"PTCASeed(node={self.node_index}, prime={self.prime}, "
            f"{kind}, circles={SEED_CIRCLES})"
        )
