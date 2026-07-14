"""Exhaustive relational (Alloy-style) property checking.

A :class:`RelationalCheck` declares finite sorts and a property that must hold
for every assignment drawn from their product. :func:`check_relational`
enumerates the entire product and evaluates the property, so a pass is a proof
over the bounded universe and a failure returns the exact assignment that breaks
it. This suits stateless facts — an access-control matrix, a detection-rule
coverage claim — where the question is "does this hold for all combinations?"
rather than "is a bad state reachable?".
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class RelationalCheck:
    name: str
    domains: dict[str, Sequence[Hashable]]
    prop: Callable[[dict[str, Hashable]], bool]
    claim: str


@dataclass(frozen=True)
class RelationalOutcome:
    holds: bool
    assignments_checked: int
    counterexample: dict[str, Hashable] | None = None


def check_relational(check: RelationalCheck) -> RelationalOutcome:
    """Evaluate the property over the full product of the declared sorts."""

    names = list(check.domains)
    domains = [list(check.domains[name]) for name in names]
    checked = 0
    for combination in product(*domains):
        assignment = dict(zip(names, combination, strict=True))
        checked += 1
        if not check.prop(assignment):
            return RelationalOutcome(
                holds=False, assignments_checked=checked, counterexample=assignment
            )
    return RelationalOutcome(holds=True, assignments_checked=checked)
