# Exact cubic two-product branch on ECC2K-130

**Fixing the first source-code low bit to one gives an exact cubic
two-product equation with no exceptional-product guard.** On an eight-code
N131 first-source branch with all 32 second-source bits free, the cubic
Gröbner solver recovered the independently group-replayed constructed pair
`(3,16722)` in 53.23 s and returned a unit ideal on the matched frozen
public-point block in 47.46 s. The original quartic equations on the
**same** blocks took 93.21 s and 65.89 s. A 16-code N131 cubic branch
reached the 4-GiB sampled RSS cap at 242.17 s, setting the next scaling
boundary. These are ordinary-host component measurements; the complete IC
candidate remains `candidate_id: null`.

## Exact branch and controls

The fields are `GF(2)[u]/(u^41+u³+1)` and
`GF(2)[u]/(u^131+u^13+u²+u+1)`, with curve `y²+xy=x³+1`. The curve IDs
are `EC1N41Ckb1h7d5e80d3c4d0` and `EC1N131Ckb1heb5f1998f20b`.
The N41 source seed is `112`, with product rotations `(12,24)`; the N131
seed mask is `898618`, with product rotations `(0,18)`. The first source
code is `base | Σ bᵢ 2^(i+1)`: base `225` with four free positions on N41,
and base `1` with three or four free positions on N131. The second source
code keeps all 10 or 32 canonical bits free. The known positive first codes
`253` and `3` lie in these branches.

For pair parameter `a` and seed `s`, the first source product is
`p=a(a+s)`. The fixed-one low code bit excludes both `a=0` and `a=s`
on the stated canonical branches, so `p≠0`. Therefore `p·F(p,q)=0` is
equivalent to the original two-product resultant `F(p,q)=0` on the whole
branch. The earlier [degree-fall result](../resultant_degree1_syzygy_20261019/RESULT.md)
shows that `pF` has Boolean degree at most three even though `F` has degree
four. The [Lean proof map](PROOF_MAP.md) gives the structural proof and the
finite-field bridge. The [checked-Sage audit](audit_result.json) confirmed
nonzero `a`, `a+s`, and `p` on **all 40 first-code occurrences** across the
three tested branches, recomputed the positive roots, and used the prior
independent N131 curve-sum replay for `(3,16722)`. On N41 it independently
enumerated all valid second codes in the branch and found only `(253,63)`
on the positive residual and zero roots on the ordinary residual.

## Frozen measurements

Each solver used one checked-Sage process, `degrevlex` PolyBoRi reduction,
one worker, a 120 s N41 or 600 s N131 wall cap, and a 4-GiB sampled
combined-RSS cap. The parent interval includes launcher, ANF build,
reduction, and wrapper completion. Runtime receipts precede the runs.
Positive N41 is the right two-pair residual of the independently replayed
public relation; ordinary N41 is the frozen public point minus three
distinct-code states. N131 positive is the archived constructed two-pair
control; ordinary N131 is the frozen raw public point. Cubic and quartic
arms use identical code branches, target points, source coefficients,
solver order, and resource caps within each field.

| Field / branch / target | Cubic result; parent wall; peak RSS | Quartic result; parent wall; peak RSS | Cubic / quartic ANF monomials |
| --- | --- | --- | ---: |
| N41, 16 first codes, positive | `(253,63)`; 6.20 s; 330 MB | `(253,63)`; 4.66 s; 298 MB | 346 / 610 |
| N41, 16 first codes, ordinary | unit ideal; 9.95 s; 333 MB | unit ideal; 4.71 s; 296 MB | 346 / 610 |
| N131, 8 first codes, positive | `(3,16722)`; **53.23 s**; 1.19 GB | `(3,16722)`; 93.21 s; 1.95 GB | 2,215 / 3,700 |
| N131, 8 first codes, ordinary | unit ideal; **47.46 s**; 1.19 GB | unit ideal; 65.89 s; 1.89 GB | 2,215 / 3,700 |
| N131, 16 first codes, positive | `RSS_CAP`; 242.17 s; 4.30 GB sampled | not run on this branch | 2,843 / unknown |
| N131, 16 first codes, ordinary | gated after positive cap | gated | unknown |

The same-block ordinary-host parent-wall ratios `quartic/cubic` are
**1.75** on the N131 positive block and **1.39** on its ordinary block;
N41 ratios go the other way. These are stage observations under an
unisolated host, not Tier 0 or Tier 1 CPU speedup measurements. The
public-block unit ideals are PolyBoRi reports without separately retained
Nullstellensatz certificates. The positive N131 codes have an independent
curve-law replay. The width-four capped run produced its `GB_START` row
with 2,843 cubic ANF monomials and no terminal basis; its ordinary case
was not promoted.

The [terminal verifier](verification_result.json) hash-checks each frozen
protocol, source, result and resource receipt, the [Sage audit](audit_result.json),
the Lean axiom log, and the width-four cap. Replay with
`python3 verify_terminal.py`. The first Sage audit attempt raised `KeyError`
when it expected an invalid source code in a table containing valid codes
only; [the failure record](audit_attempt1_failure.txt) and corrected
comparison are retained. The checked runtime records are here and in the
[matched quartic](../nonzero_branch_quartic_baseline_20261023/sage_runtime_info.json)
and [wider branch](../nonzero_branch_cubic_w4_20261023/sage_runtime_info.json)
directories.

## Next algorithmic step

The eight-code oracle handles one fixed two-pair residual. Covering all
`2^32` first-code words with disjoint eight-code branches takes `2^29`
blocks per residual before testing the other three pair slots. The
16-code RSS cap prevents simply widening this Gröbner system under the
frozen one-worker envelope. The next test must share elimination across
many first-code branches or reject a much larger target-conditioned family
per operation; its unpinned N41 relation and N131 public-point work must
be measured end to end before claiming an ordinary N131 relation. A full
candidate then requires useful matrix rank, target descent, independent
scalar replay, and a same-point isolated rho comparison.
