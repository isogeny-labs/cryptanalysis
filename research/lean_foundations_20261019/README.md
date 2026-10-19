# Rho walk foundations

The first-class `lean/` project pins crypto-lean
`60952c696ded7f3da4f4517006d9af6482662487`, Lean 4.35.0 and its exact stable
Mathlib manifest. The earlier retrospective remains frozen at its own pins.

`CryptoAnalysis.Rho.State` and `Valid` model the point/exponent invariant in
`src/rho.c`'s introductory walk description, `walk_restart`, `walk_apply`,
`walk_escape_cycle` and `rho_try_solve`. Source provenance: internal, retrieved
and read by this authoring session at b3d9c4fdece5ff698581c478d646a50c61eef029.

Nine theorem declarations prove initialization, equivalence with the actual
`a.val • P + b.val • Q` walk point, preservation under adding a multiplier,
negation and doubling, one optionally negated step, arbitrary finite schedules,
and both ordinary and negated collision recovery branches. The canonical
encoding is constructed from a point killed by n; recovery proves its
injectivity from exact prime order, with the respective nonzero denominator.

The model does not certify 64-bit modular arithmetic, hash/index selection,
canonicalization code, concurrent tables, randomness, cycle escape scheduling,
termination or runtime. Those remain explicit implementation obligations.
The C source is unchanged. No cryptanalytic advantage is claimed.

Reproduce:

```sh
cd lean
lake build
lake env lean AxiomAudit.lean
lake env lean --run .lake/packages/CryptoLean/tools/AuditAxioms.lean CryptoAnalysis.RhoState
cd ..
lean/.lake/packages/CryptoLean/tools/proof-gate.sh --out /tmp/rho-foundations-gate lean
```

Independent correspondence review is tracked in the 2026-10-19 foundation
study in `aburan28/crypto-autoresearcher`; its final report must distinguish
this algebraic model from a C refinement proof. Standard Lean axioms only;
no independent binary rechecker is installed.
