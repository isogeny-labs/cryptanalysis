# H109 paired reference harness — torsion-local derivative oracle

Status: **independent replay complete; scoped null confirmed** (2026-11-01).

This directory independently checks the artifact produced by
[isogeny-labs/crypto#3102](https://github.com/isogeny-labs/crypto/pull/3102).
The verifier is standard-library-only and does not import the canonical
experiment implementation.

## Replayed evidence

- verified all 9,096 target records and every local-identity residue;
- completely re-enumerated all 8,832 frozen coefficient tuples;
- independently regenerated and searched all 32 symmetry-matched controls;
- confirmed 0/28 exact candidate rows and 0/32 exact controls;
- confirmed result SHA `940123c44c6194b247fab3596a9ed2e331ee7e01b2fb8830fc7e8465e354993a`;
- confirmed scientific-content SHA `3991b25d2a2ddac0ebb1d25370c8b110051a40acca64a6bda3dd3baba4191b69`.

Run:

```sh
python verify.py results/torsion-division-derivative.json.gz
```

The [verification receipt](verification-receipt.json), [frozen manifest](frozen-manifest.json),
[executed protocol](PROTOCOL.md), editable [SVG](figures/h109-torsion-derivative-flow.svg),
and [four-page report](h109-torsion-derivative-preregistration.pdf) bind the replay
to the canonical artifact.

This confirms a scoped null for the frozen five-input phase family. It does
not establish novelty, an ECDLP algorithm, a lower bound, or subexponential
runtime.
