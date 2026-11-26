# Native table build and 1,013-point M31 auxiliary basis

Status: local producer evidence `[pcc:unverified]`, Apple M4 Pro, 2026-11-25. The 144-arm frozen panel in `RAW.csv` completed without failure or censoring. Each of the 48 basis/size/seed/round blocks contained a fresh-process Rust control, native table with Rust collector, and native table with fused native collector. All arms regenerated the public basis, charged the full wall and parent-plus-child CPU interval, checked each accepted relation, and verified the scalar `123456789` by generator multiplication.

Preflight checked 1,097,730 batch-inverse outputs. Independent Python affine addition checked 1,502 outputs per 500-point basis and 3,042 per 1,013-point basis over selected full rows, including six equal-x fallbacks in each case. For each basis/size, complete sorted `(point key, first payload)` maps from control, table-only, and combined binaries were byte-identical:

| Basis | Size | Complete map SHA-256 |
|---|---:|---|
| Auxiliary | 500 | `ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879` |
| Auxiliary | 1013 | `68bc887fbae1a96d049106330e624d75c3a6a148cd95857294a9c0c5024f301b` |
| Plain | 500 | `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa` |
| Plain | 1013 | `6c8e0dfebc34d97ee542d341423f9fd1ebaf8c6b16ea54324da22a15654533c4` |

The audit binary compared native and Rust *first exact hits on every walk state* through a full solve for seeds 0–2 at each basis/size. Every timed arm's input digest was identical within its basis/size and every three-arm block matched scalar, trials, relations, entries and input digest. The map was dumped once per unique input/configuration before timing, rather than serialized in every timed arm; the deterministic builders and identical input digests connect that audit to the timed blocks. This is the precise scope of the map evidence.

| Basis | Size | Arm | Charged wall median ms | Charged CPU median ms | Table median ms | Elimination median ms |
|---|---:|---|---:|---:|---:|---:|
| Auxiliary | 500 | Rust control | 64.639 | 64.275 | 8.203 | 2.926 |
| Auxiliary | 500 | Native table | 62.324 | 61.301 | 6.720 | 2.742 |
| Auxiliary | 500 | Native table + scan | 54.785 | 54.092 | 6.963 | 2.748 |
| Auxiliary | 1013 | Rust control | 129.970 | 128.613 | 39.536 | 14.602 |
| Auxiliary | 1013 | Native table | 124.401 | 123.355 | 35.622 | 13.759 |
| Auxiliary | 1013 | Native table + scan | 115.420 | 114.555 | 35.343 | 13.798 |
| Plain | 500 | Rust control | 51.524 | 50.727 | 8.040 | 2.540 |
| Plain | 500 | Native table | 49.697 | 49.124 | 6.375 | 2.405 |
| Plain | 500 | Native table + scan | 43.178 | 42.503 | 6.601 | 2.417 |
| Plain | 1013 | Rust control | 112.950 | 111.913 | 39.031 | 14.443 |
| Plain | 1013 | Native table | 109.097 | 107.782 | 34.543 | 13.800 |
| Plain | 1013 | Native table + scan | 100.631 | 99.535 | 35.563 | 13.895 |

Each row has 12 arms. Median paired native-table/control wall ratios are 0.9653/0.9629 for auxiliary 500/1013 and 0.9645/0.9695 for plain 500/1013; the table-only change won 8/12, 11/12, 10/12 and 10/12 wall pairs respectively. The combined native-table-plus-scan/control ratios are 0.8302/0.8886 auxiliary and 0.8310/0.8904 plain, winning 12/12, 11/12, 12/12 and 11/12 wall pairs. CPU ratios and wins are in the raw records and agree in direction. The combined 1,013/500 *paired charged wall* median ratios are **2.103 auxiliary** and **2.371 plain**; the larger basis won only 1/12 auxiliary and 0/12 plain comparisons. Different sizes use different table and relation workloads, so those cross-size comparisons are complete costs, not exact-workload parity.

This screen rejects the larger s=11 basis with this native table and collector implementation as a cold single-target improvement. The table FFI saves about 1.5–4.5 ms per arm, far short of offsetting the larger table and elimination. The 500-point combined path is a local candidate gain over its Rust control, but its roughly 3–4% incremental gain over the previously measured scan-only path needs a separate fresh-seed confirmation before adoption. Neither path establishes a matched-rho crossover or a new asymptotic result. No Lean proof refines the C++ ABI to the group-law scan; the existing field and bitmap proofs do not establish this implementation or measured runtime.

`RAW.csv` SHA-256: `f65c5a97aed9ddc0e58c02480627ca119e12725c35f93dcd600690d8cfe56278`. Timed source SHA-256: `main.rs` `d5bb9057ad674e3f6370c409b75096ee1d4933d1c6b2f7d1c4f4a7bacaccea8d`, `scan.cpp` `4fb1e95a75bce9c875081f0295f3d8604987cd88313e73ce50424c424c6d74e7`. Reproduce with `M31_REPLAY_TMPDIR=/Volumes/SSD990 python3 experiments/prime-field-auxiliary-ic/m31-native-table-s11/replay.py > RAW.csv` from this checkout, with compilation and preflight outside the timed arm intervals. OS caches were not flushed.
