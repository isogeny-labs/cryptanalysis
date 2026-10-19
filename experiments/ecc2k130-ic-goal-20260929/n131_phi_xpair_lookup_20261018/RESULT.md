# Exact negation-quotiented Q1358 pair lookup

An exact `x`-keyed pair index covers all **1,132,096** signed sums of Q1358
phi slots 0 and 1 with **566,048** entries. A lookup restores the required
two leaf signs, recomputes their group sum, and accepts only exact equality
with the target-conditioned key. On the frozen N131 domain, this halved the
stored entries and reduced the measured build from 72.287 s to 51.004 s and
sampled peak RSS from 386,924,544 B to 203,603,968 B. These are one-worker
ordinary-host component measurements; their roughly 1.42-fold build-time
ratio is not an end-to-end IC or isolated speedup claim.

## Frozen inputs and exact method

The curve ID is `EC1N131Ckb1heb5f1998f20b`, the public-point workload ID is
`3c1992b7c92f`, and the [protocol](protocol.json) pins the checked Sage
runtime, source geometry, all executable hashes, seeds and caps. The factor
base has 532 valid phi codes in each position and two signed point choices
per code. The full index stores each group point and its leaf witness.
The `x` index stores one representative sum and witness for each pair
`{S,-S}`. On an `x` hit it compares the stored and requested `y` coordinates;
if they differ it negates both leaf witnesses. It then recomputes their exact
sum. The conditional sign-lift rule is [proved in Lean](PROOF_MAP.md).

| N131 index arm | Full-point key | `x` key |
| --- | ---: | ---: |
| Signed pairs covered | 1,132,096 | 1,132,096 |
| Stored entries | 1,132,096 | 566,048 |
| Group additions during build | 566,048 | 566,048 |
| Build time inside script | 72.287 s | 51.004 s |
| Peak process RSS | 386,924,544 B | 203,603,968 B |
| 256 known-witness lookups | 0.0448 s | 0.0382 s |
| 1,024 target-conditioned queries, including right-family construction | 0.473 s | 0.354 s |

The two arms ran separately through the repository's checked Sage launcher,
with one worker, a 600 s build cap and 4 GiB RSS cap. The 256 planted
lookups in each arm returned their exact input witnesses. The ordinary-query
panel used 256 seeded three-leaf right partial sums at positions 12–14 and
all four archived public-point fiber endpoints. Both arms probed the same
1,024 residual points and recorded zero pair-index hits. This is a
five-leaf family diagnostic, not a natural 15-leaf relation-yield estimate.

The [independent four-sign audit](audit_result.json) performed 1,132,096
direct additions, confirmed 1,132,096 distinct point keys and 566,048
`x` keys, replayed the 256 positive controls and all ordinary query keys,
and returned `PASS_INDEPENDENT_FOUR_SIGN_KEYSET_AND_QUERY_REPLAY` in
92.256 s at 303,857,664 B peak RSS. The [N41 public-target control](n41_control_result.json)
rebuilt an `x`-keyed index over 80,656 archived left-pair states, found the
independently replayed public relation at orientation 3 and left IDs
`(0,130)`, and rejected all 1,024 sampled incompatible target-conditioned
families by absent keys. [verify.py](verify.py) returned `REPLAY_PASS` for the
frozen sources, both N131 runs, the independent audit and the N41 hit.

## Raw-lift coset audit and next search gate

The [supplementary coset audit](coset_audit.json) checked all 532 raw phi
lifts against the exact subgroup order. Raw lifts occupy all four cofactor
torsion classes; so do signed pair sums. All 1,024 ordinary residual queries
were torsion eligible. The initially attempted subgroup-only assertion failed
and is retained in [coset_attempt1_failure.json](coset_attempt1_failure.json)
with its exact [first source](coset_audit_attempt1_sage.py). The first N41
conversion attempt and its refrozen repair are likewise retained in
[attempt1_failure.json](attempt1_failure.json), its exact
[first source](n41_control_attempt1_sage.py), and
[protocol_attempt1.json](protocol_attempt1.json).

The index supplies an exact expected-constant-time hash lookup for rejecting
an incompatible pair family, but a
uniform full-curve model puts a random residual hit near
`1,132,096/(4r) = 4.16 × 10^-34`, where `r` is the pinned prime subgroup
order. That model predicts roughly `2^110.89` unrelated residual probes per
hit. The next algorithmic task is therefore to generate *structured,
target-compatible middle partial families*; random right-family sampling
cannot use this index to reach a 15-leaf relation within the stated cap.
