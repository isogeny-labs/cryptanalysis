# N83 one-slot compact-hash result

The exact 16-byte open-addressed slot reduced root-table allocation from
192.0 MiB to 128.0 MiB on the frozen Q1325 N83 stream. It retained the
hash arm's 18,616,995 target probes, 4,000,000 distinct keys and identical
first-witness samples. Its median target-dependent stage took 4.383 s,
versus 3.812 s for the separate key/value hash and 4.601 s for the sorted
23-bit reversed-prefix table. The [independent audit](audit.py) replayed the
pre-call source seal, nine raw results, operation counts, lookup samples and
recomputed summary. Every call ended at `state_cap_no_relation` after the
same 2,000,000 index states and zero table hits.

The [protocol](protocol.json) was pushed at `cdc58e3f5` before measurement.
It fixes the Q1325 base (30,977,592 actual points and 186,612 folded
columns), field modulus `z^83+z^7+z^4+z²+1`, subgroup order
`2417851639230796216685689`, public target
`(7378557141477440425043731, 6374944737560147782643405)`, coprime
state stride, one target orientation, a 1,024 MiB peak-RSS cap and a
180-second process cap per call. The nine-call order is hash, compact hash,
packed 23, compact hash, packed 23, hash, packed 23, hash, compact hash.

| Layout | Median index build s | Median target stage s | Target probes/comparisons | Table MiB | Median peak RSS MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Separate key/value hash | 1.699 | 3.812 | 18,616,995 | 192.0 | 724.4 |
| One-slot compact hash | 1.947 | 4.383 | 18,616,995 | 128.0 | 628.4 |
| Reversed sorted prefix 23 | 1.631 | 4.601 | 12,382,142 | 132.7 | 569.1 |

The compact slot saved one-third of allocated table bytes and about 96 MiB
of process peak RSS against the separate hash. Its median stage was 1.150×
slower than that hash, while 1.050× faster than the sorted packed arm.
The run order exposes substantial first-call warmup on all three layouts;
these local arm64 macOS times are L0 diagnostics without a Tier 1 or Tier 0
timing envelope. `candidate_id`, complete one-target IC time and same-point
rho speedup remain null. The primary retained-base sweep uses a different
field polynomial and needs an explicit basis conversion for transfer.

The next exact layout can keep the 16-byte slot but split its two 64-bit
halves so an empty probe reads only the half carrying the sentinel. It
requires the same first-witness and paired target-stream checks before
interpreting any speed change.

Replay from the repository root:

```sh
python3 experiments/koblitz-n83-index-design-20260929/packed_index_e1_compact_hash_20261019/audit.py
```
