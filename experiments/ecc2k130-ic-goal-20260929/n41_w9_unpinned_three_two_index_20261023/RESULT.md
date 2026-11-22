# Direct source-mask decoding removes the right reciprocal-coordinate index

The N41 W9 source admits an exact **target-conditioned two-pair membership oracle** that stores no right reciprocal-coordinate index. Given a target-derived partial-sum point, the oracle solves the S3 quadratic for the second pair-output reciprocal, computes the fixed-seed source product from that root, and inverts an eight-dimensional binary-linear map to recover its canonical source mask. It checks source columns and the full group sum before accepting a witness. On 256 frozen keys, it returned the archived positive pair `(0,130)` and rejected the other 255; an independent exhaustive index of all **79,424** eligible signed pair sums agreed on every key.

The direct-mask decoder used **3.798 s mean query time** across an in-process ABBA comparison, against **3.679 s** for a 142-coordinate right index. The 3.3% ratio is a descriptive ordinary-host stage measurement. Its cost is 142 S3 root calls per key. This memory-time exchange is useful as a component but does not yet close the five-slot public-query budget: applying it at all **83,612,805** lookups of the earlier unpinned N41 two-plus-one join would require **11,873,018,310** quadratic root calls. At the measured N41 ABBA decoder rate that is about 14.4 days of one-worker query work; the calculation is an extrapolation from this panel, not a measured full join.

## Exact instance and method

The field is `GF(2)[u]/(u^41+u³+1)`, the curve is `y²+xy=x³+1`, and the curve ID is `EC1N41Ckb1h7d5e80d3c4d0`. The frozen W9 source has 71 valid pair codes and 284 signed states in each slot, with rotations `(0,6,12,18,24)` and seed mask 56. The public raw point is `(2026560328086,1928332930914)`; the input orientation is Frobenius power 3. The archived full relation has state IDs `(0,130,233,283,152)`. All 256 keys are `Frob³(Q_raw) − P₂ − P₃ − P₄` for frozen, source-valid suffix states. The first key uses the archived positive suffix; the other 255 were selected before querying by a fixed source-only generator. Slots 0 and 1 remain free in every oracle query.

For reciprocal x coordinates `a=1/x(P₀)`, `b=1/x(P₁)`, and `t=1/x(T)`, the nonexceptional S3 chart is quadratic in `b`:

`(1+(at)²)b² + (at)b + a²+t² = 0`.

The oracle loops over the 142 distinct left coordinates, computes every field root of this quadratic, and tests each right candidate. A fixed-seed pair-output root satisfies `C b²+p b+H=0` with `C=1+H`. Since `b` and `C` are nonzero, characteristic two gives

`p/C = b+(H/C)/b`.

The source product `p` is a binary-linear function of the canonical source mask. The direct decoder inverts its rank-eight image using eight pivot rows, yielding the exact nine-bit mask (one fixed canonical bit). Source validity is checked against the complete 71-code N41 census; the mask selects its four signed states, and exact point addition resolves the coordinate/sign ambiguity. The implementation independently checks the source quadratic and mask inverse for every one of the 284 right signed states and inverts all 256 canonical masks through the forward product map. A second variant decodes a rank-eight signature and uses a 71-entry signature table; it returned the same 256 decisions.

## Frozen measurements and controls

| Component | Keys | Root calls | Target-dependent query interval | Other observed result |
| --- | ---: | ---: | ---: | --- |
| Coordinate-index oracle, first panel | 17 | 2,414 | 0.534 s | 142 right-coordinate entries; one positive key |
| Coordinate-index oracle, larger panel | 256 | 36,352 | 7.028 s | One positive, 255 misses; 264,716,288 B self peak RSS |
| Rank-eight signature decoder | 256 | 36,352 | 7.396 s | Zero right-coordinate index entries; one positive |
| Direct canonical-mask decoder | 256 | 36,352 | 3.903 s | Zero right-coordinate index entries; one positive |
| Independent complete group index | 256 | 79,424 eligible pair sums built | 7.930 s build; 0.000144 s lookup | All 256 decisions match; 288,178,176 B self peak RSS |

The separately launched 7.028/3.903 s values are sensitive to host load. The paired in-process run froze the order `index, decoder, decoder, index`, used the same 256 keys and source points, and checked all outputs against the independent group census after each arm:

| Arm order | Index 1 | Decoder 1 | Decoder 2 | Index 2 |
| --- | ---: | ---: | ---: | ---: |
| Query seconds | 3.709 | 3.828 | 3.769 | 3.648 |

The reference index's 7.930 s construction is reusable source preparation and separate from target-dependent lookup; the oracle's small setup is also separate. All timings are ordinary shared-host stage diagnostics. The frozen protocol declares one worker, 120-second wall cap and 4-GiB RSS envelope for the 256-key components. The scripts completed within the wall cap and report self peak RSS, but they did not run a process-tree RSS watchdog, so this is not a certified 4-GiB cap receipt. The previously archived N41 full join and its same-source 83.6-million-probe count are separate frozen evidence. This directory is an oracle component with `candidate_id: null`.

The N131 W29 sample projects 68,308,992 valid pair codes over its full 28-bit canonical mask domain; this is a sample-based projection, not a full census. A direct transfer of the current left enumeration would therefore require about **136,617,984** S3 root calls for **one** target-derived key, before any outer five-slot search. A compact 28-pivot mask inverse is arithmetically plausible because the prior N131 source-product map was audited at rank 28, but this N41 implementation has not measured N131 root throughput, source-validity decoding, or a complete N131 public query. The next algorithmic step is to reject large left-code regions jointly with the public target before their individual S3 root calls; this is the compact family constraint sought in the active goal.

## Reproduction and proof boundary

`protocol.json`, `batch_protocol.json`, `decoder_protocol.json`, `mask_decoder_protocol.json`, and `paired_protocol.json` freeze source and script hashes before their respective runs. `sage_runtime_info.json` records the accepted checked Sage installation. All Sage jobs were launched through `/Volumes/SSD990/cryptanalysis/sage -python`. `verify_sage.py` checks all eligible group sums and the concrete S3 chart; `batch_audit_sage.py` separately constructs the full group index for the 256 keys. `OracleComplete.lean` contains the exact conditional oracle proof and the characteristic-two quadratic decoder identity. [PROOF_MAP.md](PROOF_MAP.md) names the open Lean bridges to the concrete curve and source encoding. Run `python3 verify.py` for a read-only receipt and hash audit of the frozen artifacts.
