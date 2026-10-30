# Native tensor ECDL development validation — 2026-10-29

This is the historical implementation receipt. Its transcripts and source
manifest are preserved. The later [sampling audit](hashed-ecdl-audit-20261029/README.md)
records the extended API, new tests and a separate source manifest; use that
manifest for the updated source rather than treating this snapshot as current.

This receipt covers the compact encoder, contraction backend and full tensor
reduction. The earlier [reference receipt](hashed-ecdl-validation.md) remains
historical evidence for the bounded generic implementation. No performance
experiment, cloud job, deployed-curve run or theorem proof was performed.

Host: Linux x86-64 cloud container. Rust 1.99.1
`58cf8f9c3`, with additional Rust 1.78.0 checks. All fixtures are public.
The crate has declared MSRV 1.78. The standalone and binding sources are
byte-identical. The [source manifest](hashed-ecdl-tensor-sources.sha256)
covers Cargo metadata and all Rust source files; its SHA-256 is
`a2fdf1300848c29e7a37d5265c1c2d129aae0d3f23a515daf446b908186b3d0f`.
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
| `cargo test --locked --release --manifest-path bindings/rust/Cargo.toml -p hashed-ecdl-tensor -p cryptanalysis` after adding coupled controls | 27 core, 20 binding-unit, 19 FFI-parity and 14 documentation tests passed; [full selected-package transcript](hashed-ecdl-tensor-full-tests.txt) |
| Same complete selected-package command after replay randomness correction | 27/20/19/14 passed again; [final replay panel](hashed-ecdl-tensor-replay-tests.txt); counted-RNG assertion confirms caller propagation |
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
| `diff -ru --exclude=target` between the mirrored crate trees; source-manifest checks in both directories | identical; all 16 hashes pass |
| New post-merge workflow, pinned repository actionlint wrapper | exit 0 |
| Typst 0.15 report build and all-page visual inspection | 3 pages, 64238 bytes; all pages inspected; unused italic font subset removed to satisfy the existing 64 KiB store limit |
| Existing artifact-policy checker, `python3 tools/artifacts/artifacts.py check origin/main HEAD`, on the committed packaging follow-up | exit 0; no waiver or policy change |
| Uncapped root `cargo test --release --lib` | exit 0: 5389 passed, zero failures, 123 existing ignored tests; [compact parent-process receipt](hashed-ecdl-tensor-root-tests.txt) |
| Maintained root strict clippy, existing `scripts/clippy-maintained.sh` | exit 0 after restoring sparse compile inputs; includes the compatibility module's MSRV fix |
| Binding-core debug tests | interrupted by execution-environment restart before completion; no full debug pass claimed; complete selected-package release panel passed |

The compact core transcript preserves the complete final executable-source
panel with the terminal separator blank line omitted. The subsequent
cofactor-formula correction changes documentation only; strict Rustdoc was
rerun. It does not change arithmetic, encodings, counters or the solver.

Two subsequent test-only controls exercise correlated ports, quadratic mode
terms and two recursion levels. They are behind `cfg(test)` and change no
library execution path. The full selected-package release panel then passed
27 core tests. Its source manifest is the current 16-file manifest above;
the first 25-test snapshot used the 15-file manifest
`cedddbec1c6348e5592da9ef0e490c68b90d457e865a4778cd1dbd33f70486e3`.
Strict lint and Rust 1.78 all-target compilation also passed with the new tests.
The first coupled-control snapshot used manifest
`cc78ba18a3253daa59b202008cd50d7d7551a38e7c39debf26eb68bd5e737480`;
the final replay correction uses the manifest at the top of this receipt.

Final audit replaced replay's internal fixed fixture RNG. The solver now
forwards caller randomness through `verify_with_rng`, and standalone `verify`
uses OS randomness. A counted-RNG control asserts that replay actually consumes
the supplied source. This preserves the expected-polynomial root-extraction
hypothesis when uniform randomness is supplied. The stored public fixture's
mathematics remains replayable; diagnostic counters are historical observations.

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

The extended controls add two correlated ports at one vertex, degree-two
incoming modes with mixed coefficient 2, and a second recursive layer that
retains the first packet's creation precision. All agree with direct counts.

## Failures and setup retained

- Implementation PR1298 merged at 2026-10-29T22:23:42Z as
  `7e58a9036ce9f839903f963a9a91d85a03cb925a`. Its store job flagged the
  74400-byte report. The corrected Typst source uses a roman paper-title
  citation, removing an unused italic font subset; the PDF is now 64238 bytes.
  The typography-only candidate's extracted text matched the old report after
  whitespace normalization. The final report also documents the added tests.
  No source text was compressed, policy threshold changed or waiver applied.

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

The last root case was
`cryptanalysis::jv_isogeny_walk::tests::end_to_end_from_a_non_weak_curve_recovers_and_verifies`.
It exercises existing extension-field isogeny walking and sieving, with no
reference to the added module. It completed successfully, and the parent
command exited 0 with 5389 passes and 123 existing ignored tests. The full
482359-byte trace is local, SHA-256
`9b6f0a11eb71566010bbb7d63e02289e4b3969af92b47b7e65111004c6eb4cd8`,
and NOT_UPLOADED; the compact receipt records that storage limitation.
The later replay-helper change is covered by the complete native panel and
renewed maintained-root lint; the broad root tests do not call that helper.

The [canonical audit record](https://github.com/isogeny-labs/crypto/blob/main/problems/hashed-ecdl-tensor-backend.md)
keeps independent general correctness and complexity obligations open. No
benchmark, leaderboard, frozen run or curve/route evidence is changed.
