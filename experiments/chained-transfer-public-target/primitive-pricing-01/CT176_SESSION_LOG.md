# CT176 research continuation — 2026-11-17 UTC

Standing: **[pcc:unverified]**. This dedicated append-only session log accompanies cryptanalysis PR #1700; preserve shared logs on concurrently active branches.

## What was done (commands, files, features)

- Read crypto root #3877 (merged), live #3904 updated 05:42Z, concurrent Richelot #4514 (open), cryptanalysis #1692 (merged), #1700 (open), cryptanalysis AGENTS and crypto session log. Fetched current CT175 native Rust main, the pinned 48-fixture Git blob and source CI workflow; sampled current PR exact-head run 44019647722, which had a passed source gate but failed inherited artifact/PCC/workflows. Locked autoresearcher AGENTS could not be decoded and the protected VLT1 was not accessed.
- The CT175 cold native mode does not yet have an external fresh-process paired collector. Frozen the CT176 48×8×6 protocol at commit `99ff7fffbdaa4a4fcf56252990bd351d3f7db1e6`.
- Authored opt-in external collector at `e81d156049dd521f1247def2067c2e78858f66f2`, corrected its exact Git-object NUL hashing, spawn-error preservation, lossless stdout/stderr and incomplete-panel refusal at `61679d1e1a3f2cafe1bbe32727e0d1086170700b`. Corrections preceded any native execution.
- Committed synthetic public-record plus mutation-control test module at `22c227748936c098e3049eabe8eebf2417d0de53` and the limited source-only GitHub workflow step at `895bf9e954c5f6f1955b0614d7c2304e376d1997`; tests have been authored but hosted result not yet confirmed in this entry.
- This run had no Rust/Cargo or restored authenticated source in the isolated container; no native CT125 arithmetic, actual route measurements or public-target discrete logs were performed. GitHub Actions source parser checks are not independent scientific verification.

## Decisions made (and why)

- Continue CT175 on its existing PR branch, not overwrite the active Richelot work. Use original immutable public inputs and exact outputs/counters. Default to plan-only and refuse execution without explicit opt-in and external admission; flags do not authorize paid capacity.
- Retain each process exit/error/stdout/stderr and A/A controls; treat failed, timed-out, truncated and invalid panels as failed scientific evidence. Preserve CT174's historical warm timing semantics unchanged.
- Do not infer primitive cost or complete ECDLP gain from transfer-only timing; original 695/701, C169/C13a/C13b/N2_actual/D_padd, matched full rho/BSGS/IC, cost/CI/memory and signed PCC remain mandatory.

## Open threads (unfinished, pick up next time)

- Check exact final-head source CI at the permitted cadence, fix only introduced failures, preserve red inherited gates. Typecheck and run 48 native parity after original artifact restoration and budget admission; then execute authorized external cold panel, independently audit raw JSONL, and integrate full cold source-field solves.
- Continue Richelot #4514 under its separate owner and queue, without duplicating locked vault or failing original EKS work.

## Errors (what went wrong, how it was handled)

- Initial collector Git-blob NUL separator source was double escaped. Corrected to `bytes([0])` before any native/collector execution, commit `61679d1`.
- Original provider budget STOP and authenticated 695/701 raw custody still unresolved. Missing local Rust/Cargo and research-KB prevent native/knowledge verification. No infrastructure gate was waived.
