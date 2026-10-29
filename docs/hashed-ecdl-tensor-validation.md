# Native tensor ECDL development validation — 2026-10-29

This receipt covers the compact encoder, contraction backend and full tensor
reduction. The earlier [reference receipt](hashed-ecdl-validation.md) remains
historical evidence for the bounded generic implementation. No performance
experiment, cloud job, deployed-curve run or theorem proof was performed.

Host: Linux x86-64 cloud container. Rust 1.99.1
`58cf8f9c3`, with additional Rust 1.78.0 checks. All fixtures are public.
The crate has declared MSRV 1.78. The standalone and binding sources are
byte-identical. The [source manifest](hashed-ecdl-tensor-sources.sha256)
covers both manifests and all Rust source files; its SHA-256 is
`cedddbec1c6348e5592da9ef0e490c68b90d457e865a4778cd1dbd33f70486e3`.
The bounded compatibility/export module now hashes to
`21c5f18243bcd0a8d8dd722d254d48ff9ba2b2bd29941c1b27acf568d63c45e1`.

Run the manifest check from the crate directory, not the repository root:

```sh
cd crates/hashed-ecdl-tensor
sha256sum -c ../../docs/hashed-ecdl-tensor-sources.sha256
```

For cryptanalysis, use `bindings/rust/hashed-ecdl-tensor` and a three-level
relative path to `docs/`. The separate workspace Cargo.lock is integration
metadata; the mirrored standalone lock is also committed for reproducibility.

| Command / check | Observed outcome |
| --- | --- |
| `cargo test --release --manifest-path crates/hashed-ecdl-tensor/Cargo.toml` | 25 passed; native runner and doc targets also compiled; [compact transcript](hashed-ecdl-tensor-tests.txt) |
| `cargo clippy --manifest-path crates/hashed-ecdl-tensor/Cargo.toml --all-targets -- -D warnings` | exit 0 |
| `cargo fmt --manifest-path crates/hashed-ecdl-tensor/Cargo.toml --check` | exit 0 |
| `cargo +1.78.0 check --locked --manifest-path bindings/rust/Cargo.toml -p cryptanalysis -p hashed-ecdl-tensor --all-targets` | exit 0; both the crate and Rust/C integration compile on the declared floor |
| `cargo test --release --manifest-path bindings/rust/Cargo.toml -p cryptanalysis --lib` | 20 passed; [transcript](hashed-ecdl-tensor-binding-tests.txt), including all 199 C/BigUint scalar cross-checks |
| `cargo clippy --locked --manifest-path bindings/rust/Cargo.toml -p cryptanalysis -p hashed-ecdl-tensor --all-targets -- -D warnings` | exit 0 |
| `cargo fmt --manifest-path bindings/rust/Cargo.toml --all --check` | exit 0 |
| `RUSTDOCFLAGS='-D warnings' cargo doc --locked --manifest-path bindings/rust/Cargo.toml -p cryptanalysis -p hashed-ecdl-tensor --no-deps` | exit 0 after quoting one cofactor formula that Rustdoc treated as a link |
| cargo-deny 0.20.2, existing binding-workspace policy | advisories, bans, licences and sources all pass; no policy exception |
| Native runner solve, seeded fixture 1, p=5, order=7, explicit two-billion-step policy | scalar 4; 13 successful-trial relations; actual backend `Functional`, zero recursive calls |
| Native runner replay, separate process | exit 0; independently verified scalar 4 |
| Change receipt scalar to 5 and replay | exit 1, `verification failed: certificate extraction` |
| `diff -ru --exclude=target` between the mirrored crate trees; source-manifest checks in both directories | identical; all 15 hashes pass |
| New post-merge workflow, pinned repository actionlint wrapper | exit 0 |
| Typst 0.15 report build and all-page visual inspection | 3 pages; diagram spacing corrected and rechecked |
| Uncapped root `cargo test --release --lib` | restarted after execution-environment interruption; no complete-root pass claimed in this snapshot; final status belongs to the paired crypto PR |
| Maintained root strict clippy, existing `scripts/clippy-maintained.sh` | exit 0 after restoring sparse compile inputs; includes the compatibility module's MSRV fix |
| Binding-core debug tests | interrupted by execution-environment restart before completion; no full debug pass claimed; final executable-source release panel passed25/25 |

The compact core transcript preserves the complete final executable-source
panel with the terminal separator blank line omitted. The subsequent
cofactor-formula correction changes documentation only; strict Rustdoc was
rerun. It does not change arithmetic, encodings, counters or the solver.

The [native fixture receipt](hashed-ecdl-tensor-fixture.json) has SHA-256
`54f3a724feb70fc1cc7465371caf43a1c93578b168dec5487bed94729d42f63c`.
It is replayable with the native runner. Its counters report 390 contractions,
321126 functional input assignments and zero recursive calls; these are
uncalibrated diagnostics, not performance measurements or history attestations.
Post-merge workflows in both repositories repeat targeted native validation;
they do not change any existing pull-request merge gate.

## What the controls establish

Graph counts and prefix witnesses are compared with independent truth tables,
including parallel edges and isolated vertices. Compact products are compared
with independent BigUint multiplication through 513-bit inputs, with explicit
edge/degree inequalities. Point encodings cover every pair on two small
curves, including identity, inverse, doubling and two-torsion. Inverse-hash
enumeration is compared with a subgroup scan. Cofactor projection and a full
tiny relation pipeline are checked, with corrupted-certificate rejection.

The recursive controls cover ring units and interpolation, canonical lifting
at creation precision, normalized integral Cauchy kernels, geometric modes,
weighted monomials, tapered Hermite reconstruction and a complete forced
small packet recursion versus independent direct summation. These bounded
checks do not establish the general source theorem or a practical speedup.
The source's normal admission guards select finite-size fallback on practical
graphs; the runner reports that fact. Counters are diagnostics, not calibrated
costs and not attestations of discarded-trial history.

## Failures and setup retained

- The first inner Clippy MSRV attribute was not accepted in ordinary Rust;
  supported outer annotations preserve the old compiler and fix the two
  legacy manual-is-multiple-of lint failures. Four core style warnings were
  fixed without adding lint exemptions.
- Initial dependency packaging activated two integer versions and a new
  Unicode licence through procedural derives. The crate now uses the audit
  workspace's integer version and a generic Ratio with its optional old
  integer dependency disabled; explicit strict JSON records avoid derives.
  Cargo-deny now passes under the unchanged policy. Optional packages can
  remain in Cargo.lock without being active duplicate dependencies.
- JSON macro result-type shadowing was caught and fixed during compilation.
  API-doc validation caught a cofactor formula interpreted as a link; quoted
  the formula and reran the same strict documentation command successfully.
- Maintained root lint first lacked a tracked example include at
  `research/ml_dataset_20261028/startup-integration-cli-fixture-native/run.rs`.
  The existing `ci-scope.mjs --materialize` restored 187 compile-time inputs.
  No source, fixture, test or gate was disabled.
- A whole-binding-workspace strict lint also encounters two existing CUDA
  deprecation errors: `memcpy_stod` at solver.rs:220 and `memcpy_dtov` at 285.
  Both calls and cudarc 0.19.10 are unchanged from main. Touched core/binding
  targets pass strict lint; the unrelated CUDA source is preserved. The
  repository's bindings workflow is currently disabled manually; no workflow
  was disabled or re-enabled by this change.
- Earlier development runs on superseded dependency snapshots were interrupted
  when the final source replaced them; their partial logs are not full passes.
  The final root regression has no ten-minute cap. The old reference's capped
  5512-test trace remains explicitly incomplete in its historical receipt.
- An execution-environment restart terminated the long root build and optional
  debug panel before completion. Working files, commits and completed receipts
  survived. Restarted the mandatory broad root command alone, without a time
  cap. The optional interrupted debug panel is not reported as a pass.
- Conductor is absent; the repository's documented warn-and-allow fallback
  applies. A temporary Git index lock belonged to compile-input materialization;
  waited for that process to finish and repeated the unpublished branch refresh.
  No live lock was removed. Main's concurrent prototype files and log entries
  are preserved; only native correctness checks were executed here.

Large raw regression logs follow the artifact-store policy. This runtime has
no configured artifact-store identity, so an oversized local trace is not a
durable remote artifact and must not be represented as uploaded. Compact
diagnostics and the precise completion result are retained here when available.

The [canonical audit record](https://github.com/isogeny-labs/crypto/blob/main/problems/hashed-ecdl-tensor-backend.md)
keeps independent general correctness and complexity obligations open. No
benchmark, leaderboard, frozen run or curve/route evidence is changed.
