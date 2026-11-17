# Collector regression after indexed pair preparation

- **Status:** investigating
- **Kind:** unknown cause; empirical phase regression
- **Affected work:** [indexed preparation report](../experiments/ic-pair-index-gather-20261117/REPORT.md), claim PCC-20261117-0b5377, [static dictionary protocol](../experiments/ic-static-witness-map-20261117/PROTOCOL.md)
- **Next action owner:** Codex / T-7086 / PR #1717
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

- [x] Before new fresh timing, admit matched N24 development inputs/source/units and compare compact, packed, indexed and static paths under the separate protocol.
- [x] If work counts remain unchanged, freeze a counter-only or old-scratch-reservation counterfactual before any additional timing; retain source variants and all outcomes. Staged/indexed and counter-presence cells are admitted in one binary; native-clock measurement remains pending.
- [ ] Identify a repeatable causal contrast with independent correctness/replay, then test the remedy against the original control in a separate full primary comparison.

Instruction evidence can narrow the cause without resolving native timing. A faster new dictionary does not itself resolve the earlier attribution question. A signed/qualified broader conclusion still requires the repository's independent evidence gates. [pcc:unverified]

## Next discriminating step

- **Action:** publish fresh fixture726..767 identities and execute the separately frozen seven-path panel after the completed single-binary admission.
- **Inputs/controls:** immutable anchorordinary/compactinverse/indexedinverse controls and the admitted SP/SA/IP/IAinverse cells, matched rho and IPordinary A/A controls on exact public targets.
- **Limits:** one4CPU/8GiB/L4/900s timing allocation, declared780s controller and child caps; no instrumentation, host replacement, A/A filtering or cross-panel products.
- **Outcomes:** the within-binary effects isolate declared setup choices in this build, while frozenindexed/IP checks transfer. A repeatable effect is not automatically a historical cause or allocator/cache explanation. Failure, censoring and inconclusive intervals retain uncertainty and raw evidence.
- **Recheck trigger:** completed fresh panel and independent arithmetic replay, including all failed A/A rows.

## Resolution and history

2026-11-17: recorded the observed collector regression and missing causal contrast without changing the frozen indexed panel. Status remains investigating. [pcc:unverified]

2026-11-17: separate preparation095854-5065 completed; four diagnostic answers independently replay. Compact/packed/indexed selected collector-root/walker/probe/lookup exclusive Ir are respectively869478/1304203/315713/377271 in all three binaries, with8583lookups; inclusive collector10265859/10265770/10265700 differs by at most159Ir. Generic dispatch remains absent. These instruction results narrow an extra-work explanation, but do not resolve the native slowdown. New static map whole Ir falls while lookup Ir rises to405429. Exact raw custody, source/binary admission and limits are in [PREPARATION.md](../experiments/ic-static-witness-map-20261117/PREPARATION.md), unsigned claim PCC-20261117-b9141d. A separate counter-only/scratch counterfactual is still required. [pcc:unverified]

2026-11-17: single-binary preparation145812-d15b admitted staged/indexed and counter-present/absent configurations with exact maps and preserved semantic/inverse-vector counters. Existing independent Python arithmetic checked20pipeline answers,2560walk states and4diagnostic answers; all130outputs passed lossless working-store readback. The four N24cells retain the same selected exclusive collector/walker/probe/lookup counts as the earlier controls. This remains instruction attribution, with native collector-clock causality unresolved. The prospective panel, admission details and raw binding are in [the counterfactual preparation](../experiments/ic-collector-counterfactual-20261117/PREPARATION.md), unsigned claim PCC-20261117-b8257b. [pcc:unverified]
