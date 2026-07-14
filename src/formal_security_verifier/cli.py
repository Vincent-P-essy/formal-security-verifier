"""Command-line interface for the formal security verifier."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import uvicorn

from .benchmark import benchmark, write_benchmark
from .obligations import OBLIGATIONS
from .reporting import result_to_dict, summarize, write_report
from .verifier import verify, verify_all


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="verify", description="Formal security verifier")
    commands = root.add_subparsers(dest="command", required=True)

    verify_cmd = commands.add_parser("verify", help="verify one obligation or all of them")
    verify_cmd.add_argument("obligation", nargs="?", default="all")

    report = commands.add_parser("report", help="verify all and write a report")
    report.add_argument("--out", type=Path, default=Path("reports"))

    run_benchmark = commands.add_parser("benchmark", help="measure the catalogue")
    run_benchmark.add_argument("--iterations", type=int, default=100)
    run_benchmark.add_argument("--out", type=Path, default=Path("reports"))

    serve = commands.add_parser("serve", help="start the local API and dashboard")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8080)

    return root


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)

    if args.command == "verify":
        if args.obligation == "all":
            _print(summarize(verify_all()))
            return 0
        obligation = next((o for o in OBLIGATIONS if o.id == args.obligation), None)
        if obligation is None:
            print(f"unknown obligation: {args.obligation}")
            return 2
        _print(result_to_dict(verify(obligation)))
        return 0

    if args.command == "report":
        paths = write_report(args.out, verify_all())
        _print({key: str(path) for key, path in paths.items()})
        return 0

    if args.command == "benchmark":
        measured = benchmark(iterations=args.iterations)
        path = write_benchmark(args.out, measured)
        _print({"benchmark": str(path), **asdict(measured)})
        return 0

    if args.command == "serve":
        uvicorn.run(
            "formal_security_verifier.api:create_app",
            host=args.host,
            port=args.port,
            factory=True,
            log_level="info",
        )
        return 0

    return 2  # pragma: no cover - argparse requires a subcommand


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
