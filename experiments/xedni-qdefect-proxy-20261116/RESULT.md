# Fresh-target test of a coefficient-independent q-defect proxy

A precommitted proxy based on the bounded-precision depths of `[q]P1` and `[q]P2` changed the selected rational model on 19 of 21 fresh public relation hits, but improved the exact relation residual depth on **zero** hits. The proxy maximized the sum of the two depths before evaluating any relation vector on the candidate lifts. All 13,125 candidate models and 26,250 `[q]P_i` checks passed; 34 candidates had an exact residual at depth 2, while none of the proxy-selected or minimum-model-selected residuals exceeded depth 1. Independent modular projective arithmetic and `Fraction` group replay agree with the checked-Sage producer on every row.

## Frozen workload and selection

The [protocol](protocol.json) pins the eight field/subgroup records, 13 vectors, offsets, and generator law through the earlier fresh-query protocol hash. It changes the target seed label to `xedni-qdefect-v1|p|j` for four targets per field. There are 512 queries and 6,656 public vector tests; the 21 public hits enter the 625-shift rational lift family. No equal-x exception occurred on those hits. This is a fresh target law relative to the preceding wide-shift and depth panels.

For every candidate, Sage constructs the rational model and both points. In `Qp(p,prec=8)` it computes `[q]P1` and `[q]P2`, then caps each `v_p(-x/y)` at 4. The proxy score is their sum. The rule chooses maximum score, then minimum full model score, then lexicographic shift. It uses the known subgroup order and candidate points, but no relation coefficients. A separate minimum-model choice supplies the paired comparator. Only after both choices are fixed does the producer compute every exact rational relation residual.

| Recorded stage or result | Count / value |
| --- | ---: |
| Fresh targets / public queries / vector tests | 32 / 512 / 6,656 |
| Public relation hits / equal-x hits | 21 / 0 |
| Candidate attempts / passed / failed | 13,125 / 13,125 / 0 |
| Rational group-law controls | 13,125 passed |
| `[q]P_i` kernel-depth checks | 26,250 passed |
| First / second `q`-multiple at depth 2 | 30 / 31 |
| Candidates with both `q`-multiples at depth 2 | 0 |
| Proxy score 2 / 3 | 13,064 / 61 |
| Exact rational relation residual depth 1 / 2 | 13,091 / 34 |
| Exact rational relations | 0 |
| Proxy selection differs from minimum-model selection | 19 / 21 hits |
| Proxy residual deeper than minimum-model residual | 0 / 21 hits |
| Proxy and minimum-model selections at depth 1 | 21 / 21 each |

The producer records all query and vector rows, every candidate status, model and proxy score, both capped q-multiple depths, the exact rational relation flag, and residual depth. Its [result manifest](run-result.json) indexes the compressed raw parts. The [pure-Python audit](audit.py) independently regenerates the target law and public group relations, reconstructs every rational model and residual, and computes all q-multiple depths via modular Jacobian formulas modulo `p^4`. Its [receipt](audit.json) is `PASS`.

The checked-Sage script interval was 23.09 seconds on this ordinary host. Exclusive measured stage intervals inside it were 0.19 seconds for candidate construction, 15.23 seconds for q-multiple proxy evaluation, and 7.01 seconds for rational relation checks; the remaining interval covers public setup, query generation, serialization, and control flow. The [runtime receipt](sage-runtime.json) was saved before the run. These are component diagnostics, with no same-target rho comparison or online speedup result.

## Interpretation and next test

The sum proxy favors models with one deeper `[q]P_i`: 61 candidates have score 3, and none has both depths elevated. On this panel that preference changes model choice without making any selected short relation residual deeper. Individual depth loses the leading residue of each q-multiple. The next discriminating rule should compute the leading formal-parameter residues of `[q]P1` and `[q]P2` modulo `p`, score how many vectors in the *predeclared* 13-vector family have leading cancellation, and choose a model before learning which vectors are public relations. That rule needs a new target seed and an independent exact relation audit. Its structural bridge is the additive first-order formal-group law on the reduction kernel; formalization of that elliptic bridge remains open.

Reproduce this evidence with `python3 verify.py`. New local Sage runs use `/Volumes/SSD990/cryptanalysis/sage --runtime-info` and `/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/run.py`.
