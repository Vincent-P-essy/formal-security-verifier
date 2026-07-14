"""Serialize verification results into review artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import VerificationResult


def result_to_dict(result: VerificationResult) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": result.id,
        "title": result.title,
        "claim": result.claim,
        "method": result.method.value,
        "verdict": result.verdict.value,
        "states_explored": result.states_explored,
        "exhaustive": result.exhaustive,
    }
    if result.counterexample is not None:
        counter = result.counterexample
        payload["counterexample"] = {
            "kind": counter.kind,
            "summary": counter.summary,
            "assignment": counter.assignment,
            "steps": [
                {"index": step.index, "action": step.action, "state": step.state}
                for step in counter.steps
            ],
        }
    return payload


def summarize(results: list[VerificationResult]) -> dict[str, Any]:
    verified = sum(1 for r in results if r.verdict.value == "verified")
    refuted = sum(1 for r in results if r.verdict.value == "refuted")
    return {
        "obligations": len(results),
        "verified": verified,
        "refuted": refuted,
        "total_states_explored": sum(r.states_explored for r in results),
        "results": [result_to_dict(r) for r in results],
    }


def render_markdown(results: list[VerificationResult]) -> str:
    lines = [
        "# Security property verification",
        "",
        "| Obligation | Method | Verdict | States | Counterexample |",
        "|---|---|---|---:|---|",
    ]
    for result in results:
        counter = result.counterexample.summary if result.counterexample else "-"
        lines.append(
            f"| {result.id} | {result.method.value} | **{result.verdict.value}** | "
            f"{result.states_explored} | {counter} |"
        )
    verified = sum(1 for r in results if r.proven)
    lines += ["", f"**{verified}/{len(results)} claims discharged as expected.**", ""]
    return "\n".join(lines)


def write_report(out_dir: Path, results: list[VerificationResult]) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "verification.json"
    md_path = out_dir / "verification.md"
    json_path.write_text(
        json.dumps(summarize(results), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md_path.write_text(render_markdown(results), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}
