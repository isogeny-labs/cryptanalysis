# Prime-field arity-three CDCL(T) production implementation

- **Status:** `open`, narrowed by a passing native development oracle
- **Kind:** implementation, certificate and validation gap
- **Affected work:** [`experiments/prime-field-m3-cdclt-20261031`](../experiments/prime-field-m3-cdclt-20261031/README.md), [`crypto#3096`](https://github.com/isogeny-labs/crypto/pull/3096)
- **Next action owner:** prime-field IC execution lane
- **Last updated:** 2026-11-01

## Problem

The corrected `m=3`, `s=6..14` screen still cannot freeze or execute because
there is no source-bound production `F_p` external propagator, independent
theory-explanation/UNSAT proof checker, canonical backend exporter, complete
stage instrumentation or frozen analysis/power source.

The earlier generator/oracle gap is partially resolved: the experiment now
contains a native deterministic development oracle that binds abscissae and
signs, verifies the lift identity including `t=0`, compares exact full and
two-window model sets, tests the selected exactly-one encoding and rejects
four semantic mutations. It is not a production generator and cannot be used
to generate held-out cells.

## Evidence and uncertainty

- **Observed implementation evidence:**
  [`development_oracle.cpp`](../experiments/prime-field-m3-cdclt-20261031/development_oracle.cpp)
  passes on `E/F_7: y^2=x^3+3`, prime whole-group order 13. It checks 96
  quadratic-extension candidate triples, obtains five exact projected models,
  and agrees byte-for-byte at the projected-model-set level with the exact
  two-window oracle.
- **Observed source capability:** the Q1421 CaDiCaL 3.0.1 source remains an
  `F_{2^n}` API precedent only. Current inspected cvc5 finite-field source head
  `02f77af402b4be82f27e5cc00b86b265a90dea3d` returns no proof checker, so
  QF_FF is not presently an UNSAT-certifying decision candidate.
- **Derived accounting:** with setup `2^(a s)` and online query `2^(e s)`,
  collection costs `2^(a s)+2^((e+1)s)` before polynomial factors. At `m=3`
  the necessary gates are `a<1.5` and `e<0.5`.
- **Resource fact:** selected Sinz one-hot at `s=27` has 805,306,365 Boolean
  variables and 1,207,959,543 exactly-one clauses before theory auxiliaries.
  This is a structural size, not a measured OOM or impossibility result.
- **What remains unknown:** whether a faithful CDCL(T)/`F_p` implementation
  completes the initial natural panel, what its two exponents are, and whether
  a compact continuation representation preserves solver behavior.

## What would unblock the initial screen

- [x] Native development semantics for disjoint abscissa windows, rational-lift
  signs, signed replay, lambda discriminant, `t=0`, compact range predicates,
  selected exactly-one encoding and exact two-window agreement.
- [ ] Production typed IR/generator with protocol-hash seeds, canonical bytes,
  all chart branches and exact agreement across a wider disclosed fixture census.
- [ ] Pinned CaDiCaL external `F_p` propagator with independently replayed
  explanations for every propagation/conflict and checked Boolean-plus-theory
  proof logs for UNSAT.
- [ ] Identical F4 and pure-CNF exporters; QF_FF remains diagnostic unless a
  source-bound, independently checked finite-field UNSAT certificate appears.
- [ ] Non-overlapping cold/setup/online/verification instruction and byte
  ledgers whose stages reconcile to the cold total.
- [ ] Frozen natural-only complete-panel analysis, power calculation, runtime/
  memory preflight and immutable held-out manifest.

Satisfying these conditions makes the initial experiment executable; it does
not predetermine either slope.

## Continuation obstruction and next discriminating steps

The initial one-hot bundle has no admitted `s=15..27` continuation. Pursue two
implementation leads in order:

1. **Production `F_p` trail theory.** Port only Q1421's lifecycle shell. Drive
   the landed fixture plus additional small odd-prime-order fixtures through
   actual trail assignments; compare every partial/full theory response with
   exhaustive semantics; mutate every explanation and proof step.
2. **Compact selector equivalence.** After the initial exporter exists, build a
   binary or lazy multi-valued selector that projects to the identical signed
   model set. Compare it with Sinz one-hot on every development cell, then
   preflight setup exponent, serialized bytes and peak RSS before proposing a
   continuation amendment.

Stop either lead on a model-set mismatch, unchecked lemma, unsupported chart,
non-reconciling cost ledger or failed mutation control. A resource stop informs
the representation ceiling and remains distinct from a solver-exponent result.

## Resolution and history

- 2026-10-31: problem opened; no prime-field generator or propagator existed.
- 2026-11-01: native development oracle and exact representation sizing landed;
  production solver, certificate, exporter, accounting and analysis gaps remain.
