# Proof map

| Mathematical or implementation result | Exact hypotheses and evidence | Status |
| --- | --- | --- |
| `p(b)=u₀b+v₀` is the normalized form of the archived `E*p(b)` identity | `NormalizedStep.initial_normalization`: commutative ring, `E*inverseE=1`; archived pair equation supplies the original numerator `(C E+H A)b+H B` | Lean checked; standard axioms only |
| `A b²+B b+E=0` gives `b²=r b+s` | `NormalizedStep.normalized_root`: field of characteristic two, `A!=0`, `A*r=B`, `A*s=E` | Lean checked; standard axioms only |
| One linearized step updates `(u,v)` with two squarings and four field multiplications | `NormalizedStep.linearized_step`: commutative ring of characteristic two, `b²=r b+s` | Lean checked; standard axioms only |
| Reverse batch pass yields each denominator inverse and advances to the previous prefix inverse | `NormalizedStep.batch_inverse_step`: commutative ring, `inverseProduct*(pre*denominator)=1` | Lean checked; standard axioms only |
| New native loop preserves all frozen decisions and source recovery | `verify.py` checks eight complete N131 same-point queries against the archived baseline; `n41_control.py` compares 5,200 N41 decisions against the archived denominator-carrying implementation and its independent Sage audit | Computational replay passed in `verification.json` and `n41_result.json` |

The Lean module is built by `lean NormalizedStep.lean` under `leanprover/lean4:v4.34.1`; `lean_check.stdout` contains `#print axioms` for all four declarations and `lean_check.stderr` is empty. The native field implementation, batch-array indexing, concrete curve/source reconstruction, and timing receipts are checked computationally rather than represented in Lean. `lean4checker --fresh` was unavailable on this host.
