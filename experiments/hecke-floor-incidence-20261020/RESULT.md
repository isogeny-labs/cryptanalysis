# Ten exact floor directions in a prospective D183/f6 holdout

The prospectively frozen `D_K=-183`, `f=6` Hecke walk reached 128 points
and produced a 96-by-128 verified relation matrix of rank **80** over
`QQ`. Deleting the 48 conductor-6 columns leaves rank **70**. The ten
floor-supported directions consist of eight disjoint degree-3 pair
differences and two independent signed degree-2 cycles, matching the
frozen even-block sign forecast. The earlier D39 case had four pair
differences plus two independent cycles; D87 had six pair differences
with its two cycles inside their span. These three cases motivate a
class-group sign-orientation question, while the parity rule itself
remains conjectural.

## Frozen cells and measured outcomes

The first [D15 protocol](PROTOCOL.md) fixed `D_K=-15`, `f=6`, and
`(p,|t|)=(139,4)`. Its producer completed, but both CM `j` values had
zero rational `X_0(11)` lifts. The independent
[modular gate audit](audit_D15_gate.json) found zero roots of
`Φ_11(j,J)` over `F_139` for `j=48,52`, and recorded
`(D_K/11)=-1`. Its matrix rank is recorded as `null`; the empty producer
array is a reachability outcome, not a rank observation.

The second [D183 protocol](PROTOCOL_D183.md), frozen after the D15 gate
and before its own launch, fixed `D_K=-183`, `f=6`, Hecke degrees 2 and 3,
`(p,|t|)=(1663,8)`, and `8²-4·1663=-183·6²`. The ring-class numbers
are `h_1=8`, `h_2=8`, `h_3=24`, `h_6=24`; 11 splits. The checked-Sage
producer completed under its 600-second cap in 12.548 seconds of
subprocess wall time. That timing is a local execution receipt, not an
isolated performance comparison. The [launch receipt](launch_D183.json)
retains the command, environment, status, and byte hashes.

| D183 rows | Count | Full rank over `QQ` | Rank after deleting `c=6` columns | Floor directions |
| --- | ---: | ---: | ---: | ---: |
| Degree 2 | 64 | 64 | 62 | 2 |
| Degree 3 | 32 | 32 | 24 | 8 |
| Combined | 96 | 80 | 70 | 10 |

The [independent Sage audit](audit_D183.json) checked all 128 point
conductor labels, 256 point-degree root counts with multiplicity against
both Hecke and classical modular polynomials, and all 96 saved group
relations. Conductor strata are `(16,16,48,48)` at `c=(1,2,3,6)`.
Degree-2 root totals are 64 one-root and 64 three-root fibers; degree-3
totals are 96 one-root and 32 four-root fibers. The producer's distinct
degree-3 neighbour-x histogram has one three-distinct-root fiber; the
multiplicity-aware audit counts four roots there. The full-rank tuple is
`(64,32,80)` over `QQ` and modulo 23, 1,000,000,007, and 2,147,483,647.

The [floor audit](floor_D183.json) extracts two signed 24-row degree-2
cycles with disjoint supports covering all 48 floor columns. It also
finds eight degree-3 row pairs with equal nonfloor coefficients; their
exact differences occupy disjoint six-column supports covering the same
floor. On every one of the eight cycle–pair overlaps, the signed ratio
takes both `+1` and `-1`. The [integer validator](validation_D183.json)
reconstructs every vector from the frozen row matrix and recomputes all
full and projected ranks independently in pure Python. An initial floor
audit failed because a copied graph helper lacked one import; its stderr
and a hash-bound [dependency amendment](floor_dependency_amendment.json)
are retained before the successful rerun.

## Proof and formalization boundary

For disjoint pair supports that cover the floor, a vector lies in the
pair span exactly when its signed coordinates are a constant scalar
multiple of the pair vector on each support. The forward implication
follows because at each coordinate only one pair vector can contribute;
the reverse implication assembles those local scalars. This general
criterion is proved as `FloorIncidence.disjoint_pair_span_iff` in
[LocalSpan.lean](LocalSpan.lean).

For this D183 matrix, two opposite ratios on one block of each disjoint
cycle force both cycle coefficients to vanish in a zero combination.
One coordinate from each remaining pair block then forces all eight
pair coefficients to vanish. This exact ten-vector statement is proved
as `D183Floor.ten_floor_vectors_independent` in
[FloorTen.lean](FloorTen.lean), generated reproducibly from the frozen
certificate by [make_floor_ten_lean.py](make_floor_ten_lean.py). The rank
difference `80-70=10` proves these ten vectors form a basis of the
floor-supported part of this saved row space.

| Mathematical result | Verification | Scope |
| --- | --- | --- |
| Disjoint-support local span criterion | `LocalSpan.lean`, `#print axioms` | General finite family of `ℚ`-valued pair vectors with disjoint, covering supports |
| Independence of the ten explicit D183 floor vectors | `FloorTen.lean`, `#print axioms` | Exact `Fin 128 → ℚ` vectors from the frozen certificates |
| Elliptic-curve row identities and ranks | `audit_D183.py`, `floor_D183.py`, `validate_floor_D183.py` | Checked-Sage group replay, exact rational ranks, three modular replays; not formalized in Lean |

Both Lean modules build with the pinned `leanprover/lean4:v4.35.0-rc4`
toolchain and Mathlib revision
`021c46bdd042f67b538b9f9871d556a93713a9a9`. Their
[local-span](local-span-check.txt) and [ten-vector](lean-check.txt)
axiom audits list only `propext`, `Classical.choice`, and `Quot.sound`.
`lean4checker --fresh` was unavailable on this host. All cells retain
`candidate_id: null`; the matrix experiment does not specify a complete
IC method or a one-target online comparison.

The next test should derive pair-block signs directly from oriented
norm-2 and ramified norm-3 class actions before selecting a new
finite-field walk. The D15 gate shows that the 11-splitting condition
belongs in that design, while D39, D87, and D183 now provide exact signed
incidence certificates against which to test the proposed rule.
