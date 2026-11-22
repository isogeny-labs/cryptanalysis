# Final-pair image filter proof map

Let `F` have characteristic two. For a fixed intermediate reciprocal
coordinate `w` and public reciprocal `t`, write

`A=1+(tw)²`, `B=tw`, `D=t²+w²`, `M=AH+CD`,
`a=AD`, `b=BM`, and `q=M²+CHB²`.

The final-pair resultant is `a p²+b p+q`; the eight source-code bits map
linearly and injectively to the last pair's product `p` on this N41 source.
For `a,b ≠ 0`, set `s=b/a` and `r=qa/b²`. Substituting `p=s h` turns the
equation into `h²+h=r`. Over the odd-degree binary field, this has two
solutions iff `Tr(r)=0`; halftrace supplies one, and adding one gives the
other. When `a=0` or `b=0`, the filter uses a linear or square-root chart
instead. The producer explicitly retains the `a=b=0` chart.

For two solutions `p₀,p₁`, add their equations. Characteristic two gives
`(p₀+p₁)(a(p₀+p₁)+b)=0`. Hence if `a≠0`, they coincide or differ by
`b/a`; at most two field products need to be tested against the sparse
source-code image. Each accepted code is then checked against the exact
71-code source policy.

For a reachable four-pair sum `P`, let `Q` be the fixed public point and
`R=Q-P`. In the nonexceptional chart, `e=1/x(R)` is a root of the target
link `A e²+B e+D=0` by the characteristic-two addition law. Because
`e≠0`, choose `p=(C e²+H)/e`. Then `C e²+p e+H=0`; the source and target
quadratics share `e`, so their resultant vanishes. This proves that
the *unrestricted field-root* test accepts every such reachable `P`.
Sparse source-product membership supplies the actual rejection rule. The
independent [group bridge](group_bridge_result.json) checks this argument
on all 256 sampled reachable sums, with zero exceptional residual charts.

| Mathematical result | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| Additivity of the product map | `FinalPairImage.map_additive` | commutative ring, every element doubles to zero | Checked |
| Equal outputs have equal or kernel-shifted products | `FinalPairImage.equal_output_two_preimages` | field, characteristic two | Checked |
| Adding a kernel step preserves a solution | `FinalPairImage.second_root` | field, characteristic two, `a*step=b`, one root | Checked |
| A shared source/target root zeros the resultant | `FinalPairImage.shared_root_resultant_zero` | field, characteristic two, both quadratic equations | Checked |
| A nonzero target-link root supplies an unrestricted source product | `FinalPairImage.unrestricted_product_from_root` | field, characteristic two, nonzero `e` | Checked |

The pinned toolchain is `leanprover/lean4:v4.34.1` in `lean-toolchain`.
`lean FinalPairImage.lean` succeeded. [`lean.stdout`](lean.stdout)
contains the `#print axioms` audit: only `propext`, `Classical.choice`,
and `Quot.sound` appear; the final source has no admitted statements.
Parser and tactic failures in the first three formalization attempts are
retained as `FinalPairImage_attempt{1,2,3}.lean` with their outputs.

The Lean module proves the algebraic consequences. The group-law step
from `R=Q-P` to the target `S3` equation is not formalized in this module;
the full curve-specific structural theorem remains a partial Lean
formalization. Its exact finite-field/point bridge and all recorded
sample rows were independently checked through the repository's checked
Sage launcher. The previously checked [resultant proof](../n41_w9_code_linear_tower_20261017/PROOF_MAP.md)
covers the split, allowed-source root equivalence used by the base
circuit.
