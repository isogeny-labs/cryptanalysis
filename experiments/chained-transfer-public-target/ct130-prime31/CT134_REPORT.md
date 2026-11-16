# CT134 — explicit CM pullback to the original prime-field curve

**15 November 2026 · producer-only [pcc:unverified].** Companion to the preregistered [CT134 protocol](CT134_PROTOCOL.md), stacked on cryptanalysis #1542 and ultimately crypto #3877. The independent-host CT133 ratios on the deliberately CM-neighbor toy are *not* proof of a complete generic ECDLP speedup; this control tests a stronger original-curve operation not tested by CT133. We did not modify CT133 or any original 695/701-record Jacobian fixture.

## Algebraic result and test

The frozen E over p=2147483033 has j=287496, q=536857417, and a rational 2-isogeny phi to T:y²=x³+9x, j=1728. Write a=622683939, b=2147483024, r=969960860 and a'=-2a, b'=a²-4b (mod p). For target point (X,Y) set x'=4(X-r), y'=8Y. The normalized dual used here is

    psi(X,Y) = ((x' + a' + b'/x')/4, y'(1-b'/x'^2)/8).

This is the standard dual for the normalized 2-isogeny, with exceptional infinity/kernel branches. Let alpha(X,Y)=(-X,iY), i=392507391. Define beta=psi alpha phi. On the stated odd prime-order subgroup, phi psi=psi phi=[2], beta=[2lambda], beta²=[-4] and A=[(q+1)/2]beta=[lambda], where lambda=390258842 mod q; hence A²=[-1]. The equalities were checked using direct finite-field arithmetic at 23 distinct, fixed and seeded source scalars, with explicit rejection under Python -O and source-point verification. The source-side subgroup action is real, but **A is not a degree-one algebraic automorphism of E**: since j(E) is neither 0 nor 1728 in characteristic >3, its degree-one origin-fixing algebraic automorphisms are only +/-1. A can instead be evaluated by beta followed by subgroup scalar multiplication by inverse two.

Thus there is no cheap degree-one fourfold source automorphism corresponding to alpha. This is a precise obstruction to one comparison arm, **not** a lower bound on all source-side implementations or a proof of the CT133 target advantage against strongest rho.

## Bounded map-only measurement (developer-local, nonadmitted)

Source checked byte SHA256 `36321838d6dbe90418d79d26c8cfbaa3d87b98b1ff9ffe3be5251256b3659c4c`, Git blob SHA1 `1fb2f6d128b7633bcd0d99b4683b41062845745b` (matches the remotely fetched committed blob). Command:

```sh
python3 -S experiments/chained-transfer-public-target/ct130-prime31/ct134_pullback.py > ct134-run.json
python3 -O -S experiments/chained-transfer-public-target/ct130-prime31/ct134_pullback.py > ct134-run-O.json
```

One local process, 23 pinned public points, 16 repetitions per arm per observation, four alternating ABBA/BAAB quartets, 368 evaluated point actions per timed sample. Every source action in the literal psi-alpha-phi / scalar-half implementation consumes 49 source EC addition calls and 50 modular inversions (48 from those additions and 2 from phi/psi). Target alpha consumes one multiplication by i and sign-change, with no EC additions or inversions.

| Block | Source-side A over target alpha map-only time |
|---|---:|
| 0 | 328.97x |
| 1 | 343.70x |
| 2 | 342.52x |
| 3 | 316.30x |

These **Python map-only** ratios include interpreter and checking overhead; they are not clock-normalized C++ data, are not cold ECDLP solve ratios, and cannot be extrapolated to optimized point arithmetic. The original raw local outputs have SHA256 `ca51ac39800b7431cefac9ff7722017c34af3c9d9c364bc83507904cfb7c7781` (normal) and `9ab5b5b94c91d8b0bbf1b065b0717628b32bc9cf2f1b6ae9cccb2dbf3c93fd3e` (optimized). Those per-block timing records remain producer-local, not signed or independently replayed.

## Performance decision

**Do not spend cycles on a naive per-iteration source-side A=[1/2] psi alpha phi map.** It loses map-operation cost by construction. The stronger source comparator is an optimized rho that can use any genuinely cheap explicit degree>1 endomorphisms (or computationally transfer to the target itself), with matched memory, actual cold setup and verification. CT133 #1542 remains a scoped native toy victory over *two named source references*, not the owner's complete-solve result. CT126 #1534 C169/C13a/C13b/D pricing and full CT1523/3877 original-prime Jacobian corrections remain open, as do strongest source rho, BSGS and IC. If the stronger baseline closes the gap, retain this as a negative control and redirect to non-generic IC relation finding.

## Sources and evidence standing

Read crypto #3877/#4215, cryptanalysis #1534/#1539–1542; classical Vélu dual 2-isogeny formulas; GLV automorphism literature; explicit finite-field isogeny homomorphism discussion in [SQISign specification §2.3](https://www.math.u-bordeaux.fr/~damienrobert/pro/publications/reports/SQISign-nist2-spec.pdf). Research-KB MCP/checkout CLI unavailable here. No independent signed PCC, end-to-end complete-solve or original-prime bridge is claimed.
