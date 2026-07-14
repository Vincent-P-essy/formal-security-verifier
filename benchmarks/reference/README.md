# Reviewed reference run

`reference-run.json` is a committed benchmark over the verification catalogue,
produced by:

```bash
VERIFY_SOURCE_REVISION=reference VERIFY_SOURCE_TREE_STATE=clean-checkout \
  uv run verify benchmark --iterations 500 --out benchmarks/reference
```

`inputs.sha256` pins the committed verdict ground truth. CI verifies it with
`sha256sum --check benchmarks/reference/inputs.sha256`.

## What the run establishes

- **Correctness.** All seven obligations produce their reviewed verdict — four
  proven, three refuted — matching `fixtures/ground-truth.json`
  (`ground_truth_verified == true`).
- **Proofs, not bounds.** Each `verified` obligation is exhaustive over its
  finite model, so the result is a proof for that model, not a bounded check.
- **Counterexamples.** Each `refuted` obligation carries a concrete witness: a
  trace (revoked-token replay, secret-to-sink flow) or an assignment (a viewer
  reading a restricted incident).
- **Determinism.** Every pass produces a byte-identical result set, collapsed to
  one `report_hash`.

Latency is machine dependent and not asserted in CI; only correctness,
determinism, and input integrity are.
