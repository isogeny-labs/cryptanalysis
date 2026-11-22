# CT36 — elliptic reverse degree-7 kernels and cyclic-49 dual

**2026-11-12 | unsigned development [pcc:unverified]**

This is the independent *elliptic-factor* continuation of crypto [#3877](https://github.com/isogeny-labs/crypto/pull/3877), cryptanalysis [#1492](https://github.com/isogeny-labs/cryptanalysis/pull/1492), [#1495](https://github.com/isogeny-labs/cryptanalysis/pull/1495), [#1499](https://github.com/isogeny-labs/cryptanalysis/pull/1499) and [#1500](https://github.com/isogeny-labs/cryptanalysis/pull/1500). It **does not** duplicate the separate genus-2 Cantor replay in [#1501](https://github.com/isogeny-labs/cryptanalysis/pull/1501).

## Exact concrete kernels

All four cubics below use coefficient order (constant, x, x², x³). For each hop, the normalized forward 7-isogeny E_i -> E_{i+1} has the given h; the independently enumerated normalized reverse 7-isogeny has h_dual and codomain E_i^(7), *not E_i*.

| Chain | E_i (a,b) | E_{i+1} (a,b) | h forward | h reverse | Reverse target (a,b) |
|---|---|---|---|---|---|
| order 109, hop 0 | (1,46) | (26,58) | (72,100,35,1) | **(58,26,58,1)** | (78,72) |
| order 109, hop 1 | (26,58) | (59,27) | (99,94,75,1) | **(13,62,81,1)** | (8,82) |
| order 113, hop 0 | (44,21) | (69,50) | (59,46,8,1) | **(29,88,45,1)** | (99,68) |
| order 113, hop 1 | (69,50) | (23,7) | (53,19,40,1) | **(11,64,23,1)** | (29,8) |

For an F101 elliptic curve E:y²=x³+ax+b, let s_u:(x,y) -> (u² x,u³ y) into E^(u): y²=x³+u⁴ a x+u⁶ b. The normalized reverse map psi_i equals s_7 composed with the classical unnormalized dual of phi_i. Thus:

    psi_i o phi_i = s_7 o [7].

The normalized two-hop reverse is Psi=s_7 o psi_0 o s_(1/7) o psi_1, mapping E2 to E0^(49), and satisfies

    Psi o (phi_1 o phi_0) = s_49 o [49].

Here the outer s_7 takes E0^(7) to E0^(49), so normalization works under composition. This is classical dual-isogeny mathematics, not a new theorem.

## Exact algebraic construction and validation

The independently implemented standard-library Python oracle contains its own point arithmetic, polynomial ring arithmetic, codomain Newton sums, 7-division polynomials, normalized Vélu x/y-map evaluation and scalar multiplication. It imports none of the CT29-35 engines or producer numerators. The supplied forward cubics and coefficient models are assumptions inherited from CT29; the reverse cubics are separately checked.

For monic cubic h=x³+h2*x²+h1*x+h0 and f=x³+ax+b, its normalized x-map is X=N/h² with

    N=(7x+2h2)*h² - 2f'*h'*h + 4f*(h'²-h*h'').

The y-map is y*dX/dx. In each of four cases, both forward and reverse h divide the seventh division polynomial of their respective sources; the reverse codomain coefficients equal (7⁴a,7⁶b). Homogenized rational polynomial composition gives degree-(49,48) numerator/denominator, and the *universal* cross-product with

    49*x([7]P) = 49*(x - psi6*psi8/psi7²)

is the **zero polynomial in F101[x]** coefficientwise in every case. This is stronger than testing maps on rational points alone. [pcc:unverified]

All 109 and 113 source points pass the full two-hop normalized reverse check against scaled [49]. Across the four reverse maps, all 11,881+11,881+12,769+12,769 = **49,300 ordered group-law pairs** agree, including inverses, doubles and identity. Both resulting target point sets are complete bijections. Deliberately changing the constant coefficient of each reverse cubic is rejected by (i) its division-polynomial remainder and (ii) its universal composite identity. An intentionally wrong reverse direction fails on all nonidentity source points (108 and 112). The local normal and optimized Python runs agree byte-for-byte. [pcc:unverified]

## Reproduction

Run from repository root:

    python3 -B experiments/chained-transfer-reference/ct36/ct36_dual49_oracle.py > /tmp/ct36.normal
    python3 -O -B experiments/chained-transfer-reference/ct36/ct36_dual49_oracle.py > /tmp/ct36.optimized
    diff -u /tmp/ct36.normal /tmp/ct36.optimized
    python3 -m py_compile experiments/chained-transfer-reference/ct36/ct36_dual49_oracle.py

Local source SHA-256: ed50d5d83cbb1de4519fa58735acb8805b6d1509ce94f769535d9387c499e061. Local raw output SHA-256: 2adb2e151fcf8769b0895edb5a8bd8211bb12b9ef577f3288369a150d178c238. These are provenance references to an unsigned developer run; GitHub exact-head CI and signed PCC must be checked separately. [pcc:unverified]

## Prior art and open obligations

Primary mathematics: Silverman, *The Arithmetic of Elliptic Curves* III.6 (dual isogenies), and Bostan, Morain, Salvy, Schost, *Fast algorithms for computing isogenies between elliptic curves*, *Mathematics of Computation* 77 (2008), 1755–1778, https://arxiv.org/abs/cs/0609020. See also Lercier and Sirvent, *On Elkies subgroups of l-torsion points in elliptic curves defined over a finite field* (2009), https://doi.org/10.5802/jtnb.650. The shared research-KB, encrypted autoresearcher atlas and cost-admission controls are not accessible in this runtime; no exhaustive novelty or independent signed proof claim.

**Next discrimination:** compare the four projected elliptic maps and reverse duals with actual native Phi2/Psi2 and Richelot kernels, then reuse concurrent #1501's full 12,317-class Cantor checker to validate *the genuine genus-2 maps* and their duals. Do not conflate elliptic [49] duality with a (7,7) Jacobian isogeny. Matched cold rho/index-calculus solving-cost measurements require approved EKS/S3/budget gates and a frozen protocol. No paid compute or speedup claim. All results remain **[pcc:unverified]**.
