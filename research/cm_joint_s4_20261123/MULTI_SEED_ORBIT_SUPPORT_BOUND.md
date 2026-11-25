# Common-shift support bound for homogeneous orbit relations

## The indexed-triple ceiling

Let `G` generate a prime-order group of order `r`, let the supplied
point be `Q=[d]G`, and fix a unit `lambda mod r`. Choose `s` public
seed coefficient pairs `(a_t,b_t)` independently of the hidden `d`,
forming `H_t=[a_t]G+[b_t]Q`. The indexed base contains
`±[lambda^j]H_t` for each block `t=1,...,s` and exponent
`j=0,...,L-1`, so its nominal signed size is `B=2sL`.
An informative **homogeneous** three-sum is a triple of base points
whose point sum is `O` and whose summed public coefficient of `Q`
is nonzero. [pcc:unverified]

The number of nonzero target labels for which such a triple can
exist is at most

```text
M(s,L) = binom(2sL+2,3) - binom(2s(L-1)+2,3).           (1)
```

For fixed `s`, this is `Theta(s³L²)=Theta(sB²)`, even though the
number of indexed triples is `Theta(B³)`. It is an upper bound;
several triples can give the same target and some are uninformative.
It requires neither distinct points nor independent seed vectors.
[pcc:unverified]

## Proof

Represent an indexed triple as a multiset of `(block,sign,exponent)`
entries. If its minimum exponent is `m>0`, subtract `m` from all
three exponents. This multiplies both summed public coefficients
`A` and `B_Q` by `lambda^(-m)`, so it preserves `B_Q!=0` and the
root `d=-A/B_Q mod r`. Thus every informative target has a
representative triple with minimum exponent zero. There are
`binom(2sL+2,3)` total indexed triples with repetition. Exactly
`binom(2s(L-1)+2,3)` have all exponents at least one. Their
difference is the exact count of minimum-zero representatives,
proving (1). The more specialized [two-seed ratio bound](TWO_SEED_ORBIT_SUPPORT_BOUND.md)
gives a tighter `8L(2L-1)` for `s=2`. [pcc:unverified]

## Finite replay and materialized-base gate

The [integer replay](multi_seed_orbit_support_bound.py) checks that
all homogeneous target labels from the frozen `D=-19`, `s=2`,
`L=3` census are obtained from minimum-zero triples: 46 labels
from 364 full indexed triples and 244 normalized triples. A second
`r=1069`, `lambda=31`, `s=3`, `L=3` coefficient control gives
220 labels from 1,140 full triples and 776 normalized triples.
The latter is an algebraic count, not a horizontal solver or a
full ECDLP measurement. [pcc:unverified]

For P-192, use the same optimistic 1 PiB materialized-base cap of
32 bytes per signed point, `B<=2^45`. At each block count `s`, put
`L=floor(2^45/(2s))`. A target-independent sequence of tests that
receives only a yes/no answer to homogeneous relation existence
can cover at most `T*M(s,L)` labels in `T` tests. The 50% coverage
count is therefore at least `(r-1)/(2M(s,L))` tests. Exact integer
comparisons using `3.14159<pi<3.14160` show that for every
`2<=s<=36` this lower bound exceeds the negation-aware rho count
`sqrt(pi*r/4)`. At `s=37`, the bound first permits a smaller test
count, but only by about 2.4%, assuming the support ceiling is
attained and ignoring all setup and verification. This is a
necessary block-count screen under an optimistic one-addition-
equivalent-per-test model, not a sufficient algorithm. [pcc:unverified]

**Scope:** The common-shift argument applies to homogeneous orbit
zero sums with one shared multiplier and fixed public seed labels.
It does **not** apply to an inhomogeneous target-sum query
`P1+P2+P3=[a]G+[b]Q`: subtracting the same exponent from the three
base terms does not scale the fixed right-hand side. Such a query
can have cubic indexed support and is the next distinct candidate.
Coordinate-dependent seed selection, implicit bases beyond the
memory cap, higher arity, and batched oracles are also outside this
gate. [pcc:unverified]

Run the replay and exact threshold checks from the repository root:

```sh
python3 research/cm_joint_s4_20261123/multi_seed_orbit_support_bound.py
```
