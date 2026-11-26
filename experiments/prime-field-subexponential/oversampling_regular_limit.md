# Oversampling does not yet lower branch-system regularity

Adding more split fibers creates many valid representations of a target.  A
possible positive route is that this multiplicity lowers the solving degree
of the branch-product ideal enough to offset the larger quotient.  Two exact
controls test the first small cases.

## Why a direct small-field test is delicate

For \(r\) variables and genus excess two, a random binary branch system has
\(r+2\) quadratic equations and heuristically

\[
 \frac{2^{r+2}}{p^2}
\]

branch solutions.  Making this quantity large at small \(r\) forces a tiny
field.  Accidental intersections then cause a point to lie on both branch
hyperplanes in one slot, producing nonreduced scheme structure not expected
in the large-prime asymptotic regime.

The first executable therefore rejects positive-dimensional selections and
nontransverse roots, and records the cumulative Macaulay quotient through
degree six.  Its dense tiny-field panels are useful diagnostics but are
biased toward the rare transverse instances.

## Large-field multi-planted control

The cleaner fixture works over \(\mathbb F_{101}\).  It chooses prescribed
points and, in each equation, constructs two hyperplanes whose union contains
all planted points.  Every one of the \(2^{r+2}\) branch selections is then
solved exactly.  Panels are accepted only when:

- every root is rational and isolated;
- exactly one branch vanishes per equation at each root;
- no unintended roots occur.

The observed stabilization degrees are:

| variables \(r\) | transverse roots | stabilization degree |
|---:|---:|---:|
| 4 | 1 | 4 |
| 4 | 4 | 4 |
| 4 | 6 | 3 |
| 5 | 1 | 4 |
| 5 | 5 | 4 |
| 5 | 8 | 4 |
| 6 | 1 | 5 |
| 6 | 6 | 5 |
| 6 | 10 | 5 |

At five and six variables, increasing the number of transverse solutions by
factors of eight and ten does not change the first stabilization degree.  At
four variables only the densest panel drops by one degree.  The Macaulay
column counts at stabilization remain 126 for \(r=5\) and 462 for \(r=6\).

## Consequence

These finite panels do not prove a linear asymptotic regularity lower bound.
They do rule out the simplest expectation that a modest number of additional
representations automatically causes an early-degree collapse.  A successful
oversampling argument now needs a quantitative theorem relating

\[
 \text{representation count},\quad
 \text{regularity},\quad
 \text{quotient dimension},\quad
 \text{and root-extraction cost}.
\]

If a large degree reduction requires exponentially many roots in \(r\), the
quotient algebra itself may materialize the entropy that oversampling was
meant to avoid.  This tradeoff remains unproved and is the next relevant
algebraic target.

[Random-density diagnostic](high_density_branch_regular.py) ·
[Frozen diagnostic](high_density_branch_regular.json) ·
[Multi-planted control](multiplanted_branch_regular.py) ·
[Frozen multi-planted output](multiplanted_branch_regular.json)

~~~sh
python3 high_density_branch_regular.py | cmp - high_density_branch_regular.json
python3 multiplanted_branch_regular.py | cmp - multiplanted_branch_regular.json
~~~
