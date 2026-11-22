# CT307 — pre-registered source-only hydration-order regression guard (2026-11-22)

**Status:** prospective source/CI methodology; [pcc:unverified]. This does not run AWS, S3, Rust, ECDLP, PCC or paid compute.

## Owner's target and prior evidence
The goal remains a fully charged single-target ECDLP comparison using the **original, authenticated** 695/701 model fixture, matched 48-vector routes, 144 epoch samples and independently verified cold timing. CT302/CT304 in draft [#1912](https://github.com/isogeny-labs/cryptanalysis/pull/1912) establish source-level population/receipt guards. [CT305](CT305_ARTIFACT_SOURCE_SEMANTICS_AUDIT.md) established that current artifacts.py defaults to Git-history for S3-configured stores; [CT306](CT306_PREHYDRATION_PROVENANCE_AUDIT.md) established a specific earlier CT200 pull of the model directory before its historical pinned-tool pull. The existing CT245 workflow instead places an STS gate before its historical-tool pull. Those are the primary prior source reports; this task does not propose a new algorithm or assert novelty. BMSS08's isogeny algorithms and CT198/#1748 norm-route accounting are retained prior mechanisms, with no new computational speedup inferred.

The shared research-KB MCP interface is not loaded in this connector runtime; local `scripts/research-kb` cannot access the checked-out catalog here. Repository source reports and live GitHub PRs are the fallback, not an exhaustive prior-art search. The crypto-autoresearcher `AGENTS.md` content fetch returns a UTF-8 decode error; do not infer its contents.

## Hypothesis / source-check contract
A **read-only structural scan** of these two live workflows should classify:
1. `.github/workflows/ct200-public48-native-typecheck.yml`: **known prehydration hazard**, because an earlier `tools/artifacts/artifacts.py pull` includes `docs/research-artifacts/chained-transfer/nondual-models-18` before the historical pinned-model pull.
2. `.github/workflows/ct245-primitive-native-typecheck.yml`: **STS-first / no observed earlier literal model pull**, because the historical tool call follows `sts get-caller-identity` and fail-closed `exit 42` in the same step.
3. Both lanes must retain exact historical ref `3de8c174cf65e6b34bf8579d97b817b8f5dc2ded` and tool Git blob `c49cd3de885c5b4292c283eb85e4327b872529ed`. Unrecognized ordering, missing pinned pull, missing tokens, or a newly inserted prefetch in CT245 must **fail closed**, not return clean.
4. The audit must never claim that remote S3 was contacted, that six originals were hydrated, or that native benchmarks ran. Text scans cannot exclude aliases, shell scripts or dynamically constructed commands; an owner-reviewed source/control-flow inspection and real independent custody receipt remain necessary.

## Preregistered validation
Add a standard-library Python scanner, with two synthetic positive classifications and at least eight synthetic adversarial mutations (injected CT245 prefetch, missing STS, weakened fail, source pin/blob changes, suppressed CT200 prefetch, missing pinned pull, changed protected path). Run normal and `python3 -O -S` self-tests and run against **both real workflow files** in exact-head source-only CI; fail on unexpected classifications.

The real CT200 hazard is intentionally a passing *detection*, not a passing custody result. CT245 structural ordering is not authenticated remote execution. Do not mutate CT200/CT245, artifact manifests, credentials, cache, original source pins, PCC ledger or paid-compute gates to satisfy this check.

## Exit criteria / next work
An accepted source-only regression check closes only the missing automated warning; it does not close the [CT304 source-parity problem](../../../problems/chained-transfer-ct304-artifact-tool-parity.md), [CT245 STS/S3 access problem](../../../problems/chained-transfer-ct245-model-artifact-headobject-access.md), or runtime attestation. The artifact/custody owner must approve coherent pinned tool+config and intended remote-vs-Git provenance. A genuinely remote six-object trial requires isolated fresh cache, no prehydrated targets, redacted STS acceptance, six SHA256/length checks, and independent read receipts before exact-source native 695/701 replay, paired C169/C13a/C13b/D/N2_actual pricing, cold complete-solve rho/BSGS/frontier IC baselines, memory, uncertainty and independent PCC. No unapproved EKS/Spot job or protected merge.

## CT307 input-custody amendment after first hosted attempt

The initial hosted source-only [run #45014598439](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45014598439) completed **failure**: two synthetic positive and eight mutations passed, but `ct200-public48-native-typecheck.yml` was absent from the PR's sparse branch. Exact GitHub file reads confirmed CT200 is absent there, while CT245 is present and both original workflow blobs are present at the known PR base commit `e89b9db54d358d3a2749acf6d5277b0300bc3ba2`. This is a source input/branch coverage error, not a scientific or S3 credential finding.

The source-only workflow now separately checks out that **immutable base commit** with just the two workflow paths, verifies their exact Git blobs (`6edea0f521f5ff99ed4c4d995b350dcd6b74126d` for CT200 and `5e27d9163218788a1534ced5e05d56777861f079` for CT245), and runs the identical scanner in normal and optimized modes on those exact inputs. No missing workflow is synthesized, copied into the research branch or presented as an updated current-main snapshot. The source audit still only classifies the pinned historical workflow pair, not active S3 retrieval or native execution. New exact-head CI must pass independently. [pcc:unverified].
