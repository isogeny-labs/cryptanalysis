# Six-class GLV rho assessment — 2026-10-24

## Question and scope

Can the six-class walk in [Curve Smash commit 1f084c1](https://github.com/Layr-Labs/curvesma.sh/commit/1f084c1914c81a0cdc830b176453adba5dc19ab9) improve our GLV discrete-log research path? This record covers a native C implementation on the registered `glv-j0-26` curve, a paired toy benchmark, and the integration boundary with the Rust `crypto` worker, the `crypto-autoresearcher` harness, and Cairn's native certificate checker. These four implementations use the same class mathematics but currently have separate job derivations. Their DP records are not interchangeable.

## Method and findings

- **Derived:** For a point `P = aG+bQ`, the six-element orbit uses the three `x` rotations by `beta` and negation. The canonical representative takes the minimum rotated `x` and then `min(y,p-y)`; its key is that `y`. The orientation gives a unit `u(t)` in `{1,lambda,lambda²,-1,-lambda,-lambda²}`. Twisting each jump by `u(t)^-1` makes a jump selected by the class key equivariant. A recorded canonical point carries coefficients `u(t)a,u(t)b`. See [the editable walk diagram](walk.dot) and [rendered diagram](walk.svg).
- **Independently verified on toy curves:** C tests recover planted logs, and the Rust worker has equivariance and planted-log tests. Cairn's independent native checker recomputes the point equation and class/DP predicate. Walker provenance still needs sampled re-walks; a point equation alone does not prove that the claimed steps occurred.
- **Measured, preliminary:** The [raw paired receipt](paired-glv-j0-26.json) is one local run of `ca_sixclass_bench 20` on `glv-j0-26`: default oriented GLV rho 0.016382582 s, six-class DP rho 0.020590401 s. Both solved all 20 planted targets. Six-class took 1.257× the wall time (25.7% slower), with 46,882 class visits, 2,922 DPs and 196 short-cycle escapes. This is a negative result on this small curve, not an inference about secp256k1. The [quantitative plot](timing.svg) has total seconds, `n=20`; no error bars are available from this single run. A/A repeats and a larger curve ladder remain open.
- **Proposed, unverified at production scale:** The cited submission's 126.96-bit score and ≥0.3909 success are conditional on its H1 mixing and cost model. Commit `1f084c1` changes the accounting constant `κ` from 1.05 to 1.02 and sets the inversion batch to exactly `2^16`; its README states that the algorithm is unchanged. The native BigUint Rust worker and this C toy solver do not implement a practical secp256k1 campaign or validate those asymptotic claims.

## Reproduction and boundaries

The C benchmark uses the registry ID `glv-j0-26`, 20 fixed planted scalars, seed `19+i`, 32 branches, four DP bits, and at most 10,000 walkers for the candidate. Setup is inside each measured solve. The two algorithms have different unit counters; use wall time for this one paired comparison. The C API is opt-in and the existing default solver stays in place. The Rust worker uses its own versioned job ID and deterministic branch/start derivation. Harness Python only launches the native Rust binary and independently checks any recovered log; Cairn verifies DPs in native Rust. No EKS job was launched for this experiment.

The figure sources are [walk.dot](walk.dot) and [timing.tex](timing.tex); their renderings are [walk.svg](walk.svg) and [timing.svg](timing.svg). The [PDF report](assessment.pdf) carries both figures; [assessment.tex](assessment.tex) is its editable source. No isogeny route or canonical volcano graph changes here; the existing `experiments/volcano-ic/figures/` graph set was considered and has no new vertex or edge from this walk.

## Next checks

Repeat paired A/A and A/B runs over the registered GLV curve ladder, with a matched cost meter and confidence intervals; sample re-walk native DP receipts; then evaluate a fixed-limb implementation before considering any secp256k1 throughput claim.

The unresolved production-scale obligation is tracked in [six-class GLV rho secp256k1 throughput unmeasured](../../problems/sixclass-secp-throughput-unmeasured.md).
