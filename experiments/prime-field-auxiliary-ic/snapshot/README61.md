# Completed run over F_(2^61 - 1)

This second experiment recovered a test logarithm on y^2=x^3+3 over the
61-bit prime field. The target point has mixed order, whose largest prime
factor has **38 bits**. Index calculus solved that largest component; ordinary
Pohlig-Hellman decomposition and exhaustive search solved the three small
components. This is not a 61-bit prime-order DLP computation.

The relation search uses a pair-sum table and batch inversions. It does not
implement the Groebner-basis solver from the slides or establish a speedup
over generic algorithms.

## Reproduce

Requires Python 3 with SymPy and a C++17 compiler supporting `__uint128_t`.

```sh
cd /workspace/index_calculus_demo
python prepare61.py
g++ -O3 -std=c++17 -Wall -Wextra -o run61/solve solve61.cpp
cd run61
./solve
cd ..
python verify61.py
```

The solver reads only `run61/public.txt`, which excludes the secret scalar.
It stores every relation and a weighted elimination certificate. The verifier
uses only public inputs and that certificate to recover the full logarithm;
the final assertion against `expected.json` checks the test fixture.

## Exact instance

```text
p = 2305843009213693951 = 2^61 - 1
E: y^2 = x^3 + 3
#E(F_p) = 2305843006203085756
        = 4 * 11^2 * 30223 * 157632877033

W = (1, 2)
ord(W) = d = 104811045736503898
       = 2 * 11 * 30223 * 157632877033

Q_full = (219816249869125634, 1591304021262127525)
```

The largest prime factor is r=157632877033 (38 bits). The preparation and
independent verifier certify the order of W by checking [d]W=O and
[d/ell]W != O for each prime divisor ell. This also certifies the curve order:
d divides the curve order, and d is larger than the width of the Hasse
interval, which contains the displayed multiple of d.

## Auxiliary maps and projected factor base

The auxiliary curve C:y^2=x^3+x has cyclic order p+1=2^61, proved by the
quadratic-character cancellation x <-> -x and its unique nonidentity rational
2-torsion point. This is a supersingular reduction of the j=1728 CM curve.

For this resource-limited demonstration, use S=2048 and eleven degree-two
isogenies. `run61/auxiliary.json` records the exact maps and terminal constant.
All 2048 distinct coset x-values were checked. The larger 20-step construction
with S=2^20 is also retained in `auxiliary_61.json` from the first experiment.

Put h=#E/r=14627932, P=[h]W, Q=[h]Q_full. Then ord(P)=r and Q=[k]P.
For every auxiliary x-value that lifts to a point R on the target, use [h]R
as the factor-base point in the r-subgroup. The preparation stores the raw
points and projected points, rejects the identity, and merges +/- duplicates.
This produced 989 logarithm variables, or 1978 signed points.

This is a **cofactor-projected variant** of the earlier prime-order target
experiment. The low-degree isogeny constraints apply to the raw x-values.
Projected factor-base x-coordinates are not asserted to be roots of those
same maps. The verifier checks both the raw map constraints and the actual
three-point relations among the projected points.

## Index-calculus result

The pair table contained 1956236 distinct point sums. A deterministic random
walk maintained known a,b with R=[a]P+[b]Q, then searched for decompositions
into three signed factor-base points. No factor-base logarithms were supplied.

After 109322 walk trials and 918 relations, modular elimination reached rank
917 and canceled all 989 factor-base variables, yielding

```text
83453816041 + 137933622224*k = 0 (mod 157632877033)
k = 55300485039 (mod 157632877033).
```

Relation search and elimination, including the pair table, took about 25.38
seconds in this environment. Setup and independent verification are excluded.

For the other prime components, public-point calculations give

```text
k = 0    (mod 2)
k = 3    (mod 11)
k = 8373 (mod 30223).
```

The Chinese remainder theorem gives

```text
k = 9876543210987654 (mod 104811045736503898)
[k]W = Q_full.
```

`verify61.py` independently checks all relations, the two Semaev S3 quartics
per relation, the map roots, every cofactor projection, the linear-combination
weights canceling all factor-base columns, the group-order certificates, and
the final scalar multiplication. Recorded results are in
`run61/certificate.json` and `run61/full_result.json`.
