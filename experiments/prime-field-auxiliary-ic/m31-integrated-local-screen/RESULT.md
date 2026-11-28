# Integrated M31 command: same-public-target diagnostic

This exploratory screen used the current integrated `m31-fast` Rust command
on the frozen p=2^31-1 public target Q=(988441464,1643383878), supplied only
by coordinates. The generator is (1,814455902), the order is 2147505293,
and the checked answer is 123456789. The command's saved certificate replay
and this runner's separate Python group multiplication checked each solved
answer. All 21 fresh processes completed and solved; no failures or censored
cells were excluded. Compilation occurred before timing. [pcc:unverified]

## Fixed B256/m2 diagnostic

The first three seeds used B256 interval base, signed m2 pair index, 64 walk
lanes and four million queries/five-second online caps. Full process wall and
parent-plus-child CPU begin before launch and end after exit; the program's
internal `cold_ns` starts at main entry and ends before final stdout emission.

| Seed | Queries | Relations | Process wall ms | Process CPU ms | Internal cold ms | Pair-index setup ms | Online ms |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 2,185,536 | 134 | 143.901 | 40.599 | 36.503 | 1.667 | 34.130 |
| 1 | 2,043,977 | 129 | 39.453 | 37.529 | 33.859 | 1.618 | 31.556 |
| 2 | 1,614,642 | 103 | 32.227 | 31.699 | 27.784 | 1.642 | 25.501 |

The first wall observation contains substantial host scheduling time and is
not evidence of a different algorithmic workload. Each setup constructed
65,536 signed pair witnesses. The `online_pair_counts.lookups` field reports
zero because the direct m2 `PairIndex::decompose` path does not increment that
particular counter; query counts in `work.queries` are the relevant work
measure. Index setup is a small part of this integrated configuration's cold
cost. Its remaining time tracks millions of target queries. [pcc:unverified]

## Batch-lane screen

`LANE_PROTOCOL.md` fixed six lane counts and three seeds before running the
18-cell shuffled panel. Changing lanes changes the walks, so the table is a
descriptive tuning screen, not paired identical-work timing. All cells
solved and verified the same public target.

| Lanes | Median process wall ms | Median CPU ms | Median online ms | Median online ns/query |
| ---: | ---: | ---: | ---: | ---: |
| 32 | 45.241 | 44.731 | 38.368 | 17.063 |
| 64 | 41.125 | 40.098 | 32.600 | 15.896 |
| 128 | 40.917 | 40.263 | 34.386 | 15.231 |
| 256 | 38.436 | 37.751 | 31.536 | 14.776 |
| 512 | 42.258 | 41.828 | 35.789 | 14.257 |
| 1024 | 42.695 | 42.409 | 35.543 | 15.639 |

The best observed median throughput, at 512 lanes, is about 10% faster per
query than 64 lanes, while total cost also depends on the changed stopping
trajectory. This screen does not select a new default or establish a cold
speedup. The next algorithmic lead must materially reduce the number of
queries or the amount of work per query; another table-only improvement
cannot close the measured same-target rho gap. This is an inference from
these cost and query counts, not a lower bound for all index-calculus variants.

## Base size and inline witness interaction

`BASE_PROTOCOL.md` screened B128,256,384,512,768,1024 on three seeds of the
same public target. Seventeen of 18 cells solved; B128 seed0 hit the four
million query cap and remains incomplete. The larger base reduces online
queries but raises setup sharply. Median internal cold times were 33.895ms
at B256, 25.645ms at B384, 29.161ms at B512, 33.861ms at B768 and 50.210ms
at B1024. B384 was the best observed original representation on this target.
The one incomplete cell is retained in `base-raw.csv` and its full report.

The original `PairIndex::Entry` allocated a separate one-element `Vec` for
each distinct pair sum. The candidate keeps that first witness inline and
allocates an overflow vector only for collisions, while retaining every
witness and its order. Six release `pair_index` tests passed, including the
complete signed finite-domain/decomposition checks and all nonzero control
targets. In the `INLINE_PROTOCOL.md` three-seed paired screen, all 24 arms
solved and all 12 matched blocks agreed on exact certificate, work counts,
pair counts and independently checked answer. [pcc:unverified]

| B | Control process wall median ms | Inline wall median ms | Median paired inline/control wall ratio | Median paired CPU ratio | Median paired index-build ratio |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 256 | 37.817 | 36.316 | 0.9603 | 0.9654 | 0.7779 |
| 384 | 28.870 | 27.924 | 0.9867 | 0.9809 | 0.8229 |
| 512 | 32.851 | 30.049 | 0.9147 | 0.9129 | 0.8077 |
| 768 | 38.008 | 30.908 | 0.7881 | 0.7842 | 0.7839 |

Each row has three paired seeds, so these are development measurements,
not an independent performance finding. One B384 seed0 control wall was
heavily delayed; CPU and internal cold ratios are near 0.98 there. The
representation gain is largest where setup dominates, but the fastest
observed total remains near B384. `FRESH_PROTOCOL.md` fixes a six-arm
fresh-target comparison before those target coordinates are generated.

## Reproduction and provenance

Source Git head `ed350380e`; release `m31-fast` binary SHA-256
`66eeee2c8fcc961e41eeb4f8162739888c13d6473c3d872fa7de61ca3f54c692`.
Host: Apple M4 Pro, Darwin 27.2.0, Rust 1.93.1. Run `python3 run.py > raw.csv`
and `python3 lane_sweep.py > lane-raw.csv` from this directory's repository
checkout with the binary at the path pinned in the scripts. The scripts
create one full JSON and stderr file per cell and refuse to overwrite them.
`raw.csv` SHA-256 is
`1bd73cad91c13eee55c3704dbc2ca6c678f90b3fb77d50f64d6b55f8fed06723`;
`lane-raw.csv` SHA-256 is
`e668b4dcc6ff6cedf783e36062f1f2dcf399b586906b24f26f1a7cff0d99f940`.
`inline-raw.csv` SHA-256 is
`b2fb9d3c7cbdcaec753af8cdd512a88d2745ce5c4812dbe304cc1a302ef634d5`.
The inline candidate binary SHA-256 is
`941286d29f97320b8dbdf50294a4d242badfeca00bcfc5fc3c855cde1e63880e`.
Full JSON reports, stderr and their per-cell SHA-256 values remain in this
local directory; the compact CSVs preserve every cell, including the B128
incomplete result. The larger JSON reports are not represented as uploaded
or independently retained by this PR.
The panel used one public target and a shared local host. Its protocol and
result are published together, so it is exploratory producer evidence.
[pcc:unverified]
