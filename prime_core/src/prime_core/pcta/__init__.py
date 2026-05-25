# GPT/Claude generated; context, prompt Erin Spencer
"""PCTA — Prime Circle Tensor Architecture: circle of 7 PCNA tensors, audited as one tensor."""

from .circle import CIRCLE_SIZE, PCTACircle

UI_META = {
    "tab_id": "pcta",
    "label": "PCTA Circle",
    "icon": "Circle",
    "order": 2,
    "sections": [
        {
            "id": "audit",
            "label": "Circle Audit",
            "endpoint": "/api/v1/pcta/audit",
            "fields": [
                {"key": "circle_id",     "type": "badge", "label": "Circle"},
                {"key": "weight_mean",   "type": "gauge", "label": "Weight Mean"},
                {"key": "weight_spread", "type": "gauge", "label": "Weight Spread"},
                {"key": "total_params",  "type": "text",  "label": "Total Params"},
            ],
        },
        {
            "id": "members",
            "label": "Member Norms",
            "endpoint": "/api/v1/pcta/audit",
            "fields": [
                {"key": "weight_norms", "type": "text", "label": "Member L2 Norms"},
                {"key": "param_counts", "type": "text", "label": "Member Params"},
            ],
        },
    ],
}

DATA_SCHEMA = {
    "endpoints": [
        {"method": "GET",  "path": "/api/v1/pcta/audit"},
        {"method": "GET",  "path": "/api/v1/pcta/tensor"},
        {"method": "POST", "path": "/api/v1/pcta/forward"},
    ],
}

__all__ = [
    "CIRCLE_SIZE",
    "DATA_SCHEMA",
    "PCTACircle",
    "UI_META",
]
