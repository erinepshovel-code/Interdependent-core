"""
Tests for the theta bridge that connects PTCA snapshots and PCEA sealing.

These tests require a working ``cryptography`` package; ``conftest.py``
already skips the entire file when ``cryptography`` cannot be imported.
"""

from __future__ import annotations

import pytest

# Skip the whole module if cryptography is unavailable in this environment.
pytest.importorskip("cryptography")

from interdependent_lib import theta  # noqa: E402
from interdependent_lib.pcea import wipe  # noqa: E402
from interdependent_lib.pcea.types import LiveState  # noqa: E402
from interdependent_lib.ptca import PTCACore, PTCAInstance  # noqa: E402


IKM = b"x" * 32


def test_pack_snapshot_is_deterministic_for_same_input():
    snap = {"S6_IDENTITY": {"model_id": "m"}, "value": 42}
    a = theta.pack_snapshot(snap, epoch=1)
    b = theta.pack_snapshot(snap, epoch=1)
    assert a == b


def test_pack_unpack_round_trip():
    snap = {"foo": [1, 2, 3], "bar": {"baz": True}}
    packed = theta.pack_snapshot(snap, epoch=7)
    assert isinstance(packed, LiveState)
    assert packed.epoch == 7
    assert packed.coherence == 1.0
    assert theta.unpack_snapshot(packed) == snap


def test_unpack_rejects_unrelated_live_state():
    not_ours = LiveState(
        epoch=1,
        spiral={"phase": 0.0, "magnitude": 0.0, "base": 0.0},
        cores={"something_else": "x"},
        density_matrix=None,
        coherence=1.0,
        transport=None,
        last_renorm=0.0,
    )
    with pytest.raises(ValueError, match="snapshot"):
        theta.unpack_snapshot(not_ours)


def test_seal_unseal_snapshot_round_trip():
    snap = {"S5_CONTEXT": {"entries": [{"role": "user", "content": "hi"}]}}
    sealed, live_key = theta.seal_snapshot(
        snap,
        ikm=IKM,
        epoch=1,
        key_id="k1",
        guardian_node_id="g0",
        sealed_by="g0",
    )
    try:
        assert sealed.epoch == 1
        assert sealed.key_id == "k1"
        recovered = theta.unseal_snapshot(sealed, live_key)
        assert recovered == snap
    finally:
        wipe(live_key)


def test_seal_unseal_instance_round_trip():
    inst = PTCAInstance(model_id="claude", caller_id="user:alice", approved=True)
    inst.push_context({"role": "user", "content": "hello", "tokens": 5})
    inst.remember("favourite_colour", "indigo")
    inst.update_risk(0.2, factor="manual")

    sealed, live_key = theta.seal_instance(
        inst,
        ikm=IKM,
        epoch=2,
        key_id="k1",
        guardian_node_id="g0",
        sealed_by="g0",
    )
    try:
        recovered = theta.unseal_instance(sealed, live_key)
        assert recovered == inst.snapshot()
        assert recovered["S6_IDENTITY"]["model_id"] == "claude"
        assert recovered["S7_MEMORY"]["store"]["favourite_colour"] == "indigo"
        assert recovered["S8_RISK"]["score"] == pytest.approx(0.2)
    finally:
        wipe(live_key)


def test_seal_instance_includes_core_block_when_hosted():
    core = PTCACore.from_layer_sizes([2, 3, 1])
    inst = PTCAInstance(core=core)
    sealed, live_key = theta.seal_instance(
        inst,
        ikm=IKM,
        epoch=3,
        key_id="k1",
        guardian_node_id="g0",
        sealed_by="g0",
    )
    try:
        recovered = theta.unseal_instance(sealed, live_key)
        assert recovered["CORE"]["seed_count"] == 53
        assert recovered["CORE"]["tensor_size"] == core.tensor_size
    finally:
        wipe(live_key)


def test_unseal_with_wrong_key_fails():
    sealed, live_key = theta.seal_snapshot(
        {"v": 1},
        ikm=IKM,
        epoch=1,
        key_id="k1",
        guardian_node_id="g0",
        sealed_by="g0",
    )
    try:
        bad_key = bytearray(live_key)
        bad_key[0] ^= 0xFF
        with pytest.raises(Exception):  # AEAD authentication failure
            theta.unseal_snapshot(sealed, bytes(bad_key))
    finally:
        wipe(live_key)
