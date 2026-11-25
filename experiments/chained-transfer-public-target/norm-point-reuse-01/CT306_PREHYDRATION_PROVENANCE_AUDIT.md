# CT306 — CT200 prehydration can erase original S3 provenance (2026-11-22)

**Standing:** Source-only analysis, [pcc:unverified]. No remote request, native build, physical timing, ECDLP solve, or independently signed execution was performed. This is a conditional provenance finding, not a proof of any object compromise.

## Exact source references

Read directly from current `isogeny-labs/cryptanalysis/main` through the GitHub file connector, without editing them:

| Input | Git blob |
| --- | --- |
| `.github/workflows/ct200-public48-native-typecheck.yml` | `6edea0f521f5ff99ed4c4d995b350dcd6b74126d` |
| `.github/workflows/ct245-primitive-native-typecheck.yml` | `5e27d9163218788a1534ced5e05d56777861f079` |
| Current `tools/artifacts/artifacts.py` | `fb3c5cafcf97f93cab2d36bc109b32b71fa7cfba` |
| Original pinned `tools/artifacts/artifacts.py` at `3de8c174cf65e6b34bf8579d97b817b8f5dc2ded` | `c49cd3de885c5b4292c283eb85e4327b872529ed` |

## Observed source path (specific to CT200)

1. CT200 has an **earlier** step named `Pull store data this workflow reads (tools/artifacts)` executing current `tools/artifacts/artifacts.py pull --jobs 16 docs/research-artifacts/chained-transfer/nondual-models-18 experiments/chained-transfer-public-target`. No explicit `--source` is provided.
2. In the current tool, the default pull source is `ARTIFACTS_PULL_SOURCE` or `auto`; for a configured `s3://` remote, `auto` selects `GitHistory`, **not** `Remote(cfg)`, for missing local data. The old pinned tool has no analogous automatic Git-history source selector.
3. CT200 later calls the historical pinned tool to `pull --jobs 2 docs/research-artifacts/chained-transfer/nondual-models-18`, the **same model directory** targeted earlier. The current tool can already have materialized those files, and the cache is shared by default. The historical tool's pull path can accept verified existing files / verified cache hits without an S3 GET.
4. Thus even a later successful historic-tool pull and model SHA/size check **does not prove** the six objects were fetched from S3 in that execution. If the early Git-history recovery cannot supply an object, the workflow may fail before the historical step. This is a provenance gap, not proof that wrong bytes were accepted: the content hashes still matter.
5. The current CT245 workflow gives a better strict-source design: pinned historical tool/config hashes and exact policy comparison, redacted STS identity check **before** the pinned model pull, and no earlier `artifacts.py pull` step. Its live authorization and complete source-custody gates have not passed; the CT245 `invalid_token` / S3 403 blocker remains separate.

A source-level programmatic recheck of the four exact blobs confirmed nine expected conditions, including two CT200 calls to the same directory, default `auto`→GitHistory, cache short-circuit, old-source difference, and CT245's STS-first structure. This is not a hosted runtime trace or signed independent audit.

## Fail-closed remedy to request from the workflow / artifact owners

Before changing CT200 or claiming native custody, explicitly decide whether the job is intended to demonstrate **S3 remote custody** or only **SHA-bound recovery of files**. If S3 evidence is required:

- Reject or separate any prehydration of the six model objects before the authenticated pull. The first current-tool `pull` for the same directory must not remain in front of the original S3 evidence step.
- Keep immutable exact historical tool + configuration identities, CT245-style semantic configuration comparison where expressly approved, an authenticated STS preflight and bounded read-only remote access. Do not replace or silently advance the original pins.
- Run the approved original-tool model retrieval from an isolated empty cache with previously hydrated target files absent. Check each of the **six** manifest SHA-256 digests and exact lengths. Preserve redacted source selection, operation/remote status and failure receipts; avoid `--fast`.
- Fail the exercise if model files or cache are prepopulated (including the wrong-source positive control), if STS is invalid, if the requested remote cannot be contacted, or if any digest/length differs. Run a separate SHA-bound Git-history recovery control and ensure it is labelled as **Git**, never **S3**.
- After a successful custody gate, still require original/optimized 695/701 Rust parity, same-host C169/C13a/C13b/D/N2_actual and complete cold single-target ECDLP comparison against strongest retained-lift/rho/BSGS/frontier IC, all phases and peak memory charged, independent PCC and review. Do not launch EKS Spot or any unauthorized compute.

No production workflow was edited during CT306. The correct owner-reviewed remedy is not established until the source/custody authority and credential owner approve and execute it.

## Reproducible source inspection

In a complete checkout of `isogeny-labs/cryptanalysis`:

```sh
git show main:.github/workflows/ct200-public48-native-typecheck.yml | grep -n -E 'Pull store data|Restore exact original|artifacts.py pull'
git show main:.github/workflows/ct245-primitive-native-typecheck.yml | grep -n -E 'sts get-caller-identity|_ct245_artifact_tools/tools/artifacts/artifacts.py pull'
git show main:tools/artifacts/artifacts.py | grep -n -E 'ARTIFACTS_PULL_SOURCE|from_git|if c.exists\(\)'
git show 3de8c174cf65e6b34bf8579d97b817b8f5dc2ded:tools/artifacts/artifacts.py | grep -n 'def cmd_pull'
```

**Do not treat grep alone as execution verification.** Review the full control-flow and use a bounded authorized remote test before any custody or performance claim. Existing CT304/CT305 and CT245 problem records remain open. [pcc:unverified].
