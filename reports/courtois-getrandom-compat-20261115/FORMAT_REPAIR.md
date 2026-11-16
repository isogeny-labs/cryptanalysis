# Additive proof-metadata correction

The original `PCC-20261115-8d2645` used two plain Cargo logs as `recompute`
proofs. That proof kind requires a JSON validator report, so both files were
rejected before their reported outcomes could be considered. Main `66890bbe`
and PR head `b85bca1e` contain identical claim/log/checker bytes. Isolated
snapshots of the actual base and head checker both reproduce the refusal.
The full hosted failure and scoped reproductions are retained in
`experiments/prime-field-auxiliary-ic/random-vs-special/pcc-format-followup/`.
[pcc:unverified]

The active claim now references `validator-pcc-8d2645.json`, which pins both
unchanged text logs and extracts their reported five selected tests passed,
59 filtered out, and the earlier E0425 compiler failure. It preserves the
claim's statement, scope, producer and creation time. `original-claim-8d2645.json`
retains its exact previous bytes. The old ledger event is unchanged; a corrected
claim event and explicit correction note were appended through the PCC writer.
The local proof changes from `fail` to `not_covered`; standing remains
unverified. No native test was rerun, process exit status invented, source/execution
binding added or scientific conclusion promoted. [pcc:unverified]

The scoped report's `status: pass` describes format/hash/count reconciliation.
Its `overall_ci_status: blocked` does not waive exact-head hosted checks,
the separate GLV source-binding failure, CodeQL review or research admission.
This report is unsigned producer data, not independent verification.
[pcc:unverified]
