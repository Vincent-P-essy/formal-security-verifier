"""Dispatch an obligation to the right engine and shape the result.

Explicit-state obligations go to the reachability checker and, on failure, carry
the shortest witnessing trace. Relational obligations go to the exhaustive
predicate checker and, on failure, carry the single breaking assignment.
"""

from __future__ import annotations

from .kripke import check
from .models import (
    Counterexample,
    CounterexampleStep,
    Method,
    Verdict,
    VerificationResult,
)
from .obligations import OBLIGATIONS, Obligation
from .relational import check_relational


def _stringify(state: dict[str, object]) -> dict[str, str]:
    return {key: str(value) for key, value in state.items()}


def verify(obligation: Obligation) -> VerificationResult:
    """Verify one obligation and return its result."""

    if obligation.method is Method.EXPLICIT_STATE:
        assert obligation.system is not None
        outcome = check(obligation.system)
        verdict = Verdict.VERIFIED if outcome.holds else Verdict.REFUTED
        counterexample = None
        if not outcome.holds:
            steps = tuple(
                CounterexampleStep(index=i, action=step.action, state=_stringify(dict(step.state)))
                for i, step in enumerate(outcome.trace)
            )
            counterexample = Counterexample(
                kind="trace",
                summary=(
                    f"{obligation.system.invariant_name} violated after {len(steps) - 1} step(s)"
                ),
                steps=steps,
            )
        return VerificationResult(
            id=obligation.id,
            title=obligation.title,
            claim=obligation.claim,
            method=obligation.method,
            verdict=verdict,
            states_explored=outcome.states_explored,
            exhaustive=outcome.exhaustive,
            counterexample=counterexample,
        )

    assert obligation.relational is not None
    rel = check_relational(obligation.relational)
    rel_verdict = Verdict.VERIFIED if rel.holds else Verdict.REFUTED
    counterexample = None
    if not rel.holds and rel.counterexample is not None:
        assignment = _stringify(dict(rel.counterexample))
        counterexample = Counterexample(
            kind="assignment",
            summary="property fails for " + ", ".join(f"{k}={v}" for k, v in assignment.items()),
            assignment=assignment,
        )
    return VerificationResult(
        id=obligation.id,
        title=obligation.title,
        claim=obligation.claim,
        method=obligation.method,
        verdict=rel_verdict,
        states_explored=rel.assignments_checked,
        exhaustive=rel.holds,
        counterexample=counterexample,
    )


def verify_all() -> list[VerificationResult]:
    return [verify(obligation) for obligation in OBLIGATIONS]
