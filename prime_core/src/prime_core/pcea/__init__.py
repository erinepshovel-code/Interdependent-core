"""PCEA — Prime Circle Encryption Algorithm.

The core PCEA cipher is the bijective base-p construction over the
53-prime circle (canon C7). The legacy AES/HKDF/Shamir envelope is not
shipped in v0.1.0.
"""

from .core import (
    PCEAInstance,
    PRIME_CIRCLE,
    bijective_base_p_decode,
    bijective_base_p_encode,
    decrypt,
    derive_key_from_tensor,
    encrypt,
    prime_for_index,
)

__all__ = [
    "PCEAInstance",
    "PRIME_CIRCLE",
    "bijective_base_p_decode",
    "bijective_base_p_encode",
    "decrypt",
    "derive_key_from_tensor",
    "encrypt",
    "prime_for_index",
]
