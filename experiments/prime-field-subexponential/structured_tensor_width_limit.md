# Arithmetic and geometric progressions do not lower residual tensor width

The conjugate-center quotient leaves two genus-two residual truth tables.
Random seven-to-nine-slot panels had near-maximal balanced flattening rank.
This control tests whether deliberately structured split-fiber abscissae make
those tables contractible.

Work on

\[
y^2=x^5+16x^4+20x^3+14x^2+12x+4
\quad\text{over }\mathbb F_{101}.
\]

For lengths seven, eight, and nine, exhaust every distinct split-fiber set
that occurs as either

\[
 a+bi\qquad\text{or}\qquad ab^i
\]

with all terms distinct.  The two families are disjoint in this census and
give 41 sets total.  Construct one exact planted target on every set and a
matched random split-fiber control with the same length.  For every signing:

1. quotient the rank-two center recurrence;
2. verify that the projected signed matrix has maximal possible row rank;
3. compute its cofactor kernel and the two remaining target residuals; and
4. exhaust every balanced bipartition of the residual truth tables.

## Results

| Slots | Arithmetic panels | Geometric panels | Structured minimum balanced ranks | Matched random ranks |
| ---: | ---: | ---: | --- | --- |
| 7 | 15 | 15 | rank 7: 18; rank 8: 12 | rank 7: 16; rank 8: 14 |
| 8 | 2 | 7 | rank 10: 9 | rank 10: 9 |
| 9 | 0 | 2 | rank 15: 2 | rank 15: 2 |

All 82 structured and random panels have maximal projected rank for every
signing and exactly one signing at which both residuals vanish.  At nine
slots, almost every individual balanced cut has rank 16; the reported rank
15 is attained on only one or two of the 126 cuts in the affected residual.
The progression panels show the same rare one-rank drop as the random arm.

Thus arithmetic or geometric progression structure does not produce a
smaller tensor-network exponent in this complete small-field census.  This
is finite negative evidence, not an asymptotic lower bound.  It leaves other
abscissa designs, curve families with extra automorphisms, and algorithms
using progression structure without truth-table flattening open.

## Reproduction

~~~sh
python3 structured_tensor_width_search.py |
  cmp - structured_tensor_width_search.json
python3 -m py_compile structured_tensor_width_search.py
~~~
