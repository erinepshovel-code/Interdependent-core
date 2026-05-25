"""Deprecated — use :mod:`prime_core.theta`.

The guardian role (sealing PTCA state through PCEA) is provided by the
theta bridge. This module re-exports theta's public API and emits a
:class:`DeprecationWarning` on import. It will be removed in a future
release.
"""

from __future__ import annotations

import warnings

from prime_core.theta import (
    pack_snapshot,
    seal_instance,
    seal_snapshot,
    unpack_snapshot,
    unseal_instance,
    unseal_snapshot,
)

warnings.warn(
    "prime_core.guardian is deprecated; use prime_core.theta instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "pack_snapshot",
    "seal_instance",
    "seal_snapshot",
    "unpack_snapshot",
    "unseal_instance",
    "unseal_snapshot",
]
