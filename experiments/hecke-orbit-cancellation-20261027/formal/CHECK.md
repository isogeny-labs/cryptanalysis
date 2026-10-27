# Formal check

The project pins `leanprover/lean4:v4.35.0-rc4` in `lean-toolchain` and has no external dependencies. `lake build OrbitCancellation` completed successfully; see [build-output.txt](build-output.txt). `#print axioms` reported no axioms for each of `cancel_8_19`, `cancel_2_4`, `cancel_7_9`, and `cancel_11_15`.

Each theorem checks all 21 integer coordinates: the 20 frozen class columns and one shared outside-trace column. The latter cancels exactly in each difference. The explicit row encodings are linked to the producer's F_83 trace points and class rows by `verify.py`.

Formalization is partial for the full finite-field result. Lean does not currently define the `11a1/F_83` group law, the extension-field Hecke neighbor moment solver, Frobenius orbit traces, or the rational rank of the combined matrix. The checked Sage producer and independent pure-Python group/rank replay supply those concrete bridges.
