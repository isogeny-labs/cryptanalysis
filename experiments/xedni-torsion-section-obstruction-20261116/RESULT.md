# A torsion obstruction to exact relation-preserving rational lifts

An exact relation-preserving rational lift of a nonzero point in a prime-order public subgroup cannot exist when the rational lift group has no torsion of that order. The obstruction is the public relation `[q]U = O`: every rational lift `P` of `U` satisfies `[q]P ≠ O` under the stated torsion hypothesis. Consequently, no additive section of reduction can represent the entire public subgroup. Four Lean theorems check the group-theoretic statement, including its explicit `ZMod q` specialization.

## Mathematical statement and proof

Let `ρ : H → C` be a group homomorphism, `U ≠ O` an element of `C` with `[q]U = O`, and assume `H[q] = {O}`. For any set-theoretic lift `s` satisfying `ρ(s(U)) = U`, the element `[q]s(U)` is nonzero. Indeed, if it were zero, the torsion assumption would give `s(U)=O`, hence `U=ρ(O)=O`, a contradiction. A relation-preserving lift would send `[q]U=O` to `[q]s(U)=O`; an additive section would do so automatically. This proves the obstruction without assuming a height bound, a particular curve model, or a choice rule for the lift.

For a rational elliptic curve with good reduction at `p`, take `H` to be the rational points whose reductions lie in the selected subgroup `C ⊂ E(F_p)`. The restriction of reduction is a homomorphism. If `C` has prime order `q>7`, the [rational torsion classification cited by Kamienny and Mazur](https://www.numdam.org/article/AST_1995__228__81_0.pdf) gives `E(Q)[q]={O}`. Thus the obstruction applies to *every* rational model and rational lift with that good reduction and subgroup. This application invokes the external torsion classification; the present Lean module checks the group implication conditional on `H[q]={O}`, not the classification or the construction of elliptic-curve reduction itself.

The witness uses coefficient `q`. It therefore addresses a calculus requiring preservation of **all** public relations or an additive subgroup section. A method that seeks one relation from a coefficient box below `q` has a different obligation. The [height-selected two-image experiment](../xedni-height-selected-two-image-20261116/RESULT.md) supplies finite-panel evidence for that bounded setting; its 22 public relations did not survive on the selected rational lifts. The two results have distinct scopes.

## Proof map

| Result | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| Every right-inverse lift of nonzero `c` fails its `q` relation | `XedniTorsionSection.torsion_relation_fails` | Additive groups `H,C`; reduction homomorphism; `c≠0`; `H[q]={0}`; right inverse at `c` | Checked |
| An additive section cannot exist for public `q`-torsion | `XedniTorsionSection.no_additive_section` | Above plus `[q]c=0`; additive section | Checked |
| A relation-preserving set-theoretic right inverse cannot exist at `c` | `XedniTorsionSection.no_relation_preserving_lift` | Above plus transfer of `[q]c=0` | Checked |
| Cyclic prime-order target specialization | `XedniTorsionSection.zmod_no_relation_preserving_lift` | `q>1`, `NeZero q`, target `ZMod q`, and the preceding reduction/torsion/right-inverse hypotheses | Checked |
| Rational elliptic-curve consequence for prime `q>7` | Written corollary above | Good reduction; identified subgroup; Mazur rational torsion classification | Formalization partial: external torsion theorem and elliptic reduction bridge remain outside this module |

The pinned toolchain is Lean `v4.35.0-rc4` with mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9` in [lakefile.toml](formal/lakefile.toml) and [lake-manifest.json](formal/lake-manifest.json). The build invokes `lake build TorsionSection`; `#print axioms` appears for all four declarations in [TorsionSection.lean](formal/TorsionSection.lean). The reported axioms are `propext`, and for the `ZMod` corollary also `Classical.choice` and `Quot.sound`. The module has no `sorry`, `admit`, `sorryAx`, or claim-encoding axiom. See [build-output.txt](formal/build-output.txt) and run `python3 verify.py` for reproducible checks.

## Next proof and experiment

Formalize the good-reduction subgroup restriction and a rational `q`-torsion exclusion once an appropriate Lean elliptic-curve torsion library is available. For the bounded coefficient problem, test a predeclared lift selection invariant on fresh public hits and require a positive rational relation before comparing cost. A full-section obstruction alone supplies no rate for a bounded relation search.
