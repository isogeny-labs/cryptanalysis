# CT30 — geometric 7-torsion and Frobenius kernel audit

**Scientific standing:** [pcc:unverified], independent implementation but producer-run local development checks, no signed PCC verdict. This complements CT29 rational-map identities and does not reproduce the concurrently developed native Phi2/Jacobian code.

## Mathematical acceptance conditions

For a short Weierstrass E: y²=f(x)=x³+ax+b and monic degree-three h(x), require h | ψ7, where ψ7 is the degree-24 odd division polynomial (leading coefficient 7). Divisibility alone does **not** prove that an arbitrary triple of nonzero 7-torsion x-pairs forms one subgroup. In these fixtures h is irreducible cubic or fully split into three distinct rational roots, and Frobenius modulo 7 is semisimple with two distinct eigenvalues whose cubes are +1 and -1. For irreducible h, Frobenius³ fixes each root x, so Frobenius³P=±P. Because its two eigenvalues have different cubes, P belongs to exactly one eigenline; the three Frobenius-conjugate ± pairs are then the six nonzero points on that line, forming one cyclic order-seven subgroup. The quadratic character of Norm(f(α)) chooses the sign and eigenline. In the fully split case, each x is rational, all f(r) are nonsquares and Frobenius acts as -1 on each pair, so all three pairs lie on the unique -1 eigenline. The added oracle guard rejects cases where the two Frobenius-eigenvalue cubes do not differ. No point-count-only shortcut is used.

Frobenius acts on this stable cyclic subgroup by a scalar λ in F7*. The elliptic trace t determines the two possible λ as roots of λ²-tλ+101 modulo 7. For irreducible h, let α be any root in F101³. The determinant of multiplication by f(α) in the 3-dimensional F101-algebra is Norm(f(α)). Its quadratic character determines whether a y-coordinate lies in F101³: λ³=+1 for square norm, λ³=-1 for nonsquare norm. In the split-x case, the quadratic characters of f(r) at each rational root directly determine λ=±1.

| Input from CT29 | #E(F101) | Frobenius trace | h splitting | Norm or x root character | λ | Kernel point splitting field |
|---|---:|---:|---|---|---:|---|
| E109 forward, h=[99,94,75,1] | 109 | -7 | irreducible cubic | Norm=55, nonsquare | 5 | F101^6 |
| E109 backtrack, h=[58,26,58,1] | 109 | -7 | irreducible cubic | Norm=14, square | 2 | F101³ |
| E113 forward, h=[53,19,40,1] | 113 | -11 | roots 48,53,61 | f(r) nonsquare at each | 6 | F101² |
| E113 backtrack, h=[29,88,45,1] | 113 | -11 | irreducible cubic | Norm=43, square | 4 | F101³ |

The source kernels and curve coefficients were fixed by CT29, not rediscovered by this check. The 7-division polynomial and resultant/norm multiplication matrix are recomputed independently. Every tested h divides ψ7; constant-term mutation h+1 fails. [pcc:unverified]

## Reproduction, controls and limitations

```sh
python3 -B experiments/chained-transfer-reference/ct29/audit_geometric_seven_stdlib.py
python3 -O -B experiments/chained-transfer-reference/ct29/audit_geometric_seven_stdlib.py
python3 -B experiments/chained-transfer-reference/ct29/audit_rational_maps_stdlib.py
```

Local Python 3.13.5 checks passed with and without -O; an initial alternative full-polynomial computation using SymPy also reproduced h|ψ7, root factorization, and the four norms. The standalone committed oracle does not import SymPy or the producer's maps. Before claiming exact-head CI success, inspect Actions after publication. Local script and negative controls remain unverified scientific assertions; no execution receipt with trusted keyring verifier was produced.

**Distinct scope:** These are kernel point splitting degrees, not the cyclic-49 kernel splitting degrees 42/14 already present in crypto PR #3877. The result does not construct the Jacobian Phi2/Psi2, certify 2-torsion gluing, independently validate genus-2 addition, or provide any solve-cost improvement.

**Next discriminating test:** compute the 2-torsion action of both nondual elliptic maps, compare with the transported HLP anti-isometry, then replay actual native Phi2 maps and their dual identities on every 12,317 rational Jacobian class without importing the producer's group arithmetic.

**Prior art and repository context:** elliptic division polynomial/finite-field Frobenius documentation in Sage; Kohel/Vélu isogeny formula methods; cryptanalysis CT29 RESULTS.md/VERIFICATION.md; crypto PR #3877, cryptanalysis #1492 and concurrent #1493. Current KB/atlas and EKS budget gates not bypassed.
