# Width-eight rational-height beam

## Measured result

The precommitted width-eight beam reached 313-adic formal-parameter depth
eight on the same public relation used by the three parent experiments.
Its best exact rational model at that depth is 158 bits, 47 bits below the
first-axis path and 49 bits below the greedy model-height path. The final
group residual is nonidentity; its rational coordinates require 3,803 bits
at maximum. This is a measured representation-height improvement for the
fixed relation and depth.

| Depth | First axis | Short digit | Greedy model | Width-eight beam |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 23 | 23 | 23 | 23 |
| 2 | 54 | 32 | 22 | 22 |
| 3 | 74 | 69 | 40 | 37 |
| 4 | 102 | 100 | 82 | 57 |
| 5 | 119 | 102 | 106 | 76 |
| 6 | 148 | 150 | 157 | 111 |
| 7 | 177 | 200 | 157 | 119 |
| 8 | 205 | 235 | 207 | 158 |

All columns use `p=313`, subgroup order `q=331`, target scalar `w=300`,
offsets `(0,13)`, points `(15,174)` and `(236,132)`, and relation vector
`(5,4)`. They start from the identical centered rational model. The metric
is the maximum numerator or denominator bit length among the interpolated
curve coefficients `A,B` and the four point coordinates.

## Search rule and evidence

At each precision, each retained state computes four coordinate finite
differences of `t(5P1+4P2)` modulo `p^(k+1)`. It finds the first feasible
signed-digit radius at most eight and enumerates every cancelling tuple
through radius `h+2`. Candidate selection uses only the interpolated
curve and point model height; it does not inspect each candidate's group
residual. Equal shift tuples are deduplicated, and the beam retains the
first eight by `(model_bits, max_abs_shift, sum_abs_shift, shift_tuple,
parent_id, digit_tuple)`. The selected states are then checked by exact
rational group arithmetic before the next expansion.

The seven compressed JSONL ledgers contain all 1,139 candidate models,
their parent derivative probes, selection flags, and failure statuses.
`run-result.json` pins each ledger's raw and compressed SHA-256 and retains
every selected state's exact curve, points, residual, and formal parameter.
The independent `audit.py` checks the hashes, enumerates all bounded
candidate tuples and minimum-radius certificates, reconstructs their
models using `Fraction`, and replays every retained exact group sum. Its
receipt is `audit-result.json`.

The checked [height-divisibility theorem](../xedni-hensel-height-20261118/formal/HeightDivisibility.lean)
still requires a bound on the exact residual numerator before it can force
an exact relation. This beam run measures an improved finite-depth lift;
the model height and residual-coordinate height remain separate quantities.
The next mathematical step is a uniform relation between them for this
lift family, with the reduction-kernel assumptions stated explicitly.

## Reproduction

From the repository root with the three parent results present:

```sh
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/xedni-height-beam-20261118/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/xedni-height-beam-20261118/run.py
python3 experiments/xedni-height-beam-20261118/audit.py
```

`protocol.json` freezes the beam width, radius cap, ranking, parent
result digests, and stop rules. `runtime-info.json` records the accepted
Sage build. Construction timing is a diagnostic and is not a same-target
IC/rho comparison.
