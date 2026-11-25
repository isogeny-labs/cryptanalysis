# Same-target cold distance to archived M31 rho

The protocol in `RHO_PROTOCOL.md` was frozen before measurement. The bitmap-combined Rust IC collector and archived C++ `compare_rho.cpp` used the same public curve, generator and target in both frozen M31 bases. The auxiliary and plain fixtures share P and Q; rho cells were repeated per basis to retain balanced pairing. Both programs reported and independently checked scalar `123456789`. The C++ rho source asserts `[k]P=Q`, compiled with assertions enabled; the wrapper checked its metrics and scalar. All 96 fresh-process arms completed without replacement.

| Basis | Bitmap IC wall median ms | Rho wall median ms | Median paired IC/rho wall ratio | Bitmap IC CPU median ms | Rho CPU median ms | Median paired IC/rho CPU ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 122.981 | 14.584 | 10.402 | 116.838 | 10.798 | 11.958 |
| Plain | 115.744 | 12.525 | 10.674 | 105.318 | 9.996 | 11.199 |

Rho walk steps for seeds 0, 1 and 2 were 26,296, 26,343 and 119,375. The paired ratios are medians of pairwise ratios and need not equal ratios of the displayed arm medians. Each IC arm charged basis regeneration, input writing, table construction, relation collection, elimination, answer verification and process exit. Each rho arm charged writing the frozen input, the complete fresh rho process, metrics parsing and exit. Compilation and frozen JSON loading preceded timing; OS caches were not flushed. Source language and arithmetic implementation differ, so this is a same-target wall/CPU distance indicator rather than an operation-normalized comparison or the strongest precomputed-rho control.

The bitmap collector remains well behind this rho reference at M31. This does not erase its directly measured improvement over the original IC collector; the two comparisons have different controls and are not pooled. One host and one public target limit the scope. Raw `rho-raw.csv` SHA-256 is `f79cc2190266c4afa8b84b6b9d266e9112be0adab49a59392e0afa7164a82ddf`. [pcc:unverified]
