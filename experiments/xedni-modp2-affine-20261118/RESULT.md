# Direct modular probes preserve affine lift selection

Computing `[q]P_i` with Jacobian arithmetic modulo `p²` produced the same leading formal-parameter residues as Sage `Qp` on every measured probe in a fresh 32-target panel. The two-plus-two affine lookup then selected exact rational residual depth two on **16 of 19** public relation hits. A full-grid independent replay checked **45,619** rational models and found zero affine-residue or lookup mismatches; the producer constructed **7,361** models, including three required full-grid fallbacks. The [frozen audit](audit.py) checks the complete match set and all exact rational residuals.

## Construction and measured result

The [protocol](protocol.json) fixes eight field/subgroup records, four new targets per field under `xedni-modp2-affine-v1|p|j`, 16 public queries per target, 13 predeclared short vectors, and the seven-value shift grid. Its 512 queries and 6,656 vector tests yielded 19 public hits. Every hit had distinct image x-coordinates, so its full grid contains 2,401 models.

For each of five probe shifts `0,e1,e2,e3,e4`, the producer reduces the interpolated curve coefficient `A` and both lift points modulo `p²`, computes their `[q]` multiples in Jacobian coordinates, and takes `t = -XZ/Y mod p²` when the multiple reduces to identity and `Y` is a unit. The leading residue is `(t/p) mod p`. These ten residues determine the affine cancellation equation. The two-plus-two lookup processes 49 left pairs and 49 right pairs per hit, then constructs and scores only matching models. If no valid match exists, it enumerates the full grid and selects the minimum-model baseline. Sage `Qp` evaluates all probe models **after** selection as a separate control; it also confirms the selected model. The selected exact rational residual is checked after the lookup.

| Recorded item | Result |
| --- | ---: |
| Fresh targets / public queries / vector tests | 32 / 512 / 6,656 |
| Public hits / independently checked full-grid models | 19 / 45,619 |
| Modular probe models / `Qp` validation models | 95 / 95 |
| `Qp` selected-model confirmations | 19 |
| Left / right lookup pairs | 931 / 931 |
| Cancellation matches / exact depth-two candidates | 78 / 78 |
| Producer rational models constructed | 7,361 |
| Models on 16 hits with a match | 158 |
| Full-grid fallbacks | 3 hits, 7,203 models |
| Selected residuals at depth two | 16 / 19 hits |
| Affine or lookup mismatches | 0 / 0 |
| Exact rational relations in full-grid audit | 0 |

The fallback hits were events 243, 454, and 502. The independent audit reconstructed every public query and finite relation, every full-grid rational model, both `[q]P_i` leading residues via modular projective arithmetic, and exact rational residual depth via Python `Fraction` group operations. It verified the producer's probe records, `Qp` controls, match set, attempt sequence, selected model, and selected rational outcome. Across the full grid, 45,541 candidate residuals had depth one and 78 had depth two. The [audit receipt](audit.json) is `PASS`; the [result manifest](run-result.json) indexes all compressed producer rows.

The checked-Sage script interval was **1.526 seconds** on an ordinary host. Exclusive stage timers were 0.0015 seconds probe-model construction, 0.0020 seconds for direct modular probes, 0.0087 seconds lookup, 0.0008 seconds matching-model construction, 0.1488 seconds fallback-model construction, 0.1405 seconds for `Qp` probe validation, 0.0227 seconds selected `Qp` confirmation, and 0.0340 seconds selected exact rational checks. The remaining interval includes finite-field setup and public queries, serialization, and control flow. The [runtime receipt](sage-runtime.json) was saved before the run. The modular and `Qp` probe timers use the same probe models, but this ordinary-host timing is a component diagnostic rather than a gated CPU speedup or same-target IC/rho comparison.

## Proof map and next step

The [Lean module](formal/JacobianFormalParameter.lean) proves `jacobian_formal_parameter`: for nonzero `Y` and `Z` in a field, the rational parameter `-(X/Z²)/(Y/Z³)` equals `-XZ/Y`. The pinned build succeeds and `#print axioms` reports only Lean's standard `propext`, `Classical.choice`, and `Quot.sound`. This is the coordinate identity used to extract the modular parameter. The full elliptic theorem remains **partial**: a Lean proof must establish the Jacobian addition and doubling formulas over the relevant integral model, the reduction-kernel and unit conditions for `[q]P_i`, the mod-`p²` residue bridge, and the first-order affine behavior of the interpolated lift family. The earlier [Lean leading-map module](../xedni-leading-defect-selector-20261116/formal/LeadingDefect.lean) proves the downstream additive cancellation implication under its explicit homomorphism hypothesis. Neither module substitutes an assumed conclusion for that missing bridge.

The next discriminating experiment is to remove even the five modular q-multiplications by deriving the first-order slopes directly from finite-field tangent and curve-deformation data. It should use a new target law, retain fallback costs, and independently replay the exact rational residuals. Reproduce this panel with `python3 verify.py`; new local Sage runs use `/Volumes/SSD990/cryptanalysis/sage --runtime-info` before `/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/run.py`.
