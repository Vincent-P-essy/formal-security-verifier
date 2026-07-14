"""Deterministic benchmark over the verification catalogue.

Runs every obligation ``iterations`` times, verifies each verdict against the
committed ground truth, confirms the full result set is byte-identical across
passes via a single stable hash, and measures wall time. Verification is
deterministic by construction (exhaustive search over finite models), so the
hash never varies.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import VerificationResult
from .obligations import ground_truth
from .reporting import result_to_dict
from .resources import packaged_path
from .verifier import verify_all


@dataclass(frozen=True)
class BenchmarkResult:
    iterations: int
    obligations: int
    verified: int
    refuted: int
    matched: int
    ground_truth_verified: bool
    deterministic: bool
    report_hash: str
    total_states_explored: int
    latency_pass_p50_ms: float
    latency_pass_p95_ms: float
    elapsed_seconds: float
    source_revision: str
    source_tree_state: str


def _percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    rank = max(0, min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1))))
    return round(ordered[rank], 4)


def _outcome_map(results: list[VerificationResult]) -> dict[str, object]:
    return {r.id: result_to_dict(r) for r in results}


def _hash(payload: dict[str, object]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def committed_ground_truth() -> dict[str, str]:
    data: dict[str, str] = json.loads(
        packaged_path("ground-truth.json").read_text(encoding="utf-8")
    )
    return data


def benchmark(iterations: int = 100) -> BenchmarkResult:
    declared = ground_truth()
    durations_ms: list[float] = []
    hashes: set[str] = set()
    matched = 0
    verified = 0
    refuted = 0
    total_states = 0
    started = time.perf_counter()

    for iteration in range(iterations):
        pass_start = time.perf_counter()
        results = verify_all()
        durations_ms.append((time.perf_counter() - pass_start) * 1000)
        hashes.add(_hash(_outcome_map(results)))
        if iteration == 0:
            verified = sum(1 for r in results if r.verdict.value == "verified")
            refuted = sum(1 for r in results if r.verdict.value == "refuted")
            total_states = sum(r.states_explored for r in results)
            matched = sum(1 for r in results if r.verdict.value == declared[r.id])

    elapsed = time.perf_counter() - started
    return BenchmarkResult(
        iterations=iterations,
        obligations=len(declared),
        verified=verified,
        refuted=refuted,
        matched=matched,
        ground_truth_verified=matched == len(declared),
        deterministic=len(hashes) == 1,
        report_hash=next(iter(hashes)) if hashes else "",
        total_states_explored=total_states,
        latency_pass_p50_ms=_percentile(durations_ms, 50),
        latency_pass_p95_ms=_percentile(durations_ms, 95),
        elapsed_seconds=round(elapsed, 4),
        source_revision=os.environ.get("VERIFY_SOURCE_REVISION", "unknown"),
        source_tree_state=os.environ.get("VERIFY_SOURCE_TREE_STATE", "unknown"),
    )


def write_benchmark(out_dir: Path, result: BenchmarkResult) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "benchmark.json"
    path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
