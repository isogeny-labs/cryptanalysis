# Curve25519 representation research: exploratory archive

**Status: draft archive import; artifact-store access blocked; all scientific assertions unverified.** This PR packages an earlier chat-produced research bundle. It does not complete the broader request to establish a better index-calculus algorithm. [pcc:unverified]

The source-produced report describes torsion invariants, Edwards/Montgomery/Weierstrass models, factor-base selection, low-degree isogenies, bounded integer lifts, and an Elligator check. Its reported toy outcomes are historical producer assertions, not independently signed results. [pcc:unverified]

## Read the material

- [Historical research note](original/README.md), preserved without rewriting its earlier language.
- [Editable nine-page report source](original/report.tex); build instructions below.
- [Coverage figure](figures/coverage.svg), [equation figure](figures/equations.svg), [field-structure figure](figures/field-structure.svg). These plots summarize producer-supplied data and are unverified. [pcc:unverified]
- [Source-access record](original/sources.json), [historical scope record](original/PROTOCOL.md), and [amendments](original/AMENDMENT.md).
- [Original file digests](original/SHA256SUMS), [pending-upload inventory](pending-artifacts.json), and [evidence-qualification problem](../../problems/curve25519-representation-evidence-qualification.md).

The original note/PDF and script fields such as `verified`, `passed`, or `status` are source data. Under the current PCC contract they do not establish verification. The current import status here overrides any stronger historical wording, including the earlier chat answer. [pcc:unverified]

## What is in this PR

Classification: **accounting and archival documentation**, not an algorithmic improvement. The original Python sources, TeX, small figure PDF assets, provenance and hashes are preserved; reviewable SVG copies remove trailing whitespace only, with both hashes in `figure-normalization.json`. No benchmark, curve/candidate registry, factor-base archive, isogeny graph, performance ranking, or shared verifier is promoted or modified. [pcc:unverified]

Raw outputs, the original rendered report and ZIP are excluded from Git and listed in `pending-artifacts.json`; no `.artifacts.json` was fabricated. The artifact client returned `HeadObject: 403 Forbidden`; the focused bucket check returned `GetBucketLocation: AllAccessDisabled`. Consequently this branch does **not** claim durable storage of those bytes. They remain available in the originating session's `/workspace/artifacts/curve25519-research-20261117/`. [pcc:unverified]

Archival statement record: `PCC-20261117-5c71b9`, standing `unverified`. [pcc:unverified]

## Evidence limitations

- The original scope notes are not frozen `experiment.protocol/v1` records or a certified export. This import is retrospective/exploratory and cannot repair preregistration after the data. [pcc:unverified]
- Original content-hash curve aliases do not satisfy the current complete EC1/UID metadata contract; registration is unresolved. No legacy label is silently reassigned. [pcc:unverified]
- The source reports toy recovery/census checks and a retained-system timeout. No signed independent scientific verdict or execution proof is present. [pcc:unverified]
- Production solver measurements, complete cost accounting, growing-size tests, faithful Lean formalization and source/curve registration remain open. The bounded checks are not evidence of security, impossibility, a cryptographic-size attack or a performance advantage. [pcc:unverified]

## Packaging checks and report build

From the repository root:

```sh
make -C research/curve25519-representations-20261117 check
make -C research/curve25519-representations-20261117 report
```

`check` audits archived file hashes, parses the Python sources without executing their experiment entrypoints, and checks the pending-upload inventory. It is an archive integrity self-check, not a scientific verifier. `report` typesets the historical report using committed figure assets into `.build/report.pdf`; it does not run a search, solver, benchmark or new experiment. The build needs pdfLaTeX/TikZ and `pdftotext`. [pcc:unverified]

Do not treat the historical reproduction recipes as authorization to bypass current protocol, checkpoint, execution, compute, PCC or storage rules. New or repeated scientific runs need their own current admission and frozen records. [pcc:unverified]

## Next action

Restore permitted read/write access to the lab artifact store, then use the unchanged `tools/artifacts/artifacts.py push` and remote verification flow for the pending inventory. Do not mark this archive fully delivered until its data and rendered PDF can be hydrated from real store manifests. Independent scientific review and a properly preregistered successor remain separate requirements. [pcc:unverified]
