# Fresh public M31 inline-witness confirmation

`FRESH_PROTOCOL.md` was committed at `fde4323dd` before five new public
target coordinates were generated. `fresh-public.json` was committed at
`92c5421e3` before timing. The evaluator scalars were kept in a separate
local file until all 90 worker reports were saved, then checked against every
reported answer. Workers received only Q coordinates. Independently, each
reported scalar was multiplied by the public generator and compared with its
target. All 90 fresh processes solved, all answers matched, and there were no
failures, timeouts, censored arms or replacements. Within each target/seed,
the original and inline B384 certificates, work counts and pair counts were
identical; the same held for B768. [pcc:unverified]

The field is p=2147483647, curve y²=x³+2x+14, prime order N=2147505293,
generator G=(1,814455902). Five public targets × three seeds × six arms were
run. Each IC arm used a fresh B256/B384/B768 interval base, signed m2 pair
index, 64 walk lanes, 4M query cap and 5s soft online cap. Rho was the frozen
`comparison/compare_rho.cpp` on the same coordinates. Wall and
parent-plus-child CPU start before process launch and end after process exit,
JSON/metrics parsing and public group-equation verification. IC basis build,
index build, search, elimination, certificate replay and teardown are charged.
Compilation and frozen fixture loading are excluded. Arm order rotates by
target/seed and blocks are shuffled as specified. OS caches and other host
load were not controlled. [pcc:unverified]

| Configuration | Median charged wall ms | Median charged CPU ms | Median internal cold ms | Median index build ms | Median online ms | Median queries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original B256 | 42.471 | 42.144 | 38.192 | 1.674 | 35.659 | 1,870,684 |
| Original B384 | 38.760 | 37.254 | 33.769 | 3.847 | 28.417 | 1,483,386 |
| Inline B384 | 36.293 | 35.674 | 31.523 | 3.060 | 27.969 | 1,483,386 |
| Original B768 | 43.245 | 42.455 | 38.166 | 16.319 | 15.307 | 751,573 |
| Inline B768 | 36.245 | 35.770 | 31.132 | 14.158 | 15.427 | 751,573 |
| Archived rho | 17.059 | 14.348 | — | — | — | — |

| Paired comparison | Median wall ratio | Wall wins | Median CPU ratio | CPU wins |
| --- | ---: | ---: | ---: | ---: |
| Inline/original B384 | 0.9305 | 13/15 | 0.9278 | 13/15 |
| Inline/original B768 | 0.8574 | 14/15 | 0.8553 | 15/15 |
| Inline B384/original B256 | 0.9205 | 10/15 | 0.9306 | 10/15 |
| Inline B768/original B256 | 0.9810 | 8/15 | 0.9248 | 8/15 |
| Inline B384/rho | 2.2592 | 1/15 | 2.7407 | 0/15 |
| Inline B768/rho | 2.4566 | 1/15 | 2.9862 | 0/15 |

The ratios are medians of within-target/seed paired ratios, not quotients of
the displayed configuration medians. The target-level median wall ratios for
inline/original B384 were 0.849, 0.980, 0.927, 0.851, 0.981; for inline/rho
they were 2.305, 2.207, 3.035, 2.789, 1.861. The 15 cells reuse only five
independent public targets. Wall times include host scheduling variation; CPU
and the internal phases support the same direction for equal-size inline
comparison. The B384 versus B256 choice is less stable across targets and
was screened after seeing one development target, so no default is changed
by this panel. The candidate remains slower than rho at the median on both
wall and CPU. [pcc:unverified]

Source: original binary SHA-256
`66eeee2c8fcc961e41eeb4f8162739888c13d6473c3d872fa7de61ca3f54c692`,
inline binary `941286d29f97320b8dbdf50294a4d242badfeca00bcfc5fc3c855cde1e63880e`,
inline `pair_index.rs` `473e6b72341a798c5caba40bf4a20222498e60c172473d121954628b702c82cf`.
After the panel, the existing atomic ID increment was rewritten as a
`compare_exchange_weak` loop to satisfy newer Rust Clippy while retaining
Rust 1.78 compatibility. The measured binary and its hash above are unchanged;
this later compatibility edit is not presented as a measured speedup.
Public-target file SHA-256
`dc724fc613d9c2b824b90d59c876f1f7f84b3273d8d607c648e1ba3fbc089252`;
`fresh_replay.py` SHA-256
`cbb4a170a39b6b04d8936af4ba20d86c3c341469d570a4eddd8efcea87ff41fd`;
`fresh-raw.csv` SHA-256
`488efa5df8581ae2f210562d2be7a0f8a1f378fef1629ad437c0b5fdfc98c396`.
The full stdout, stderr and rho metrics for every cell remain in this local
directory with their hashes in the CSV. They are not asserted uploaded or
independently retained by this PR. Host: Apple M4 Pro, Darwin 27.2.0, Rust
1.93.1, Apple clang 21.0.0. No GPU was used. These are local producer
measurements, not a general or independently admitted performance result.
[pcc:unverified]
