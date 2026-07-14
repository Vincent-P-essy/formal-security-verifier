from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from formal_security_verifier.api import create_app
from formal_security_verifier.cli import main
from formal_security_verifier.models import (
    Counterexample,
    Method,
    Verdict,
    VerificationResult,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_healthz(client: TestClient) -> None:
    assert client.get("/healthz").json()["status"] == "ok"


def test_obligations_listing(client: TestClient) -> None:
    assert len(client.get("/obligations").json()["obligations"]) == 7


def test_verify_one(client: TestClient) -> None:
    verified = client.post("/obligations/rbac-viewer-confinement/verify").json()
    assert verified["verdict"] == "verified"
    refuted = client.post("/obligations/secret-leak-via-tool/verify").json()
    assert refuted["verdict"] == "refuted"
    assert refuted["counterexample"]["steps"]
    assert client.post("/obligations/nope/verify").status_code == 404


def test_verify_all_endpoint(client: TestClient) -> None:
    summary = client.get("/verify").json()
    assert summary["verified"] == 4
    assert summary["refuted"] == 3


def test_dashboard(client: TestClient) -> None:
    assert client.get("/").status_code == 200


def _capture(capsys: pytest.CaptureFixture[str]) -> object:
    return json.loads(capsys.readouterr().out)


def test_cli_verify_all(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["verify", "all"]) == 0
    assert _capture(capsys)["obligations"] == 7


def test_cli_verify_named(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["verify", "jwt-revocation-safety"]) == 0
    assert _capture(capsys)["verdict"] == "verified"


def test_cli_verify_unknown(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["verify", "nope"]) == 2


def test_cli_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["report", "--out", str(tmp_path)]) == 0
    assert Path(_capture(capsys)["json"]).exists()


def test_cli_benchmark(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["benchmark", "--iterations", "2", "--out", str(tmp_path)]) == 0
    assert _capture(capsys)["deterministic"] is True


def test_model_helpers() -> None:
    result = VerificationResult(
        id="x",
        title="t",
        claim="c",
        method=Method.RELATIONAL,
        verdict=Verdict.VERIFIED,
        states_explored=3,
        exhaustive=True,
    )
    assert result.proven is True
    counter = Counterexample(kind="assignment", summary="s", assignment={"a": "1"})
    assert counter.kind == "assignment"
