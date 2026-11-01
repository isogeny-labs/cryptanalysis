# Reversed-prefix E-1 lookup result

An exact reversal of the 83-bit canonical root key reduced the packed
index's target lookup comparisons from 58,251,024 to 33,522,387 on the
frozen 2,000,000-state N83 stream. The median target-dependent stage was
4.442 s versus 5.213 s for the original packed layout, a 1.174× stage
ratio. The same-point hash arm took 3.988 s by its median. The [independent
receipt audit](audit.py) replayed the source seal, all nine raw calls,
first-witness samples, operation counts, target outcomes and summary.

The [protocol](protocol.json) was pushed at
`b915f02fd` before the calls. It fixed the Q1325 30,977,592-point base
(186,612 folded columns), GF(2^83) modulus `z^83+z^7+z^4+z²+1`, subgroup
order `2417851639230796216685689`, public target
`(7378557141477440425043731, 6374944737560147782643405)`, a coprime
stride over 2,890,395,199,152 quotient-pair states, one orientation per
selected state, a 1,024 MiB RSS cap and a 180-second process cap per call.
The sequence was `hash, packed, packed-rev, packed, packed-rev, hash,
packed-rev, hash, packed`. Every arm used the same first 2,000,000
selected states, found 4,000,000 distinct root keys, scanned the same
target stream and produced `state_cap_no_relation` with zero table hits.

| Layout | Median index build s | Median target stage s | Target lookups/comparisons | Table MiB | Median peak RSS MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hash | 1.798 | 3.988 | 18,616,995 | 192.0 | 724.5 |
| Packed, canonical prefix | 1.337 | 5.213 | 58,251,024 | 76.7 | 513.2 |
| Packed, reversed prefix | 1.350 | 4.442 | 33,522,387 | 76.7 | 513.1 |

The reversed prefix preserves the exact key and duplicate-key witness
semantics because bit reversal is bijective. The unit test checks hash,
original packed and reversed packed first-witness equality on duplicates;
the nine-call panel checks 64 actual lookup samples and every exposed
arithmetic-operation count across modes. The reversed layout reduced the
packed lookup count by 42.45% and kept its 2.50× table-memory advantage
over hash. Its stage time was still 11.36% above hash at this cap.

These arm64 macOS times are L0 stage diagnostics: the host has no frozen
Tier 1 or Tier 0 timing envelope, and the first call of each layout was
slower than its later calls. The full single-target online IC time and
same-point rho ratio remain unmeasured. `candidate_id`, `run_id`, and
`online_speedup` remain null. The primary retained-base sweep uses a
different field polynomial; transferring this layout requires a pinned
basis conversion and a new candidate measurement.

The next access variant can widen the reversible directory prefix within
the same 1,024 MiB cap. Four million root records over a 20-bit directory
average about four records per prefix. A 22-bit directory adds 24 MiB to
the table and may cut target lookup work. It must be compared on this same
stream before any conclusion about that change.

Replay from the repository root:

```sh
python3 experiments/koblitz-n83-index-design-20260929/packed_index_e1_revprefix_20261019/audit.py
```
