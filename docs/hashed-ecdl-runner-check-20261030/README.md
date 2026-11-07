# Hashed ECDL runner selection and standalone verification

The documented `cargo run --locked --release -- ...` commands failed after
`hashed-ecdl-panel` became the crate's second binary. Both pinned repositories
returned exit 101, listing `hashed-ecdl` and `hashed-ecdl-panel`.
Adding `default-run = "hashed-ecdl"` under `[package]` restores the documented
commands. Explicit `--bin hashed-ecdl-panel` selection remains available.

## Sources and scope

Reviewed the existing crate README, native implementation/workstream reports,
and [open general-audit record](../../problems/hashed-ecdl-tensor-backend.md).
The native implementation names Bochum v0.2 revision
`1ee44e562b1b9a50ea339f3b8f81112b5a24b96f` and OpenAI Appendix D revision
`7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a`; this check supplies no new proof
of either manuscript. The [official Cargo reference](https://doc.rust-lang.org/cargo/reference/manifest.html#the-default-run-field)
defines default-run as the binary selected by cargo run when several exist.

Snapshots were fetched through the GitHub connector at these immutable revisions:

| Repository | Revision | Standalone crate |
| --- | --- | --- |
| crypto | `4b1834891e78ca3f83b64540717042e0569d2a60` | `crates/hashed-ecdl-tensor` |
| cryptanalysis | `0fd71e100cef049176895395d7ecd0bda780f55b` | `bindings/rust/hashed-ecdl-tensor` |

All 51 downloaded file blobs were checked against Git's blob SHA before the
one-line manifest edits. [Source inventory](source-manifest.json) records those
original blobs; the modified manifest in each repository has Git blob SHA
`200a345ae1605680c3e6eb648e213d99f4ecba69` and SHA-256
`4468c86b8a971e1ae62390a7b098e5da922d91c7a4a4b21741e19344a1d2e1bb`.
No Rust implementation, fixture, dependency version or lockfile changed.

The snapshots are not byte-identical mirrors: six Rust files differ.
The contraction/network changes and one reduction-test flag correspond to the
pruning follow-up in [crypto #2915](https://github.com/isogeny-labs/crypto/pull/2915),
which was open when inspected, and merged cryptanalysis #1307. The other
differences concern stricter JSON handling in the runner, curve and
serialization modules; cryptanalysis also has a strict-JSON integration test.
These existing differences were preserved.

## Commands and observed results

Development host: Linux 6.18.55 x86-64, glibc 2.41;
rustc 1.99.1 (`58cf8f9c35b355199727627d07ae34a4e2846d67`).
Both native suites ran concurrently as correctness checks. Their elapsed
times and work counters are not benchmark comparisons.

From each standalone crate directory:

```sh
cargo test --release --locked
cargo fmt --all -- --check
cargo clippy --locked --offline --all-targets -- -D warnings
cargo run --locked --release -- validate examples/eccp131-certified.json
```

| Check | crypto | cryptanalysis |
| --- | --- | --- |
| Existing library tests | 34 passed | 37 passed |
| Runner tests | 0 | 5 passed |
| Panel tests | 3 passed | 3 passed |
| Strict-JSON integration tests | absent | 3 passed |
| Total executed tests | 37 passed, zero failed/ignored | 48 passed, zero failed/ignored |
| Formatting | exit 0 | exit 0 |
| Strict all-target Clippy | exit 0 | exit 0 |
| Default runner, before fix | exit 101, ambiguous binary | exit 101, ambiguous binary |
| Default runner, after fix | exit 0, validated | exit 0, validated |

The library suites include complete tiny relation/certificate replay,
corrupted-proof rejection, independent arithmetic/graph controls and forced
recursive versus direct counts. The manifest edit affects run selection only;
the Rust source tested is unchanged. Parameter validation reports
`charged_steps: 5589` and `challenge_solved: false` in both snapshots.

Raw results: [crypto tests](crypto-test-results.txt),
[cryptanalysis tests](cryptanalysis-test-results.txt),
[before fix](runner-before.txt),
[crypto fixed runner](crypto-default-run-results.txt),
[cryptanalysis fixed runner](cryptanalysis-default-run-results.txt),
[crypto Clippy](crypto-clippy-results.txt),
[cryptanalysis Clippy](cryptanalysis-clippy-results.txt).

No parent workspace, C/FFI integration, Rust 1.78 build, Lean proof,
scientific experiment or performance comparison was rerun here.
These standalone checks supplement the historical receipts rather than
replacing or broadening their claims. Conductor was absent (exit 127);
the documented unavailable-binary behavior in
[CONDUCTOR.md](https://github.com/isogeny-labs/crypto/blob/4b1834891e78ca3f83b64540717042e0569d2a60/docs/CONDUCTOR.md)
permits development edits without a reservation.

## Remaining original requirements

| Requirement | Status after this check |
| --- | --- |
| Locate and run the uploaded native code | Verified on both standalone snapshots |
| Make the documented cargo run command select the solver | Fixed and checked; publication/merge tracked by the paired PRs |
| Arbitrary-precision fields and automatic prime preprocessing | Implementations present, including AKS and optional checked Pocklington proofs; bounded controls passed |
| General tensor theorem and full implementation/time/space correspondence | Open, as recorded in the existing audit problem |
| Practical cryptographic or challenge solve | Not established by this work |

The source constants select exact finite-size fallback on addressable networks.
Forced small recursion controls and passing unit tests do not establish the
claimed subexponential bound. No challenge scalar was recovered by these checks.
