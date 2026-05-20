"""PCEA core tests — bijective base-p round-trip and edge cases."""

import random

import pytest

from prime_core.invariants import PRIME_CORE_SIZE
from prime_core.pcea import (
    PCEAInstance,
    PRIME_CIRCLE,
    bijective_base_p_decode,
    bijective_base_p_encode,
    decrypt,
    encrypt,
    prime_for_index,
)


# ---------------------------------------------------------------------------
# Bijective codec
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("p", [2, 3, 5, 7, 11, 53, 241])
def test_bijective_round_trip_small(p):
    for v in range(1, p * p + 5):
        assert bijective_base_p_decode(bijective_base_p_encode(v, p), p) == v


def test_bijective_digits_in_range():
    for v in [1, 2, 10, 99, 100, 9999, 123456]:
        for p in [2, 7, 53, 241]:
            digits = bijective_base_p_encode(v, p)
            assert all(1 <= d <= p for d in digits)


def test_bijective_rejects_zero():
    with pytest.raises(ValueError):
        bijective_base_p_encode(0, 7)


def test_bijective_rejects_bad_base():
    with pytest.raises(ValueError):
        bijective_base_p_encode(5, 1)


# ---------------------------------------------------------------------------
# Prime circle
# ---------------------------------------------------------------------------

def test_prime_circle_length():
    assert len(PRIME_CIRCLE) == PRIME_CORE_SIZE


def test_prime_circle_starts_correctly():
    assert PRIME_CIRCLE[:5] == [2, 3, 5, 7, 11]


def test_prime_circle_ends_at_241():
    # 53rd prime is 241.
    assert PRIME_CIRCLE[-1] == 241


def test_prime_for_index_wraps():
    assert prime_for_index(0) == 2
    assert prime_for_index(52) == 241
    assert prime_for_index(53) == 2
    assert prime_for_index(53 * 5 + 4) == PRIME_CIRCLE[4]


# ---------------------------------------------------------------------------
# Stateless encrypt / decrypt
# ---------------------------------------------------------------------------

def test_round_trip_length_53():
    random.seed(0)
    state = [random.randint(1, 5000) for _ in range(53)]
    last_state = [random.randint(1, 5000) for _ in range(53)]
    assert decrypt(encrypt(state, last_state), last_state) == state


def test_round_trip_state_of_one():
    state = [1]
    last_state = [1]
    encrypted = encrypt(state, last_state)
    assert decrypt(encrypted, last_state) == state


def test_round_trip_very_large_values():
    state = [10 ** 12, 2 ** 40 + 7, 999_999_999_999]
    last_state = [2 ** 30, 17, 1]
    encrypted = encrypt(state, last_state)
    assert decrypt(encrypted, last_state) == state


def test_round_trip_last_state_shorter_than_state():
    state = [random.randint(1, 1000) for _ in range(127)]
    last_state = [3, 7, 11]  # cycles
    encrypted = encrypt(state, last_state)
    assert decrypt(encrypted, last_state) == state


def test_encrypt_rejects_empty_last_state():
    with pytest.raises(ValueError):
        encrypt([1, 2, 3], [])


def test_digit_count_invariant():
    random.seed(53)
    state = [random.randint(1, 100_000) for _ in range(80)]
    last_state = [random.randint(1, 100_000) for _ in range(80)]
    encrypted = encrypt(state, last_state)
    for i, (v, e) in enumerate(zip(state, encrypted)):
        p = prime_for_index(i)
        assert len(bijective_base_p_encode(v, p)) == len(bijective_base_p_encode(e, p))


# ---------------------------------------------------------------------------
# Stateful PCEAInstance
# ---------------------------------------------------------------------------

def test_instance_paired_round_trip():
    seed = [random.randint(1, 1000) for _ in range(53)]
    enc = PCEAInstance(seed=seed)
    dec = PCEAInstance(seed=seed)

    plain1 = [random.randint(1, 1000) for _ in range(53)]
    plain2 = [random.randint(1, 1000) for _ in range(53)]
    plain3 = [random.randint(1, 1000) for _ in range(53)]

    c1 = enc.encrypt(plain1)
    c2 = enc.encrypt(plain2)
    c3 = enc.encrypt(plain3)

    assert dec.decrypt(c1) == plain1
    assert dec.decrypt(c2) == plain2
    assert dec.decrypt(c3) == plain3


def test_instance_first_encrypt_equals_stateless():
    seed = [11, 13, 17, 19, 23]
    plain = [1, 2, 3, 4, 5]

    inst = PCEAInstance(seed=seed)
    inst_out = inst.encrypt(plain)
    stateless_out = encrypt(plain, seed)
    assert inst_out == stateless_out


def test_instance_advances_state():
    seed = [11, 13, 17, 19, 23]
    plain = [42, 99, 7, 1, 100]
    inst = PCEAInstance(seed=seed)
    inst.encrypt(plain)
    assert inst.last_state == plain


def test_instance_rejects_empty_seed():
    with pytest.raises(ValueError):
        PCEAInstance(seed=[])
