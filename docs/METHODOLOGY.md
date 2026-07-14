# Methodology

How the measured evidence is produced and what a verdict means.

## Ground truth

Each obligation declares the verdict a reviewer expects. `obligations.ground_truth()`
collects those, and the set is committed to `fixtures/ground-truth.json`. A test
asserts the three sources agree — the declared expectations, the committed
fixture, and the verdicts the checker actually produces — so none can drift.

## Verdicts

- **verified** — the checker explored the entire finite model without finding a
  violation. Because the exploration is exhaustive, this is a proof for the
  model, reported with the number of states or assignments examined.
- **refuted** — the checker found a concrete witness: a shortest execution trace
  (explicit-state) or a single assignment (relational). Every refuted obligation
  carries its counterexample.
- **inconclusive** — only possible if a model's reachable space exceeds the
  `max_states` guard; none of the committed obligations do.

## Determinism

`verify benchmark` runs the whole catalogue `iterations` times and hashes the
full result set — verdicts, state counts, and counterexamples — each pass.
`deterministic == true` means every pass produced one identical hash. There is no
randomness, no wall-clock dependence, and no external solver, so results are
byte-for-byte stable.

## What a green run proves and does not prove

A green run proves that, **for the committed models**, four security properties
hold with no reachable violation and three broken designs are caught with a
witness. It does **not** prove anything about a production system: the model is an
abstraction, and model checking is only as strong as that abstraction. The models
are intentionally small so a reviewer can read each one and judge its fidelity to
the design it stands in for.

Reproduce locally:

```bash
uv run verify verify all
uv run verify benchmark --iterations 500
```
