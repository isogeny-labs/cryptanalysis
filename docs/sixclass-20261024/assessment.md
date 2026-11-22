# Six-class GLV rho assessment — 2026-10-24

## Question and scope

Can the six-class walk in [Curve Smash commit 1f084c1](https://github.com/Layr-Labs/curvesma.sh/commit/1f084c1914c81a0cdc830b176453adba5dc19ab9) improve our GLV discrete-log research path? This record covers a native C implementation on the registered `glv-j0-26` curve, a paired toy benchmark, and the integration boundary with the Rust `crypto` worker, the `crypto-autoresearcher` harness, and Cairn's native certificate checker. The C solver uses its own job derivation. Cairn now checks the Rust worker's versioned records on both p25 and a full secp256k1 public challenge; C records are not interchangeable with them.

## Method and findings

- **Derived:** For a point `P = aG+bQ`, the six-element orbit uses the three `x` rotations by `beta` and negation. The canonical representative takes the minimum rotated `x` and then `min(y,p-y)`; its key is that `y`. The orientation gives a unit `u(t)` in `{1,lambda,lambda²,-1,-lambda,-lambda²}`. Twisting each jump by `u(t)^-1` makes a jump selected by the class key equivariant. A recorded canonical point carries coefficients `u(t)a,u(t)b`. See [the editable walk diagram](walk.dot) and [rendered diagram](walk.svg).
- **Independently verified on toy curves:** C tests recover planted logs, and the Rust worker has equivariance and planted-log tests. Cairn's independent native checker recomputes the point equation and class/DP predicate. Walker provenance still needs sampled re-walks; a point equation alone does not prove that the claimed steps occurred.
- **Measured, preliminary:** The [original raw paired receipt](paired-glv-j0-26.json) is one local run of `ca_sixclass_bench 20` on `glv-j0-26`: default oriented GLV rho 0.016382582 s, six-class DP rho 0.020590401 s. Both solved all 20 planted targets. Six-class took 1.257× the wall time (25.7% slower), with 46,882 class visits, 2,922 DPs and 196 short-cycle escapes. The [quantitative plot](timing.svg) represents this original run only.
- **Measured with an A/A drift arm:** The [new raw A/B/A receipt](paired-glv-j0-26-aba.json) preserves each of 20 planted targets and the default / six-class / default times. The default arms total 0.012935407 s and 0.012907277 s; six-class totals 0.023595841 s, 1.826× the mean default time. All answers and A/A group-operation counts matched. This is another negative toy observation, not an independent success distribution or a secp256k1 inference. Each solve is only milliseconds long; scheduler and host effects remain material. The raw per-target rows, including any future failure field, are the evidence. No confidence interval or production speed claim is attached.
- **Proposed, unverified at production scale:** The cited submission's 126.96-bit score and ≥0.3909 success are conditional on its H1 mixing and cost model. Commit `1f084c1` changes the accounting constant `κ` from 1.05 to 1.02 and sets the inversion batch to exactly `2^16`; its README states that the algorithm is unchanged. The native BigUint Rust worker and this C toy solver do not implement a practical secp256k1 campaign or validate those asymptotic claims.

## Reproduction and boundaries

The C benchmark uses the registry ID `glv-j0-26`, 20 fixed planted scalars, seed `19+i`, 32 branches, four DP bits, and at most 10,000 walkers for the candidate. Setup is inside each measured solve. The A/B/A version emits every row and a machine-readable failure if any answer or A/A work count differs. The two algorithms have different unit counters; wall time is a toy diagnostic only. The C API is opt-in and the existing default solver stays in place. The Rust worker uses its own versioned job ID and deterministic branch/start derivation. Harness Python launches native binaries, pins receipts, and checks endpoints; Cairn verifies DPs in native Rust. No EKS job was launched for this experiment.

| Method obligation | Current evidence | Status |
|---|---|---|
| Private-answer custody with a public challenge | `crypto-autoresearcher` isolated custody receipt and Cairn secp256k1 objective | Implemented on one host; custodian and Docker daemon remain trusted |
| Falsifiable H1 clauses | `crypto-autoresearcher/harness/fixtures/sixclass_h1_matrix.json` and coverage report | Five clauses registered; empirical validation open |
| Full-work paired comparison | This C A/B/A receipt and `crypto` native paired receipt | Paired toy counters and drift implemented; full production cost unpriced |
| One frozen reviewer-selected follow-up | `crypto-autoresearcher/harness/evidence/sixclass-followup-p25-20261024/` | Bounded local protocol exercised; independent reviewer process open |

The figure sources are [walk.dot](walk.dot) and [timing.tex](timing.tex); their renderings are [walk.svg](walk.svg) and [timing.svg](timing.svg). The [PDF report](assessment.pdf) carries both figures; [assessment.tex](assessment.tex) is its editable source. No isogeny route or canonical volcano graph changes here; the existing `experiments/volcano-ic/figures/` graph set was considered and has no new vertex or edge from this walk.

## Next checks

Repeat paired A/A and A/B runs over the registered GLV curve ladder with independent target seeds, a matched field-operation and memory cost meter, and confidence intervals; sample re-walk native DP receipts; then evaluate a fixed-limb implementation before considering any secp256k1 throughput claim.

The unresolved production-scale obligation is tracked in [six-class GLV rho secp256k1 throughput unmeasured](../../problems/sixclass-secp-throughput-unmeasured.md).
