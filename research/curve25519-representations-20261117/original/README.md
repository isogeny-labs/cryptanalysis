# Curve25519 representations — research and exact diagnostics

17 November 2026. Status: completed first pass on all five proposed directions. Mathematical derivations, literature review, CPU correctness tests and exhaustive tiny-field diagnostics. **No verified competitive attack or performance improvement.** No publication or novelty claim.

Read [report.pdf](report.pdf) for the illustrated nine-page report. The scripts and raw JSON are the reproducibility bundle. The earlier PDF from the conversation was absent from the restored workspace; this is a new report.

## Main findings

1. **Derived identity:** on `v²=u³+A*u²+u`, `T=(0,0)` gives `(u,v)+T=(1/u,-v/u²)`. The invariant `z=u+1/u` is the x-coordinate, minus A, of the degree-2 isogeny
   `phi(u,v)=(u+A+1/u, v*(1-1/u²))`
   to `Y²=X³-2A*X²+(A²-4)*X`. The kernel is `{O,T}`. On an odd prime subgroup H the kernel is trivial, so this is injective; z identifies only the already-folded sign pair within H. This is not an independent extra compression mechanism. Exceptional points are handled by the projective map.
2. **Exact stage diagnostic:** for six fixed geometric bases and targets, the specialized two-summand relation equations have 9 monomials in Montgomery u and 5 in Edwards y. Their total degrees are all 4. Twenty-four reference Groebner computations preserve the checked root sets. Their reduced output term counts are equal across the four tested representations on each case. Neither input nor output sparsity measures internal solver work.
3. **Exact factor-base census:** 18 curves over six fields with prime subgroup orders 11–479; equal numbers of sign classes selected by u, Edwards y, z, or a fixed-seed shuffle. Coverage varies by curve and policy. No policy dominates all 18. Transporting a fixed geometric base through the 2-isogeny preserves the entire pair-sum histogram. Twelve cofactor-1 controls are retained, with their field/subgroup differences explicit; they do not isolate a causal effect of torsion.
4. **Sparse membership construction:** all 159 cases with D dividing p−1 and D≤64 were checked for multiplicative-subgroup membership and the Dickson recurrence `C_D(u+1/u)=u^D+u^(-D)=2`. Ninety cases have empty nonidentity prime-subgroup bases. Actual base sizes differ, so these are not a head-to-head yield comparison with the equal-size bases.
5. **Bounded negative lift result:** the fixed Curve25519 integer model has only `(0,0)` in the scan of all integer u with |u|≤10000. This says nothing conclusive about rational denominators, other lifts, larger heights or other number fields.
6. **Extra encoding check:** RFC Elligator 2 was checked over every parameter on each of the 18 toy curves. Cofactor-cleared outputs lie in H; every instance has an explicit additivity counterexample. An encoding parameter is not a discrete logarithm.
7. **Correctness pipeline:** 72/72 toy IC lookup/linear-algebra scalar recoveries pass; rho also recovers the same public targets. Fixtures use k=7, queries use a fixed seed, identity queries are skipped, and all recovered base logs are replayed. Base selection uses exhaustive subgroup enumeration and is not scalable. The lookup collector is separate from the reference Groebner checks. No clock or operation-count speedup is claimed.
8. **Independent arithmetic path:** 2,895 differential-ladder and artifact checks pass. This is a second arithmetic algorithm, not independent-host replay or an independent review of every research claim.

9. **Retained-system limit:** the full nine-variable, eleven-constraint reference solve on the first symbolic fixture hit its fixed 45-second limit. Its maximum input degree was only 3. This failure is retained in `retained-results.json`; it is not a performance comparison or evidence of an asymptotic lower bound. The separate 216 signed-pair arithmetic checks pass.

## A field-structure counterpoint

Trial division of p−1 through 100000 was computed in JavaScript while startup was pending and then independently recomputed in Python. The complete smooth parts through that bound have approximate bit lengths: Curve25519 19.58; P-224 137.32; P-256 55.23; P-384 11.31; P-521 136.18. Remaining cofactors are explicitly unfactored and not certified prime. In particular v2(p−1)=2 for Curve25519 and 96 for P-224. These are arithmetic descriptors, not attack costs. The PKC 2016 construction explicitly discusses P-224.

## Priority after this pass

Implement and profile composed sparse membership constraints together with retained Edwards product equations on the same geometric factor base. First establish complete solution-set handling, including infinity charts, sign lifting and torsion offsets; then compare production solvers and a matched same-target rho baseline. Varying the factor base is a separate experiment. Auxiliary-curve membership-map construction is also distinct from transporting the attacked curve through an isogeny.

The full production F4/F5/SAT/QUBO comparison, general auxiliary-isogeny search, large-field scaling and common-field bounded-height lifting algorithms remain unimplemented. The report does not turn those open tasks into positive results. All proposed directions were investigated; they were not all resolved.

## Reproduce

Requires Python with SymPy, NumPy and Matplotlib; the report uses pdfLaTeX and TikZ.

```sh
python research.py
python followup.py
python verify.py
python retained.py  # up to 45 seconds; timeout is a retained outcome
python figures.py
pdflatex -interaction=nonstopmode -halt-on-error report.tex
pdflatex -interaction=nonstopmode -halt-on-error report.tex
```

Run from this directory for the TeX build. The Python scripts locate their outputs relative to their own path. No remote jobs, credentials or network requests are used. `results.json` records the Python, SymPy and platform versions. `PROTOCOL.md` and `AMENDMENT.md` are standalone scope records, not a certified experiment.protocol/v1 or benchmark export. Earlier preliminary calculations are explicitly marked in `preliminary.json`.

## Files and provenance

- `results.json`: full instance parameters, subgroup generators and content-hash labels, actual bases, coverage, symbolic equations, encoding images, integer points, real Curve25519 map checks.
- `followup-results.json`: all recovery outcomes, reference rho answers, Groebner output descriptors, structured-base and cancellation cases, field-factor records.
- `verification.json`: independent arithmetic-path check result.
- `retained-results.json`: full retained-system construction and bounded-solver outcome, including the timeout.
- `sources.json`: primary source links and exact access depth; several full papers were unavailable. The 2020 negative result is explicitly conditional and method-specific.
- `coverage.svg`, `equations.svg`, `field-structure.svg`: quantitative vector figures, with corresponding PDF assets and generating source.
- `report.tex`: editable report and schematic diagrams.
- `SHA256SUMS`: delivered-file hashes.

Existing repository candidate/curve/factor-base registries and canonical graphs were not modified. The related catalog and representation-join note were inspected; the new bundle establishes no new canonical isogeny discovery or performance result for promotion.
