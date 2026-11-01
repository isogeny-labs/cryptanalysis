# Main integration checks, frozen before replay

Merge main d90192b50b13f25d2f8356bf40133a05554285a2, which includes reviewed
CI repairs from PR 1114, into fd03d2f9. Resolve the single artifact-checker
conflict with complete object IDs (`--no-abbrev`) and retain both real sparse/
partial-clone regressions. No C cleanup is authored in this integration.

Replay all eleven artifact-tool tests, global workflow wiring, and the
96-source Lean gate (91 archive-bound plus five rebuilt sources). Theorem
sources and axiom expectations are unchanged. The new main C source hash is
60796724ef7d7c5b3b7dfd89c29db85d5e188deb247b5d9d0bd69b84551afe20,
already pinned by main to 8bf648dcbefe7b8131e5fb26909c77e68778332a.
Preserve the old live receipt and validator bytes copied from fd03d2f9.
Check the old source's exact selector and both negative controls, check the
new main validator's live receipt, and check the new whole-file C pin.
Do not relax any selector, hash, negative control or proof axiom assertion.

Generate a new corpus receipt at
reports/lean-current-corpus-20261025-main-update/receipt.json; preserve every
older receipt and manifest. Retain all replay failures and fixes as separate
attempts. Record explicit old/new hashes for mutable gate/problem paths and
main-updated inputs rather than regenerate frozen manifests. Run policy and
whitespace checks on the merged result. Hosted CI must still pass on the
final head before a guarded merge. No curve, attack, novelty, timing or
mathematical result is changed by these maintenance checks.
