# Wider lift search finds four additional leading cancellations

On a frozen fresh-target panel, enlarging each of four coordinate-shift axes from five values to seven found a cancellation candidate on **four additional public relation hits**. The nested 625-model rule selected a depth-two rational residual on 20 of 27 hits; the 2,401-model rule selected one on 24. The other three hits had no cancellation candidate even in the wider family. The full [independent replay](audit.py) reconstructed every public query, rational model, q-multiple leading residue, and exact rational residual for all 64,827 wide-grid candidates.

## Paired construction and outcomes

The [protocol](protocol.json) pins the source field/subgroup and query laws, a fresh 32-target seed label `xedni-width-v1|p|j`, and the two nested shift grids before measurement. Among 512 public queries and 6,656 predeclared vector tests, there were 27 public relation hits. Every hit had distinct image x-coordinates, so all 27 received 2,401 wide-grid candidates; the 625 narrow-grid candidates are a subset of those same rows.

For a known public-hit vector `(a,b)`, each policy chooses the minimum-model candidate satisfying `a*c1+b*c2=0 mod p`, where `ci` is the first formal-parameter residue of `[q]Pi`. If its grid has no such candidate, it chooses that grid's minimum-model baseline. Choices are fixed before any exact rational residual is evaluated. The wide and narrow policies therefore use the same target, hit vector, field, model law, residue rule, and tie rule; only the allowed coordinate shifts differ.

| Paired result | Five values per axis | Seven values per axis |
| --- | ---: | ---: |
| Candidates per ordinary hit | 625 | 2,401 |
| Candidate attempts across 27 hits | 16,875 | 64,827 |
| Hits with cancellation candidate | 20 | 24 |
| Selected residuals at depth two | 20 | 24 |
| Hits without cancellation candidate | 7 | 3 |
| Candidate-construction timer | 0.340 s | 1.033 s |
| q-multiple residue timer | 17.030 s | 65.779 s |

The wide policy changed 15 selected models, improved the exact residual depth on four hits, and worsened none. Those four are events 161, 383, 422, and 460; each had zero cancellation candidate in the narrow subset. Across the full wide grid, 127 candidate residuals had exact depth two and 64,700 had depth one. All 64,827 candidate, prediction, and rational group-law checks and 129,654 q-multiple checks passed, with zero recorded failures. Exact rational relation count was zero in this panel.

The checked-Sage producer took 102.87 seconds on an ordinary host. It spent 34.396 seconds evaluating every exact rational candidate as a diagnostic after selection, including 0.0116 seconds on the wide selected models and 0.0121 seconds on the narrow selected models; those selected intervals are subsets of the diagnostic total. The wide search adds about 49.44 seconds of measured model and q-multiple work beyond the nested subset on this host. Public setup, query generation, serialization, and control flow occupy the remainder of the script interval. The [runtime receipt](sage-runtime.json) was saved before the run. These stage intervals do not establish a same-target online IC/rho comparison.

## Proof map and next step

The selection rule uses the first graded additive law of the elliptic formal group. The parent [Lean module](../xedni-leading-defect-selector-20261116/formal/LeadingDefect.lean) proves the linear-combination and kernel-cancellation implications for an explicit additive leading map with arbitrary integer coefficients. Its pinned build and axiom audit are in the parent experiment. Constructing that map from the elliptic reduction-kernel filtration and identifying depth-two membership in Lean remains open. This experiment changes the search family and measures its paired effect; it does not revise the mathematical theorem.

The next discriminating step is an adaptive search on the three remaining hits, with a precommitted stopping rule and explicit cost per newly covered hit. Reproduce this panel with `python3 verify.py`; new local Sage runs use `/Volumes/SSD990/cryptanalysis/sage --runtime-info` before `/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/run.py`.
