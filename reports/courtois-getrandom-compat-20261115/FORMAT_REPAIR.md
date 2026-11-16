# Additive proof-metadata correction

Current state after main integration `a175be78`: the active record adopts
reviewed main's attestation metadata. The branch JSON-repair record is retained
as `branch-json-repair-8d2645-20261116.json`, alongside its unchanged validator
and all previous ledger events. The explicit adoption note and
[integration receipt](../../experiments/prime-field-auxiliary-ic/random-vs-special/main-integration-20261116/README.md),
claim `PCC-20261116-62ae45` (unverified), preserve both histories. The account
below describes the earlier branch repair and its source-scoped hosted result;
it does not describe a new verification or native rerun. [pcc:unverified]

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

The hosted PCC job subsequently succeeds on exact source `df6d8afb`:
[run 43789263534](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43789263534/job/133043742308).
The captured provider metadata is retained under `pcc-format-followup`, claim
`PCC-20261116-537de4` (unverified). Only the proof-format obstruction is resolved;
the original claim's standing and remaining validation requirements are unchanged.
[pcc:unverified]
