# Target-orbit coverage bound for fixed-prefix W23 relation searches

**An exact finite-image bound locates the N131 frontier for target-independent fixed-prefix searches at five or six unresolved W23 pair slots.** With one signed pair state fixed and the other five free, even a perfect 131-orientation completion oracle reaches at most **0.0002506285113438053** of uniformly selected subgroup targets per fixed state. At least **1,995** fixed-state trials are necessary before the union bound *permits* 50% subgroup-target coverage. Searching one uniformly selected raw preimage instead gives a fourfold smaller per-state ceiling and a threshold of **7,980** trials. Fixing two pair states leaves four free and raises the subgroup threshold to **8,372,694,666** trials.

These are coverage ceilings under the stated input laws. They do not estimate the success probability of the frozen published point, and reaching a threshold does not guarantee a relation. The bounds count every source state as a separate label and ignore column conflicts, so they remain valid when actual source compatibility only removes tuples.

## Counting theorem

Let `G=E(GF(2^131))` have order `4r`, with `r=680564733841876926932320129493409985129`. The frozen W23 source has `E=1,049,218` usable pair edges and `M=4E=4,196,872` signed states per slot. Fix any source states in `6−h` slots. Each labeled tuple in the remaining `h` slots, together with one of the 131 Frobenius orientations, emits **one** raw group point after inverse Frobenius and **one** subgroup target after cofactor-four projection. Consequently the sets of distinct reachable raw and subgroup targets each have cardinality at most `131M^h`.

For a uniform subgroup target, the reach probability is at most `min(1,131M^h/r)`. For a uniform raw point it is at most `min(1,131M^h/(4r))`. A deterministic rule selecting one of a subgroup target's four raw preimages retains the subgroup ceiling; its average need not equal the uniform-raw value. For `k` prefixes selected independently of the target, the union bound multiplies either ceiling by at most `k`, including a schedule that chooses the next prefix from earlier miss bits: every unsuccessful run follows the same all-miss path. The 50% thresholds below are the first `k` for which that upper bound reaches one half. **Target-dependent prefix selection is outside this bound.**

| Free pair slots `h` | Uniform subgroup ceiling per fixed prefix | Minimum prefixes before 50% is permitted | Uniform raw threshold |
| ---: | ---: | ---: | ---: |
| 2 | `3.39041845076035e−24` | 147,474,421,597,684,593,869,297 | 589,897,686,390,738,375,477,186 |
| 3 | `1.42291522642795e−17` | 35,139,127,807,015,462 | 140,556,511,228,061,846 |
| 4 | `5.97179307216911e−11` | 8,372,694,666 | 33,490,778,663 |
| 5 | `2.50628511343805e−4` | **1,995** | **7,980** |

For the 600-second, one-worker N131 gate, the five-free topology would need an equivalent rate of at least **3.325 fixed prefixes/s** under the subgroup ceiling, or **13.3 prefixes/s** under the uniform-raw ceiling, if the whole cap were spent on those trials. The corresponding time allowances are 300.75 ms and 75.19 ms per prefix. These necessary throughput conditions are not runtime predictions for a five-free solver. The four-free subgroup threshold alone would demand about 13.95 million prefix trials per second for 600 seconds, before charging any completion work.

## Four raw preimages and the N41 control

The independently audited W23 six-slot count bounds the number of compatible labeled signed tuples. Averaging after cofactor projection over subgroup targets and summing **all four raw preimages** gives an orbit-summed mean in

`[1051.765558320160835…, 1051.840744031034527…]`.

Averaging over **one uniformly selected raw preimage** and its 131 conjugates gives exactly one quarter as much:

`[262.941389580040208…, 262.960186007758632…]`.

The earlier N41 orbit experiment selected one raw preimage. Its first-hit native search verified one relation in each of 41 orientations; those 41 relations used 35 distinct slot-zero signed states and gave matrix rank 41. These are observed **lower bounds** on that fixed point's relation and fixed-state coverage because the worker stopped at its first hit in each orientation. The N41 source's exact 10,672,346,234,880 labeled six-pair tuples give a separate uniform-raw orbit mean of 198.98185943755945; that average is not substituted for the observed fixed-point count.

The [versioned erratum](ERRATUM.md) corrects the prior orbit report's use of the all-four-preimage mean next to a one-raw-preimage query. [protocol.json](protocol.json) hashes the two independent W23 censuses, exact source bound, N41 source count and verified orbit relations. [result.json](result.json) stores every ceiling and threshold as an exact rational or integer; [terminal.json](terminal.json) independently checks the arithmetic and hashes. The pinned Lean [finite-image theorem](Coverage.lean) proves that removing duplicate targets from the emitted tuple-orientation list cannot increase its length. The [proof map](PROOF_MAP.md) records the concrete curve and averaging bridges.

## Next algorithmic gate

A completion primitive on only two, three, or four free W23 slots cannot supply broad uniform-target coverage at a few thousand **target-independent** fixed-prefix trials, even if it decides each residual exactly. The next design should keep **at least five pair slots jointly unresolved**, or derive a target-conditioned rule for choosing prefixes whose induced coverage is measured separately. It should use the public target and its Frobenius orbit before expanding signed source states. A candidate must first recover an unpinned N41 public relation with complete target-dependent costs, then pass a source-bound projection for the frozen N131 one-worker, 600-second, 4-GiB query. The eventual factor-log, target descent, and matched same-point rho stages remain part of the active IC goal; this coverage study has `candidate_id: null`.
