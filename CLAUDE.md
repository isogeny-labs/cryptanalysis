## Authorized target scope

Work in this repository is limited to public benchmark instances, published
challenge curves, toy or synthetic parameters, and systems the owner operates
or is explicitly authorized to test. Do not develop or test operational
attacks against production keys, wallets, accounts, or third-party systems.
A task that requires a non-public target stops and asks for written
authorization before proceeding.

**Goal and first step** (AGENTS.md, "Goal: what to work on next" and "First
step of every task"): the SessionStart hook prints `tools/goal_brief.py` (the
pinned goal and items in `docs/ACTIVE.md`, then the newest session-log open
threads); with no other instruction, take the first unchecked item and start.
`/goal` re-reads the brief; `/goal <text>` pins a new goal. Before any other
work on a task, add its line to `docs/ACTIVE.md`, commit that alone, push and
open a **draft** PR; when the work is finished and checked, tick the line and
mark the PR ready for review.

A task's pull request opens as a **draft** as the task's first step, with its
line in `docs/ACTIVE.md` (owner, 2026-11-16), and is marked ready for review as
soon as the work is finished and checked, whatever the runtime defaults to.
This and the repository's other agent rules are in
[`AGENTS.md`](AGENTS.md) ("Track research work in pull requests").
# CLAUDE.md

**Success criterion** (owner, 2026-10-15): every verified, measured
improvement over the current index-calculus baseline is a success. Beating
Pollard rho is the long-term goal, reached iteratively, not by one
breakthrough. Report each row's gap to the matched rho as the distance
remaining, not as a pass/fail gate. Relabelling and accounting changes are
not improvements. Full rule: [`AGENTS.md`](AGENTS.md), "Success criterion:
iterative improvement of the index-calculus baseline".

**Sabotage is assumed** (owner, 2026-11-04): a result is cited by its pcc claim
id and standing (`[pcc:ID]`), or labelled `[pcc:unverified]` as an assertion.
CI runs `python3 tools/pcc/pcc.py canary` and `ledger verify`. Rule:
[`AGENTS.md`](AGENTS.md), "Sabotage is assumed: proof-carrying claims".

Read **[AGENTS.md](AGENTS.md)**: it is the contract for every runtime, Claude
Code included.

The session that opens a PR tracks it until it is merged or closed: it
subscribes to PR activity (or keeps spaced check-ins: about 50 minutes, then
about four hours, stopping after three quiet ones), fixes the failures its
change causes, and merges once green. Any model tier does this, Claude Opus
and Fable included. A non-required check queued for 24 hours without starting
does not block the merge. AGENTS.md, "Continue through the PR: track it and
merge it".

**Resume checkpoints** (owner, 2026-10-24): before any experiment run, fill
`.resume/RESUME.md` (`scripts/checkpoint.sh init`) so a fresh session could
resume the effort from it alone. The hooks push it to S3 with the specs,
leads and unpushed work, and refuse run launchers until that succeeds.
AGENTS.md, "Resume checkpoints in S3 before every run".

Look up curve facts and existing measurements in the lab's curve database
before computing them: MCP server `ecdb` (export `ECDB_TOKEN` from secret
`ecdb/api` first) or `scripts/ecdb.sh`. AGENTS.md, "Querying the curve
database (ecdb)".

**Knowledge base first.** The shared `research-kb` MCP server is the
cross-repository retrieval layer. Query it before a literature or lead claim,
a factor-base/solver choice, a novelty or "not tried" statement, or a subagent
handoff; read the best hits and record the `source_id`/`repo:path`. Canonical
procedure: the trunk skill `isogeny-labs/workspace:.agents/skills/research-kb/SKILL.md`
(loads as `research-kb` from a workspace checkout); fallback `scripts/research-kb`. AGENTS.md, "Shared knowledge
base"; lab contract §11.


**Benchmark records** (owner, 2026-11-04): every benchmark run leaves a
`bench.record/v1` record in Git (`python3 tools/benchrec.py init|run|add-raw|
metric|close`), its raw data in S3 by SHA-256, and a regenerated progress
report in `benchmarks/progress/`, in the same PR. The hooks refuse unrecorded
benchmark launchers and unrecorded pushes; the `bench-records` check fails
the PR. AGENTS.md, "Benchmark records: data in S3, metadata in Git, one
progress report"; [docs/benchmark-records.md](docs/benchmark-records.md).

## Persistent scientific research loop

Read and follow [AGENTS.md](AGENTS.md#persistent-scientific-research-loop).
That section governs hypothesis testing, recovery from obstacles, continued
iteration, checkpoints and evidence required before stopping in this runtime.
