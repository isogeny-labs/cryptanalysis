# An affine W23 code pair saturates the RR linear-certificate space

For a frozen N131 W23 affine source family, the target-conditioned
Riemann–Roch determinant's nonconstant sign coefficients reach **full
131-bit rank after the second code's second x root**. Their pooled ranks
across the first four charts are **34, 68, 102, 131**. A shared binary-linear
functional can separate zero for the first three charts, but none can do so
for the fourth or the complete four-code family. Independent checked Sage
recomputed all 512 determinants and the same rank sequence, then a separate
curve-addition replay checked all 512 sign assignments against the raw
public point. A third checked-Sage audit reconstructed all 18 selected and
fixed folded columns. All 512 signs miss that point. This is an exact obstruction to
one common linear determinant-word certificate on this source-valid affine
family; `candidate_id` is `null`.

## Frozen selection and exact test

The curve is `y²+xy=x³+1` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, curve ID
`EC1N131Ckb1heb5f1998f20b`. The raw public target and five suffix pair
points are frozen in the earlier [RR panel](/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/n41_n131_sixpair_rr_root_span_20261016/frozen_panels.json).
The [protocol](protocol.json) fixes first-slot anchor mask `3`, seed mask
`898618`, the direction order, source checks, one worker, 600 s wall alarm,
and a 4-GiB recorded RSS envelope before selection. The first eligible
affine square has masks `(3,515,1027,1539)` and selector directions
`(512,1024)`. The checked-Sage [preparer](panel.json) tried 2,233 direction
pairs; 20 gave four source-valid edges, and one passed the eight-column and
five-fixed-edge disjointness checks. It independently reconstructed both x
roots and both signs of every pair output and checked the distinct-x
determinant chart.

For six selected points and `-Q`, evaluate the `L(7O)` basis
`(1,x,y,x²,xy,x³,x²y)`. Changing a point sign changes its y coordinate,
and the 7×7 determinant has Boolean degree at most three in the six sign
bits. The 34 possible nonconstant coefficients are field words. A single
GF(2)-linear functional `L` that kills all nonconstant words and maps each
constant word to one would certify every sign in those charts has nonzero
determinant. The screen inserts the coefficient words and labelled constants
into binary bases, in the frozen order code 0 root 0, code 0 root 1, etc.

| Frozen chart prefix | Pooled nonconstant rank | Pooled augmented rank | Common linear separator |
| --- | ---: | ---: | --- |
| Code 0, root 0 | 34 | 35 | yes |
| Code 0, roots 0–1 | 68 | 70 | yes |
| Code 0 both roots; code 1 root 0 | 102 | 105 | yes |
| Codes 0–1, both roots | **131** | **132** | **no** |
| All four codes, both roots | **131** | **132** | **no** |

The full nonconstant span forces every linear functional annihilating it
to be zero. The labelled constant requirement then makes a common separator
impossible. The checked [Lean theorem](SpanObstruction.lean) formalizes this
structural implication; [PROOF_MAP.md](PROOF_MAP.md) states the exact scope
and computational bridge. The earlier arbitrary-code N131 panel required
four root-zero code charts to reach rank 131. This affine family reaches it
after two codes when both roots are included; this is one frozen family, not
a rank statement for every affine square.

## Measurement and next gate

The source selection interval was 4.315 s, the native-field rank screen
0.080 s, independent Sage determinant replay 2.230 s, and direct group
replay 0.267 s. These are separate ordinary-host process intervals after
their imports and startup. Their respective peak self RSS readings were
263.8, 22.0, 266.5, and 260.1 MB. Each run completed under its wall alarm;
the 4-GiB RSS threshold was recorded, not enforced by a parent monitor.
The [rank result](result.json), [Sage determinant audit](audit_result.json),
[group audit](group_audit_result.json), and [column audit](column_audit_result.json) retain all chart outcomes and
source hashes.

The shared-linear RR certificate cannot reject this complete affine family
even though its 512 exact signs all miss the target. The next N41 unpinned
public-point gate should use a code-dependent or nonlinear partial-RR
condition and measure whole-family rejection before signed-state expansion.
A method that passes that gate and fits the frozen N131 one-worker,
600-second, 4-GiB relation envelope can advance to the ordinary N131 point;
relation rank, target descent, and matched isolated rho remain charged
parts of the full pipeline.
