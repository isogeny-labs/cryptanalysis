# Native M31 flat pair lookup: frozen negative result

The five-target x three-seed panel followed `PROTOCOL.md`. It compared the native `PairIndex` HashMap and a bounded open-addressed x-to-entry table at B384 and B512, plus matched archived rho. All 75 fresh-process arms solved. Within every same-size HashMap/flat block, the answer, basis, exact certificate digest, pair/work counters and relation counts agreed. `audit.py` independently reopened every saved stdout by its CSV digest, checked every public answer, and replayed all 14,218 IC certificate equations and weighted factor-base cancellations. No arm failed or was censored. Raw CSV SHA-256: `b70952d3571ade7d5cdb01892bba00c4b782ae85c6ff05429527ee433e7a93e3`.

| Arm, 15 blocks | Charged wall median ms | Charged CPU median ms | Pair-index median ms | Online median ms |
| --- | ---: | ---: | ---: | ---: |
| HashMap B384 | 29.040 | 28.628 | 3.159 | 20.727 |
| Flat B384 | 32.490 | 31.618 | 3.246 | 23.566 |
| HashMap B512 | 31.546 | 30.844 | 5.680 | 19.823 |
| Flat B512 | 42.101 | 41.690 | 5.931 | 30.381 |
| Matched rho | 15.464 | 14.794 | — | — |

Median paired HashMap/flat wall and CPU ratios were `0.9114`/`0.9132` at B384 and `0.7301`/`0.7256` at B512. Flat won **0/15** wall and **0/15** CPU blocks at either size. Direct current HashMap B384/flat B512 ratios were `0.6708` wall and `0.6761` CPU; flat B512 won one wall block and zero CPU blocks. The prespecified selection gates failed. The production `PairIndex` keeps its HashMap. The conditional flat implementation is removed after preserving its source at commit `6f65acfc877e73d37d94285605b54f84029b8237` and all observations here.

Pair-index construction changed modestly, while the flat online phase became slower, especially at B512. The open-addressed table's 4 MiB random-access probes and serial collision chain are plausible contributors, but these phase timers do not isolate cache misses or instructions. The current HashMap uses a custom fast hasher; a generic claim that flat tables are faster is unsupported. HashMap B384/rho same-panel median paired ratios were `1.6756` wall and `1.9427` CPU; the source languages and arithmetic differ. This is a distance measure on these targets, not an operation-normalized comparison.

External wall and parent-plus-child CPU clocks charged the fresh process from launch through basis generation, pair-index construction, relation collection, elimination, certificate replay, output parse and independent public answer verification. Compilation and frozen public JSON loading preceded timing, and OS caches were not flushed. `HOST.json` records the exposed local Apple M4 Pro. This is exploratory producer evidence [pcc:unverified], without Tier 1 isolation or independently signed performance standing. The result is a data-structure falsification, not a new mathematical theorem; Lean timestamp arithmetic would not change it.

Measured `pair_index.rs` SHA-256: `bb25e994b6dc042a605ff4d0121db3bea755adfaf7670122d865bf7158ac308a`. The replay script SHA-256 is `3455c90427fde25b3444fb8665d96e08ff5d419c4258f3c754057007b88cbd9a`. The CSV records the hash of each binary and stdout. The seed manifest SHA-256 is `adc996d6924d44c53f9b8e58b871467e266ca4ecb99faaa7c64e9f5053f4572b` and the public target JSON SHA-256 is `dc724fc613d9c2b824b90d59c876f1f7f84b3273d8d607c648e1ba3fbc089252`.
