# Bounded balanced genus2 arithmetic

The prototype in `src/balanced.rs` supplies the two-infinity representation
missing from the production odd-degree backend. It supports canonical monic
smooth sextics over checked primes5..101. The production backend and the
1,940-row cover catalog are unchanged. All results remain unsigned/unverified;
PCC-20261111-8b7ca0 binds the complete guarded replay. [pcc:unverified]

## Primary construction and exact representation

Galbraith, *Mathematics of Public Key Cryptography*, corrected ch.10§10.4.2,
Definition10.4.9 and Theorem10.4.19 give the canonical balanced representation.
For `C:y²=f(x)`, monic squarefree sextic, set `K=∞++∞−`. Store

    D_fin + n∞+ + (2−m−n)∞− − K,
    m=deg(u)≤2, 0≤n≤2−m, u monic, deg(v)<m, u divides f−v².

Finite Mumford support is semireduced; the identity is `(1,0,1)`, not
`(1,0,0)`. The infinity difference δ is `(1,0,2)` and its inverse `(1,0,0)`.
Negation replaces v by−v mod u and n by2−m−n. Model/field tags and canonical
coefficient checks reject mixed or malformed inputs. The polynomial and
prime-field arithmetic is reused unchanged. [pcc:unverified]

Affine Cantor composition gives `u=u₁u₂/d²` and the standard Bezout v,
without odd-degree reduction. Lemma10.4.10 updates the signed infinity count
to `n=n₁+n₂+deg(d)−1`. Equivalently the degree4 effective sum has nonnegative
infinity counts `N+=n₁+n₂+deg(d)` and
`N−=(2−m₁−n₁)+(2−m₂−n₂)+deg(d)`, with `m+N++N−=4`.
If the resulting pair/count is already canonical, it is returned.
[pcc:unverified]

Otherwise use a cubic ℓ≡v mod u. For m=4, ℓ=v; for m≤3, take
`ℓ=G_s+(v−G_s mod u)` matching the branch carrying the remaining infinity
support. The polynomial part of y at∞+ is

    G+=x³+c₂x²+c₁x+c₀,
    c₂=f₅/2, c₁=(f₄−c₂²)/2, c₀=(f₃−2c₂c₁)/2; G−=−G+.

Set `u'=monic((f−ℓ²)/u)`, `v'=−ℓ mod u'`, r=deg(u'). The exact valuation
update is `n'=n−ord∞+(y−ℓ)−r`. If ℓ's cubic coefficient is+1, this valuation
is `3−deg(f−ℓ²)`; otherwise it is−3. This explicitly includes degree4
interpolation with leading±1, where blindly assuming two poles of order3
would be incorrect. For the infinity branch steps the updates become
`n+m−3` and `n+3−r`, as in Lemma10.4.14. The degree4 effective-input bounds
ensure the result is canonical after this single reduction. Exact division,
degree and infinity bounds are checked, rather than assumed. [pcc:unverified]

The six upstream Lean lemmas in `BalancedDivisors.lean` prove the degree/count
accounting, inverse-count range/involution, branch updates and square of G+.
They do not construct valuations, finite fields or Picard groups. The primary
canonical-representative theorem and geometric divisor identities remain
written inputs. Claim crypto PCC-20261111-1cadd0 is unsigned. [pcc:unverified]

## Exhaustive model controls and induced quadratic maps

Complete bounded enumeration includes rational point pairs and tangencies,
irreducible quadratic Frobenius orbits, both infinity choices and δ. For
`y²=x^6+1/F101`, all10,404 representatives biject with the pre-existing chart
at W=(10,0), using t=1/(x−10),Y=yt³. Paired additions, every inverse and
inverse cancellation, every δ-translation and every first quotient norm
agree. All six finite-degree/infinity-count patterns occur. δ has order3.
Both engines use Cantor; their agreement is not independent signed standing.
[pcc:unverified]

The translated model `y²=(x+1)^6+1` has nonzero infinity polynomial
`x³+3x²+3x+1`. All10,404 classes, paired additions and inverses also match
the old engine after the explicit coordinate shift. On the primary example
`y²=x^6+x+1/F37`, the code reproduces Example10.4.18 and checks1,211 fixed
associativity triples. Infinity, singular, nonmonic, composite, malformed and
foreign-model controls are retained. These are finite correctness tests,
not a universal machine proof. [pcc:unverified]

For the pre-existing source `E/F101:y²=x³+x+46`, #E109,G=(2,37), the quadratic
cover `C:y²=x^6+x²+46` has no rational Weierstrass point. Whole pullback sends
finite `(U,V)` to `(u=x²−U,v=V,n=0)` and O to the balanced identity. The first
norm projects arbitrary canonical support by `(x,y)↦(x²,y)` using the same
closed-point trace helper as the cubic prototype. Both infinities map to O,
so K and δ have norm zero. No scalar labels enter either map. All109 source
scalars preserve their relations; norm-after-pullback is[2], invertible by55
modulo109. [pcc:unverified]

The source Jacobian has11,663 enumerated classes. Independent elliptic point
counts give109 and107 for `y²=x³+x+46` and `y²=x³+x²+96`, the normalized
reciprocal quotient `(X,Y)=(46/x²,46y/x³)`. The product agrees with the
balanced count. All11,663 paired arbitrary-class norm additions pass; the
norm has109 images, each with107 preimages. This is a rational-class count,
not a geometric kernel cardinality or solver measurement. [pcc:unverified]

## Reproduce, retained failures and remaining work

With installed Rust on PATH and the unchanged crypto75a737b8 runtime sources,
run `experiments/chained-transfer-reference/check.sh`. Receipt
`evidence/balanced-pinned-01.txt` passes guards, formatting, strict Clippy,
native25 and reference37 tests; one pre-existing benchmark remains ignored.
The first compile used an integer where the native oracle requires Fp2;
the first Clippy run requested div_ceil. Both failures remain retained beside
the passing development receipts. The norm helper was factored for powers2/3;
all earlier cubic controls pass again. No frozen witness or receipt changed.
[pcc:unverified]

This narrows the catalog's representation gap only in a bounded development
prototype. Extension fields, large primes, nonmonic/inert infinity models,
catalog replay, normalized Montgomery/Edwards targets and production API
integration remain unsupported. It does not close the catalog-wide problem.

Next assess the predeclared E19/F17 sextic's Frobenius-stable unordered
Richelot splittings, including determinant, actual base-field codomain and
map descent. The lack of individually rational quadratic factors is not a
universal obstruction. No actual non-split correspondence is implemented by
this checkpoint. Same-field covers and a larger ambient Jacobian establish
neither prime-field descent nor a computational advantage. No benchmark ran;
S3/live-budget/KB/vault gates remain unchanged. [pcc:unverified]

Canonical transfer/leaderboard graphs remain current because no signed
scientific result or measured performance edge is promoted. This report's
diagram records only the bounded development implementation and its limits.
