# N83 E-1 RunPod capacity replay

The exact 16-byte split-slot root index reduced sampled peak RSS by **192 MiB**
and table allocation by **128 MiB** against the separate-key/value hash
layout on one RunPod CPU Pod. Both layouts completed the sealed
four-million-state index and four-million-state target scan below the
1,024 MiB worker-sampled peak-RSS gate. The earlier local macOS hash cutoff
did not recur on this Linux allocation; the capacity threshold depends on
the allocator and host.

The public workload uses `EC1N83Ckb1h876c2921cb64`, field modulus
`z^83 + z^7 + z^4 + z^2 + 1`, subgroup order
`2417851639230796216685689`, Q1325's 30,977,592 usable factor-base
points (186,612 folded columns), and target
`(7378557141477440425043731, 6374944737560147782643405)`. The
factor-base set digest is
`56c951ad78cc4036d3e8ff70bcb9d7feccacc6c763220b285def056cba30afb8`.
This polynomial representation differs from the primary retained-base
sweep. The stage source and Linux dependency graph were sealed at
`b57a02234` before the first measured call; the protocol SHA-256 is
`a30baec1798483e73a5bac98db45a9c89dd0994dc35304f4323fef9b7d56ecf8`.

| ABBA call | Layout | Index states | Target states | Peak RSS (MiB) | Table (MiB) | Index build (s) | Target stage (s) | Recorded status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | hash | 4,000,000 | 4,000,000 | 1,012.5 | 384 | 3.4318 | 7.1448 | `state_cap_no_relation` |
| 2 | split | 4,000,000 | 4,000,000 | 820.5 | 256 | 3.2878 | 7.4629 | `state_cap_no_relation` |
| 3 | split | 4,000,000 | 4,000,000 | 820.5 | 256 | 3.4553 | 7.0816 | `state_cap_no_relation` |
| 4 | hash | 4,000,000 | 4,000,000 | 1,012.5 | 384 | 3.5305 | 7.1305 | `state_cap_no_relation` |

Median index-build time was 3.4811 s (hash) and 3.3715 s (split). Median
target-stage time was 7.1376 s (hash) and 7.2723 s (split); these two
repeats per layout do not support a target-stage speed claim. Each arm
found eight million distinct root keys and zero target table hits under the
frozen state cap. Exact first-witness samples and the native
generator/target control match across all four arms. The next selection
step is a same-point scalar-recovery comparison; `candidate_id`, IC online
time, rho online time, and online speedup remain `null` in the record.

The allocation was RunPod Pod `r6r84q42t4ji5j`, reported as 8 vCPUs,
16 GiB RAM, zero GPUs, and $0.24 per active hour. It exposed an AMD EPYC
9655 host, an eight-CPU affinity set, `cpu.max=max 100000`, and a 16 GB
cgroup memory limit. The four calls recorded zero cgroup throttle events
and zero host steal-jiffy deltas; before/after calibration ratios ranged
from 1.0015 to 1.0349. The Pod was stopped after the evidence archive was
copied and its SHA-256 verified as
`6a1ef7b3d0f56d598a182f2fb5ebbac049ab86a8ebd277b82d39e84dd5d2aa7a`.
The raw files, build receipt, host probes, and first-attempt records are
beside this report. This single-point stage panel precedes the five
fresh-point same-target IC/rho Tier 1 timing panel in the benchmark contract.

From a clean checkout of the pinned `crypto` commit
`46416a4129c299dad4b1fd62d1a620dbd0d34317`, run:

```sh
N83_CRYPTO_ROOT=/path/to/clean/crypto-commit-46416a4 python3 -B audit.py
```

The independent audit returns `PASS_SEALED_RUNPOD_TIER1_STAGE_REPLAY` after
checking the sealed source commit, input digests, all raw rows and summary
arithmetic, first witnesses, and exposed resource counters.
