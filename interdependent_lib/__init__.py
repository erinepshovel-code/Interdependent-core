# GPT/Claude generated; context, prompt Erin Spencer
# Date: 2026-04-06

"""interdependent-lib — unified PCNA/PCTA/PTCA/PCEA/EDCM library."""

from typing import Any

from . import edcm, pcna, pcta, ptca

__version__ = "0.1.0"
__all__ = ["edcm", "pcna", "pcta", "ptca", "ui_structure"]

# pcea depends on the third-party `cryptography` package. Import it lazily so
# environments without a working `cryptography` install can still use the
# stdlib-only subpackages.
try:
    from . import guardian, pcea  # noqa: F401
except Exception:  # pragma: no cover - import guard
    pcea = None  # type: ignore[assignment]
    guardian = None  # type: ignore[assignment]
else:
    __all__.extend(["pcea", "guardian"])


def ui_structure() -> dict[str, Any]:
    """Aggregate ``UI_META`` + ``DATA_SCHEMA`` from every available subsystem.

    Mirrors the a0 ``/api/v1/ui/structure`` convention so a host application
    can mount this library's modules into its console without hardcoding
    tab definitions.

    Returns
    -------
    dict
        ``{"modules": [{"name": str, "ui_meta": dict, "data_schema": dict}, ...]}``,
        ordered by each module's ``UI_META["order"]``.
    """
    candidates: list[tuple[str, Any]] = [
        ("pcna", pcna),
        ("pcta", pcta),
        ("ptca", ptca),
        ("edcm", edcm),
    ]
    if pcea is not None:
        candidates.append(("pcea", pcea))
    if guardian is not None:
        candidates.append(("guardian", guardian))

    modules: list[dict[str, Any]] = []
    for name, mod in candidates:
        ui_meta = getattr(mod, "UI_META", None)
        data_schema = getattr(mod, "DATA_SCHEMA", None)
        if ui_meta is None or data_schema is None:
            continue
        modules.append({
            "name": name,
            "ui_meta": ui_meta,
            "data_schema": data_schema,
        })
    modules.sort(key=lambda m: m["ui_meta"].get("order", 0))
    return {"modules": modules}
