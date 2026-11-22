# Corrected target-conditioned two-leaf suffix support on N41

The N41 public-point suffix support is now placed on the correct chain
coordinate. Exact subtraction of all 3,600 signed choices for leaves 10 and
11 yields 3,577 finite residual reciprocal-phi masks for `partial8`, and an
independent formula rebuild maps that coordinate to XCNF variables 402–442.
The corrected guided formula preserves every record of the unpinned source
formula and adds exact membership implications for those masks. This repairs
the archived `partial9` placement error while keeping the public target and
all twelve leaf selectors unpinned.

## Frozen construction and checks

The binary field degree is 41, the curve has cofactor four, and the subgroup
order in the source protocol is `549756390943`. The supplied public point is
`(882970412038, 429061500157)` in the source coordinate encoding. Its
verified endpoint is `(318142711405, 2037395762706)`. The factor-base domain
has 30 valid six-bit phi selectors per position and 60 signed point choices.
The source formula SHA-256 is
`0260fe23321c46749a87fc7d894fcf2af049061e994ffb9a1c0cd15ff713f2c0`;
the corrected formula SHA-256 is
`104b2dde30da29113538a88f218246174ebbaedef4e4fbab51ae2715f8c67253`.
The [protocol](protocol.json) pins every source and executable hash and was
written before solver execution.

The [independent Sage audit](audit_sage.py) rebuilt the source byte for byte,
enumerated all suffix choices, checked `partial8 + P10 + P11 = endpoint` for
each choice, verified equality of the positive and negative endpoint mask
sets, and checked every appended XCNF clause against `partial8` variables
402–442. The group equivalence is [proved in Lean](PROOF_MAP.md) for an
arbitrary additive commutative group. The exact curve and formula bridge is
audited separately. The audit returned
`PASS_GROUP_AND_PARTIAL8_FORMULA_AUDIT` before either solver arm ran.

## Paired unpinned public-point observations

| Arm | Exact status | Parent wall | Sampled combined peak RSS |
| --- | --- | ---: | ---: |
| Source formula | `BOUNDED_UNKNOWN_ARM_WALL_CAP` | 240.019 s | 147,144,704 B |
| Corrected target-guided formula | `BOUNDED_UNKNOWN_ARM_WALL_CAP` | 240.089 s | 395,231,232 B |

Both arms used one CryptoMiniSat worker, the same public point and solver
flags, a 240 s parent cap per arm, a 550 s campaign cap, and a 4 GiB combined
RSS cap. Their solver output contains no terminal SAT or UNSAT state.
[verify.py](verify.py) checked all frozen source, formula, stdout, stderr,
command, and resource receipt hashes and returned `REPLAY_PASS`.
[replay_sage.py](replay_sage.py) retained both bounded statuses in
[replay.json](replay.json). The combined parent solver-arm wall was
480.109 s; these ordinary-host stage results are not an isolated timing
comparison.

## Decision and next gate

The correction establishes complete target-conditioned suffix support and
its exact XCNF placement. The ordinary-relation yield gate remains bounded
under this solver configuration, so this encoding is not promoted to the
N131 public-point cap yet. The source density receipt estimates
`3,726,104.05428` full 15-leaf representations across its four endpoints
under a uniform-sum model. Fixing one signed leaf divides that heuristic by
1,064 to about `3,502`; fixing three divides it to about `0.00309`. A viable
N131 suffix experiment should therefore screen one leaf or keep all leaf
codes free, and test whether a compact projected-membership circuit improves
propagation on this N41 control before spending the N131 budget.
