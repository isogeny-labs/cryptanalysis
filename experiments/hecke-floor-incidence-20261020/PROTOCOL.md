# Prospective D15/f6 signed floor-incidence holdout

The observed D87/f6 certificate has uniform cycle-to-pair sign ratios on
every overlapping six-column floor block (three blocks per degree-2 cycle).
The independently sealed D39/f6 certificate has opposite ratios within
each of two blocks per cycle. The exact local span criterion is: when pair
vectors have disjoint supports partitioning the floor, a cycle supported
on a union of whole pair supports lies in their span if and only if its
coordinate ratio to each pair vector is constant on that pair's support.
The parity pattern suggested by these two cases is conjectural.

Freeze `D_K=-15`, Frobenius-order conductor `f=6`, Hecke degrees `[2,3]`,
and `PFS_WALK_PMIN=0`. The checked producer's prime search should choose
`(p,|t|)=(139,4)`, because `4²-4·139=-15·6²=-540`. The fundamental
discriminant has 2 split and 3 ramified. The ring-class counts predicted
from the class-number formula are `h_1=2`, `h_2=2`, `h_3=6`, `h_6=6`.
Conditional on two rational `X_0(11)` lifts per CM `j` and complete
component reachability, predict 32 columns with conductor strata
`(4,4,12,12)`, 16 complete degree-2 fibers sourced at conductors 1 and 3,
and eight complete degree-3 fibers sourced at conductors 1 and 2. Predict
24 verified rows and combined full rank `32-2h_6=20`.

The checked-Sage class scan found that the norm-2 class in the conductor-3
order has order 6. Predict two signed six-row degree-2 cycles with disjoint
floor supports covering the 12 conductor-6 columns. Predict that the four
degree-3 rows sourced at conductor 2 form two equal-nonfloor-part pairs;
their differences should have disjoint six-column floor supports covering
the same 12 columns. The **prospective parity hypothesis** predicts that
each cycle's six signed floor coefficients are proportional to the matching
pair difference. Its sharper rank forecasts (full/nonfloor) are degree 2:
`16/14`; degree 3: `8/6`; combined: `20/18`. Thus the floor-supported
subspace should have dimension two. Preserve opposite ratios, a failed
class-reachability gate, or any rank mismatch as the actual outcome.

The producer source and helper, class-order scan, prior comparison,
checked-Sage runtime, environment, and cap are SHA-256 frozen in
`protocol.json` before launch. Run the copied producer through
`/Volumes/SSD990/cryptanalysis/sage -python` with a 600-second wall cap;
record process status and every output byte. Independently replay point
conductor labels, root counts with multiplicity against both Hecke and
classical modular polynomials, row group identities, exact integer cycle
and pair vectors, and ranks over `QQ` and three finite fields. Local wall
time is an execution diagnostic only. Keep `candidate_id: null` because
this is a class-walk matrix investigation, not a complete IC candidate.
