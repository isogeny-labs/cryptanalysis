# Signed-pair coverage on the M31 depth-ten basis

The input is the ordered vector of x coordinates in the archived
`field31_s10/structured_roots.json`, Git blob
`5f02f75aaacd3a1513424d4beafb15258e02794c`. Lift on
`y² = x³ + 2x + 14` over the prime field of order 2147483647. Number the 500
liftable coordinates from zero in input order. Count unordered signed point
pairs with replacement and discard the point at infinity.

| Retained coordinates | Finite pairs | Distinct finite sums |
|---:|---:|---:|
| 500 | 500000 | 499940 |
| 499 | 498002 | 497954 |
| 491 | 482162 | 482162 |

The PARI census enumerates point additions and sorts by the entire affine
point. The ten collision supports have four coordinates each and multiplicity
six. Only coordinate 112 (x = 1273657599) occurs twice among the supports.
Eight disjoint supports and either of the two that meet at 112 give nine
disjoint obstructions. Removing 112 and the smallest index in each of the
eight other supports gives a collision-free witness of size 491. Its deleted
indices are 11, 14, 18, 58, 103, 112, 140, 208 and 221.

Lean proves the cardinality upper bound from nine disjoint obstructions.
The curve-specific premises and the lower-bound witness are checked by PARI.
For a pass that costs a fixed amount plus one unit per finite pair, dividing
pass cost by distinct coverage gives the uniform-target cost model. The
491/499 and 499/500 switch points are 482162/329 and 980020/331 fixed units.
A runtime claim requires measuring the pass cost. Perfect coverage per pair
can improve the full basis's coverage per pair by less than 0.0121 percent.

## Replay

From the repository root, with PARI/GP installed, run

```sh
d=experiments/prime-field-auxiliary-ic/m31-subset-frontier
{
  printf 'xs='
  git cat-file blob 5f02f75aaacd3a1513424d4beafb15258e02794c | tr -d '\n'
  printf ';\n'
  cat "$d/census.gp"
} | gp -q -f -s 256M
```

The final output contains all three rows in the table. For the Lean replay,
set `proof` to the absolute path of `Frontier.lean`, enter a Mathlib checkout
with Lean 4.34.1 and run `lake env lean -DwarningAsError=true "$proof"`.

## Point-negation orbit table

For an x-membership query, a point and its negative share the same answer.
The curve cubic has no field root, so each finite x in the sum table has
exactly two signed points. For each coordinate pair i < j, enumerate Pᵢ + Pⱼ
and Pᵢ − Pⱼ. For i = j, retain the double. The sign choices omitted from the
outer loop give the negatives of these sums. The program checks equality of
the complete projected baseline set with the orbit set, including the count
499940 = 2 × 249970. It does not construct signed decomposition witnesses.

Use the same input pipeline above, substituting orbit.gp for census.gp and
384M for 256M. Initialization and the exact comparison precede timing.
The six warm pairs alternate order on a shared ARM64 host. Timings cover
enumeration, key packing, and sorting into a set. Baseline keys encode the
full affine point, orbit keys encode x. Each column below is in milliseconds.

| Pair | Baseline CPU | Orbit CPU | Baseline wall | Orbit wall |
|---:|---:|---:|---:|---:|
| 1 | 891 | 430 | 1851 | 614 |
| 2 | 1060 | 465 | 2096 | 726 |
| 3 | 993 | 445 | 2127 | 856 |
| 4 | 1115 | 480 | 2478 | 1097 |
| 5 | 1008 | 458 | 1395 | 597 |
| 6 | 910 | 408 | 1073 | 477 |
