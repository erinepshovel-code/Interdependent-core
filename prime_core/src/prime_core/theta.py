"""Theta bridge — connects PTCA session state to the PCEA core.

In the monolith, ``theta`` packed a PTCA snapshot into a strongly-typed
``LiveState`` and sealed it with the AES/HKDF/Shamir envelope. In
prime_core the envelope is excluded from v0.1.0 (canon C7), so this
bridge seals over the bijective base-p core instead:

    snapshot (JSON-serialisable dict)
        --pack-->   flat list[int]  (positive integers)
        --encrypt-> flat list[int]  (PCEA ciphertext)
        --decrypt-> flat list[int]
        --unpack--> snapshot

The packing is deterministic and round-trippable: the snapshot is
serialised with sorted keys, so two packs of the same payload produce
identical integer streams.

Example
-------
::

    from prime_core.theta import seal_instance, unseal_instance

    seed = [11, 13, 17, 19, 23]
    sealed = seal_instance(inst, seed=seed)
    snapshot = unseal_instance(sealed, seed=seed)

The ``seed`` is the PCEA ``last_state``; a paired sealer and unsealer
must use the same seed (canon C7, stateless mode).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from prime_core.pcea.core import decrypt, encrypt

if TYPE_CHECKING:  # pragma: no cover
    from prime_core.ptca.instance import PTCAInstance

# Bytes are 0..255; the bijective base-p core requires every value >= 1,
# so payload bytes are offset by 1 before encryption and restored on unpack.
_BYTE_OFFSET = 1


UI_META = {
    "tab_id": "theta",
    "label": "Theta Bridge",
    "icon": "Shield",
    "order": 6,
    "sections": [
        {
            "id": "sealed",
            "label": "Last Seal",
            "endpoint": "/api/v1/theta/state",
            "fields": [
                {"key": "length", "type": "gauge", "label": "Ciphertext Length"},
            ],
        },
    ],
}

DATA_SCHEMA = {
    "endpoints": [
        {"method": "GET",  "path": "/api/v1/theta/state"},
        {"method": "POST", "path": "/api/v1/theta/seal"},
        {"method": "POST", "path": "/api/v1/theta/unseal"},
    ],
}


def pack_snapshot(snapshot: Any) -> list[int]:
    """Encode a JSON-serialisable snapshot into a flat list of positive integers.

    Deterministic: keys are sorted and separators are fixed, so equal
    inputs always yield equal integer streams.
    """
    blob = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return [b + _BYTE_OFFSET for b in blob]


def unpack_snapshot(values: list[int]) -> Any:
    """Inverse of :func:`pack_snapshot`."""
    try:
        blob = bytes(v - _BYTE_OFFSET for v in values)
    except ValueError as exc:  # value outside 1..256 → not a packed snapshot
        raise ValueError(
            "values are not a valid packed snapshot (byte out of range)"
        ) from exc
    return json.loads(blob.decode("utf-8"))


def seal_snapshot(snapshot: Any, *, seed: list[int]) -> list[int]:
    """Pack ``snapshot`` and encrypt it against ``seed`` (PCEA last_state)."""
    return encrypt(pack_snapshot(snapshot), seed)


def unseal_snapshot(encrypted: list[int], *, seed: list[int]) -> Any:
    """Decrypt a sealed snapshot back to its original object. Inverse of
    :func:`seal_snapshot`."""
    return unpack_snapshot(decrypt(encrypted, seed))


def seal_instance(instance: "PTCAInstance", *, seed: list[int]) -> list[int]:
    """Snapshot ``instance`` and seal it via the PCEA core."""
    return seal_snapshot(instance.snapshot(), seed=seed)


def unseal_instance(encrypted: list[int], *, seed: list[int]) -> Any:
    """Alias of :func:`unseal_snapshot` for symmetry with :func:`seal_instance`."""
    return unseal_snapshot(encrypted, seed=seed)


__all__ = [
    "DATA_SCHEMA",
    "UI_META",
    "pack_snapshot",
    "seal_instance",
    "seal_snapshot",
    "unpack_snapshot",
    "unseal_instance",
    "unseal_snapshot",
]
