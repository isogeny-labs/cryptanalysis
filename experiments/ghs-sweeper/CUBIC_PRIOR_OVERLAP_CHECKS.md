# Historical overlap check, 2026-10-25

Perform a read-only evidence audit of the completed five-only source census
against the retained pre-existing `runs/smoke.sqlite`. This is not a new curve
search or performance experiment. Freeze this scope before the bulk lookup.

Read the exact trace set from `cubic-gluing-checks/binary-census-attempt-1.json`,
selecting `five_module_status=split_distinct` and `three_kernel=false`.
For each trace, query historical candidates whose saved model has base degree
three and relative degree three, and whose source JSON has that exact trace.
Require raw verification and independently verified source order for a
retained overlap witness. Save the smallest spectral model ID as a replayable
witness, the match count, its model/source JSON and verification flags.

Record the database SHA-256 and exact SQL. Do not promote historical spectral
matches into explicit maps, infer exact b-model identity from trace equality,
or infer publication priority from this local database. A matching trace
identifies an existing source isogeny class over the fixed finite field.
Any missing trace remains explicitly missing. Preserve the previous 89-file
artifact manifest; bind this additional audit with a separate manifest.
