# CT44 — Weil-pairing covariance across the degree-7/49 elliptic-factor chains

**2026-11-12 · [pcc:unverified]**. This is an independent arithmetic/obstruction preflight for the *abstract* E109/E113 four-torsion modules. It does not construct, evaluate or identify the actual native quartic/Jacobian isogenies. The root producer's concurrently completed actual quartic-gluing check is separate: [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877).

## Mathematical statement (standard isogeny pairing functoriality)

Let R=Z/4, and fix symplectically normalized four-torsion bases on two elliptic factors with the same mod-4 Frobenius companion matrix

    F = [[0,3],[1,1]], F^2-F+I=0, F^3=-I.

The actual traces -7 and -11 both reduce to 1 modulo four, and p=101 reduces to 1. In these bases every F-equivariant unit is a+bF. There are 12 units: six with determinant 1 and six with determinant 3=-1. CT43 classified the six F-equivariant Weil anti-isometries U (det U=3).

For an odd-degree isogeny phi with gcd(deg phi,4)=1, functoriality of the Weil pairing gives

    e4(phi(P),phi(Q)) = e4(P,Q)^(deg phi),

hence in symplectic bases det(M_phi) = deg(phi) mod 4. Thus a degree-7 elliptic hop has det A=3; a degree-49 two-hop composite has det=1. The matrix of the dual of a degree-7 hop is adj(A)=3*A^(-1), since dual(phi)*phi=[7]=3I on four-torsion. For degree 49, the dual is the ordinary inverse matrix because [49]=I on E[4].

If a source quartic graph is Graph(U) and the two factor maps have four-torsion matrices A and B, the **only possible transported graph**, assuming both maps and the kernel graph are the actual ones, is

    U' = B * U * A^(-1).

It remains a Weil anti-isometry when both maps have degree 7 modulo 4:

    det U' = (3)(3)(3^(-1)) = 3 mod 4.

At two hops, A2*A1 and B2*B1 have determinant 49=1 mod 4 and the same composition formula holds. All statements are algebraic consequences of standard dual-isogeny and Weil-pairing functoriality; no novelty claim.

**Counterexample acceptance rule:** If one factor is transported by a degree-seven hop and the other by a degree-one symplectic identification, the transported graph has determinant 1, *not* 3. Its product Weil pairing is nontrivial for a symplectic basis pair: with i=10 in F101, i^2=-1 and the incorrect graph pairing is -1. Reduction mod 2 misses this entirely because both +1 and -1 are 1 mod 2. This catches an orientation error that group laws and 2-torsion identifications alone would not catch.

## Independent executable arithmetic

- `ct44_covariance.py`: enumerates all 256 matrices over R, obtains the 16-element Frobenius centralizer, the six determinant-3 and six determinant-1 units. Verifies all 216 ordered one-hop (A,B,U) transports against **all 256 ordered Weil-pair comparisons each**, including explicit µ4 values in F101. Verifies all 7,776 ordered two-hop (A1,A2,B1,B2,U) transport identities, six adjugate dual identities, and 216 mismatched-degree controls that deceptively pass mod-2 pairing checks.
- `ct44_independent.js`: a separate polynomial-algebra implementation in R[F]/(F²-F+1) (not Python matrix multiplication). Checks the 6+6 determinant/norm classification, six adjugates, all 216 ring one-hop transports, 7,776 two-hop compositions, and 216 wrong-degree negative controls.
- No native Jac(T_i)[4] point or quotient was imported, and the tests do not claim to be independent scientific signature verification.

Reproduce without cloud:

```sh
python3 -B experiments/chained-transfer-reference/ct44/ct44_covariance.py
python3 -O -B experiments/chained-transfer-reference/ct44/ct44_covariance.py
python3 -m py_compile experiments/chained-transfer-reference/ct44/ct44_covariance.py
node --check experiments/chained-transfer-reference/ct44/ct44_independent.js
node experiments/chained-transfer-reference/ct44/ct44_independent.js
node --no-opt experiments/chained-transfer-reference/ct44/ct44_independent.js
```

## Evidence dependencies, scope and next gate

Sources checked before implementation: [CT43 source](../ct43/CT43_MOD4_FROBENIUS_GLUE.md); [crypto root #3877](https://github.com/isogeny-labs/crypto/pull/3877), particularly its native quartic4-glue evaluator, QUARTIC_GLUING_PROOF and frozen full-class controls; Bruin–Doerksen (2011), *The Arithmetic of Genus Two Curves with (4,4)-Split Jacobians*, https://doi.org/10.4153/CJM-2011-039-3 ; Silverman, *The Arithmetic of Elliptic Curves*, III.8 on dual isogenies and Weil pairings; Galbraith, *Mathematics of Public Key Cryptography*, Ch. 26. The shared research-KB MCP/wrapper and locked lead atlas are unavailable in this runtime; no negative literature or novelty inference is made.

**Actual-map acceptance still needed:** determine the *native* degree-seven factor-map matrices A,B on symplectically oriented E_i[4] bases, verify the resulting U' against native quartic gluing and actual A_i[4] maps through the full genus-2 Cantor engine (including ramified, nonsplit, extension-field classes). Apply matching tests to both hops and all six directions, with a wrong-degree map and a determinant-one graph as negative controls. The producer root has concurrent full-A[4] work; do not duplicate or overwrite it. Theoretical conjugacy is necessary, not sufficient for an actual geometric correspondence.

The discrete-log advantage question is unchanged: no target-specific full-cost rho/index-calculus comparison, solver improvement, paid compute, S3 access or signature is asserted by CT44. No budget, protected-branch or ledger change was made. **Standing: [pcc:unverified].**
