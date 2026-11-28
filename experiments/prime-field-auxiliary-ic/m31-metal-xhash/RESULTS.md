# Exact GPU x hash after the M31 bitmap

The frozen protocol and source are at commit `d0179b25d`. The opt-in GPU screen tests a 22-bit x bitmap and then an exact 131072-slot x table built from the Rust `PairIndex` entries. Rust still performs exact point and first-witness replay. The fixed Q0 admission matched the 22-bit-only complete certificate digest, scalar, queries, relations and rank; its first screen's first lane agreed on every flag with a Rust affine-addition and exact x-membership reference. The admission is in `XHASH_ADMISSION.jsonl` and was excluded from timing. [pcc:unverified]

The fresh 30-arm panel compared the merged 20-bit Metal control and exact-x candidate on five public targets and three newly derived seeds. Every answer passed independent affine multiplication, and every matched pair had the same complete certificate digest, queries, relation count and rank. No arm failed, timed out or was censored. `verify.py` passed. The source and binary hashes, schedule, raw stdout/stderr and phase records are in `XHASH_MANIFEST.json` and `XHASH_RAW.jsonl`. [pcc:unverified]

| Metric | 20-bit control | Exact-x after 22-bit bitmap |
| --- | ---: | ---: |
| Median charged process wall, 15 arms each | 151.564 ms | 120.603 ms |
| Median charged child CPU, 15 arms each | 89.513 ms | 61.716 ms |
| Median GPU-positive candidates | 1,561,202 | 1,458 |
| Median Rust exact lookups | 1,165,945 | 198 |
| Median accumulated GPU screen | 40.026 ms | 37.448 ms |
| Median paired control/candidate wall ratio | — | **1.255×** |
| Median paired control/candidate CPU ratio | — | **1.458×** |
| Candidate wins, wall / CPU | — | **15/15 / 15/15** |

The prespecified ≥1.20 wall and CPU median gates and ≥12/15 win gates passed locally. These medians are producer-run measurements on a shared Apple M4 Pro host; they are not a signed independent performance verdict. The reduction in Rust lookups explains a plausible mechanism, but the phase clocks alone do not isolate GPU and CPU causal contributions. The Lean `XFilter.lean` theorem supplies the semantic first-witness guarantee when rejected x coordinates truly are absent; it does not establish that the compiled GPU table realizes that premise or prove the measured runtime. [pcc:unverified]

## Matched archived rho distance

`RHO_PROTOCOL.md` was frozen before outcomes. All 15 archived C++ rho processes completed on the same public Q and walk seeds, and an independent Python affine multiplication checked each scalar. Its median charged process wall and child CPU were 15.621 and 13.118 ms. Median paired exact-x IC/rho ratios were **7.536× wall** and **4.673× child CPU**. The wide paired wall range, 1.217–17.555×, reflects visible host variation and should not be pooled with the IC-vs-IC gain. `RHO_MANIFEST.json` fixes the source and binary hashes; `RHO_RAW.jsonl` retains all 15 outcomes. This archived rho is a distance control, and the exact-x index calculus remains slower on the median single-target comparison. [pcc:unverified]

## Fresh-seed confirmation

The independently seeded `CONFIRM_PROTOCOL.md` kept the source, workload, timing boundary and ≥1.20 paired wall/CPU gate unchanged. All 30 fresh-process arms completed; `verify_confirm.py` independently checked every public answer and all 15 matched pairs had identical complete certificate digests, queries, relations and rank. No arm failed or timed out. Raw records and hashes are in `CONFIRM_RAW.jsonl` and `CONFIRM_MANIFEST.json`. [pcc:unverified]

| Metric | 20-bit control | Exact-x candidate |
| --- | ---: | ---: |
| Median charged wall, 15 arms each | 165.249 ms | 141.574 ms |
| Median charged child CPU, 15 arms each | 90.394 ms | 61.415 ms |
| Median GPU-positive candidates | 1,559,442 | 1,462 |
| Median Rust exact lookups | 1,152,648 | 200 |
| Median accumulated GPU screen | 55.613 ms | 57.072 ms |
| Median paired control/candidate wall ratio | — | **1.194×** |
| Median paired control/candidate CPU ratio | — | **1.480×** |
| Candidate wins, wall / CPU | — | 15/15 / 15/15 |

The confirmation **missed the frozen 1.20× wall gate**. The first panel passed, and both panels show an operational gain in these local runs, but the prespecified selection rule requires the fresh-seed confirmation to pass. The exact-x candidate is therefore not promoted as the default. The result is compatible with the expected CPU replay reduction; it is not independent performance standing or a proof of a rho crossover. [pcc:unverified]
