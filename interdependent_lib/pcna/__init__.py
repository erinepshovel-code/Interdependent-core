# GPT/Claude generated; context, prompt Erin Spencer
"""PCNA — back-propagating neural network: the base tensor layer."""

from .activations import apply, apply_grad
from .layer import PCNALayer
from .network import PCNANetwork

UI_META = {
    "tab_id": "pcna",
    "label": "PCNA Network",
    "icon": "Brain",
    "order": 1,
    "sections": [
        {
            "id": "config",
            "label": "Network Configuration",
            "endpoint": "/api/v1/pcna/state",
            "fields": [
                {"key": "layer_sizes",     "type": "text",  "label": "Layer Sizes"},
                {"key": "activations",     "type": "text",  "label": "Activations"},
                {"key": "parameter_count", "type": "text",  "label": "Parameters"},
            ],
        },
        {
            "id": "training",
            "label": "Training Signal",
            "endpoint": "/api/v1/pcna/state",
            "fields": [
                {"key": "last_loss",     "type": "gauge", "label": "Last Loss"},
                {"key": "last_grad_norm","type": "gauge", "label": "Gradient Norm"},
                {"key": "last_lr",       "type": "text",  "label": "Learning Rate"},
            ],
        },
    ],
}

DATA_SCHEMA = {
    "endpoints": [
        {"method": "GET",  "path": "/api/v1/pcna/state"},
        {"method": "POST", "path": "/api/v1/pcna/forward"},
        {"method": "POST", "path": "/api/v1/pcna/backward"},
        {"method": "POST", "path": "/api/v1/pcna/update"},
    ],
}

__all__ = [
    "DATA_SCHEMA",
    "PCNALayer",
    "PCNANetwork",
    "UI_META",
    "apply",
    "apply_grad",
]
