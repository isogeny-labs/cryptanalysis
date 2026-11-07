# Transfer audit specification (2026-10-28)

User deliverable: a classification/trust theorem and obstruction, plus a Rust transfer audit CLI with explicit coverage certificates for a specified binary curve, including isogeny-class coverage. A universal exclusion of all possible transfers remains a separate open requirement; identity and same-field covers already preclude that literal exclusion.

Acceptance: (1) exact polynomial-basis input and irreducibility validation; (2) all subfields, exact integer Weil bounds and subgroup-size exclusions; (3) exact classical GHS rank; (4) evaluated Frobenius isogeny orbit; (5) complete small-field ordinary isogeny-class enumeration using trace, with a hard disclosed bound and no fabricated maps; (6) strict certificate replay and tamper rejection; (7) written cyclic-group classification, algebraic Frobenius obstruction and coverage trust theorem, with faithful feasible Lean components, clearly partial geometry formalization; (8) positive/negative controls, B-163 fixture, sources, report/diagram/PDF, CI.

No cost, rho, global novelty, evaluated generic GHS/gGHS quotient, or general isogeny-class map construction is inferred from these gates. Every unsupported family remains explicit. All scientific and CI manifests from PR1104 remain immutable.

Verification: cargo formatting, strict Clippy, Rust mathematical and CLI tests; Lean kernel build and transitive axiom audit; native certificate replay and altered-certificate rejection. New research experiments require the repository S3 checkpoint gate. No paid compute or Sage is required for implementation and unit checks.
