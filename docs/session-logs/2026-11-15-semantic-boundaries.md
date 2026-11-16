
## 2026-11-16T03:25Z - late PCC base race

### What was done
PR1609 merged as28d1c3b043481baad61aa7a84423586f56aaa1b7 while its PCC job still ran. Its ledger166 preserves every entry of first parent f885c90394f9addd6e71cd807da8cc28d03cb132. Main advanced to167 entries in5d4bcf089a164a1ac8eb248ab89aedd8eb804463 before the job fetched it, causing a false prefix failure. Pin the ledger, trust keyring and advisory diff to HEAD^1 of the default PR merge checkout, following the existing owner workflow. Push BEFORE verification is unchanged.

### Decisions made
Use the immutable base of the tested merge tree; retain prefix, keyring and sabotage checks. No ledger or frozen report changes. Sources checked (KB): source:6ca2a527db9b9503b93d4e57be4091e6, crypto:docs/SABOTAGE_RESISTANCE.md; index revision9141e386254340a9bdba3036f2bb706a last refreshed2026-11-14, older than this race. Current workflow, verifier and exact failed-run history govern the repair.

### Open threads
Replay the moving-base failure and existing negative controls; publish and follow CI.

### Errors
The merged PR's late PCC failure remains recorded; merging did not establish a green result.

Replay completed: live origin/main fails166/167; immutable merge parent passes166. Removing the last entry fails165/166; changing the trust keyring also fails. Receipt: docs/audits/2026-11-16-pcc-moving-base.json. Existing29 PCC tests pass. [pcc:unverified]
