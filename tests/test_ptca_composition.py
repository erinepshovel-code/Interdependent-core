"""
Tests for the PTCA composition layer: PTCASeed and PTCACore.

Covers the documented hierarchy:
    PCNA network -> PCTA circle (7 PCNAs) -> PTCA seed (7 PCTAs) ->
    PTCA core (53 seeds, 4 sentinels -> 9 S-channels)
"""

from __future__ import annotations

import pytest

from interdependent_lib import pcna, pcta, ptca
from interdependent_lib.pcna import PCNANetwork
from interdependent_lib.pcta import PCTACircle
from interdependent_lib.ptca import (
    CORE_SEEDS,
    DEFAULT_SENTINEL_INDICES,
    PRIME_NODES,
    SEED_CIRCLES,
    SENTINEL_SEED_COUNT,
    SENTINELS,
    PTCACore,
    PTCASeed,
    SentinelState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _circle(layer_sizes=(2, 3, 1)) -> PCTACircle:
    members = [PCNANetwork(list(layer_sizes)) for _ in range(7)]
    return PCTACircle(members)


def _seed(node_index: int = 0) -> PTCASeed:
    circles = [_circle() for _ in range(SEED_CIRCLES)]
    return PTCASeed(
        circles,
        node_index=node_index,
        prime=PRIME_NODES[node_index],
    )


def _seed_list() -> list[PTCASeed]:
    return [_seed(i) for i in range(CORE_SEEDS)]


# ---------------------------------------------------------------------------
# Top-level package re-exports
# ---------------------------------------------------------------------------


def test_top_level_subpackages_exposed():
    import interdependent_lib

    assert interdependent_lib.pcna is pcna
    assert interdependent_lib.pcta is pcta
    assert interdependent_lib.ptca is ptca
    # edcm always available
    assert hasattr(interdependent_lib, "edcm")


# ---------------------------------------------------------------------------
# PTCASeed
# ---------------------------------------------------------------------------


def test_seed_requires_seven_circles():
    circles = [_circle() for _ in range(6)]
    with pytest.raises(ValueError, match="exactly 7"):
        PTCASeed(circles)


def test_seed_holds_seven_circles_and_reports_metadata():
    seed = _seed(node_index=5)
    assert len(seed) == SEED_CIRCLES == 7
    assert len(seed.circles) == 7
    assert seed.node_index == 5
    assert seed.prime == PRIME_NODES[5]
    assert seed.is_sentinel is False
    assert seed.sentinel_state is None


def test_seed_sentinel_carries_state():
    circles = [_circle() for _ in range(SEED_CIRCLES)]
    seed = PTCASeed(circles, is_sentinel=True)
    assert seed.is_sentinel is True
    assert isinstance(seed.sentinel_state, SentinelState)


def test_seed_as_tensor_is_concatenation_of_circle_tensors():
    seed = _seed()
    flat = seed.as_tensor()
    expected = sum((c.as_tensor() for c in seed.circles), start=[])
    assert flat == expected
    assert len(flat) == seed.tensor_size


def test_seed_audit_reports_aggregate_stats():
    seed = _seed(node_index=3)
    audit = seed.audit()
    assert audit["node_index"] == 3
    assert audit["prime"] == PRIME_NODES[3]
    assert audit["is_sentinel"] is False
    assert len(audit["circles"]) == SEED_CIRCLES
    assert audit["total_params"] == seed.tensor_size
    assert audit["max_spread"] >= 0.0


def test_seed_repr_distinguishes_sentinel_and_regular():
    regular = _seed()
    sentinel = PTCASeed(
        [_circle() for _ in range(SEED_CIRCLES)],
        is_sentinel=True,
    )
    assert "regular" in repr(regular)
    assert "sentinel" in repr(sentinel)


# ---------------------------------------------------------------------------
# PTCACore
# ---------------------------------------------------------------------------


def test_core_requires_fifty_three_seeds():
    with pytest.raises(ValueError, match="exactly 53"):
        PTCACore(_seed_list()[:10])


def test_core_default_sentinel_layout():
    core = PTCACore(_seed_list())
    assert len(core) == CORE_SEEDS == 53
    assert core.sentinel_indices == DEFAULT_SENTINEL_INDICES
    assert len(core.sentinel_seeds) == SENTINEL_SEED_COUNT == 4
    assert len(core.regular_seeds) == CORE_SEEDS - SENTINEL_SEED_COUNT


def test_core_reassigns_seed_metadata_and_sentinel_flags():
    seeds = _seed_list()
    for s in seeds:
        s.is_sentinel = False
        s.sentinel_state = None
    core = PTCACore(seeds, sentinel_indices=(2, 5, 7, 11))
    assert core.sentinel_indices == (2, 5, 7, 11)
    for idx, seed in enumerate(core.seeds):
        assert seed.node_index == idx
        assert seed.prime == PRIME_NODES[idx]
        if idx in core.sentinel_indices:
            assert seed.is_sentinel is True
            assert isinstance(seed.sentinel_state, SentinelState)
        else:
            assert seed.is_sentinel is False
            assert seed.sentinel_state is None


def test_core_rejects_wrong_number_of_sentinels():
    with pytest.raises(ValueError, match="4 sentinel"):
        PTCACore(_seed_list(), sentinel_indices=(0, 1, 2))


def test_core_rejects_duplicate_sentinels():
    with pytest.raises(ValueError, match="unique"):
        PTCACore(_seed_list(), sentinel_indices=(0, 0, 1, 2))


def test_core_rejects_out_of_range_sentinels():
    with pytest.raises(IndexError):
        PTCACore(_seed_list(), sentinel_indices=(0, 1, 2, 53))


def test_core_as_tensor_is_concat_of_seeds():
    core = PTCACore(_seed_list())
    flat = core.as_tensor()
    expected = sum((s.as_tensor() for s in core.seeds), start=[])
    assert flat == expected
    assert len(flat) == core.tensor_size


def test_core_channel_owner_distributes_nine_channels_across_four_sentinels():
    core = PTCACore(_seed_list())
    owners = [core.channel_owner(ch).node_index for ch in range(SENTINELS)]
    assert set(owners) == set(core.sentinel_indices)
    # Channels round-robin -> 9 channels / 4 sentinels -> 3, 2, 2, 2
    owner_counts = [owners.count(i) for i in core.sentinel_indices]
    assert sorted(owner_counts, reverse=True) == [3, 2, 2, 2]


def test_core_channel_owner_rejects_out_of_range():
    core = PTCACore(_seed_list())
    with pytest.raises(IndexError):
        core.channel_owner(SENTINELS)


def test_core_sentinel_state_for_returns_owner_state():
    core = PTCACore(_seed_list())
    for ch in range(SENTINELS):
        state = core.sentinel_state_for(ch)
        assert state is core.channel_owner(ch).sentinel_state


def test_core_exchange_writes_to_owned_tensor():
    core = PTCACore(_seed_list())
    before = core.tensor.get(0, 0, 0, 0)
    result = core.exchange.route(node=0, phase=0, slot=0, s1=1.0, s5=0.5)
    after = core.tensor.get(0, 0, 0, 0)
    assert after != before
    assert isinstance(result.score, float)


def test_core_audit_aggregates_seed_audits():
    core = PTCACore(_seed_list())
    audit = core.audit()
    assert audit["seed_count"] == CORE_SEEDS
    assert audit["sentinel_seed_count"] == SENTINEL_SEED_COUNT
    assert audit["channel_count"] == SENTINELS
    assert audit["tensor_size"] == core.tensor_size
    assert audit["sentinel_indices"] == list(DEFAULT_SENTINEL_INDICES)


def test_core_from_layer_sizes_factory():
    core = PTCACore.from_layer_sizes([2, 4, 1])
    assert len(core) == CORE_SEEDS
    assert all(len(s) == SEED_CIRCLES for s in core.seeds)
    for s in core.sentinel_seeds:
        assert s.is_sentinel
        assert isinstance(s.sentinel_state, SentinelState)
    # Tensor is the concatenation of every nested PCNA's flat tensor.
    assert core.as_tensor() == sum((s.as_tensor() for s in core.seeds), start=[])


def test_core_repr_summary():
    core = PTCACore(_seed_list())
    text = repr(core)
    assert "seeds=53" in text
    assert "sentinels=4" in text
    assert "channels=9" in text
