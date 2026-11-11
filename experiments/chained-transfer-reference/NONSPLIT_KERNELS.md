# Frobenius-stable Richelot kernels: fixed-field assessment

`src/nonsplit.rs` constructs kernel splittings and codomain models on the
predeclared E19/F17 fixture, and independently audits the E109/F101 control.
It does **not** yet implement a divisor correspondence. Claims42713c and
final guarded-replay record3c51f5 remain unsigned/unverified. No benchmark or
computational advantage is asserted. [pcc:unverified]

## Primary construction and bounded arithmetic

Kunzweiler, DCC92(2024), §§3.1–3.2, Lemma6 and Propositions7–8 identify the
15 maximal isotropic2-kernels with partitions of six branch points into
three pairs. A kernel is base-field-defined precisely when its unordered
pairing is Frobenius-stable. The quadratic factors need not individually
have base-field coefficients. The determinant and normalized brackets are

    δ = det(coefficients of G1,G2,G3 in ascending powers),
    Hi = (G'j Gk − Gj G'k)/δ,
    C': w²=H1 H2 H3.

Zero determinant is retained as the product-of-elliptic-curves case, not a
genus2 codomain. The published normalization/sign convention is used without
retwisting. The primary PDF digest and earlier source review are in crypto's
SOURCES_20261111.md. KB lookup remains unavailable, retained separately.

The new assessment reuses BigUint polynomial arithmetic in
`F17[T]/(T³+2T+2)`. The modulus has no F17 root and hence is irreducible.
Choose β²=T by the first coefficient encoding c0+17c1+17²c2; its conjugates
β,β17,β289 and their negatives are all six branch roots. Frobenius permutes
them as(012)(345). The complete recursive pairing enumeration produces15
distinct matchings and3 stable ones. [pcc:unverified]

## E19/F17 outcomes and equivalence control

The source is `C: y²=x^6+2x²+2`, from the existing elliptic curve
`E:y²=x³+2x+2`, order19, generator(5,1). Its balanced rational Jacobian has
285 classes. With root labels above, the outcomes are:

| Pairing | δ | Raw codomain coefficients in ascending powers |
|---|---|---|
|(0,3),(1,4),(2,5)|0|Degenerate; product case retained|
|(0,4),(1,5),(2,3)|11|[10,6,14,2,12,10,9]|
|(0,5),(1,3),(2,4)|6|[10,11,14,15,12,7,9]|

Both nondegenerate targets are smooth, their normalized coefficients descend
to F17, and leading coefficient9 has square root3. Dividing the raw
equation by9 gives monic coefficient arrays
`[3,12,11,4,7,3,1]` and `[3,5,11,13,7,14,1]`, each with285 balanced rational
classes. These are rational counts, not kernel degrees. [pcc:unverified]

The two targets are the **same F17 curve up to z↦−z,w↦w**. They are not two
new destinations. A complete PGL2(F17) audit checks4,896 normalized matrices
per comparison and requires a square ordinate scaling. It finds0 source→target
maps in both cases,1 map between targets,2 source self-maps on the quotient
line, and1 self-map for either target. This distinguishes curves over F17;
no unpolarized-Jacobian nonisomorphism is inferred. Lack of an additional
base-field involution only obstructs degree2 elliptic quotients; it does not
exclude higher-degree elliptic maps. [pcc:unverified]

The audit includes every invertible2×2 matrix modulo scalar by normalizing
the first nonzero entry to1. For each it compares binary sextics
`Σ f_i(aX+b)^i(cX+d)^(6−i)` up to a nonzero square. The explicit reflection
identity independently explains the target-target equivalence. The reported
coefficient arrays,285 count and full audit counts are regression assertions.
[pcc:unverified]

## E109/F101 negative, at its exact scope

For `E:y²=x³+x+46`, the cubic is irreducible over F101. If α is a root,
`Norm(α)=−46=55` is nonsquare. In its odd-degree cubic field, α is therefore
nonsquare: Euler's criterion follows from
`(p³−1)/2=((p−1)/2)(p²+p+1)`. A square root β of α has degree6, with
Frobenius³β=−β. Consequently the quadratic sextic has a single6-cycle of
branch roots. [pcc:unverified]

Among all15 matchings, a6-cycle preserves only opposite-root pairs. These
give `Gi=X²−αi`, so the entire linear-coefficient column vanishes and δ=0.
Thus this **specific** E109 quadratic cover has no nondegenerate
F101-rational Richelot kernel leading directly to a genus2 codomain. It can
still have the product quotient. This does not exclude shifted/other covers,
other isogeny degrees, paths through products, extension-field constructions,
or computational transfers in general. [pcc:unverified]

Upstream `FrobeniusPairings.lean` proves five bounded certificate/accounting
lemmas:15 distinct valid listed matchings, their stable filters for the two
cycle types, zero determinant column and odd-norm exponent identity. The
5-declaration gate passes, crypto PCC465142 unsigned. The finite table is
explicit; its identification with all geometric kernels and finite-field
norm theory remain written primary-source inputs. [pcc:unverified]

## Next operational-map obligation

Freeze the **first nondegenerate pairing in the complete ordering**, δ11,
before map evaluation. Its target normalization is w=3Y. Implement the
actual correspondence

    G1(x)H1(z)+G2(x)H2(z)=0,
    yw=G1(x)H1(z)(x−z).

For arbitrary rational balanced source classes, finite support has degree≤2.
Its F17² roots and F17³ factor coefficients fit in the compositum F17⁶.
Keep the target fiber as a quadratic Mumford pair; no target root choice or
F17¹² point splitting is required. Infinity contributions must be tracked
relative to K, and every reduced result must descend coefficientwise to F17.
Use w=3Y on target input/output, and the sign-corrected reversed correspondence
for the dual. Check both dual norms[2] on all285 rational classes, additivity,
all19 source scalars and composed source recovery[4]/inverse5 modulo19.
These are planned acceptance criteria, not completed map results.
[pcc:unverified]

Production/catalog integration, independent signed standing, prime-field
descent and total solver cost remain open. The canonical graphs are unchanged:
this is unsigned kernel/codomain evidence without an implemented non-split
map or performance edge. Keep the existing S3/live-budget/KB/vault blockers.

Reproduce with `experiments/chained-transfer-reference/check.sh`, using
installed Rust1.99.1 and the unchanged crypto75a737b8 runtime pin. Final
receipt `evidence/nonsplit-pinned-02.txt` passes guards, formatting, strict
Clippy, native25/reference40 tests and1 existing ignored benchmark. The
initial development output and earlier complete pass remain retained;
no frozen evidence was replaced. [pcc:unverified]
