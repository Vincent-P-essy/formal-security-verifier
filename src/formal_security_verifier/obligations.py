"""The catalogue of security properties to verify.

Each obligation pairs a claim with a model and the verdict a reviewer expects.
Four model correct designs and must be proven; three model deliberately broken
variants and must be refuted with a concrete counterexample. Proving the correct
designs and catching the broken ones is the whole point: it shows the checker
distinguishes a safe design from an unsafe one rather than rubber-stamping both.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass

from .kripke import Action, TransitionSystem
from .models import Method, Verdict
from .relational import RelationalCheck

State = dict[str, Hashable]


@dataclass(frozen=True)
class Obligation:
    id: str
    title: str
    claim: str
    method: Method
    expect: Verdict
    system: TransitionSystem | None = None
    relational: RelationalCheck | None = None


# --- JWT revocation ---------------------------------------------------------


def _jwt_system(*, checks_revocation: bool) -> TransitionSystem:
    initial = ({"issued": False, "revoked": False, "decision": "none"},)

    def present(state: State) -> State:
        accepted = (
            state["issued"] if not checks_revocation else (state["issued"] and not state["revoked"])
        )
        return {**state, "decision": "accept" if accepted else "reject"}

    actions = (
        Action(
            "issue",
            lambda s: not s["issued"],
            lambda s: {**s, "issued": True, "decision": "none"},
        ),
        Action(
            "revoke",
            lambda s: bool(s["issued"]) and not s["revoked"],
            lambda s: {**s, "revoked": True, "decision": "none"},
        ),
        Action("present", lambda s: bool(s["issued"]), present),
    )
    return TransitionSystem(
        name="jwt",
        initial=initial,
        actions=actions,
        invariant=lambda s: not (s["decision"] == "accept" and s["revoked"]),
        invariant_name="a revoked token is never accepted",
    )


# --- Secret exfiltration ----------------------------------------------------


def _secret_system(*, gated: bool) -> TransitionSystem:
    initial = ({"secret": False, "buffer_tainted": False, "sink_tainted": False},)

    def external_call(state: State) -> State:
        leaked = state["sink_tainted"] or state["buffer_tainted"]
        return {**state, "sink_tainted": leaked}

    external_guard = (lambda s: not s["buffer_tainted"]) if gated else (lambda s: True)

    actions = (
        Action("load_secret", lambda s: not s["secret"], lambda s: {**s, "secret": True}),
        Action(
            "copy_to_buffer", lambda s: bool(s["secret"]), lambda s: {**s, "buffer_tainted": True}
        ),
        Action(
            "redact", lambda s: bool(s["buffer_tainted"]), lambda s: {**s, "buffer_tainted": False}
        ),
        Action("external_call", external_guard, external_call),
    )
    return TransitionSystem(
        name="secret-flow",
        initial=initial,
        actions=actions,
        invariant=lambda s: not s["sink_tainted"],
        invariant_name="a tainted secret never reaches the external sink",
    )


# --- RBAC -------------------------------------------------------------------

_ROLES = ("viewer", "operator", "admin")
_ACTS = ("read", "write", "delete")
_SENS = ("public", "internal", "restricted")
_ACT_RANK = {"read": 0, "write": 1, "delete": 2}
_SENS_RANK = {"public": 0, "internal": 1, "restricted": 2}


def _grant_correct(role: str, action: str, sensitivity: str) -> bool:
    if role == "admin":
        return True
    if role == "operator":
        return _ACT_RANK[action] <= 1 and _SENS_RANK[sensitivity] <= 1
    return action == "read" and _SENS_RANK[sensitivity] <= 1  # viewer


def _grant_broken(role: str, action: str, sensitivity: str) -> bool:
    # BUG: "read-only roles may read anything" leaks restricted reads to viewers.
    if role == "viewer" and action == "read":
        return True
    return _grant_correct(role, action, sensitivity)


def _rbac_check(*, broken: bool) -> RelationalCheck:
    grant = _grant_broken if broken else _grant_correct

    def prop(a: State) -> bool:
        role, action, sens = str(a["role"]), str(a["action"]), str(a["sensitivity"])
        return not (
            role == "viewer"
            and action == "read"
            and sens == "restricted"
            and grant(role, action, sens)
        )

    return RelationalCheck(
        name="rbac",
        domains={"role": _ROLES, "action": _ACTS, "sensitivity": _SENS},
        prop=prop,
        claim="a viewer can never read a restricted incident",
    )


# --- Correlation coverage ---------------------------------------------------

_INDICATORS = ("failed_logins", "priv_esc", "exfil", "lateral")


def _correlation_check() -> RelationalCheck:
    def any_rule_fires(a: State) -> bool:
        return (
            bool(a["failed_logins"])
            or (bool(a["exfil"]) and bool(a["lateral"]))
            or bool(a["priv_esc"])
        )

    def prop(a: State) -> bool:
        in_bruteforce_class = bool(a["failed_logins"])
        return (not in_bruteforce_class) or any_rule_fires(a)

    return RelationalCheck(
        name="correlation",
        domains={indicator: (False, True) for indicator in _INDICATORS},
        prop=prop,
        claim="every brute-force pattern triggers at least one correlation rule",
    )


OBLIGATIONS: tuple[Obligation, ...] = (
    Obligation(
        id="jwt-revocation-safety",
        title="Revoked JWTs are never accepted",
        claim="In the revocation-checking auth model, no reachable state accepts a revoked token.",
        method=Method.EXPLICIT_STATE,
        expect=Verdict.VERIFIED,
        system=_jwt_system(checks_revocation=True),
    ),
    Obligation(
        id="jwt-missing-revocation-check",
        title="Auth without a revocation check is unsafe",
        claim="An auth model that skips the revocation check accepts a revoked token.",
        method=Method.EXPLICIT_STATE,
        expect=Verdict.REFUTED,
        system=_jwt_system(checks_revocation=False),
    ),
    Obligation(
        id="rbac-viewer-confinement",
        title="Viewers cannot read restricted incidents",
        claim="Under the correct RBAC policy, no viewer/read/restricted combination is granted.",
        method=Method.RELATIONAL,
        expect=Verdict.VERIFIED,
        relational=_rbac_check(broken=False),
    ),
    Obligation(
        id="rbac-broken-hierarchy",
        title="A read-any misconfiguration escalates viewers",
        claim="A policy that lets read-only roles read anything grants viewers restricted reads.",
        method=Method.RELATIONAL,
        expect=Verdict.REFUTED,
        relational=_rbac_check(broken=True),
    ),
    Obligation(
        id="correlation-no-false-negatives",
        title="No false negatives on brute-force patterns",
        claim="Every event pattern in the brute-force class triggers at least one rule.",
        method=Method.RELATIONAL,
        expect=Verdict.VERIFIED,
        relational=_correlation_check(),
    ),
    Obligation(
        id="secret-non-exfiltration",
        title="A gated agent never leaks a secret",
        claim="With a taint gate on external calls, no reachable state taints the sink.",
        method=Method.EXPLICIT_STATE,
        expect=Verdict.VERIFIED,
        system=_secret_system(gated=True),
    ),
    Obligation(
        id="secret-leak-via-tool",
        title="An ungated agent leaks a secret",
        claim="Without a taint gate, an external tool call exfiltrates the secret.",
        method=Method.EXPLICIT_STATE,
        expect=Verdict.REFUTED,
        system=_secret_system(gated=False),
    ),
)


def ground_truth() -> dict[str, str]:
    return {obligation.id: obligation.expect.value for obligation in OBLIGATIONS}
