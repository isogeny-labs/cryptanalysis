# N83 split-slot root-hash result

The split `u64` slot matched the separate key/value hash's exact first
witness, 4,000,000 distinct roots, 18,616,995 target probes, operation
counts and target outcome on all nine sealed calls. Its allocated table was
128.0 MiB versus 192.0 MiB for the separate hash, with median process
peak RSS of 628.4 versus 724.5 MiB. Median target-dependent stage times
were 4.028 and 4.032 seconds respectively. The 4.5 ms difference is
within this host's observed variation. The [independent audit](audit.py)
verified the source seal, all raw first-attempt receipts and the recomputed
summary; every arm ended at `state_cap_no_relation` after the same 2,000,000
index states and zero table hits.

The [protocol](protocol.json) was pushed at `e9a35206d` before execution.
It fixes the Q1325 factor base (30,977,592 points and 186,612 folded
columns), field modulus `z^83+z^7+z^4+z²+1`, subgroup order
`2417851639230796216685689`, public target
`(7378557141477440425043731, 6374944737560147782643405)`, coprime
state stride, one target orientation, 4,096-state S3 windows, a 1,024 MiB
peak-RSS cap and a 180-second process cap per call. The three layouts ran
in the order hash, packed `u128`, split `u64`, packed `u128`, split `u64`,
hash, split `u64`, hash, packed `u128`.

| Layout | Median index build s | Median target stage s | Target probes | Table MiB | Median peak RSS MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Separate key/value hash | 1.848 | 4.032 | 18,616,995 | 192.0 | 724.5 |
| Packed `u128` slot | 1.839 | 4.071 | 18,616,995 | 128.0 | 628.5 |
| Split `u64` slot | 1.852 | 4.028 | 18,616,995 | 128.0 | 628.4 |

This panel establishes a one-third table-allocation reduction with the
same measured local stage-time range as the separate hash. The arm64 macOS
host has no Tier 1 or Tier 0 timing envelope, so it does not establish a
speedup. The table fits an exact 83-bit key and a 45-bit descriptor, with
the all-ones high half reserved by the shift bound; the release test checks
the maximum valid key and descriptor. The primary retained-base sweep uses
a different field polynomial, so transfer requires an explicit basis map
and a newly measured complete candidate. `candidate_id`, full one-target
IC time and same-point rho speedup remain null.

The next measured gate is a qualified-host paired repeat with the same
single public point and resource envelope, followed by a capacity panel
that spends the 64 MiB table saving on additional indexed states. Natural
verified relation yield, useful rank and final linear algebra remain the
selection criteria for a complete factor base.

Replay from the repository root:

```sh
python3 experiments/koblitz-n83-index-design-20260929/packed_index_e1_split_slot_20261019/audit.py
```
