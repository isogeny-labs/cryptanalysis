# The final degree-13 fiber has a unique lift and an explicit orbit trace

The source-19 degree-13 neighbor polynomial on the frozen D=-79, conductor-2 class has one rational x-root of multiplicity two at `x=4` and one degree-12 factor. The fourteen Hecke moments determine a repeated-root y-sum of 82. Curve-lift enumeration, all moment equations, the modular polynomial, and the Hecke group sum select the unique pair `(4,38)` and `(4,44)`. The twelve-point Frobenius orbit traces to `(18,31)` in `11a1(F_83)`.

The two rational neighbors are frozen class points `P_2` and `P_3`, which are elliptic-curve negatives. The independently checked trace equation therefore simplifies to

```text
P_2 + P_3 + (18,31) = 4 P_19,       P_2 + P_3 = 0,
so (18,31) = 4 P_19 in 11a1(F_83).
```

The orbit trace `(18,31)` lies outside the frozen 20-point class and has no exact-coordinate match among the saved degree-5 or earlier degree-13 outside traces. Under the predeclared individual-row rule, the matrix remains at **rank 17 over both Q and F_5**. The lift completes the degree-13 fiber accounting across all 20 sources: nineteen squarefree fibers in the preceding panel and this one multiplicity-two fiber.

The [protocol](PROTOCOL.md) and [input manifest](inputs.json) froze source 19, its preceding `(1)^2(12)` factor record, the extension field, wall cap, and acceptance rule. The checked-Sage [lift](lift.py) retains the complete candidate and orbit trace in [lift-result.json](lift-result.json). The [independent validator](verify.py) enumerates the F_83 curve lifts at x=4, checks the trace equation with separate point arithmetic, and replays both ranks. It returned `DEGREE13_REPEATED_PASS`.

The feasible finite uniqueness step is also proved in [formal/RepeatedRoot.lean](formal/RepeatedRoot.lean): all 83 possible y residues and all unordered candidate pairs are checked in Lean. The pinned build and two `#print axioms` audits passed with no axioms; see the [proof map](formal/PROOF_MAP.json) and [build check](formal/CHECK.md). The extension-field Hecke lift and full group trace are tied to the theorem by the saved moments and independent replay, and remain outside this Lean module.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/hecke-degree13-repeated-20261027/sage-runtime-info.txt
gtimeout 600 ./sage -python experiments/hecke-degree13-repeated-20261027/lift.py
python3 experiments/hecke-degree13-repeated-20261027/verify.py
cd experiments/hecke-degree13-repeated-20261027/formal
lake build RepeatedRoot
```
