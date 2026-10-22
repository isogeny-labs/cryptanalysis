---
name: experiment-protocol
description: Design, preregister and freeze an unbiased controlled experiment as an experiment.protocol/v1 record before any data is taken, and land the run's rows as one experiment.export/v1. Pointer to the canonical skill in aburan28/crypto-autoresearcher; here the measurement contract (experiments/ic-candidate-catalog/MEASUREMENT.md) is the instrument, and the protocol is the preregistration that names its claims, controls, seeds, phases and what counts.
---

# Experiment protocol (pointer)

Canonical in `aburan28/crypto-autoresearcher`: skill
`.claude/skills/experiment-protocol/SKILL.md`, rules
`docs/experiment-protocol.md`, schemas `schemas/experiment-protocol.v1.json`
and `schemas/experiment-export.v1.json`, checker
`tools/experiment_protocol.py`, example
`examples/experiment-protocol/ecbench-l2-smoke-subset/`. Read the canonical
skill and follow it; where this pointer and it disagree, the canonical skill
wins. This repository's `AGENTS.md` rules on candidate and curve identity,
the one-target online metric, phase accounting, CPU performance evidence
tiers and GPU run records still bind every design here.

## In this repository

- `protocol.json` sits in the experiment directory beside the candidate and
  workload manifests and is committed before the first run. Its arms are
  candidates (`candidate_id`) and the paired rho reference; the A/A arm is
  the same candidate under a second `pair_block_id`; the positive control is
  a planted decomposition or a known-scalar target (a completeness check,
  never a yield estimate); a negative control, where a yield or rate is
  claimed, is the matched ordinary-query stream or a certified UNSAT
  control.
- Counted metrics first (`total_operations`, phase operation counts,
  verified relations, rank increments); `online_wall_ns` is a timed metric
  that needs `timed_primary_justification` and a Tier 0 or Tier 1 receipt
  (`isolation_required: tierA` or `tierB`).
- The measurement contract's one-JSON-object-per-run `.jsonl` is the raw
  record; the export is built from it with `from-rows` (map `run_id`,
  `candidate_id` as the arm, `workload_id` as the instance, `status`,
  `wall_ns` and the phase counts), checked with `check-export
  --verify-files`, and committed beside the `.jsonl`.

```sh
A=../crypto-autoresearcher/tools/experiment_protocol.py
python3 $A validate experiments/<study>/protocol.json
python3 $A freeze experiments/<study>/protocol.json --commit auto --filed-before-affected-data
python3 $A from-rows experiments/<study>/runs.jsonl --protocol experiments/<study>/protocol.json \
    --out experiments/<study>/export.json --export-id <study> --map arm=candidate_id --map instance_id=workload_id
python3 $A check-export experiments/<study>/export.json --protocol experiments/<study>/protocol.json --verify-files
```

Use a sibling checkout at `../crypto-autoresearcher` on `origin/main`; never
copy the tool here.
