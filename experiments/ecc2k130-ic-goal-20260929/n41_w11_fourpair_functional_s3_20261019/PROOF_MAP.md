# Functional S3 proof map

The circuit replaces each of two free intermediate S3 reciprocals with one branch bit and inverse witnesses, while retaining the original S3 equations. Its linear exceptional chart is included. For nonzero input reciprocals `a,b`, put `A=(ab)²+1`, `B=ab`, and `D=(a+b)²`. The S3 equation is `A z²+B z+D=0`. Since `B≠0`, let `v_B=B⁻¹`. When `A≠0`, also let `v_A=A⁻¹` and `q=A D v_B²`. If `h²+h=q`, the two roots are `z=B v_A h` and `z=B v_A(h+1)`. When `A=0`, the unique root is `z=D v_B`. A root in the ordinary chart implies `Tr(q)=0`; in `GF(2^41)` the half-trace computes an `h` for that trace-zero input. The circuit uses the trace-shifted linear half-trace map and separately enforces `Tr(q)=0`.

The Boolean `zero` bit and field witness `v_A` obey `A v_A=1+zero`, `zero·A=0`, and `zero·v_A=0`. In characteristic two these equations select `zero=0,v_A=A⁻¹` when `A≠0`, and `zero=1,v_A=0` when `A=0`. The output equation is `z=Bv_A(h+branch)+zero·Dv_B`. Thus both chart cases retain all quadratic roots under the stated reciprocal and half-trace assumptions.

| Mathematical result | Lean declaration or finite check | Scope and status |
| --- | --- | --- |
| S3 is quadratic in its output reciprocal | `../n41_w11_n131_w33_density_20261018/SharedRootTrace.lean`, `s3_output_quadratic` | Checked algebraic identity for arbitrary field elements. |
| Trace-shifted half-trace is linear and solves the trace-zero Artin-Schreier equation | Same module, `shifted_halftrace_add`, `shifted_halftrace_trace_zero` | Checked under explicit trace and half-trace hypotheses. |
| Ordinary-branch root soundness and completeness | `FunctionalS3.lean`, `quadratic_branch_sound`, `quadratic_branch_complete` | Checked in Lean 4.34.1 for arbitrary `Field F`, characteristic two, explicit inverse witnesses, and `h²+h=q`. |
| Exceptional linear root soundness and completeness | `FunctionalS3.lean`, `linear_branch_sound`, `linear_branch_complete` | Checked under explicit characteristic-two and inverse assumptions. |
| Concrete N41 S3 charts on archived relations | `audit_chart.py`, `chart_result.json` | All 32 independently replayed relations passed 96 S3 equations; all 96 use the ordinary chart. |
| Complete circuit assignments | `build.py`, `audit_all_witnesses.py`, `all_witnesses_result.json` | Every one of the 32 public-relation assignments passes all 102,722 clauses and 4,308 native XOR rows of the same circuit. |

`elan run leanprover/lean4:v4.34.1 lean FunctionalS3.lean` completed with empty stderr. `lean.stdout` records `#print axioms` for all four new theorems: only Lean's `propext`, `Classical.choice`, and `Quot.sound`. The module contains no `sorry`, `admit`, custom claim axiom, or native-evaluation proof. The earlier `SharedRootTrace.lean` has its own pinned build and axiom receipt.

The Lean theorems prove the abstract field root classification. The bridge from the Boolean gates to the exact polynomial-basis `GF(2^41)` implementation is checked by the complete assignments and finite arithmetic replay, rather than formalized as a Lean bit-vector model. A general theorem that the concrete half-trace implementation supplies every trace-zero root for this field remains a formalization obligation; the source uses its exact finite-field identity, and the 32-witness audit checks the instances used here.
