# Induced-transfer replay repair, 2026-11-16

## What was done

Created PR #1704 to keep the frozen consumer/producer replay separate from current verification. Added a six-input amendment contract, dual replay driver, seven refusal controls, and the current GLV pin with its historical sized-cap control retained. Local historical/current replay completed; CI is pending. All validation assertions remain unsigned. [pcc:unverified]

## Decisions made

Retain the original proof, reference, receipts, keyring snapshot and nine claim bindings in their original consumer checkout. Require unchanged bytes for all other sealed inputs. Keep deadlines, outputs and final guards explicit. Source references and validation scope are in `docs/audits/2026-11-17-induced-transfer-dual-replay.md`, recorded by PCC-20261117-9d1f62; that record carries no signed standing. [pcc:unverified]

## Open threads

Track current-head CI on #1704, review failures, and merge only after applicable checks pass. The separate crypto compiler integration remains in progress. S3 is unavailable; an HTTP 403 recheck was retained and no store check was bypassed. [pcc:unverified]

## Errors

The first local current-test attempt lacked sparse-checkout dependencies. The next exposed the old GLV-current binding; the repair retains the old pin as history and checks the maintained source separately. An intermediate replay caught a workflow edit in its final source guard and failed. The later complete replay passed with all source guards unchanged. Failed attempts remain retained. [pcc:unverified]
