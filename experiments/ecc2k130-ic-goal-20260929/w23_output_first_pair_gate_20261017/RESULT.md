# W23 output-first pair gate: exact decoder and measured circuit cost

The 22-dimensional W23 source-product space admits an exact output-first
encoding. Given a nonzero pair output reciprocal `z` and checked inverse
`b=z⁻¹`, the source product is `p=Cz+Hb`, with `C=1+H` and
`H=halftrace(seed)²`. A 22-coordinate left inverse recovers every source
selector bit from `p`; the remaining 109 coordinates are exact parity checks.
The constructed N131 pair passes the independent circuit assignment checker
in both orientations.

The direct gate screen favors the existing code-first orientation for the next
six-pair solver experiment. Both gates impose the same fixed-seed source
eligibility and pair-output law; output-first adds an inverse multiplication
and larger parity support.

| Exact one-pair gate | AND gates | Variables | CNF clauses | XOR rows | Constructed check |
| --- | ---: | ---: | ---: | ---: | --- |
| Code-first | 5,764 | 6,630 | 17,557 | 582 | 17,557 clauses, 582 XOR rows pass |
| Output-first | 8,699 | 13,427 | 26,471 | 4,335 | 26,471 clauses, 4,335 XOR rows pass |

Output-first adds 2,935 AND gates and 3,753 XOR rows per pair. A six-pair
extension would also change link propagation, so these one-pair gate counts
are a circuit screen, not a six-pair solve-time estimate. The deterministic
decoder audit checked all 22 basis vectors and 1,024 seeded combinations;
the independent field arithmetic check confirmed `z*b=1` and
`p=Cz+Hb` on the frozen constructed pair.

## Exact instance and method

- Curve: `EC1N131Ckb1heb5f1998f20b`; field polynomial has taps
  `[0,1,2,13]`, source width 23, fixed seed mask 898618, 22 free code bits.
  The encoded source is the W23 source in the existing six-pair experiment.
- Input: first pair from the frozen six-pair constructed fixture; no target
  value or source option was changed between orientations.
- Decoder: invert the first 22 independent rows of the 131-by-22 product
  basis matrix over `GF(2)`. The code and 109-dimensional syndrome are
  emitted as direct XOR forms of the 262 output and inverse bits.
- Source eligibility: the same product inverse witness and endpoint trace
  conditions in both gates.
- Resources: local macOS correctness and circuit-size diagnostic, one process;
  the checked Sage runtime receipt is `sage_runtime_info.json`. Build and
  checker durations are recorded in `result.json`, but are not isolated solver
  timings. `candidate_id` remains null because this is one pair gate rather
  than a complete IC pipeline.

Run from the repository root:

```sh
./sage --runtime-info > experiments/ecc2k130-ic-goal-20260929/w23_output_first_pair_gate_20261017/sage_runtime_info.json
./sage -python experiments/ecc2k130-ic-goal-20260929/w23_output_first_pair_gate_20261017/experiment.py
```

The source/input/runtime SHA-256 values, decoder pivots, checker counts, and
exact circuit counts are in `result.json`. A failed first script run stopped
at a diagnostic key mismatch (`satisfied` rather than the checker's actual
`clauses` and `native_xor_rows` keys); its mathematical checks had not failed.
The rerun above completed after fixing that assertion.

## Proof map

The equivalence `Cz²+pz+H=0 ↔ p=Cz+Hb` under `z*b=1` is the existing theorem
`OutputLinearization.pair_output_linear_iff` in
`../n131_w20_output_inverse_linear_20261012/OutputLinearization.lean`.
It quantifies over a characteristic-two commutative ring with the displayed
ring laws, all `z,b,p,C,H`, and the inverse-witness hypothesis. Its parameters
apply directly to this W23 pair. Lean 4.34.1 checked the actual module again:

```sh
cd experiments/ecc2k130-ic-goal-20260929/n131_w20_output_inverse_linear_20261012
lean OutputLinearization.lean
```

`#print axioms` reports no axioms; the saved output is `lean_check.txt`.
The concrete 22-row rank and the Python gate construction are executable
checks in `experiment.py`, not a Lean theorem. The next target-coupled test
should seek code-family rejection before enumerating pair combinations;
the current output-first change alone gives no measured rejection advantage.
