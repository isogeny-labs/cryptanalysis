# Frozen public M31 full Rust comparison

Run `python3 replay.py > raw.csv` from this directory or its repository root.
The runner compiles the existing `prime-field-auxiliary-ic` arithmetic crate
and this standalone Rust collector once, then measures 24 matched blocks for
each of the frozen auxiliary and plain M31 public fixtures. Eight blocks use
each seed 0, 1, and 2. The flat and reflected arms alternate execution order.
Each arm regenerates its factor base from the frozen `snapshot/prepare.py`
construction, checks it against the published 500-point fixture, launches a
fresh Rust process, and checks the returned scalar against the fixture.

The Rust collector uses the same target, signed factor base, pair-key format,
first-payload rule, walk and elimination in both arms. Only pair-row
construction differs. Every accepted relation is checked by point addition.
The final scalar is verified by multiplying the target generator, and the
runner checks the expected public answer. All 48 matched pairs had identical
basis digests, table sizes, trial counts, relation counts and answers.

The charged wall clock starts before basis generation and ends after Rust
process exit and answer parsing. CPU time includes parent user/system and
child user/system time in that window. The Rust internal clock starts after
reading the public fixture. Compilation, extraction of frozen source and
fixture JSON, and reference data preparation occur before each timed arm.
OS file caches remain under host control. This is a local Apple M4 Pro run
with background activity, so the observations are exploratory. The run does
not use a signed independent verifier. [pcc:unverified]

| Fixture | Flat wall median ms | Reflected wall median ms | Median paired flat/reflected wall ratio | Reflected wins |
| --- | ---: | ---: | ---: | ---: |
| Auxiliary | 131.719 | 130.069 | 0.9998 | 12/24 |
| Plain | 113.409 | 112.383 | 1.0165 | 15/24 |

| Fixture | Flat CPU median ms | Reflected CPU median ms | Median paired flat/reflected CPU ratio | Reflected wins |
| --- | ---: | ---: | ---: | ---: |
| Auxiliary | 128.656 | 127.573 | 0.9993 | 12/24 |
| Plain | 111.071 | 110.487 | 1.0143 | 16/24 |

The median paired table-construction ratios were 1.172 and 1.173 for auxiliary
and plain. Pair ratios and ratios of arm medians differ because they summarize
different quantities. The charged auxiliary panel is effectively tied. The
plain difference is small relative to the unisolated host conditions. No
end-to-end performance breakthrough is claimed. [pcc:unverified]

This is a new standalone Rust collector reproducing the archived explicit
three-point relation method. It is separate from `PreparedSolver`, whose
circuit decomposition does not use a pair table. The `FlatIndex` from the
public-table microbenchmark is also separate: the full collector uses Rust's
`HashMap` in both arms to keep lookup semantics constant. Here `flat` means
directly computed pair rows, and `reflected` means reconstructing odd rows by
negating even-row sums. The source, raw 96-arm CSV, and environment receipt
are stored together for replay.
