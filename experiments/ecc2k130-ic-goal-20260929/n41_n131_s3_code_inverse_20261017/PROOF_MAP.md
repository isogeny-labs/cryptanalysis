# Direct S3 code inverse: proof map

The checked [Lean module](S3Inverse.lean) builds with pinned Lean 4.34.1
using `lean S3Inverse.lean`. Its [axiom output](lean.stdout) reports only
`propext`, `Classical.choice`, and `Quot.sound` for five theorems; the
sixth depends on no axioms. It contains no `sorry`, `admit`, `sorryAx`, custom axiom, or
native-evaluation proof. `lean4checker --fresh` is unavailable here.

| Mathematical step | Lean declaration | Exact scope and verification |
| --- | --- | --- |
| S3 becomes quadratic in the second reciprocal coordinate | `s3_second_quadratic` | Identity over any field. Checked. The curve/group-to-S3 coordinate bridge is inherited from earlier audited curve arithmetic and remains a separate formal obligation. |
| Half-trace solution reconstructs a quadratic root | `halftrace_root_sound` | Assumes characteristic two, explicit inverses of nonzero coefficients `A,B`, and a solution of `v²+v=A D/B²`. Proves `b=(B/A)v` satisfies `A b²+B b+D=0`. Checked. The finite-field trace-zero iff solvable theorem and half-trace construction are checked computationally here but not formalized in Lean. |
| Recover second source product | `recover_second_product` | Assumes characteristic two and an inverse of nonzero `b`; proves `q=(C b²+H)/b` satisfies the fixed-seed pair-output equation. Checked. Membership of `q` in the enumerated source set and point signs remain empirical checks. |
| Separable S3 discriminant | `normalized_rhs_separates` | With characteristic two and explicit inverses of `a,t`, proves `A D/B²=a²+a⁻²+t²+t⁻²`. Checked. |
| Vanishing solvability trace for curve coordinates | `normalized_rhs_trace_zero` and `reciprocal_curve_trace_zero` | The first theorem assumes an additive trace invariant under squaring and zero reciprocal-x curve trace for `a,t`; it proves zero trace of the normalized S3 right-hand side. The second derives each curve trace condition from a solution of the reciprocal-coordinate Artin–Schreier equation, assuming characteristic two in the trace codomain. Both checked. The exact finite-field trace and curve-coordinate interpretation remain concrete bridge obligations. |
| N41 full ordinary suffix panel | Three theorems plus producer and independent bit-field audit | The producer solved 9,230 S3 quadratics over 65 fixed-suffix queries. A distinct integer-field implementation checked each field root, source-product hit, and archived exact group-family result. The concrete field polynomial, 71-code table, and 65 query certificates are not yet kernel checked in Lean. |
| N131 sampled source controls | Three theorems plus checked-Sage producer and independent bit-field audit | The 512 source codes were independently validated in the preceding group/field audits; two known control codes were added. The constructed first-two-pair witness and fixed-suffix public-point query are checked on that finite set. A full `GF(2^131)` source and elliptic-curve group formalization remains open. |

The readable inversion proof is direct. Write the S3 relation as
`A b²+B b+D=0`, with `A=1+(a t)²`, `B=a t`, and `D=a²+t²`. For
nonzero `A,B`, substitute `b=(B/A)v`. The equation becomes
`v²+v=A D/B²`. In an odd-degree binary field this has roots precisely
when its trace is zero; half-trace returns one root and adding one returns
the other. When `A=0`, the equation is linear because `B≠0` on the
nonzero reciprocal chart. Every candidate `b≠0` determines exactly one
source product `q=(C b²+H)/b`. The source-product index admits the
candidate only when its code is valid. A final group and column replay
must resolve point signs and disjointness; the archived N41 relation and
constructed N131 control have those separate audits. This eliminates root and
sign expansion for all code pairs during the target-dependent query.

The remaining mathematical bridge is the converse that the two cases
enumerate every field root of S3, including the trace criterion. The
finite-field and group implementations explicitly enumerate and replay
the tested instances, but that general converse is not a Lean declaration
in this module.

The separated trace identity explains a negative search boundary. For
reciprocal x-coordinates of actual curve points, each term has zero
trace. Therefore the S3 quadratic's trace test accepts every such
first-coordinate/target pair on the tested nonzero chart. In these
experiments the selectivity comes from membership of the recovered
second product in the source code set, not from the trace test. The
concrete [all-coordinate trace census](trace_result.json) is frozen by
its [protocol](trace_protocol.json).
