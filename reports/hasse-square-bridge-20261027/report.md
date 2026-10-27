# Squared Hasse predicate bridge: technical review

2026-10-27 UTC · Conductor T-504 · producer `f1c2dca` · pre-dispatch review plan `4ceec28` · cryptanalysis main base `dc73f979`.

## Observation

`HasseSquareBounds.lean` proves a Nat implication matching the arithmetic shape of Rust's `hasse_unique_multiple`: center `p+1`, a piecewise unsigned difference, squared deviations at most `4p`, and `r²>16p`. If both proposed and actual cardinalities are multiples of `r` and meet those squared bounds, they coincide. The source SHA-256 is `26e3e7bbf28aad0f60f72137fca027427b435f05bcef9f5de5881d7979307c42`; Lean pin SHA-256 is `d5edba4e4b8faad9c1baeadb265716d20d03be4d1a2647dc5e35b0c0325bea7b` (Lean 4.34.1).

## Comparison

Blind reviewer A derived the arithmetic without producer access, checked positive and zero cases, and gave a sharp counterexample at `p=1,r=4,n=0,m=4` when the strict threshold is weakened to equality. Source reviewer B compared the declarations with the proof map, Rust predicate, parser route and README. B read generic process skills, an unrelated memory hit, and neighboring Rust source beyond the plan's literal list; this was disclosed and no A material was read. The extra reads limit a strict file-list attestation but supplied no sibling verdict. Both reviewers' attestations are self-reported.

The coordinator rebuilt the exact committed Lean source and base imported theorem in isolation, audited transitive axioms, checked a positive application and sharp-boundary fixture, and tested a `sorry` false theorem and missing module. All nine machine steps matched their expected exits and every input hash was unchanged before and after. The imported base and new module built successfully. The new module audit found five theorem declarations with zero failures and zero `native_decide` exceptions; each reported only `[propext, Quot.sound]` or no axioms. The positive application and sharp-boundary fixtures built and audited. The `sorry` control compiled but its audit failed with `sorryAx`; the unknown module audit failed closed. The complete commands, exit codes, hashes and raw logs are in `machine-receipt.json` and adjacent outputs. The installed Lean kernel is the machine trust boundary; `lean4checker --fresh` was unavailable.

## Verdict

| Claim | Machine | Fidelity | Overall |
| --- | --- | --- | --- |
| Nat squared-predicate common-multiple uniqueness | Passed: exact-source build, transitive axiom audit, positive/boundary and negative controls | Faithful scoped, two independent joints | Validated scoped |
| Full P-192/P-224 Lean curve-order certificate | Missing bridges | Partial | Not verified |

## Inference and limits

The proof closes the *arithmetic* conversion from squared integer predicates to a short common-multiple interval. It does not establish a prime field, nonsingular elliptic group, exact generator order, Lagrange divisibility, Hasse for the actual cardinality, Lucas/Pratt checker correctness, Rust BigUint/parser correspondence, or concrete P-192/P-224 instantiation. The README accurately describes the older module but does not yet link this new partial bridge. No experiment or benchmark was run, so no quantitative graph or dashboard value changed. `proof-boundary.svg` explains the claim boundary.
