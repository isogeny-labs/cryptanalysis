# 2026-11-21 — High-genus order certification audit (ChatGPT) [pcc:unverified]

## What was done (commands, files, features)
- Inspected connected GitHub PR #1884, high-genus README, the Rust IC module header, AGENTS.md and docs/ACTIVE.md.
- Opened stacked draft PR #1897 against `claude/higher-genus-5-131` and registered task.
- Added `suite/docs/highgenus/ORDER_CERTIFICATION_AUDIT.md` and corrected the README and module documentation.

## Decisions made (and why)
- **Do not infer exact Jacobian order** from the gcd of a few relation minors and sampled annihilation checks.
- For a collected relation lattice L contained in the full kernel K, the full-rank index satisfies [Z^m:L]=|<FB>|[K:L]; a sampled-minor gcd can be even larger.
- Preserve already reported planted-log verification as an independent property, not a group-order certificate.
- Keep PR draft: documentation fixes only, no independent group-order proof or CI run.

## Open threads (unfinished, pick up next time)
- Implement independent certificate or change runtime output to clearly distinguish unverified candidate order.
- Add negative tests for incomplete relation lattices and proper factor-base subgroups.
- Run Rust tests and PCC gate in a checked-out environment; review results.

## Errors (what went wrong, how it was handled)
- Connector permits source inspection and commits but does not execute Cargo/tests. No test pass is claimed.
