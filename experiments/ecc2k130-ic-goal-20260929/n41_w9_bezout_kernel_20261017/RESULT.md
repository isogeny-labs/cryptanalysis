# A normalized Bezout kernel witness for the N41 five-pair source

## Contribution

The final two N41 W9 pair quartics can be coupled by four **linear equations in a normalized Bezout kernel vector**. A genuine shared field root `w` supplies `(1,w,w²,w³)`, so fixing the first kernel coordinate to one preserves every source-valid decomposition. Conversely, any normalized kernel forces the Bezout determinant to vanish. The [Lean module](KernelWitness.lean) checks both structural implications and the quartic row identities under explicit characteristic-two assumptions.

The frozen circuit passed the archived relation and rejected all 32 source-valid reachable controls. It has **141,260 variables and 389,112 total constraints**, reductions of **4.89%** and **5.05%** from the preceding exact determinant circuit with the same five source codes and public point. The frozen four-arm, one-worker fixed-conflict probe completed; kernel arms used fewer decisions and propagations, while the two adjacent wall comparisons disagreed. Its predeclared full-query promotion gate therefore failed.

## Method and proof

The field is `GF(2)[u]/(u^41+u^3+1)` and the curve is `y²+xy=x³+1`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`, subgroup order `549756390943`. The public point is `Q=(1936680952394,910597499030)`. The five aligned W9 pair rotations are `(0,0,12,12,24)`, with 71 allowed source codes and four signed states per code. The circuit keeps the five eight-bit code words, preceding 41-bit reciprocal `z`, and three 41-bit kernel coordinates free. The first kernel coordinate is the constant one. Its full IC candidate remains `candidate_id: null`.

Let `B(z,p3,p4,Q)` be the symmetric four-by-four Bezout matrix of the two pair quartics in the [preceding circuit](../n41_w9_two_quartic_circuit_20261017/RESULT.md). This experiment replaces `det(B)=0` with `B·(1,u,v,s)ᵀ=0`. If the quartics share a root `w`, the Bezout quotient identity gives `B·(1,w,w²,w³)ᵀ=0`. If a normalized vector solves the four equations, the first-column cofactor identity gives `det(B)=0`. The standard Bezout determinant-resultant identity and the final quartic's checked four-root split then provide a common field root. The [proof map](PROOF_MAP.md) states the Lean-checked steps, exact hypotheses and remaining polynomial/curve formalization bridges.

## Frozen correctness and circuit measurements

The [independent Sage panel](kernel_result.json) checked the exact matrix on 33 frozen source-valid rows. The archived relation has rank three, and its source intermediate `w` gives a normalized kernel vector. All 32 controls have rank four. Sage's arithmetic interval was **3.064 s**, self peak RSS **210,927,616 B**, after the checked [runtime receipt](sage_runtime_info.json) was saved. The panel's hashes and 120-second cap were frozen in [kernel_protocol.json](kernel_protocol.json).

The [builder](build.py) retains the first-three-pair F4 norm, exact code restrictions and folded-column collision clauses. Its [receipt](build_result.json) records 33/33 expected Boolean decisions and a complete satisfying assignment for the archived relation. The full builder took **77.061 s**, including panel assignment checks, with self peak RSS **152,666,112 B** under its frozen 300-second/4-GiB envelope.

| Formula | AND gates | Variables | CNF clauses | Native XOR rows | Total constraints | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Prior Bezout determinant | 129,802 | 148,526 | 391,183 | 18,643 | 409,826 | 13,285,051 |
| Normalized kernel witness | **123,078** | **141,260** | **371,134** | **17,978** | **389,112** | **12,710,695** |

The [read-only verifier](verify.py) checks frozen source and solver hashes, the arithmetic and Boolean controls, XCNF counts and raw streams, Lean output, and that none of the 204 code/`z`/kernel input bits has a unit clause.

## Frozen fixed-conflict probe

The [probe protocol](probe_protocol.json) fixed one CryptoMiniSat worker, 20,000 requested conflicts, a 170-second solver limit, a 180-second parent cap, 4-GiB sampled combined RSS and serial determinant/kernel/kernel/determinant order. Every arm reported 20,001 conflicts and `INDETERMINATE`; no wall or RSS cap was reached. Raw streams and per-arm receipts are linked from [the aggregate result](probe_result.json).

| Arm | Formula | Wall seconds | Reported decisions | Reported propagations | Peak sampled combined RSS |
| ---: | --- | ---: | ---: | ---: | ---: |
| 0 | Determinant | 61.390 | 226,016 | 56M | 111,394,816 B |
| 1 | Kernel | 41.100 | 172,961 | 52M | 94,617,600 B |
| 2 | Kernel | 40.413 | 172,961 | 52M | 78,561,280 B |
| 3 | Determinant | 37.155 | 226,016 | 56M | 86,097,920 B |

The two adjacent kernel/determinant wall ratios were **0.669** and **1.088**. The same determinant formula varied by a factor of 1.65 across its two runs on this shared host. The frozen promotion gate required the kernel to finish both adjacent comparisons in at most 80% of determinant wall, with all monitors passing. The second pair failed that gate, so this experiment did not launch another 600-second ordinary query. The fixed-conflict counts show a smaller search trace at this boundary; they do not establish earlier relation recovery. A read-only [host probe](isolation_probe.json) reports Darwin, where the repository's strict Linux Tier 0 benchmark service cannot run. No Tier 1 allocation was used for this stage comparison.

## Next discriminator

The normalized vector exposes the shared-root condition through lower-degree row equations but introduces 123 free field bits. A source-preserving next variant sets `(u,v,s)=(w,w²,w³)` from one 41-bit root witness; only `w³` needs a new field multiplication because squaring is binary-linear. Freeze the new Boolean circuit, verify its archived relation and reachable controls, then compare fixed-conflict propagation and size under the same frozen input law before another ordinary N41 query. Promotion to N131 still requires an unpinned independently replayed N41 relation and a source-bound 600-second/4-GiB N131 feasibility gate.
