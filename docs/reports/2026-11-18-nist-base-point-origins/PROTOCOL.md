# NIST base-point origin protocol

Frozen: 2026-11-18, before the retained search run.

## Requested question

Determine the documented or reproducible source of the published base points in
the attached `NIST_curve_origins_report.pdf`, with particular attention to a
possible RNG continuation or seed-derived rule.

## Acceptance criteria

For each claimed reconstruction, reproduce the complete published `Gx`
coordinate exactly and identify the generator, seed/state, encoding and attempt
number. A complete point provenance also needs the `Gy` selection rule. If a
bounded search has no match, report only the exact tested construction and
bound; do not infer nonexistence.

## Inputs

- Attached report: `/tmp/codex-remote-attachments/6afd0797-50fc-8191-96f0-39fdc1821027/BC782771-FAD0-4C0E-A423-1E9D8D6BE87D/1-NIST_curve_origins_report.pdf`
- FIPS 186-2 curve parameters and base-point coordinates.
- Anthropic, “The origins of ECDSA’s elliptic curves,” including the recovered
  FreeLIP and `lrand48` constructions.
- Exact constants embedded in `search.py`.

## Frozen hypotheses and controls

1. Positive control: reproduce the six FreeLIP `Gx` coordinates at their
   published recovered seeds and attempt numbers.
2. Same-stream hypothesis: after initializing the recovered `lrand48` stream
   for each unexplained curve, scan from initialization through the documented
   curve-seed endpoint and 50,000 additional state updates. Test state top 8,
   `lrand48` top 31, `mrand48` top 32, state low 26 and full 48-bit state;
   concatenate both most- and least-significant limb first; use both
   `ceil(bits/width)` and one extra limb; reduce modulo the field integer.
   Binary results use the published polynomial-basis coordinate. The B-curve
   stream is also tested against the corresponding Koblitz `Gx`.
3. Curve-seed hash hypothesis: for every published prime and random-binary
   curve seed, test counters 0 through 65,535 for a concatenated SHA-1 chain,
   both byte orders, followed by reduction modulo the field integer.
4. A negative result leaves untested normal-basis encodings, other PRNGs,
   reseeding, discarded-output rules and undocumented manual selection.

## Retained command

```sh
python3 docs/reports/2026-11-18-nist-base-point-origins/search.py \
  --extra-lrand-calls 50000 --hash-counters 65536 \
  --out docs/reports/2026-11-18-nist-base-point-origins/search-results.json
```

An earlier run wrote `/tmp/nist-base-point-search.json` before this protocol and
checkpoint. It is exploratory only and will not be promoted as retained
evidence.
