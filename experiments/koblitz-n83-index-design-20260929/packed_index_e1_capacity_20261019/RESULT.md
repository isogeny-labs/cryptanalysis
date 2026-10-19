# N83 four-million-state index capacity result

The exact split-slot root hash completed a 4,000,000-state N83 index and
scanned all 4,000,000 target states under the frozen 1,024 MiB sampled
peak-RSS gate. The separate key/value hash reached `memory_cap_exceeded`
after 3,235,840 index states in both bracketed calls; target scanning did
not start in those calls. At the same gate, the split layout admitted
764,160 more indexed states, a 23.62% increase over the hash stopping
point. The [independent audit](audit.py) checks the pre-call source commit,
four first-attempt raw receipts, input hashes, exact RSS boundary and
recomputed summary.

The [protocol](protocol.json) was pushed at `7d41c7aa6` before execution.
It fixes the Q1325 base (30,977,592 points, 186,612 folded columns),
field modulus `z^83+z^7+z^4+z²+1`, subgroup order
`2417851639230796216685689`, public target
`(7378557141477440425043731, 6374944737560147782643405)`, and the
same coprime state permutation used by the 2,000,000-state panel. Calls
ran hash, split, split, hash, with one target orientation, 4,096-state S3
windows and a 180-second outer process cap each. The 1,024 MiB memory
gate is the worker's sampled process peak after each index window; it is
not an OS hard limit.

| Layout | Calls | Index states | Table MiB | Peak RSS MiB | Target states | Recorded outcome |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Separate key/value hash | 2 | 3,235,840 each | 384.0 | 1,024.20 | 0 | `memory_cap_exceeded` |
| Exact split slot | 2 | 4,000,000 each | 256.0 | 1,003.42 | 4,000,000 each | `state_cap_no_relation` |

The 1,024 MiB threshold is 1,073,741,824 bytes. Hash peaked at
1,073,954,816 bytes, 212,992 bytes above the sampled gate. Split peaked
at 1,052,164,096 bytes, 21,577,728 bytes below it. The split calls'
target-dependent stage times were 7.125 and 7.678 seconds, with a 7.401
second median; the hash calls have no comparable target-stage time because
they stopped during index construction. All four calls retain their exact
state counts and status, with no zero-yield assignment to the capped hash
arm. The two completed split calls had zero table hits at this query cap.

This is a measured E-1 index-capacity gain with exact first-witness
semantics on the declared field representation. It does not select a
factor base or a complete one-target IC runtime: `candidate_id`, natural
relation/rank evidence, final matrix solve and same-point rho ratio remain
unknown. The primary retained-base sweep uses a different field polynomial;
applying this storage layout there requires a pinned basis conversion and a
fresh end-to-end measurement. The local arm64 host has no Tier 1 or Tier 0
timing envelope, so the time values are stage diagnostics.

Replay from the repository root:

```sh
python3 experiments/koblitz-n83-index-design-20260929/packed_index_e1_capacity_20261019/audit.py
```
