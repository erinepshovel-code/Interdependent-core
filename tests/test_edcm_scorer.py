"""
Tests for the EDCM 9-metric scorer.

The canon flags four metrics as lexically computable (R, N, L, E) and five
as embedding-dependent (C, D, O, F, I).  The scorer must produce a numeric
score in [0, 1] for the first set and ``None`` for the second, while still
returning marker counts for both.
"""

from __future__ import annotations

import pytest

from interdependent_lib.edcm import (
    EDCMScorer,
    MetricScore,
    parse_transcript,
    score_transcript,
)

LEXICAL_METRICS = {"R", "N", "L", "E"}
EMBEDDING_METRICS = {"C", "D", "O", "F", "I"}


def _parsed(turns):
    return parse_transcript(turns)


def test_score_returns_all_nine_metric_keys():
    scorer = EDCMScorer()
    scores = scorer.score(_parsed([{"speaker": "A", "text": "hello"}]))
    assert set(scores.keys()) == LEXICAL_METRICS | EMBEDDING_METRICS


def test_lexical_metrics_produce_floats_in_unit_interval():
    scorer = EDCMScorer()
    scores = scorer.score(
        _parsed(
            [
                {"speaker": "A", "text": "You must stop. Can you confirm?"},
                {"speaker": "B", "text": "I can't do that."},
                {"speaker": "A", "text": "Fair enough, understood."},
            ]
        )
    )
    for k in LEXICAL_METRICS:
        s = scores[k]
        assert isinstance(s, MetricScore)
        assert s.value is not None
        assert 0.0 <= s.value <= 1.0
        assert s.requires_embeddings is False


def test_embedding_metrics_return_none_value_but_marker_counts_present():
    scorer = EDCMScorer()
    scores = scorer.score(
        _parsed([{"speaker": "A", "text": "I demand you reconsider."}])
    )
    for k in EMBEDDING_METRICS:
        s = scores[k]
        assert s.value is None
        assert s.requires_embeddings is True
        assert isinstance(s.marker_counts, dict)


def test_refusal_score_is_zero_when_no_constraints():
    scorer = EDCMScorer()
    scores = scorer.score(
        _parsed([{"speaker": "A", "text": "Nice weather today."}])
    )
    assert scores["R"].value == 0.0


def test_refusal_score_rises_with_refusals_against_constraints():
    scorer = EDCMScorer()
    no_refuse = scorer.score(
        _parsed(
            [
                {"speaker": "A", "text": "You must do this. Can you?"},
                {"speaker": "B", "text": "Of course."},
            ]
        )
    )
    full_refuse = scorer.score(
        _parsed(
            [
                {"speaker": "A", "text": "You must do this. Can you?"},
                {"speaker": "B", "text": "I refuse. I won't."},
            ]
        )
    )
    assert no_refuse["R"].value == 0.0
    assert full_refuse["R"].value > 0.5


def test_noise_score_falls_when_resolutions_appear():
    scorer = EDCMScorer()
    no_res = scorer.score(
        _parsed(
            [
                {"speaker": "A", "text": "You must comply. You have to act."},
                {"speaker": "B", "text": "Maybe later."},
            ]
        )
    )
    with_res = scorer.score(
        _parsed(
            [
                {"speaker": "A", "text": "You must comply. You have to act."},
                {"speaker": "B", "text": "Agreed. Understood. Fair enough."},
            ]
        )
    )
    assert no_res["N"].value > with_res["N"].value


def test_load_score_grows_monotonically_with_constraint_density():
    scorer = EDCMScorer()
    low = scorer.score(_parsed([{"speaker": "A", "text": "Hello."}]))
    high = scorer.score(
        _parsed(
            [
                {
                    "speaker": "A",
                    "text": (
                        "You must do A. You have to do B. You need to do C. "
                        "And also do D. On top of that, do E."
                    ),
                }
            ]
        )
    )
    assert low["L"].value < high["L"].value


def test_escalation_score_rises_with_commitment_intensity():
    scorer = EDCMScorer()
    flat = scorer.score(
        _parsed(
            [
                {"speaker": "A", "text": "I think we should consider this."},
                {"speaker": "A", "text": "Maybe we should consider this."},
            ]
        )
    )
    rising = scorer.score(
        _parsed(
            [
                {"speaker": "A", "text": "I think we should consider this."},
                {"speaker": "A", "text": "I believe we must act."},
                {"speaker": "A", "text": "I insist. I demand action now."},
            ]
        )
    )
    assert rising["E"].value > flat["E"].value


def test_escalation_score_drops_with_deescalation_phrases():
    scorer = EDCMScorer()
    rising = scorer.score(
        _parsed(
            [
                {"speaker": "A", "text": "I think this matters."},
                {"speaker": "A", "text": "I insist this matters."},
            ]
        )
    )
    rising_then_deesc = scorer.score(
        _parsed(
            [
                {"speaker": "A", "text": "I think this matters."},
                {"speaker": "A", "text": "I insist this matters."},
                {"speaker": "B", "text": "Let's take a step back. I hear you."},
            ]
        )
    )
    # Either equal (no further rise) or strictly lower.
    assert rising_then_deesc["E"].value <= rising["E"].value


def test_module_level_score_transcript_helper():
    parsed = _parsed([{"speaker": "A", "text": "You must act. I refuse."}])
    scores = score_transcript(parsed)
    assert scores["R"].value > 0


def test_score_text_convenience():
    scorer = EDCMScorer()
    scores = scorer.score_text("A: You must.\nB: I refuse.")
    assert scores["R"].value > 0
    assert scores["L"].value > 0


def test_scorer_uses_provided_canon():
    """Pre-loading a CanonLoader avoids re-loading JSON for repeat scoring."""
    from interdependent_lib.edcm.canon import CanonLoader

    canon = CanonLoader()
    scorer = EDCMScorer(canon=canon)
    # Use a known-refusal phrase to confirm matchers were built from this canon.
    scores = scorer.score(_parsed([{"speaker": "A", "text": "I refuse."}]))
    assert "refusal" in scores["R"].marker_counts


def test_noise_default_when_no_constraints():
    scorer = EDCMScorer()
    scores = scorer.score(_parsed([{"speaker": "A", "text": "hello."}]))
    assert scores["N"].value == 0.0
    assert "no constraint" in scores["N"].notes
