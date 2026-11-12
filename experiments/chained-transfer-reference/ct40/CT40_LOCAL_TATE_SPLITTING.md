# CT40 — Prime-to-202 local Tate-module projector splitting

**Date:** 2026-11-12. **Scientific standing: [pcc:unverified].**
Scope: the three fixed F_101 Jacobians in crypto PR #3877, conditional on their CT39 characteristic polynomial, not an arbitrary genus-2 curve or an ECDLP algorithm. This is an instance of standard Frobenius/Chinese-remainder algebra; no novelty or cost advantage is claimed.

## Precise input and result

CT39 separately reconstructed the complete characteristic polynomial on each fixed T0, T1, T2 Jacobian:

`P(T)=f109(T) f113(T)`, with
`f109(T)=T^2+7T+101`, `f113(T)=T^2+11T+101`.
These point counts are separate unsigned evidence, not rechecked by the CT40 matrix oracle.

**Proposition (conditional on P).** Let J/F_101 be any abelian surface whose Frobenius has characteristic polynomial P. For every prime `ell != 2,101` and integer `n>=1`, the finite etale Galois module `J[ell^n](Fbar_101)` has **canonical Frobenius-polynomial complementary idempotents** `e109,e113`, and decomposes into their images. Every F_101-defined subgroup `H <= J[ell^n]` is the direct sum of its two intersections with these images. Every F_101-defined homomorphism between two such surfaces respects this decomposition on ell-power torsion. The statement covers all ell-adic depths, not merely inspected finite powers.

The explicit **integral** polynomial identity over Z[T] is

```
A(T)=-(T+7) f113(T)= -T^3-18T^2-178T-707
B(T)= (T+11)f109(T)=  T^3+18T^2+178T+1111
A(T)+B(T)=404=4*101
A(T) B(T)=-(T+7)(T+11) P(T).
```

For a fixed `m=ell^n`, define `u = 404^(-1) mod m` and

```
e109 = u A(pi)|J[m],       e113 = u B(pi)|J[m].
```

These are **integral operators on J[m]** (scalars taken mod m), even though the global projectors A(pi)/404 and B(pi)/404 generally lie only in the rational/localized endomorphism ring. This is not a claim that a principally polarized Jacobian is an integral product of the two elliptic curves.

## Mathematical proof

By Cayley–Hamilton for the ell-adic Frobenius action, `P(pi)=0` on `J[ell^n]`. From `A+B=404` and `AB=-(T+7)(T+11)P`, the operators satisfy

```
e109 + e113 = 1,
e109 e113 = 0,
e109^2 = e109,   e113^2 = e113.
```

Indeed, `A^2-404A=-AB` and similarly for B. Further, `f109(pi) A(pi)=0` and `f113(pi) B(pi)=0`, so the first image is annihilated by f109 and the second by f113; each is rank two at the Tate-module level, because the f109 and f113 primary blocks each have degree two. These are the canonical distinct Frobenius-isotypic components, not individual Frobenius eigenlines.

If H is F_101-defined, its geometric points are stable under pi. As e109 and e113 are polynomials in pi with integer coefficients mod m, they preserve H. Thus each h in H equals e109(h)+e113(h), with zero intersection by orthogonality. If phi:J→J' is an F_101 homomorphism and both Weil polynomials are P, then phi pi_J=pi_J' phi, so `phi e_i=e_i' phi` on ell-power torsion. This proves block preservation for every such map, including the actual Phi/Psi maps *provided their construction and field of definition are separately certified*. No rational-point corpus or conjectural map is used in the argument.

For `ell != 101`, all ell-power torsion is finite etale, so the geometric-point statement transfers to subgroup schemes. This establishes the conditional theorem for all n.

## Why the excluded primes matter

- At `ell=2`, 404 is not invertible and `f109 ≡ f113 ≡ T²+T+1 mod 2`. Frobenius-polynomial CRT separation fails. This is **compatible with**, but does not establish, the observed 2-primary Richelot/HLP gluing. No claim that every 2-kernel mixes is made.
- At `ell=101`, 404 is not invertible and both reduced factors share the root zero. Also 101-primary torsion is not generally finite etale. This particular argument does not cover it.
- The result does not rule out odd-degree within-component isogenies; it rules out mixing of the two distinct Frobenius primary components by any F_101 homomorphism on ell-primary torsion for `ell != 2,101`. It is not a generic ECDLP lower bound or a computational transfer across characteristics.

For the existing 7/49 kernel, the two components therefore *must* remain separated on every 7^n torsion group. The selected degree-7 elliptic kernels and CT32/33/34 direct degree-49 map are compatible with the theorem. It does **not** certify the actual native Phi2/Psi2 kernel, polarization, dual, or Jacobian evaluation; those remain separate obligations.

## Independent executable arithmetic control

The new Node.js standard-library-free arithmetic oracle `ct40_projector_audit.js` reconstructs P, A, B over exact integer polynomials. Independently of the producer Jacobian engine, it evaluates these polynomials on two 2x2 Frobenius companion blocks modulo 30 prime powers `ell^n` for `ell=3,5,7,11,13,17,19,23,29,31` and `n=1,2,3`. It checks rank-2 block selection, sum one, idempotence, orthogonality and commuting with Frobenius. A deliberately wrong second trace 12 fails idempotence modulo 7. It tests the mod-2 polynomial collision and common mod-101 root. All checks throw exceptions, never Node assertions that can be disabled.

```sh
node experiments/chained-transfer-reference/ct40/ct40_projector_audit.js
```

The algebraic argument proves **all** eligible primes and depths; the 30 matrix checks are diagnostic controls, not a finite search proving that universal statement. Ordinary local run passed before the source commit; CI result must be inspected at its actual commit SHA. **[pcc:unverified].**

## Source audit and boundaries

- crypto `research/chained_jacobian_transfers_20261110/ODD_KERNEL_CHECKPOINT.md`: earlier fixed 3/5/7 RREF/torsion projectors and exceptional polarization discussion.
- cryptanalysis `experiments/chained-transfer-reference/ct37/CT37_FROBENIUS_ISOTYPY.md`: earlier exact Bezout 404 and *rational* projectors; CT40 does not claim the polynomial identity or abstract Hom-zero was new.
- cryptanalysis `experiments/chained-transfer-reference/ct39/CT39_TWO_FIELD_ZETA.md`: exact characteristic polynomial on the actual T0/T1/T2 curves; independently rechecking that corpus is outside CT40.
- J.S. Milne, *Abelian Varieties* (2008), sections on Tate modules and Frobenius: https://www.jmilne.org/math/CourseNotes/av.html
- *Finite group subschemes of abelian varieties over finite fields* (2014): https://doi.org/10.1016/j.ffa.2014.04.001 ; existing theory of Frobenius actions on prime-to-p torsion.
- Shared research-KB MCP is unavailable in this tool runtime; the encrypted autoresearcher atlas remains locked, and no novelty/absence claim is made.

**Not performed:** direct Phi2/Psi2 geometric-kernel construction or proof replay, full independent nonlinear Cantor-map evaluation, Lean formalization of the geometric objects, PCC independent scientific signing, EKS/S3 paid jobs, or matched cold rho/index-calculus comparisons. The next decisive work is the actual native map projection and geometric 7-kernel check, not another finite companion-matrix table.
