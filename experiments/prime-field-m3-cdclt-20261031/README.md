# Prime-field arity-three CDCL(T) exponent screen

**Status:** corrected execution design; not frozen and not run.

This directory is the `cryptanalysis` execution handoff for the prime-field
index-calculus correction recorded in
[`crypto#3096`](https://github.com/isogeny-labs/crypto/pull/3096). It does not
promote the accepted two-summand factor-base results into an arity-three
solver claim, and it contains no new measurement.

## Requested scope and evidence status

| Requirement | Status in this repository | Evidence or remaining gap |
| --- | --- | --- |
| Treat arity two as structurally irrelevant to a rho crossover | verified as a cost identity | If one PDP costs `2^(e s)` at `s=log2(p)/m`, collecting `Theta(2^s)` relations costs `p^((e+1)/m)` up to polynomial factors; rho requires `e<m/2-1`, which is impossible at `m=2`. |
| Use a prime-field hybrid solver rather than call pure CNF the candidate | specified, not implemented | [`PROTOCOL.md`](PROTOCOL.md) fixes CaDiCaL plus an external `F_p` theory, with cvc5 `QF_FF` as the independent route. The current source-bound external propagator is an `F_{2^n}` architectural precedent, not an `F_p` implementation. |
| Preserve the useful algebra and semantic clauses | specified | The quadratic lambda lift, discriminant `16t^2 f(x)`, guarded three-summand rationality, higher-arity rationality circuits and forbidden-word clauses are retained explicitly. |
| Measure the arity-three exponent | preregistered design only | Initial ladder `s=6..14`, strict corrected upper-interval gate `e<0.5`, curve-free null and exact two-window enumeration control. No generator, held-out instances or run rows exist yet. |
| Provide a path to 40--80-bit prime fields | staged | Fixed `m=3`; the target band is `s=13..27`. The initial ladder reaches `s=13,14`; `s=15..27` requires a separately frozen continuation after the initial screen. |

## Why the arity correction changes the experiment

For factor-base scale `s=log2(p)/m`, relation collection needs on the order of
`2^s` relations. A PDP oracle of cost `2^(e s)` therefore gives total exponent
`(e+1)/m` in `p`. The strict rho crossover is

```text
e < m/2 - 1.
```

At `m=2` the right side is zero. Faster presentation-specific degree or
solver work at two summands can remain a valid component result, but it cannot
change the ECDLP exponent. At `m=3`, the first relevant fixed arity, the gate
is `e<0.5`. Exact enumeration scans two windows and supplies the `e=2`
control; it is not the gate.

## Existing external-propagator source binding

The executable CaDiCaL precedent is
[`q1421_work_counted/theory_solver.cpp`](../compact-s3-m4-20261003/q1421_work_counted/theory_solver.cpp)
at repository base `1ee4f47e962aac7f0f09781e34fccfaec1c6456e`:

- source SHA-256: `0a0d2c673e9484f4b217917ee306e7663140e4d4618d8bb0ed8dc91947d08bc6`;
- CaDiCaL version: `3.0.1`;
- pinned header SHA-256: `b7111690c61935b9c096d3701be59b3c3d26c555eab8e070f19eb2a97dc5d38c`;
- pinned library SHA-256: `8bb5e4c5128864e8e5f4e2542d9c828befb416c4cda01460718c6ed561600315`.

That source demonstrates the external-propagator lifecycle and counted field
API calls over `F_{2^n}`. It does **not** implement the required prime-field
lambda theory, one-hot windows, exceptional chart, or independently checked
explanations. Reusing its API shell is allowed; relabelling it `CDCL(T)/F_p`
is not. The open implementation obligations are tracked in
[`problems/prime-field-m3-cdclt-implementation.md`](../../problems/prime-field-m3-cdclt-implementation.md).

## Execution status

- Scientific runs: 0.
- Held-out instances generated: 0.
- Solver exponent estimates: 0.
- Claims of an ECDLP or rho speedup: 0.

The next action is implementation and small exhaustive correctness replay,
not collection of the preregistered ladder.
