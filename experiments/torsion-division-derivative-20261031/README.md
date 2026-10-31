# H109 paired reference harness — torsion-local derivative oracle

Status: **preregistered; implementation pending** (2026-10-31).

This directory freezes the independent reference-harness role for
[isogeny-labs/crypto#3102](https://github.com/isogeny-labs/crypto/pull/3102).
The canonical hypothesis, transfer assessment, and eventual research result
live in `isogeny-labs/crypto`. This repository owns the independently
composed arithmetic checks, matched generic baselines, and operation accounting.

## Mechanism under test

For a prime-order subgroup `<P>` of a short Weierstrass curve over `F_p`
and `Q=[k]P`, H109 tests whether the invariant local derivative
`delta_r(Q)=D psi_r(Q)` participates in a constant-size two-power character
formula that returns scalar parity. The predicted algebraic control is

```
delta_r(Q)^2 = -r^2 psi_(r-1)(Q) psi_(r+1)(Q).
```

The [frozen protocol](PROTOCOL.md), [editable diagram](figures/h109-torsion-derivative-flow.svg),
and [rendered report](h109-torsion-derivative-preregistration.pdf) are mirrored
here so review of this harness is hash-bound to the same preregistration.

## Reference-harness obligations

1. Independently evaluate the local identity and candidate field products.
2. Match the complete 28-row / 9,096-target matrix from the canonical PR.
3. Run the 32 symmetry-matched random-label controls with the identical
   `4^5` formula budget.
4. Record recurrence nodes, field operations, character phases, memory,
   setup/advice, decoder work, and EC verifications.
5. Compare the complete candidate with matched generic BSGS/rho references
   and H107/H108's charged linear-support character baselines.
6. Refuse any speed claim unless every target is recovered and verified.

No measured improvement or ECDLP result is claimed by this preregistration.
