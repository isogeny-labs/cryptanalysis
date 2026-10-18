# Exact target-conditioned two-plus-one N41 join

An exact **two-plus-one-versus-two indexed join recovered the archived N41
public relation** with 79,424 entries on each precomputed pair side and
35,471,360 bytes sampled peak combined RSS. The one-worker run reached the
relation at Frobenius orientation 3 in 292.425 parent wall seconds, below the
frozen 600-second and 4-GiB caps. Independent checked Sage reconstructed all
ten source leaves, verified ten distinct folded columns, transported the
sum back to raw public point `(2026560328086,1928332930914)`, and checked
its cofactor-four subgroup point `(1654986373106,1310318707590)`.

The worker stores only disjoint first-slot and second-slot point sums. For
each target orientation, third-slot state `C`, and right-pair state `R`, it
looks up the exact key `target − C − R`; left-pair witnesses are expanded
only on an index hit. `TwoPlusOneJoin.exact_pair_lookup` proves that this
key preserves every five-point sum in an arbitrary commutative group. The
native worker then enforces all ten folded columns distinct and rechecks
the group sum. This is a target-conditioned partial-sum family test: a
missing key rejects the entire family of left-pair witnesses for that
`(C,R,target)` without expanding them.

| Frozen W9 public-point run | Three-plus-two table, earlier run | Two-plus-one target lookup |
| --- | ---: | ---: |
| Reusable left index entries | 21,868,032 triples | 79,424 pairs |
| Precomputed right-pair entries | Generated during query | 79,424 pairs |
| Target-conditioned lookups through hit | 317,569 right pairs | 83,612,805 `(C,R)` families |
| Parent wall seconds | 22.410 | 292.425 |
| Sampled peak RSS | 1,286,029,312 B worker | 35,471,360 B combined parent and worker |
| Relation orientation and state IDs | `3`, `(0,130,233,283,152)` | `3`, `(0,130,233,283,152)` |

The two wall measurements are separate ordinary-host runs, and the RSS
boundaries differ (worker only versus combined). Their roughly 36-fold RSS
and 13-fold wall ratios describe these recorded runs, not an isolated
speedup comparison. The indexed worker built each pair table in less than
0.2 worker seconds, completed orientations 0, 1, and 2 without a match,
and found the exact relation after 18,008,709 probes in orientation 3.
Across the run it made 83,612,805 target-conditioned lookups. The full raw
logs, source and binary hashes, compiler command, resource protocol, checked
Sage runtime receipt, Sage replay, Lean proof, and `python3 verify.py` are
preserved here. `candidate_id` is null.

The index-memory reduction alone does not scale the method to the frozen
N131 workload. The earlier W9/W29 directory's audited `sample_result.json`
(SHA-256 `2e22b5f396a859e3ce2a36ad02a97aa5afb4623e0ed13a257f5ddd400c3683a6`)
and `sample_audit_result.json`
(SHA-256 `69e4a228b1a55858113a56ed726e2bd68c84dd16e22dca758170f4eec6aa2f27`)
report 16,677 eligible canonical masks in 65,536 draws. Extending that fraction to the
`2^28` canonical-mask domain and four signed states per eligible edge gives
a **sample-based projection** of 273,235,968 states per slot, hence roughly
`7.47 × 10^16` two-state entries before column filtering. An illustrative
32-byte entry representation would use about `2.39 × 10^18` bytes. This
is a conditional size calculation, not an exact N131 census or a measured
memory requirement.

The next algorithmic gate is an **implicit left-pair membership oracle**:
given the target-conditioned key, decide whether two admissible source
pairs can sum to it and return exact witnesses without materializing the
quadratic-size pair table. Test that oracle against this N41 run's frozen
keys and independently replayed hit, charging failed probes, before
promoting it to the N131 public-point cap.
