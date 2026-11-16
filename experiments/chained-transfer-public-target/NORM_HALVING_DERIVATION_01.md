# Complete norm-halving evaluation of the degree-13 Jacobian transfer

The protocol was published as d5db7698 before this sibling implementation. Native05 passes four unfiltered tests and retains every earlier whole native record without masks (PCC-20261114-7ff793). Both unchanged Lean gates accept the ten declarations; nine additional exact bindings bring the partial binding count to82 (PCC-20261114-3ba28f). These are unsigned observations. [pcc:unverified]

## Fixed objects and domains

Use the field, curves, origins and model identifiers in [NORM_HALVING_PROTOCOL_01.md](NORM_HALVING_PROTOCOL_01.md). Here K=F223[z]/(z³−3), L=F223[w]/(w⁶−3), and z maps to w². Write J0 and J1 for the actual matched prime-field Jacobians, Phi_i for their base-changed elliptic quotient maps, N_i for their admitted rational norm maps, gamma:E→E13 for the original degree13 isogeny and Psi=Phi_1 gamma. The existing complete-C map beta satisfies beta Phi_0=Psi. The relevant identities on these admitted domains are Phi_i N_i=[2] and N_i Phi_i=[2]. None of these geometric bridges is formalized merely by giving abstract functions to Lean. [pcc:unverified]

Each public input undergoes the same canonical packet checks, complete norm/geometry validation and actual full Jacobian-order admission in both implementations. The norm already computed during validation is retained. Thus the common admission still includes a large Jacobian scalar; its work is included and unpriced. The immutable decoders had already computed and discarded that norm. [pcc:unverified]

## Strong scalar baseline

Let ell=2773073, #J=4ell and k=1386537, so 2k=ell+1. For an admitted x, x2=[ell]x is its two-primary component because ell=1 modulo4. By the explicit norm square and linearity,

```
Psi([k]N0(x)) - beta(x2)
  = [2k]beta(x) - [ell]beta(x)
  = beta(x).
```

This strengthens the earlier baseline by moving inverse-two multiplication to E(K); it still includes the Jacobian CRT projection, original complete cofactor table and complete-C constructor. The conditional Lean theorem `strongest_scalar_baseline_identity` proves exactly this algebra, with its commuting and linearity assumptions explicit. [pcc:unverified]

## A full elliptic lift is a required bridge

Geometric surjectivity of a Weil-restriction quotient does not alone provide a single point a0 in E(L) with Phi_0(a0)=x. The needed bridge instead uses the existing odd/cofactor decomposition x=xo+x2. The odd lift is ao=[k]N0(xo): Phi_0(ao)=[2k]xo=xo because [ell]xo=0. Use an actual retained cofactor lift a2 in E(L) with Phi_0(a2)=x2. Then a0=ao+a2 has Phi_0(a0)=x, and the norm identity gives [2]a0=N0(x). The finite cofactor lifts remain actual native/written inputs. `preimage_from_odd_and_cofactor` derives this conclusion from those inputs; it does not assume the desired full lift. [pcc:unverified]

All E[2] is K-rational for these fixed curves. For any geometric half a of Q=N0(x), sigma(a)−a lies in E[2], where sigma is K-Frobenius. Since sigma fixes that difference, sigma²(a)=a. Thus all four halves lie in E(L). On the actual F223⁶ representation, sigma is coordinate F³, not coordinate F. The abstract proof is `halves_fixed_by_frobenius_square`; the finite source-field bridge is checked natively. [pcc:unverified]

## Coordinates and correction

For Q=(u,v), v≠0, the existing halving selector uses

```
H(X)=X⁴−4uX³−2AX²−4(Au+2B)X+A²−4Bu,
T(X)=X³−3uX²−AX−Au−2B,  Y=T(X)/(2v).
T(X)²−4(u³+Au+B)(X³+AX+B)=H(X)(X−u)².
```

The ordinate identity is universally proved over a commutative ring. Exact integer expansion and the unchanged original certificate issuer/checker also accept both identities. Omitting −2B produces five nonzero coefficient differences and an actual original-checker counterexample (PCC-20261114-d91395). The identity alone requires neither division nor a claim that every arbitrary quartic root is a valid half. Runtime checks retain the curve equation and [2]a=Q. Q=O uses the complete E[2] dictionary; nonzero two-torsion Q uses the literal original selector and both ordinates at each abscissa. [pcc:unverified]

Choose any half a. Since a0 and a have the same double, t=a0−a is in E[2](K), and Phi_0(t)=x−Phi_0(a). The runtime dictionary stores the actual image of all four source two-torsion points; it has two image keys with two points per fibre. Look up the actual correction and return

```
Psi(a)+Psi(t)=Psi(a+t)=beta(Phi_0(a+t))=beta(x).
```

The explicit quotient square proves equality with beta and independence from the half or correction representative. These implications are formalized under explicit map hypotheses; the actual quotient, finite dictionary and Picard arithmetic remain native/written bridges. The direct implementation constructs its own norms, quadratic models and dictionaries, and does not call complete-C or the four-class CRT table in its transfer core. [pcc:unverified]

## Actual validation and remaining costs

Native05 checks448 exceptional inputs,48 mixed cases,40 public sector/direction rows and96 addition pairs against both the strengthened baseline and immutable complete-C. Every four actual halves is corrected and checked; corrected Phi/Psi values, source isogeny/dual[13], both new-map[13] compositions, full inverse and original public source recovery agree. All48 coordinate targets match the literal selector, including infinity, nonzero two-torsion and generic cases; changed constant, zero denominator, non-K halves, F³ and incorrect coordinate-F controls are retained. Both deliberately shifted origin subtractions fail the original odd-membership check. This last control is private test corruption, not an assertion that production admits a corrupt context. [pcc:unverified]

The direct transfer core replaces its CRT/half-odd scalars with quartic factorization, complete quadratic Phi/Psi, an elliptic isogeny and finite two-torsion correction. Generic selected counts include four ordinate recoveries and eight explicit doubling checks; literal-selector internal checks are unpriced. Constructor counts include two elliptic two-torsion factorizations, eight prime-field Phi calls, eight source-isogeny calls and two quadratic origin traces. All model/context/field/Picard/validation/verification work remains included and unpriced. Full inverse additionally uses the Jacobian scalar3413013. The fixed-L pole admission uses #E(L)=N(2q³+2−N) from the existing #E(K) input and13∤#E(L); it is not a new formal point-count certificate or general pole handler. [pcc:unverified]

No calibrated primitive cost, end-to-end improvement, computational advantage over ECDLP algorithms, novel halving formula or full geometric formalization follows. Source-linked [results and PDF](reports/norm-halving-results-01/REPORT.md), [proof map](NORM_HALVING_PROOF_MAP_01.md), whole raw indices and failures preserve the scope. Complete primitive coverage/admitted matched references and a genuinely nondual degree13 continuation remain queue items. [pcc:unverified]
