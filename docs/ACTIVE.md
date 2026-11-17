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

- [ ] CT183 implement a v2 counterbalanced cold-process producer matched to CT182, with bounded capture and fail-closed source tests (automation, started 2026-11-17, branch research/ct183-v2-balanced-cold-producer-20261117; source-only, no native admission)

- [x] CT177 bound CT176 child output capture and prevent unbounded process memory while preserving raw evidence (automation, started 2026-11-17, branch research/ct177-bounded-process-capture-20261117, PR #1706; scoped source CI passed)
- [x] CT178 require explicit aggregate wall budget and refuse expired/incomplete 2,304-process panels (automation, started 2026-11-17, branch research/ct177-bounded-process-capture-20261117, PR #1706; 32/32 tests normal and optimized source CI #44042761162; no native run)

<!-- One line per task, added as the task's first step with its draft PR:
- [ ] <task> (<runtime>, started YYYY-MM-DD, branch <branch>, PR #<n>) -->

## Blocked / questions for the owner
