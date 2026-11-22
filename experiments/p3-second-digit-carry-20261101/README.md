# H112: `p^3` second-digit halving carry

H112 tested whether the second formal digit of a canonical `p^3` halving
section carry, or one of 72 fixed cross-digit combinations, gives scalar
parity on generic prime-field toy curves.

Status: measured scoped null. All 9,096 target cases and structural/torsion
checks passed, but none of 144 preregistered predicates was exact on any of 28
curve/generator rows. The standalone replay reproduced scientific digest
`3f0d58b381df5d308537942c29f80e826217105bdd7c8db4129885c4e91ea832`.

- `PROTOCOL.md`: frozen mechanism, predicates, controls, and promotion gates.
- `RESULT.md`: measurements, costs, proof boundary, and interpretation.
- `p3_second_digit_carry_lab.py`: canonical experiment.
- `h112_reference_verify.py`: source-independent arithmetic replay.
- `H112P3SecondDigitCarry.lean`: structural and conditional recovery proof.
- `RECOVERY_PROVENANCE.json`: original and recovered hash lineage.
- `p3-second-digit-carry.json.xz`: exact recovered raw JSON (artifact-store
  managed after PR publication).

The measurement rejects only the frozen family. It does not establish an
impossibility theorem for arbitrary functions of the carry.
