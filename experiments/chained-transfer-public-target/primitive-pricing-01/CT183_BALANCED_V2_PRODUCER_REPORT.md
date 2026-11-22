# CT183 source implementation report — balanced v2 cold-process producer

2026-11-17 UTC · [pcc:unverified] · [draft PR #1713](https://github.com/isogeny-labs/cryptanalysis/pull/1713), stacked only on CT178 producer [#1706](https://github.com/isogeny-labs/cryptanalysis/pull/1706).

## Substantive change and evidence level

A new `ct183_v2_cold_process_collector.py` implements the **producer** for the versioned [CT182 offline adjudicator #1711](https://github.com/isogeny-labs/cryptanalysis/pull/1711). It preserves the entire CT178 bounded stdout/stderr capture, process-group kill/reap, single-child timeout, global panel wall deadline and 48 original packet/output/counter validators through direct import of `ct176_cold_process_collector`. No source file in CT176 has been altered.

The CT181 position-only null falsified the old fixed ABBA design. CT183 assigns ABBA or BAAB according to block+packet parity, retaining two A/A controls. Across 8 blocks and 48 frozen packets, the v2 population remains exactly 2,304 fresh processes. The canonical roster hash `1dddb4839321ad6560fd429330778aa083ff3a13625393250e964c05f9fc5ee4` was independently calculated from Python's deterministic shuffle and six treatment slots; it matches the wire-serialization algorithm in CT182's reader source. Source/fixture tests and the separate hosted workflow still determine whether the new implementation accepts the actual frozen original fixture.

The CLI is **plan-only by default**. Execution requires explicit `--execute --admission-approved --panel-wall-seconds N`, an immutable executable SHA-256 and output path in addition to external owner/provider authorization. There is no authorization for this run. Every child failure and aggregate deadline failure produces a terminal refusal, preserving the incomplete raw panel. The reader does not reinterpret v1 evidence as v2. This is an implementation claim without signed PCC or native proof.

## Reproduce source-level controls only

```sh
root=experiments/chained-transfer-public-target/primitive-pricing-01
fixture=experiments/chained-transfer-public-target/evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json
git hash-object "$fixture" # expected 9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3
python3 -S -m py_compile "$root/ct183_v2_cold_process_collector.py" "$root/test_ct183_v2_cold_process_collector.py"
python3 -S -m unittest discover -s "$root" -p 'test_ct183_v2_cold_process_collector.py' -v
python3 -O -S -m unittest discover -s "$root" -p 'test_ct183_v2_cold_process_collector.py' -v
python3 -S "$root/ct183_v2_cold_process_collector.py" --fixture "$fixture"
```

The added workflow `ct183-balanced-v2-producer-source.yml` is limited to these source/synthetic checks and plan-only; it **does not** run the native Rust binary or test a speedup. Fail-closed test cases include invalid admission and binary hash, empty/invalid budget, first-child synthetic refusal, non-complete terminal, v1 isolation and exact per-packet order balance. CI status must be read for the final commit before calling these tests passing.

## Missing measurement / independent evidence

The producer and adjudicator currently live in **separate stacked draft PRs**; an exact final combined-tree v2 reader/producer compatibility test must run after their branches are reconciled, including authentic 695/701 custody. CT183's source checks are not a substitute for native 48-case parity, approved same-host `C169, C13a, C13b, N2_actual, D_padd` pricing or any cold complete prime-field target solve. All setup, transfer, inversion, LA, target recovery/verification, peak memory and the strongest matched rho/BSGS/IC competitors must be included. The frozen 48 selected-call dataset is a **transfer-only subpopulation**, not the complete Jacobian execution corpus. No independent signed PCC, measured absolute runtimes, paid EKS/Spot/GPU work, or end-to-end advantage is claimed.

Sources: [root crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [queue #3904](https://github.com/isogeny-labs/crypto/issues/3904), [cost frontier #4215](https://github.com/isogeny-labs/crypto/pull/4215), [consumer #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [GPU IC #4178](https://github.com/isogeny-labs/crypto/pull/4178), [CT178 #1706](https://github.com/isogeny-labs/cryptanalysis/pull/1706), [CT182 #1711](https://github.com/isogeny-labs/cryptanalysis/pull/1711). Research-KB and locked autoresearcher vault inaccessible; no novelty/absence claim. [pcc:unverified]

## Exact-head source CI readback

[Workflow #44087794086](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44087794086) at commit `b4ae69dcefe11ab88f110c2fc81a89981f00c4bc`, decoded job `134054692704`, **passed**: 8/8 Python tests normal, 8/8 under `-O`, Python syntax parse, original frozen Git blob and 48-row plan, exact 2,304-slot roster hash, normal/optimized plan comparison. No genuine native arithmetic or timed benchmark ran. Later source-documentation commits must be checked separately; no independent signed PCC has been issued. [pcc:unverified]
