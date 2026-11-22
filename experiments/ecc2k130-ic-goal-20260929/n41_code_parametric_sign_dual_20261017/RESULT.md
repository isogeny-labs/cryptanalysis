# Degree-three threshold for a code-dependent N41 sign dual

**A target-conditioned trace mask that varies quadratically with the eight
source-code bits cannot certify all 35 lower-root charts in the frozen N41
fixed-five-slot panel.** An exact 235-equation XOR contradiction establishes
the degree-two obstruction. A degree-three mask fits every chart and rejects
all **2,240** lower-root sign assignments. The fit has 93 field-width
coefficient blocks, 34 nonzero, and was constructed after processing all
35 charts; it is a finite interpolation result rather than a compact
source-family search rule.

## Exact panel and construction

The [source census](../n41_rr_pairwise_certificate_20261017/RESULT.md)
fixes five pair states from the archived ordinary public relation on
`EC1N41Ckb1h7d5e80d3c4d0`, and varies the first source code over 35
legal, column-compatible W8 masks. For each code it selects the lower x
root and all 64 sign choices. The source's checked-Sage audit recomputed
all 2,240 seven-point Riemann–Roch determinants. Each separate code chart
has a trace mask certifying its 64 determinant values as nonzero. The
archived relation's first pair takes the other x root and is retained by
the full source: the prior full-root census records code mask 6, upper root,
sign assignment 15 as its exact zero chart. The present predicate applies
to these lower-root charts.

We sought a mask `L_d(c)=⊕_{|A|≤d}c^A ℓ_A`, with `ℓ_A` a 41-bit vector,
that is one on each chart's constant determinant coefficient and zero on
all its sign-dependent coefficients. The frozen [producer protocol](protocol.json)
binds the previous coefficient census, code, equation law and degrees
0–3. Pure integer GF(2) elimination yielded:

| Code degree | Monomials / formal mask bits | Code-monomial rank on 35 masks | Exact system result |
| ---: | ---: | ---: | --- |
| 0 | 1 / 41 | 1 | Inconsistent; 18-row XOR certificate |
| 1 | 9 / 369 | 8 | Inconsistent; 54-row XOR certificate |
| 2 | 37 / 1,517 | 29 | **Inconsistent; 235-row XOR certificate** |
| 3 | 93 / 3,813 | 35 | Satisfiable; 1,225 independent equations |

The degree-two conflict appeared after 1,380 of the 1,470 nonzero-coefficient
equations, with rank 1,154 immediately before the contradictory row.
All 35 charts and 1,470 nonzero-coefficient equations enter the degree-three
fit; its coefficient-equation rank is 1,225. The monomial restriction has
rank 35 at degree three, so it can interpolate arbitrary masks on this finite
35-code set. Its satisfiability therefore provides no extrapolation beyond
those codes.

The [independent parity audit](audit_result.json) rebuilt each conflict from
its saved chart/coefficient labels, checked zero left parity and odd right
parity, and evaluated the degree-three score on all 2,240 determinant sign
values. The [terminal verifier](verification.stdout) checked source hashes,
the prior Sage audit, all three contradiction sizes, the monomial ranks,
Lean output and empty stderr. Both producer and audit ran in one local
Python process in under 0.2 seconds of recorded arithmetic time each;
these are exact finite-system diagnostics on an ordinary host. They are not
single-target IC wall times. The contribution is the source-bound degree
threshold and its replayable certificates, with `candidate_id: null`.

The first protocol-freeze invocation stopped at an incorrect assertion on
the upstream result status; the [attempt record](freeze_attempt1.json)
preserves that setup failure. The assertion was corrected before the
protocol and measured system were frozen.

## Next algorithm gate

The first degree that fits these 35 code charts has the same full
35-dimensional evaluation capacity as a per-code table. A useful
code-dependent condition therefore needs a structural derivation from
unresolved source bits, or a target-conditioned multi-slot constraint that
rejects source families before enumerating their members. Test its
ordinary unpinned N41 relation against the exact native join, then require
a source-bound cost projection before the frozen N131 600-second/4-GiB
public-point gate. The [proof map](PROOF_MAP.md) identifies the checked
structural Lean theorem and the finite-data formalization boundary.
