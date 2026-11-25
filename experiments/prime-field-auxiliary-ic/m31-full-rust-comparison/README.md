# Frozen public M31 full Rust comparison

Run `python3 replay.py > raw.csv` from the repository root. The runner compiles
the existing Rust arithmetic crate and this standalone collector, then measures
24 matched blocks for each of the auxiliary and plain M31 public fixtures.
Eight blocks use each seed 0, 1 and 2. Arm order is balanced within each seed.
Each arm regenerates its 500-point basis from the frozen
`snapshot/prepare.py`, checks it against the published fixture, launches a
fresh Rust process, and checks the returned public answer.

Both arms use the same contiguous open-addressed flat index with 1,048,576
slots, the same signed point set, walk, relation checking and elimination.
The `flat` arm computes every pair row directly. The `reflected` arm computes
even rows and reconstructs odd rows by sign reflection. All 48 matched pairs
had identical basis digests, table sizes, trial counts, relation counts and
answers. Every accepted relation was checked by point addition; the final
answer was checked by generator multiplication. [pcc:unverified]

The charged wall clock starts before basis generation and ends after Rust
process exit and answer parsing. CPU time includes parent and child user and
system time in the same window. Compilation, frozen-source extraction and
fixture JSON loading occur before each timed arm. OS file caches remain under
host control. This is an exploratory local Apple M4 Pro panel with background
activity and no signed independent verifier. [pcc:unverified]

| Fixture | Flat wall median ms | Reflected wall median ms | Median paired flat/reflected wall ratio | Reflected wins |
| --- | ---: | ---: | ---: | ---: |
| Auxiliary | 256.309 | 254.561 | 0.9683 | 10/24 |
| Plain | 236.642 | 228.619 | 1.0055 | 13/24 |

| Fixture | Flat CPU median ms | Reflected CPU median ms | Median paired flat/reflected CPU ratio | Reflected wins |
| --- | ---: | ---: | ---: | ---: |
| Auxiliary | 236.100 | 239.541 | 0.9798 | 10/24 |
| Plain | 218.106 | 210.031 | 1.0122 | 15/24 |

The median paired table-construction ratios were 0.9976 and 1.0847 for
auxiliary and plain. The ratios use matched observations, so they can differ
from ratios of the displayed arm medians. The auxiliary whole-run result does
not favor reflection, and the plain difference is small. This panel does not
establish an end-to-end performance breakthrough. [pcc:unverified]

The original commit `93ae8852f` used `HashMap` in both arms while labelling
its direct-row arm `flat`. That changed the control relative to the prior flat
hash benchmark. Its 96 observations are preserved in `hashmap-raw.csv` for
provenance. The current `raw.csv` and source contain the corrected flat-index
comparison. Do not pool the two panels.

This standalone Rust collector reproduces the archived explicit three-point
relation method. The library `PreparedSolver` uses a different circuit path
without this pair table. The Rust walk is deterministic and shared by arms,
but uses a different random generator from the archived C++ program.

A separate flat-index hash comparison is documented in [HASH_RESULTS.md](HASH_RESULTS.md).
