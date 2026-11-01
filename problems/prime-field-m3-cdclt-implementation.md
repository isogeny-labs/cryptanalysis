# Prime-field arity-three CDCL(T) implementation

- **Status:** `open`
- **Kind:** implementation gap and validation gap
- **Affected work:** [`experiments/prime-field-m3-cdclt-20261031`](../experiments/prime-field-m3-cdclt-20261031/README.md), [`crypto#3096`](https://github.com/isogeny-labs/crypto/pull/3096)
- **Next action owner:** prime-field IC execution lane
- **Last updated:** 2026-10-31

## Problem

We cannot freeze or execute the corrected `m=3`, `s=6..14` prime-field
exponent screen because this repository has no source-bound `F_p` theory
propagator, explanation checker or canonical one-hot/window instance generator
for the chained quadratic-lambda predicate.

The acceptance criterion is not “a SAT process runs.” The candidate must be a
hybrid CDCL(T) implementation whose Boolean and prime-field theory boundaries
match the draft protocol, whose exceptional cases are represented, whose
theory explanations replay independently, and whose complete counted interval
can be compared against enumeration, F4, cvc5 `QF_FF`, A/A and curve-free
null controls.

## Evidence and uncertainty

- **Observed:** the repository contains a pinned CaDiCaL 3.0.1 external-
  propagator precedent at
  [`q1421_work_counted/theory_solver.cpp`](../experiments/compact-s3-m4-20261003/q1421_work_counted/theory_solver.cpp),
  source SHA-256
  `0a0d2c673e9484f4b217917ee306e7663140e4d4618d8bb0ed8dc91947d08bc6`.
  It counts exact root and `F_{2^n}` field calls on a binary-field four-summand
  predicate. It is not an `F_p` theory implementation.
- **Derived or proved:** at scale `s=log2(p)/m`, relation collection with PDP
  exponent `e` has exponent `(e+1)/m` in `p`; a rho crossover requires
  `e<m/2-1`. Thus `m=2` cannot cross and `m=3` requires the strict gate
  `e<0.5`.
- **Suspected explanation:** none. This is a named missing implementation, not
  evidence that CDCL(T) will or will not meet the slope gate.
- **Missing capability:** canonical `F_p` IR/generator, the external theory
  implementation, independently checkable explanations, cvc5 exporter,
  complete work instrumentation and frozen analysis/power code.
- **What this evidence does not establish:** the binary-field Q1421 results do
  not predict prime-field scaling; the cost identity does not establish any
  solver exponent; an implementation pass would not itself establish an
  ECDLP speedup.

## What would unblock it

- [ ] A canonical generator emits the three disjoint one-hot windows, chained
  `S3`/lambda constraints, explicit `t=0` branch and forbidden-word clauses,
  and exact enumeration agrees on every development cell.
- [ ] A pinned CaDiCaL external `F_p` propagator returns independently replayed
  explanation clauses for every theory propagation/conflict and passes all
  five mutation controls.
- [ ] The identical IR exports to pinned cvc5 `QF_FF`, F4 and pure-CNF cost
  controls, with model/proof replay and complete operation/instruction ledgers.
- [ ] Analysis and power code validate, preflight fixes runtime/memory limits,
  and a reviewed immutable protocol freezes before held-out generation.

These conditions are necessary to start the screen. Meeting them would make
the experiment executable; it would not satisfy the `e<0.5` evidence gate.

## Next discriminating step

- **Action or proof obligation:** port only the Q1421 external-propagator API
  shell to the prime-field lambda predicate, then validate it exhaustively on
  development cells before any ladder data are generated.
- **Inputs and controls:** small odd prime-order curves, disjoint and deliberately
  overlapping windows, `t=0` cases, forbidden words, planted/natural/UNSAT
  targets, exact enumeration, and corrupted explanations.
- **Execution limits and stop condition:** development fixtures only; stop on
  any model-set mismatch, unchecked explanation, unsupported exceptional case
  or incomplete cost ledger. Scientific ladder budgets remain unset until
  preflight.
- **Outcomes and next actions:** exact agreement advances to cvc5/F4 exporter
  and preflight work; a mismatch remains an implementation defect; resource
  censoring informs preflight but is not a solver-exponent result; an
  infrastructure failure is recorded separately.
- **Recheck trigger:** source-bound `F_p` generator/propagator and explanation
  checker land together.

## Resolution and history

Unresolved. This record names the execution gap; it contains no run result.
