# GPT/Claude generated; context, prompt Erin Spencer
"""EDCM — Energy Dissonance Circuit Model: bone inventory, marker tables, and transcript parser."""

from .bones import affixes, bone_set, bones, meta, multiword_joins, punctuation, words_by_family
from .canon import CanonLoader
from .markers import family, marker_set, markers
from .parser.turns_rounds import (
    BoneToken,
    FleshToken,
    ParsedTranscript,
    Round,
    Turn,
    parse_transcript,
)

UI_META = {
    "tab_id": "edcm",
    "label": "EDCM Parser",
    "icon": "Network",
    "order": 5,
    "sections": [
        {
            "id": "canon",
            "label": "Canon Counts",
            "endpoint": "/api/v1/edcm/canon",
            "fields": [
                {"key": "bone_count",      "type": "text", "label": "Bones"},
                {"key": "multiword_count", "type": "text", "label": "Multiword Joins"},
                {"key": "affix_count",     "type": "text", "label": "Affixes"},
                {"key": "punct_count",     "type": "text", "label": "Punctuation"},
                {"key": "marker_count",    "type": "text", "label": "Markers"},
            ],
        },
        {
            "id": "families",
            "label": "PKQTS Family Counts",
            "endpoint": "/api/v1/edcm/parse",
            "fields": [
                {"key": "family_counts.P", "type": "gauge", "label": "P (Polarity)"},
                {"key": "family_counts.K", "type": "gauge", "label": "K (Conditional)"},
                {"key": "family_counts.Q", "type": "gauge", "label": "Q (Quantity)"},
                {"key": "family_counts.T", "type": "gauge", "label": "T (Temporal)"},
                {"key": "family_counts.S", "type": "gauge", "label": "S (Structural)"},
            ],
        },
        {
            "id": "rounds",
            "label": "Parse Stats",
            "endpoint": "/api/v1/edcm/parse",
            "fields": [
                {"key": "round_count", "type": "text", "label": "Rounds"},
                {"key": "turn_count",  "type": "text", "label": "Turns"},
                {"key": "bone_count",  "type": "text", "label": "Bone Tokens"},
                {"key": "speakers",    "type": "text", "label": "Speakers"},
            ],
        },
    ],
}

DATA_SCHEMA = {
    "endpoints": [
        {"method": "GET",  "path": "/api/v1/edcm/canon"},
        {"method": "POST", "path": "/api/v1/edcm/parse"},
        {"method": "GET",  "path": "/api/v1/edcm/markers"},
        {"method": "GET",  "path": "/api/v1/edcm/bones"},
    ],
}

__all__ = [
    "DATA_SCHEMA",
    "UI_META",
    # bones
    "affixes",
    "bone_set",
    "bones",
    "meta",
    "multiword_joins",
    "punctuation",
    "words_by_family",
    # canon
    "CanonLoader",
    # markers
    "family",
    "marker_set",
    "markers",
    # parser
    "BoneToken",
    "FleshToken",
    "ParsedTranscript",
    "Round",
    "Turn",
    "parse_transcript",
]
