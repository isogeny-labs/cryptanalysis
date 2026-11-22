# Cryptanalysis Git remote rejects PR branch push

- **Status:** `resolved` for Git transport; hosted PR validation remains separate
- **Kind:** access/tool limit; the cause is unknown
- **Affected work:** [Lean evidence audit and 93-file local replay](../reports/lean-evidence-audit-20261021/report.md), branch `codex/cryptanalysis-proof-audit-20261021` (initial audit commit `a9d2addf364fc604f56cf005a2711248c29e1e9d`)
- **Next action owner:** this task for the ready PR; hosted CI and review for the PR owner
- **Last updated:** 2026-10-22

## Problem

Git smart HTTP returned HTTP 403 with “Your repository is disabled” on October
21, preventing publication of the committed Lean audit. The reason was not
established. Read and write access returned on October 22, and the audit
branch was pushed; this access obstruction is resolved.

## Evidence and uncertainty

- **Observed:** `git push origin HEAD:refs/heads/codex/cryptanalysis-proof-audit-20261021`
  from local commit `a9d2addf364fc604f56cf005a2711248c29e1e9d` failed with
  `remote: Your repository is disabled` and HTTP 403 on 2026-10-21. A separate
  `git ls-remote origin refs/heads/main` received the same response. The
  GitHub REST repository read still succeeded and returned `disabled: false`.
  The local audit script, report, diagram, and PDF remain committed in the
  isolated worktree; a subsequent local replay compiled all 93 tracked Lean
  files and is recorded in the same branch.
- **Derived or proved:** no theorem or repository-policy conclusion follows
  from the HTTP response.
- **Suspected explanation:** unknown. The Git smart HTTP response and REST
  metadata disagree; this record does not infer an account, abuse, size, or
  branch-protection cause.
- **Recovery observed:** `git ls-remote origin refs/heads/main` returned
  `7bcc0bf05f51132e74637657275420f1e71f72ff` on October 22. After
  integrating that main, `git push origin
  HEAD:refs/heads/codex/cryptanalysis-proof-audit-20261021` succeeded from
  merge commit `94a38d8b26931e4f9cbcd223ef6a6a2fba864bb9`. This proves
  Git read/write access to that branch was restored; the cause and duration
  of the earlier 403 remain unknown.
- **What this evidence does not establish:** why access failed earlier, or
  that the audit passed hosted CI, review, or semantic proof obligations.

## What would unblock it

- [x] `git ls-remote origin refs/heads/main` succeeds without the disabled
  response, and the audit branch is pushed.
- [ ] A ready pull request and its hosted checks and review complete under
  the repository's PR rules. This is a separate delivery and validation gate.

The restored delivery path does not validate the theorems or the audit's
scientific claims. The PR and its checks remain separate obligations.

## Next action

Open the ready PR from the published branch. Its hosted checks, review, and
any merge decision must use that PR's exact head. Preserve this record as the
historical 403 and recovery evidence; a future access failure is a new
observation, not a reason to infer a mathematical defect.
