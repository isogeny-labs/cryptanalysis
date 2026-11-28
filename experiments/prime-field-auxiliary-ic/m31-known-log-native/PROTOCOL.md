# Public M31 known-log pair-table control

Question: can the existing fast signed pair table, with every base point's
generator coefficient constructed and charged, solve a single M31 public
target cold faster than the matched rho implementation? This is the known-log
two-sum method already present in `crypto/src/cryptanalysis/ecbench/known_log.rs`,
not a novel index-calculus algorithm. Its purpose here is to isolate whether
factor-base logarithm acquisition, rather than pair lookup and group
arithmetic, is the current bottleneck.

Build a target-blind base of B distinct signed scalar classes sampled from
`SplitMix64(base_seed=20261128)`, with each point `[s_i]G` computed from the
public generator and every scalar multiplication charged. Lift the resulting
x coordinates through `FactorBase::without_maps`; retain the exact signed
coefficient of each representative. Build `PairIndex` and probe
`R=Q+[a]G`, incrementing a by one with each query. On a verified signed pair
relation `R=ε_iF_i+ε_jF_j`, compute
`k=ε_i s_i+ε_j s_j-a mod N`; require `[k]G=Q` before reporting.
Count all failed probes, setup and certificate replay. No target scalar enters
the worker. Group-law correctness is a proof obligation, separate from
wall-clock measurements.

Development screen: frozen public Q=(988441464,1643383878), B=128,192,256,384,
seeds 0,1,2, 1M-query and 5s online caps. Compile before timing; fresh process
per arm; rotate B order. Charge parent-plus-child CPU and wall from before
launch through exit, parsing and public group-equation verification. Preserve
incomplete/failure arms. Compare to same-target archived C++ rho and current
integrated IC B384. If any size beats both on median charged wall and CPU,
freeze a five-target validation before drawing or running additional targets.
The validation must include a same-memory BSGS control because the known-log
method is a generic table/search trade.

Prior work: `crypto/src/cryptanalysis/ecbench/known_log.rs` implements the
target-blind known-log two-sum algorithm and its work ledger; `docs/ic/README.md`
describes the factor-base-log/individual-log split (KB source
`source:1b0931506d3ea315eba4ef0e525701`). The existing corpus reports
sub-rho results for neither its 16-, 20- nor 24-bit cold counted panels.
This screen makes no novelty, asymptotic or security claim.

## Frozen five-target validation (before execution)

Development screen outcome: known256 passed the prespecified median gate on
one public Q across three seeds. The next panel uses the five immutable public
Q in `m31-integrated-local-screen/fresh-public.json` (SHA256
`dc724fc613d9c2b824b90d59c876f1f7f84b3273d8d607c648e1ba3fbc089252`),
three seeds 0,1,2 and four arms per block: known256, current integrated IC384,
archived C++ rho, and existing CT322 generic BSGS source recompiled on the
same curve. Shuffle 15 blocks with `random.Random(2026112751)`; rotate arm
order by `(target+seed) mod 4`. No additional tuning or dropping unsuccessful
arms. Each process is cold, with source compilation before timing, and external
wall and parent-plus-child CPU include launch, output parse, and independent
public group-equation verification. Timeout is 20s per arm. Preserve stdout,
stderr, binary/source digests and every status. Report medians across 15
matched blocks, per-target medians, paired ratios and win counts. Include
internal phase breakdown for known256 and IC384. Peak RSS where available;
CT322 has ~46k full-point baby entries and known256 has ~65k pair entries,
so BSGS is a comparable table-size control, not an exact byte-matched one.
Do not claim memory parity without a per-process measurement.

This is a generic known-log table/search comparison, not an algorithmic
breakthrough even if it wins this local panel. The five-target validation
tests one host and one curve. Group-law implications need an actual Lean
theorem; timing comparisons are empirical and are not Lean obligations.
