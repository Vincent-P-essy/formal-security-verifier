"""Smoke-test the installed wheel from outside the source checkout."""

from __future__ import annotations

from formal_security_verifier.benchmark import committed_ground_truth
from formal_security_verifier.obligations import ground_truth
from formal_security_verifier.verifier import verify_all


def main() -> int:
    if ground_truth() != committed_ground_truth():
        print("ground truth drift")
        return 1
    results = verify_all()
    declared = committed_ground_truth()
    for result in results:
        if result.verdict.value != declared[result.id]:
            print(f"unexpected verdict for {result.id}: {result.verdict.value}")
            return 1
        if result.verdict.value == "refuted" and result.counterexample is None:
            print(f"missing counterexample for {result.id}")
            return 1
    verified = sum(1 for r in results if r.proven)
    print(f"ok: {verified}/{len(results)} proven, {len(results) - verified} refuted with witnesses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
