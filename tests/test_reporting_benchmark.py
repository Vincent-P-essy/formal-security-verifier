from __future__ import annotations

import json
from pathlib import Path

from formal_security_verifier.benchmark import _percentile, benchmark, write_benchmark
from formal_security_verifier.reporting import render_markdown, summarize, write_report
from formal_security_verifier.verifier import verify_all


def test_percentile() -> None:
    assert _percentile([], 50) == 0.0
    assert _percentile([1.0, 2.0, 3.0], 50) == 2.0


def test_benchmark_is_deterministic() -> None:
    result = benchmark(iterations=5)
    assert result.deterministic is True
    assert result.ground_truth_verified is True
    assert result.matched == result.obligations == 7
    assert result.verified == 4
    assert result.refuted == 3
    assert result.report_hash


def test_write_benchmark(tmp_path: Path) -> None:
    path = write_benchmark(tmp_path, benchmark(iterations=2))
    assert json.loads(path.read_text(encoding="utf-8"))["iterations"] == 2


def test_reporting(tmp_path: Path) -> None:
    results = verify_all()
    summary = summarize(results)
    assert summary["verified"] == 4
    markdown = render_markdown(results)
    assert "verification" in markdown.lower()
    assert "counterexample" in markdown.lower() or "Counterexample" in markdown

    paths = write_report(tmp_path, results)
    assert paths["json"].exists()
    assert paths["markdown"].exists()
