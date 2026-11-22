# Functional quadratic roots: proof map

The calculation uses a field of characteristic two. For the fixed-seed
source pair, write `C*u² + p*u + H = 0`, with `C,p != 0`. Set `v=C*u/p`.
Multiplying `v²+v=CH/p²` by `p²` gives
`p²(v²+v)+CH=C(C*u²+p*u+H)`. Since `C != 0`, these equations are
equivalent. For the target S3 equation, set
`A=1+(t*u)²`, `B=t*u`, `D=t²+u²`, with `A,B != 0`, and `r=A*w/B`.
Then `B²(r²+r)+AD=A(A*w²+B*w+D)`, giving the second equivalence.

For either normalized equation `z²+z=q`, suppose a half-trace value `h`
satisfies `h²+h=q`. Any other root `z` obeys
`(z+h)(z+h+1)=0`, so `z=h` or `z=h+1`. Thus a source code and two bits
select all four ordered pair-root/target-root branches when both trace
conditions vanish and all denominators above are nonzero. In the concrete
odd-degree fields, the half-trace implementation sums
`q^(2^(2j))`, `j=0..(n-1)/2`, and verifies `h²+h=q` on every audited
source and target quadratic.

| Result | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| Source equation equivalence | `FunctionalRoots.source_normalization` | Arbitrary `Field F`, characteristic two, `C != 0`, and `p*v=C*u`; kernel checked. |
| Target equation equivalence | `FunctionalRoots.target_normalization` | Arbitrary `Field F`, characteristic two, `A != 0`, and `B*r=A*w`; kernel checked. |
| Exactly two possible roots once one root exists | `FunctionalRoots.two_branch_completeness` | Arbitrary characteristic-two field and two solutions of the same Artin-Schreier equation; kernel checked. |
| Concrete half-trace identity and curve/code bridge | Open Lean bridge | Requires finite-field construction for `GF(2^41)` and `GF(2^131)`, Frobenius period, finite trace, half-trace implementation, and the Koblitz source-product and S3 coordinate identities. Exact Sage checks cover the frozen domains; this bridge is not reported as a Lean theorem. |
| Finite-sample quadratic-section exclusion | Open Lean certificate bridge | The [certificate](low_degree_result.json) gives subsets whose degree-at-most-two Boolean feature vectors XOR to zero while their first half-trace source-root values XOR to a nonzero field element. The independent [verifier](verify.py) recomputes each XOR. A Lean encoding of the numeric feature/output certificate has not been completed. |

For the final row, any degree-at-most-two Boolean polynomial in the code
bits is a linear combination of the constant, linear, and pairwise-product
features. Therefore XORing its output over a subset whose feature XOR is
zero must give zero. The recorded nonzero root XOR contradicts such a
representation of the **first half-trace section** on the frozen subset.
This statement concerns that canonical section; per-code choice of the
other quadratic root is a separate representation question.

The actual theorem module is [FunctionalRoots.lean](FunctionalRoots.lean),
with pinned [Lean 4.34.1](lean-toolchain). `lean FunctionalRoots.lean`
returned exit code `0`; [lean_check.log](lean_check.log) records
`#print axioms` for each declaration. Each uses only `propext`,
`Classical.choice`, and `Quot.sound`. `lean4checker --fresh` was unavailable
on this host. The module contains no `sorry`, `admit`, custom axioms,
or native-evaluation proof step.
