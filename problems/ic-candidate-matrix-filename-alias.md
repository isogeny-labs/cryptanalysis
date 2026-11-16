# Historical IC matrix candidate filenames omit the u32 LA suffix

- **Status:** investigating; local repair passes, paired mirror pending source merge
- **Kind:** metadata identity implementation gap
- **Affected work:** PR1621, experiments/ic-euclid-inversion-20261116, experiments/ic-bench/candidate_aliases.json
- **Next action owner:** T-6450; paired mirror T-6737
- **Last updated:** 2026-11-16

## Problem

Ten already published matrix-variant filenames say LAgauss while their frozen
hashed contents correctly declare LAgaussu32. The full semantic gate rejects
the stage/name mismatch. The original bytes and raw references must be retained.

## Evidence and uncertainty

[pcc:unverified] During the packed-square input freeze, the full semantic check
reports exactly ten older prefixchainu32/prefixeuclidu32 candidate errors across
N15/18/21/24/27. Fresh packed-square candidates do not trigger those errors.
The old producer's filename construction hardcodes LAgauss while constructing
LAgaussu32 in matrix-variant records. The candidate content hashes match their
suffixes. Initial failure is archived in the packed-square native-001 manifest.
Unsigned claim 8dd896 records the local repair checks.

The error concerns naming and reference resolution. It does not alter arithmetic
answers, certify performance, or resolve PCC custody and signed standing.

## What would unblock it

- [x] Preserve all ten original candidate files and raw run references byte for byte.
- [x] Add canonical-name copies and a separate exact SHA-pinned alias manifest.
- [x] Keep stage/curve/base/hash checks after alias resolution; reject changed or
  missing canonical copies, changed source/pins, path escape, chains and extra fields.
- [ ] Merge the source repair, then mirror the validator and tests in crypto as
  required by crypto:docs/curves/ic/README.md and AGENTS.md.

[pcc:unverified] Local full semantic validation passes and 15 tests pass, including
negative controls and canonical-hash rejection after aliasing. This is an unsigned
producer check, not independent signed standing. The shared mirror remains pending.

## Next discriminating step

Publish the source repair in PR1621 with all original records untouched. After
its merge, update the shared validator/tests byte for byte in a paired crypto PR.
The prepared clean worktree is crypto/wt/ic-candidate-alias-20261116, branch
codex/ic-candidate-alias-20261116, currently untouched at d2f6c9e3f5. Do not publish
mirror changes before the source merge. No frozen input or old receipt is rewritten.

## Sources checked

KB revision9141e386254340a9bdba3036f2bb706a,last_refresh2026-11-14T21:44:48Z,
lexical index ready, hybrid not current; source age predates this implementation,
so actual owning files were read. Queries: IC1 candidate historical alias canonical
hash immutable; IC curve crosswalk mirror validate_semantics.
source:3f229009b48656312b2b4613691c6603,
cryptanalysis:docs/curve-identities.md, published internal analysis/evidence none,
not superseded: requires separate alias mappings and unchanged hash preimages.
source:542be06887264e3f772a553a72dd4376,
crypto:docs/curves/ic/README.md, published internal analysis/evidence none,
not superseded: requires source merge before mirror update. Read both primary
files and the owning validator, tests and old freeze_inputs.py.

## Resolution and history

2026-11-16: Failed gate preserved. Exact canonical copies plus strict alias
validation and negative controls implemented. Local checks pass; shared mirror
and source merge remain unresolved. This metadata repair grants no performance
standing or merge-gate waiver.
