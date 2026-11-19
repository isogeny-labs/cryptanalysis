# Hyperelliptic cover infrastructure

This directory records the bounded library mirror from
[`isogeny-labs/crypto`](https://github.com/isogeny-labs/crypto/tree/5c6e43a6f0cffe0afc4c962ff54056716cf6437e).
The composed Montgomery degree-two cover, direct cover dependency, and
prime-module routing are pinned to implementation commit
`5c6e43a6f0cffe0afc4c962ff54056716cf6437e`. The underlying degree-one
Montgomery/short-Weierstrass model adapter remains byte-identical to producer
`e0ae0fe5d09c0492a8b50600e88d0b9da68afef1`; balanced-Jacobian and
deterministic-primality files remain pinned to
`153ac585d3b1ece0ebb0d49312b13267f651c94b`. Unchanged support and binary files
retain their original source revisions in the machine-readable manifest.
The upstream
[audit and evidence](https://github.com/aburan28/crypto/tree/d167ce0af49c22947b6d40f373b35df75e13e82e/research/hyperelliptic_cover_infrastructure_20261006)
separate curve construction, Jacobian arithmetic, transfer, subgroup
preservation, and measured advantage. The upstream standalone
[`hyperelliptic-cover`](https://github.com/aburan28/crypto/blob/153ac585d3b1ece0ebb0d49312b13267f651c94b/src/bin/hyperelliptic_cover.rs)
command exposes the certificate replay, structured arithmetic, and binary
certificate-catalog interface. This mirror intentionally adds no solver, CLI,
or generated catalog. It mirrors the reusable composed library API and bounded
public controls only. Catalog export remains owned by crypto because it binds
crypto's EC1/ICV1 registry, cover graph, schema, and packaging contract; this
repository mirrors and tests the underlying library arithmetic and generic
model isomorphism instead. [pcc:unverified]

## Crypto-owned corpus and oracle evidence

The newest mirrored library component is the typed Montgomery cover composition
from crypto revision `5c6e43a6f0cffe0afc4c962ff54056716cf6437e`; its direct cover dependency is
pinned to that same revision. The degree-one model adapter remains pinned to
`e0ae0fe5d09c0492a8b50600e88d0b9da68afef1`, while balanced arithmetic remains
pinned to `153ac585d3b1ece0ebb0d49312b13267f651c94b`. The current binary catalog
successor was cleanly regenerated from producer
`e0ae0fe5d09c0492a8b50600e88d0b9da68afef1` and is carried by final package
head `22f195741f2f68f37e56ffe134fe2b48fe172245`. The exact
`docs/curves/binary-subgroup-transfer-certificates.json` bytes are 500,924
bytes with SHA-256
`671425585e8f67e0596186fc574f2265938cd6465057d85ca1ae9844e47619cc`
and producer-source SHA-256
`73afe2092d1c065c048c5c9aa566d0c0ab606f3291230392a70697898267b870`.
The predecessor `f402ccd4...` / `74752a1e...` / `8c61e842...` corpus remains
historical in its preserved package receipt. The still earlier
`bb87d501aa763e7243f845d4f07c8a31b88435f1` receipt is superseded:
exact-head release replay proved that it had relabeled intermediate producer
output instead of regenerating every record from its named source. The clean
producer now binds the binary module routing and deterministic primality
implementation used by exact-order evidence.
The successor retains all 174 declared binary maps and 150 named bindings with zero
failed records. Exact generated order is locally proved for 102 bindings; the
other 48 remain explicitly unknown rather than being promoted from
probable-prime metadata. This repository cites those crypto-owned bytes and
does not copy them. [pcc:unverified]

Crypto evidence head `e0bb87e6e99ec8020f0c6437a4640f315fa79850`
adds a separate 17,879,352-byte odd-characteristic corpus with SHA-256
`7c60fc122c73abbe7b0df1413d24abbb064a9842bb35c2da8248d30c87f65670`.
Its clean producer is `e0ae0fe5d09c0492a8b50600e88d0b9da68afef1`, with framed source digest
`3116ef637921b9aade22bbbaa0bd5f3eaaa798e6d7517474dab912a9dc8c2768`.
It retains all 22,243 odd maps and 940 named records: 675 supported, 233
proof-range unsupported, 0 kernel-intersection unsupported, 22 normalized
backend unsupported, 9 extension backend unsupported, 1 invalid target
generator, and no other invalid or transfer-arithmetic failures. Canonical
same-implementation replay exits 1 because incomplete rows are retained;
Git-tree source replay exits 0. This repository cites those crypto-owned bytes
and does not copy the exporter, corpus, registry, graph, or schema.
[pcc:unverified]

That odd corpus predates the composed Montgomery backend and remains immutable.
The six live Montgomery maps and seven named bindings are all outside the
accepted primality-proof range, so composition promotes no live row. A future
crypto-owned successor export is expected to retain 675 supported bindings
while moving those seven records from the historical normalized-backend bucket
to the proof-range bucket: 240 proof-range unsupported, 15 Edwards-backend
unsupported, 9 extension-backend unsupported, and 1 invalid generator. This is
a disposition correction, not new subgroup support. [pcc:unverified]

Crypto revision `153ac585d3b1ece0ebb0d49312b13267f651c94b` retains a
separately implemented exhaustive Picard-class oracle for the one exact
fixture `y^2=x^6+1` over `F_5`. It checks all 36 classes, all 1,296 ordered
sums, exceptional support, target arithmetic, and both transfer compositions
before comparing with production arithmetic. It is producer-side
code-path-independent evidence for that fixture, not an independent review or
general genus-two certificate. The generic F5 and shifted F7 source-law
oracles remain open. [pcc:unverified]

That producer revision also adds a separate exact `F_2` control for
`E: y^2+xy=x^3+1`, `H: v^2+u^2v=u^7+u`, and
`phi(u,v)=(u^3,uv+1)`. It constructs 20 source classes from principal
divisors without production Jacobian addition, checks all 400 ordered sums
and all 8,000 associativity triples, independently implements both maps, and
checks both composition identities before comparison with production. This is
partial independent source-law evidence for one tiny general-path fixture.
Crypto producer `e0ae0fe5d09c0492a8b50600e88d0b9da68afef1` separately freezes a
non-production fixed-`GF(8)` oracle that constructs all 486 source classes,
checks all 114,791,256 associativity triples and 236,196 ordered transfer
pairs, and records the fixture-specific `L(9*infinity)` completeness argument.
Its clean Rust 1.98 replay and resource receipt remain a local unsigned draft,
not signed review or catalog-wide support. Both test sources remain
crypto-owned and are not copied here. [pcc:unverified]

The earlier exact-head package replay is preserved as historical evidence in
[the 2026-11-18 receipt](package-replay-receipt.json). It covers crypto head
`74752a1e644b1c9cc8f4efeb2e2befac6e24f7bb`, the superseded binary corpus
produced at `f402ccd4...`, and three CLI startup checks; it does not attest the
later odd-corpus, source-binding, fixed-`GF(8)`, or sweeper package surface.
[pcc:unverified]

[The additive 2026-11-19 receipt](package-replay-receipt-2026-11-19.json)
binds release run `44486941745`, Linux Rust job `135433215419`, artifact
`14511771570`, and exact crypto head
`22f195741f2f68f37e56ffe134fe2b48fe172245`. The required package job
succeeded even though unrelated jobs left the aggregate workflow cancelled.
The downloaded 104,395,359-byte ZIP has SHA-256
`da77a91bf90511f264ff6ba89995aa2440cc9b57d5a28f7dfe83cfaf7cca2fb8`,
matching GitHub's API digest and size; its safely inspected 105,176,141-byte
inner archive has SHA-256
`6b0bf03c6b09f090e3e3e5ee6390e0b8510520790c2b080da5d7f46413d7f0d7`.
All four CLI startup checks passed. Installed-layout replay regenerated the
500,924-byte successor binary corpus exactly, matched its retained replay,
and returned `verified_complete` for all 174 maps and 150/150 named bindings.
The odd replay returned its required semantic exit 1 with
`verified_named_subgroup_incomplete`, exact raw and canonical pins, and
675/940 supported named bindings; Git-tree source replay passed all five
checks. The fixed-`GF(8)` order replay returned 486, and sweeper capabilities
reported two integrated constructive families among six explicitly scoped
shapes. The retention-bound artifact expires on 2027-02-17. This is
same-implementation package-integrity evidence, not signed standing,
independent mathematics, a stable public release, a packaged run of the full
fixed-`GF(8)` integration-test oracle, a Jacobian solver, or speed evidence.
[pcc:unverified]

The highest-coverage direct short-Weierstrass boundary now covers 20,539 maps
over 675 linked EC1 records through deterministic `u64` validation plus
exactly two live 73-bit pilot rows over `p=5902977611310272157103` under the
strict Sorenson--Webster `psi_13` bound. The final odd corpus separates the
remaining population into its immutable pre-composition partition of 233
proof-range gaps, 22 normalized-backend gaps, 9 extension-backend gaps, and one
invalid generator. The composed Montgomery backend changes the prospective
successor disposition of seven normalized records to proof-range gaps, but does
not widen the accepted field proof boundary. This two-row pilot is not general
wide-prime support. [pcc:unverified]

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
  over prime fields proved either by the complete deterministic `u64` test or
  by the strict Sorenson--Webster `psi_13` gate. Values outside that proof
  range return structured `unsupported_without_primality_certificate`, while
  a deterministic compositeness witness makes the input invalid. For the
  direct short-Weierstrass `prime_quadratic_pullback_v1` family, it implements
  arbitrary-class pushforward, rational-point pullback, the deck action, and
  checked identities `pi_*pi^*=[2]` and `pi^*pi_*=1+deck_*`. Its named
  generator certificate uses a checked odd annihilator and does not assert
  exact order or primality. The widened boundary includes exactly the two
  live 73-bit pilot rows over `p=5902977611310272157103`; it is not a general
  claim for larger prime fields. A separate typed composition now supports
  Montgomery targets admitted by the same proof gate. Edwards targets,
  extension fields, proof-uncovered primes, and nonsplit infinity remain
  unsupported. The
  exhaustive `F_{p²}` counter keeps its explicit `p ≤ 4096` enumeration bound.
  [pcc:unverified]
- The mirrored `PrimeMontgomeryAdapterP` implements the checked degree-one
  isomorphism between a nonsingular Montgomery model
  `B*y^2=x^3+A*x^2+x` and its short-Weierstrass model. It validates canonical
  affine/projective points, preserves infinity, and exposes both directions.
  Exhaustive small-field tests and one implementation-separated small
  group-law control exercise this generic model conversion. The mirrored
  `PrimeMontgomeryQuadraticCoverP` composes that degree-one isomorphism with
  the degree-two split-sextic cover, retains original Montgomery coordinates
  at its public target boundary, and supplies target arithmetic, pullback,
  arbitrary-class pushforward, deck action, and certificates for
  `pi_*pi^*=[2]` and `pi^*pi_*=1+deck_*`. Its public controls exhaust one
  `F_7` fixture with 12 target points and 72 balanced classes and separately
  exercise `B=2,c=1` on a 120-class source. Those are bounded production-path
  controls, not an independent combined-map oracle, catalog-wide subgroup
  certificate, solver, or speedup. [pcc:unverified]

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

The latest mirrored implementation source is crypto commit
`5c6e43a6f0cffe0afc4c962ff54056716cf6437e` for the composed Montgomery
transfer, direct cover dependency, and prime-module routing. The degree-one
model adapter remains pinned to `e0ae0fe5d09c0492a8b50600e88d0b9da68afef1`;
balanced arithmetic and deterministic primality remain pinned to
`153ac585d3b1ece0ebb0d49312b13267f651c94b`. The original audit baseline is
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
| `src/prime_hyperelliptic/balanced.rs` | `153ac585d3b1ece0ebb0d49312b13267f651c94b` | `suite/src/prime_hyperelliptic/balanced.rs` | exact: `5a5f275021cf901e44a2a2a0e3fb9238e55da2772a1620ec153d0d8e4461d451` |
| `src/prime_hyperelliptic/cover_transfer.rs` | `5c6e43a6f0cffe0afc4c962ff54056716cf6437e` | `suite/src/prime_hyperelliptic/cover_transfer.rs` | exact: `10bb0b0fd2c35b8fafb9e5570c01c5ff597f43a71bdac49a9b9f7e51ad5093a4` |
| `src/prime_hyperelliptic/curve.rs` | `3b8664a466efd56121509cd77866a07e3cb55741` | `suite/src/prime_hyperelliptic/curve.rs` | exact: `7a769bfb7abfe92ce06da7c02340f2a2426827d8066ebef510375149b8c3d5ad` |
| `src/prime_hyperelliptic/fp2.rs` | `3b8664a466efd56121509cd77866a07e3cb55741` | `suite/src/prime_hyperelliptic/fp2.rs` | exact: `b833bdff5247f2eea0cde7feb89d0378cfe8305671f9065d2dae7ab538c03e55` |
| `src/prime_hyperelliptic/model_transfer.rs` | `e0ae0fe5d09c0492a8b50600e88d0b9da68afef1` | `suite/src/prime_hyperelliptic/model_transfer.rs` | exact: `cf8d723a0aadd9a4bbdcd2dd56e581ee4bdc0253513d6da9deba95fc5f67ec50` |
| `src/prime_hyperelliptic/normalized_cover_transfer.rs` | `5c6e43a6f0cffe0afc4c962ff54056716cf6437e` | `suite/src/prime_hyperelliptic/normalized_cover_transfer.rs` | exact: `35f81b57d72b4f12e1c14a2392e2510982ca9225843117798c0f1e80d16a571a` |
| `src/prime_hyperelliptic/mod.rs` | `5c6e43a6f0cffe0afc4c962ff54056716cf6437e` | `suite/src/prime_hyperelliptic/mod.rs` | operation-pricing adapter: source `e199bbc9bd33e6df119f4f71a153737f7bdf6e1da3303fc702f6347a4a8e6766`, mirror `32b996fe614230480c11edd695cd778018fac0d7443d6a1f3907d4bf79c78bed` |
| `src/prime_hyperelliptic/fp_poly.rs` | `3b8664a466efd56121509cd77866a07e3cb55741` | `suite/src/prime_hyperelliptic/fp_poly.rs` | selected domain-binding adapter: source `b5d1a1ba5e95d8d0dd06b71757567fb559adbdd09b1ab623ae76e0049ee593c2`, mirror `44f7af14d22bed78d85c4bd009ccce7197fa9257e7ff56164c8d891303e49590` |
| `src/prime_hyperelliptic/primality.rs` | `153ac585d3b1ece0ebb0d49312b13267f651c94b` | `suite/src/prime_hyperelliptic/primality.rs` | exact: `3b055ac166717960963e4e80b7d75eaba6c1681a7bc2e7ddfbb0d4af4d5aaf1c` |

The binary module adapter preserves two existing unlinked rustdoc references,
omits crypto-only `efd`, operation-tally, and trace-zero modules, and retains
the cover/Jacobian exports used by this mirror. Its remaining bytes match after
those declared transformations. The polynomial adapter
ports the required coefficient-field equality guard and regression test,
while preserving cryptanalysis's pre-existing lack of crypto's unrelated
`pow_mod` helper. The prime-module adapter omits only crypto's operation-pricing
module while retaining the model adapter, composed-cover module, and their
public exports. The model adapter, composed Montgomery transfer, direct cover,
balanced arithmetic, and deterministic-primality modules are byte-exact at
their recorded per-file revisions. Exact machine-readable identities and
adapter rules live in [`source-parity.json`](source-parity.json).
