# CT147 rational-map transport canary — bounded protocol

Date 2026-11-15. Root crypto #3877; extend cryptanalysis #1589 without modifying the original q223 evaluator, frozen 695/701 record population or CT146 source.

Standing **[pcc:unverified]**. This protocol was committed before adding the repository CT147 implementation. An exploratory local prototype was already exercised; therefore this is **not** a prospective performance test and none is claimed. It is a finite deterministic regression/negative-control audit.

## Question and exact distinctions

CT146's scalar-homomorphism canary is not a test of a genuine nontrivial rational isogeny with poles. Test the same corrected-half identity through a real degree-two rational map, including the kernel point, infinity, the dual map, Frobenius action, and the subgroup subtleties. Distinguish the sufficient condition [2]T=O from the exact condition gamma([2]T)=O; prove/verify no stronger necessity claim. A completely different q223 degree-13/169 homomorphism remains independently unproved.

Use F25 = F5[u]/(u²-2), E:y²=x³+x²+x and the kernel {O,(0,0)}. Put a=b=1, E':y²=x³-2a x²+(a²-4b)x. The standard 2-isogeny is
X = x + a + b/x, Y = y (1-b/x²), with the kernel and infinity mapped to O.
Construct its normalized dual by applying the same formula over E' and scaling x by 1/4 and y by 1/8 to recover E.

Acceptance checks: enumerate both groups fully; verify curve membership, kernel image and cardinality; verify gamma(P+Q)=gamma(P)+gamma(Q) for every ordered pair; verify gamma∘Frob=Frob∘gamma; verify every corrected P+T for T in E[2]; verify dual∘gamma=[2] on all source points; verify at least one non-E[2] T with gamma([2]T)=O and explicitly preserve that nuance; reject a wrong correction with gamma([2]T) != O and reject an on-curve translated nonhomomorphism. Explicit fail-closed runtime checks under both ordinary and optimized Python, identical JSON. No paid compute.

Evidence fields include all tested cardinalities and negative-control totals, not merely an overall true flag. A failure is retained, not silently replaced. This toy test cannot establish q223 gamma being K-defined, a global morphism, Jacobian norm identity, full 695-record parity, native C169/C13a/C13b/D timings or complete cold ECDLP advantage.

## Reviewed sources

- cryptanalysis #1533 CT125 original q223 `rational.rs` and `lib.rs`, #1584 CT145, #1589 CT146; crypto #3877 and #4215; existing CT141 admission gate #1553 / receipt #1562.
- Silverman, *Arithmetic of Elliptic Curves*, Chapter III, Theorem 4.8 (pointed morphism of elliptic curves is a group homomorphism); Harvard Math 223, September 23 lecture notes: https://abel.math.harvard.edu/~elkies/M223.24/index.html .
- Stanford pairing-based cryptography notes, elliptic rational maps: https://crypto.stanford.edu/pbc/notes/elliptic/map.html .
- Shared research-KB service and repository-local Conductor not exposed through available connector runtime; scoped existing primary source review performed instead; no novelty or absence inference.

## Next q223 acceptance

Prove/independently check the actual six rational maps are K-defined pointed morphisms, including poles and descent, replay the unmodified original/reuse 695/701 records with all exceptional outcomes, then run owner-admitted same-host ABBA pricing and complete cold same-target rho/BSGS/IC with setup/LA/transfer/memory/uncertainty and signed PCC. [pcc:unverified]
