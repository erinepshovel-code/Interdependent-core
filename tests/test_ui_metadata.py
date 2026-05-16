"""
Tests for the a0-style UI_META / DATA_SCHEMA convention applied to every
subsystem, plus the top-level ``ui_structure()`` aggregator.

The convention is:

    UI_META = {"tab_id", "label", "icon", "order", "sections": [...]}
    DATA_SCHEMA = {"endpoints": [{"method": ..., "path": ...}, ...]}
"""

from __future__ import annotations

import interdependent_lib
from interdependent_lib import edcm, pcna, pcta, ptca


VALID_FIELD_TYPES = {"text", "gauge", "badge"}
VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

# Subsystems we expect to always be present (stdlib-only).
ALWAYS_PRESENT = [pcna, pcta, ptca, edcm]


def _check_ui_meta(meta: dict) -> None:
    assert isinstance(meta["tab_id"], str) and meta["tab_id"]
    assert isinstance(meta["label"], str) and meta["label"]
    assert isinstance(meta["icon"], str) and meta["icon"]
    assert isinstance(meta["order"], int)
    assert isinstance(meta["sections"], list) and meta["sections"]
    for section in meta["sections"]:
        assert isinstance(section["id"], str) and section["id"]
        assert isinstance(section["label"], str) and section["label"]
        assert section["endpoint"].startswith("/api/v1/")
        assert isinstance(section["fields"], list) and section["fields"]
        for field in section["fields"]:
            assert isinstance(field["key"], str) and field["key"]
            assert field["type"] in VALID_FIELD_TYPES
            assert isinstance(field["label"], str) and field["label"]


def _check_data_schema(schema: dict) -> None:
    assert isinstance(schema["endpoints"], list) and schema["endpoints"]
    for ep in schema["endpoints"]:
        assert ep["method"] in VALID_METHODS
        assert ep["path"].startswith("/api/v1/")


def test_every_subpackage_declares_ui_meta_and_data_schema():
    for mod in ALWAYS_PRESENT:
        assert hasattr(mod, "UI_META"), f"{mod.__name__} missing UI_META"
        assert hasattr(mod, "DATA_SCHEMA"), f"{mod.__name__} missing DATA_SCHEMA"
        _check_ui_meta(mod.UI_META)
        _check_data_schema(mod.DATA_SCHEMA)


def test_pcea_and_guardian_declare_metadata_when_available():
    if interdependent_lib.pcea is None:
        return
    _check_ui_meta(interdependent_lib.pcea.UI_META)
    _check_data_schema(interdependent_lib.pcea.DATA_SCHEMA)
    assert interdependent_lib.guardian is not None
    _check_ui_meta(interdependent_lib.guardian.UI_META)
    _check_data_schema(interdependent_lib.guardian.DATA_SCHEMA)


def test_tab_ids_are_unique():
    tab_ids = []
    for mod in ALWAYS_PRESENT + [interdependent_lib.pcea, interdependent_lib.guardian]:
        if mod is None:
            continue
        tab_ids.append(mod.UI_META["tab_id"])
    assert len(tab_ids) == len(set(tab_ids)), tab_ids


def test_ui_structure_aggregates_and_orders_modules():
    structure = interdependent_lib.ui_structure()
    assert isinstance(structure, dict)
    assert "modules" in structure
    modules = structure["modules"]
    assert modules, "ui_structure must return at least the stdlib subsystems"

    names = [m["name"] for m in modules]
    # PCNA -> PCTA -> PTCA -> EDCM order required by UI_META["order"].
    pcna_i = names.index("pcna")
    pcta_i = names.index("pcta")
    ptca_i = names.index("ptca")
    edcm_i = names.index("edcm")
    assert pcna_i < pcta_i < ptca_i < edcm_i

    # Each entry carries both halves of the contract.
    for entry in modules:
        assert set(entry.keys()) == {"name", "ui_meta", "data_schema"}
        _check_ui_meta(entry["ui_meta"])
        _check_data_schema(entry["data_schema"])


def test_ui_structure_includes_pcea_and_guardian_when_available():
    if interdependent_lib.pcea is None:
        return
    names = [m["name"] for m in interdependent_lib.ui_structure()["modules"]]
    assert "pcea" in names
    assert "guardian" in names
    # Guardian last (order=6).
    assert names[-1] == "guardian"


def test_data_schema_paths_match_ui_meta_endpoint_prefixes():
    """Each module's UI_META endpoints should share its DATA_SCHEMA's API prefix."""
    for mod in ALWAYS_PRESENT:
        prefix_tokens = {ep["path"].split("/")[3] for ep in mod.DATA_SCHEMA["endpoints"]}
        # All section endpoints live under the same prefix segment.
        section_tokens = {
            section["endpoint"].split("/")[3]
            for section in mod.UI_META["sections"]
        }
        assert section_tokens.issubset(prefix_tokens), (
            f"{mod.__name__}: UI endpoint segments {section_tokens} "
            f"not covered by DATA_SCHEMA segments {prefix_tokens}"
        )
