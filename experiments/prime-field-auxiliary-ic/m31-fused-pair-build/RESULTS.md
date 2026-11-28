# Fused signed-pair build and wide bitmap on public M31 targets

The frozen six-arm panel ran five public Q across three new manifest-derived walk seeds, with 90 fresh processes and no failures or censored arms. All four B768 Rust variants returned identical answers, work and pair counters, and exact certificate digests within every block. The exhaustive source test compared every B768 canonical key, first witness and ordered alternate witness in the fused and current indexes, both with and without the wide bitmap. `audit.py` reopened each saved output by its CSV hash, checked every public answer by independent generator multiplication, and replayed 28,073 certificate relation equations and weighted factor-base cancellations. These are producer-side checks pending independent signed standing. [pcc:unverified]

| Arm, 15 blocks | Charged wall median ms | Charged CPU median ms | Pair-index median ms | Online median ms |
| --- | ---: | ---: | ---: | ---: |
| Current B384 | 30.832 | 30.070 | 3.228 | 21.994 |
| Current B768 | 37.671 | 36.542 | 14.310 | 16.239 |
| Fused build B768 | 36.719 | 36.088 | 13.280 | 16.105 |
| Wide bitmap B768 | 35.648 | 34.561 | 14.533 | 13.371 |
| Fused plus bitmap B768 | 34.781 | 33.589 | 13.485 | 13.905 |
| Matched rho | 11.247 | 10.944 | — | — |

Median paired current-B768/combined ratios were 1.0893 wall and 1.0890 CPU, with 14/15 and 15/15 combined wins. Against the current B384 path, median paired B384/combined ratios were **0.8898 wall and 0.8987 CPU**, with only 3/15 and 2/15 combined wins. The combined candidate failed both frozen selection gates. Its median paired cost relative to same-target rho was 2.8771 wall and 2.8565 CPU; the current B384 path's corresponding ratios were 2.5599 and 2.5790. The production pair builder and bitmap policy are restored after retaining the measured source commit `2b84615bd` and raw records. [pcc:unverified]

The separated arms attribute most of the B768 change to the bitmap: current/fused was 1.0248 wall and 1.0111 CPU with 10/15 wins each, while current/bitmap was 1.0683 wall and 1.0534 CPU with 14/15 and 13/15 wins. The two features are not additive in this run. Their internal build/online timers are diagnostic; they do not isolate field multiplication, cache misses or instruction count. The algebraic shared-denominator identity did not yield a selected end-to-end improvement, so no Lean timing or payload theorem is claimed for this rejected implementation. [pcc:unverified]

External wall and parent-plus-child CPU clocks charged process startup, basis generation, pair construction, relation collection, graph elimination, certificate replay, JSON parsing, independent answer verification and process exit. Compilation and fixture loading preceded timing; OS caches were not flushed. Host: shared local Apple M4 Pro, arm64, macOS 27.2. This was not Tier 1 isolated or independently signed. `raw.csv` SHA-256 `c58c995668b975e5a9761e9b75b2a29d6ddc7880313b184f965f2d86e5bbaf26`; `SEEDS.json` SHA-256 `6e197cea5ef10ad50372d438f9630a0ce6f88da23901dd41c091fd7cea094916`; measured `pair_index.rs` SHA-256 `fbdea5c8ac4e78d65a91af93793d92ca3edc1c6d97ecd541f145064f2ece7fac`. CSV rows pin every binary and stdout digest. [pcc:unverified]
