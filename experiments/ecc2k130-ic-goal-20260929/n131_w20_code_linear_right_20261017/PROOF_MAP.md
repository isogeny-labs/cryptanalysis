# Code-linear right product: proof map

The N131 W20 right pair has product `p = sum_j u_j b_j` for 19 binary code bits
`u_j`, where the `b_j` are the frozen rotated product basis. For a supplied
left reciprocal root `c` and target reciprocal `t`, set

`A = 1 + (ct)^2`, `B = ct`, `D = c^2 + t^2`,
`U = C D + H A`, and `V = H B`.

The target link is `A d^2 + B d + D = 0`, while the right pair law is
`C d^2 + p d + H = 0`. In characteristic two, these imply `D p = U d + V`.
Indeed, the S3 equation gives `D=d(Ad+B)`. Multiplying the pair equation's
`p d=C d^2+H` by `Ad+B` yields
`D p=C D d+H A d+H B=U d+V`.
Substituting `d = (D p + V)/U` gives

`(A D^2) p^2 + (B U D) p + A V^2 + B U V + D U^2 = 0`.

Squaring is binary linear, so this is a 131-row binary system in the 19
code bits. A full-rank system returns at most one code. The implementation
checks source validity, reconstructs `d`, and checks both quadratics. The
`D=0`, `U=0`, and rank-deficient paths retain an exact root fallback.
Conversely, the code equation is `U^2` times the target S3 equation after
substitution. When `U` is invertible, it therefore proves S3 for the
reconstructed `d`. The scaled identity then gives `D` times the pair
equation equal to `H` times the S3 equation; invertibility of `D` proves
the pair equation.

| Mathematical result | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| Scaled pair-product identity | `CodeLinear.scaled_product` | commutative ring, `2=0`, target S3 and pair equations | Checked |
| Necessary code equation | `CodeLinear.source_implies_linearized` | same | Checked |
| Reconstructed code satisfies S3 | `CodeLinear.linearized_implies_s3` | commutative ring, `2=0`, code equation, explicit inverse of `U` | Checked |
| Reconstructed code satisfies pair law | `CodeLinear.linearized_implies_pair` | preceding plus explicit inverse of `D` | Checked |

The pinned toolchain is `leanprover/lean4:v4.34.1`. Run `lean CodeLinear.lean`
from this directory. The retained [`lean.stdout.txt`](lean.stdout.txt) and
[`lean.stderr.txt`](lean.stderr.txt) show all four `#print axioms` audits:
`propext`, `Classical.choice`, and `Quot.sound`. `lean4checker --fresh` was
unavailable on this host. The computational bridge from each source mask to
the frozen pair-product basis and source-point columns is checked by the
source table, positive witness, and independent full-candidate audit; this
module formalizes the algebraic target link and its reverse reconstruction.
