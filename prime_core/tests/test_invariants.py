"""Day-one invariant tests — v0.1.0 acceptance criteria.

These tests are the contract for the scaffold. They are quoted verbatim
in ``CLAUDE.md``; do not relax them without revising canon.
"""

import pytest

from prime_core import PRIME_CORE_SIZE
from prime_core.pcna import (
    COHERENCE_WEIGHTS,
    PCNANetwork,
    RING_ROLES,
    SIGMA_PSI_MAX,
    TOPOLOGY,
    inject_sigma_to_psi,
)
from prime_core.pcta import PCTACircle
from prime_core.ptca import TENSOR_SHAPE, exchange_score
from prime_core.pcea import (
    PRIME_CIRCLE,
    bijective_base_p_encode,
    decrypt,
    encrypt,
    prime_for_index,
)


def test_pcna_topology_partition():
    assert TOPOLOGY["global_router"] == 1
    assert TOPOLOGY["meta_routers"] == 7
    assert TOPOLOGY["sentinels"] == 4
    assert TOPOLOGY["compute_seeds"] == 49
    assert TOPOLOGY["total"] == 61
    assert TOPOLOGY["core_ring"] == 53
    assert TOPOLOGY["sentinels"] + TOPOLOGY["compute_seeds"] == TOPOLOGY["core_ring"]


def test_pcna_coherence_weights_sum_to_one():
    total = sum(COHERENCE_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9


def test_three_53s_are_linked_constant():
    assert PRIME_CORE_SIZE == 53
    assert TOPOLOGY["core_ring"] == PRIME_CORE_SIZE
    assert TENSOR_SHAPE[0] == PRIME_CORE_SIZE
    assert len(PRIME_CIRCLE) == PRIME_CORE_SIZE


def test_pcea_preserves_digit_count():
    import random
    random.seed(53)
    state = [random.randint(1, 1000) for _ in range(53)]
    last_state = [random.randint(1, 1000) for _ in range(53)]
    encrypted = encrypt(state, last_state)
    for i, (v, e) in enumerate(zip(state, encrypted)):
        p = prime_for_index(i)
        assert len(bijective_base_p_encode(v, p)) == len(bijective_base_p_encode(e, p)), \
            f"digit count not preserved at index {i}"
    decrypted = decrypt(encrypted, last_state)
    assert decrypted == state


def test_ptca_tensor_shape():
    # Canon C4: shape (53, 9, 8, 7). Product = 26,712. The handoff CLAUDE.md
    # quotes 26,796 in prose, which is an arithmetic error in the source
    # document — the shape is the canonical fact and the product is derived.
    assert TENSOR_SHAPE == (53, 9, 8, 7)
    nodes, sentinels, phases, slots = TENSOR_SHAPE
    assert nodes * sentinels * phases * slots == 26712


def test_ptca_score_computable():
    score = exchange_score(s1=1.0, s2=0.5, s3=0.5, s5=0.5, s8=0.0, bonus=0.0)
    assert isinstance(score, float)


def test_pcta_circle_size():
    members = [PCNANetwork([4, 4]) for _ in range(7)]
    circle = PCTACircle(members, circle_id=0)
    assert len(circle.members) == 7


def test_sigma_injection_is_bounded():
    inject_sigma_to_psi(strength=0.0)
    inject_sigma_to_psi(strength=SIGMA_PSI_MAX)
    with pytest.raises(ValueError):
        inject_sigma_to_psi(strength=SIGMA_PSI_MAX + 0.1)
    with pytest.raises(ValueError):
        inject_sigma_to_psi(strength=-0.1)


def test_logical_view_materializes_at_pcna_scale():
    assert RING_ROLES["Phi"] == "cognitive_substrate"
    assert RING_ROLES["Psi"] == "self_model"
    assert RING_ROLES["Omega"] == "autonomy"
    assert RING_ROLES["Theta"] == "microkernel_gate"
    assert RING_ROLES["Sigma"] == "filesystem_observer"
