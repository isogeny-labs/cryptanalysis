# H114 independent multiradix carry-cohomology audit

Status: paired preregistration and independent verifier source are published
before measurement. Candidate data are pending. No H114 result or speedup is
asserted here. [pcc:unverified]

This directory mirrors the exact protocol freeze from crypto PR #4622 and is
tracked by cryptanalysis PR #1736.

- `PROTOCOL.md` SHA-256 is
  `92a970c1392183ceb5c84d76082af7b977ebf52145c6b938704cfca24d708c3b`.
- `PROTOCOL.json` SHA-256 is
  `8d89092331a64a00d51ce7caa1602b035ff582835f8b6f7287912d07590ed51c`.
- `CURVES.json` SHA-256 is
  `5dff248152f4cfb3a8b5f9f39542110767d60779d4b917e4b817a935b6170385`.
- `h114_multiradix_verify.rs` SHA-256 is
  `307589c02d437d7d13377c6fce194b441f37579d0b1879263fbe925591a26650`.
- `h114-multiradix-carry-flow.svg` is the editable mechanism figure.

`h114_multiradix_verify.rs` imports no producer code. It independently
reconstructs the seven curve orbits, coordinate-fixed and control sections,
`kappa_2`, `kappa_3`, `kappa_5`, all three pair windings, all six lifted and
represented paths, six oriented edge equations, braid residual, shared-channel
CRT features, all 11,520 predicate IDs, 30-by-30 contingency matrices, exact-ID
intersections, conditional base-30 decoder traces, raw digest, and summary
bindings.

Development check:

```text
rustc --edition=2021 -D warnings h114_multiradix_verify.rs -o h114_multiradix_verify
./h114_multiradix_verify --self-test
```

The self-test independently finds base point `(0,3)` and scalar-one record

```text
k2=16, k3=100, k5=20,
n23=-101, n25=101, n35=0,
w23=-1, w25=1, w35=0,
K=(362,766,463,1675,665,1675), braid=0.
```

It also checks all 11,520 unique predicate-ID round trips, all 30 CRT residue
triples, SHA-256, and the inverse-30 certificate `(36,13)` on the first curve.
[pcc:unverified]

When frozen producer output exists, run:

```text
./h114_multiradix_verify RAW.tsv SUMMARY.json
./h114_multiradix_verify --tamper-test RAW.tsv SUMMARY.json
```

The tamper mode first requires the original dataset to pass, then rebinds raw
digest metadata so semantic mutations reach their intended checks. It must
reject a path coefficient, CRT limb, scalar label, digest, and summary count.
No result fixture is committed or generated in this source-only step.

## Interpretation boundary

Verifier acceptance would establish internal consistency of the frozen toy
cohort and its recorded score. It would not extrapolate an exact predicate to
generic prime fields. The crypto-side Lean theorem keeps that uniform-oracle
premise explicit, and measurement additionally remains behind the private
checkpoint/EKS gate. [pcc:unverified]
