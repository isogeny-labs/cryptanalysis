# Hyperelliptic cover infrastructure

This directory records the bounded library mirror from
[`isogeny-labs/crypto`](https://github.com/isogeny-labs/crypto/tree/6cb5ab1edb141b48b9a9767fc63fe95ba1aac217).
The updated transfer and balanced-Jacobian files are pinned to implementation
commit `6cb5ab1edb141b48b9a9767fc63fe95ba1aac217`; unchanged support files retain
their original source revisions in the machine-readable manifest.
The upstream
[audit and evidence](https://github.com/aburan28/crypto/tree/d167ce0af49c22947b6d40f373b35df75e13e82e/research/hyperelliptic_cover_infrastructure_20261006)
separate curve construction, Jacobian arithmetic, transfer, subgroup
preservation, and measured advantage. The upstream standalone
[`hyperelliptic-cover`](https://github.com/isogeny-labs/crypto/blob/6cb5ab1edb141b48b9a9767fc63fe95ba1aac217/src/bin/hyperelliptic_cover.rs)
command exposes the certificate replay, structured arithmetic, and binary
certificate-catalog interface. This mirror intentionally adds no solver, CLI,
or generated catalog. Catalog export remains owned by crypto because it binds
crypto's EC1/ICV1 registry, cover graph, schema, and packaging contract; this
repository mirrors and tests the underlying library arithmetic instead.

## Supported boundary

- `binary_cubic_pullback_v1` constructs and checks the same-field separable
  degree-three map from its genus-three, one-infinity binary source to an
  ordinary binary elliptic curve. The library supports checked Mumford
  arithmetic, rational source-point pushforward, pullback of rational
  elliptic point classes, arbitrary valid reduced degree-at-most-three class
  pushforward through closed-point residue fields, typed witnesses for
  `phi_* phi^*([P]-[O]) = [3]([P]-[O])`, and a named-generator certificate.
  For a checked nonidentity `G` and a checked annihilator `r` with
  `gcd(r,3)=1`, that certificate verifies `[r]G=O`,
  `[r]phi^*(G)=0`, and degree-inverse recovery. Those checks prove
  injectivity on `<G>` without claiming that `r` is prime or the exact order
  of `G`. The generic subgroup classifier retains its exact-order premise;
  when three divides the supplied integer, the kernel intersection remains
  unresolved.
  Image-endomorphism and normalized torsion-projector certificates check their
  stated identities for the supplied class; they do not establish the supplied
  order. The exhaustive 486-class `GF(8)` table remains a separate control for
  its one fixed model. Other models use the general residue-field path and do
  not thereby gain an independent map oracle. [pcc:unverified]
- Odd-characteristic arithmetic keeps one-infinity odd-degree curves and
  split-sextic two-infinity curves in separate representations. The balanced
  `(u,v,n_plus)` implementation supports monic squarefree genus-two sextics
  over deterministically validated prime fields of at most 64 bits. For the
  direct short-Weierstrass `prime_quadratic_pullback_v1` family, it implements
  arbitrary-class pushforward, rational-point pullback, the deck action, and
  checked identities `pi_*pi^*=[2]` and `pi^*pi_*=1+deck_*`. Its named
  generator certificate uses a checked odd annihilator and does not assert
  exact order or primality. Normalized targets, extension fields, larger
  prime fields, and nonsplit infinity remain unsupported. The exhaustive
  `F_{p²}` counter keeps its explicit `p ≤ 4096` enumeration bound.
  [pcc:unverified]

Generic pullback/pushforward across other cover families, full-Jacobian
relation collection or target decomposition, production key recovery,
calibrated costs, matched rho, and any end-to-end speedup are unsupported or
not established. A bounded unsupported result is not a nonexistence result.
[pcc:unverified]

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

The current transfer implementation source is crypto commit
`6cb5ab1edb141b48b9a9767fc63fe95ba1aac217`; the original audit baseline is
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
| `src/binary_ecc/cover_transfer.rs` | `6cb5ab1edb141b48b9a9767fc63fe95ba1aac217` | `suite/src/binary_ecc/cover_transfer.rs` | exact: `e1336ef5e5fb6ab32d58be956e72a8732adc43aca30d46a4f8ce45b03cdcdad5` |
| `src/binary_ecc/mod.rs` | `6cb5ab1edb141b48b9a9767fc63fe95ba1aac217` | `suite/src/binary_ecc/mod.rs` | adapter: source `22668e7636d35b175c80505307d40cae32f1a1b1e8bec9b1c0239bebb11b3d51`, mirror `dcf9aa0c6dee67aebf5cc8624288ceb4d6a5eabff67ebf7aecae274f741a0382` |
| `src/prime_hyperelliptic/balanced.rs` | `6cb5ab1edb141b48b9a9767fc63fe95ba1aac217` | `suite/src/prime_hyperelliptic/balanced.rs` | exact: `550675a30d344a65a067fbe927203c8085eccec1acfa19f952011c570576d464` |
| `src/prime_hyperelliptic/cover_transfer.rs` | `6cb5ab1edb141b48b9a9767fc63fe95ba1aac217` | `suite/src/prime_hyperelliptic/cover_transfer.rs` | exact: `97ffe80dd14332eb0a2854dfcafcf21d98964289366762e1f3bd8228b84d7dc3` |
| `src/prime_hyperelliptic/curve.rs` | `3b8664a466efd56121509cd77866a07e3cb55741` | `suite/src/prime_hyperelliptic/curve.rs` | exact: `7a769bfb7abfe92ce06da7c02340f2a2426827d8066ebef510375149b8c3d5ad` |
| `src/prime_hyperelliptic/fp2.rs` | `3b8664a466efd56121509cd77866a07e3cb55741` | `suite/src/prime_hyperelliptic/fp2.rs` | exact: `b833bdff5247f2eea0cde7feb89d0378cfe8305671f9065d2dae7ab538c03e55` |
| `src/prime_hyperelliptic/mod.rs` | `6cb5ab1edb141b48b9a9767fc63fe95ba1aac217` | `suite/src/prime_hyperelliptic/mod.rs` | operation-pricing adapter: source `03660be55198a76e3334a38e524ca1ea1ef4bf643ce6b5094c036f7cde7daff9`, mirror `fa36d063ddad804c97e9f8422259d39b0f113d13aa898bab593d276531f42c62` |
| `src/prime_hyperelliptic/fp_poly.rs` | `3b8664a466efd56121509cd77866a07e3cb55741` | `suite/src/prime_hyperelliptic/fp_poly.rs` | selected domain-binding adapter: source `b5d1a1ba5e95d8d0dd06b71757567fb559adbdd09b1ab623ae76e0049ee593c2`, mirror `44f7af14d22bed78d85c4bd009ccce7197fa9257e7ff56164c8d891303e49590` |

The binary module adapter preserves two existing unlinked rustdoc references,
omits crypto-only `efd`, operation-tally, and trace-zero modules, and retains
the cover/Jacobian exports used by this mirror. Its remaining bytes match after
those declared transformations. The polynomial adapter
ports the required coefficient-field equality guard and regression test,
while preserving cryptanalysis's pre-existing lack of crypto's unrelated
`pow_mod` helper. The prime-module adapter omits only crypto's operation-pricing
module; the balanced arithmetic and induced-map modules are byte-exact. Exact
machine-readable identities and adapter rules live in
[`source-parity.json`](source-parity.json).
