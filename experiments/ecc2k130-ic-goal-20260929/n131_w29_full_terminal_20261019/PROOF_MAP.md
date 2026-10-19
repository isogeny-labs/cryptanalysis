# Proof map for the linear half-trace terminal

The target-conditioned S3 root argument admits a square normalization. In
the characteristic-two field, put `u=1/c`, `v=1/t`, and
`z=c+u+t+v`. For nonzero `c,t`, the quadratic coefficient is
`A=1+(ct)^2`, the linear coefficient is `B=ct`, and the constant term is
`D=(c+t)^2`. Direct expansion gives `A D/B²=z²`. The native baseline
evaluates a 66-term half-trace on `A D/B²` for each left output. The new
query evaluates the same linear map on `z` by XORing precomputed images
of its set field bits. It checks `h²+h=z²` for every output before
emitting either S3 root, so the optimization cannot silently turn a
nonroot into a root.

| Mathematical obligation | Lean declaration | Exact scope and status |
| --- | --- | --- |
| Square normalization | `HalfTraceLinear.normalized_s3_argument_square` | Any field `F` with `x+x=0`, elements `c,t,u,v` satisfying `cu=tv=1`. Kernel checked. |
| Additivity of the actual half-trace recurrence | `HalfTraceLinear.halfTraceRec_add` | Any such field, any term count `n`, all `x,y`. `halfTraceRec 66` is the loop's input plus 65 successive fourth powers. Kernel checked. |
| Trace compatibility for rational reciprocal coordinates | `HalfTraceLinear.s3_trace_compatible` | Any field and additive square-invariant trace map, conditional on the two coordinate trace equations. Kernel checked. The curve-to-trace bridge is verified in the Sage source audit, not proved in this module. |
| Table evaluation of an additive map | `HalfTraceLinear.linear_table_fold` | Any additive map on an additive commutative monoid and any finite input list. Kernel checked. |
| Concrete binary fields and table | `n41_linear_control_sage.py`, `audit_sage.py`, `full_stream_linear.cpp` | Checked Sage tests all 562 N41 left outputs and 1,124 roots, plus 256 frozen N131 `z` values and all 131 table columns. The native N131 query checks the Artin–Schreier equation on every emitted root. The full finite-field implementation bridge is computational, not Lean-formalized. |
| Fixed-seed output inversion and source-product membership | Prior `PairOutputRecovery.lean` and full-stream audit | The prior Lean theorem gives the exact inverse formula and uniqueness. The current Sage audit replays the first 2,128 stream outputs and every reported hit. |

The toolchain is pinned by `lean-toolchain` to Lean 4.34.1, using the bundled
`Std` and `Init.Grind.Ring.Basic` modules with no external package. Run
`lean HalfTraceLinear.lean`; its saved output is `lean.stdout` and
`lean.stderr`. The four `#print axioms` audits list only standard
`propext`, `Classical.choice`, and `Quot.sound` foundations. The module
contains no admitted proof, custom research axiom, or native proof
shortcut. `lean4checker --fresh` was unavailable on this host.
