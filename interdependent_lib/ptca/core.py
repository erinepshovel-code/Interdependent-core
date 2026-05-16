# GPT/Claude generated; context, prompt Erin Spencer
"""
PTCACore — 53 prime-indexed PTCA seeds, 4 of them sentinels.

A core composes the full PTCA hierarchy:

    PCNA network  ->  base tensor
    PCTA circle   ->  7 PCNA tensors
    PTCA seed     ->  7 PCTA circles
    PTCA core     ->  53 seeds, 4 designated as sentinel seeds whose
                       9 sentinel channels (S1-S9) gate every exchange

The core also owns one routing :class:`PTCATensor` (shape 53x9x8x7) and
an :class:`Exchange` router so that scores written during exchanges live
on the same object that holds the structural weight tensor.

Default sentinel positions
--------------------------
The 4 sentinel-seed positions default to evenly-spaced indices across the
53-seed core (0, 13, 26, 39).  Callers may override via ``sentinel_indices``.

The chosen indices are persisted in ``sentinel_indices`` and exposed via
``sentinel_seeds`` / ``regular_seeds`` for downstream consumers (PCEA
seal of guardian state, audit views, etc.).
"""

from __future__ import annotations

from typing import Any, Iterable

from interdependent_lib.pcna.network import PCNANetwork
from interdependent_lib.pcta.circle import PCTACircle
from interdependent_lib.ptca.constants import NODES, SENTINELS
from interdependent_lib.ptca.exchange import Exchange
from interdependent_lib.ptca.primes import PRIME_NODES
from interdependent_lib.ptca.seed import PTCASeed, SEED_CIRCLES
from interdependent_lib.ptca.sentinels import SentinelState
from interdependent_lib.ptca.tensor import PTCATensor

CORE_SEEDS = NODES                  # 53
SENTINEL_SEED_COUNT = 4             # 4 sentinel seeds upgrade to 9 S-channels
DEFAULT_SENTINEL_INDICES: tuple[int, ...] = (0, 13, 26, 39)


class PTCACore:
    """
    A 53-seed PTCA core, with 4 designated sentinel seeds.

    Parameters
    ----------
    seeds:
        Exactly 53 :class:`PTCASeed` instances, in node order.  Each seed's
        ``is_sentinel`` flag is overwritten to match ``sentinel_indices``.
    sentinel_indices:
        Indices of the 4 sentinel seeds within the 53-seed core.
        Defaults to ``(0, 13, 26, 39)``.
    """

    def __init__(
        self,
        seeds: list[PTCASeed],
        *,
        sentinel_indices: Iterable[int] | None = None,
    ) -> None:
        if len(seeds) != CORE_SEEDS:
            raise ValueError(
                f"A PTCACore requires exactly {CORE_SEEDS} seeds, got {len(seeds)}"
            )
        chosen = tuple(sentinel_indices) if sentinel_indices is not None else DEFAULT_SENTINEL_INDICES
        if len(chosen) != SENTINEL_SEED_COUNT:
            raise ValueError(
                f"Expected exactly {SENTINEL_SEED_COUNT} sentinel indices, "
                f"got {len(chosen)}"
            )
        if len(set(chosen)) != SENTINEL_SEED_COUNT:
            raise ValueError(f"Sentinel indices must be unique: {chosen}")
        for idx in chosen:
            if not (0 <= idx < CORE_SEEDS):
                raise IndexError(
                    f"Sentinel index {idx} out of range [0, {CORE_SEEDS})"
                )
        self.sentinel_indices: tuple[int, ...] = tuple(sorted(chosen))

        # Reconcile flags + node/prime metadata against canonical positions.
        for i, seed in enumerate(seeds):
            seed.node_index = i
            seed.prime = PRIME_NODES[i]
            is_sentinel = i in self.sentinel_indices
            seed.is_sentinel = is_sentinel
            if is_sentinel and seed.sentinel_state is None:
                seed.sentinel_state = SentinelState()
            elif not is_sentinel:
                seed.sentinel_state = None
        self.seeds: list[PTCASeed] = seeds

        # The four sentinel seeds collectively realise the 9 S-channels:
        # channels are distributed round-robin across the 4 sentinel seeds,
        # so each sentinel seed owns 2 or 3 of the 9 channels.  The map below
        # is canonical and used by ``channel_owner``.
        self._channel_owner: dict[int, int] = {
            ch: self.sentinel_indices[ch % SENTINEL_SEED_COUNT]
            for ch in range(SENTINELS)
        }

        # Routing tensor + exchange router (shared with downstream consumers).
        self.tensor = PTCATensor()
        # Use the first sentinel seed's state as the canonical SentinelState
        # for the Exchange router; the core's other sentinel seeds remain
        # addressable individually via ``sentinel_state_for``.
        primary = self.seeds[self.sentinel_indices[0]].sentinel_state
        assert primary is not None  # invariant: index is in sentinel_indices
        self._exchange = Exchange(self.tensor, primary)

    # ------------------------------------------------------------------
    # Composition views
    # ------------------------------------------------------------------

    @property
    def sentinel_seeds(self) -> list[PTCASeed]:
        return [self.seeds[i] for i in self.sentinel_indices]

    @property
    def regular_seeds(self) -> list[PTCASeed]:
        return [s for s in self.seeds if not s.is_sentinel]

    def as_tensor(self) -> list[float]:
        """Flat concatenation of all 53 seed tensors."""
        result: list[float] = []
        for seed in self.seeds:
            result.extend(seed.as_tensor())
        return result

    @property
    def tensor_size(self) -> int:
        return sum(s.tensor_size for s in self.seeds)

    # ------------------------------------------------------------------
    # Sentinel access
    # ------------------------------------------------------------------

    def channel_owner(self, channel_index: int) -> PTCASeed:
        """Return the sentinel seed that owns S(channel_index+1)."""
        if not (0 <= channel_index < SENTINELS):
            raise IndexError(
                f"Channel index {channel_index} out of range [0, {SENTINELS})"
            )
        return self.seeds[self._channel_owner[channel_index]]

    def sentinel_state_for(self, channel_index: int) -> SentinelState:
        """Return the SentinelState backing the owner of channel ``channel_index``."""
        owner = self.channel_owner(channel_index)
        assert owner.sentinel_state is not None  # invariant
        return owner.sentinel_state

    @property
    def exchange(self) -> Exchange:
        return self._exchange

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    def audit(self) -> dict[str, Any]:
        """Aggregate audit across all 53 seeds."""
        per_seed = [s.audit() for s in self.seeds]
        means = [a["mean_of_means"] for a in per_seed]
        spreads = [a["max_spread"] for a in per_seed]
        return {
            "seed_count": CORE_SEEDS,
            "sentinel_indices": list(self.sentinel_indices),
            "sentinel_seed_count": SENTINEL_SEED_COUNT,
            "channel_count": SENTINELS,
            "mean_of_seed_means": sum(means) / len(means),
            "max_seed_spread": max(spreads),
            "total_params": sum(a["total_params"] for a in per_seed),
            "tensor_size": self.tensor_size,
        }

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    @classmethod
    def from_layer_sizes(
        cls,
        layer_sizes: list[int],
        *,
        activations: list[str] | None = None,
        sentinel_indices: Iterable[int] | None = None,
    ) -> "PTCACore":
        """
        Build a full 53-seed core whose every PCNA network shares
        the given ``layer_sizes`` / ``activations``.

        Each underlying PCNA network is initialised via Xavier from
        ``os.urandom``, so the resulting core is not deterministic.
        """
        seeds: list[PTCASeed] = []
        for node_idx in range(CORE_SEEDS):
            circles: list[PCTACircle] = []
            for circle_idx in range(SEED_CIRCLES):
                members = [
                    PCNANetwork(layer_sizes=layer_sizes, activations=activations)
                    for _ in range(7)
                ]
                circles.append(PCTACircle(members, circle_id=circle_idx))
            seeds.append(
                PTCASeed(
                    circles,
                    node_index=node_idx,
                    prime=PRIME_NODES[node_idx],
                )
            )
        return cls(seeds, sentinel_indices=sentinel_indices)

    def __len__(self) -> int:
        return CORE_SEEDS

    def __repr__(self) -> str:
        return (
            f"PTCACore(seeds={CORE_SEEDS}, sentinels={SENTINEL_SEED_COUNT}, "
            f"channels={SENTINELS}, params={self.tensor_size})"
        )
