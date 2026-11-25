# Reviewed Rust floor integration, 2026-11-15/16

PR #1586 merged upstream as `f3223fe6`. This follow-up integrates main
`66890bbe` in source `bbdf695d`, retaining both merge parents. It adopts the
owner-reviewed Rust 1.85 native/consumer floor and keeps the original locked
lint, correctness and minimum-version checks. The standalone prime-field IC
core and its dedicated Rust 1.78 matrix are unchanged. [pcc:unverified]

Claim `PCC-20261116-f7dd33` is an unsigned producer assertion. Its scoped
[validator report](msrv-qualification-validator.json) reports local integration
checks, with `overall_ci_status: blocked`. It does not certify the full PR,
performance, or independent execution. [pcc:unverified]

The initial report omitted PCC's required `raw_data` and `headline` fields.
Its [failed validation](initial-validator-format-failure.log),
[original claim bytes](original-claim-f7dd33.json) and
[original report](msrv-integration-validator.json) are retained. An explicit
claim metadata correction points to the scoped report with those fields;
both claim ledger events and a correction note remain. The statement, raw
checks and overall blocked CI status are unchanged. The corrected report is
`not_covered` because it is unsigned, not independently verified.
[pcc:unverified]

| Scope on `bbdf695d` | Local producer outcome |
| --- | --- |
| Native `hashed-ecdl-tensor` and `cryptanalysis` | Formatting, locked strict Clippy, 180 release correctness tests, locked Rust 1.85 all-target compilation pass |
| Structured consumer | Formatting, locked strict Clippy, 33 library and three CLI release tests, locked Rust 1.85 all-target compilation pass |
| PCC canary | 69 refusal/control classes behave as required |

These counts have separate scopes and are not pooled. Correctness tests ran
on stable; minimum-version checks compiled all targets on Rust 1.85. No new
local standalone-core test or Rust 1.78 native compatibility claim is made.
Full commands, exit statuses and log hashes are in
[native-checks.json](native-checks.json) and
[consumer-checks.json](consumer-checks.json). The compiler, manifests,
lockfiles and source hashes are pinned in
[source-provenance.json](source-provenance.json). [pcc:unverified]

The initial hosted read concerns `e0ad790a`, not `bbdf695d` or a later evidence
commit. Only the dynamic CodeQL run was present: six analysis jobs passed and
the aggregate check failed with 23 annotations. The regular validation
workflows had not run on that head; their absence is not success. The cause
is not established. The raw PR, upstream-fix, review and check read is retained
in [initial-hosted-read.json](initial-hosted-read.json). New-head hosted results
must be assessed separately. [pcc:unverified]

The inherited GLV source-pin drift remains open. This merge changes neither
`src/curve.c` nor the selector's expected digest. The known CodeQL threads
remain visible; no alert-management API retry, suppression or output removal
was attempted. The previous minimum-version rejection and partial-receipt
format failure remain in the earlier
[consumer follow-up](../ci-consumer-followup-20261115/). [pcc:unverified]

The [ledger merge receipt](ledger-merge.json) records the exact canonical main
prefix and all 13 replayed unsigned events, including both distinct events for
the earlier metadata-corrected claim and its correction note. The PCC append
writer retained the event bodies; no main event or signature was rewritten.
The frozen snapshot retains its exact tree and 2,473 files; all three earlier
follow-up evidence trees are unchanged. [pcc:unverified]

No benchmark was launched. Checkpoint access, an admitted GPU allocation,
frozen targets, phase accounting and independent signed replay remain required
before a new timing claim. Applicable hosted CI and blocking reviews must pass
before merge; local successes do not waive the GLV or CodeQL blockers.
[pcc:unverified]
