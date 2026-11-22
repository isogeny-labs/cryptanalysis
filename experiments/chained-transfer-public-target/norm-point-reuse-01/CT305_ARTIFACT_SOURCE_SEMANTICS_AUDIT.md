# CT305 — historical vs current artifact-hydration source audit (2026-11-22)

**Scope:** Read-only audit of the CT304 native-replay pre-S3 blocker. **Scientific standing:** [pcc:unverified]. This is source analysis, not a hosted runtime test, successful S3 authentication, original fixture hydration, native ECDLP benchmark, or signed PCC.

## Source identities and reproducible comparison

Repository: `isogeny-labs/cryptanalysis`. Historical pinned commit: `3de8c174cf65e6b34bf8579d97b817b8f5dc2ded`. Compared exact GitHub file contents at that ref with the current `main` source, without changing either file.

| File | Historical pinned Git blob | Current main Git blob |
| --- | --- | --- |
| `.artifacts/config.json` | `2a9a2e9e679fb697c429597f5053ff55e264b90a` | `0ae263d334797b125ac31cc0af105699a8971145` |
| `tools/artifacts/artifacts.py` | `c49cd3de885c5b4292c283eb85e4327b872529ed` | `fb3c5cafcf97f93cab2d36bc109b32b71fa7cfba` |

The config retains the same S3 URI and all 58 original keep-list entries; current `main` appends a **redundant second `pcc/ledger.jsonl`** (59 entries). The tool changes are substantive (733 vs 937 lines; a line-based longest-common-subsequence diff found 27 change hunks, 232 additions and 28 removals). All the behavioral assertions below were checked against the fetched source bodies, not guessed from filenames.

A read-only reproduction in a complete repository checkout:

```sh
git cat-file -p 3de8c174cf65e6b34bf8579d97b817b8f5dc2ded:.artifacts/config.json > /tmp/ct305-pinned-config.json
git cat-file -p 3de8c174cf65e6b34bf8579d97b817b8f5dc2ded:tools/artifacts/artifacts.py > /tmp/ct305-pinned-artifacts.py
git show main:.artifacts/config.json > /tmp/ct305-current-config.json
git show main:tools/artifacts/artifacts.py > /tmp/ct305-current-artifacts.py
git diff --no-index /tmp/ct305-pinned-artifacts.py /tmp/ct305-current-artifacts.py || test "$?" -eq 1
git diff --no-index /tmp/ct305-pinned-config.json /tmp/ct305-current-config.json || test "$?" -eq 1
```

## Source-based compatibility findings

1. **Remote-source default changed.** Historical `cmd_pull` always constructs `Remote(cfg)` and calls `ensure_cached(..., remote, ...)` for absent local objects. Current `cmd_pull` computes `from_git = source == "git" or (source == "auto" and cfg.remote.startswith("s3://"))`, then chooses `GitHistory` when true. The current parser defaults `--source` to `ARTIFACTS_PULL_SOURCE` or `auto`. Therefore a default pull with this S3 config uses local verified cache, recovery bundles and Git history **without S3 reads** for missing local files, not the historical remote-only recovery path.
2. **Explicit remote is necessary but not sufficient for S3 execution evidence.** The new option `--source remote` chooses `Remote(cfg)` if a download is needed. However `cmd_pull` skips existing files with verified hash and length, and `ensure_cached` accepts an existing verified cache hit. Consequently the flag alone does not certify that any remote request occurred, although manifest SHA-256/length consistency remains checked on the normal path. `--fast` additionally trusts a present file's size; that option must not be admitted to custody evidence.
3. **S3 API changed.** Historical `Remote.get_args` invokes high-level `aws s3 cp`; current source uses `aws s3api get-object` with differentiated error diagnosis. Both have hash/size validation before publication through `ensure_cached`. This is operationally material to pinned AWS CLI/permissions and must be tested on the approved remote, not declared equivalent from a source diff.
4. **Ownership/validation semantics also changed.** Current `cmd_pull` protects index-tracked paths from stale manifest hydration, adds portable Unicode/case collision handling, and current manifest validation rejects additional malformed entries/symlinks. Blind replacement with the old tool would lose those protections in the affected branch; a config-only edit does not solve the tool mismatch.
5. **Already-preserved CI failure is a precondition failure, not S3 evidence.** [Original run 45000602416](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45000602416) and [fixed-chain run 45000602417](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45000602417) stopped at the first byte `cmp` before the second `cmp` or a storage request. The separate older [CT245 model-access problem](../../../problems/chained-transfer-ct245-model-artifact-headobject-access.md) records `invalid_token`/HTTP 403, but neither failure proves an ECDLP arithmetic defect.

### Decision boundary / owner-reviewed reconciliation

Do **not** delete the duplicate and call parity restored; do **not** upgrade historical pins automatically; do **not** remove either `cmp`, change S3 credentials/policy, substitute historical artifacts, or alter the immutable six-object manifests.

The responsible artifact-tools and custody owners should first approve one coherent exact tool+config source pair, record its Git blobs, and specify whether the required test proves **remote S3 custody** or merely **SHA-bound recovery from authorized Git history**. For the former, require a read-only explicit remote-source attempt on an approved isolated empty artifact cache, unmodified source manifests, exact six-object SHA-256/length checks, retained request/status receipts with secrets redacted, a negative wrong-digest control, and a separately authenticated STS identity. A successful hydrated-file hash on its own is not proof of remote access or independently signed execution. An alternate authorized recovery method must be labeled distinctly and must not be silently promoted to an S3 hydration result.

Only after this gate and the existing STS/S3 permissions are resolved may the existing budget-authorized native Rust 695/701 original+reuse run execute. Measure independently priced `C169/C13a/C13b/D/N2_actual`, A/A and ABBA paired cold complete single-target costs including setup, transfer, relation collection, linear algebra, recovery, verification and peak memory against strongest retained lift / optimized rho / BSGS / frontier IC. Require independently reproduced matching verified outputs, uncertainty, and signed PCC before an advantage claim.

## Limitations

The audit inspected current and historical *source code*, not actual AWS responses, a full native-build CI environment, live artifact bytes, model correctness, or cryptanalytic performance. It is a narrow implementation/custody finding. The original EKS Spot/budget STOP is unchanged. **[pcc:unverified].**
