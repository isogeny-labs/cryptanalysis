# Fresh-target transfer of the frozen Hensel beam

The frozen width-eight beam reached depth eight with a lower exact rational model height than the first-axis rule on **all 13 public relation hits** in a new 32-target panel. Paired reductions range from 12 to 68 bits. An independent Python audit re-enumerated the public panel and checked all 10,392 beam candidates and all 13 first-axis paths.

## Frozen workload

[`protocol.json`](protocol.json) was written before the new target seed was evaluated. It pins the SHA-256 target label `xedni-hensel-independent-transfer-v1`, the prior public field/vector protocol, the previous beam result digest, and the exact transfer rule. The finite-field curve is `y²=x³−x−2` in eight prime fields `p ∈ {313,421,431,547,571,593,617,677}`, with the subgroup orders in the parent protocol. There are four newly seeded targets per field, 16 ordered public queries per target, and 13 fixed coefficient vectors per query: 512 queries and 6,656 vector tests. Every public relation with distinct x coordinates is admitted in event order, with equal-x exclusions retained.

The audit finds **zero repeated target points** against the preceding 32-target panel. The field set, query law, and vector family are shared deliberately, so the result tests transfer to fresh targets under the same workload family. Thirteen public hits occurred across six fields; all had distinct x coordinates. Both arms reached the declared depth-eight cap on every admitted hit.

| Hit | `p` | `q` | Target | Query | Vector | First axis bits | Beam bits | Beam − axis bits |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 313 | 331 | 0 | 1 | 12 | 195 | 152 | −43 |
| 1 | 421 | 439 | 2 | 9 | 6 | 214 | 177 | −37 |
| 2 | 421 | 439 | 3 | 7 | 8 | 216 | 189 | −27 |
| 3 | 421 | 439 | 3 | 14 | 5 | 215 | 176 | −39 |
| 4 | 431 | 419 | 1 | 2 | 2 | 208 | 167 | −41 |
| 5 | 431 | 419 | 3 | 0 | 10 | 216 | 167 | −49 |
| 6 | 593 | 313 | 1 | 9 | 11 | 225 | 200 | −25 |
| 7 | 593 | 313 | 1 | 14 | 10 | 221 | 175 | −46 |
| 8 | 617 | 293 | 0 | 6 | 0 | 226 | 158 | −68 |
| 9 | 617 | 293 | 1 | 11 | 5 | 226 | 197 | −29 |
| 10 | 617 | 293 | 2 | 4 | 3 | 210 | 190 | −20 |
| 11 | 677 | 353 | 1 | 8 | 0 | 219 | 207 | −12 |
| 12 | 677 | 353 | 1 | 15 | 7 | 226 | 207 | −19 |

Model height is the maximum numerator/denominator bit length among the two rational curve coefficients and the four point coordinates. It is measured on the exact interpolated rational model, after the same attained depth. The 13 public hits out of 6,656 fixed vector tests describe finite-field admission; the height comparison is conditional on those hits. All 26 final exact rational group residuals are nonidentity at the depth cap. These observations concern model representation size, not a relation-yield or solver-time improvement.

## Raw evidence and replay

[`summary.json`](summary.json) lists every paired comparison and digests for [`run-result.json.gz`](run-result.json.gz). The result retains all public hits and arm statuses, exact models and residuals, and raw/compressed SHA-256 digests for 91 `hitNN.depthK.jsonl.gz` ledgers. [`audit-result.json`](audit-result.json) records the independent replay; [`runtime-info.json`](runtime-info.json) records the checked Sage build before the run. The compressed result SHA-256 was identical on two executions: `dc6aefbdcc34ee73d4b24b11bf638405150eacbe80334e46be8f70bf9d62f68d`.

From the repository root:

```sh
./sage --runtime-info > experiments/xedni-hensel-fresh-transfer-20261118/runtime-info.json
./sage -python experiments/xedni-hensel-fresh-transfer-20261118/run.py
python3 experiments/xedni-hensel-fresh-transfer-20261118/audit.py
```

The Sage run reconstructs and checks every selected exact rational curve, point, residual, and attained depth. The Python audit uses its own modular elliptic-curve arithmetic to regenerate every public query and `Fraction` arithmetic to replay every first-axis and beam candidate, rank, selection, ledger digest, and comparison. It also checks target nonoverlap with the earlier panel.

## Proof map and next step

This is an empirical transfer result and introduces no new mathematical theorem. The earlier checked Lean theorem `numerator_height_lower_bound` in `experiments/xedni-hensel-height-20261118/formal/HeightDivisibility.lean` is conditional on a congruence and rational numerator-height bound. The checked `TorsionSection.lean` in `experiments/xedni-torsion-section-obstruction-20261116/formal/` rules out a relation-preserving homomorphic section under its explicit torsion hypothesis. Neither theorem bounds all nonhomomorphic lift choices in this experiment.

The next discriminating step is a bound or counterexample for the exact rational residual under the frozen finite-width lift law, with the final model size and subgroup assumptions carried into the statement. The present observations support only the paired height property on the two enumerated panels.
