# Integral chord filter for CRT xedni lifts

The two-point CRT lift has an exact prefilter: if lifted integer-coordinate
points `U=(x₁,y₁)` and `V=(x₂,y₂)` with `x₁≠x₂` satisfy `U+2V=O` on a
nonsingular monic Weierstrass curve with `a₁,a₂∈ℤ`, then
`(y₁−y₂)/(x₁−x₂)∈ℤ`. The reconstructed family in the frozen CRT panels has
integral `a₁,a₂,a₃`; its solved `a₄,a₆` may be rational. The condition
therefore applies to every accepted curve in those panels without assuming
`a₄,a₆` are integral.

On the eight-field matched subgroup panel, the filter leaves 12 of 472
reduced-relation rows. Ten of those rows passed the saved CRT gates and two
satisfied the exact monic equality; these are the same two rows that
satisfied the rational relation in the independent group-law replay. For
`p=101,191,251,347`, the integral-slope
count is zero, so the filter already forces zero rational relations under the
frozen centered-coordinate lifts. The other zero-yield fields retain
integral-slope candidates; their outcome depends on later gates.

| `p` | Subgroup `r` | Reduced relations | Integral slopes | Accepted integral slopes | Monic equality | Rational relations |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 47 | 43 | 42 | 4 | 4 | 2 | 2 |
| 101 | 53 | 52 | 0 | 0 | 0 | 0 |
| 191 | 53 | 52 | 0 | 0 | 0 | 0 |
| 211 | 79 | 78 | 4 | 2 | 0 | 0 |
| 251 | 61 | 60 | 0 | 0 | 0 | 0 |
| 281 | 73 | 72 | 2 | 2 | 0 | 0 |
| 347 | 47 | 46 | 0 | 0 | 0 | 0 |
| 349 | 71 | 70 | 2 | 2 | 0 | 0 |
| **Total** | | **472** | **12** | **10** | **2** | **2** |

## Proof

Write the curve as

`y²+a₁xy+a₃y=x³+a₂x²+a₄x+a₆`.

For a rational relation `U+2V=O` with `x₁≠x₂`, the line through `U,V`
is tangent at `V`. Its slope `m=(y₁−y₂)/(x₁−x₂)` therefore has the
standard duplication coordinate

`x₁=x(2V)=m²+a₁m−a₂−2x₂`.

Thus `m` is a rational root of the monic polynomial
`X²+a₁X−(a₂+x₁+2x₂)∈ℤ[X]`. A rational root of a monic integral polynomial
is integral. Equivalently, if `m=A/B` is reduced with positive `B`, then
`B² | A(A+a₁B)` and coprimality forces `B=1`. The argument uses only
`a₁,a₂,x₁,x₂∈ℤ`; the remaining coefficients cancel from the duplication
`x`-coordinate.

The Lean module `formal/IntegralChord.lean` checks the monic-root implication
and the algebraic chord/tangent bridge under its exact hypotheses. The proof
map identifies the separate elliptic-curve group-law bridge and its status.

## Replay and boundary

`audit.py` checks pinned hashes of the prior panel protocol, result, and
arithmetic audit; reconstructs the public subgroup point and each
`Pᵢ=Q−tᵢG`; replays all 30,008 raw rows; recomputes every reduced relation;
checks the uncompressed row digests and saved accepted/relation counts; and
asserts that every saved rational relation has an integral slope. For the ten
accepted integral-slope rows, it reconstructs the selected `a₁,a₂`, checks
the saved auxiliary probe counts, and evaluates the monic equality. Run it
with `python3 experiments/xedni-integral-chord-filter-20261115/audit.py`.
The parent panel's independent audit remains the source for its auxiliary
coefficient-search and rational group-law replay.

The filter is exact for the saved centered integer point representatives and
integral `a₁,a₂` policy. A new experiment can vary point lifts by multiples
of `p` or allow rational `a₁,a₂`, freeze the resulting height and search
budget, and ask whether the integral-slope bottleneck moves. Those are
different selection laws and require their own complete accounting.

This filter and the monic-equality diagnostic were derived after the parent
panel was measured. They explain its frozen rows exactly but are not a
preregistered prediction of a new field panel.
