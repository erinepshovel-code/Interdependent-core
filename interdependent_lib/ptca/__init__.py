# GPT/Claude generated; context, prompt Erin Spencer
"""PTCA — Prime Tensor Circular Architecture: prime-indexed tensor, sentinel channels, exchange routing."""

from .constants import (
    AGG6,
    AGG_SEEDS,
    ALPHA,
    BETA,
    DELTA,
    GAMMA,
    NODES,
    PHASES,
    SENTINEL_INDEX,
    SENTINEL_NAMES,
    SENTINEL_WEIGHTS,
    SENTINELS,
    SLOTS,
)
from .core import CORE_SEEDS, DEFAULT_SENTINEL_INDICES, PTCACore, SENTINEL_SEED_COUNT
from .exchange import Exchange, ExchangeResult, aggregate_identity, aggregate_seeds, compute_score
from .instance import PTCAInstance
from .primes import PRIME_NODES, PRIME_TO_NODE, is_prime_node, node_for_prime, prime_for_node
from .provenance import (
    build_block,
    chain_hashes,
    extend_chain,
    hash_block,
    verify_chain,
)
from .seed import SEED_CIRCLES, PTCASeed
from .sentinels import (
    S1ProvenanceState,
    S2PolicyState,
    S3BoundsState,
    S4ApprovalState,
    S5ContextState,
    S6IdentityState,
    S7MemoryState,
    S8RiskState,
    S9AuditState,
    SentinelState,
)
from .tensor import PTCATensor

UI_META = {
    "tab_id": "ptca",
    "label": "PTCA Core",
    "icon": "Hexagon",
    "order": 3,
    "sections": [
        {
            "id": "instance",
            "label": "Instance State",
            "endpoint": "/api/v1/ptca/state",
            "fields": [
                {"key": "session_id",   "type": "text",  "label": "Session"},
                {"key": "model_id",     "type": "text",  "label": "Model"},
                {"key": "caller_id",    "type": "text",  "label": "Caller"},
                {"key": "approved",     "type": "badge", "label": "Approved"},
                {"key": "risk_score",   "type": "gauge", "label": "Risk"},
            ],
        },
        {
            "id": "sentinels",
            "label": "Sentinel Channels",
            "endpoint": "/api/v1/ptca/state",
            "fields": [
                {"key": "S5_CONTEXT.token_count", "type": "text",  "label": "S5 Tokens"},
                {"key": "S7_MEMORY.store",       "type": "text",  "label": "S7 Memory"},
                {"key": "S8_RISK.score",         "type": "gauge", "label": "S8 Risk"},
                {"key": "S9_AUDIT.log",          "type": "text",  "label": "S9 Audit Entries"},
            ],
        },
        {
            "id": "core",
            "label": "Hosted Core",
            "endpoint": "/api/v1/ptca/core/audit",
            "fields": [
                {"key": "seed_count",            "type": "text",  "label": "Seeds"},
                {"key": "sentinel_seed_count",   "type": "text",  "label": "Sentinel Seeds"},
                {"key": "channel_count",         "type": "text",  "label": "Channels"},
                {"key": "tensor_size",           "type": "text",  "label": "Tensor Size"},
                {"key": "mean_of_seed_means",    "type": "gauge", "label": "Mean Weight"},
                {"key": "max_seed_spread",       "type": "gauge", "label": "Max Spread"},
            ],
        },
    ],
}

DATA_SCHEMA = {
    "endpoints": [
        {"method": "GET",  "path": "/api/v1/ptca/state"},
        {"method": "POST", "path": "/api/v1/ptca/route"},
        {"method": "POST", "path": "/api/v1/ptca/approve"},
        {"method": "POST", "path": "/api/v1/ptca/revoke"},
        {"method": "GET",  "path": "/api/v1/ptca/audit"},
        {"method": "GET",  "path": "/api/v1/ptca/core/audit"},
        {"method": "GET",  "path": "/api/v1/ptca/core/tensor"},
    ],
}

__all__ = [
    "DATA_SCHEMA",
    "UI_META",
    "AGG6",
    "AGG_SEEDS",
    "ALPHA",
    "BETA",
    "CORE_SEEDS",
    "DEFAULT_SENTINEL_INDICES",
    "DELTA",
    "GAMMA",
    "NODES",
    "PHASES",
    "PRIME_NODES",
    "PRIME_TO_NODE",
    "PTCACore",
    "PTCAInstance",
    "PTCASeed",
    "PTCATensor",
    "SEED_CIRCLES",
    "SENTINEL_SEED_COUNT",
    "S1ProvenanceState",
    "S2PolicyState",
    "S3BoundsState",
    "S4ApprovalState",
    "S5ContextState",
    "S6IdentityState",
    "S7MemoryState",
    "S8RiskState",
    "S9AuditState",
    "SENTINEL_INDEX",
    "SENTINEL_NAMES",
    "SENTINEL_WEIGHTS",
    "SENTINELS",
    "SLOTS",
    "SentinelState",
    "Exchange",
    "ExchangeResult",
    "aggregate_identity",
    "aggregate_seeds",
    "build_block",
    "chain_hashes",
    "compute_score",
    "extend_chain",
    "hash_block",
    "is_prime_node",
    "node_for_prime",
    "prime_for_node",
    "verify_chain",
]
