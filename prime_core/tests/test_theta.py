"""Tests for the theta bridge — PTCA snapshot ↔ PCEA core round-trips."""

from __future__ import annotations

import warnings

import pytest

from prime_core import theta
from prime_core.ptca import PTCAInstance


SEED = [11, 13, 17, 19, 23, 29, 31]


# ---------------------------------------------------------------------------
# pack / unpack
# ---------------------------------------------------------------------------

def test_pack_is_deterministic_for_same_input():
    snap = {"S6_IDENTITY": {"model_id": "m"}, "value": 42}
    assert theta.pack_snapshot(snap) == theta.pack_snapshot(snap)


def test_pack_independent_of_key_order():
    a = theta.pack_snapshot({"a": 1, "b": 2})
    b = theta.pack_snapshot({"b": 2, "a": 1})
    assert a == b


def test_pack_produces_positive_integers():
    values = theta.pack_snapshot({"foo": [1, 2, 3], "bar": {"baz": True}})
    assert values
    assert all(v >= 1 for v in values)


def test_pack_unpack_round_trip():
    snap = {"foo": [1, 2, 3], "bar": {"baz": True}, "n": 0}
    assert theta.unpack_snapshot(theta.pack_snapshot(snap)) == snap


def test_unpack_rejects_out_of_range_values():
    with pytest.raises(ValueError):
        theta.unpack_snapshot([1, 2, 999])


# ---------------------------------------------------------------------------
# seal / unseal
# ---------------------------------------------------------------------------

def test_seal_unseal_round_trip():
    snap = {"session_id": "abc", "S8_RISK": {"score": 0.5, "factors": ["x"]}}
    sealed = theta.seal_snapshot(snap, seed=SEED)
    assert theta.unseal_snapshot(sealed, seed=SEED) == snap


def test_seal_changes_the_stream():
    snap = {"k": "value that is reasonably long so digits shift"}
    packed = theta.pack_snapshot(snap)
    sealed = theta.seal_snapshot(snap, seed=SEED)
    # Same length (digit-count invariant at byte granularity), different content.
    assert len(sealed) == len(packed)
    assert sealed != packed


def test_unseal_with_wrong_seed_does_not_recover_snapshot():
    snap = {"session_id": "abc", "n": 12345}
    sealed = theta.seal_snapshot(snap, seed=SEED)
    wrong = [s + 1 for s in SEED]
    with pytest.raises(Exception):
        theta.unseal_snapshot(sealed, seed=wrong)


# ---------------------------------------------------------------------------
# instance helpers
# ---------------------------------------------------------------------------

def test_seal_unseal_instance_round_trip():
    inst = PTCAInstance(session_id="s1", model_id="m1", caller_id="c1")
    sealed = theta.seal_instance(inst, seed=SEED)
    recovered = theta.unseal_instance(sealed, seed=SEED)
    assert recovered == inst.snapshot()


# ---------------------------------------------------------------------------
# guardian deprecation shim
# ---------------------------------------------------------------------------

def test_guardian_is_deprecated_alias_of_theta():
    import importlib
    import sys

    sys.modules.pop("prime_core.guardian", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        guardian = importlib.import_module("prime_core.guardian")
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert guardian.seal_snapshot is theta.seal_snapshot
    assert guardian.unseal_instance is theta.unseal_instance
