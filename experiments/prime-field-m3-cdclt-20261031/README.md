# Prime-field arity-three CDCL(T) exponent screen

**Status:** hardened draft plus native development oracle; not frozen and not
scientifically run.

This directory owns the executable contract for the prime-field
index-calculus correction begun in
[`crypto#3096`](https://github.com/isogeny-labs/crypto/pull/3096). The
2026-11-01 amendment repairs preprocessing accounting, censoring, target-class
pooling, one-hot continuation sizing, multiplier wording, abscissa/sign
semantics, UNSAT eligibility, range encoding and decision provenance before
any held-out data exists.

The compact evidence map and review narrative are available as
[`HARDENING_REPORT.md`](HARDENING_REPORT.md) and its rendered
[`HARDENING_REPORT.pdf`](HARDENING_REPORT.pdf).

## Requirement-to-evidence status

| Requirement | Status | Evidence or remaining gap |
| --- | --- | --- |
| Include reusable preprocessing in the cost bridge | specified and mechanically checked | [`PROTOCOL.md`](PROTOCOL.md) uses `S(s)+2^s Q(s)` and gates both `a<1.5` and `e<0.5`; exact stage instrumentation is not implemented. |
| Fit a censor-safe natural workload | specified | Every natural row must complete and verify; planted and exact-UNSAT rows are controls and never enter the primary slope. Analysis/power code is still missing. |
| Freeze a concrete exactly-one encoding | implemented at development scope | [`development_oracle.cpp`](development_oracle.cpp) emits and exhaustively checks Sinz sequential exactly-one through `n=8`; the full generator/exporter is missing. |
| Admit the continuation honestly | exact structural sizing implemented | At `s=27`, the selected encoding has 805,306,365 Boolean variables and 1,207,959,543 exactly-one clauses before theory auxiliaries. A compact/lazy amendment or measured resource admission is required. |
| Scope pure-CNF multiplication cost | corrected | Quadratic growth is asserted only for a frozen schoolbook control; no universal lower bound is claimed. |
| Bind abscissae, rational lifts and signs | implemented at development scope | The native oracle uses disjoint abscissa windows, explicit rational-lift signs, chained `S3` checks and exact signed replay on an odd-prime-order curve. The production typed IR remains missing. |
| Require checked UNSAT evidence | source-reviewed and specified | cvc5 source head `02f77af402b4be82f27e5cc00b86b265a90dea3d` has no finite-field proof checker, so QF_FF is diagnostic unless a checked certificate route is bound before freeze. |
| Avoid exponential forbidden-word lists | implemented at development scope | The canonical semantic constraint is unsigned `< domain`; the oracle checks the comparator exhaustively. Exporters may enumerate invalid words only below a frozen cap. |
| Preserve decision identity | corrected cross-repository | `DEC-20261031-cd6460` remains the checker-defect decision; the arity correction is `DEC-20261031-b51282`, hardened additively by `DEC-20261101-26f1fa`. |

## Native development oracle

Build and run:

```sh
make -C experiments/prime-field-m3-cdclt-20261031 check
```

The deterministic fixture is `E/F_7: y^2=x^3+3`, whose whole group has prime
order 13. Three disjoint windows cover the seven abscissae. The oracle:

- checks the lambda discriminant and lift equivalence for every
  `x,t,s0,lambda`, retaining the complete `t=0` branch;
- enumerates every quadratic-extension lift and finds five projected models
  among 96 candidate triples;
- verifies every accepted lift is rational under the guarded three-summand
  argument;
- checks both chained `S3` relations and exact signed group replay;
- compares complete enumeration with the exact two-window oracle;
- rejects overlapping windows, an out-of-range word, a changed coefficient
  and a corrupted sign/root;
- exhaustively checks the selected exactly-one clauses through eight selectors;
- emits exact initial/continuation selector, auxiliary and clause counts.

These are disclosed development fixtures, not the held-out ladder. They
establish the landed oracle's bounded behavior only.

## Source and literature boundary

- Semaev, *Summation polynomials and the discrete logarithm problem on
  elliptic curves*, ePrint 2004/031: the chained summation-polynomial source.
- Sinz, *Towards an Optimal CNF Encoding of Boolean Cardinality Constraints*,
  DOI `10.1007/11564751_73`: selected sequential cardinality construction.
- Harvey and van der Hoeven, *Integer multiplication in time O(n log n)*,
  DOI `10.4007/annals.2021.193.2.4`: why quadratic multiplication is not a
  universal Boolean lower bound.
- cvc5 1.4.2 finite-field examples and source head `02f77af...`: QF_FF model
  route and the missing finite-field proof checker.

The Sinz and Annals full PDFs were not retrievable in this environment;
metadata and accessible official source were checked, and no fresh full-text
audit is claimed. The selected clause construction is independently derived
and exhaustively tested by the native oracle.

## Existing external-propagator source binding

The CaDiCaL API precedent remains
[`q1421_work_counted/theory_solver.cpp`](../compact-s3-m4-20261003/q1421_work_counted/theory_solver.cpp),
SHA-256 `0a0d2c673e9484f4b217917ee306e7663140e4d4618d8bb0ed8dc91947d08bc6`,
with CaDiCaL 3.0.1. It is an `F_{2^n}` architectural precedent, not the
missing `F_p` theory or certificate checker.

## Execution status

- Development-fixture checks: implemented and passing as recorded in
  [`VALIDATION.md`](VALIDATION.md).
- Held-out instances or scientific rows: 0.
- Prime-field propagator, explanation checker and proof logger: not implemented.
- Solver exponent estimates or performance claims: 0.

The next implementation lead is the source-bound `F_p` trail propagator plus
independent explanation/proof replay on these fixtures, followed by the
canonical exporter and scratch preflight. The open boundary is tracked in
[`problems/prime-field-m3-cdclt-implementation.md`](../../problems/prime-field-m3-cdclt-implementation.md).
