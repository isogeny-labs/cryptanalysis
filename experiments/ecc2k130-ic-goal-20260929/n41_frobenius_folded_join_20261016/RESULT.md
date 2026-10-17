# Frobenius-folded triple reuse in the N41 public-point join

**The six-slot N41 source has an exact three-slot Frobenius copy.** Every state in slots 3, 4, and 5 is the `2^18`-Frobenius image of the same-index state in slots 0, 1, and 2. The folded join builds each compatible left triple sum once, applies Frobenius to that sum for the right probe, and recovers the same public-point relation as the archived direct three-plus-three join. This removes the right-side triple group additions for the 1,100,323 probes made before the first accepted hit. It retains one target subtraction and hash probe per right triple.

## Construction and correctness

The input is the frozen 960-state, six-slot source on `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t^3+1)`, with six rotations `(0,6,12,18,24,30)` and raw public point `(2026560328086,1928332930914)`. Each slot has 160 signed states. The source input SHA-256 is `7fc0362121ecc510d9ec9ea62a17c1efc878cd96fed7292246675c1951f006fb`.

Let `F` be point Frobenius to the eighteenth power. The source satisfies `P_{j+3,i}=F(P_{j,i})` for every `j=0,1,2` and `i=0,...,159`. Since `F` preserves addition, the right triple indexed by `(a,b,c)` has sum `F(P_{0,a}+P_{1,b}+P_{2,c})`. The code uses a 6×256-byte-indexed table for the field map, verifies all 480 point correspondences and all 76,800 pairwise column-compatibility correspondences before the join, then retains the ordinary exact target lookup and full hit replay. The independent [audit](audit_result.json) reconstructs the field arithmetic separately, repeats those checks, and verifies the twelve distinct columns and the complete six-point target sum for the hit.

The target lookup returned the same IDs `(12,122,116,47,128,34)` and the same `(1,100,323 probes, 3 coordinate matches)` in all four direct A/B/B/A measurements. The independent raw sums are left `(2016441755294,1506714436645)` and right `(2022264776108,885920745014)`; their sum is the frozen public point.

## Matched diagnostic

The [v3 protocol](protocol_v3.json) freezes both source and binary hashes, compiler flags, input, order, one worker, a 180 s per-run cap, and a 4 GiB RSS boundary. These are ordinary-host component timings. The parent clock includes input reading and table construction. `RUSAGE_CHILDREN.ru_maxrss` is a cumulative maximum across children; the first baseline and first folded readings are attributable to their respective runs, whereas later readings are only an upper envelope.

| Order | Arm | Parent wall | Worker hit clock | Child RSS reading |
| --- | --- | ---: | ---: | ---: |
| 1 | Direct | 5.982 s | 5.597 s | 223,576,064 B |
| 2 | Folded | 6.477 s | 6.058 s | 343,638,016 B |
| 3 | Folded | 6.287 s | 5.951 s | cumulative 343,638,016 B |
| 4 | Direct | 7.740 s | 7.386 s | cumulative 343,638,016 B |

The wall ranges overlap. The structural reduction is exact, but this implementation has no isolated wall-time win: its extra vector of 3,750,144 triple records raises memory, and Frobenius transforms plus target subtraction still dominate right probes. It is a source-specific implementation experiment, `candidate_id: null`, with the same public target and frozen source in both arms. It does not yet meet the N131 implicit-family requirement: materializing its W23 triples is far beyond the declared 4 GiB gate.

The first `/usr/bin/time -l` wrapper completed each child and printed the same hit, then returned exit 1 because sandboxed `sysctl kern.clockrate` was denied. Its [four-run receipt](result.json) and stderr are retained as wrapper failures. The subsequent `ps`-polled monitor was denied by the sandbox before producing a complete comparison; its protocol and source are retained. The direct v3 runner supplied valid child exit codes and the matched result.

## Formalization and next experiment

[FoldedJoin.lean](FoldedJoin.lean) proves that an additive map transports a three-point sum and that the target-conditioned lookup is equivalent to full equality. Lean 4.34.1 builds both theorems; `#print axioms` reports no axioms. The [proof map](PROOF_MAP.md) records the concrete field/curve and native-code bridges supplied by finite independent checks.

The next implementation step is to stream the reusable triple sums through a compact representation or recompute only low-cost metadata, then measure whether the saved right additions exceed Frobenius and target-lookup costs without a second large vector. Before transfer to N131, it must express the join on unresolved source families, because an explicit W23 triple list cannot fit the 600 s / 4 GiB gate.
