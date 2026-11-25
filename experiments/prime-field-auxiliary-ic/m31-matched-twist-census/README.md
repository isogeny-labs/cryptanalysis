# Matched M31 auxiliary and twist sign census

Run `python3 replay.py > fresh.csv` and compare the output with `counts.csv`.
All three arms in each block use the same 500 ordered magnitudes. There are
50 per bit length from 21 through 30. Both signs must lift on the target
curve with coefficients (2,14) over the prime field of order 2147483647.
The smooth arm condition restricts the magnitude to integers with greatest
prime factor at most 211.

The auxiliary selector chooses the sign x for which x³+x is a square. The twist
selector chooses the other sign, for which −(x³+x) is a square. The random-sign
control flips a reproducible coin at each magnitude. In every arm the points
used in the census are on the same target curve.

Each counted row uses four distinct basis entries with signed coefficients.
The replay computes the ordinate of each candidate pair sum and uses its parity
to put both witnesses in the same orientation. It checks that each normalized
signed row appears through exactly three pair partitions. A private column is a
basis index used by only one row in the same arm and block. When every row has a
private column, those rows are independent over the group-order field.

Seeds 0–11 were the initial comparison, run with and without the smoothness
restriction. Seeds 12–35 were the fresh smooth confirmation, selected after
viewing the initial result. Confirmation means were 10.96, 10.00 and 9.92 for
auxiliary, twist and random sign. A paired block is the sampling unit.
The confirmation mean difference of 0.96 rows against the twist includes
11 positive differences, 10 negative differences and three ties. This census
measures incidence on the public bases and excludes collector runtime.
