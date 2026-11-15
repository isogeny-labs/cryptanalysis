# Joint public-coefficient relation targets

`joint::JointTable`, `prepared::solve_joint` and `solve-hashed-joint` add an
optional shared doubling chain for the existing public `uG+vQ` relation target.
The existing prepared point search, selected witnesses, coefficients, matrix,
elimination and certificate replay remain. The three-point table is created
once, lazily after the original subgroup validation, and reused across relation
attempts/base trials for the same curve/G/Q. [pcc:unverified]

This is HAC Algorithm14.88 in additive notation for two fixed bases. All group
operations use the checked native affine addition, with no scalar reduction or
unchecked formula. The public table constructor validates both subgroup points;
the collector uses only its certified generator and already validated target.
The decomposition oracle sees the resulting point and never the coefficients.
The original `solve-hashed` target-generation path remains a direct control.

## Development evidence

The initial locked release all-target suite passes 121 cases. The first formatting
check then found module declaration ordering only; the failed logs/source are
retained. Final current-source targeted controls and strict all-target clippy
pass after reordering. The initial/final source snapshots and both source
identities remain distinct. [pcc:unverified]

Common controls cover every scalar pair0..18 with equal/opposite/identity
point pairs, mixed/unreduced scalars through1024 bits on F17, invalid and
noncanonical/fixed-cofactor subgroup points, step/width/vector errors, full
seeded certificate/RNG/search-event equality at seeds1,42,83, identity solve,
and actual p5 CLI receipt equality/replay plus exclusive output preservation.
No scientific/benchmark run or general independent audit is recorded.
[pcc:unverified]

The common kernel/API and correctness controls match Crypto byte-for-byte.
The mirror has no addition-event Meter field; no counter was invented or
copied into its runtime. Crypto retains a separately named diagnostic control
for that field. No mirror runtime or calibrated work result is asserted.
[pcc:unverified]

Current-source formatting and strict all-target clippy pass in both mirrors.
Existing getrandom0.4.3 edition2024 manifest prevents inherited Rust1.78 check; see problems/hashed-ecdl-rust-msrv.md; not changed or passed here. [pcc:unverified]

[source.sha256](source.sha256) pins every native Rust source/test, fixture,
manifest/lock and API document, plus the actual parent Rust workspace inputs
when applicable. [qualification.json](qualification.json) records commands,
exit codes, source transition, archive bytes/digest and scope. Unchanged
source is pinned by dependency parent `7893dc931c6f691a57b428d16f7cf8df193082ad`.
[development.tar.xz](development.tar.xz) retains raw stdout/stderr, first
formatting failure, initial/full manifest and touched initial/final sources.
Extract into a fresh directory, then run `sha256sum -c SHA256SUMS` from its
`development/` directory. These are producer artifacts, not signed verdicts.
[pcc:unverified]

## Runtime qualification remains open

Fresh preflight finds no local AWS credentials, checkpoint upload token or bound
cloud identity. The actual checkpoint gate reached transport selection and
failed before upload/readback; its complete attempted note is retained and the
original tracked note restored unchanged. The documented GitHub checkpoint
workflow lookup returns404; the experiment workflow exists, but it does not
supply the missing checkpoint/native-image admission. No workflow dispatch,
image build, cloud job or scientific batch was launched. [pcc:unverified]

The [named runtime dependency](../../problems/point-table-joint-runtime-qualification.md)
keeps the matched runtime comparison open. It does not make a mathematical
impossibility claim. The prior first-pilot USD10 override and original
32-context/2368-attempt workload in separate PR2984 remain unchanged. No study
branch, frozen evidence, scalar result or general-audit standing was changed.

## Sources checked

- [HAC chapter14, Algorithm14.88 and Note14.90, pp617–618](https://cacr.uwaterloo.ca/hac/about/chap14.pdf): established simultaneous multiplication, precomputation and zero-column costs.
- Native `curve.rs`, `reduction.rs`, `prepared.rs` and existing pair controls: validation, lifecycle, randomness, selector ordering and replay contracts.
- Sources checked (KB): KB unavailable; no MCP tools loaded and repository wrapper status/three mechanism, negative and batch-inversion queries fail for missing executable. Lead atlas fails for missing orchestration module; narrow native paths and the primary HAC text are the fallback. No novelty/absence claim.
