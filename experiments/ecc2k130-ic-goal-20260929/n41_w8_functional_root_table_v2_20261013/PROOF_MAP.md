# Functional root-offset proof map

The pair-output equation has the form `F(a)=C*a²+p*a+h²=0` in the N41 binary field, with `C=1+h²`. The source code fixes `p` through a seven-bit linear map. For every permitted code, `C` is nonzero and the two roots are `a` and `a+p/C`. The finite root table and seven rotations are checked exhaustively by `experiment.py` and `audit_bdd.py` against the frozen 40-code domain; the constructed seven-pair assignment also checks the full XCNF.

`RootOffset.root_shift` proves the structural implication `C*d=p ∧ F(a)=0 ⇒ F(a+d)=0` in an arbitrary commutative characteristic-two ring with the listed additive and multiplicative laws. Its quantifiers cover all `C,p,h,a,d`; it does not assume the conclusion. `#print axioms RootOffset.root_shift` reports no axioms. The exact Lean toolchain is `leanprover/lean4:v4.34.1`; the local command was `lean RootOffset.lean`, with output in `lean_check.log`. This proof does not formalize the N41 field construction, the 40-code enumeration, the Boolean circuit, or the claim that the two roots are distinct. Those bridges are supplied by the frozen exhaustive checks and remain separate from the Lean theorem.

To see the algebra, in characteristic two `(a+d)²=a²+d²`. Thus `F(a+d)=F(a)+C*d²+p*d`, and `C*d=p` makes the added term `p*d+p*d=0`. The concrete field division gives `d=p/C` because `C≠0`.
