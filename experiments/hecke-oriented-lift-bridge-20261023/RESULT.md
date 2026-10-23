# Frobenius eigenlines prevent sheet switching in the split level-11 Hecke walk

**Result.** For an elliptic curve over a finite field, when Frobenius has two distinct eigenvalues on its 11-torsion, every rational isogeny of degree prime to 11 carries each eigenline to the eigenline with the *same* eigenvalue. Consequently a degree-3 Hecke edge on the ordinary, noncuspidal part of \(X_0(11)\) preserves the two eigenline labels. Over the audited \(D=-1295\), \(p=11719\) conductor-2 class, this gives a structural reason for the four observed 18-cycles, paired over two 18-element sets of \(j\)-invariants, rather than the competing two 36-cycles. The new replay certifies the two eigenvalue pairs — \(1,4\) for trace \(16\), and \(7,10\) for trace \(-16\) — and checks the sealed cycle data.

## Theorem and proof

Let (E,E'/\mathbf F_q) be elliptic curves, let \(\ell\ne\operatorname{char}\mathbf F_q\) be prime, and suppose the characteristic polynomial of Frobenius on \(E[\ell]\) has two distinct roots \(\lambda,\mu\in\mathbf F_\ell\). Let \(\phi:E\to E'\) be an \(\mathbf F_q\)-isogeny of degree coprime to \(\ell\). Then \(\phi\) induces an isomorphism \(E[\ell]\to E'[\ell]\), and

\[
 \phi(\ker(\pi_E-\lambda))=\ker(\pi_{E'}-\lambda),\qquad
 \phi(\ker(\pi_E-\mu))=\ker(\pi_{E'}-\mu).
\]

Indeed, a rational isogeny commutes with Frobenius. Its restriction to \(\ell\)-torsion is injective because its kernel has order coprime to \(\ell\), and hence bijective because both torsion groups have \(\ell^2\) geometric points. For any \(P\in E[\ell]\), the equality \(\phi(\pi_E P-\lambda P)=\pi_{E'}\phi(P)-\lambda\phi(P)\) proves both inclusions, using injectivity for the reverse implication. Distinct Frobenius eigenvalues give precisely two Frobenius-invariant lines: the two eigenspaces. These are exactly the rational cyclic order-\(\ell\) subgroups in the ordinary, noncuspidal moduli interpretation of \(X_0(\ell)\). A degree-\(d\) Hecke edge for \(d\nmid\ell\) sends \((E,C)\) to \((E/H,\phi(C))\), so the two lines retain their eigenvalue labels. The moduli rule is stated in [Snowden's Hecke-correspondence lecture](https://websites.umich.edu/~asnowden/teaching/2013/679/L16.html); the horizontal ideal-class cycles on ordinary curves are described by [Sutherland, *Isogeny volcanoes*, §§2.8–2.9](https://msp.org/obs/2013/1-1/obs-v1-n1-p25-s.pdf).

For a horizontal base \(j\)-cycle of length \(m\), assume its Hecke edges are rational isogenies of degree coprime to \(\ell\), all vertices have the same trace, and each vertex has exactly the two nonexceptional level-\(\ell\) lifts above it. A lifted walk visits successive base vertices while keeping its eigenvalue label. After \(m\) steps it returns to the same base vertex and the same one of its two lifts, so each base cycle lifts to two cycles of length \(m\). The finite-field degree-3 Hecke point computation and the exact two-point fiber gate for this field were independently checked in the [sealed predecessor experiment](/Volumes/SSD990/cryptanalysis/experiments/hecke-two-sheet-small-order-20261023/RESULT.md).

## Exact arithmetic and replay

Here \(q=p=11719\), \(|t|=16\), \(\ell=11\), and \(d=3\). The characteristic-polynomial discriminant is \(t^2-4p\equiv9\pmod{11}\), a nonzero square. For \(t=16\), \(X^2-tX+p=(X-1)(X-4)\pmod{11}\); for \(t=-16\), its roots are \(7,10\). Thus the eigenlines are distinct in either quadratic twist. The inherited audit reconstructs 72 conductor-2 level-11 points over 36 \(j\)-values and four degree-3 cycles of length 18. Each cycle contains 18 distinct \(j\)-values, with identical \(j\)-sets for cycle pairs \((0,3)\) and \((1,2)\). The degree-3 nonfloor row kernel has dimension 8. [replay.py](/Volumes/SSD990/cryptanalysis/experiments/hecke-oriented-lift-bridge-20261023/replay.py) verifies these facts against the predecessor's frozen selection, audit and validation files; [replay.json](/Volumes/SSD990/cryptanalysis/experiments/hecke-oriented-lift-bridge-20261023/replay.json) contains their SHA-256 handles and the eigenvalue certificate. The predecessor performed the checked-Sage production and independent Sage audit; this new arithmetic replay uses standard Python and does not start a new Sage job.

## Proof map and boundary

| Claim | Lean declaration | Status |
| --- | --- | --- |
| An equivariant injective map preserving zero transports the annihilator of any subset of acting endomorphisms in both directions | `IdealOrientation.transport_iff` | Built; `#print axioms` reports none |
| The same map preserves both distinct ideal/eigenline predicates simultaneously | `IdealOrientation.two_ideal_labels_preserved` | Built; `#print axioms` reports none |
| Frobenius characteristic polynomial has two distinct roots, rational level-11 points are the two eigenlines, degree-3 Hecke edges induce rational isogenies, and each lifted cycle has base length | No elliptic-curve/modular-curve Lean declaration | Written proof and exact-field replay; formalization partial |

The Lean core quantifies over every acting set and every equivariant injective map; instantiate its action with \(\pi-\lambda\) and \(\pi-\mu\). The remaining Lean bridge needs finite-field elliptic curves, their torsion and Frobenius, isogeny kernel-degree facts, and the \(X_0(11)\) moduli interpretation connected to the concrete Hecke routine. [IdealOrientation.lean](/Volumes/SSD990/cryptanalysis/experiments/hecke-oriented-lift-bridge-20261023/formal/IdealOrientation.lean) and [build.json](/Volumes/SSD990/cryptanalysis/experiments/hecke-oriented-lift-bridge-20261023/formal/build.json) retain the pinned mathlib revision, build command, source and output hashes, and the axiom audit. `lean4checker --fresh` is unavailable on this host. The candidate remains `candidate_id: null`, with `timing_claim: null`: this is a theorem-and-relation-structure result, not an end-to-end IC timing measurement.
