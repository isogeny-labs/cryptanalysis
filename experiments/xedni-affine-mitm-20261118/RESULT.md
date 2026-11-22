# Two-plus-two lookup constructs only cancellation-matching lifts

The affine leading-defect equation can be searched with a two-plus-two lookup over the four coordinate shifts. On a frozen fresh-target panel, the lookup found **all 105 cancellation candidates** in the 2,401-model grid for each of 19 public hits. The producer constructed **2,596** rational models rather than all **45,619** grid models; 2,401 of its constructions came from one required fallback with no cancellation candidate. On the other 18 hits, it constructed only **195** models in total and selected a depth-two rational residual on every hit. The [independent audit](audit.py) enumerated the entire grid and replayed exact rational group arithmetic.

## Frozen algorithm and measurements

The [protocol](protocol.json) fixes the eight field/subgroup records, 32 fresh targets under `xedni-affine-mitm-v1|p|j`, 16 public queries per target, 13 short test vectors, and the seven-value coordinate-shift grid. The 512 queries and 6,656 vector tests yielded 19 public relation hits. All 19 hits had distinct image x-coordinates.

For a public-hit vector `(a,b)`, five `Qp` probe models give the affine residue equation `d0 + s1*d1 + s2*d2 + s3*d3 + s4*d4 = 0 mod p`. The implementation hashes all 49 values of `d0+s1*d1+s2*d2` and queries that table with the 49 required negatives of `s3*d3+s4*d4`. It constructs and scores only matching rational models. If no valid match exists, it enumerates the full grid and chooses the minimum-model baseline. The selected model gets an independent `Qp` confirmation and an exact rational residual check.

| Recorded item | Result |
| --- | ---: |
| Fresh targets / public queries / vector tests | 32 / 512 / 6,656 |
| Public hits / full-grid models checked independently | 19 / 45,619 |
| Left / right pair values processed | 931 / 931 |
| Lookup matches / exact depth-two candidates | 105 / 105 |
| Probe models / selected-model confirmations | 95 / 19 |
| Rational models constructed by producer | 2,596 |
| Models constructed on 18 covered hits | 195 |
| Full-grid fallback | 1 hit, 2,401 models |
| Selected depth-two residuals | 18 / 19 hits |
| Lookup or affine mismatches in full-grid audit | 0 / 0 |
| Exact rational relations in full-grid audit | 0 |

The one fallback was event 70, vector index 1. Across the full grid, 45,514 candidates had exact residual depth one and 105 had depth two. The independent audit reconstructed all public queries, finite group relations, 45,619 rational curves and points, `[q]P_i` residues via modular Jacobian arithmetic, and exact rational residuals via Python `Fraction` operations. It verified the complete lookup match set, unique producer attempt sequence, minimum-model selection, selected `Qp` confirmation, and all recorded statuses; its [receipt](audit.json) is `PASS`. The [result manifest](run-result.json) indexes all compressed producer rows.

The checked-Sage producer's script interval was **0.469 seconds** on an ordinary host. Exclusive stage timers were 0.0021 seconds probe-model construction, 0.0751 seconds for 95 `Qp` probe models, 0.00066 seconds pair lookup, 0.0013 seconds matching-model construction, 0.0177 seconds fallback-model construction, 0.0135 seconds selected `Qp` confirmations, and 0.0353 seconds selected exact rational checks. The remaining time covers finite-field setup and queries, result packing, and control flow. The [runtime receipt](sage-runtime.json) was saved before the run. The count comparison uses the same frozen hit panel; the independent audit and producer use different implementations and timing boundaries, so their wall times are not compared as a speedup. No same-target online IC/rho pair was run.

## Mathematical status and next step

The lookup is complete for the stated affine equation because every grid shift splits uniquely into one left pair and one right pair, and the table returns exactly those pairs whose two sums cancel modulo `p`. The full-grid audit checks both completeness and the affine first-order prediction on every measured model. A general elliptic theorem still needs the first-order deformation and formal-group bridge described in the parent [affine report](../xedni-affine-leading-defect-20261116/RESULT.md). The earlier [Lean module](../xedni-leading-defect-selector-20261116/formal/LeadingDefect.lean) proves the downstream additive cancellation implication under its explicit leading-map hypothesis. This experiment adds an algorithm and measurements; it does not promote the finite-panel affine observation to a general theorem.

The next work is to derive the coefficients `d_j` directly from mod-`p²` tangent and interpolation arithmetic, eliminating the five `Qp` probes, then test that formula on fresh targets. Reproduce the receipt with `python3 verify.py`; new local Sage runs use `/Volumes/SSD990/cryptanalysis/sage --runtime-info` before `/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/run.py`.
