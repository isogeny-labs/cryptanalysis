# Paired Metal x-coordinate screen

The frozen source and protocol are at commit `17ea02bae`. Mode 3 fuses the target-minus and target-plus x-coordinate calculations for each pair entry, using one inverse of the shared ordinary denominator. Identity and equal-x cases call the prior candidate routine. Mode 2 is the exact-x GPU control with the same coarse/fine bitmaps, exact x table, output order and Rust witness replay. [pcc:unverified]

The fixed Q0 admission checked **every flag in the first 64-lane GPU round** against Rust affine addition and exact x membership for both modes. Their full ordered flag digests, complete certificate digests, scalar, queries, relations and rank matched. `edge_check.swift` also compared all 32 flags from four inputs (identity, P, −P and 2P) against the original kernel, including vertical and tangent outputs. Admission and edge checks were excluded from timing. [pcc:unverified]

The fresh 30-arm panel used five public Q and three new seeds. All 30 answers passed independent affine multiplication; all 15 matched pairs had identical complete certificate digests, queries, relations and rank. `verify.py` passed, with no failures or censored arms. `PAIRED_MANIFEST.json` fixes source and binary hashes and schedule; `PAIRED_RAW.jsonl` retains each process record. [pcc:unverified]

| Metric | Exact-x control | Paired x candidate |
| --- | ---: | ---: |
| Median charged wall, 15 arms each | 148.720 ms | 131.872 ms |
| Median charged child CPU, 15 arms each | 68.278 ms | 68.048 ms |
| Median accumulated GPU screen | 54.262 ms | 37.900 ms |
| Median GPU-positive candidates | 1,476 | 1,476 |
| Median Rust exact lookups | 202 | 202 |
| Median paired control/candidate wall ratio | — | **1.159×** |
| Median paired control/candidate CPU ratio | — | **1.004×** |
| Candidate wins, wall / CPU | — | 15/15 / 11/15 |

The candidate reduced the measured screen phase but **failed the frozen ≥1.20 wall and CPU gates**. It is not selected as a replacement for mode 2. This is a local producer comparison, not independent PCC standing. A direct same-target comparison against the merged 20-bit Metal path is needed to determine the joint effect; ratios from separate panels must not be multiplied into a claimed end-to-end gain. [pcc:unverified]
