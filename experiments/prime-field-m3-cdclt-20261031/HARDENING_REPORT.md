---
title: "Prime-field arity-three protocol hardening"
date: 2026-11-01
geometry: margin=20mm
fontsize: 10pt
---

![Evidence and cost gates. Green is implemented only at development-fixture scope; amber remains open; red is ineligible or unadmitted.](hardening-flow.pdf){width=100%}

## Outcome

All nine review findings are now explicit executable-contract requirements.
The native C++ development oracle passes on a deterministic prime-order
small-field fixture. This is implementation evidence, not a solver exponent or
performance result. No held-out instance was generated and no scientific row
was run.

## Corrections

1. Cold relation collection is `2^(a s) + 2^((e+1)s)` up to polynomial
   factors. For arity three, both `a < 1.5` and `e < 0.5` are necessary.
2. The primary slope uses natural instances only and requires the complete
   preregistered natural panel. Any censoring makes the decision inconclusive.
3. Planted and exact-UNSAT instances are separately reported controls.
4. Sinz sequential exactly-one is frozen and exhaustively checked at small
   size. Its exact `s=27` structure is 805,306,365 Boolean variables and
   1,207,959,543 exactly-one clauses before theory auxiliaries, so the one-hot
   continuation is not admitted.
5. Quadratic multiplication cost is scoped to the selected schoolbook CNF
   control; no universal `Theta((log p)^2)` lower bound is asserted.
6. The model binds abscissae to rational lift signs and verifies the signed
   group relation. Chained `S3` equations alone are sign-blind.
7. At inspected cvc5 source head `02f77af...`, finite fields expose no proof
   checker. QF_FF is therefore a SAT/model diagnostic unless an independently
   checked UNSAT certificate route is frozen later.
8. Field membership is the compact unsigned predicate `word < p`; per-word
   forbidden clauses are allowed only under an explicit enumeration cap.
9. Decision provenance is additive: `DEC-20261031-cd6460` remains the checker
   defect, `DEC-20261031-b51282` is the arity correction, and
   `DEC-20261101-26f1fa` records this hardening.

## Implemented evidence

`development_oracle.cpp` checks the rational-lift discriminant
`16 t^2 f(x)`, the complete `t=0` branch, disjoint windows, guarded
three-summand rationality, signed replay, chained `S3`, exact full-versus-
two-window model-set agreement, compact range semantics and the selected
exactly-one encoding. Mutation controls reject overlapping windows, an
out-of-range word, a changed curve coefficient and a corrupted sign/root.

The fixture is `E/F_7: y^2=x^3+3`, with whole group order 13. Complete
quadratic-extension enumeration examines 96 candidate triples and projects to
five accepted signed models. These numbers characterize only this disclosed
fixture.

## Open production boundary

The production typed IR, prime-field external propagator, independent
explanation/UNSAT-proof checker, matched exporters, non-overlapping cost
instrumentation, analysis/power source and resource preflight remain open.
Until those gates pass, the held-out ladder stays blocked. The next lead is to
drive actual Boolean trail assignments through a source-bound `F_p` theory and
compare every response and explanation with exhaustive small-field semantics.

## Reproduction

Run:

```sh
make -C experiments/prime-field-m3-cdclt-20261031 check
make -C experiments/prime-field-m3-cdclt-20261031 check-sanitize
```

The authoritative specification is `PROTOCOL.md`; exact observed commands and
the evidence boundary are in `VALIDATION.md`.
