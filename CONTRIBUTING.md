# Contributing

Every change to a model or engine needs:

1. for a correct design, a test that the property is `verified` and the search
   was exhaustive (a real proof, not a bounded one);
2. for a broken design, a test that the property is `refuted` and a concrete
   counterexample (trace or assignment) is produced;
3. a determinism check: verification must be reproducible with a single stable
   benchmark hash;
4. a ground-truth review when a verdict changes, kept in sync with
   `fixtures/ground-truth.json` (a test enforces this).

An obligation that claims a property must actually model that property; do not
weaken an invariant to make a proof succeed. When adding a state variable, keep
the reachable space finite so `check` stays exhaustive, and prefer the shortest
counterexample by leaving the search breadth-first.

Run before submitting:

```bash
uv sync --frozen --all-extras
make lint
make test
make benchmark
sha256sum --check benchmarks/reference/inputs.sha256
docker compose config --quiet
docker build -t formal-security-verifier:test .
```

Do not commit generated co-author trailers. Keep every claim tied to a model a
reviewer can read and a verdict the checker reproduces.
