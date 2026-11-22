# CT187 — bounded native-eligible same-route sham and strict reader

2026-11-17 UTC · [pcc:unverified] · [draft PR #1719](https://github.com/isogeny-labs/cryptanalysis/pull/1719) stacked on CT186 #1718.

## New source implementation

The missing bridge between CT186's source-only blinded-placebo design and an executable admitted test is now present as `ct187_native_sham_panel.py`. **Execution was not performed**. The runner is plan-only by default and refuses a native launch without the externally approved owner/provider budget plus explicit execution/admission flags, native binary path/SHA-256, positive global wall-time budget and exclusive output. It reads the immutable original 48-packet Git blob, uses the exact 1,536-position CT186 schedule, physically calls only direct_composite regardless of placebo label, and reuses CT176 bounded output, child process-group cleanup, host/affinity checks, per-child timeouts and aggregate deadline. Invalid or censored samples leave terminal refusal and retained partial evidence rather than a misleading result.

The separate offline adjudication path validates the entire 1,536-child JSONL transcript: exact manifest/schema/roster hash, authenticated original fixture Git bytes, child command, complete base64 stdout/stderr with SHA-256, original 19-word packet/target, all 21 frozen native counters, native clock nesting (setup + route ≤ internal ≤ external), exit/terminal status and RSS presence. Only after validating every sample does it compute the CT186 placebo statistic. The report always states that original full 695/701 custody, signed independent PCC and full cold ECDLP speedup are **not** established.

## Source tests and CI

At exact code/workflow commit `b1adbcbf1b013161e6e9cc8ff00c98022d5b8c89`, [scoped source-only GitHub Actions run #44129576806](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44129576806), job 134202603147, passed its test step. Decoded log: **5/5 CT187 normal Python, 5/5 CT187 optimized Python, plus 7/7 inherited CT186 source-only sham tests**. Included an actual serialized 1,536-record producer-to-reader pass with mocked, correctly structured native transcripts and an expected 1.00× *synthetic placebo* ratio; rejected wrong physical arm, blinded label, pipe digest, terminal count, missing terminal, first-child failure and unsafe plan-mode execution flags. No subprocess was spawned by the test (the runner's native function was patched). Hosted workflow completion and final documentation-only head should be checked separately.

Reproduce on a complete exact-source checkout:

```sh
root=experiments/chained-transfer-public-target/primitive-pricing-01
python3 -S -m unittest discover -s "$root" -p 'test_ct187_native_sham_panel.py' -v
python3 -O -S -m unittest discover -s "$root" -p 'test_ct187_native_sham_panel.py' -v
python3 -S -m unittest discover -s "$root" -p 'test_ct186_same_route_sham.py' -v
```

Plan-only (no native work):
```sh
python3 -S "$root/ct187_native_sham_panel.py" plan --fixture experiments/chained-transfer-public-target/evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json
```

Actual native execution is intentionally **not provided as an authorized command here**. It requires independent admission and a verified native binary. No paid EKS/Spot/GPU allocation was launched.

## Scientific interpretation and next gates

A nonzero placebo effect would diagnose assignment-related timing bias. A zero same-A sham **cannot** prove absence of physical A/B carryover. The designed 1.50× false comparison from CT185 remains a synthetic falsification, not hardware evidence.

Prior evidence reviewed: merged root [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), prospective counter-only [crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215), merged consumer [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), GPU IC [crypto #4178](https://github.com/isogeny-labs/crypto/pull/4178), CT178/182/183/184/185/186 and [central queue #3904](https://github.com/isogeny-labs/crypto/issues/3904). No claim of prior-art absence; shared research-KB and original locked crypto-autoresearcher vault not accessed.

Unresolved: independently authenticated 695/701 original fixture and whole custody; full native 48 arithmetic parity; actual 1,536-process same-host sham and C169/C13a/C13b/N2_actual/D pricing under approval; physically randomized treatment order to test carryover; **complete** public-target single-log ECDLP candidate versus strongest matched rho, BSGS and IC, counting all setup, transfer, inversion, LA, individual-log recovery, memory and uncertainty; signed independent PCC and review/merge gates. No complete solver speedup or mathematical obstruction is claimed.
