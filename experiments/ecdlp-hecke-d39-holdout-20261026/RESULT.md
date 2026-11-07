# Exploratory low-conductor `D_K=-39` Hecke rank control

> **Exploratory, not an independently verifiable holdout.** `PROTOCOL.md` and the completed result are first published together in this PR. Although the protocol records that inputs and predictions were fixed before the producer ran, this repository does not establish an earlier public freeze; the agreement below is therefore a post-run exploratory comparison.

The prespecified `D_K=-39`, conductor-6 class walk on `X_0(11)/F_367` reached 64 rational points, and its 48 verified Hecke relations have rank 40. Both numbers match the frozen prediction from the earlier `D_K=-7` empirical rule. The 64 Atkin–Lehner rows raise rank to 52, also matching the frozen deficiency prediction of 11. A prior `D_K=-39`, conductor-30 run over `F_8779` had already established cross-discriminant behavior; this run adds a smaller, different-field check at conductor 6 and norm-2 class order 12, versus order 24 in that earlier conductor-30 case.

| Frozen or measured quantity | Prediction | Observation |
| --- | ---: | ---: |
| Class points | 64 | 64 distinct |
| Hecke relations from degrees 2, 3 | — | 32, 16; all 48 group-verified |
| Hecke rank | 40 | 40 |
| Projective deficiency `C-1-rank` | 23 | 23 |
| Atkin–Lehner rank | 52 | 52 |
| Atkin–Lehner deficiency | 11 | 11 |

The [protocol](PROTOCOL.md) fixed `D_K=-39`, `f=6`, degrees `[2,3]`, `p=367`, trace magnitude 8, the source hashes, prediction, and 180-second cap before the producer ran. The checked launcher reported Sage `10.10.rc0` and a verified runtime manifest in [runtime-info.json](runtime-info.json). The [launch receipt](launch.json) records exit 0 in 32.04 seconds, including launcher startup; the producer's internal work took 2.31 seconds and is only diagnostic. Its stderr records four CM `j` roots and eight rational starting points above them. The complete [raw output](data/exp11_class_walk_D39_f6.json), [stdout](producer.stdout), and [stderr](producer.stderr) are retained.

The independent [matrix audit](matrix_audit.json) enumerates primitive reduced forms directly and obtains class numbers `4,4,12,12` at conductors `1,2,3,6`. Its separate sparse elimination obtains ranks `40` and `52` over `F_11`, `F_1009`, and `F_1000000007`. The [conductor audit](conductor_audit.json), run through the checked Sage launcher, computes the actual endomorphism order of every distinct saved `j`: exactly `8,8,24,24` points at conductors `1,2,3,6`, with two points over each of 32 `j` values.

The degree-2 [integer graph audit](graph_audit.json) finds two signed incidence components of 12 rows each. Their integer row sums cancel every lower-conductor column and cover all 24 floor columns with coefficients `+1` or `-1`. This is a post-run structural diagnostic. The norm-2 form `(2,1,44)` in `Cl(-351)` has order 12 under the checked Sage [class-group computation](class_order_audit.json), agreeing with each detected block size; this class-action explanation remains a conjectural bridge to the rational `X_0(11)` lift.

The accompanying [evidence-map diagram](visual-report/d39-evidence-map.svg) and [visual research report PDF](visual-report/report.pdf) summarize the frozen artifacts; the [editable Typst source](visual-report/report.typ) and [rendering notes](visual-report/README.md) are included. The visual is a schematic summary, not a point-level graph. We checked the experiment directory and the existing [elliptic-surface report](../../docs/ecdlp-surfaces/REPORT.md), [transfer diagram source](../../docs/ecdlp-surfaces/transfer.dot), and rendered transfer/count figures. Those canonical transfer figures remain unchanged: this finite signed-incidence audit does not certify new point-level graph edges or alter the established surface-transfer evidence.

The next discriminator is a prespecified class whose signed blocks and nonfloor pivots have competing predictions under the existing graph models, followed by the same full relation and conductor audit. A proof needs to identify the degree-2 signed components with ideal-class orbits and account for the remaining nonfloor pivots. The exact integer certificates here provide another concrete finite instance for that proof construction.
