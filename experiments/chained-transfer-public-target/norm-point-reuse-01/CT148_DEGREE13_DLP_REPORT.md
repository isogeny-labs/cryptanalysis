# CT148 — genuine degree-13 isogeny: subgroup order, full DLP recovery and collision cost

Date: 2026-11-15 America/Denver. Parent cryptanalysis #1589; root crypto #3877. **[pcc:unverified]**. CT148 is an exact finite toy mathematical/control result, not an original-q223 transfer or a measured speedup.

## Algebraic theorem and relevance

For a group homomorphism γ:E→E' and a source cyclic generator G of exact order n, the image of [x]G determines x mod n if and only if the image generator has order n, equivalently ⟨G⟩∩ker(γ)={O}. If the image generator has order m<n, the target image determines only x mod m and every target instance has n/m indistinguishable source scalars. For a separable degree-d isogeny, gcd(n,d)=1 is a sufficient (not necessary) injectivity test. Each degree-13 hop and composite transfer must establish this on the actual source generator; a faster DLP in a quotient is not a complete ECDLP unless missing kernel/coset information is recovered and priced.

The finite check instantiates a degree-13 rational Vélu quotient on E(F_229): y^2=x^3+x^2+x. The deterministic 13-kernel generator is (49,65). The resulting target is y^2=x^3+x^2+223x+13 (cubic discriminant 148 mod 229, nonzero). Whole-group order is 208 on both curves; kernel has 13 points; rational image has 16 points. Code verifies all 43,264 source-pair group-addition identities and all input/image curve membership/exceptional poles. These finite computations do not constitute a global function-field formal proof or original-q223 map certification. [pcc:unverified]

## Reproduced local developer-only output

| Metric | Observed |
|---|---:|
| E(F229), E'(F229) | 208, 208 |
| Kernel and image | 13, 16 |
| Group-homomorphism pairs checked | 43,264 |
| Safe generator (69,12): source/image orders | 8 / 8 |
| Safe public BSGS target solves, verified on source | 8/8 |
| Unsafe generator (2,48): source/image orders | 104 / 8 |
| Ambiguous source candidates per target-only DLP | 13 |
| Naive target-only scalar answers rejected by source verification | 96 / 104 |
| Direct source BSGS public solves | 104/104 |
| Target BSGS plus source coset-repair full solves | 104/104 |
| Source scalar candidate comparisons for all 104 repaired solves | 728 |
| Repair worst-case source candidate comparisons | 13 |

An exact collision witness: source scalars **0 and 8** (mod 104) map to the same target point even though their source points differ. Target-only BSGS yields a residue mod 8; it is not a 104-element ECDLP solve. Complete source-side coset repair tests x=r+8j for j=0,...,12, verifies the original point, and recovers every public scalar. Across the frozen 104-scalar cohort it costs 728 source-point candidate comparisons (average 7, maximum 13). Source BSGS independently solves the same 104 targets. No wall-time comparison is performed and this operation count alone is **not** a runtime advantage or disadvantage claim.

The difference is exactly what an original degree-13/169 chain must price when any hop intersects the source DLP subgroup. If that original generator has order coprime to 13, this particular obstruction vanishes; that requires checking its actual order and map image rather than inferring it from the degree. A chain might carry auxiliary side information that distinguishes fibers, but its cost must enter the cold solver. [pcc:unverified]

## Execution and custody

Local sandbox, standard library only; source file SHA-256 (developer-local) `e585751d7cd7f120f13ea141c0766cc5e176cdbc869d6e4f572c48b95448bcce`, normal JSON SHA-256 `a93280a0658169753d9d32a3d5f3a1219c33fcc2938645a89a718d7f802a8ea7`. Identical byte-for-byte normal vs optimized `python3 -O` JSON results; local 208-point and 43,264-pair tests succeeded. This is **producer-run**, with no independent signed PCC claim. The source-only CI workflow checks all frozen numbers and witness values; hosted result must be inspected independently, not inferred from this report.

Reproduce from feature branch:

```sh
python3 experiments/chained-transfer-public-target/norm-point-reuse-01/ct148_velu13_subgroup_canary.py > /tmp/ct148-normal.json
python3 -O experiments/chained-transfer-public-target/norm-point-reuse-01/ct148_velu13_subgroup_canary.py > /tmp/ct148-opt.json
cmp /tmp/ct148-normal.json /tmp/ct148-opt.json
```

The finite protocol `CT148_DEGREE13_DLP_PROTOCOL.md` was repository-committed before the code. The exploratory local prototype preceded that commit, so **neither this extension nor its measurements are claimed as a prospectively blinded performance result**. The complete-repair extension was added after observing the initial finite collision and is described accordingly.

## Next required original-prime gates

1. On exact q223 source/target generators (and any cofactor/corrected lift used in the 695/701 cases), verify full-order membership and compute the **image-generator order after each degree-13 hop and the 169 composite**; retain any exceptions and negative outcomes. Do not confuse the norm corrected-half identity CT146/147 with DLP injectivity.
2. Execute unfiltered original vs norm-reuse compiled Rust sources on the frozen fixture; independent Jacobian norm and exception parity, including all 695 records. Avoid concurrent branch duplication.
3. With owner admission, measure same-host cold C169,C13a,C13b,D, and complete rho/BSGS/IC reference costs (all transfer, setup, LA, verification, RSS, uncertainty and PCC).
4. If the actual source generator has no kernel intersection, this finite counterexample is a **general guard only**, not an obstruction for the real transfer. If it does intersect, price exact coset recovery or decline the full-DLP speedup claim.

References: SageMath isogeny documentation https://doc.sagemath.org/html/en/reference/arithmetic_curves/sage/schemes/elliptic_curves/ell_curve_isogeny.html, Silverman III.4.8, CT125 #1533, CT145 #1584 and CT146/147 #1589, root crypto #3877 and original Jacobian #1523. Research-KB/Conductor were unavailable in this connector runtime; prior work and primary files were reviewed. No EKS/Spot, paid compute, protected merge, frozen science edits or signed PCC occurred. [pcc:unverified]
