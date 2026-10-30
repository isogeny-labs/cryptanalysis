# Orbit-trace cancellation raises the D=-79 class rank to 16

The degree-5 Frobenius-orbit construction now covers all 20 points of the frozen D=-79, conductor-2 class over F_83. A multiplicity-aware lift resolves the one repeated-x fiber at source 18 and supplies a sixth individual class-only row. Four pairs of other fibers share exactly the same outside-class trace point; subtracting each pair cancels that point and supplies four further exact rows on the original 20-point class. Together these ten orbit-derived rows raise the corrected degree-2 rational rank from **10 to 16**.

| Rows added to corrected degree-2 matrix | Rational rank |
| --- | ---: |
| None | 10 |
| Six individually class-closed trace rows | 14 |
| Four outside-trace cancellation rows as well | 16 |

The individually closed sources are `0, 1, 3, 6, 10, 18`. At source 18, the repeated rational x-root is `x=0` with multiplicity two. The six Hecke moments determine a y-sum of 82; enumeration and the curve, modular-polynomial, moment, and group-sum checks leave the unique pair `(0,40)` and `(0,42)`. Its quartic Frobenius orbit traces to class point 18, yielding the class row `P_0 + P_1 = 0` after the source term cancels.

| Shared outside trace point | Subtracted source rows | New row status |
| --- | --- | --- |
| `(7,26)` | 19 minus 8 | Exact class-only row |
| `(7,56)` | 4 minus 2 | Exact class-only row |
| `(53,24)` | 9 minus 7 | Exact class-only row |
| `(64,62)` | 15 minus 11 | Exact class-only row |

The [protocol](PROTOCOL.md) fixed the source-18 lift and lowest-source subtraction rule before output. [inputs.json](inputs.json) pins the class, corrected rows, preceding orbit census, and Hecke builder. The [checked Sage lift](lift.py) retains the unique candidate and its orbit traces in [lift-result.json](lift-result.json). [combine.py](combine.py) records the exact four row differences, all outside-point clusters, and the sequential rank path in [result.json](result.json). The [independent validator](verify.py) reconstructs all 20 orbit trace sums with separate F_83 group arithmetic, checks the repeated pair, verifies every row difference, and performs exact rational elimination. It returned:

```text
ORBIT_CANCELLATION_PASS closed 6 pair_rows 4 rank 10 -> 14 -> 16
```

The finite free-module cancellation step is also checked for all four pairs in [formal/OrbitCancellation.lean](formal/OrbitCancellation.lean); `#print axioms` reports none. The [proof map](formal/PROOF_MAP.json) and [build check](formal/CHECK.md) separate that Lean step from the extension-field Hecke correspondence and the F_83 group-law receipts. The latter and the exact rank calculation remain finite computation certificates, independently replayed rather than formalized in Lean.

The remaining six outside trace points occur at only one source under this one-degree policy. A next experiment can enlarge the frozen trace graph or test another correspondence to pair those points; its input law and row-elimination rule should be frozen separately.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/hecke-orbit-cancellation-20261027/sage-runtime-info.txt
./sage -python experiments/hecke-orbit-cancellation-20261027/lift.py
python3 experiments/hecke-orbit-cancellation-20261027/combine.py
python3 experiments/hecke-orbit-cancellation-20261027/verify.py
cd experiments/hecke-orbit-cancellation-20261027/formal
lake build OrbitCancellation
```
