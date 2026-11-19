# First-order Jacobian jets recover affine coefficients, with a higher Python cost

Propagating four coordinate-shift derivatives through one Jacobian `[q]` computation per lift point recovered the same affine leading-defect coefficients as five ordinary modular probe models on every hit of a fresh panel. The vector-aware lookup selected exact rational residual depth two on **11 of 14** public relation hits. The independent full-grid audit checked **33,614** models and found zero affine-residue or lookup mismatches. The jet reduced the number of `[q]` propagations from 70 ordinary modular probes to 28 vector-valued propagations, but the Python jet stage took **0.0164 seconds** versus **0.0015 seconds** for ordinary modular probe validation on this panel. That is a negative component-cost result for this implementation.

## Frozen construction and measurements

The [protocol](protocol.json) fixes the eight field/subgroup records, four new targets per field under `xedni-jacobian-jet-v1|p|j`, 16 public queries per target, 13 predeclared short vectors, and the seven-value shift grid. The 512 public queries and 6,656 vector tests yielded 14 public relation hits, all with distinct image x-coordinates. Five rational probe models determine the central interpolated coefficient `A` modulo `p²` and its four first-order derivatives. The [jet implementation](jet.py) propagates values modulo `p²` and four derivatives modulo `p` through the polynomial Jacobian doubling and addition formulas. For a `[q]P_i` result with `Z` divisible by `p` and `X,Y` units, it extracts the intercept from `-X(Z/p)/Y` and each slope from `-X(dZ_j)/Y` modulo `p`.

The same two-plus-two lookup as the parent experiment searches the resulting affine cancellation equation. Only matching models are scored; if none is valid, the full 2,401-model grid is scored as a baseline fallback. Choices are fixed before ordinary modular and Sage `Qp` probe validation, selected-model `Qp` confirmation, and exact rational residual checking. A jet normal-form failure would have been recorded and would trigger the frozen ordinary-modular fallback; no such failure occurred.

| Recorded item | Result |
| --- | ---: |
| Fresh targets / queries / vector tests | 32 / 512 / 6,656 |
| Public hits / independently audited grid models | 14 / 33,614 |
| Jet attempts / failures | 14 / 0 |
| Jet `[q]` propagations | 28 |
| Ordinary modular / `Qp` probe validations | 70 / 70 models |
| Lookup matches / exact depth-two candidates | 45 / 45 |
| Producer models constructed | 7,303 |
| Models on 11 covered hits | 100 |
| Full-grid fallbacks | 3 hits, 7,203 models |
| Selected depth-two residuals | 11 / 14 hits |
| Affine or lookup mismatches in full-grid audit | 0 / 0 |
| Exact rational relations in full-grid audit | 0 |

The fallback hits were events 100, 300, and 438. The [independent audit](audit.py) reconstructed every public query, 33,614 rational models, modular Jacobian leading residues, and exact rational residuals with Python `Fraction` group operations. It checked all jet-derived intercepts and slopes against the separate full-grid modular calculation, the complete lookup match set, the producer attempt sequence, and the selected model. Every ordinary modular and Sage `Qp` probe value recorded after selection matched the jet prediction. The [audit receipt](audit.json) is `PASS`, and the [result manifest](run-result.json) indexes all compressed producer rows.

The checked-Sage producer's script interval was **0.405 seconds** on an ordinary host. Exclusive stage timers include 0.0164 seconds for jet propagation, 0.0015 seconds for ordinary modular probe validation, 0.0353 seconds for Sage `Qp` probe validation, 0.0446 seconds for fallback-model construction, 0.0177 seconds for selected `Qp` confirmation, and 0.0310 seconds for selected exact rational checks. These intervals use one frozen hit panel but a fixed order and an ordinary host; they are component diagnostics, not a Tier 0/1 CPU result or an end-to-end IC/rho comparison. The [runtime receipt](sage-runtime.json) was saved before the run.

## Proof map and next step

The pinned [Lean module](formal/FirstOrderJet.lean) proves `first_order_product`: in a commutative ring with a square-zero perturbation, multiplication propagates a first-order derivative by the product rule. Applied componentwise, this is the arithmetic law used by the four-direction jets. Its build succeeds, and `#print axioms` reports `propext` only. The earlier [Jacobian parameter lemma](../xedni-modp2-affine-20261118/formal/JacobianFormalParameter.lean) handles `t=-XZ/Y` under nonzero-denominator hypotheses. Formalization remains **partial**: the polynomial Jacobian group-law formulas, their branch and normal-form behavior over the square-zero extension, and the elliptic first-order affine bridge have not been proved in Lean. The finite-panel replay does not replace those obligations.

Because this Python jet implementation costs more than five ordinary modular probes at the measured component boundary, the current modular-probe policy remains the practical reference. A future jet implementation needs a sound lower-level cost case and matched fresh-panel timing before a performance claim. The more valuable proof step is to formalize the elliptic deformation bridge. Reproduce this panel with `python3 verify.py`; new local Sage runs use `/Volumes/SSD990/cryptanalysis/sage --runtime-info` before `/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/run.py`.
