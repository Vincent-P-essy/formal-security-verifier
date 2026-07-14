from __future__ import annotations

import json

from formal_security_verifier.benchmark import committed_ground_truth
from formal_security_verifier.models import Method, Verdict
from formal_security_verifier.obligations import OBLIGATIONS, ground_truth
from formal_security_verifier.resources import packaged_path
from formal_security_verifier.verifier import verify, verify_all


def test_every_obligation_matches_expected_verdict() -> None:
    for obligation in OBLIGATIONS:
        result = verify(obligation)
        assert result.verdict is obligation.expect, obligation.id


def test_verified_obligations_are_exhaustive() -> None:
    for result in verify_all():
        if result.verdict is Verdict.VERIFIED:
            assert result.exhaustive is True
            assert result.counterexample is None


def test_refuted_obligations_carry_counterexamples() -> None:
    for result in verify_all():
        if result.verdict is Verdict.REFUTED:
            assert result.counterexample is not None


def test_jwt_replay_counterexample() -> None:
    obligation = next(o for o in OBLIGATIONS if o.id == "jwt-missing-revocation-check")
    result = verify(obligation)
    assert result.verdict is Verdict.REFUTED
    assert result.counterexample is not None
    actions = [step.action for step in result.counterexample.steps]
    assert actions == ["init", "issue", "revoke", "present"]


def test_rbac_counterexample_is_viewer_restricted_read() -> None:
    obligation = next(o for o in OBLIGATIONS if o.id == "rbac-broken-hierarchy")
    result = verify(obligation)
    assert result.method is Method.RELATIONAL
    assert result.counterexample is not None
    assert result.counterexample.assignment == {
        "role": "viewer",
        "action": "read",
        "sensitivity": "restricted",
    }


def test_ground_truth_matches_committed_fixture() -> None:
    committed = json.loads(packaged_path("ground-truth.json").read_text(encoding="utf-8"))
    assert committed == ground_truth() == committed_ground_truth()
