---
name: review-run
description: Review another runner's experiment from its experiment.export/v1 bundle, without the producer's session, and file a write-once experiment.review/v1 record of checks, observations, per-claim judgments, open questions and a recommendation. Pointer to the canonical skill in aburan28/crypto-autoresearcher; here a review is an input to the PR review and the IC benchmark baseline gate, never a history.csv row or a promotion.
---

# Review a run (pointer)

Canonical in `aburan28/crypto-autoresearcher`:
`.claude/skills/review-run/SKILL.md`, schema
`schemas/experiment-review.v1.json`, tool `tools/experiment_protocol.py
review new|validate`. Read the canonical skill and follow it; where this
pointer and it disagree, the canonical skill wins.

## In this repository

- Replay with the native instruments: `ca_rho_solve`, `ca-ic` and `ca_bench`
  at the pinned source hashes, `experiments/ic-candidate-catalog/analyze.py`
  on the `.jsonl` for the rates and the paired online speedup; a replay
  writes only under the review directory.
- Check the one-target accounting: the five exclusive online phases sum to
  `online_wall_ns`, the paired rho solved the same public point, the scalar
  certificate verifies, and planted rows were not counted as yield.
- File the record under `<study>/reviews/REV-*.json` on your own branch and
  open or refresh a PR; the `fb-refs`, `fb-archive` and IC benchmark gates
  still apply to anything the review's PR touches.

```sh
A=../crypto-autoresearcher/tools/experiment_protocol.py
python3 $A review new experiments/<study>/export.json --role validator --runtime <r> --model <m> --session <s>
python3 $A review validate experiments/<study>/reviews/REV-*.json
```
