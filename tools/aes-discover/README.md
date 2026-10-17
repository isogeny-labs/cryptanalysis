# AES discovery laboratory

A native Rust binary for **discovering candidate differential distinguishers and
testing frozen candidates on fresh plaintexts and fresh, individually reported
keys**. It also supplies component and structural experiments. This is research
software using public synthetic fixtures and table-based AES.

```sh
cargo build --release --locked --manifest-path tools/aes-discover/Cargo.toml
cargo test --release --locked --manifest-path tools/aes-discover/Cargo.toml
tools/aes-discover/target/release/aes-discover --help
```

Rust 1.87+ and OpenSSL (for the independent correctness tests) are required.
The standalone crate deliberately avoids compiling unrelated algebra/ECDLP
engines. Its sources and lockfile are mirrored byte-for-byte between
`aburan28/crypto` and `aburan28/cryptanalysis`; `crypto` is the source of truth
after this coordinated change. Changes must update both and check SHA-256 parity.

## Discovery and validation

```sh
BIN=tools/aes-discover/target/release/aes-discover
"$BIN" discover --rounds 3 --seed 100 --validation-seed 200 \
  --candidates 48 --samples 512 --keys 2 --top 8 \
  --validation-samples 8192 --validation-keys 8 --out candidates.json
sha256sum candidates.json
# Paste the printed digest, binding the exact bytes including the trailing newline.
"$BIN" validate --spec candidates.json --expect-sha256 DIGEST --out validation.json
```

Discovery explores single-byte input differences first, then seeded differences
with more active bytes. For every input difference it searches byte equalities
and bit equalities of XOR projections of single bytes, columns, rows, diagonals
and the whole state. It retains the best event per input difference and the
requested number of input/event candidates. These are **empirical endpoints**,
not intermediate differential trails. Discovery scores are exploratory.

The candidate artifact fixes the cipher, event, direction, discovery key IDs and
the **entire subsequent validation plan**: seed, fixed sample count, key count,
alpha, and primary oracle. Validation accepts no statistical tuning flags. Both
the CLI and library bind the validated object to the frozen bytes. Every output
file uses exclusive creation; reuse a fresh directory for a new run.

Each validation key is fixed across its queries. Validation keys and streams
are disjoint from discovery. Input pairs are disjoint, including reversed pairs,
across the complete event family within each key. The matched control is a lazy
random permutation with consistent forward and inverse maps, sampled without
replacement. Every candidate/key pair has raw primary/control counts, effect,
query counts, and a transcript hash. Seeds reproduce public keys and transcripts;
they are not secret-key generation or a substitute for independent final testing.

For a nonempty XOR projection of distinct bytes and a mask of rank `r`, the
ideal output-difference probability is
`(2^(128-r) - [target=0]) / (2^128 - 1)`. The implementation uses its numerically
stable normalized form. It reports a **two-sided Chernoff upper bound**, not an
exact p-value or a normal approximation, adds a conservative finite-query PRP
collision-coupling slack, and applies Bonferroni across **both arms, all frozen
events and all validation keys**. The slack uses all queries for that key, not
just a favorable row. Tests in multiple separate specs need an additional
campaign-level alpha allocation, frozen before execution.

A candidate is listed only if its frozen direction passes on **every tested
key**, and the matched random-control family passes. This does not establish a
universal key-independent property. A failed null control withholds the entire
family. The Hoeffding deviation threshold and sufficient effect for 80% power
are explicitly IID-model sensitivity diagnostics; they do not assert empirical
power, account for unknown alternative dependence, or turn a null result into
security. Repeated use of the same holdout to revise an event is prohibited by
the experiment protocol, not magically prevented by a file hash.

## Commands and boundaries

| Command | What it produces | What remains separate |
| --- | --- | --- |
| `tables` | Exact AES S-box DDT/LAT/BCT enumeration summaries | BCT excludes zero differences only; the nonzero diagonal is included |
| `trail` | Value-level, bounded beam proposals with round states, DDT weights, expanded/discarded counts | Local DDT products are model scores, not fixed-key probabilities, hull bounds, feasibility or optimality certificates |
| `discover` | Input difference, output predicate, direction and frozen validation plan | Search ranking is not an inferential result |
| `validate` | Per-key replication, raw counts, conservative bounds, PRP control | No new event search, optional stopping or pooling-only conclusion |
| `integral` | 256-text XOR sums, matched PRP and one-member mutant | Known integral reproduction, no new invariant theorem |
| `quartets` | Inversion/cross-ratio check and real affine-map/random-bijection ablations | Local component check; not the complete 2026/1549 construction |
| `schedule` | One-bit key-expansion differences for AES-128/192/256 | Related-key diagnostic; no ordinary single-key attack |
| `boomerang` | Fixed input/output-delta return counts and trivial-swap counts | Requires forward/inverse oracle access; no adaptive choice of observed delta and no significance claim |
| `dataset` | JSONL pairs and a hashed sidecar with key-disjoint train/validation/test streams | No training or neural-performance claim; exclude metadata and labels from features |
| `encrypt` | FIPS/reference known-answer fixture | Full rounds with final MixColumns omitted match standard AES |

Every cipher artifact records key size, rounds and final-MixColumns convention.
All states are column-major (`index=4*column+row`), with initial whitening and
the corresponding AES key schedule. Standard AES uses 10/12/14 rounds with
`final_mix_columns=false`; retaining the last MixColumns defines a different
permutation. The laboratory supports both conventions, explicitly.

The PRNG is ChaCha20 with SHA-256 domain separation, reproducibly seeded for
public experiments. It approximates experimental randomness; no claim relies on
the public fixture generator being unpredictable to an adversary.

## First experiment suite

See the frozen protocol and runner in
[`experiments/aes-distinguisher-lab-20261017`](../../experiments/aes-distinguisher-lab-20261017/README.md).
The runner records exact argv, binary/source/protocol hashes, environment,
timestamps, stdout/stderr and exit status. Results are engineering observations
outside existing official AES campaign arms; no ledger or scientific status is
changed. The source-linked open-angle assessment and remaining experiments live
in the companion `crypto-autoresearcher` study.

There is no SAT/MILP proof backend, exhaustive full-AES trail search, GPU path,
learned model training, complete DS-MitM/biclique attack, or claimed full-AES break
in this version. Those are explicit follow-up hypotheses, not hidden capabilities.
