# Degree-order recovery of an N131 W33 width-four source block

**Degree reverse lexicographic reduction recovered the verified N131
two-pair source codes `(3,16722)` with four first-code bits and all 32
second-code bits free in 426.50 seconds.** The paired frozen public raw
point's width-four source block returned the unit ideal in 335.48
seconds. Both runs stayed within one worker, a 600-second parent wall
cap, and 4 GiB sampled combined RSS. The earlier lexicographic query
on the same constructed positive ended `BOUNDED_UNKNOWN` at its
600-second cap. This is a cap-to-completion improvement for the
target-conditioned two-pair component; the full first-code space and
higher-arity relation search remain the next gates.

The [source diff](source_diff.patch) shows the only algorithmic change:
`BooleanPolynomialRing` uses `order='degrevlex'` instead of `order='lex'`.
The new script also records the order in its output. It builds the same
13-term resultant ANF: 131 field-bit equations, 36 Boolean variables,
5,317 monomials, and 2,976 degree-four monomials on each N131 point.
The source products, rotations, target points, code blocks, input hashes
and caps are frozen in [protocol.json](protocol.json).

| Frozen setting | Exact value |
| --- | --- |
| N41 control | `EC1N41Ckb1h7d5e80d3c4d0`; `GF(2)[u]/(u^41+u³+1)`, W11, seed `s=112`, rotations `(12,24)`, first-code width five |
| N131 target | `EC1N131Ckb1heb5f1998f20b`; `GF(2)[u]/(u^131+u^13+u²+u+1)`, `y²+xy=x³+1`, W33 seed mask `898618`, rotations `(0,18)` |
| N131 block | First codes `0..15`; all 32 bits of the second code free |
| Positive point | `(5517532314023373700997554907490549211, 1154446546775871399813774752133352167830)` |
| Public raw point | `(877610862732227974378969808549299291499, 2063336771837286479337213121437715536874)` |
| Candidate identity | `candidate_id: null`; actual full IC factor base and target pipeline unresolved |

The [N41 promotion gate](n41_gate.json) first recovered the archived
positive pair `(253,63)` with five first-code bits free and reported the
unit ideal on its paired ordinary residual. Its positive and ordinary
monitored walls were 38.65 and 32.90 seconds. The prior lexicographic
N41 walls were 22.41 and 21.19 seconds on separate ordinary-host runs;
the degree-order pilot therefore has no N41 timing win. The frozen
N41 all-code census and exact witness replay bind the control's
correctness.

The N131 public query was launched only after the
[positive gate](positive_gate.json) checked all 36 recovered code bits,
the complete solver receipt, and the earlier independent source-point
and curve-sum replay for `(3,16722)`. The public unit-ideal result is a
PolyBoRi report; a separately checkable Gröbner certificate was not
saved. The [panel verifier](verify_panel.py) replays source hashes,
both terminal receipts, the frozen gates and the same-input lexicographic
cap. Its [receipt](panel_verification.json) passes.

| N131 width-four stage | Constructed positive | Frozen public block |
| --- | ---: | ---: |
| Exact ANF build | 1.838 s | 3.046 s |
| PolyBoRi Gröbner reduction | 416.646 s | 324.962 s |
| Monitored child interval | **426.498 s** | **335.480 s** |
| Sampled combined peak RSS | 2,250,686,464 B | 2,216,738,816 B |
| Terminal result | `(3,16722)`, 36 pinned bits | Unit ideal reported |

These are one-worker ordinary-host component measurements with checked
Sage startup and ANF construction included in the monitored interval.
The [runtime receipt](sage_runtime_info.json) was saved before the
workload. The mathematical expansion is covered by the prior
[checked Lean proof map](../joint_block_gb_20261018/PROOF_MAP.md).
The previous lexicographic width-four positive row remains a
600.149-second `BOUNDED_UNKNOWN` receipt with 1,912,569,856 B sampled
peak RSS; its public block was gated. A capped run does not give a
numeric timing ratio against the completed degree-order run.

At width four, a disjoint scan of the full 32-bit first-code domain
still requires `2^28` block queries per residual. The measured
335–426-second block cost makes serial scanning incompatible with the
600-second ordinary-relation gate. The next algorithmic experiment
should reuse the second-code quadratic reduction across many first-code
regions or derive a nonlinear target-conditioned rejection rule that
covers much larger regions. The preceding [top-degree rank result](../resultant_topdegree_rank_20261018/RESULT.md)
shows that a binary-linear output projection cannot remove every
quartic term from this encoding.
