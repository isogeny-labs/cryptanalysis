For p = 2147483647, the census partitions nonzero x by the exponent of
x to base 7 modulo 462. The CSV columns are class, neither, right only,
left only, and both. Left and right test for nonzero squares of
x³ + 2x + 14 and x³ + 2x − 14 respectively. The program checks that
neither polynomial vanishes on the enumerated domain.

Lean checks the order of 7, the period 4648233 of the within-class step,
and the quotient and remainder of the exponent. The CSV is an exhaustive
native computation. To reproduce it, run the following in this directory.

```sh
c++ -O3 -std=c++17 census.cpp -o census
./census > replay.csv && cmp replay.csv counts.csv
```

Conditional on left membership, the full-domain overlap among nonzero x
is 536844426 / 1073752646. Class 78 attains the maximum
1163807 / 2323499. Any selection based solely on the class has a rate
bounded by this maximum because its rate is a weighted mean.

The default implementation enumerates classes 0 through 230. Negating x
shifts its class by 231 and interchanges the two polynomial values with a
minus sign. For nonzero values, negation flips square membership in this
field. Thus the opposite row swaps the neither and both counts and preserves
each one-sided count. The Lean file checks all three identities. Pass
`--full` to enumerate both halves independently and compare its CSV.

On an Apple M4 Pro, four sequential fresh processes from one clang++ -O3
binary took 38.734 s (full), 21.628 s (paired), 22.336 s (paired), and
38.548 s (full). Wall time includes square-table construction and CSV
output. All four outputs matched the archived CSV byte for byte.
The ratio of mean times is 1.76× for this public census.
