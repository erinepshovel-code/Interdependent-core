# GPT/Claude generated; context, prompt Erin Spencer
"""PCEA — Prime Circle Encryption Algorithm: key management, AEAD sealing, and secret sharing."""

from .aead import AuthenticationError, seal, unseal
from .codec import encode_aad, encode_key_info, encode_nonce_input, encode_wrap_aad
from .commitment import make_commitment, verify_commitment
from .guardian import seal_live_state, unseal_live_state
from .kdf import derive_keys, derive_nonce
from .rekey import reconstruct_meta_key, rekey_epoch, split_meta_key
from .threshold import reconstruct_secret, split_secret
from .types import (
    LiveState,
    MetaShares,
    RekeyEpoch,
    SealedState,
    UnsealGrant,
    WrappedLiveKey,
)
from .validate import InvariantViolation, validate_invariant
from .wipe import wipe, wipe_bytearray, wipe_bytes
from .wrap import unwrap_live_key, wrap_live_key

UI_META = {
    "tab_id": "pcea",
    "label": "PCEA Crypto",
    "icon": "Lock",
    "order": 4,
    "sections": [
        {
            "id": "keys",
            "label": "Active Keys",
            "endpoint": "/api/v1/pcea/state",
            "fields": [
                {"key": "epoch",        "type": "text",  "label": "Epoch"},
                {"key": "key_id",       "type": "text",  "label": "Key ID"},
                {"key": "sealed_count", "type": "text",  "label": "Sealed States"},
                {"key": "last_sealed",  "type": "text",  "label": "Last Sealed"},
            ],
        },
        {
            "id": "shares",
            "label": "Meta Shares",
            "endpoint": "/api/v1/pcea/shares",
            "fields": [
                {"key": "threshold",    "type": "text",  "label": "Threshold"},
                {"key": "total_shares", "type": "text",  "label": "Total Shares"},
                {"key": "commitment",   "type": "text",  "label": "Commitment"},
            ],
        },
    ],
}

DATA_SCHEMA = {
    "endpoints": [
        {"method": "GET",  "path": "/api/v1/pcea/state"},
        {"method": "POST", "path": "/api/v1/pcea/seal"},
        {"method": "POST", "path": "/api/v1/pcea/unseal"},
        {"method": "POST", "path": "/api/v1/pcea/rekey"},
        {"method": "GET",  "path": "/api/v1/pcea/shares"},
        {"method": "POST", "path": "/api/v1/pcea/shares/split"},
        {"method": "POST", "path": "/api/v1/pcea/shares/reconstruct"},
    ],
}

__all__ = [
    "AuthenticationError",
    "DATA_SCHEMA",
    "UI_META",
    "InvariantViolation",
    "LiveState",
    "MetaShares",
    "RekeyEpoch",
    "SealedState",
    "UnsealGrant",
    "WrappedLiveKey",
    "derive_keys",
    "derive_nonce",
    "encode_aad",
    "encode_key_info",
    "encode_nonce_input",
    "encode_wrap_aad",
    "make_commitment",
    "reconstruct_meta_key",
    "reconstruct_secret",
    "rekey_epoch",
    "seal",
    "seal_live_state",
    "split_meta_key",
    "split_secret",
    "unseal",
    "unseal_live_state",
    "unwrap_live_key",
    "validate_invariant",
    "verify_commitment",
    "wipe",
    "wipe_bytearray",
    "wipe_bytes",
    "wrap_live_key",
]
