# Six-class GLV rho secp256k1 throughput unmeasured

- **Status:** `open`
- **Kind:** implementation gap and empirical bottleneck
- **Affected work:** [2026-10-24 six-class assessment](../docs/sixclass-20261024/assessment.md), Curve Smash `six-class-rho-secp-tight-v2` adoption
- **Next action owner:** research implementer
- **Last updated:** 2026-10-24

## Problem

We cannot establish a secp256k1 cost or success improvement from the present six-class integration because it contains a 64-bit toy C solver and a BigUint Rust research worker, with no fixed-limb production implementation or matched secp256k1 measurement. The cited 126.96-bit estimate depends on the source submission's H1 mixing and cost model. The current implementation and small-curve run do not test the production scale or that model.

## Evidence and uncertainty

- **Observed:** The [paired raw receipt](../docs/sixclass-20261024/paired-glv-j0-26.json) covers 20 planted `glv-j0-26` logs: all solved, with the six-class path 1.257 times slower in one local run. The C implementation is opt-in in `src/sixclass.c`.
- **Observed with drift control:** The [A/B/A raw receipt](../docs/sixclass-20261024/paired-glv-j0-26-aba.json) covers the same 20 planted targets. Both default arms solved every target and had identical group-operation counts; the six-class time was 1.826 times their mean on this local run. These millisecond solves are a diagnostic, not a precision estimate. The Rust harness also retains two p25 A/B/A trials and a fresh full-curve DP, with all unpriced categories explicit.
- **Routing instrumentation:** The [exploratory two-target telemetry](../docs/sixclass-20261024/routing-telemetry-2trials.md) now records six twist counts and joint twist/route-parity counts for every C class visit. Both row totals reconcile, but walk visits are correlated and this is not an H1 statistical test.
- **Derived or proved:** The six-class automorphism is valid for the checked curve and toy planted-log tests. No secp256k1 throughput theorem or end-to-end cost measurement is established.
- **Suspected explanation:** Extra canonicalization, DP management and short-cycle work may outweigh a quotient gain on this curve. A matched operation and wall-time breakdown is needed to distinguish these costs.
- **Missing capability:** A fixed-limb worker with batch inversion, production branch count, a global field-operation and memory work meter, independent sampled trail replay, and matched secp256k1-scale measurement. Versioned native jobs, a local private-answer challenge, a native DP checker, and toy A/B/A rows now exist. The harness's five-clause H1 matrix leaves every distributional clause open.
- **What this evidence does not establish:** The toy loss does not refute a secp256k1 gain; the source submission's conditional estimate does not establish one in this codebase.

## What would unblock it

- [ ] Build and verify a fixed-limb secp256k1 worker implementing the frozen six-class protocol, with independently replayed sampled trails and a pinned binary/job receipt.
- [ ] Run a preregistered matched ladder with default GLV rho and six-class rho, including A/A controls, correctness checks, all setup costs, and confidence intervals. Report a fixed-limb operation breakdown and the gap to the source cost model.

These conditions would establish measured behavior at tested sizes and a defensible extrapolation boundary. They would not by themselves prove H1 mixing or a deployed-curve security reduction.

## Next discriminating step

- **Action or proof obligation:** Implement a fixed-limb version of the existing six-class worker and compare it against the default on the registered 26- to 44-bit GLV ladder before extrapolating.
- **Inputs and controls:** Fixed planted logs, the registered curve IDs, identical host and protocol, A/A and default GLV rho references, independent log and sampled-trail replay.
- **Execution limits and stop condition:** Use the existing runbook's resource and review gates; stop a run at its preregistered timeout, recording a censored result rather than treating it as failure or proof.
- **Outcomes and next actions:** A robust win justifies a larger ladder and cost-model audit; a loss prompts profiling and jump/DP redesign; inconclusive results call for precision or controls; infrastructure failure is retried under the same protocol.
- **Recheck trigger:** Fixed-limb worker or new validated ladder evidence.

## Resolution and history

2026-10-24: opened from the toy native implementation and first paired result. Added a local A/B/A receipt, isolated full-curve challenge custody, and a falsifiable H1 matrix. Later added descriptive C routing telemetry. The production throughput and mixing obligations remain open; no production claim is promoted.
