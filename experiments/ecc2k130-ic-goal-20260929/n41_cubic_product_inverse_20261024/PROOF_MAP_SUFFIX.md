# Proof map for the N41 suffix pivot

The pinned toolchain is `leanprover/lean4:v4.35.0` from this directory's `lean-toolchain`. `lean RightQuotient_20261024.lean` exited zero. The saved `#print axioms` output for every declaration contains only `propext`, `Classical.choice`, and `Quot.sound`; the module contains no `sorry`, `admit`, custom research axiom, or native evaluation. `lean4checker --fresh` was unavailable on this host.

| Mathematical result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| `L_λ(x)+L_λ(v)=(x+v)(x+v+λ)` | `RightQuotient.factor` | Any commutative ring of characteristic two; checked. |
| `Q_V(L_λ(x))=P_V(x)P_V(x+λ)` where `P_V(x)=∏_{v∈V}(x+v)` and `Q_V(y)=∏_{v∈V}(y+L_λ(v))` | `RightQuotient.composition` | Any finite list `V` in a commutative ring of characteristic two; checked. Duplicates are permitted. |
| `Q_V(y)=0 ↔ ∃v∈V, y=L_λ(v)` | `RightQuotient.membership` | Characteristic-two commutative ring, `1≠0`, and no zero divisors expressed as a multiplication-zero implication; checked. The list can contain duplicates. |
| The chart coefficient `A=1+B` | `ChartQuartic.chart_A` | Any commutative ring of characteristic two; checked. |
| The chart coefficient `D=T²+u²` | `ChartQuartic.chart_D` | Same ring; checked. |
| The resultant reduces to `D²+S²+(S²+S)B²+pB(D+S)+p²D(D+1)` | `ChartQuartic.resultant_simplified` | Same ring; checked after substituting `A=1+B`. |
| The backward coefficient recurrence computes the exact linearized image vanisher | No Lean declaration | Algebraic coefficient identity and N41 finite-field checks completed; formal bridge from the recurrence list to `RightQuotient.imageVanisher` remains open. |
| The N41 field representation, curve, source products, chart table, and witness replay instantiate the generic identities | No Lean declaration | Frozen Sage source hashes, native full traversal, and independent archived group replay checked; a full Lean curve/chart model remains open. |

`P_V` and `Q_V` in the Lean module are finite products, so the membership theorem is exact even when `λ` belongs to `V` and the image has smaller rank. The compact coefficient recurrence used by the Sage diagnostic has a separate executable check, and its formal equivalence to this product is the remaining central proof obligation.
