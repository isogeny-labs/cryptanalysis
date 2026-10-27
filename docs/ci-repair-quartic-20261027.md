# Replay the quartic certificate backlog without rewriting its evidence

This integration retains the exact 27 author heads listed in
[the manifest](../tools/ci/quartic_certificates.json): PRs 1162–1179, 1181–1182,
and 1184–1190. Every head is an ancestor through ordinary merge commits. Their
changes are confined to `experiments/hecke-432*`; no source, protocol, result,
failed attempt, timing cap or archived proof receipt is rewritten. Main's
separate artifact-tool owner update is included unchanged.

## Verified locally

All 37 submitted Lean modules build afresh with Lean `v4.35.0-rc4` and Mathlib
`021c46bdd042f67b538b9f9871d556a93713a9a9`. All 113 requested axiom reports
are present and use only `propext`, `Classical.choice` and `Quot.sound`, or no
axioms. The initial pass found 15 missing local Mathlib cache dependencies;
restoring those exact pinned modules resolved those failures without changing
proof sources. Both attempts and the final module-by-module result are retained
in [the evidence directory](ci-repair-quartic-20261027/). `lean4checker --fresh`
is unavailable; these are actual Lean kernel checks, with that additional
independent checker still unavailable.

Nine existing integer audits run in an isolated copy and reproduce their
committed JSON outputs byte for byte: discriminant norms, field index, ideal
support overlap, relative quadratic support, quartic local-order arithmetic,
the F23 residue-extension witness, coefficient conjugacy, quadratic-residue
tables, and common prime support. The latter checks the full exact gcd before
bounded prime division, with the original one-million cap; no claim of primality
or complete factorization is added for the individual large residuals.

Three refusal controls pass: changed/missing inputs fail; parent and symlink
escapes fail before reading outside the replay root; missing or nonstandard
axiom output cannot stand in for a proof.

## CI replay and remaining verification

The scoped workflow replays all 42 submitted integer checkers and all 37 proof
modules. Its input manifest fixes 1,398 exact digests, including the original
9,260,825-byte PARI checkpoint SHA-256
`b7f7588ee150c5c3ebe09fd0057f640eb6291d8a1463546d904bd1a086ebce27`.
That checkpoint is absent locally; its content-addressed pointer is preserved,
and the existing authenticated CI reader must retrieve and verify it. No
replacement bytes are generated. The checkpoint is hashed, never executed or
deserialized by these Python audit jobs.

Several frozen protocols and terminal receipts contain the original absolute
`/Volumes/SSD990/cryptanalysis` path. CI recreates that layout in a separate,
disposable copy, then compares every frozen input and output digest before and
after replay. The source checkout is not used as an output directory. The
ordinary hosted runner does correctness checks only; no Sage experiment,
benchmark, new held-out selection or performance measurement is launched.
Raw successes and failures are retained even when another checker fails.

The full hosted integer replay and all current-head required/applicable checks
remain unverified until their jobs complete. This report does not treat the
planned 42 checks as passed. A missing/corrupt input or changed output fails the
job; the manifest is not a license to replace expected bytes after a failure.

## Claim boundaries

These are retrospective integration and certificate audits. A protocol's
original `FROZEN_BEFORE_*` status is preserved as the author's record; publication
of a protocol and its result in one packet is not independent evidence of a
prospective timestamp. This integration creates no prospective validation or
speedup claim.

The proof maps in each study remain authoritative about scope. Arithmetic
certificates and general ring/permutation implications do not establish the
complete Sage/PARI number-field bridge. The local Hensel lifting, discriminant
to Frobenius-sign bridge, and exact field/ideal encodings remain partial where
the reports say so. Saved stack failures and timeouts remain bounded unknown
results; later local certificates do not turn those original attempts into
successes. No solver baseline, receipt, cost, threshold, curve identity or
scientific validation status is promoted by this integration.

The separate Hecke matrix integration has 21 unavailable frozen inputs and is
not covered or unblocked by these quartic checks.


## Move three original census files to their required storage location

The inherited artifact gate identifies three source-census JSON files larger
than one MiB: the j1728 path holdout, j1728 product holdout, and sign-branch
holdout. Their original digests remain in the input manifest. A separate,
manual-only migration job checks those exact bytes, uses the unchanged shared
artifact tool to store them and verify the remote objects, and exports only
its pointer/ignore metadata for an ordinary reviewed Git commit. The job has
no GitHub write permission and cannot push or merge. Migration and a fresh
hosted retrieval remain pending at this checkpoint. No policy exception or
large-file override is used.
