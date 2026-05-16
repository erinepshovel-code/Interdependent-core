# GPT/Claude generated; context, prompt Erin Spencer
"""
Guardian adapter: bridges PTCA session state and PCEA encryption.

PCEA seals a strongly-typed :class:`LiveState` dataclass.  PTCA produces
session snapshots via :meth:`PTCAInstance.snapshot` and structural state
via :meth:`PTCACore.audit`.  This module packs those PTCA payloads into
a ``LiveState`` so they can be sealed/unsealed end-to-end in one call.

The packing is deterministic and round-trippable:

    pack_snapshot(snapshot, epoch=N) -> LiveState
    unpack_snapshot(LiveState)       -> snapshot

LiveState fields not used by the snapshot carry stable placeholder values
(zeroed spiral, empty cores/transport, coherence=1.0, last_renorm=0.0) so
that two packs of the same payload produce identical LiveState objects.

Sealing a :class:`PTCAInstance`
-------------------------------
::

    from interdependent_lib.guardian import seal_instance, unseal_instance
    sealed, live_key = seal_instance(
        inst,
        ikm=b"...32+ bytes of entropy...",
        epoch=1,
        key_id="k1",
        guardian_node_id="g0",
        sealed_by="g0",
        seal_counter=0,
    )
    snapshot = unseal_instance(sealed, live_key)

The function returns the live key so the caller can wipe it after use::

    from interdependent_lib.pcea import wipe
    wipe(live_key)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from interdependent_lib.pcea.guardian import seal_live_state, unseal_live_state
from interdependent_lib.pcea.kdf import derive_keys
from interdependent_lib.pcea.types import LiveState, SealedState

if TYPE_CHECKING:
    from interdependent_lib.ptca.instance import PTCAInstance


_SPIRAL_DEFAULT: dict[str, float] = {"phase": 0.0, "magnitude": 0.0, "base": 0.0}


def pack_snapshot(snapshot: dict[str, Any], *, epoch: int) -> LiveState:
    """
    Pack a PTCA snapshot dict into a :class:`LiveState`.

    The snapshot is stored verbatim in ``cores`` so all of its
    structure round-trips through JSON serialisation.  Unused
    LiveState fields are populated with stable placeholders so two
    packs of the same input produce equal LiveState objects.
    """
    return LiveState(
        epoch=epoch,
        spiral=dict(_SPIRAL_DEFAULT),
        cores={"snapshot": snapshot},
        density_matrix=None,
        coherence=1.0,
        transport=None,
        last_renorm=0.0,
    )


def unpack_snapshot(state: LiveState) -> dict[str, Any]:
    """Inverse of :func:`pack_snapshot`."""
    cores = state.cores or {}
    if "snapshot" not in cores:
        raise ValueError(
            "LiveState.cores does not contain a 'snapshot' field; "
            "this LiveState was not produced by pack_snapshot()."
        )
    return cores["snapshot"]


def seal_snapshot(
    snapshot: dict[str, Any],
    *,
    ikm: bytes,
    epoch: int,
    key_id: str,
    guardian_node_id: str,
    sealed_by: str,
    seal_counter: int = 0,
) -> tuple[SealedState, bytes]:
    """
    Derive a fresh live key from ``ikm`` and seal ``snapshot``.

    Returns ``(sealed, live_key)``.  The caller is responsible for
    wiping ``live_key`` after use via :func:`interdependent_lib.pcea.wipe`.
    """
    live_key, _meta_key = derive_keys(ikm, epoch, key_id, guardian_node_id)
    state = pack_snapshot(snapshot, epoch=epoch)
    sealed = seal_live_state(
        state,
        live_key,
        epoch=epoch,
        key_id=key_id,
        seal_counter=seal_counter,
        guardian_node_id=guardian_node_id,
        sealed_by=sealed_by,
    )
    return sealed, live_key


def unseal_snapshot(sealed: SealedState, live_key: bytes) -> dict[str, Any]:
    """Decrypt a sealed PTCA snapshot back to its original dict."""
    state = unseal_live_state(sealed, live_key)
    return unpack_snapshot(state)


def seal_instance(
    instance: "PTCAInstance",
    *,
    ikm: bytes,
    epoch: int,
    key_id: str,
    guardian_node_id: str,
    sealed_by: str,
    seal_counter: int = 0,
) -> tuple[SealedState, bytes]:
    """Snapshot ``instance`` and seal it via PCEA."""
    return seal_snapshot(
        instance.snapshot(),
        ikm=ikm,
        epoch=epoch,
        key_id=key_id,
        guardian_node_id=guardian_node_id,
        sealed_by=sealed_by,
        seal_counter=seal_counter,
    )


def unseal_instance(sealed: SealedState, live_key: bytes) -> dict[str, Any]:
    """Alias of :func:`unseal_snapshot` for symmetry with :func:`seal_instance`."""
    return unseal_snapshot(sealed, live_key)
