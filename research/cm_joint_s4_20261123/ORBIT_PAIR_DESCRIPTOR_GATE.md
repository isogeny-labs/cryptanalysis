# Pair-orbit descriptors compress storage, not point queries

For a signed geometric base from `s` public seed blocks, let `n=2s`
be the number of signed seed categories and let every category have
the same length `L` under a known scalar action `lambda`. The indexed
base has `B=nL` points. Every unordered indexed pair has a unique
exponent gap `delta`. At `delta=0`, choose an unordered pair of
categories; this gives `n(n+1)/2` descriptors, each with an arc of
length `L`. At `delta>=1`, choose the lower and higher category in
order; this gives `n^2` descriptors for that gap, each with an arc of
length `L-delta`. A descriptor seed is

```text
H(low,high,delta) = low + [lambda^delta] high,
pair sums = { [lambda^j] H : 0 <= j < L-delta }.
```

Thus the descriptor count is
`D=n(n+1)/2+(L-1)n^2`, while its arcs encode exactly
`B(B+1)/2` indexed pairs, including repeated point sums.
This is an indexing identity for **any** known scalar action. It is
not a CM-specific relation-yield gain. [pcc:unverified]

For the existing two-seed `D=-19`, `p=47`, `r=61` control,
`n=4`, `L=3`, `B=12`: **42 descriptors encode all 78 indexed pairs**.
The [independent coefficient replay](orbit_pair_descriptor_replay.py)
compares the full pair-sum counters, including multiplicities, and
checks the first frozen `d=3` target-sum witness. Its pair indices
`[0,2]` lie in the gap-one arc with seed `G+[7]G=[8]G`;
index `[9]` is `-[7]Q=-7Q`. The published first query therefore
still gives `15G+56Q=O`. The existing Sage runner checks the actual
elliptic-curve points. [pcc:unverified]

The query `P1+P2+P3=R` now asks, for a base point `P3`, whether
`R-P3` belongs to any descriptor arc, and needs its exponent and
category witness. Materializing descriptors saves pair-table
storage from quadratic to linear in `B`, but a direct scan of all
`B*D` point/descriptor combinations remains too expensive. Even
granting an unrealistically free **one-addition-equivalent**
arc-membership test for each combination, the original optimistic
`B=2^45` base has `D` just below `2^47`, hence nearly `2^92`
tests **per query**. The previously derived room under the
negation-aware P-192 rho reference is only `2^36.241` additions per
query at that base size. These figures are gates for this direct
scan, not performance measurements. [pcc:unverified]

If descriptors are also materialized at an optimistic 32 bytes each,
the base-only `1 PiB` allowance no longer applies: `B=2^45`
would use about `5 PiB` for base plus descriptors. Constraining
both arrays to `1 PiB` gives
`L=floor((2^45+6)/20)=1,759,218,604,441`,
`B=7,036,874,417,764`, and `D=28,147,497,671,050`.
The generic triple-count ceiling then requires at least
`2^66.551` independent uniform queries per hit and leaves below
`2^29.275` additions for a **complete** per-query oracle to fit
under the same `2^95.826` rho reference, before setup and failures.
The direct `B*D` scan is about `2^87.356` arc tests per query even
under the favorable unit-cost assumption. The 32-byte descriptor
figure is only a storage assumption; actual metadata may cost more.
[pcc:unverified]

The next relevant construction would be a collective arc-membership
oracle that answers a point query with its indexed witness at a
charged cost inside this budget. It must beat the identical native
`[lambda]` scalar-orbit control. An index that simply lists every
pair sum would restore quadratic storage; an implicit index needs
its construction, lookup, failure rate, and verification charged.
This gate does not rule out such an oracle, but descriptor compression
alone supplies neither the oracle nor a full ECDLP cost advantage.
[pcc:unverified]

Reproduce the coefficient check with
`python3 research/cm_joint_s4_20261123/orbit_pair_descriptor_replay.py`.
