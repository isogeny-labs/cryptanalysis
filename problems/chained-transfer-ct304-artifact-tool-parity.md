# CT304 pinned artifact-tool parity blocks native replay before S3

- **Status:** `open`
- **Kind:** implementation/tool source drift; separate downstream credential access limit remains open
- **Affected work:** [norm-reuse gate draft #1912](https://github.com/isogeny-labs/cryptanalysis/pull/1912), [original evaluator CI](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45000602416), [fixed-chain CI](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45000602417), [CT245 access obstruction](chained-transfer-ct245-model-artifact-headobject-access.md)
- **Next action owner:** shared artifact-tools maintainer and immutable-input custody reviewer; cryptanalysis native run owner only after a source parity remedy is approved
- **Last updated:** 2026-11-22 UTC
- **Scientific standing:** [pcc:unverified]

## Problem

Current exact-head native original/fixed-chain replay workflows fail the byte-identical historical artifact-tool comparison *before the first S3 attempt*. As a result, the original six manifest-pinned models cannot be authenticated by those workflows, native Rust 1.99.1 695/701 replay remains unrun, and physical `C169/C13a/C13b/D/N2_actual` / complete single-target ECDLP costs are unavailable.

These workflows sparse-checkout pinned `isogeny-labs/cryptanalysis` commit `3de8c174cf65e6b34bf8579d97b817b8f5dc2ded` into `artifact-tools` and run both:
```sh
cmp ../artifact-tools/.artifacts/config.json .artifacts/config.json
cmp ../artifact-tools/tools/artifacts/artifacts.py tools/artifacts/artifacts.py
```
The first `cmp` fails, so the second comparison and S3 requests are never executed. An earlier separate CT245 workflow observed `STS=invalid_token`, but **that observation is not the failure cause for these two newer jobs**.

## Evidence and uncertainty

- **Observed CI:** [#45000602416](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45000602416), failed job `137141079646`, and [#45000602417](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45000602417), failed job `137141079812`, both on 2026-11-22 UTC. Logs show `.artifacts/config.json differ: byte 4000, line 63`, with exit code 1 before AWS/S3.
- **Exact configuration source identity:** pinned Git blob `2a9a2e9e679fb697c429597f5053ff55e264b90a` vs current branch and `main` Git blob `0ae263d334797b125ac31cc0af105699a8971145`. Parsed `policy.keep` arrays have 58 vs 59 entries; the only added element is a redundant trailing second `pcc/ledger.jsonl`. No entries were removed. The pinned and current configuration lengths are 4,012 and 4,038 bytes.
- **Second guard also diverges:** pinned `tools/artifacts/artifacts.py` blob `c49cd3de885c5b4292c283eb85e4327b872529ed` (30,699 bytes) vs current `fb3c5cafcf97f93cab2d36bc109b32b71fa7cfba` (42,335 bytes). The specific tool semantic changes have **not** been exhaustively adjudicated; a config-only edit cannot restore this second check.
- **Derived or proved:** only the exact byte-source mismatch and the recorded pre-S3 short circuit. No novel ECDLP theorem, tool security equivalence proof, native arithmetic failure or complete-cost result is established.
- **Unknowns:** whether the pinned 2026 source remains safe/authorized relative to the current tool, and whether approved new tool/version pins have been issued by the artifact owner. Do not infer equivalence of two different scripts from a shared filename.
- **What this does not establish:** access to all six S3 objects, valid STS credentials, valid physical primitive prices, complete-solver superiority, independent execution or PCC standing.

## What would unblock it

- [ ] The responsible artifact-tools owner selects and records an explicitly approved coherent **tool + configuration** revision with exact SHA/git-blob identifiers and a review of security and custody semantics; no uncontrolled pin advance, duplicate removal alone, or skipped `cmp` allowed.
- [ ] New exact-head read-only CI with that approved coherent pair passes both source comparisons, followed by the unchanged manifest SHA-256/length checks for all six original content-addressed objects. Capture both success and failure receipts.
- [ ] Separately resolve the CT245 STS/S3 permission failure using approved credentials/role, *without printing secrets* or weakening policy.

The first condition repairs only source identity. Even satisfying all three unblocks model hydration/typechecking, not native timing, ECDLP cost advantage or independently signed PCC.

## Next discriminating step

- **Action:** have the shared artifact-tools owner compare the pinned `3de8c174` source against the current full tool revision, determine allowed migration of exact-tool and exact-config pins, and register the chosen pair *before* any write.
- **Inputs/controls:** immutable original six-object manifests, current/pinned Git blobs above, two preserved failed CI logs, original working CT137 historical hydration receipt, matching read-only source-only CT244 pass as a non-native positive control.
- **Limits/stop:** offline diff and bounded source-only CI until approved tool and credential owner signs off. Do not launch EKS Spot, install an unpinned tool, modify the original model, skip source comparisons, or rechain the PCC ledger.
- **Outcomes:** approved source-equivalent pair allows unchanged six-object hydration trial; incompatible semantics require explicit migration/independent custody review; failed STS after tool-parity recovery remains a separate CT245 blocker.
- **Recheck trigger:** approved artifact-tools owner decision, updated exact-head native workflow or restored STS.

## Resolution and history

2026-11-22: discovered via exact-head CT304 follow-up. The two failures and byte identities are retained; no source parity repair, credential change, native ECDLP run or independent PCC claimed. **Unresolved. [pcc:unverified]**


## CT305 source-semantics audit — 2026-11-22

The exact historical/current source comparison identified an **additional migration hazard**, separate from the pre-S3 `cmp` failure: current `artifacts.py pull` defaults to `GitHistory` for S3-configured repositories (`--source auto`) whereas historical `pull` uses `Remote(cfg)`. Current `--source remote` restores remote selection **only when a download is necessary**; already-hydrated files and verified cache entries can suppress remote reads. Current S3 client changed from `aws s3 cp` to `aws s3api get-object`, and tracked-path/manifest validation was tightened. A new pin cannot be inferred to certify original S3 access simply because materialization succeeds. Source comparison supports this conclusion; no hosted S3 experiment occurred.

Full immutable source identities, 27-hunk source audit, exact fallback selection, impact, and owner-reviewed decision gates: [CT305 audit](../experiments/chained-transfer-public-target/norm-point-reuse-01/CT305_ARTIFACT_SOURCE_SEMANTICS_AUDIT.md) (GitHub commit `e8bf9eff5e3850d8ff382e71a6e19dd7bdb3dc55`). **Reconciliation now also requires explicit owner selection of remote-S3 custody versus separately labeled SHA-bound Git recovery.** For remote evidence, mandate isolated empty cache, explicit remote selection, original six-object manifest checks and remote/status receipts before allowing native timing. This is not authority to waive pin comparisons or modify shared tool/source. Existing STS 403, budget STOP and PCC gates remain. [pcc:unverified].


## CT306 — CT200 existing-workflow prehydration provenance gap (2026-11-22)

Separate from the CT304 pre-S3 `cmp` failure, the already-existing `ct200-public48-native-typecheck.yml` prehydrates `docs/research-artifacts/chained-transfer/nondual-models-18` with the **current** artifact tool before its later **historical pinned** tool's pull of that same directory. Because current S3-default `--source auto` uses Git-history recovery, a success at the later historical pull might be a local-file/cache hit with **no S3 GET at all**. Source inspection confirmed this overlap and the cache-hit path; it did **not** show successful remote access, modified object bytes, or an ECDLP issue. The CT245 native typecheck already pins its historical tool, checks STS before retrieval and avoids that initial prefetch, but its STS/S3 authentication still fails.

See the [CT306 exact-source control-flow audit](../experiments/chained-transfer-public-target/norm-point-reuse-01/CT306_PREHYDRATION_PROVENANCE_AUDIT.md) at GitHub commit `a74b140af92a22d8b4ba6e48517788af49274ef2`. Before calling a remote-custody replay validated, require owner approval of explicit remote-vs-Git evidence semantics, no prehydrated model files, isolated empty cache, authenticated STS, immutable original six-manifest hashes/lengths and retained operation/remote status receipts. **Do not edit shared workflows or weaken pins unilaterally.** CT304 original tool parity and CT245 access blockers remain open. [pcc:unverified].

## CT307 regression guard — 2026-11-22

[CT307 protocol](../experiments/chained-transfer-public-target/norm-point-reuse-01/CT307_HYDRATION_ORDER_GUARD_PROTOCOL.md), [source scanner](../experiments/chained-transfer-public-target/norm-point-reuse-01/ct307_hydration_order_audit.py) and [new source-only workflow](../.github/workflows/ct307-hydration-order-audit.yml) now preserve **automated detection** of the CT200 earlier pull of the protected six-model directory and the distinct CT245 STS-first literal source ordering, without modifying those workflows.

The initial source-only [run #45014598439](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45014598439) failed because the CT200 workflow is absent from this draft's sparse branch despite being present on the exact base. The source-only workflow now uses a separate read-only checkout at commit `e89b9db54d358d3a2749acf6d5277b0300bc3ba2` and verifies the pinned CT200/CT245 workflow blobs. [Run #45014696853](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45014696853), job `137184394980`, completed success at source `f957a252`: both Python modes passed two synthetic positives/eight mutations, independently printing CT200=`known_pre_hydration_hazard`, CT245=`sts_first_no_observed_literal_prefetch`. **This is a source-only warning/ordering check, not remote retrieval, credential validation, a repair of the pre-S3 parity block, or model execution.** It does not close this problem. [pcc:unverified].
