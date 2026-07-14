"""Explicit-state safety model checking.

A :class:`TransitionSystem` is a set of initial variable assignments, a list of
guarded actions, and a safety invariant. :func:`check` performs a breadth-first
reachability search: it explores every state reachable from an initial state and
checks the invariant at each. If a reachable state violates the invariant it
returns the shortest witnessing trace; if the entire reachable state space is
explored with the invariant intact, the property is *proven* for the model — not
merely bounded — because the search was exhaustive over a finite space.

BFS also yields the shortest counterexample, which is the most useful one to
read. A ``max_states`` guard keeps an accidentally infinite model from running
forever; hitting it yields an inconclusive result rather than a false proof.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Hashable, Mapping
from dataclasses import dataclass

Assignment = Mapping[str, Hashable]
State = tuple[tuple[str, Hashable], ...]


def freeze(assignment: Assignment) -> State:
    return tuple(sorted(assignment.items()))


def thaw(state: State) -> dict[str, Hashable]:
    return dict(state)


@dataclass(frozen=True)
class Action:
    name: str
    guard: Callable[[dict[str, Hashable]], bool]
    effect: Callable[[dict[str, Hashable]], dict[str, Hashable]]


@dataclass(frozen=True)
class TransitionSystem:
    name: str
    initial: tuple[Assignment, ...]
    actions: tuple[Action, ...]
    invariant: Callable[[dict[str, Hashable]], bool]
    invariant_name: str


@dataclass(frozen=True)
class TraceStep:
    action: str
    state: dict[str, Hashable]


@dataclass(frozen=True)
class CheckOutcome:
    holds: bool
    exhaustive: bool
    states_explored: int
    trace: tuple[TraceStep, ...] = ()


def check(system: TransitionSystem, *, max_states: int = 100_000) -> CheckOutcome:
    """Exhaustively explore reachable states and check the invariant."""

    visited: set[State] = set()
    predecessor: dict[State, tuple[State, str]] = {}
    queue: deque[State] = deque()

    for assignment in system.initial:
        state = freeze(assignment)
        if state not in visited:
            visited.add(state)
            queue.append(state)

    # Check initial states first so a violated initial condition is caught.
    for state in list(queue):
        if not system.invariant(dict(thaw(state))):
            return CheckOutcome(
                holds=False,
                exhaustive=False,
                states_explored=len(visited),
                trace=_trace(state, predecessor),
            )

    while queue:
        if len(visited) > max_states:
            return CheckOutcome(holds=True, exhaustive=False, states_explored=len(visited))
        state = queue.popleft()
        current = thaw(state)
        for action in system.actions:
            if not action.guard(current):
                continue
            nxt = action.effect(dict(current))
            frozen = freeze(nxt)
            if frozen in visited:
                continue
            visited.add(frozen)
            predecessor[frozen] = (state, action.name)
            if not system.invariant(nxt):
                return CheckOutcome(
                    holds=False,
                    exhaustive=False,
                    states_explored=len(visited),
                    trace=_trace(frozen, predecessor),
                )
            queue.append(frozen)

    return CheckOutcome(holds=True, exhaustive=True, states_explored=len(visited))


def _trace(state: State, predecessor: dict[State, tuple[State, str]]) -> tuple[TraceStep, ...]:
    steps: list[TraceStep] = []
    cursor: State | None = state
    while cursor is not None:
        parent = predecessor.get(cursor)
        action = parent[1] if parent is not None else "init"
        steps.append(TraceStep(action=action, state=thaw(cursor)))
        cursor = parent[0] if parent is not None else None
    steps.reverse()
    return tuple(steps)
