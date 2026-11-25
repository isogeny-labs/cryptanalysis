# Transposing the orbit query still leaves a quadratic search

The [descriptor gate](ORBIT_PAIR_DESCRIPTOR_GATE.md) asks whether one
of the `B` differences `R-P` lies in one of `D` orbit arcs. Its
`B*D` direct scan is not the best immediate implementation. Hash
the descriptor **seeds** once. For each third base point `P` and
each candidate common exponent `j`, look up

```text
[lambda^(-j)](R-P)
```

in that hash, accepting a descriptor of gap `delta` only when
`j<L-delta`. The returned category pair and exponent reconstruct
the indexed triple and its public `(G,Q)` labels. This is exact:
`R-P=[lambda^j]H` if and only if the transformed point is the
descriptor seed `H`. It uses `D` stored descriptors and at most
`B*L` transformed-point lookups per query, plus construction,
point subtraction, inverse-action evaluation, duplicate handling,
and verification. No unknown scalar is supplied to the query.
[pcc:unverified]

The [Sage replay](transposed_orbit_membership_replay.py) uses the
same `D=-19`, `p=47`, `r=61` curve and all 1,920 fixed queries from
the [frozen target-sum panel](INHOMOGENEOUS_ORBIT_REPORT.md). It
constructs the hash from the **public points** `G,Q`, recovers
every indexed triple by point equality, checks its actual group sum,
and matches each frozen query's total, informative count, and first
informative witness. It passed all 1,920 comparisons. The scalar
`d` enters only when constructing and checking the finite control
instances. The hash has 42 descriptor records, and each query
examines at most `12*3=36` transformed points. This is a functional
replay, not a measured speedup. [pcc:unverified]

At the optimistic P-192 joint `1 PiB` base-plus-descriptor cap of
the descriptor gate, `B=4L` with `L=1,759,218,604,441`; hence
`B*L` is about `2^83.356` transformed lookups **per query**. This
is over `2^54` times the favorable `2^29.275` complete-query
budget derived there. Inverse-action evaluation and setup only add
cost. The transpose reduces the direct `B*D` scan by roughly a
factor of 16 for two seed blocks, but it does not supply the
collective membership method needed at this scale. The same
identities and point sets hold for the matched known-scalar action,
so neither yield nor this lookup count is CM-specific.
[pcc:unverified]

The repository's earlier
[`IDEA-20260913-04fb8c`](https://github.com/isogeny-labs/crypto-autoresearcher/blob/fc70d15bb6e41544c5194eae9b70e45a83f1eb2b/ledger/proposals/IDEA-20260913-04fb8c.yaml)
already identifies membership with an unknown index in a
geometric-orbit window as the priced operation. The present hash
transpose applies that question to a **union of pair-sum arcs**;
it should not be cited as a new resolution of orbit membership.
Likewise, the existing
[point-to-ray homomorphism gate](POINT_TO_RAY_HOMOMORPHISM_GATE.md)
already rules out a simple additive map into the CM or ray class
group on P-192. The surviving candidate must read point
coordinates in a nonadditive way, return an indexed relation, and
beat the same known-scalar construction after all costs are charged.
[pcc:unverified]

Reproduce the point-query comparison from the repository root:

```sh
/Volumes/SSD990/cryptanalysis/sage -python research/cm_joint_s4_20261123/transposed_orbit_membership_replay.py
```
