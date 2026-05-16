"""
Tests for PTCAInstance hosting a PTCACore.
"""

from __future__ import annotations

import pytest

from interdependent_lib.ptca import PTCACore, PTCAInstance


def _core() -> PTCACore:
    return PTCACore.from_layer_sizes([2, 3, 1])


def test_instance_without_core_routes_through_private_tensor():
    inst = PTCAInstance(approved=True)
    assert inst.core is None
    r = inst.route(node=0, phase=0, slot=0, s1=1.0)
    assert inst.tensor.get(0, 0, 0, 0) == r.score


def test_instance_with_core_shares_routing_tensor():
    core = _core()
    inst = PTCAInstance(approved=True, core=core)
    assert inst.core is core
    assert inst.tensor is core.tensor
    r = inst.route(node=0, phase=0, slot=0, s1=1.0)
    # the core's tensor saw the write
    assert core.tensor.get(0, 0, 0, 0) == r.score


def test_attach_core_after_construction():
    inst = PTCAInstance(approved=True)
    assert inst.core is None
    core = _core()
    inst.attach_core(core)
    assert inst.core is core
    assert inst.tensor is core.tensor
    # Audit log records the attachment.
    tail = inst.audit_tail(1)
    assert tail and tail[-1]["event"] == "core_attached"
    assert tail[-1]["seed_count"] == 53


def test_audit_core_requires_attached_core():
    inst = PTCAInstance()
    with pytest.raises(RuntimeError, match="No PTCACore"):
        inst.audit_core()
    with pytest.raises(RuntimeError, match="No PTCACore"):
        inst.as_core_tensor()


def test_audit_core_delegates_to_core():
    core = _core()
    inst = PTCAInstance(core=core)
    audit = inst.audit_core()
    assert audit == core.audit()


def test_as_core_tensor_returns_full_structural_tensor():
    core = _core()
    inst = PTCAInstance(core=core)
    flat = inst.as_core_tensor()
    assert flat == core.as_tensor()
    assert len(flat) == core.tensor_size


def test_snapshot_includes_core_summary_when_hosted():
    core = _core()
    inst = PTCAInstance(model_id="m", caller_id="c", core=core)
    snap = inst.snapshot()
    assert "CORE" in snap
    assert snap["CORE"]["seed_count"] == 53
    assert snap["CORE"]["tensor_size"] == core.tensor_size
    assert snap["CORE"]["sentinel_indices"] == list(core.sentinel_indices)


def test_snapshot_omits_core_block_without_hosted_core():
    inst = PTCAInstance()
    assert "CORE" not in inst.snapshot()
