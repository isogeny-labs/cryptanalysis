# Quadratic target-support ceiling for two geometric orbit arcs

## Exact statement

Work in a cyclic group of prime order `r` with public generator `G`
and supplied `Q=[d]G`. Fix a unit `lambda mod r` and arc length
`L>=1`. Let `S={±lambda^j:0<=j<L}`. Choose two publicly labelled
seeds

```text
H1=[a1]G+[b1]Q,    H2=[a2]G+[b2]Q,
Delta=a1*b2-a2*b1 != 0 mod r.
```

The indexed base comprises `S*H1` and `S*H2`, at most `B=4L`
points. Allow repeated indices in a signed three-sum. Excluding the
at most two target labels for which `H1=O` or `H2=O`, the number of
nonzero scalar labels `d` for which **any informative zero-sum
triple** exists is at most

```text
8 L (2L-1).                                              (1)
```

The theorem applies whether `lambda` is produced by a smooth CM
endomorphism or native scalar multiplication. It bounds distinct
target labels, not the number of indexed relations at a given label.
It permits collisions and repeated orbit points; those can only
reduce the support. [pcc:unverified]

## Proof and the lost exponent

A zero sum entirely within one seed block has zero public
`(G,Q)` coefficients unless that seed itself is `O`; it cannot be
informative outside the two exceptions. A mixed triple has seed
coefficients `(c1,c2)` in either `(S+S) x S` or `S x (S+S)`.
When both are nonzero, put `u=c1/c2`. For the first case write
`c1=epsilon1*lambda^i+epsilon2*lambda^j` and
`c2=epsilon3*lambda^k`. Factoring by the smaller of `i,j` gives

```text
u = ±lambda^m (1 ± lambda^Delta),
m in {-(L-1),...,L-1},  Delta in {0,...,L-1}.
```

There are at most `4L(2L-1)` displayed values. In the second case
`u` is the inverse of one of these nonzero values, so the union has
at most `8L(2L-1)` elements. The apparent cubic number of indexed
triples loses one exponent because common powers cancel in the ratio.
For a nonzero seed pair, the group equality is

```text
(a1*u+a2)+(b1*u+b2)*d = 0 mod r,
d = -(a1*u+a2)/(b1*u+b2) mod r.                       (2)
```

Since `Delta!=0`, equation (2) is a fractional-linear bijection on
the projective line; it cannot increase the number of `d` values.
A zero `c1` or `c2` forces one seed to be `O`, an excluded exception.
This proves (1). It also shows why replacing `(G,Q)` by two other
independent public seed coefficient vectors does not restore cubic
target support. [pcc:unverified]

## Frozen control and P-192 scale

The [frozen `D=-19` census](TWO_SEED_ORBIT_REPORT.md) used
`r=61`, `lambda=7`, `L=3`, and seeds `(G,Q)`. Its **216 indexed
informative triples** hit only **46 distinct target labels**.
The [independent integer replayer](two_seed_orbit_support_bound.py)
constructs the ratio set, recovers exactly the same 46 labels,
and checks a second independent seed matrix after excluding its
two zero-seed labels. The ceiling `8*3*(2*3-1)=120` is deliberately
loose at this small order; the exact ratio-set computation is the
finite control. [pcc:unverified]

For the P-192 subgroup order used throughout this PR, an optimistic
1 PiB allocation at 32 bytes per **signed** base point allows
`B<=2^45`, hence `L<=2^43`. Formula (1), even after adding the two
exceptional labels, caps support below `2^90` of roughly `2^192`
nonzero targets. A fixed arc therefore has natural-target hit
fraction below about `2^-102`. A target-independent sequence of
different two-seed arc tests needs at least about `2^101` tests
before its union can cover half of the target labels, even if each
test answers exact membership for free. The negation-aware rho
reference is about `2^95.826` group-addition equivalents. Thus a
conventional one-or-more-addition-equivalent cost per tested arc
already exceeds that reference by over five bits, before any
isogeny, coordinate solve, storage, or verification cost.
[pcc:unverified]

This is a **scoped cost gate**. It assumes two fixed-length
geometric orbit arcs of a common multiplier, an explicit base
subject to the stated memory cap, and seed choices whose public
coefficients are fixed independently of the hidden `d` except for
earlier yes/no outcomes. It does not bound an implicit base larger
than the memory cap, a coordinate-dependent choice of seeds from
`Q`, more than two independent seed blocks, higher arity, or an
oracle that batches many tests below one addition equivalent each.
Those routes still need an explicit relation law and full charged
cost. [pcc:unverified]

Reproduce the finite and integer checks from the repository root:

```sh
python3 research/cm_joint_s4_20261123/two_seed_orbit_support_bound.py
```
