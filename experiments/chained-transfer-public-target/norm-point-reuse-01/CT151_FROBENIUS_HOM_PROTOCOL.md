# CT151 — prospective prime-field-to-cubic-source Hom obstruction certificate

Date: 2026-11-15 America/Denver. Standing **[pcc:unverified]**. Root isogeny-labs/crypto#3877; continuation of CT150 in cryptanalysis#1589. This protocol is committed **before** CT151 executable/witness code. It freezes the hypotheses, integer inputs, acceptance controls, and scope, not a performance claim.

## Frozen conditional input and question

Take k=F_223 and K=F_(223^3). CT150 reports two *unverified source orders* for elliptic curves E'/K: N_0=11,092,292 and N_nu=11,086,844, yielding the *conditional* K-Frobenius traces T_0=-2724 and T_nu=+2724. These counts are not independently established in this protocol. CT150 enumerates all possible prime-field elliptic traces t with |t|<=29 and observes t^3-3*223*t != T_i.

The new question is strictly stronger than whether E' is a base change: can *any* elliptic curve E/k admit a nonzero **k-defined homomorphism of abelian varieties** E -> Res_(K/k)(E')? An affirmative k-defined hom is a necessary algebraic precursor for a homomorphic prime-field ECDLP transfer that actually lands in this fixed cubic elliptic factor. The question says nothing about alternate Jacobian factors, non-homomorphic encodings with separate proofs, or base-prime p31/NIST transfer.

## Required exact integer-polynomial witness

For each t in {-29,...,29} and each model trace T, define

- P_t(X)=X^2-t X+223;
- Q_T(X)=X^6-T X^3+223^3, the *predicted* Frobenius polynomial of Res_(K/k)(E'), conditional on field and group-order inputs;
- delta=t^3-3*223*t-T;
- V_t(X)=(t-X)^3.

Use exact ZZ[X] polynomial long division to construct R_(t,T)(X) by

`V_t(X) Q_T(X) - delta*223^3 = R_(t,T)(X) P_t(X)`.

**Fail** if remainder is nonzero, division is not integral, delta is zero when claiming an obstruction, or any displayed identity is not reverified from independently constructed polynomials. The displayed identity is a Bézout certificate with nonzero constant delta*223^3 if and only if delta !=0. Check all 59 traces for both T, record minimum absolute delta and associated t and the full witness-degree/identity summary. Verify the identity a second way in ZZ[X]/(P_t) with pair-basis multiplication using X^2=tX-223, independent of long division.

Mathematical inference to record, *conditionally* and with explicit assumptions: if A=Res_(K/k)(E') is an abelian threefold with k-Frobenius annihilator Q_T and E/k has P_t, then any k-hom f:E->A commutes with Frobenius. Applying the polynomial identity to f yields (delta*223^3) f=0. Since Hom_k(E,A) is torsion-free and delta !=0, f=0. This excludes a **direct** k-hom into these particular A, not a general isogeny/Jacobian attack or arbitrary computations in another field. The alternate proof via adjunction and non-isogeny of E_K,E' can be documented but not substituted for the explicit machine-checkable certificate.

## Falsification, cost and execution

- Positive boundary control T=t0^3-3*223*t0 for t0=4: delta=0. It MUST be rejected as an obstruction; record that this is a trace-polynomial control and does not construct a curve.
- Negative controls: corrupt one R coefficient, corrupt delta, feed nonprime p or a claimed source count not matching frozen N; fail closed.
- Independent second arithmetic route must reproduce all trace differences and polynomial identity results.
- Execute under ordinary Python and `python3 -O` and require byte-identical deterministic JSON. Source-only scoped CI may run unadmitted; do not run EKS, GPU, chargeable compute or the manually admitted native C169/C13/D job.
- No new prime-field DLP, 695/701 original/reuse replay, complete cold rho/BSGS/IC timing or PCC signature is asserted. **This obstruction should prevent an unsupported inference** that benchmarking q223 cubic-source transfers has measured an arbitrary prime-field ECDLP speedup; it does not prohibit continuing the independently valuable q223 native reuse-pricing experiment.
- Preserve original Rust, fixture, PCC ledger, session logs and existing open-PR merge gates. Any mathematical claim must retain **[pcc:unverified]** until an independent signed record is available.

## Sources checked

CT150 source/protocol/report at cryptanalysis#1589; reported frozen original/nu12 orders from CT149; crypto#3877 current status, root public-n4 map-degree report and related PRs. GitHub AGENTS consulted. Research-KB MCP / checkout-local lead atlas unavailable in this execution environment; no novelty or prior-art absence claim.
