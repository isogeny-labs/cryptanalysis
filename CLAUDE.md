Open pull requests ready for review, never as drafts, whatever the runtime
defaults to, and mark an existing draft ready; only a user request in the task
makes a draft. This and the repository's other agent rules are in
[`AGENTS.md`](AGENTS.md) ("Track research work in pull requests").
# CLAUDE.md

**Success criterion** (owner, 2026-10-15): every verified, measured
improvement over the current index-calculus baseline is a success. Beating
Pollard rho is the long-term goal, reached iteratively, not by one
breakthrough. Report each row's gap to the matched rho as the distance
remaining, not as a pass/fail gate. Relabelling and accounting changes are
not improvements. Full rule: [`AGENTS.md`](AGENTS.md), "Success criterion:
iterative improvement of the index-calculus baseline".

Read **[AGENTS.md](AGENTS.md)**: it is the contract for every runtime, Claude
Code included.

The session that opens a PR tracks it until it is merged or closed: it
subscribes to PR activity (or keeps spaced check-ins: about 50 minutes, then
about four hours, stopping after three quiet ones), fixes the failures its
change causes, and merges once green. Any model tier does this, Claude Opus
and Fable included. A non-required check queued for 24 hours without starting
does not block the merge. AGENTS.md, "Continue through the PR: track it and
merge it".
