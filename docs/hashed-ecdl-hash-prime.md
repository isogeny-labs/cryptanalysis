# Checked hash-modulus setup

`Curve::with_cofactor_and_certificates` now retains its checked prime facts for
auxiliary hash moduli. Factor-base construction and replay reuse those facts;
uncovered values retain exact primality. Optional `Config.hash_prime` / problem
JSON `hash_prime` declares a fixed modulus, as permitted by the source's section
3. Its interval, primality, seed and resource checks remain mandatory.

Use `examples/eccp131-certified-hash.json` with the native runner's `validate`
mode for the supplied p/r/target/s preflight. This validates setup only. The
132-bit hash modulus is checked with one additional Pocklington node. The
original two-million-step policy is preserved; the development control charges
5,897 diagnostic steps. No elapsed-time gain or challenge solve follows.

The public native `prepare-certified-hash` example reproduces the extra proof
using bounded candidate proofs and the ordinary exact verifier. Proof preparation
cost is separate setup work and belongs in any future cold measurement.

Omitting `hash_prime` preserves the previous random candidate stream. Declaring
it explicitly removes random-prime draws and defines a distinct configured
input; do not silently change the frozen comparison panel. Receipt replay checks
the declared pin for nonidentity targets. The general >u64 AKS fallback and
literal recursion cutoff remain unchanged.

The complete source-linked report, diagram, inspected PDF, raw validation and
source hashes are in
[the pinned crypto study](https://github.com/isogeny-labs/crypto/blob/edfadbab5ac71471be7fd2971a9e50825307363f/research/hashed_ecdl_hash_prime_20261030/README.md).
The native fixture/preparer/tests are mirrored in cryptanalysis; that repo's
independently landed input hardening and functional pruning are preserved.

This integration's complete native source context is pinned in
[hashed-ecdl-hash-prime-sources.sha256](hashed-ecdl-hash-prime-sources.sha256).
