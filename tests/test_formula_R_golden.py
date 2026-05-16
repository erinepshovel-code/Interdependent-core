"""Golden test for metric R canon formula patch."""

import json
from pathlib import Path

from interdependent_lib.edcmbone.behavioral.formula_eval import evaluate

REPO = Path(__file__).resolve().parents[1]
CANON = REPO / "interdependent_lib/edcmbone/canon/behavioral/_R_patch.json"
FIXTURE = REPO / "tests/fixtures/r_golden_001.json"
GOLDEN = REPO / "tests/golden/r_golden_001.json"


def test_R_matches_golden():
    canon = json.loads(CANON.read_text())
    fixture = json.loads(FIXTURE.read_text())
    golden = json.loads(GOLDEN.read_text())
    got = evaluate(canon["formula"], fixture["variables"])
    assert abs(got - golden["expected"]) < 1e-9, (
        f"R drift: got {got}, expected {golden['expected']}"
    )


def test_formula_eval_rejects_attribute_access():
    try:
        evaluate("().__class__", {})
    except ValueError as exc:
        assert "forbidden" in str(exc) or "only direct" in str(exc)
    else:
        raise AssertionError("attribute access must be rejected")


def test_formula_eval_rejects_unknown_functions():
    try:
        evaluate("eval(1)", {})
    except NameError as exc:
        assert "unknown function" in str(exc)
    else:
        raise AssertionError("unknown functions must be rejected")


if __name__ == "__main__":
    test_R_matches_golden()
    print("R golden test: PASS")
