# Frozen inhomogeneous two-seed orbit relation screen

The [homogeneous support bound](TWO_SEED_ORBIT_SUPPORT_BOUND.md)
does not apply when a fixed query point appears on the right-hand
side. This screen tests that exact remaining mechanic, without
claiming a CM cost gain. [pcc:unverified]

Use the fixed `D=-19`, `p=47`, `r=61`, `G=(2,1)` curve and
degree-five normalized `w=6+pi` from the prior two-seed protocol.
For every supplied target `Q=[d]G`, `d=1,...,60`, build the same
twelve indexed signed arc points `±w^j(G)` and `±w^j(Q)`, `j=0,1,2`,
with public `(G,Q)` labels. Check each point against the identical
native `[7]` scalar arc. Fix **32** query pairs `(a,b)` in the
committed `QUERY_PAIRS` constant of `inhomogeneous_orbit.py`; they
were drawn with Python seed `20261125`, `a in [0,60]`, and
`b in [1,60]` before any outcome was inspected. Keep all query
pairs, including any identity queries. The `d=3` target missed by
the homogeneous screen is the preselected focus. [pcc:unverified]

For each `R=[a]G+[b]Q`, enumerate all 364 indexed three-term
multisets and check their actual point sums against `R`. A matched
triple with label totals `(A,B)` gives

```text
(A-a) + (B-b)*d = 0 mod 61.
```

Call it informative iff `B-b!=0`. Check that the derived scalar
`-(A-a)/(B-b)` reproduces the supplied `Q`. Retain every query's
match counts, informative counts, first informative witness, and
failures. Do not select or redraw queries after the run. The exact
prediction is only that at least one preselected `d=3` query has an
informative witness; failure rejects that finite prediction. The
matched scalar arm must have identical indexed points and relation
counts; any discrepancy is an implementation defect.
[pcc:unverified]

For a P-192 cost interpretation, count the complete setup, 32
failures/successes, and relation verification on this finite curve.
The earlier [three-summand scale gate](README.md) supplies the
optimistic `C(B+2,3)/r` relation-probability ceiling and the
same-target rho reference. A finite success alone cannot establish
a large-curve oracle, a CM attribution, or a full-cost advantage.
[pcc:unverified]
