# CT178 — aggregate wall-clock bound for the native cold-process collector (prospective)

Date: 2026-11-17 UTC. Pre-implementation protocol. [pcc:unverified]

## Hypothesis and failure mode
The CT177 collector has bounded *individual* child execution and capture, but its
fixed 48 packets x 8 blocks x 6 arms = 2304 fresh-process roster has no
aggregate runtime deadline. With the previous 120 s default per-child timeout,
the *nominal timeout sum alone* permits 276,480 s (76.8 h), excluding process
launch, fsync, preflight and host-metadata overhead. Neither this upper bound
nor a launched run is a measured performance claim.

## Fixed scope
Preserve the immutable 48-packet fixture, A/B/B/A/A/A roster, exact executable
SHA-256 and frozen Rust native evaluator. Do not execute any EKS, Spot, GPU or
paid host. No change to historical evidence, to its counters or to CT175 arithmetic.

Before any `--execute` action the operator must supply a positive integer
`--panel-wall-seconds` explicitly *in addition* to prior
`--admission-approved` and genuine external owner/budget admission.
A missing/zero/negative aggregate limit rejects execution before the
first subprocess, while plan-only mode remains available without it.

The collector starts a monotonic deadline before writing the manifest. It
rechecks available budget before *every* spawn and passes the lesser of
per-child timeout and remaining aggregate time to the existing bounded-child
runner. A child that reaches the cap must be killed/reaped under CT177's
existing rules. Failure, timeout or aggregate expiry emits a terminal
`verified_complete=false` refusal and retains any preceding raw samples.
Even if a child returns valid math at/after the aggregate deadline, the
*panel* is refused, not promoted as complete. Exclusive output creation,
flushed/fsynced JSONL and all prior source guards stay unchanged.

## Acceptance checks (synthetic source-only)
1. Exact budget is canonical positive integer; missing and invalid values
   cannot enter the execution path.
2. With a deterministic synthetic monotonic clock, the per-child allowance is
   `min(per-child cap, remaining total)`; no spawn when allowance is zero.
3. The terminal status preserves an aggregate refusal even if a record
   itself verifies.
4. Normal and optimized Python suites retain all CT176/CT177 tests and
   the original 48-packet plan with zero native invocations.
5. Any recorded CI success is only source/synthetic evidence. Native
   typecheck, 695/701 custody, full 48 arithmetic replay, C169/C13a/C13b/
   N2/D timing, cold full prime-field solves, PCC and budget authorization
   remain separate prerequisites.

## Expected negative results
An expired aggregate budget is a *censored measurement*, never a slow
successful sample and never evidence for a transfer advantage. A failure to
execute the full 2304 roster is recorded as incomplete with the originally
requested population unchanged.

## Reproduction
```sh
python3 -m unittest discover -s experiments/chained-transfer-public-target/primitive-pricing-01 -p 'test_ct176_cold_process_collector.py' -v
python3 -O -m unittest discover -s experiments/chained-transfer-public-target/primitive-pricing-01 -p 'test_ct176_cold_process_collector.py' -v
# Plan only; no paid/native execution:
python3 experiments/chained-transfer-public-target/primitive-pricing-01/ct176_cold_process_collector.py --fixture <CT125-frozen-48-fixture>
```

Sources checked: crypto #3877 and #3904, cryptanalysis #1700 and #1706,
CT177 committed collector and test source, cryptanalysis AGENTS.md, and
cross-repository lab contract pointer. Shared research-KB unavailable in
this tool runtime; no novelty claim.
