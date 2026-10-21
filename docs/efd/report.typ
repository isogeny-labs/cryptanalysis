#set page(paper: "a4", margin: 18mm)
#set text(font: "DejaVu Sans", size: 10pt)
#set par(leading: 0.6em)
= Binary EFD formula integration
2026-10-21 · crypto and cryptanalysis · Engineering implementation

The linked characteristic-two Explicit-Formulas Database section is imported
as 135 executable reference programs in 19 representations on three models.
The source snapshot includes assumptions, curve and coordinate definitions,
attribution, URLs and SHA-256 hashes. The methods are established prior work.

#image("architecture.svg", width: 100%)

== Delivered scope
The library exposes finite-point encoding, typed full/X/W projection, program
compilation and evaluation, and checked Weierstrass addition/doubling adapters.
Parameter and mixed-input restrictions are checked. Exceptional full-point
operations use the existing affine law and expose their execution path.
Both repositories contain identical core source, catalogue and native tooling.

#table(columns: (1fr, auto), inset: 6pt,
  [Operation], [Imported programs],
  [Addition], [41], [Doubling], [47], [Tripling], [2],
  [Differential addition], [16], [Ladder step], [16], [Scaling], [13])

== Validation
All 135 programs agree with the unoptimized affine model laws over GF(2^4)
and GF(2^5): 8,640 successful formula/input comparisons per repository.
Unit and nonunit scales are exercised where allowed; singular affine charts
and zero denominators are counted separately in coverage.json.
Applicable full-point Weierstrass operations also agree with pre-existing
arithmetic, including public known-scalar fixtures at 113, 131 and 163 bits.
Source hashes, cache and parameter mismatches, infinity, opposites, missing
charts and field-width errors have explicit tests.

These are finite correctness checks, not universal proofs. The upstream
Sage scripts are linked but were not replayed. See REPORT.md and validation/
for exact commands, host and complete execution status, including wider suites.

== Limits
This import covers the linked binary-field section, not prime-field formulas.
Low-level callers establish model-point membership and differential relations.
Curve model changes are explicit. Production rho walks and GPU kernels are
unchanged; selectors must remain independent of projective scaling. No speedup
or new cryptanalytic result is claimed. GPU tuning and complete-step timings
remain unmeasured. Existing result graphs have no new performance value to plot.

== Sources
#link("https://www.hyperelliptic.org/EFD/g12o/index.html")[Bernstein–Lange binary EFD index];
#link("https://www.hyperelliptic.org/EFD/g12o/auto-shortw-lambda.html")[lambda formulas];
the three imported model definitions; crypto:ecc2k130/LAMBDA-PROJECTIVE.md.
The full source inventory and requirement-to-evidence table are in README.md
and REPORT.md beside this PDF.
