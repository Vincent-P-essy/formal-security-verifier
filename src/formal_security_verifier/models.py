"""Serializable result model for verification obligations.

The runtime models a checker consumes — transition systems and relational
predicates — are dataclasses defined next to each engine because they carry
callables. This module holds the frozen, JSON-friendly types that describe an
obligation's outcome: a verdict, how much of the state space was explored, and,
when a property fails, a concrete counterexample.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Method(StrEnum):
    EXPLICIT_STATE = "explicit-state"
    RELATIONAL = "relational"


class Verdict(StrEnum):
    VERIFIED = "verified"
    REFUTED = "refuted"
    INCONCLUSIVE = "inconclusive"


class Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CounterexampleStep(Frozen):
    """One state along a refuting execution trace."""

    index: int = Field(ge=0)
    action: str
    state: dict[str, str]


class Counterexample(Frozen):
    """A concrete witness that a property does not hold.

    For explicit-state checks it is a trace of steps from an initial state to the
    violating state. For relational checks it is a single variable assignment.
    """

    kind: str  # "trace" or "assignment"
    summary: str = Field(max_length=300)
    steps: tuple[CounterexampleStep, ...] = ()
    assignment: dict[str, str] = Field(default_factory=dict)


class VerificationResult(Frozen):
    """The outcome of verifying one obligation."""

    id: str
    title: str
    claim: str = Field(max_length=300)
    method: Method
    verdict: Verdict
    states_explored: int = Field(ge=0)
    exhaustive: bool = False
    counterexample: Counterexample | None = None

    @property
    def proven(self) -> bool:
        return self.verdict is Verdict.VERIFIED
