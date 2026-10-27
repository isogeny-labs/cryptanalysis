# Hecke backlog integration and replay — 2026-10-27

This branch preserves the linked research commits through PR #1219, plus the root PR #1193’s latest artifact-migration commit, on top of the shared CI repair. All 19 current research PR heads are contained. It makes the submitted archive validators and all ten proof modules executable in a bounded CI workflow. No scientific input, output, protocol or claimed rank is rewritten.

## Verified locally

- All ten exact Lean proof modules passed with their pinned Lean 4.35.0-rc4 toolchain. The five mathlib projects declare the same exact revision, 021c46bdd042f67b538b9f9871d556a93713a9a9. Each source was checked afresh and its requested axiom audit counted; only propext, Classical.choice and Quot.sound are allowed. The orbit-cancellation proofs have no axioms.
- Three recovery controls pass: exact bytes with preservation of conflicting existing evidence; refusal of corrupt objects under an expected key; refusal of path traversal and symlink escapes.
- The shared artifact tool's 20 tests pass. The new workflow passes Actionlint; the artifact wiring check passes with the existing unrelated separate-path notice.
- Four of the original fifteen integer validators passed in an independent scratch replay; the others stopped on absent ancestor inputs. The complete linked set has 19 integer validators. It is not represented as fully replayed.

## Input custody still being resolved

The explicit replay manifest binds 31 input paths to their previously recorded SHA-256 hashes. Twenty-one are absent from the integration tree. They include the D79/D7 original matrices, original hecke11.py, and older conductor-6 matrices. They were not found in main or the currently open file inventories. Anonymous S3 reads at the bucket's correct us-east-2 endpoint return 403, which does not distinguish inaccessible and absent objects. A response from the wrong regional endpoint was a redirect document; its digest mismatch was refused and none of those response bytes was accepted as data.

CI uses the repository's existing artifact identity to read only these reviewed content-addressed keys. Each result must match its frozen hash before appearing at the expected path; a present conflicting record is preserved and fails. The workflow retains verified bytes and failure diagnostics, then runs every submitted independent integer validator and rejects tracked evidence changes. The store is read-only in this workflow. Recovery or replay failure blocks integration; a saved earlier success is not substituted for a current check.

The raw scientific Sage producers are not rerun by this software repair. Conditional Lean statements remain conditional, and successful integer replay would establish only the recorded finite checks. No performance or general ECDLP claim is made.

## Exact-path Git history search

All 21 still-missing original input paths were also searched with `git log --all -- <exact path>` across the fetched main and research refs. None has a history entry. This complements the authenticated S3 404s, current-tree/content-digest search and lossless-format checks; no original was found. The pinned input checks remain intact.

## Historical store lookup

The shared storage contract keeps the former `crypto-autoresearcher` bucket
read-only; current writers use `setec-astronomy-artifacts`. A manual replay now
also attempts the same reviewed hashes against that historical store, retaining
a separate report and separately exported checksum-verified bytes. It invokes
the unchanged recovery helper, with no upload or producer rerun. The original
canonical-store failure remains a failure; this diagnostic cannot substitute
for a fresh successful canonical replay. No input hash or integer/proof gate is
relaxed. Historical-store availability and access are not assumed until the
authenticated results arrive.
