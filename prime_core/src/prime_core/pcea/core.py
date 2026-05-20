"""PCEA core — bijective base-p cipher over the 53-prime circle (canon C7).

The cipher operates on flat integer sequences. Each index ``i`` of the
state is paired with prime ``PRIME_CIRCLE[i % 53]``; the payload digit
is taken in *bijective* base-p (digits ``{1, …, p}``) while the key
digit is taken in *standard* base-p (digits ``{0, …, p-1}``). The two
are combined with a per-digit modular shift so the digit count is
preserved and the operation is exactly invertible.

Public API
----------
- :data:`PRIME_CIRCLE`           — first 53 primes
- :func:`prime_for_index`
- :func:`bijective_base_p_encode`, :func:`bijective_base_p_decode`
- :func:`encrypt`, :func:`decrypt`
- :class:`PCEAInstance`          — stateful, paired encryptor/decryptor

See ``docs/canon.md`` for the v0.1.0 frozen specification.
"""

from __future__ import annotations

from typing import Iterable

from prime_core.invariants import PRIME_CORE_SIZE


# ---------------------------------------------------------------------------
# Prime circle — computed via a sieve at module load, then frozen.
# ---------------------------------------------------------------------------

def _first_n_primes(n: int) -> list[int]:
    """Return the first ``n`` primes via a simple incremental sieve."""
    primes: list[int] = []
    candidate = 2
    while len(primes) < n:
        is_prime = True
        limit = int(candidate ** 0.5)
        for p in primes:
            if p > limit:
                break
            if candidate % p == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
        candidate += 1
    return primes


PRIME_CIRCLE: list[int] = _first_n_primes(PRIME_CORE_SIZE)
assert len(PRIME_CIRCLE) == PRIME_CORE_SIZE, "PRIME_CIRCLE must have 53 entries"


def prime_for_index(i: int) -> int:
    """Return ``PRIME_CIRCLE[i % 53]`` — the prime scheduled for index ``i``."""
    return PRIME_CIRCLE[i % PRIME_CORE_SIZE]


# ---------------------------------------------------------------------------
# Bijective base-p codec
# ---------------------------------------------------------------------------

def bijective_base_p_encode(v: int, p: int) -> list[int]:
    """Encode ``v >= 1`` in bijective base ``p`` (digits ``{1, …, p}``).

    The most-significant digit is first.
    """
    if p < 2:
        raise ValueError(f"base must be >= 2; got {p}")
    if v < 1:
        raise ValueError(f"bijective base-p requires v >= 1; got {v}")
    digits: list[int] = []
    while v > 0:
        v, r = divmod(v - 1, p)
        digits.append(r + 1)
    digits.reverse()
    return digits


def bijective_base_p_decode(digits: Iterable[int], p: int) -> int:
    """Decode a bijective base-``p`` digit sequence back to an integer."""
    v = 0
    for digit in digits:
        if not 1 <= digit <= p:
            raise ValueError(f"digit {digit} outside bijective range [1, {p}]")
        v = v * p + digit
    return v


def _standard_base_p_digits(v: int, p: int, length: int) -> list[int]:
    """Standard base-p digits (``{0, …, p-1}``), zero-padded to ``length``.

    Most-significant digit first. Used for the key channel only.
    """
    if v < 0:
        raise ValueError(f"key value must be >= 0; got {v}")
    digits: list[int] = []
    n = v
    while n > 0:
        digits.append(n % p)
        n //= p
    if len(digits) < length:
        digits.extend([0] * (length - len(digits)))
    elif len(digits) > length:
        # Key has more digits than payload: truncate the high end.
        # This keeps digit-count invariant on the encrypted side.
        digits = digits[:length]
    digits.reverse()
    return digits


# ---------------------------------------------------------------------------
# Element-level encrypt / decrypt
# ---------------------------------------------------------------------------

def _encrypt_element(v: int, k: int, p: int) -> int:
    v_digits = bijective_base_p_encode(v, p)
    k_digits = _standard_base_p_digits(k, p, len(v_digits))
    enc_digits = [((vd - 1 + kd) % p) + 1 for vd, kd in zip(v_digits, k_digits)]
    return bijective_base_p_decode(enc_digits, p)


def _decrypt_element(e: int, k: int, p: int) -> int:
    e_digits = bijective_base_p_encode(e, p)
    k_digits = _standard_base_p_digits(k, p, len(e_digits))
    dec_digits = [((ed - 1 - kd) % p) + 1 for ed, kd in zip(e_digits, k_digits)]
    return bijective_base_p_decode(dec_digits, p)


# ---------------------------------------------------------------------------
# Stateless API
# ---------------------------------------------------------------------------

def encrypt(state: list[int], last_state: list[int]) -> list[int]:
    """Encrypt ``state`` against ``last_state``.

    ``last_state`` is indexed modulo its own length, which allows a shorter
    key sequence to drive a longer payload.
    """
    if not last_state:
        raise ValueError("last_state must be non-empty")
    L = len(last_state)
    return [
        _encrypt_element(v, last_state[i % L], prime_for_index(i))
        for i, v in enumerate(state)
    ]


def decrypt(encrypted: list[int], last_state: list[int]) -> list[int]:
    """Decrypt ``encrypted`` against ``last_state``. Inverse of :func:`encrypt`."""
    if not last_state:
        raise ValueError("last_state must be non-empty")
    L = len(last_state)
    return [
        _decrypt_element(e, last_state[i % L], prime_for_index(i))
        for i, e in enumerate(encrypted)
    ]


# ---------------------------------------------------------------------------
# Stateful API
# ---------------------------------------------------------------------------

class PCEAInstance:
    """Stateful PCEA encryptor / decryptor.

    The instance holds an internal ``last_state``. After each
    :meth:`encrypt` or :meth:`decrypt` call the last_state advances to
    the just-processed *plaintext* — so a paired encryptor and decryptor
    initialised from the same seed remain in lock-step.
    """

    def __init__(self, seed: list[int]):
        if not seed:
            raise ValueError("seed must be non-empty")
        self._last_state: list[int] = list(seed)

    @property
    def last_state(self) -> list[int]:
        return list(self._last_state)

    def encrypt(self, state: list[int]) -> list[int]:
        encrypted = encrypt(state, self._last_state)
        self._last_state = list(state)
        return encrypted

    def decrypt(self, encrypted: list[int]) -> list[int]:
        plaintext = decrypt(encrypted, self._last_state)
        self._last_state = list(plaintext)
        return plaintext


# ---------------------------------------------------------------------------
# Optional helper: quantise a tensor into a positive-integer key.
# ---------------------------------------------------------------------------

def derive_key_from_tensor(tensor: list[float], scale: float = 1000.0) -> list[int]:
    """Quantise a list of floats into positive integers suitable as last_state.

    Values are scaled, rounded, taken absolute, and clipped to ``>= 1``. This
    is *not* a cryptographic KDF — it is a convenience for wiring tensor
    activations into the cipher's key channel.
    """
    out: list[int] = []
    for x in tensor:
        v = int(abs(round(x * scale)))
        if v < 1:
            v = 1
        out.append(v)
    return out


__all__ = [
    "PRIME_CIRCLE",
    "PCEAInstance",
    "bijective_base_p_decode",
    "bijective_base_p_encode",
    "decrypt",
    "derive_key_from_tensor",
    "encrypt",
    "prime_for_index",
]
