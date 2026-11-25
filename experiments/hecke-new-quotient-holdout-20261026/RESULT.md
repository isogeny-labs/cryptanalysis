# Six mixed incidence components span a 54-dimensional Hecke floor kernel

The prospectively selected `D_K=-2631`, conductor-6 class on `X_0(11)/F_23743` has **768 rational points, 576 verified Hecke rows, exact rational rank 480, and nonfloor projected rank 426**. Its 54-dimensional floor-only row space has an explicit integer basis: six disjoint alternating degree-2 cycles of 48 rows and 48 degree-3 row-pair differences. Each cycle meets eight pairs, and all 48 overlaps contain both sign ratios. These quantities match the [frozen forecast](PRODUCER_PROTOCOL.md) for a mixed incidence configuration with six components.

| Quantity | Frozen prediction | Checked result |
| --- | ---: | ---: |
| Points at conductors `1,2,3,6` | `96,96,288,288` | `96,96,288,288` |
| Degree-2 / degree-3 complete rows | `384 / 192` | `384 / 192`, all group-verified |
| Full rational relation rank | `480` | `480` |
| Nonfloor projected rank | `426` | `426` |
| Signed degree-2 cycles | `6` | `6` of length `48` |
| Degree-3 floor pair differences | `48` | `48` of support size `6` |
| Mixed incidence components / balanced components | `6 / 0` | `6 / 0` |
| Floor-only row-space dimension | `54` | `54` |

The [selection rule](SELECTION_PROTOCOL.md) was saved before candidate screening. Among 30 screened discriminants satisfying its inexpensive arithmetic conditions, the first eligible value was `D_K=-2631`; the [selection receipt](selection.json) retains all rejections and its class-action data. The norm-2 class orders are 16 at conductor 1 and 48 at conductor 3; the ramified norm-3 class is the eighth norm-2 step at conductor 1. The resulting six predicted components exceed the earlier mixed cases in the frozen predictor panel. The first permitted field prime is `p=23743`, with `u=16` and `u²-4p=-2631·6²`.

The independent [two-sheet gate](fiber_gate.json) found 48, 48, 144, and 144 rational CM `j` values at the four conductors, each with exactly two rational `X_0(11)` lifts and the expected trace. Under the checked-Sage launcher, the copied regularized producer completed under its 600-second cap and saved the full [point and relation matrix](data/exp11_class_walk_D2631_f6.json), [launch receipt](producer_launch.json), stdout and stderr. The checked runtime, exact source hashes, and gate status are retained alongside the protocol.

The [independent Sage audit](audit.json) reconstructs all 768 points, checks each distinct `j` value's endomorphism-order conductor, compares all 1,536 point-degree rational-root counts with the classical modular polynomials including multiplicities, and replays all 576 saved relation rows and group sums. It obtains the full and nonfloor ranks over `QQ`, 23, and 1000000007. Its degree-subset ranks are `384/378` for degree 2 and `192/144` for degree 3, where each pair is full/nonfloor rank.

The [floor audit](floor_audit.json) stores every signed source-row coefficient and floor vector. The [independent integer validator](validation.json) reconstructs all 54 vectors from the raw matrix, checks both disjoint floor coverings, finds eight mixed pair overlaps per cycle, and obtains witness/full/nonfloor ranks `54/480/426` over `QQ`, 23, and 1000000007. Since the 54 integer vectors lie in the floor kernel, are independent, and the exact rank difference is 54, they form a basis of this saved floor-supported row space.

**Proof map.** The pinned [Lean module](formal/MixedSix.lean) proves `MixedSix.local_mixed_zero` and `MixedSix.six_by_eight_mixed_zero`: given both opposite-sign coordinate equations on each cycle–pair overlap, all six cycle and 48 pair coefficients in a vanishing combination are zero. `lake env lean MixedSix.lean` built with Lean `v4.35.0-rc4` and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9`; its [`#print axioms` record](formal/build-output.txt) lists only `propext`, `Classical.choice`, and `Quot.sound`. The integer validator supplies the concrete equations and the exact matrix ranks externally. Formalizing the full 768-column row identities and class-action-to-rational-`X_0(11)` correspondence in Lean remains open; the theorem is the conditional structural step, not a replacement for those bridges. `lean4checker --fresh` was unavailable on this host.

The first gate-wrapper invocation stopped before launching Sage because a selector file named `select.py` shadowed Python's standard `select` module. Renaming it to `select_candidate.py` resolved that launcher error; the saved gate and producer receipts are from the completed runs. This experiment is a relation-stage diagnostic with `candidate_id: null` and `timing_claim: null`. The next proof step is to derive the six mixed incidence components uniformly from the two rational level-11 eigenline labels and the conductor-1 norm-3 class action.
