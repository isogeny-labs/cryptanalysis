# Prospective D39 conductor-6 norm-3 floor-pairing holdout

Freeze `D_K=-39`, Frobenius-order conductor `f=6`, Hecke degrees `[2,3]`,
and `PFS_WALK_PMIN=0` before launching the checked-Sage producer. The
deterministic prime search is predicted to choose `(p,|t|)=(367,8)`, with
`t²-4p=-39·6²=-1404`. The fundamental discriminant has 2 split, 3
ramified, and 11 split. Rational `X_0(11)` reachability is an observed gate.

The ring-class predictions are `h_1=4`, `h_2=4`, `h_3=12`, and `h_6=12`.
Conditional on two rational `X_0(11)` lifts per CM `j` value and full
component reachability, predict 64 columns with endomorphism-conductor
strata `(8,8,24,24)` at `c=(1,2,3,6)`. The scalar-Frobenius rule predicts
complete degree-2 fibers at `c=1,3` (32 rows) and complete degree-3 fibers
at `c=1,2` (16 rows), totaling 48 verified relation rows. The empirical
class-floor rank law predicts combined rank `64-2h_6=40`.

The norm-2 class at odd conductor 3 is represented by `(2,1,44)` of
discriminant `-351` and has order 12. Predict two signed 12-row degree-2
cycles with disjoint floor supports covering the 24 conductor-6 columns.
The ramified norm-3 class at conductor 2 is `(3,0,13)` of discriminant
`-156` and has order 2. Predict that the eight degree-3 rows sourced at
conductor 2 pair into four equal-nonfloor-part pairs. Their four
differences should have disjoint six-column floor supports covering the
floor, and each degree-2 cycle vector should lie in the span of two such
differences. The sharper, conjectural subset full/nonfloor rank forecasts
are degree 2: `32/30`; degree 3: `16/12`; combined: `40/36`.

These predictions extend the D87 ramified-degree-3 pattern to a different
fundamental discriminant. Preserve any failed reachability, count, rank,
pairing, or span prediction as its measured outcome. The producer source,
multiplicity-aware helper, checked Sage runtime, frozen inputs, wall cap,
and timing boundary are hashed in `protocol.json`. Run the copied producer
through `/Volumes/SSD990/cryptanalysis/sage -python` with a 600-second cap.
Retain process status, stdout/stderr, result hash, all points and rows, and
failed or censored runs. Independently replay conductor labels, root counts
with multiplicity against both the Hecke and classical modular polynomials,
group identities, exact integer floor certificates, and ranks over `QQ`
and three finite-field moduli.
