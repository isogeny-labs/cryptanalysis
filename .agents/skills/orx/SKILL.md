---
name: orx
description: Use OpenResearch in this repository to search literature, inspect projects and experiment evidence, and work with its local dashboard and CLI.
---

# OpenResearch

Read the repository's `AGENTS.md` first. This adapter supplies tool mechanics;
repository instructions and the lab contract remain authoritative for research
routing, roles, compute, budgets, evidence, checkpoints and publication.

Run `bash scripts/openresearch.sh skill` at the start of an OpenResearch task
to load the installed CLI's current manual. Load a relevant module with
`bash scripts/openresearch.sh skill <module>` rather than copying its contents.

Use `bash scripts/openresearch.sh doctor` to inspect the local installation.
If absent, run `bash scripts/openresearch.sh setup`. The pinned release,
dashboard import steps and local storage locations are in
`docs/openresearch.md`.

Use OpenResearch for literature retrieval and local evidence navigation.
Before launching experiments, follow the repository's existing execution route;
an OpenResearch project or experiment node is not approval or a replacement for
the lab's run records, validation or archival process. Preserve the fixed run
contract and immutable answered nodes described by the bundled manual.
