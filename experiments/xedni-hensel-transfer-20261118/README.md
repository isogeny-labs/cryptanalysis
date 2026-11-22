# Xedni Hensel beam transfer across the fixed public panel

The frozen width-eight beam rule reached depth eight with a smaller exact rational model than the first-axis rule on **all nine distinct-x public relation hits** in the 512-query panel. The paired reduction is 15–47 bits. An independent Fraction replay checked every candidate in all 63 beam ledgers (6,902 candidates), every selected path, and the public hit enumeration.

## Protocol and result

[`protocol.json`](protocol.json) fixes the source panel, admission rule, depth cap, first-axis control, beam ranking, exact checks, and 1,200-second run cap before this transfer measurement. The panel comprises eight prime fields, four targets per field, 16 queries per target, and 13 vectors per query: 512 queries and 6,656 vector tests. All nine public hits had distinct x coordinates and were admitted; there were no exclusions or capped arms. These are the remaining hits in the original panel, so this is a within-panel transfer test, not an independent fresh holdout.

Both arms reached depth eight on each hit. The model height is the maximum numerator/denominator bit length in the exact interpolated rational model, using the same definition in both arms.

| Hit | Field `p` | Subgroup `q` | Target | Query | Vector | First axis bits | Beam bits | Beam − axis bits |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 313 | 331 | 0 | 5 | 3 | 205 | 158 | −47 |
| 1 | 421 | 439 | 1 | 13 | 4 | 212 | 190 | −22 |
| 2 | 431 | 419 | 1 | 15 | 5 | 218 | 174 | −44 |
| 3 | 547 | 571 | 0 | 10 | 2 | 215 | 183 | −32 |
| 4 | 571 | 599 | 3 | 0 | 6 | 224 | 177 | −47 |
| 5 | 571 | 599 | 3 | 11 | 12 | 214 | 199 | −15 |
| 6 | 593 | 313 | 2 | 2 | 8 | 209 | 183 | −26 |
| 7 | 593 | 313 | 2 | 11 | 8 | 228 | 188 | −40 |
| 8 | 617 | 293 | 0 | 1 | 12 | 216 | 198 | −18 |

All 18 final exact group residuals are nonidentity, and every arm stops at the predeclared depth cap. The public-hit frequency, 9/6,656 vector tests, belongs to the fixed finite-field panel; the beam experiment is conditional on those admitted hits. The measured contribution is the rational model-height reduction. It does not measure a complete relation algorithm or a solver-time gain.

## Evidence and replay

[`summary.json`](summary.json) gives the comparison and SHA-256 digests of the compact [`run-result.json.gz`](run-result.json.gz). The full result includes every public hit, per-arm status, shift and exact model record, and the raw/compressed digests for 63 `hitNN.depthK.jsonl.gz` candidate ledgers. [`audit-result.json`](audit-result.json) records the independent replay outcome. [`runtime-info.json`](runtime-info.json) records the checked installed Sage runtime before measurement.

From the repository root:

```sh
./sage --runtime-info > experiments/xedni-hensel-transfer-20261118/runtime-info.json
./sage -python experiments/xedni-hensel-transfer-20261118/run.py
python3 experiments/xedni-hensel-transfer-20261118/audit.py
```

`audit.py` separately enumerates the public panel with Python modular elliptic-curve arithmetic and replays the first-axis paths and all beam candidates with exact `Fraction` arithmetic. It checks the source and beam parent digests, result and ledger digests, rankings, depth, reductions, exact group identities, and paired summary.

## Proof map and next test

This transfer result is empirical. The earlier conditional Lean theorem `numerator_height_lower_bound` in `experiments/xedni-hensel-height-20261118/` relates congruence depth and rational numerator height under its stated assumptions; it does not assert a bound for every lift or every elliptic-curve relation. The independent mod-2 theorem in `experiments/xedni-auxiliary-mod2-independence-20261116/` certifies an abstract quotient-and-descent implication, while the eight concrete rational point-pair certificates are in `experiments/xedni-beam-auxiliary-independence-20261118/`. This experiment introduces no new mathematical theorem.

The next experiment should freeze fresh public instances and repeat the paired height comparison with their complete hit and failure rows. A separate proof step would need a lift-independent bound that connects the rational group residual to the exact coordinate and subgroup hypotheses; the present conditional theorem does not supply that bridge.
