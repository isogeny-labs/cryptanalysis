# Hyperelliptic cover infrastructure

This directory records the bounded library mirror from
[`isogeny-labs/crypto`](https://github.com/isogeny-labs/crypto/tree/333c0f0a2390c57f245730ab9294e7ee905d9cd3).
The updated binary files are pinned to implementation commit
`333c0f0a2390c57f245730ab9294e7ee905d9cd3`; unchanged prime-field files
retain their original source revision in the machine-readable manifest.
The upstream
[audit and evidence](https://github.com/aburan28/crypto/tree/d167ce0af49c22947b6d40f373b35df75e13e82e/research/hyperelliptic_cover_infrastructure_20261006)
separate curve construction, Jacobian arithmetic, transfer, subgroup
preservation, and measured advantage. The upstream standalone
[`hyperelliptic-cover`](https://github.com/isogeny-labs/crypto/blob/333c0f0a2390c57f245730ab9294e7ee905d9cd3/src/bin/hyperelliptic_cover.rs)
command exposes the certificate replay and structured arithmetic interface.
This mirror intentionally adds no solver, CLI, or generated catalog.

## Supported boundary

- `binary_cubic_pullback_v1` constructs and checks the same-field separable
  degree-three map from its genus-three, one-infinity binary source to an
  ordinary binary elliptic curve. The library supports checked Mumford
  arithmetic, rational source-point pushforward, pullback of rational
  elliptic point classes, arbitrary valid reduced degree-at-most-three class
  pushforward through closed-point residue fields, typed witnesses for
  `phi_* phi^*([P]-[O]) = [3]([P]-[O])`. Pullback is injective only if the
  supplied integer is independently established as the exact subgroup order
  and is coprime to three; the API does not prove that caller precondition.
  When three divides the order, the kernel intersection remains unresolved.
  Image-endomorphism and normalized torsion-projector certificates check their
  stated identities for the supplied class; they do not establish the supplied
  order. The exhaustive 486-class `GF(8)` table remains a separate control for
  its one fixed model. Other models use the general residue-field path and do
  not thereby gain an independent map oracle. [pcc:unverified]
- Odd-characteristic arithmetic accepts only deterministically validated odd
  prime moduli of at most 64 bits and smooth monic squarefree models of exact
  degree `2g+1`, with one rational point at infinity. Its exhaustive
  `F_{p²}` counter uses an immutable, checked nonresidue context and the
  explicit `p ≤ 4096` enumeration bound. It explicitly rejects the upstream
  `prime_quadratic_pullback_v1` genus-two sextic: that source has two rational
  points at infinity and needs a different Jacobian representation.

Generic pullback/pushforward across other cover families, prime
even-degree/two-infinity induced maps, full-Jacobian relation collection or
target decomposition, production key recovery, calibrated costs, matched rho,
and any end-to-end speedup are unsupported or not established. A bounded
unsupported result is not a nonexistence result. [pcc:unverified]

## Quartic PR #290 is a separate norm projection

Cryptanalysis [PR #290](https://github.com/aburan28/cryptanalysis/pull/290),
paired with crypto [PR #1389](https://github.com/aburan28/crypto/pull/1389),
studies the genus-three **nonhyperelliptic plane quartic**
`C: v^4 = x^3 + ax + b` and `pi(x,v) = (x,v^2)` over tiny prime fields.
It certifies complete line sections, but forms its linear system only after
elliptic norm projection. Its columns identify projected elliptic images,
not divisor classes in the full `Jac(C)`; deck-conjugate divisors can differ
in the Prym component. The retained fixture and controls therefore establish
bounded norm-projection correctness, not a hyperelliptic construction,
full-Jacobian index calculus, scaling, or a speed result. See the mirrored
[`quartic kernel`](../../suite/src/cryptanalysis/bielliptic_quartic.rs),
[`quartic-ic` command](../../suite/src/bin/quartic_ic.rs), and
[`replay check`](../../tools/check_bielliptic_quartic.mjs).

## Source parity

The current binary implementation source is crypto commit
`333c0f0a2390c57f245730ab9294e7ee905d9cd3`; the original audit baseline is
`5874ce8b393dccc4c735cc7ca5a47de7fe196c59`. Unchanged prime-field files remain
bound to `3b8664a466efd56121509cd77866a07e3cb55741`. The SHA-256 values below record
the mirrored file identities. From the repository root, run
`cargo run --locked --manifest-path suite/Cargo.toml --bin hyperelliptic-source-parity --`
to check the local mirror. Append `--crypto-root PATH` after `--` to load every
source file with `git show <file.source_commit>:<source_path>` from a crypto
checkout and compare the recorded source bytes.

| Crypto source | Source revision | Cryptanalysis mirror | SHA-256 status |
| --- | --- | --- | --- |
| `src/binary_ecc/hyperelliptic.rs` | `333c0f0a2390c57f245730ab9294e7ee905d9cd3` | `suite/src/binary_ecc/hyperelliptic.rs` | exact: `816d2316e80b74220b912ff0c3cfc8d1173d67aacc945fff4a2e63c5afa59c15` |
| `src/binary_ecc/cover_transfer.rs` | `333c0f0a2390c57f245730ab9294e7ee905d9cd3` | `suite/src/binary_ecc/cover_transfer.rs` | exact: `bfddf75758b9a4e11af1944b84e40cda4dd35c557776ae8c05df9892bd3b4909` |
| `src/binary_ecc/mod.rs` | `333c0f0a2390c57f245730ab9294e7ee905d9cd3` | `suite/src/binary_ecc/mod.rs` | adapter: source `154732fb1266bd55dfbc2d198ce94ea7cfce420ed0196c006bf6988425d0f727`, mirror `5319e0357e47a9815ac833c33a351e5318d124f965baa87fd4b1a7b821f2497e` |
| `src/prime_hyperelliptic/curve.rs` | `3b8664a466efd56121509cd77866a07e3cb55741` | `suite/src/prime_hyperelliptic/curve.rs` | exact: `7a769bfb7abfe92ce06da7c02340f2a2426827d8066ebef510375149b8c3d5ad` |
| `src/prime_hyperelliptic/fp2.rs` | `3b8664a466efd56121509cd77866a07e3cb55741` | `suite/src/prime_hyperelliptic/fp2.rs` | exact: `b833bdff5247f2eea0cde7feb89d0378cfe8305671f9065d2dae7ab538c03e55` |
| `src/prime_hyperelliptic/mod.rs` | `3b8664a466efd56121509cd77866a07e3cb55741` | `suite/src/prime_hyperelliptic/mod.rs` | exact: `b6906f75b4d0eb6b7ac406a0fca1b2cef1786a528d4aedbab414e9fa1e7f7662` |
| `src/prime_hyperelliptic/fp_poly.rs` | `3b8664a466efd56121509cd77866a07e3cb55741` | `suite/src/prime_hyperelliptic/fp_poly.rs` | selected domain-binding adapter: source `b5d1a1ba5e95d8d0dd06b71757567fb559adbdd09b1ab623ae76e0049ee593c2`, mirror `44f7af14d22bed78d85c4bd009ccce7197fa9257e7ff56164c8d891303e49590` |

The binary module adapter preserves two existing unlinked rustdoc references,
omits crypto-only `efd`, operation-tally, and trace-zero modules, and retains
the cover/Jacobian exports used by this mirror. Its remaining bytes match after
those declared transformations. The polynomial adapter
ports the required coefficient-field equality guard and regression test,
while preserving cryptanalysis's pre-existing lack of crypto's unrelated
`pow_mod` helper. Exact machine-readable identities and adapter rules live in
[`source-parity.json`](source-parity.json).
