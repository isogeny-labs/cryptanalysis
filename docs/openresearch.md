# OpenResearch

This repository includes a thin integration with
[alphaXiv OpenResearch](https://github.com/alphaXiv/OpenResearch), pinned to
[v0.2.27](https://github.com/alphaXiv/OpenResearch/releases/tag/v0.2.27).
It provides a local dashboard, literature retrieval and experiment navigation
with Codex and other supported agents.

## Set up

On macOS or Linux, from this checkout:

```sh
bash scripts/openresearch.sh setup
bash scripts/openresearch.sh doctor
bash scripts/openresearch.sh up
```

Setup downloads the official versioned installer, checks its pinned SHA-256,
and lets that installer check the platform archive. The default install is
`~/.local/bin/orx`; shell profiles are not changed. The wrapper finds it even
when that directory is absent from `PATH`. An existing CLI with another version
is left in place and reported; use `OPENRESEARCH_BIN=/absolute/path/to/orx`
to select another installation. `OPENRESEARCH_PREFIX` selects an install prefix.
Anonymous analytics and agent feedback are disabled by setup.

The repository-local `orx` skill is discoverable through both
`.agents/skills/orx/` (Codex/OpenCode) and `.claude/skills/orx/` (Claude Code).
There is one canonical body; the other surface is a relative symlink.
To also install the upstream global Codex shim, optionally run:

```sh
bash scripts/openresearch.sh install-skills --agent codex
```

## Connect this checkout

Open `http://127.0.0.1:4791` on the machine running the CLI. Add a project,
choose the existing-folder option and select this checkout. Use Codex as the
agent when its CLI and authentication are available. A cloud workspace's
loopback URL belongs to that workspace; use its private preview or an SSH
tunnel to access it from another computer. Keep the default loopback binding.

Local project commands and literature retrieval do not require an OpenResearch
account. Managed OpenResearch compute requires `orx login`; agent credentials
are separate. Setup performs no login, experiment run or repository publication.

```sh
bash scripts/openresearch.sh skill
bash scripts/openresearch.sh skill lit-review
bash scripts/openresearch.sh projects --json
bash scripts/openresearch.sh discover keyword 'isogeny cryptanalysis'
```

The authoritative CLI guide is bundled in `orx skill`. Repository `AGENTS.md`
and `docs/lab-contract.md`, where present, control research routing, compute,
budgets, checkpoint custody, evidence and publication. OpenResearch's default
local compute setting does not change the lab's established execution route.
Importing a project does not qualify or promote any scientific result.

OpenResearch stores its local database, settings and projects under
`~/.config/openresearch` by default. Treat that data and an unlocked working
tree as local plaintext. For a vaulted repository, unlock with its existing
vault tooling before using OpenResearch; commits must still pass through the
required vault filter. Do not place credentials or exported research bundles
in Git, and publish or share a project only when requested.

## Check the integration

```sh
bash scripts/test-openresearch.sh
```

These checks cover shell syntax, argument forwarding from another working
directory, an existing CLI version mismatch and rejection of a modified
installer. They do not launch research or assert agent authentication.

Sources: upstream README, `SKILL.md`, `src/commands/install_skills.rs` and
v0.2.27 release metadata (reviewed 2026-11-16). To change the pin, review the
release, update both the version and installer digest, then rerun these checks.
