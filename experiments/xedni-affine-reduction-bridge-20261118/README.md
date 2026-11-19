# Regular affine reduction on known-relation lifts

The thirteen exact known-relation lifts admit 54 consecutive rational additions from their recorded rational point `T` to the multiples needed for `P1` and `P2`. Every step has integral input and output coordinates at its row's prime, a unit slope denominator, and the same result after reduction as finite-field addition. The steps consist of 13 tangents and 41 chords. The source is fixed by SHA-256 in `protocol.json`; `python3 run.py` independently recomputes and asserts each check, with all step-level observations in `result.json`.

The generic mathematical statement is: for a commutative ring `R`, field `S`, and ring homomorphism `f : R →+* S`, an affine chord or tangent with unit denominator in `R` has slope and output coordinates that commute with `f`. The written proof is substitution into the Weierstrass addition formulas. A unit `d` satisfies `f(d) f(d⁻¹)=1`, so the mapped rational slope equals the quotient of mapped numerator and denominator. The output coordinates are polynomials in the inputs and slope, and ring homomorphisms preserve those polynomials.

## Proof map

| Result | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| Unit-denominator slope transfer | `map_regularSlope` | `R` commutative ring, `S` field, `f` ring homomorphism, denominator a unit of `R`; checked by `lake build AffineReductionBridge` |
| Coordinate polynomial transfer | `map_addX`, `map_addY` | Same rings and homomorphism; checked by the same build |
| Chord formula transfer | `regular_chord_reduction` | Chord denominator is a source unit equal to `x₂ - x₁`; checked by the same build |
| Tangent formula transfer | `regular_tangent_reduction` | Tangent denominator is a source unit equal to `2*y`; checked by the same build |
| Exact rational addition paths on 13 recorded lifts | `run.py`, `result.json` | Fraction-level replay, finite-field replay, all 54 steps asserted; computational certificate, not a Lean theorem about the elliptic-curve group |
| Point membership under reduction | `XedniRegularChainReduction.mapPoint` | A short-Weierstrass point over `R` maps to a point on the coefficient-reduced curve over `S` |
| One regular addition step under reduction | `XedniRegularChainReduction.map_regularStep` | A chord or tangent with a source-unit denominator, recorded endpoint point, and exact affine addition formulas maps to a field step |
| Finite regular path under reduction | `XedniRegularChainReduction.map_regularChain` | Every step in the source chain satisfies `RegularStep`; the mapped start, addend, intermediates, and endpoint satisfy `FieldChain` |
| Field step is elliptic-curve addition | `XedniRegularGroupLaw.fieldStep_group_add` | Over a field, with the reduced short curve elliptic, a `FieldStep` is equality to mathlib's point-group addition; covers distinct-x chords and nonvertical doubling |
| Field chain gives a group relation | `XedniRegularGroupLaw.fieldChain_group_relation` | The field endpoint equals its start plus a natural-number multiple of the fixed addend |
| Reduced regular chain gives a group relation | `XedniRegularGroupLaw.reduced_regularChain_group_relation` | Combines the source-chain reduction theorem and field group law; requires ellipticity of the coefficient-reduced short curve |

The Lean chain theorem transfers a path of curve points and regular affine steps, and the group-law theorem identifies its reduced endpoint with a group multiple. A full formal point-level reduction homomorphism would additionally define the `p`-local rational coordinate ring and residue map, infinity and the vertical branch, then identify each recorded rational point in that model. That bridge is open. The experiment supplies exact regular paths for these thirteen rows; it does not itself establish the group-level theorem for arbitrary rational points.

## Reproduction

From this directory, run `python3 run.py`, `lake build AffineReductionBridge`, `lake build RegularChainReduction`, and `lake build RegularGroupLaw`. The Lean version is pinned in `lean-toolchain`, mathlib in `lake-manifest.json`; `build-output.txt`, `build-output-chain.txt`, and `build-output-group-law.txt` record the theorem builds and `#print axioms` output. The replay needs only the Python standard library and its source JSON at the sibling path named in the protocol.
