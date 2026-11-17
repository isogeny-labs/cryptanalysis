# Induced-transfer replay repair, 2026-11-16

## What was done

Created PR #1704 to keep the frozen consumer/producer replay separate from current verification. Added a six-input amendment contract, dual replay driver, seven refusal controls, and the current GLV pin with its historical sized-cap control retained. Local historical/current replay completed; CI is pending. All validation assertions remain unsigned. [pcc:unverified]

## Decisions made

Retain the original proof, reference, receipts, keyring snapshot and nine claim bindings in their original consumer checkout. Require unchanged bytes for all other sealed inputs. Keep deadlines, outputs and final guards explicit. Source references and validation scope are in `docs/audits/2026-11-17-induced-transfer-dual-replay.md`, recorded by PCC-20261117-9d1f62; that record carries no signed standing. [pcc:unverified]

## Open threads

Track current-head CI on #1704, review failures, and merge only after applicable checks pass. The separate crypto compiler integration remains in progress. S3 is unavailable; an HTTP 403 recheck was retained and no store check was bypassed. [pcc:unverified]

## Errors

The first local current-test attempt lacked sparse-checkout dependencies. The next exposed the old GLV-current binding; the repair retains the old pin as history and checks the maintained source separately. An intermediate replay caught a workflow edit in its final source guard and failed. The later complete replay passed with all source guards unchanged. Failed attempts remain retained. [pcc:unverified]

## Follow-up: current corpus expectation

The induced-transfer job passed CI at 7d2ba80d3. The separate corpus job then completed its native delta checks and failed comparison with the old November 1 expectation. Added a separate current expectation and an exact three-source-field amendment checker; five controls prohibit rewriting the historical receipt or changing theorem evidence/counts. The original receipt remains intact. New-head corpus replay is pending, and S3-dependent gates remain blocked. [pcc:unverified]

## Follow-up: workflow input wiring

Reconciled four unchanged workflows reported by the artifact gate. CT125 and CT146 now name exact source-only inputs instead of the whole archive ancestor; their finite-field, source mutation, derivative and refusal controls pass in a private staged copy. CT137 and the separately approved CT141 job now have the canonical pull for nondual18 model fixtures while retaining the original pinned hydrator and exact hashes. CT141 PR controls have no artifact pull, and its manual approval step remains before checkout. The global wiring check now passes without changing the checker, manifests or any frozen source/record. New-head CI is required; S3 remains unavailable. [pcc:unverified]

## Follow-up: exact sparse Python closure

Current-head CI exposed a missing `check_pair.py` import in CT141's narrowed source checkout. Added that exact source dependency and reran the source-guard commands in a private tree containing only the declared sparse files; both Python modes and the existing deny-without-admission checks pass. No benchmark job was run. The corpus expectation comparison now passes; the corpus gate reaches a previously unreviewed archived LPGraph source, which is being replayed separately without editing its frozen input. [pcc:unverified]
