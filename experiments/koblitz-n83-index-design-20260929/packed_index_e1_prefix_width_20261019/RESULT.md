# N83 reversible-prefix width result

A 23-bit directory reduced target lookup comparisons to 12,382,142 on the
frozen N83 stream, from 33,522,387 with a 20-bit directory and 18,616,995
hash-table probes. Its median target-dependent stage took 4.413 s, compared
with 4.661 s at 20 bits and 3.697 s for hash. The [independent audit](audit.py)
verified the pre-call source seal, fifteen first-attempt raw receipts, equal
first-witness samples, operation counts, target streams and recomputed
medians. All fifteen calls returned `state_cap_no_relation` at 2,000,000
index states and zero table hits.

The [protocol](protocol.json) was pushed at `bfcc8ff51` before execution.
It holds the Q1325 base, exact field representation and public target from
the preceding reversible-prefix panel fixed, with three calls per layout
and a rotated order. Each call used one target orientation, a 1,024 MiB
peak-RSS cap, 4,096-state S3 windows and a 180-second process cap. The
source field modulus is `z^83+z^7+z^4+z²+1`, and the subgroup order is
`2417851639230796216685689`. The target point is
`(7378557141477440425043731, 6374944737560147782643405)`.

| Layout | Median index build s | Median target stage s | Target lookups/comparisons | Table MiB | Median peak RSS MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hash | 1.712 | 3.697 | 18,616,995 | 192.0 | 724.5 |
| Reversed prefix 20 | 1.195 | 4.661 | 33,522,387 | 76.7 | 513.1 |
| Reversed prefix 21 | 1.419 | 4.469 | 26,152,331 | 84.7 | 521.1 |
| Reversed prefix 22 | 1.348 | 4.662 | 18,971,138 | 100.7 | 505.1 |
| Reversed prefix 23 | 1.303 | 4.413 | 12,382,142 | 132.7 | 569.1 |

The packed 23-bit table used 132.7 MiB, 1.45× less allocation than hash;
its median stage remained 1.194× slower. Lookup counts fell monotonically
as the prefix widened, while stage times did not. This separates the cost
of comparisons from directory-cache and record-access costs on this host.
The 21- and 23-bit stage ranges overlap, so this L0 local panel does not
select a timing winner between them. It also has no Tier 1 or Tier 0 host
envelope. `candidate_id`, complete single-target IC time and same-point
rho speedup remain null.

The next concrete layout is a 16-byte open-addressed slot carrying the
83-bit exact root key and a bounded state descriptor in one load. It can
preserve the hash arm's first-witness policy while reducing its 24-byte
key/value payload per slot. A paired control must validate exact lookup
semantics and target results before interpreting any timing difference.

Replay from the repository root:

```sh
python3 experiments/koblitz-n83-index-design-20260929/packed_index_e1_prefix_width_20261019/audit.py
```
