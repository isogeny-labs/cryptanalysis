# Shared quadratic normalization and source-capacity gate

**The frozen two-pair resultant has one reusable quadratic form in the
second 32-bit code, and exactly one exceptional first code (zero) on
each tested N131 target row.** Dividing by the nonzero coefficient
`A(p)=c13*p+c33*p^3` makes every second-code pair coefficient independent
of the first code and target. The pure-integer audit and an independent
Sage field/span audit agree on all four frozen N41/N131 rows. The
[Lean proof map](PROOF_MAP.md) gives the checked normalization,
zero-preservation, exceptional-factor, and enumeration statements.

For the exact 13-term support, the only terms in `q^3` are
`c13*p*q^3+c33*p^3*q^3`. If `q=sum(y_i Q_i)` with binary `y_i`, the
coefficient of `y_i*y_j` for `i<j` is `A(p)*B_ij`, where
`B_ij=Q_i^2*Q_j+Q_i*Q_j^2`. Whenever `A(p)` is nonzero,
`A(p)^(-1) F(p,q)=0` has the same solutions, and its quadratic
coefficient is exactly `B_ij`. The target and first code then affect
only the affine part in the second-code bits. The N131 `B_ij` vectors
have full field-bit rank 131, so there is no smaller output projection
that retains this entire shared quadratic core.

| Frozen row | First-code span rank | Second-code quadratic rank | Other root of `A` in first-code span | Exceptional code count |
| --- | ---: | ---: | --- | ---: |
| N41 constructed positive | 10/10 | 37/41 | no | 1, code 0 |
| N41 ordinary residual | 10/10 | 37/41 | no | 1, code 0 |
| N131 constructed positive | 32/32 | 131/131 | no | 1, code 0 |
| N131 frozen public point | 32/32 | 131/131 | no | 1, code 0 |

N41 uses `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[u]/(u^41+u^3+1)`, W11 seed `112`, and Frobenius rotations
`(12,24)`. N131 uses `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[u]/(u^131+u^13+u^2+u+1)`, W33 seed mask `898618`, and
rotations `(0,18)`. Both use `y^2+xy=x^3+1`; the exact target points
and coefficients are in the pinned result and source tables.

The first-code product map has full rank in each field. Factoring
`A(p)=p(c13+c33*p^2)` leaves `p=0` and the unique square root of
`c13/c33` as its only field roots. The latter lies outside the exact
first-code span on every row; N41's 1,024 codes were additionally
enumerated. For N131 the span test covers all `2^32` codes without
enumerating them. Five nonexceptional first codes and five second codes
per row were evaluated against the full frozen resultant before and
after normalization. This is a structural audit, not a solver timing
comparison.

## Capacity of this exact source law

Two 32-bit source codes give at most `2^64` ordered code pairs. Each
code fixes two source x-coordinates; the binary curve equation has at
most two y-branches per coordinate. Thus there are at most 16 branch
assignments per ordered code pair, or `2^68` branch assignments for
this complete two-pair source law. Duplicate sums and invalid source
codes only reduce its image. For a uniformly sampled point on the full
N131 curve, the probability that this exact law covers it is at most

`2^68 / #E(F_(2^131)) <= 2^68 / (2^131 + 1 - 2*sqrt(2^131))`,

approximately `2^-63` by the Hasse bound. This is an input-law bound,
not a classification of the fixed public point. It shows why even a
zero-cost scan of all first-code blocks for this two-pair law would have
very low ordinary-target yield. The earlier N41 all-code census found
the known constructed witness and no witness on its paired ordinary
residual; that observation is consistent with the bound but does not
replace it.

The next goal-aligned solver design needs more source entropy: four
independent W33 factor-base points or additional independently coded
pair sources, while keeping exact target-conditioned rejection and
charging all queries. The shared quadratic form remains a reusable
component if a higher-arity construction conditions one pair at a time.

## Reproduction and status

The [protocol](protocol.json) pins the exact source files, scripts,
runtime, results, and Lean log. Run `python3 verify.py` here to check
the hashes and cross-audit; its current result is `VERIFIED` for four
rows and sixteen pinned hashes. The independent audit used the
repository's checked Sage launcher and retained
[runtime information](sage_runtime_info.json). Its first two invocations
stopped before an arithmetic result because of a cross-parent modulus
equality check and a missing `fetch_int` method; the corrected audit
uses coefficient-list equality and polynomial-basis conversion.

This is an ordinary-host algebraic diagnostic with `candidate_id: null`.
It records no one-target online IC/rho measurement. The earlier
[width-four degree-order solve](../joint_block_order_20261018/RESULT.md)
remains the measured conditioned-solver component; its 600-second
N131 block envelope cannot be promoted into a full ordinary relation
from the source law audited here.
