# CT141 — admission-gated original-prime native primitive execution protocol

Date: 2026-11-15. Scientific standing: [pcc:unverified]. Parent: cryptanalysis #1549 (CT137), which is stacked on #1534. Root: crypto #3877; selected-call control #4215; consumer #1523; GPU IC baseline #4178.

## Question, negative controls, and scope

The previously completed CT137 CI **compiled** both distinct Rust 1.99.1 graphs, but did not link or execute either. This follow-on supplies an executable, **manual-only**, bounded path to native CT126 original and CT125 norm-point-reuse pricing. It does not substitute another curve or manufactured prices. Before treating a native result as evidence, run the unchanged `check_pair.py` auditor in both normal and `python -O`, enforce ABBA across four separate native process executions, and inspect each output and failure. The inherited five public scalar fixtures establish a **small deterministic primitive-price diagnostic** only; they do **not** reproduce all 695/701 Jacobian records or solve any discrete logarithm.

The intended cost question is whether `C169 - (C13_first + C13_second)` has a reproducible positive sign, and how that relates to separately measured target doubling `D`, direct and retained warm map cost and setup. The symbolic 48-row result in crypto #4215 is the prospective comparator, not a substitute for timing. The direct, two-hop and retained maps must produce identical canonical public outputs for each tested fixture. Any failure, A/A instability, or nonpositive price advantage is an explicit non-win.

## Frozen sources and execution order

* Branch derived from exact CT137 head `b6dc3a21a8db4fee01560c3d3dd32d2409d1605d`. Restore root crypto at **exact** `4de29a113dfc1b9d32c1809820b8caa2975042a8` (not today's moving #3877), require original evaluator Git blob `8016634385d76207b23a3eb3a4dae9b0366ac68d`, and run the three original predecessor materializers, followed by the original seven-section materializer and guarded CT125 derivative. Hash both generated Rust libraries before execution.
* Restore both immutable `nondual-models-18` compressed fixtures from their approved artifact vault with original fixed SHA-256 and byte-count guards. Never log credentials.
* Pin Rust 1.99.1 and the exact CT137 `Cargo.toml`, main Rust source and `check_pair.py` inherited from this branch. Build the original/reuse native `--release` binaries **once each**, then run those exact binaries (never four separate Cargo rebuilds).
* Run four distinct child processes in the fixed `original-1, reuse-1, reuse-2, original-2` order. Each child has an absolute 480 s timeout, 2 GiB virtual-memory limit, and externally measured full process elapsed time and max resident memory. Save its raw stdout, stderr, external resource receipt, SHA-256, exit status, and binary SHA-256. Do not overwrite a prior output directory. Stop after any failed child; retain prior outputs and mark the failure.
* Only after all four pass, run unchanged `check_pair.py` with both `python3 -S` and `python3 -O -S` on *separate copies* of the captured data; compare exact diagnostic JSON. Run `--self-test` under both interpreters (its eight sabotage mutations must fail). Record independent SHA-256s of audit output.
* A positively evaluated **manual** admission token must be supplied for actual execution. No `push` or `pull_request` event may run pricing. No EKS, Spot, GPU or cloud cluster is launched. This workflow is a launch path only, not authorization to spend; owner/budget approval remains separately required. All final research results remain [pcc:unverified] until a signed independent verdict.

## Abort and reporting

A source-hash mismatch, unresolved artifact, Rust link failure, failed map identity, wrong subgroup/group order, nonzero exit, timeout, memory breach, missing process receipt, failed A/A/ABBA validation, or audit discrepancy must fail closed, preserving raw artifacts under `if: always()`. Process-level timing includes cold binary startup and full `Runtime::construct`; the internal Rust `C169/C13/D` blocks are warmed arithmetic only, and each must retain its correct scope. Do not infer a 695/701 whole-record replay, a complete cold ECDLP advantage, or a cross-characteristic transfer.

## Remaining distinct acceptance gates

Native successful pricing must be joined to unchanged full original 695/701 parity (including all omission tests), matched stronger direct rho, BSGS, and index-calculus complete scalar recovery on the **same public instances**, all setup/transfer/linear-algebra and memory costs and source/target verification. Any batch or multi-target amortization must be excluded from the single-cold-target claim. Independently signed PCC and original repository review/CI/merge gates are unchanged.

Sources reviewed: pinned CT137 compile CI and decoded result (cryptanalysis #1549), CT126 `run_pair.sh` / `check_pair.py`, crypto #4215 selected-call cost frontier, cryptanalysis #1523 norm reuse and root #3877's newest relation-character diagnostics; BMSS08 (Bostan–Morain–Salvy–Schost, arXiv:cs/0609020). Research-KB MCP and the cross-repo autoresearcher lab-contract fetch were unavailable to this environment; no novelty or prior-art absence claim is made.

## Launch hardening addendum (no execution)

The workflow additionally requires a repository-owner-controlled Actions secret `CT141_OWNER_APPROVAL` with the exact intentional approval marker `CT141_NATIVE_CPU_APPROVED_20261115`, checked as the **first** step before checkout, vault hydration or Cargo. A dispatch menu selection by itself is not an owner/budget authorization. The approval secret is currently not asserted to exist, and must not be fabricated or silently defaulted. No native job has been requested. Source-only pull-request CI remains unaffected. [pcc:unverified]
