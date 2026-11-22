# Seven forward S3 links encode the all-seed N41 four-pair relation

An exact source-bound Boolean circuit now encodes eight independent masks
from the 125-mask W8 source, forces eight distinct folded columns, and
propagates their four pair sums through seven forward S3 roots to one frozen
public target. A constructed complete assignment satisfies every one of its
361,813 CNF clauses and 97,546 native XOR rows. An independent checked-Sage
replay verifies all seven roots, the eight source points, and the public
point. The unpinned query and a two-pair pinned diagnostic both reached
their frozen wall caps with active solver restarts.

## Exact instance and construction

- Curve ID: `EC1N41Ckb1h7d5e80d3c4d0`; field
  `GF(2)[t]/(t^41+t^3+1)`, curve `y²+xy=x³+1`, subgroup order
  `549756390943`, cofactor four.
- Public point: `(920359962848, 755404565011)`. The checked chart uses raw
  preimage `(946309826754, 403262551014)` under multiplication by four.
- Source: 125 admissible eight-bit masks. Eight masks are selected across
  rotations `(0,7,14,21)`, two per rotation. Their folded columns must be
  distinct. The four pair sums and three higher sums use seven S3 links.
- Primary Boolean choices: 64 mask bits and seven root branch bits. The
  exact circuit has 217,778 variables, 120,161 AND gates, 361,813 CNF
  clauses, and 97,546 native XOR rows. Candidate ID remains null because
  this is a point-decomposition stage, without a complete IC pipeline.

The positive chart is the previously verified diagonal four-pair relation;
its role here is to test the new circuit exactly. It does not add a new
relation row to the N41 matrix. The circuit includes the zero/nonzero guards
of the inherited forward S3 implementation and covers the nonexceptional
reciprocal chart.

## Frozen experiments

| Query | Pinned source masks | Free source masks | Free root bits | One worker cap | Peak combined RSS | Restarts | Recorded status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Ordinary public query | 0 | 8 | 7 | 190 s parent, 4 GiB | 237,993,984 B | 1,304 | `BOUNDED_UNKNOWN`, wall cap, 190.027 s |
| Positive diagnostic | 4 | 4 | 7 | 65 s parent, 4 GiB | 202,604,544 B | 757 | `BOUNDED_UNKNOWN`, wall cap, 65.054 s |

The public formula and solver flags were hash frozen in
[solver_protocol.json](solver_protocol.json) before the unpinned run;
[solver_result.json](solver_result.json) and
[solver_audit.json](solver_audit.json) retain the terminal state, hashes,
restart count, cap and memory. The second run used the same target and
formula with 32 source-mask unit clauses fixed to the known positive chart;
its source hashes and cap are in [pin_protocol.json](pin_protocol.json).
[pin_audit.json](pin_audit.json) checks its frozen hashes and bounded status.
Both rows are exploratory CPU diagnostics on this host, not isolated
wall-time comparisons. The first run returned no SAT/UNSAT terminal before
the parent killed it. The second similarly returned no terminal. Neither
status determines natural relation yield.

The [independent Sage audit](audit_result.json) used the repository's
checked launcher after saving [runtime info](sage_runtime_info.json). It
verified all seven reciprocal roots from native field and curve arithmetic,
eight distinct folded columns, the raw sum, and the public point. The
[proof map](PROOF_MAP.md) gives the checked Lean structural theorem and the
remaining arithmetic bridge.

## Next experiment

Run a frozen pin ladder at three source pairs, then fix source pairs while
varying the seven root branches. These controls separate mask-selection
work from root-choice propagation. If three-pair pinning is easy but
two-pair pinning remains capped, add an exact pair-sum lookup constraint
early in the search, preserve every witness, and compare it on the same
N41 public query and caps before attempting the N131 transfer.
