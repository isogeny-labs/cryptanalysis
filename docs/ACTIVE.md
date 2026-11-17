# Active goal and items

Owner-pinned work queue. `tools/goal_brief.py` prints this file at the start
of every Claude and Codex session (SessionStart hooks) and for `/goal`
(AGENTS.md, "Goal: what to work on next"). When this file has no unchecked
item, sessions fall back to the newest "Open threads" in `docs/session-logs/`.

Keep it short: one goal, a few ordered items. Sessions add their task here as
the first step of the task (AGENTS.md, "First step of every task"), keep the
line current, and tick it when done; history belongs in the session log or the
PR, not in this file.

## Current goal

_(none pinned — set one with `/goal <text>`)_

## Active items (top = next)

- [ ] CT181 expose and eliminate positional confounding in proposed cold transfer panel (automation, started 2026-11-17, branch research/ct181-counterbalanced-cold-design-20261117, PR #1711)
- [ ] CT180 reject impossible cold-process nested-time records (automation, started 2026-11-17, branch research/ct180-nested-cold-time-consistency-20261117, PR #1710)
- [x] CT179 validate and adjudicate the frozen cold transfer panel without treating transfer timing as a complete solve (automation, started 2026-11-17, branch research/ct179-cold-panel-adjudication-20261117, PR #1708; source-only 9/9 normal and -O CI #44050792557, native timing pending)

<!-- One line per task, added as the task's first step with its draft PR:
- [ ] <task> (<runtime>, started YYYY-MM-DD, branch <branch>, PR #<n>) -->

## Blocked / questions for the owner
