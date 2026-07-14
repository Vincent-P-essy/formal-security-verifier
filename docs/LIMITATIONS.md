# Limitations

This is a portfolio-grade prototype. It demonstrates the *method* of formal
verification — proving safety properties by exhaustive search and producing
counterexamples for broken designs — over small synthetic models, not a
production verification of any real system.

- **Models, not systems.** A `verified` result is a proof for a committed model.
  Whether that model faithfully abstracts a real design is a human judgement the
  tool cannot make. The models are deliberately small so that judgement is easy.
- **Finite state only.** The explicit-state checker decides finite reachable
  spaces. It has no symbolic reasoning, abstraction refinement, or support for
  unbounded data; a model must stay finite to be proven rather than bounded.
- **Safety properties only.** It checks invariants ("nothing bad is reachable").
  It does not check liveness ("something good eventually happens"), fairness, or
  full temporal-logic (LTL/CTL) formulas.
- **No external solver.** It is self-contained by design, which keeps it
  deterministic and dependency-free but means it cannot match the scale of a real
  SMT-backed checker, TLA+/TLC, Alloy, or ProVerif on large models.
- **Relational checks are bounded universes.** Exhaustive enumeration is a proof
  only over the finite sorts declared; widening a sort widens the proof but costs
  exponentially.
- **Local API.** Unauthenticated and for loopback only.

The right way to read a result: it establishes a property of a small, readable
model, and it will hand you a concrete counterexample the moment the model —
correct or broken — permits one. See the [architecture](ARCHITECTURE.md) and
[methodology](METHODOLOGY.md).
