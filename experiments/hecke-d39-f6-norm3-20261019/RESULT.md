# Six exact floor directions in the D39 conductor-6 Hecke class walk

The prospectively frozen `D_K=-39`, `f=6` class walk yields a 48-by-64
verified relation matrix of rank 40 over `QQ`. Projection away from the 24
conductor-6 columns has rank 34. Thus its row space contains **six**
independent vectors supported entirely on that floor. Four are differences
of paired degree-3 rows; two are signed degree-2 cycles. The frozen forecast
of four floor directions and projected rank 36 is falsified, while its
class-size, row-count, pairing, cycle, and full-rank predictions hold.

## Instance and prospective test

The [protocol](PROTOCOL.md) and [machine-readable freeze](protocol.json)
were recorded before the producer. The field is `F_367`, with Frobenius
trace magnitude 8 and discriminant `8²-4·367=-39·6²`. The walk uses
Hecke degrees 2 and 3, with 64 rational points arranged by endomorphism
conductor `c=1,2,3,6` in counts `8,8,24,24`. The norm-2 ideal class at
odd conductor 3 has order 12; the ramified norm-3 class at conductor 2 has
order 2. This is a finite class-walk relation study; its `candidate_id` is
`null` because no complete IC pipeline is specified.

| Rows | Count | Full rank over `QQ` | Rank after deleting `c=6` columns | Floor-only directions |
| --- | ---: | ---: | ---: | ---: |
| Degree 2 | 32 | 32 | 30 | 2 |
| Degree 3 | 16 | 16 | 12 | 4 |
| Combined | 48 | 40 | 34 | 6 |

The same ranks hold modulo 23, 1,000,000,007, and 2,147,483,647. The
checked-Sage producer completed under the 600-second cap in 16.797 seconds
of subprocess wall time. That interval is a diagnostic execution receipt,
not an isolated CPU comparison. Its runtime record is in
[sage_runtime.json](sage_runtime.json), and the complete process command,
environment, exit status, and file hashes are in [launch.json](launch.json).

## Verification and proof

The independent [Sage audit](audit.py) reconstructs all 64 point conductor
labels and checks 128 point-degree root counts with multiplicity against
both Hecke-neighbour and classical modular polynomials. It verifies all 48
group identities and saved row coordinates, then recomputes ranks over
`QQ` and three finite fields. The root-count histograms are degree 2:
32 points with one root and 32 with three; degree 3: 48 with one and 16
with four. The [floor audit](floor.py) extracts two signed 12-row degree-2
cycles with disjoint supports covering all 24 floor columns, and four
degree-3 row pairs with equal nonfloor parts. Their differences have
disjoint six-column floor supports, again covering all 24 columns.

The [integer validator](validate_floor.py) replays the six signed vectors
directly from the frozen row matrix and checks their exact cancellations.
Their independence has a short witness proof. At floor columns 3 and 5,
the first cycle has opposite ratios to pair vector 1, forcing both
coefficients to vanish in any zero linear combination. Columns 21 and 15
do the same for the second cycle and pair vector 0. Columns 33 and 2 then
force pair vectors 2 and 3. The full and projected rank difference is six,
so these six independent vectors form a basis of the floor-supported
subspace of this row space. This exact finite statement is also proved in
[FloorSixV2.lean](FloorSixV2.lean) as
`D39Floor.six_floor_vectors_independent` for six explicit functions
`Fin 64 → ℚ`. The proof map is:

| Mathematical result | Lean declaration or checker | Status |
| --- | --- | --- |
| Independence of the six explicit floor vectors over `QQ` | `D39Floor.six_floor_vectors_independent` | Checked; `#print axioms` lists `propext`, `Classical.choice`, `Quot.sound` |
| Each vector is an integer row combination with zero nonfloor coordinates | `validate_floor.py`, frozen row matrix | Independently replayed; not formalized as an elliptic-curve statement in Lean |
| Combined full/projected ranks 40/34 | `audit.py`, `floor.py`, `validate_floor.py` | Exact `QQ` rank and three modular replays; not Lean-formalized |

The Lean generator [make_floor_lean.py](make_floor_lean.py) maps the frozen
certificates into six exact coordinate functions, and
[make_floor_lean_v2.py](make_floor_lean_v2.py) records the three syntactic
normal-form corrections. The first source and its failed build remain in
`FloorSix.lean` and `lean-check.txt`; the corrected source was frozen in
[formal_protocol_v2.json](formal_protocol_v2.json) before its successful
check. The toolchain is `leanprover/lean4:v4.35.0-rc4`, with Mathlib pinned
at `021c46bdd042f67b538b9f9871d556a93713a9a9`. The module build and
axiom audit are retained in `lean-build-v2.txt` and `lean-check-v2.txt`.
`lean4checker --fresh` was unavailable on this host.

The held-out discrepancy is structural: in this instance the degree-2
cycles are independent of the degree-3 pair differences, whereas the
forecast transferred a span relation from the earlier D87 ramified case.
The next prospective test should freeze the signed cycle/pair incidence
matrix from class-group action before constructing a new finite-field
walk. That would distinguish a character-orientation rule from a feature
specific to these two discriminants.
