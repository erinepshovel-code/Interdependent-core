# GPT/Claude generated; context, prompt Erin Spencer
"""
EDCM scorer — turns a :class:`ParsedTranscript` into the 9 metric vector
(C / R / D / N / L / O / F / E / I).

The canon ships marker phrase tables and a ``requires_embeddings`` flag
per metric.  This scorer implements the four metrics the canon marks as
**lexically computable** (R, N, L, E) end-to-end, and exposes marker
counts for the five **embedding-dependent** metrics (C, D, O, F, I) so
a downstream embedding-aware host can finish them without re-parsing.

Score shape::

    {
        "C": MetricScore(value=None, marker_counts={...}, requires_embeddings=True),
        "R": MetricScore(value=0.4,  marker_counts={...}, requires_embeddings=False),
        ...
    }

Marker counts are per-category integers; values are floats in [0, 1]
(or ``None`` if embeddings are required).
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from interdependent_lib.edcm.canon import CanonLoader
from interdependent_lib.edcm.parser.turns_rounds import ParsedTranscript, Turn

# Entries longer than this are treated as descriptive notes, not phrases.
_PHRASE_MAX_LEN = 50

# Commitment intensity weights for E.
_COMMITMENT_WEIGHTS = {
    "commitment_low": 1.0,
    "commitment_medium": 2.0,
    "commitment_high": 3.0,
}


@dataclass
class MetricScore:
    """One metric's score on a transcript.

    ``value`` is ``None`` when the metric requires embeddings the scorer
    does not implement; ``marker_counts`` is always populated so an
    embedding-aware caller can finish the computation.
    """

    value: float | None
    marker_counts: dict[str, int] = field(default_factory=dict)
    requires_embeddings: bool = False
    notes: str = ""


def _is_phrase(s: Any) -> bool:
    """Treat short string entries as literal phrases; skip descriptive notes."""
    return isinstance(s, str) and 0 < len(s) <= _PHRASE_MAX_LEN


def _compile_phrase(phrase: str) -> re.Pattern[str]:
    """Word-boundary case-insensitive matcher for a literal phrase."""
    return re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)


class EDCMScorer:
    """Score a :class:`ParsedTranscript` against the 9 EDCM metric families.

    Parameters
    ----------
    canon:
        Optional pre-loaded :class:`CanonLoader`.  A fresh instance is
        constructed if omitted.
    """

    def __init__(self, canon: CanonLoader | None = None) -> None:
        self._canon = canon or CanonLoader()
        self._matchers: dict[str, dict[str, list[re.Pattern[str]]]] = {}
        for metric in self._canon.metric_names():
            info = self._canon.metric_info(metric)
            categories: dict[str, list[re.Pattern[str]]] = {}
            for cat, value in info.get("markers", {}).items():
                if not isinstance(value, list):
                    continue
                phrases = [p for p in value if _is_phrase(p)]
                if phrases:
                    categories[cat] = [_compile_phrase(p) for p in phrases]
            self._matchers[metric] = categories

    # ------------------------------------------------------------------
    # Per-turn marker counts
    # ------------------------------------------------------------------

    def _count_in_text(self, text: str, metric: str) -> Counter[str]:
        """Count marker matches in ``text`` for one metric, by category."""
        result: Counter[str] = Counter()
        for cat, patterns in self._matchers.get(metric, {}).items():
            hits = 0
            for pat in patterns:
                hits += len(pat.findall(text))
            if hits:
                result[cat] = hits
        return result

    def _per_turn_counts(
        self, turns: list[Turn], metric: str
    ) -> list[Counter[str]]:
        return [self._count_in_text(t.text, metric) for t in turns]

    # ------------------------------------------------------------------
    # Metric implementations
    # ------------------------------------------------------------------

    def _score_R(self, turns: list[Turn]) -> MetricScore:
        """R = refusal density = refusals / constraint statements + requests."""
        counts: Counter[str] = Counter()
        for t in turns:
            counts.update(self._count_in_text(t.text, "R"))
        refusals = counts.get("refusal", 0) + counts.get("soft_refusal", 0)
        denominator = counts.get("constraint_statement", 0) + counts.get("request", 0)
        value = refusals / denominator if denominator else 0.0
        return MetricScore(
            value=min(value, 1.0),
            marker_counts=dict(counts),
            requires_embeddings=False,
        )

    def _score_N(self, turns: list[Turn]) -> MetricScore:
        """N = noise = 1 - (resolution markers / constraint markers)."""
        r_counts: Counter[str] = Counter()
        for t in turns:
            r_counts.update(self._count_in_text(t.text, "R"))
            r_counts.update(self._count_in_text(t.text, "N"))
        resolution = r_counts.get("resolution", 0)
        constraints = r_counts.get("constraint_statement", 0) + r_counts.get("request", 0)
        if constraints == 0:
            return MetricScore(
                value=0.0,
                marker_counts={"resolution": resolution, "constraints": 0},
                requires_embeddings=False,
                notes="no constraint markers found; N defaults to 0",
            )
        ratio = resolution / constraints
        value = max(0.0, 1.0 - ratio)
        return MetricScore(
            value=min(value, 1.0),
            marker_counts={"resolution": resolution, "constraints": constraints},
            requires_embeddings=False,
        )

    def _score_L(self, turns: list[Turn]) -> MetricScore:
        """L = load = total constraint tokens per window (proxy by marker count)."""
        counts: Counter[str] = Counter()
        for t in turns:
            counts.update(self._count_in_text(t.text, "L"))
            counts.update(self._count_in_text(t.text, "R"))
        constraints = counts.get("constraint_statement", 0) + counts.get("request", 0)
        amplifiers = counts.get("load_amplifiers", 0)
        # Normalise to [0, 1] by a saturating function so callers can compare.
        raw_load = float(constraints + amplifiers)
        value = 1.0 - (1.0 / (1.0 + raw_load))
        return MetricScore(
            value=value,
            marker_counts={
                "constraint_statement": constraints,
                "load_amplifiers": amplifiers,
                "raw_load": int(raw_load),
            },
            requires_embeddings=False,
        )

    def _score_E(self, turns: list[Turn]) -> MetricScore:
        """E = escalation = sum of positive deltas in commitment intensity."""
        intensities: list[float] = []
        totals: Counter[str] = Counter()
        for t in turns:
            counts = self._count_in_text(t.text, "E")
            totals.update(counts)
            intensity = sum(
                _COMMITMENT_WEIGHTS[level] * counts.get(level, 0)
                for level in _COMMITMENT_WEIGHTS
            )
            deesc = counts.get("deescalation_signals", 0)
            intensities.append(max(0.0, intensity - deesc))
        positive_delta = 0.0
        for prev, curr in zip(intensities, intensities[1:]):
            positive_delta += max(0.0, curr - prev)
        max_possible = max(intensities) if intensities else 0.0
        normaliser = max(max_possible, 1.0)
        value = min(1.0, positive_delta / normaliser) if intensities else 0.0
        return MetricScore(
            value=value,
            marker_counts=dict(totals),
            requires_embeddings=False,
        )

    def _score_embedding_only(
        self, turns: list[Turn], metric: str, notes: str
    ) -> MetricScore:
        """Return marker counts but no value for embedding-dependent metrics."""
        totals: Counter[str] = Counter()
        for t in turns:
            totals.update(self._count_in_text(t.text, metric))
        return MetricScore(
            value=None,
            marker_counts=dict(totals),
            requires_embeddings=True,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, parsed: ParsedTranscript) -> dict[str, MetricScore]:
        """Score a :class:`ParsedTranscript` against all 9 metrics."""
        turns = parsed.turns
        return {
            "C": self._score_embedding_only(
                turns,
                "C",
                "needs semantic contradiction detection (cross-turn)",
            ),
            "R": self._score_R(turns),
            "D": self._score_embedding_only(
                turns,
                "D",
                "needs aboutness measurement (token-vs-constraint similarity)",
            ),
            "N": self._score_N(turns),
            "L": self._score_L(turns),
            "O": self._score_embedding_only(
                turns,
                "O",
                "needs scope-expansion similarity beyond marker counts",
            ),
            "F": self._score_embedding_only(
                turns,
                "F",
                "needs cosine_sim(embed(constraint_t), embed(constraint_{t-1}))",
            ),
            "E": self._score_E(turns),
            "I": self._score_embedding_only(
                turns,
                "I",
                "needs sim(correction_response, expected_response)",
            ),
        }

    def score_text(self, text: str) -> dict[str, MetricScore]:
        """Convenience: parse and score a single plain-text transcript."""
        from interdependent_lib.edcm.parser.turns_rounds import parse_transcript

        parsed = parse_transcript(text, canon=self._canon)
        return self.score(parsed)


def score_transcript(
    parsed: ParsedTranscript,
    *,
    canon: CanonLoader | None = None,
) -> dict[str, MetricScore]:
    """Module-level convenience for one-off scoring."""
    return EDCMScorer(canon).score(parsed)
