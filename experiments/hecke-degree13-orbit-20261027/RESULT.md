# Degree-13 orbit traces raise the D=-79 class rank from 16 to 17

On the frozen 20-point D=-79, conductor-2 class over F_83, the degree-13 Hecke correspondence supplies five individually class-closed Frobenius-orbit trace rows. Added to the corrected degree-2 and verified degree-5 orbit rows, they raise rank from **16 to 17 over both Q and F_5**. The source-3 row is the rank-increasing one in ascending-source insertion order:

```text
2 P_10 + P_19 - 4 P_3 = 0  in 11a1(F_83).
```

The checked producer verifies all fourteen lifted neighbors, their Hecke moments, modular-polynomial roots, and group sum for each squarefree fiber. An independent pure-Python implementation checks the F_83 group sums and reproduces the rational and F_5 ranks.

| Degree-13 fiber outcome | Sources | Observed result |
| --- | ---: | --- |
| All orbit traces in the frozen class or identity | 5 | Five exact rows; combined rank 17 |
| A trace outside the frozen class | 14 | Trace recorded; no class-only row inserted |
| Repeated rational x-root | 1 | Source 19 retained for a multiplicity-aware lift |

Nineteen neighbor-x polynomials factor as `(1)(1)(12)` over F_83; source 19 factors as `(1)^2(12)`. Every splitting degree is 12. This matches the predeclared projective Frobenius cycle lengths `1,1,12` modulo 13 at the kernel level, while the repeated x-root is an image collision. The degree-13 outside traces have no exact-coordinate match among the saved degree-5 outside traces under this panel's join rule.

The [protocol](PROTOCOL.md) fixed all 20 sources, degree 13, the extension cap, 600-second wall cap, and row acceptance rule before output. [inputs.json](inputs.json) pins the class and preceding relation receipts. The successful checked-Sage run and its runtime are in [producer-stderr.txt](producer-stderr.txt), [producer-output.txt](producer-output.txt), and [sage-runtime-info.txt](sage-runtime-info.txt). The first attempt completed the fiber computation but failed at final JSON serialization of a Sage integer; its failed logs are retained. The rerun changed only that conversion.

The [independent validator](verify.py) verifies every saved trace point with separate F_83 group arithmetic, reconstructs the five class rows, and performs exact rational and F_5 elimination. It returned `DEGREE13_ORBIT_TRACE_PASS`. A short F_5 separator makes the rank increment auditable: the vector with nonzero coordinates `w_2=4, w_3=2, w_4=2, w_6=3, w_18=3, w_19=1` annihilates every one of the 20 preceding relation rows, while its dot product with the source-3 row is `3 mod 5`. [formal/RankWitness.lean](formal/RankWitness.lean) checks both finite statements without axioms, generated reproducibly by [formal/generate.py](formal/generate.py). The [proof map](formal/PROOF_MAP.json) and [build check](formal/CHECK.md) delimit the finite Lean certificate and the independently checked elliptic-curve bridge.

The next bounded experiment is a multiplicity-aware lift for source 19's `(1)^2(12)` fiber. Its y-pair reconstruction can use the six-moment method from the degree-5 source-18 follow-up, extended to fourteen moments.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/hecke-degree13-orbit-20261027/sage-runtime-info.txt
gtimeout 600 ./sage -python experiments/hecke-degree13-orbit-20261027/run.py
python3 experiments/hecke-degree13-orbit-20261027/verify.py
cd experiments/hecke-degree13-orbit-20261027/formal
python3 generate.py
lake build RankWitness
```
