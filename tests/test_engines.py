from __future__ import annotations

from collections.abc import Hashable

from formal_security_verifier.kripke import Action, TransitionSystem, check
from formal_security_verifier.relational import RelationalCheck, check_relational

State = dict[str, Hashable]


def _counter_system(limit: int, invariant_bound: int) -> TransitionSystem:
    return TransitionSystem(
        name="counter",
        initial=({"x": 0},),
        actions=(Action("inc", lambda s: int(s["x"]) < limit, lambda s: {"x": int(s["x"]) + 1}),),
        invariant=lambda s: int(s["x"]) < invariant_bound,
        invariant_name="x stays below bound",
    )


def test_exhaustive_proof() -> None:
    outcome = check(_counter_system(limit=2, invariant_bound=5))
    assert outcome.holds is True
    assert outcome.exhaustive is True
    assert outcome.states_explored == 3  # x in {0,1,2}


def test_counterexample_trace() -> None:
    outcome = check(_counter_system(limit=5, invariant_bound=3))
    assert outcome.holds is False
    # init x=0, inc->1, inc->2, inc->3 (violates)
    assert [step.action for step in outcome.trace] == ["init", "inc", "inc", "inc"]
    assert outcome.trace[-1].state["x"] == 3


def test_initial_state_violation() -> None:
    system = TransitionSystem(
        name="bad-init",
        initial=({"x": 5},),
        actions=(),
        invariant=lambda s: int(s["x"]) < 3,
        invariant_name="x below three",
    )
    outcome = check(system)
    assert outcome.holds is False
    assert len(outcome.trace) == 1


def test_max_states_is_inconclusive() -> None:
    outcome = check(_counter_system(limit=1_000, invariant_bound=10_000), max_states=10)
    assert outcome.holds is True
    assert outcome.exhaustive is False


def test_relational_holds_and_refutes() -> None:
    holding = RelationalCheck(
        name="ok",
        domains={"a": (1, 2, 3)},
        prop=lambda x: int(x["a"]) > 0,
        claim="all positive",
    )
    assert check_relational(holding).holds is True

    failing = RelationalCheck(
        name="bad",
        domains={"a": (1, 2, 3), "b": (0, 1)},
        prop=lambda x: not (int(x["a"]) == 2 and int(x["b"]) == 0),
        claim="never (2, 0)",
    )
    outcome = check_relational(failing)
    assert outcome.holds is False
    assert outcome.counterexample == {"a": 2, "b": 0}
