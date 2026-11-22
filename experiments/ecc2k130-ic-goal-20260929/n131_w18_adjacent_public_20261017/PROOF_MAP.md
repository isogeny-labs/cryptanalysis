# Adjacent leaf proof map

For the binary Koblitz curve (y^2+xy=x^3+1), the neighboring
Frobenius pair τP has x-coordinate (x(P)^2). The [previous
adjacent-source proof](../n41_n131_adjacent_frob_leaf_20261017/PROOF_MAP.md)
establishes, for nonexceptional x,
(x(P+τ P)=x+1/x) and
(x(P-τ P)=f(f(x))), where (f(x)=x+1/x).
Writing (a=1/x), the first reciprocal is (a/(1+a^2)). Composition
gives the second reciprocal

\[
  \frac{a(1+a^2)}{(1+a^2)^2+a^2}
  = \frac{a+a^3}{1+a^2+a^4}
\]

in characteristic two. The first circuit join uses one Boolean sign
wire e. Its exact field equation is

\[
  w(1+a^2+e a^4)=a+e a^3,
  \qquad e\in\{0,1\}.
\]

At e=0 this is the plus map, and at e=1 it is the minus map. Both
denominators are nonzero on the frozen source; the complete 66,382-root
field audit and 512 Sage group checks are bound by the protocol. The
constructed ten-pair assignment checks the entire Boolean formula,
including this join, against an independently replayed curve-point sum.

| Result | Lean declaration | Exact scope | Status |
| --- | --- | --- | --- |
| e=0 leaf polynomial | `AdjacentLeaf.plus_branch` | Integer a, direct branch substitution | Built |
| e=1 leaf polynomial | `AdjacentLeaf.minus_branch` | Integer a, direct branch substitution | Built |
| Composed denominator modulo two | `AdjacentLeaf.composed_denominator_mod_two` | Integer a, exact twice-remainder identity | Built |
| Entire extension-field point-decomposition circuit | No declaration yet | GF(2^131), source roots, signed group sum, target selector | Partial formalization; full Boolean assignment and independent Sage control checked |

`lean-toolchain` pins Lean 4.34.1, and `lean.stdout` retains the
`#print axioms` output. The first two theorems depend on `propext`;
the third also uses `Classical.choice` and `Quot.sound`. The available
Lean environment has no `lean4checker` executable. The remaining
formal bridge needs a characteristic-two field model, the binary
Weierstrass addition law, and equivalence between its field elements
and the circuit bit representation.
