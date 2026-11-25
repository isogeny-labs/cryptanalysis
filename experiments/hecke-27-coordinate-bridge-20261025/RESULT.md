# Exact coordinate bridge for the quarter-shift evaluator

The two \(j\)-invariants of a cyclic 27-isogeny now determine coordinates on the optimal model \(C=X_0(27):y^2+y=x^3-7\) for the finite-field outputs of the quarter-shift evaluator. Exact q-series linear algebra produced both rational \(j\)-functions on \(C\). Inverting them gave one point for each of the four previously computed level-27 moduli pairs. At \(p=883\), the two conjugate points descend through the twist and dual three-isogeny to the exact point \((16,558)\) on \(B: y^2=x^3-16\), the optimal level-432 curve.

## Coordinate functions and certification

Let \(P=(x,y)\in C\), with the cusp \(\infty\) as origin. `coordinate_map.json` stores rational functions in the form \(A(P)j(P)+N(P)=0\) for the source \(j(\tau)\) and target \(j(27\tau)\). The basis monomials are \(x^a y^b\), \(b\in\{0,1\}\), with pole order \(2a+3b\) at infinity. The source function has \(A\in L(35\infty)\), \(N\in L(36\infty)\); the target function has \(A\in L(9\infty)\), \(N\in L(36\infty)\). The respective interpolation matrices have unique kernels at those bounds and zero kernels one bound lower. Each identity was fitted on q-exponents \(-36\) through 59 and checked independently on exponents 60 through 107.

The coefficient check also proves the rational-function identities, subject to the standard modular-curve fact that each \(j\)-projection has degree \([\mathrm{SL}_2(\mathbf Z):\Gamma_0(27)]=36\). Indeed, \(A j+N\) has pole degree at most 71 in the source case and 45 in the target case, while the verified q-series vanishes to order at least 108 at infinity. A nonzero rational function cannot have more zeros than poles. The source coordinates and q-expansion come from [Sage's modular parametrization](https://doc.sagemath.org/html/en/reference/arithmetic_curves/sage/schemes/elliptic_curves/modular_parametrization.html) of [the optimal model `27a1`](https://www.lmfdb.org/EllipticCurve/Q/27a1/). As an independent coordinate normalization check, the [published eta-product isomorphism](https://www.claymath.org/wp-content/uploads/2022/03/cmip08c.pdf) to \(Y^2+9Y=X^3-27\) agrees through q-exponent 59 after \(x=X,\ y=-Y-5\).

The functions also satisfy the exact identity

\[
j_{\mathrm{source}}(P)=j_{\mathrm{target}}\bigl((3,-5)-P\bigr)
\]

in \(\mathbf Q(C)\). `verify_involution_sage.py` proves this by function-field equality, while `test_involution_sage.py` checked 813 defined points over \(\mathbf F_{877}\). The rational addition formula preserves \(C\) for \(x\ne3\); its addition coordinates, numerator identity, and point-on-curve implication are separately checked in `formal/CoordinateInvolution.lean`. The identity exhibits the level-27 Atkin–Lehner exchange in this model and reduces the data needed to evaluate both \(j\)-projections.

## Evaluated finite-field points

`evaluate_sage.py` eliminates \(y\) from the two linear-in-\(y\) equations, takes roots over the input field, and retains only points on \(C\) with both denominator values nonzero and both \(j\)-values exact. The input pairs come from the earlier [quarter-shift moduli evaluator](../hecke-432-moduli-shift-evaluator-20261025/result.json).

| Input field | Quarter shift | \((j(E),j(E/C_{27}))\) | Recovered point on \(C\) |
| --- | --- | --- | --- |
| \(\mathbf F_{877}\) | plus | \((780,682)\) | \((285,416)\) |
| \(\mathbf F_{877}\) | minus | \((215,707)\) | \((271,629)\) |
| \(\mathbf F_{883^2}\) | plus | exact extension-field values in `coordinate_evaluation.json` | \((34u+344,619u+111)\) |
| \(\mathbf F_{883^2}\) | minus | Frobenius conjugates of the plus values | \((849u+480,264u+821)\) |

The two \(\mathbf F_{883^2}\) points are Frobenius conjugates. Their difference is \(D=(272,731u+745)\). With the same oriented \(i\) recorded by the moduli evaluator, \((-4x(D),-8i(y(D)+1/2))=(678,741)\in E(\mathbf F_{883})\), where \(E:y^2=x^3+432\). The checked dual-isogeny equation gives its unique \(\mathbf F_{883}\)-rational lift \((16,558)\in B(\mathbf F_{883})\), and direct replay maps that point back to \((678,741)\). The label `plus` is tied to the recorded Weil-pairing orientation; matching it to the analytic `+1/4` convention still requires a sign calibration.

## Proof map and scope

| Result | Certificate | Status |
| --- | --- | --- |
| Rational \(j\)-functions on \(C\) | q-series coefficients, unique interpolation kernels, 48-exponent holdouts, pole-degree argument | Exact mathematical certificate; the modular-curve divisor bridge is written here and not formalized in Lean |
| Eta-product model normalization | `verify_eta_sage.py` | Exact q-series equality through exponent 59 |
| \(j\)-function exchange under \(P\mapsto(3,-5)-P\) | `verify_involution_sage.py` | Exact identity in \(\mathbf Q(C)\) |
| Rational addition formula preserves \(C\) | `CoordinateInvolution.numerator_identity`, `addition_coordinates`, `involution_preserves_curve` | Lean checked; `#print axioms` shows only `propext`, `Classical.choice`, `Quot.sound` |
| Full modular interpretation and degree-36 pole divisor | no Lean declaration | Written proof uses standard modular-curve properties; formalization remains partial because the required modular-curve and divisor definitions are absent from this Lean module |

This completes a forward finite-field evaluation on the specified \(X_0(432)\) inputs. The next experiment is to compute fibers of the map \(X_0(432)\to B\) for independently selected points on \(B\), using the new coordinate bridge to test coverage, fiber cost, and whether any Hecke relation rows give new rank under a fixed resource cap. Keep those questions separate from the exact forward-map result.

Replay from the repository root with `./sage -python experiments/hecke-27-coordinate-bridge-20261025/derive_j_sage.py`, followed by `evaluate_sage.py`, `verify_eta_sage.py`, `test_involution_sage.py`, and `verify_involution_sage.py` through the same checked launcher. `sage_runtime.json`, the JSON receipts, and `SEAL.sha256` bind the exact run. The Lean module builds with the pinned toolchain and Mathlib revision in `formal/DEPENDENCIES.json`; `formal/build-output.txt` contains the axiom audit.
