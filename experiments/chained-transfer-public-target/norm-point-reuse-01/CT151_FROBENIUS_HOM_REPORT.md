# CT151 — Exact Frobenius zero-Hom certificate for the two reported q223 cubic-source models

15 November 2026, America/Denver. **[pcc:unverified]**. Conditional mathematical obstruction only; not an original-prime ECDLP solver, host timing, actual source point count, Lean-kernel proof or signed PCC record.

## The stronger result

Let k=F_223, K=F_(223^3), and E'/K have **reported** order N=11,092,292 (original) or N=11,086,844 (fixed nu12). Their *conditional* cubic Frobenius traces are T=-2724 or T=+2724. Put A=Res_(K/k)(E'), a k-abelian threefold. Frobenius on A has characteristic polynomial `Q_T(X)=X^6-TX^3+223^3`.

For **every** elliptic curve E/k, Frobenius has polynomial `P_t(X)=X^2-tX+223` for one of the 59 Hasse-bounded integer traces t=-29,...,29. Set `d=t^3-669t-T`. The exact integral Bézout identity is

`(t-X)^3 Q_T(X) - R_(t,T)(X) P_t(X) = d*223^3`

with integral degree-seven quotient R. Indeed `Q_T(X)=d X^3 (mod P_t)` and `X(t-X)=223 (mod P_t)`. Its resultant counterpart is `Res(P_t,Q_T)=223^3*d^2`. Every d is nonzero for both reported models; the minimum absolute value is 112, attained at t=4 for original and t=-4 for nu12.

**Conditional theorem:** `Hom_k(E,A)=0` for any E/F_223. A k-defined hom f:E->A commutes with Frobenius. Evaluate the identity on f: both polynomial terms vanish, giving `d*223^3 f=0`. The abelian-variety Hom group is torsion-free, so f=0. Equivalently Weil-restriction adjunction reduces the claim to absence of an isogeny E_K->E', which follows from unequal cubic point counts. This strengthens CT150's no-base-change observation to **all k-defined homomorphisms into either of these fixed Weil restrictions**, conditional on their recorded field and source orders.

This is not a universal obstruction to E/Fp -> another Jacobian factor, cover, alternate elliptic curve, larger prime p or a nonhomomorphic encoding. It does not invalidate the separate q223 extension-field norm-reuse computation.

## Execution and falsification

The [CT151 protocol](CT151_FROBENIUS_HOM_PROTOCOL.md) was committed first at `8754139c`, followed by [standalone integer source](ct151_frobenius_hom_certificate.py) at `2d668f99` and [source-only CI](../../../../.github/workflows/ct151-frobenius-hom-certificate.yml). Developer-local normal/`python3 -O` output matched byte-for-byte, JSON SHA-256 `1bd745c9d53eeae0cd33cf92f06459ae779160f5adfd521d90384bafec6622ab`. The executed source's git blob SHA1 `0c430dd3dd32fbfb57f9d8caf5bd1b3ccf415d61` matched an independent GitHub readback. 118 integer quotient witnesses (59 per model) passed exact polynomial division **and** a separate quadratic-basis calculation. Roster hashes: original `8c2bd08831a79fa4ebeb388d1393d76007aa8f66edd96748ceaa3c9d85a72ed6`, nu12 `1360905d0acfa2db3ef1d20c6cdfa2ca11a24aac64486ba566b51c8856bdcf21`.

A separately written local SymPy resultant calculation reproduced `Res(P_t,Q_T)=223^3 d^2` for all 118 pairs, with minimum nonzero absolute resultant `139107528448`. Deliberate controls rejected mutated quotient, mutated d, composite p and changed recorded source order. A positive boundary with t=4,T=-2612 gives d=0 and resultant=0, so the script correctly **does not** issue a zero-Hom certificate for a trace-compatible source.

Reproduce:
```sh
python3 experiments/chained-transfer-public-target/norm-point-reuse-01/ct151_frobenius_hom_certificate.py > /tmp/ct151-normal.json
python3 -O experiments/chained-transfer-public-target/norm-point-reuse-01/ct151_frobenius_hom_certificate.py > /tmp/ct151-opt.json
cmp /tmp/ct151-normal.json /tmp/ct151-opt.json
```


## Conditional quotient-Jacobian corollary

If the root chain's **proposed degree-eight polarized quotient** is in fact a **k-defined isogeny** `A -> J` to the complete destination Jacobian `J/k`, then the zero-Hom obstruction extends to **the whole J**, not merely to one named elliptic factor: `Hom_k(E,J)=0` for every elliptic `E/k`. A k-isogeny becomes invertible in `Hom^0=Hom tensor Q`; hence `Hom^0(E,J) = Hom^0(E,A)=0`, and torsion-freeness yields the integral Hom result. Equivalently compose any purported nonzero E->J map with a k-defined quasi-inverse isogeny J->A to get a forbidden nonzero E->A map.

This corollary **requires independent certification of the actual k-defined A~J isogeny and both reported E'/K group counts**. If the purported quotient is only a K-map, lacks the claimed source, or the target is a genuinely different Jacobian isogeny class, this corollary does **not** apply. Nonhomomorphic algorithms with fully proved inverse semantics are also outside its scope. None of those missing hypotheses was certified by CT151. [pcc:unverified]

## Still necessary for the owner's complete-solve goal

The q223 source is over K, not the prime field; neither current conditional factor can be used as a direct prime-field elliptic *homomorphic* target via Res without contradicting the Frobenius certificate. Verify real q223 point counts and K/k identification independently; do not infer correctness from reported integer counts. Independently replay 695/701 original/reuse Jacobian outputs, and run the existing separately admitted C169/C13a/C13b/D cold benchmark with setup, transfer, LA, verification, peak RSS, uncertainty, full rho/BSGS/IC references and signed PCC. In parallel, choose an **actual E/Fp source** (p31/NIST route), prove a nonzero subgroup-injective explicit transfer to a valid destination and measure complete cold single-target cost. A genuine prime-field bridge is not yet exhibited here.

The Lean version of the Frobenius/Hom lemma and `#print axioms` audit are uncompleted. No chargeable compute, protected merge or PCC ledger modification occurred. No novelty/absence claim; shared research-KB/lead-atlas was unavailable. [pcc:unverified]
