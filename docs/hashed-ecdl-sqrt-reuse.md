# Hashed-ECDL square-root setup reuse

2026-10-30. The native factor-base enumerator now retains Tonelli–Shanks
setup for a batch of point decodings. For primes congruent to 3 modulo 4,
root extraction uses one modular exponentiation followed by an exact square
check. These are classical implementation changes. This record establishes
correctness and reduced repeated work on unit fixtures; wall-time performance
and the full reduction's complexity remain unmeasured here.

## Sources and implementation

Before editing, reviewed the existing native arithmetic, point decoder,
factor-base enumeration, strict-input receipts and source-linked tensor docs.
The [pinned Bochum v0.2 source](https://github.com/bochum-crypto/subexponential-ecdl/tree/1ee44e562b1b9a50ea339f3b8f81112b5a24b96f),
section 3.5, lists the base by inverse hash, solving `y² = x³ + ax + b`
and selecting the root of the encoded parity. It cites the
[Handbook of Applied Cryptography, chapter 3](https://cacr.uwaterloo.ca/hac/about/chap3.pdf),
Algorithm 3.34 and Fact 3.35. The modulus decomposition, a sampled quadratic
nonresidue and its initial power depend only on the prime, so they can serve
every extraction for that prime. Algorithm 3.36 gives the exponent `(p+1)/4`
when `p ≡ 3 mod 4`; squaring the candidate rejects nonsquares directly.

`arithmetic::SquareRootContext` borrows one fixed odd prime and lazily stores
its decomposition and the successfully computed initial nonresidue power.
Each extraction clones that initial power before updating the local
Tonelli–Shanks state. Storage is O(log p) bits, with no root table. The caller
still supplies randomness and certifies primality. Zero needs no setup;
nonsquares do not sample a nonresidue. Random-source failures and resource
exhaustion propagate as errors. Every nonzero call checks its own meter's
bit bound, including calls after setup is cached.

`curve::PointDecoder` binds that context to one certified curve.
`FactorBase::enumerate` creates one decoder for its loop. Encoding range,
coordinate parity, equation replay, subgroup membership, sorting and
duplicate rejection retain their existing checks. The existing one-shot
`square_root` and `Curve::decode` APIs remain available.

Fewer random draws can change later seeded query histories and diagnostic
counts. A seed reproduces an execution only with the same source version.
The certificate wire format and verifier equations are unchanged, and the
previous stored scalar-4 receipt still replays. Frozen receipts and source
manifests retain their historical bytes.

## Validation

All five new tests run in the full release panel:

- On the public 19-point curve over F17, independently enumerating `[1..18]G`
  gives exactly the same 18 sorted nonidentity points as decoding and inverse
  hashing. A controlled test RNG is called 18 times by separate decoders and
  once by the batch decoder. The old enumerator fails the new one-call
  assertion; the final implementation passes it.
- Independent residue tables for primes 3, 5, 7, 17, 19, 43, 97 and 257 match
  reused extraction in both input orders. Every returned root is squared and
  checked. This also exercises reuse after the local state has changed.
- Lazy setup, zero and nonsquare handling, random-source failure and retry,
  noncanonical inputs, new narrower bit bounds and exhausted work budgets
  are covered. A separate fixture checks one setup versus six one-shot setups.
- For F7, both a square and a nonsquare fit the existing abstract five-step
  budget for one two-bit modular exponentiation. The earlier two-exponent
  path fails that test. These meter and RNG observations are unit diagnostics,
  not measured CPU ratios.

| Check | Final result |
| --- | --- |
| `cargo test --locked --release --manifest-path bindings/rust/Cargo.toml -p hashed-ecdl-tensor -p cryptanalysis` | exit 0; 32 core + 5 runner + 3 strict-JSON + 20 binding + 19 FFI + 14 documentation tests, all 93 passed |
| Same packages, strict all-target Clippy | exit 0 |
| Same packages, Rust 1.78.0 all-target check | exit 0 |
| Strict API documentation, `RUSTDOCFLAGS='-D warnings'`, `--no-deps` | exit 0 |
| Formatting | exit 0 |
| Rebuilt native CLI, replay existing scalar-4 receipt | exit 0; `certificate verified: scalar 4` |

The [compact transcript](hashed-ecdl-sqrt-reuse-tests.txt) preserves the
initial missing-import compilation error, both reproduced regression
failures, final panel, lint, compatibility, documentation and replay output,
with original byte counts and SHA-256 digests. No assertion, validation gate,
dependency or resource limit was weakened. This Linux x86-64 development
container supplies correctness evidence only. No benchmark, external-tool
comparison, research experiment, challenge solve or cloud resource was run.
The [earlier strict-input record](hashed-ecdl-tensor-input-validation.md)
remains a historical snapshot; its crypto root result is not reused here.

## Source identity and remaining work

This change starts from cryptanalysis merge
`cf35a825b25c3f1ece5d7d36dd98d78ea66a4022`. The new
[17-file manifest](hashed-ecdl-sqrt-reuse-sources.sha256) covers the native
Cargo, source and test files. Its SHA-256 is
`07014e0ba3f11e3624ec42d630f23b90d7e83159d477cfbb88a95ed80b6b4fdc`.
Verify it from `bindings/rust/hashed-ecdl-tensor` with
`sha256sum -c ../../../docs/hashed-ecdl-sqrt-reuse-sources.sha256`.

The new square-root, decoder and enumeration fragments match crypto
`c84df306cc583957f8351ff233c50ef422900697` byte for byte; fragment hashes are
in the transcript. Whole crate trees differ because crypto main separately
added prime certificates, canonical witnesses and a bounded GPU-base hook.
Those unrelated features were preserved there rather than ported here.

Conductor checks returned 127 because the executable is absent. The documented
warn-and-allow fallback in crypto's `docs/CONDUCTOR.md` applies; no shared
reservation or remote artifact upload is claimed. CI and review must pass
on the published head before normal guarded MERGE.

Full independent theorem and complexity audit remains open in the
[canonical problem](https://github.com/isogeny-labs/crypto/blob/main/problems/hashed-ecdl-tensor-backend.md).
This refactor adds no new theorem or Lean proof, end-to-end speed claim,
fastest-tool comparison, sub-rho result or deployed-curve claim.
