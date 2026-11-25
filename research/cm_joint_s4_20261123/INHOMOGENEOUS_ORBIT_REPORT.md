# Target-sum relations escape the homogeneous orbit ceiling

The [protocol](INHOMOGENEOUS_ORBIT_PROTOCOL.md) and
[`inhomogeneous_orbit.py`](inhomogeneous_orbit.py) were pushed at
commit `5b64b61d9` before any query outcome was inspected. It fixes
32 public `(a,b)` query pairs and runs them on all 60 nonzero target
labels of the `D=-19`, `p=47`, `r=61` control, against the same
twelve-point two-seed orbit base as the [homogeneous census](TWO_SEED_ORBIT_REPORT.md).
The runner checks every indexed base point against its native `[7]`
counterpart, all 364 triple point sums, every public label, and the
recovered scalar of every informative match. Complete records are
in [`inhomogeneous_orbit_results.json`](inhomogeneous_orbit_results.json).
The separate [coefficient replay](inhomogeneous_orbit_scalar_replay.py)
checks all 1,920 query counts and first witnesses without elliptic-
curve operations. [pcc:unverified]

The preselected `d=3` target, which had no homogeneous triple,
has an informative target-sum relation on **31/32** frozen queries,
including the first. For that first query, `(a,b)=(54,59)` and
`R=(44,14)`. The indexed triple with points `(2,1)`, `(23,33)`,
and `(20,16)` sums to `R`; its public labels total `(A,B)=(8,54)`.
Subtracting the query labels yields

```text
(A-a)G+(B-b)Q = 15G+56Q = O,
d = -15/56 = 3 mod 61.
```

The runner verifies `[3]G=Q`. Across all 60 targets, **1,884/1,920**
query instances have an informative witness; all 60 targets have
one on their first frozen query. These are exact results for this
small finite group and its selected base and query stream. The
first-query observation does not predict a comparable rate at a
larger order. [pcc:unverified]

The mechanism is genuinely distinct from the homogeneous zero-sum
screen: `P1+P2+P3=R` has a fixed right-hand side, so shifting all
orbit exponents multiplies the left side but does not preserve the
equality. The [multi-seed common-shift bound](MULTI_SEED_ORBIT_SUPPORT_BOUND.md)
therefore says nothing about this query family. The CM and native
scalar bases remain **identical point by point**, so their query
relations and yield are identical. This establishes a reproducible
point relation involving the supplied `Q`, while leaving the
isogeny-specific cost question unresolved. [pcc:unverified]

The scale hurdle is explicit. With the optimistic P-192 materialized
base cap `B=2^45`, the number of indexed unordered triples is at
most `binom(B+2,3)`, giving a uniform-query hit probability at most
`2^-59.585` and at least about `2^59.585` queries per hit when
using independent uniform queries. Against the negation-aware rho
reference `2^95.826`, a one-relation route would need a complete
query oracle below about `2^36.241` group-addition equivalents,
before setup, failures, and verification are charged. An explicit
pair-table scan at this base size would spend about `2^104.585`
point lookups across those queries even before its table cost and
memory. These are favorable **derived ceilings**, not measured
P-192 solver times. The missing object is a coordinate-based
membership and witness oracle whose advantage over the identical
native-scalar base is caused by horizontal isogeny structure.
[pcc:unverified]

Reproduce the full finite records and independent replay from the
repository root:

```sh
/Volumes/SSD990/cryptanalysis/sage -python research/cm_joint_s4_20261123/inhomogeneous_orbit.py > /tmp/inhomogeneous_orbit_replay.json
cmp /tmp/inhomogeneous_orbit_replay.json research/cm_joint_s4_20261123/inhomogeneous_orbit_results.json
python3 research/cm_joint_s4_20261123/inhomogeneous_orbit_scalar_replay.py
```
