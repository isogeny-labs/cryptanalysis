# Public generator anchor in the M31 signed relation graph

This is a retrospective exact-rank screen over the 15 previously published
IC384 certificates in `m31-known-log-native` (validation CSV SHA256
`5c7028c05f308c0396c4edc93491040926011ff9c0bb0a1a41e60859baa94585`).
The interval base has representative 0 exactly equal to the public generator
G. `replay.py` verifies every saved row as a group equation, then runs
incremental modular elimination twice on the same ordered row prefix: with
all 384 factor-base logs unknown, and with the exact identity F₀=G imposed.
The unanchored replay first recovers at the same final row as the saved native
certificate in all 15 cases, and both replays return the independently
verified scalar on every target.

| Measure | Result |
|---|---:|
| Same-target/seed streams | 15 |
| Anchor saves at least one accepted row | 3/15 |
| Rows saved on those streams | 3, 12, 3 |
| Median rows saved | 0 |
| Total accepted rows saved | 18 of 3,132 |

The exact per-stream table is `raw.csv` (SHA256
`8dc154dbe1d721698c7f08fe73220da83497fc4962668d3bd11f87b4e188ab9c`).
This does not measure a new cold runtime: the archived collector stopped when
the unanchored graph solved, and the stored certificate lacks the query index
at each accepted row. It establishes that adding the one already-known
generator column cannot remove more than the listed row suffix on these
streams. Most runs gain no earlier algebraic recovery. A generator-only anchor
therefore does not justify changing certificate semantics and the native
collector as the next large performance lead. A hybrid with many charged
known-log columns is a different experiment and must be compared to a fully
known-log table as a generic-method control.
