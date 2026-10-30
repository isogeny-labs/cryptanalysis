# Degree-13 Frobenius order three changes the D=-79 trace geometry

At the prespecified second field prime **p=179**, the D=-79, conductor-2 rational X_0(11) class again has 20 points, but every degree-13 neighbor-x fiber splits as `(1)(1)(3)(3)(3)(3)`. All 20 squarefree fibers were lifted and verified in F_(179³). Their Frobenius orbit traces yield one individually class-closed relation, raising the saved rational degree-2/5 matrix from **rank 10 to 11 over both ℚ and F₁₃**. The other 19 source equations have outside-class traces; none share the complete outside-trace multiset required by the frozen support-two difference rule.

The change in cycle geometry has an exact finite-field explanation at the kernel level. For CM trace magnitude 20 and p=179, the Frobenius characteristic polynomial modulo 13 has distinct roots 2 and 5 (for the positive trace sign). Their ratio is `2/5 = 3 mod 13`, of order three. At p=83, the corresponding roots for trace magnitude four are 7 and 10, with ratio `10/7 = 7 mod 13` of order twelve. The [Lean module](formal/FrobeniusRatio.lean) checks both root identities and both exact orders without axioms. The identification of this projective action with each saved degree-13 Hecke fiber is checked experimentally by the independently refactored neighbor polynomials; the general correspondence bridge remains an open formalization step.

| Prespecified field | Class points | Degree-13 factor pattern | Individually closed traces | Outside-trace equations |
| --- | ---: | --- | ---: | ---: |
| p=83, prior panel | 20 | 19 `(1)(1)(12)`; one `(1)^2(12)` | 5 | 14 plus one repeated-root status |
| p=179, this panel | 20 | 20 `(1)(1)(3)^4` | 1 | 19 |

For p=179, the X_0(11) curve has 195 points and largest prime factor 13. Ten degree-2 rows and no degree-5 rows are individually class-closed in the frozen base. The one degree-13 closed row is from source 8 in the new field's lexicographic point order:

```text
P_3 + P_6 + P_10 + P_11 + P_13 + P_19 - 4 P_8 = 0.
```

The [protocol](PROTOCOL.md) fixed the first-prime selector, source hash, extension and time caps, row policy, and all failure statuses before output. The checked-Sage [producer](run.py) retained all 20 factor patterns, all 120 Frobenius orbit traces, source equations, ranks, and zero equal-trace pairs in [result.json](result.json). Its runtime and logs are saved beside the result. The [independent integer-field replay](verify.py) counted the 195 group points directly, verified every saved trace and class group equation, reconstructed the closed row and equal-trace pair list, and reproduced all rational and F₁₃ ranks. The [separate checked-Sage audit](validate_sage.py) enumerated the entire 195-point group, found exactly the saved 20 class members by j-trace magnitude, and refactored every degree-13 neighbor polynomial. Both audits passed; their outputs are [validation.json](validation.json) and [sage-validation.json](sage-validation.json).

The result isolates a concrete sensitivity of trace-row closure to the projective Frobenius order: the same 20-point CM class size supports four degree-3 auxiliary traces per source at p=179, versus one degree-12 auxiliary trace in the common p=83 pattern. A next bounded test should enumerate support-three group-law cancellations of the p=179 outside traces and replay their incremental F₁₃ rank. That would distinguish exact-trace-pair scarcity from a broader failure of short trace closure.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/hecke-d79-second-prime-20261027/sage-runtime-info.txt
gtimeout 900 ./sage -python experiments/hecke-d79-second-prime-20261027/run.py
python3 experiments/hecke-d79-second-prime-20261027/verify.py
gtimeout 180 ./sage -python experiments/hecke-d79-second-prime-20261027/validate_sage.py
cd experiments/hecke-d79-second-prime-20261027/formal
lake build FrobeniusRatio
```
