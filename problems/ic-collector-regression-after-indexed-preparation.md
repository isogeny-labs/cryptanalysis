# Collector regression after indexed pair preparation

- **Status:** investigating
- **Kind:** unknown cause; empirical phase regression
- **Affected work:** [indexed preparation report](../experiments/ic-pair-index-gather-20261117/REPORT.md), claim PCC-20261117-0b5377, [static dictionary protocol](../experiments/ic-static-witness-map-20261117/PROTOCOL.md)
- **Next action owner:** Codex / T-7064 / PR #1709
- **Last updated:** 2026-11-17

## Problem

The indexed preparation experiment does not yet explain why N24 and N27 collector clocks regress despite lower fixed-development instruction totals and several table-setup gains. This prevents a causal explanation and a broad pipeline-improvement conclusion; it does not prevent further bounded optimization. [pcc:unverified]

The frozen seven-path panel uses the original N15/18/21/24/27 curves/bases, fixed m2/direct probe, identical point and relation schedules and compact witness storage. The acceptance criterion remains measured same-target primary cost with correctness/replay, retained controls and exact setup/collector boundaries. [pcc:unverified]

## Evidence and uncertainty

- **Observed:** job084938-72bc completed210blocks; all2310answers/10240states replay. Four failed A/A rows are retained, none in N24/N27. N24 compact-inverse/indexed-inverse collector ratio0.946381[0.938764,0.969274], packed-inverse/indexed-inverse0.965837[0.953195,0.978858]. N27 corresponding ratios0.983146[0.977529,0.990853] and0.987050[0.979115,0.994297]. Full primary/setup results are in the linked unsigned report; the N27 primary interval improves slightly. [pcc:unverified]
- **Derived or proved:** semantic schedule, map and first-witness equality pass the recorded checks. A causal explanation for collector-clock changes is not established. [pcc:unverified]
- **Suspected explanation:** allocation/cache/code-layout coupling is a hypothesis only. An additional instruction/call layer, instrumentation metadata and environmental effects have not been separately excluded at N24. No hardware-counter evidence is available in this study. [pcc:unverified]
- **Missing capability:** matched N24 instruction/call-edge evidence and a controlled counterfactual that changes one suspected source of the slowdown at a time. [pcc:unverified]
- **Limits:** N27 whole-guest instruction savings cannot explain N24 collector timing. Zero failed A/A rows in a field does not establish a physical cause, complete-process cold or a signed performance verdict. [pcc:unverified]

## What would unblock it

- [ ] Before new fresh timing, admit matched N24 development inputs/source/units and compare compact, packed, indexed and static paths under the separate protocol.
- [ ] If work counts remain unchanged, freeze a counter-only or old-scratch-reservation counterfactual before any additional timing; retain source variants and all outcomes.
- [ ] Identify a repeatable causal contrast with independent correctness/replay, then test the remedy against the original control in a separate full primary comparison.

Instruction evidence can narrow the cause without resolving native timing. A faster new dictionary does not itself resolve the earlier attribution question. A signed/qualified broader conclusion still requires the repository's independent evidence gates. [pcc:unverified]

## Next discriminating step

- **Action:** execute the separately declared N24 instruction diagnostic before fresh target generation, not on the completed timing allocation.
- **Inputs/controls:** exact fixture0 public point, synthetic unit values1 explicitly labeled non-timing, immutable compacta44/packedd238/indexed847 binaries and admitted new static source.
- **Limits:** the new preparation's existing4CPU/8GiB/L4/900s envelope and published child caps; no completed-panel instrumentation or host replacement.
- **Outcomes:** extra instruction/call work identifies a source-level candidate to isolate; equal work leaves layout/allocation/environment hypotheses open. Failure or censoring retains the original uncertainty and raw evidence.
- **Recheck trigger:** completed native diagnostic or a published controlled counterfactual.

## Resolution and history

2026-11-17: recorded the observed collector regression and missing causal contrast without changing the frozen indexed panel. Status remains investigating. [pcc:unverified]
