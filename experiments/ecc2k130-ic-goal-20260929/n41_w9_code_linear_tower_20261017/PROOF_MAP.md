# Rootless final-pair resultant: proof map

For the last pair output `e`, the source law is
`f(e)=C e²+p e+H=0`. Its two roots `e₀,e₁` are rational on each allowed
N41 W9 code, with `C≠0`, `C(e₀+e₁)=p`, and `C e₀e₁=H`. The public target
link through intermediate reciprocal `w` is
`g(e)=A e²+B e+D=0`, where `A=1+(tw)²`, `B=tw`, `D=t²+w²`.

Set `M=A H+C D`, `L=A p+C B`, and `N=B H+p D`. In characteristic two,

`M²+L N=C² g(e₀)g(e₁)`.

The identity follows by observing that `C g(eᵢ)=L eᵢ+M`, multiplying
these two equations, then using the root sum and product. Since the field
has no zero divisors and `C≠0`, the resultant vanishes **exactly when at
least one source-valid root obeys the public target link**. The condition
also covers `D=0` and other charts excluded by a divided formula.

Expanding the resultant gives

`M²+L N=(A D)p²+(B M)p+M²+C H B²`.

Squaring and multiplication by fixed field elements are F₂-linear in `p`.
Because `p` is a linear combination of the eight source-code product
basis elements, the final link has a binary-linear code block conditioned
on `w`. The factored form produced the smaller circuit in this experiment.

| Result | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| Expanded resultant identity | `FinalPairResultant.resultant_linearized` | commutative ring | Checked |
| Additivity of nonconstant product map | `FinalPairResultant.code_map_additive` | commutative ring, characteristic two | Checked |
| Resultant equals split-root value product | `FinalPairResultant.resultant_split_identity` | field, characteristic two, nonzero `C`, two source roots with Viète relations | Checked |
| Zero iff one source root satisfies target link | `FinalPairResultant.resultant_zero_iff_source_root` | same | Checked |

The pinned toolchain is `leanprover/lean4:v4.34.1`. Run
`lean FinalPairResultant.lean` from this directory. The saved
[`lean.stdout`](lean.stdout) and [`lean.stderr`](lean.stderr) show a successful
build and `#print axioms`: each theorem uses only `propext`,
`Classical.choice`, and `Quot.sound`. The final source contains no admitted claims.

The left three-pair F4 norm and right `S3(d,z,w)` norm reuse the checked
quadratic-tower structure in the archived
[`TargetTowerSound.lean`](../n41_w9_implicit_fivepair_tower_20261017/TargetTowerSound.lean).
The concrete bridge from all allowed source codes to their two split roots
is checked by the archived pair-law audit and the independent audit here.
The N41 curve-point bridge for any solver model requires independent signed
group replay; a Boolean solution alone is not a relation certificate.
