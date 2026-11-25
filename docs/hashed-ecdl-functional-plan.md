# Exact rejection pruning for hashed ECDL functional leaves

Continuation started 2026-10-29 (America/Los_Angeles), source base
`bd4c2fe5e6f` in `crypto`, Conductor T-873. This is native implementation
and fixed software correctness testing, not a scientific timing run.

## Requested scope and chosen increment

Continue the Boolean tensor-contraction / hashed-factor-base ECDL algorithm.
The current implementation already has certified primality and canonical
single-pass witness search. Improve its finite-size functional fallback by
skipping assignments certified to fail the same earlier constraint. Preserve
the actual recursive backend, source parameters, exact counts, interface
ordering, hash distributions, independent replay and resource-error behavior.
Retain the unpruned implementation as an explicit control.

## Sources checked before implementation

- [Bochum v0.2, pinned source](https://github.com/bochum-crypto/subexponential-ecdl/blob/1ee44e562b1b9a50ea339f3b8f81112b5a24b96f/subexponential-ecdl.pdf),
  Section 2 definitions and Lemma 1: contraction counts satisfying full edge
  assignments; prefix restrictions select a language word. Section 3's
  parsimonious gadgets justify a unique extension of built-in free inputs.
  Read the full relevant definitions and prefix-count proof from the PDF.
- `crates/hashed-ecdl-tensor/src/network.rs`: private Program metadata,
  deterministic Define/Check steps and independent full-graph evaluation.
- `crates/hashed-ecdl-tensor/src/contraction.rs`: exact functional leaf,
  lexicographically ordered witness search and retained prefix-count control.
- `crates/hashed-ecdl-tensor/src/reduction.rs`: seeded relation collection and
  complete-certificate equality regression. Both copies must stay identical.
- `docs/session-logs/2026-10-30.md`: the separate ecdl-tensor-ic measurement
  campaign is already owned elsewhere. This task does not duplicate it.

This is a standard dependency-based search pruning optimization, with no
novelty claim and no claim to change the manuscript's asymptotic bound.

## Soundness invariant

For a fixed enumeration order, digit zero changes fastest. Assign each free
signal its digit position and each constant or pinned free input the sentinel
position n. Each Define output conservatively inherits the minimum position
among all inputs, transitively; a Check inherits the minimum among its ports.
Thus a rejection at position k is independent of digits 0 through k-1.
Reset these lower digits and increment the suffix starting at k. This skips
only the remainder of the contiguous rejected block. A sentinel rejection
ends the enumeration, since no remaining input can affect it. Successful
assignments always advance by one, so multiplicities are retained exactly.

Dependency propagation deliberately does not treat a pinned derived signal
as constant: its computation must still meet that pin. All returned witnesses
still undergo the existing full graph evaluation. Arbitrary GraphBuilder
predicates cannot obtain Program metadata and retain the original path.

Counts may use reverse free-input order to expose early independent checks;
witnesses retain interface-priority order and derived-interface minimum search.
Preparation and visited assignments are charged to Meter. Resource exhaustion
remains Error::Limit, never UNSAT. Diagnostics count only visited assignments
and rejected blocks, not invented work for skipped candidates.

## Fixed validation contract, written before code changes

1. Native library tests and existing exact edge-enumeration controls pass.
2. Exhaustively compare pruned and unpruned counts and canonical witnesses
   over a small asymmetric network with transitive dependencies, unused free
   inputs, aliases, derived interface pins and all ternary pin combinations.
3. Include constant rejection, no-free-input networks, contradictory aliases,
   output pins, successful multiplicities and step-budget exhaustion.
4. Preserve byte-identical full seeded ECDL certificates, then independently
   replay their group equations and recovered scalar on public tiny fixtures.
5. Add a regression proving that an irrelevant-input block is actually skipped
   and the unpruned control still visits it. This is a software work counter,
   not calibrated runtime or an end-to-end speed result.
6. Run strict Clippy, formatting and Rust 1.78 checks. Mirror native sources
   into cryptanalysis and validate its native integration before delivery.

No benchmark, paid job or challenge solve is launched by this validation
contract. A later runtime claim needs a frozen matched protocol, native EKS
admission, complete costs, replay and the existing reference arms. The general
ECDLP improvement objective remains open after this implementation increment.

## Outcome

Implemented in `network.rs`, `contraction.rs` and the retained control in
`reduction.rs`. These three files are byte-identical in the paired
cryptanalysis worktree based on `b14932651dcf9df2ba346fdc7efdb63b68904475`.
Other pre-existing differences between the repository bases (strict JSON
input handling) are retained; this is not a claim that the entire crate trees
have identical bytes at these two bases.

| Requirement | Outcome and evidence |
| --- | --- |
| Exact counts and canonical witnesses | Verified: all 37 native library tests pass in each repository, including the new 81-pin comparison and independent existing graph controls. |
| Seeded full ECDL certificate and algebraic replay | Verified: `tensor_relation_pipeline_recovers_and_replays_without_scalar_leakage` passes against the original unpruned prefix-count control; the complete certificate is equal and independently replayed. |
| Rejection actually skips inputs | Verified in the fixed native fixture: exhaustive witness search visits 17 inputs; pruning visits 2 and records one rejected block. Both return `[true, false, false, false, false]`. Counting retains all 16 successful assignments, visits 17 inputs and returns exactly 16. These are regression assertions, not runtime measurements. |
| Input and binding integration | Verified in cryptanalysis: 5 runner, 3 strict-JSON, 20 binding-unit, 19 FFI-parity and 14 documentation tests pass. |
| Formatting, strict Clippy, Rust 1.78 | Verified for both native crate copies and cryptanalysis binding checks. |
| Broad crypto root library suite | Tracked separately in the paired crypto report; this is not a cryptanalysis workspace check. Its compile-time fixtures required sparse materialization. No broad crypto pass is claimed here. |
| Runtime / larger ECDLP improvement | Not measured. Preparation overhead, low-pruning cases and ordering tradeoffs require a matched experiment before making a speed claim. |

The native default remains exact. `functional_pruning = false` restores
exhaustive enumeration; also set `functional_witnesses = false` for the
original prefix-count control. Dependency preparation costs resource budget;
a tight budget can fail earlier, and Error::Limit is still not UNSAT.

The seeded certificate regression uses the public synthetic short-Weierstrass
curve `y^2 = x^3 + 2x + 1` over F_5, generator `(0,1)`, subgroup order 7,
target `[4]G`, seed 1 and a two-billion-step software-test budget. It requires
the same complete certificate (13 relations) from both paths. This is a
correctness fixture, not an unknown-scalar challenge or a scaling result.
The three pruning regressions also use tiny constructed Boolean networks;
their counts do not depend on an elliptic-curve parameter choice.

### Reproduce the checks

From crypto:

```sh
cargo test --locked --release --manifest-path crates/hashed-ecdl-tensor/Cargo.toml
cargo clippy --locked --all-targets --manifest-path crates/hashed-ecdl-tensor/Cargo.toml -- -D warnings
cargo +1.78.0 check --locked --all-targets --manifest-path crates/hashed-ecdl-tensor/Cargo.toml
cargo fmt --manifest-path crates/hashed-ecdl-tensor/Cargo.toml -- --check
CARGO_BUILD_JOBS=2 cargo test --release --lib
```

From cryptanalysis `bindings/rust`, the following package pairs were checked
in separate invocations (same locked workspace):

```sh
CARGO_BUILD_JOBS=2 cargo test --locked --release -p hashed-ecdl-tensor -p cryptanalysis
CARGO_BUILD_JOBS=2 cargo clippy --locked -p hashed-ecdl-tensor -p cryptanalysis --all-targets -- -D warnings
CARGO_BUILD_JOBS=2 cargo +1.78.0 check --locked -p hashed-ecdl-tensor -p cryptanalysis --all-targets
cargo fmt --package hashed-ecdl-tensor -- --check
```

Stable compiler: `rustc 1.99.1 (58cf8f9c3 2026-10-13)` on the shared x86-64
development host. No timing isolation is claimed. No scientific job,
challenge solve or measurement checkpoint was started; these were local
software checks. The root build initially lacked sparse local dependencies;
the binding build initially lacked `cuda/ca_device.cuh`. The required paths
were materialized before retrying, without changing their contents.

### Source and visual evidence

The following SHA-256 digests agree across the two modified native copies:

| Source | SHA-256 |
| --- | --- |
| `src/network.rs` | `55accd8c18a9c94cdeee19568da1517b9fca7b0661044eef3b4dde8feaf388a0` |
| `src/contraction.rs` | `8ad7339b241205d52ff62fb04042c3bc4098b79928589cbe28735dfdee1fed4c` |
| `src/reduction.rs` | `43f1b2f5c7768d8bd5921698f8375cc3a4b85962395e21209fcc2b8347f47dba` |

See the [validation transcript](hashed-ecdl-functional-validation.txt),
[editable diagram](hashed-ecdl-functional-pruning.svg),
[rendering source](hashed-ecdl-functional-pruning.typ) and
[inspected one-page PDF](hashed-ecdl-functional-pruning.pdf).

The existing IC scoreboard and leaderboard were checked for relevant hashed
ECDL/functional entries. No validated runtime or curve-coverage result is
added, so their data and plots remain unchanged. Existing frozen source
manifests and historical receipts are retained unchanged.
