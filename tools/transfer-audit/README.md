# Binary transfer audit

Rust CLI for a specified ordinary binary curve, exact obstruction arithmetic,
evaluated Frobenius isogenies, same-field genus-three pullbacks, and explicitly
bounded isogeny-class classification. This is a transfer/certificate tool, not
an ECDLP solver or a universal weakness classifier.

```sh
cargo build --release --locked --manifest-path tools/transfer-audit/Cargo.toml
tools/transfer-audit/target/release/transfer-audit audit \
  --input tools/transfer-audit/fixtures/b163.json --output /tmp/b163-audit.json
tools/transfer-audit/target/release/transfer-audit verify \
  --certificate /tmp/b163-audit.json
```

Output files must not exist. Inputs reject unknown fields. `verify` recomputes
the entire certificate, including coverage rows and implementation/input
hashes; edited or incomplete certificates fail. This is same-implementation
replay, not a signature, independent implementation, or formal proof of Rust.

## Implemented scope

| Component | Certificate | Limit or unresolved premise |
|---|---|---|
| Binary field | exact irreducibility and coefficient-width checks | degree 1–571, polynomial basis |
| Source subgroup | prime certificate, nonzero G and rG=O | without G/prime proof, exact subgroup order stays conditional |
| Curve order | direct small-field count, or unique Hasse-interval multiple of certified r | otherwise unresolved; no supplied order is trusted |
| All subfields | every d dividing n, including the original field | target field enlargement is separate |
| Arbitrary genus-bounded Jacobian targets | exact Weil integer upper bound and excluded genus interval | genus bound at most 256; actual subgroup order is required |
| Classical GHS | augmented Frobenius rank over F2 for each subfield | formal genus only; no GHS/gGHS quotient or twist selection |
| Frobenius isogeny orbit | evaluated coefficient and generator images under (x,y) -> (x²,y²) | complete coefficient orbit, not entire isogeny class |
| Full small-field ordinary class | all canonical models, exact orders and equal-trace classification | explicitly requested, degree at most 8; no paths to every member |
| Same-field genus three | native geometry, Mumford pullback, image order, pull/push and public 37G control | no unknown-log solve, generic Jacobian norm, descent or speed claim |
| Supplied spectral targets | exact gcd over Q with restriction-of-scalars polynomial | target curve and its Frobenius polynomial must independently be established |

To request small-field class enumeration, set `exhaustive_class: true`; see
`fixtures/toy-f8.json`. A larger request returns an error instead of a partial
enumeration labelled complete. These canonical models classify ordinary
Fq-isomorphism classes; an equal trace classifies Fq-isogeny by the elliptic
finite-field isogeny theorem. This does not construct isogeny paths.

Optional `spectral_targets` entries have `base_degree` and ascending signed
decimal `coefficients` of a monic, q-reciprocal polynomial of positive even
degree at most 512. At most 32 entries are accepted. Reciprocity alone does
not establish a Weil polynomial or a Jacobian. Non-coprime output certifies
neither an explicit map nor nonzero action on the chosen r-subgroup.

Large primes require recursive Pocklington certificates. Each factor's
primality, divisibility into r−1, exponent, Fermat/gcd witnesses and product
greater than sqrt(r) are checked. Leaves use the deterministic seven-base
64-bit Miller–Rabin test. The B-163 fixture has a checked certificate chain;
it does not rely on a probable-prime verdict.

`all_possible_transfers_ruled_out` is always false. Unknown families are
listed even when every requested finite check finishes. A matching spectral
polynomial, subgroup-size test, or finite walk cannot close those families.

## Theorems, validation and research limits

Read [THEOREMS.md](THEOREMS.md) for the abstract-group classification,
algebraic obstruction, class-uniform Weil obstruction and coverage trust
theorem, with written proofs and exact hypotheses. These combine established
mathematics; no new attack family or publication novelty is asserted.
The [report](REPORT.md) and [PDF](REPORT.pdf) distinguish execution from
existence, and [the open problem](../../problems/transfer-audit-completeness.md)
retains the broader requested classification and formalization gaps.

The feasible Lean checker proofs are in
[`tools/lean/transfer-audit`](../lean/transfer-audit/TransferAudit.lean).
The geometry, finite-group classification, Tate theorem and Rust/Lean
refinement are not formalized by that module. Its dedicated CI gate audits
every theorem transitively; the historical research-corpus receipts are
unchanged. New-code Clippy is strict. The reused native module retains only
the two relevant, existing suite/Cargo.toml lint allowances; they do not
apply to the new audit code.

```sh
tools/transfer-audit/check.sh
```

This runs unit and fixed-fixture correctness checks, not cryptanalytic timing
or a new search campaign. For a research sweep or new experiment, first run
`scripts/checkpoint.sh gate` under the current repository policy. The retained
checkpoint attempt could not upload because this runtime lacked credentials
or an upload token. No new research sweep was launched under that failure.

Source reuse is by path to the existing native module, not a copied fork.
The certificate hashes the CLI/library source, Cargo manifest and lockfile,
and all six imported native source files. Field elements are unsigned decimal
or `0x` strings; no floats are used. Inputs and certificates are audit records,
not new EC1/IC1 registry or weak-curve catalogue entries.
