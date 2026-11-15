# Prepared point-table collector: implementation and development receipts

The native library now exposes `prepared::PairTable`, `prepared::solve` and the
`solve-hashed` file command. Preparation reuses the relation collector's complete
factor-base enumeration once per nonempty trial. Queries derive `Q=R-P`, match
full canonical points and replay original arithmetic membership and the sum
before accepting a relation. Original coefficients, matrix construction,
elimination and certificate verification remain. [pcc:unverified]

| Requested step | Implementation and control |
|---|---|
| Decode/validate bases once | Private trial factory consumes existing complete indexes; standalone PairTable constructor enumerates once |
| Exact point hash table | Full Point Eq/Hash keys; constant-hash control preserves all answers |
| Derive Q for each P | Selector order and slot identities preserved, including unequal/tied limits |
| Replay before acceptance | Original arithmetic membership and sum checks; injected table hit and forged certificate rejected |
| Both repositories | New module, common tests and feature document are byte-identical; existing main differences preserved |

These rows describe producer implementation/controls, not signed execution or
independent audit standing. [pcc:unverified]

## Qualification

Final relevant release checks report 67 library, 5 runner, 12 finite, 5 prepared-pair and 3 strict-JSON controls
passing. Strict all-target clippy and changed-source formatting pass. Complete
seeded certificates and final label-RNG states match the original selector
oracle. Additional controls cover all F17 subgroup points, empty bases, limits,
fixed cofactor, fresh-trial rebuilding, CLI replay and exclusive output.
These are development correctness checks, with no runtime comparison.
[pcc:unverified]

Modern Rust checks pass. The inherited getrandom 0.4.3 graph fails Cargo 1.78 because it requires edition2024/Rust 1.85; see [the open compatibility record](../../problems/hashed-ecdl-rust-msrv.md). No dependency version or declared floor was changed. [pcc:unverified]

Exact source/lock identities and commands are in [qualification.json](qualification.json)
and [source.sha256](source.sha256). [development.tar.xz](development.tar.xz)
retains original Cargo stdout/stderr and initial/corrected/final touched-source
snapshots. Extract into a fresh directory; inside `development/`, run
`sha256sum -c SHA256SUMS`. Full unchanged source is pinned by the dependency
base commit and the manifest. The mirror manifest includes its actual parent
Rust workspace lock as well as the older leaf lock. [pcc:unverified]

The original getrandom API failure, missing mirror Meter field, unused import
and strict-clippy findings remain in that archive. One corrected-stage Crypto
wrapper printed Cargo success but returned exit 1 to the tool; it is not treated
as a successful wrapper. The separate direct final Crypto all-target invocation
exits 0 and is retained. The mirror's corrected-stage all-target invocation
also exits 0. [pcc:unverified]

## Scope and follow-up

The feature is opt-in and requires two prime-field slots. Ordered vectors and
hash keys are retained alongside matrix indexes; setup, memory, hash work,
query failures and verification must be charged in an admitted measurement.
Counters are unpriced diagnostics. No scientific/benchmark run or runtime gain
is claimed. The prior frozen ECBench studies, challenge work and separate study
branch are unchanged. [pcc:unverified]

Primary sources reviewed: HAC 3.56 (established matching with table construction
and memory costs), official Rust HashSet Eq/Hash documentation, and the native
finite/reduction/curve contracts. The crate's PREPARED_PAIRS.md gives API,
lifecycle, ordering and replay details. Runtime qualification and independent
review remain open.
