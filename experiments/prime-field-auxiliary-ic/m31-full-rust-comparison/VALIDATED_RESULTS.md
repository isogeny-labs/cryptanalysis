# Repeated validation cost in the M31 collector

The frozen protocol is in `VALIDATED_PROTOCOL.md`. The fixed signed factor base
is built with checked curve constructors. Every walker point is initialized
and advanced by checked group operations. The candidate omits repeated
curve-membership tests for these already validated inputs; both arms call the
same batched arithmetic after the guard. Both use the one-multiply flat hash.

Two local 24-block panels per fixture completed on an Apple M4 Pro with
Rust 1.93.1. Each of the 192 arms regenerated the 500-point basis, collected
checked three-point relations, eliminated them, and checked scalar 123456789
by generator multiplication. Within every matched pair, basis digest, table
entry count, trial count, relation count, and answer were identical. The
second panel used a different block shuffle. [pcc:unverified]

| Panel | Fixture | Checked wall median ms | Prevalidated wall median ms | Median paired checked/prevalidated wall ratio | Prevalidated wins |
| --- | --- | ---: | ---: | ---: | ---: |
| Initial | Auxiliary | 205.588 | 172.811 | 1.1640 | 23/24 |
| Initial | Plain | 178.888 | 156.065 | 1.1597 | 24/24 |
| Repeat | Auxiliary | 205.284 | 183.323 | 1.1666 | 21/24 |
| Repeat | Plain | 181.622 | 160.703 | 1.1438 | 23/24 |

| Panel | Fixture | Checked CPU median ms | Prevalidated CPU median ms | Median paired checked/prevalidated CPU ratio | Prevalidated wins |
| --- | --- | ---: | ---: | ---: | ---: |
| Initial | Auxiliary | 204.249 | 171.717 | 1.1631 | 24/24 |
| Initial | Plain | 177.238 | 154.020 | 1.1701 | 24/24 |
| Repeat | Auxiliary | 203.673 | 182.014 | 1.1475 | 24/24 |
| Repeat | Plain | 180.625 | 155.545 | 1.1605 | 24/24 |

The charged window covers basis regeneration and comparison, fixture file
writing, collection, elimination, answer verification, and Rust process exit.
Compilation and frozen JSON loading are outside it; OS caches were not
flushed. The ratios use matched pairs, so they differ from ratios of displayed
arm medians. `validated-raw.csv` and `validated-confirm.csv` retain all arms.
The producer script `validated_analyze.py` enforces the pair invariants.

This is a measured local same-target collector gain, not a mathematical
complexity improvement. The prevalidated API relies on its documented input
precondition. It was compared against checked `batch_add` in the crate unit
test, and the complete library suite passed locally. Independent PCC replay
and a proof linking the Rust API contract to a Lean model remain pending.

Source and evidence SHA-256 at measurement:

```
field.rs               3c7f04e599a66bb115d2789bb99383af1a1e5ad3bf29d40628b7fdc260b6a73b
main.rs                95868025f4c518c7d6f22c485ea498fc927e6dc0c5ff2529eb93f2fe2869f31b
validated_replay.py    48d9ef0d27416c2d21e5d6165a9ec44c8d6a2067bc92052f80016a02d5fc53e4
validated-raw.csv      a76e1f91be43a415d7bd5786f9149ca07b4faaaf97da39a0047843ef36dc2f62
validated-confirm.csv  c6e864107f5289a82f9cc4bd424ae813337ee28e5bf88c5c9ed1bdab8d054ed1
```
