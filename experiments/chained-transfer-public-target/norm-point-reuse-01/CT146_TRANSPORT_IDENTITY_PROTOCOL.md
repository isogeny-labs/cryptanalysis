# CT146 prospective transport-identity audit (frozen before implementation)

Date: 2026-11-15. Parent: CT125 #1533, CT145 #1584 (merged into parent). Root: crypto #3877. Standing: **[pcc:unverified]**.

## Decision question

CT145 showed that ordinary quadratic point trace of a nonrational point need not equal its double even when the double is rational. Does that counterexample actually invalidate CT125's replacement of the *second source-isogeny evaluation* by doubling the **already transported, corrected** elliptic point? Treat group trace, elliptic point transport, and Picard/Jacobian norm as three distinct operations. No native q223 outcome is assumed.

## Prospective mathematical hypotheses / falsifiers

For elliptic groups A and B (over a common extension), q in A, p in A, t in A[2], and an identity-preserving *group homomorphism* g:A->B with [2]p=q, let z=g(p+t). Then [2]z=g(q). For two compatible homomorphisms g1,g2, [2]g2(g1(p+t))=g2(g1(q)). No Frobenius-fixedness of p or z is needed for **these particular equalities**. The original source program's reference norm is g(lift(q)), not a quadratic field trace of z. The corrected-lift route must actually add an order-two t; the map must actually be a group homomorphism; the target point's double must descend faithfully into the source K model.

Separate obligation: relating Picard/Jacobian norm N(Phi(z)) to [2]z is *not* proved by these identities. The unchanged independent `check_final` is a runtime acceptance predicate, not a theorem about all possible inputs. CT125 must preserve exactly the same class Phi(z), source packet, correction, and test population. Because its old/reference transported norm equals [2]z under the stated hypotheses, old and reused final acceptance predicates must agree; a native whole-record equality audit is still mandatory.

## Experiments frozen now

1. Independently implement F25 arithmetic and the curve y^2=x^3+1, not importing CT145's arithmetic. Exhaust all 36 points and the 4 geometric 2-torsion points (the toy has **only 2 K-rational** 2-torsion points, unlike actual q223, so do not conflate populations): 144 corrected-lift pairs.
2. Check the identity for five single scalar homomorphisms [2],[3],[5],[7],[13] (720 equalities) and three composed pairs [3] then [5], [5] then [7], [13] then [13] (432 equalities).
3. Include CT145's Z=(4+u,3) with rational double, unequal Frobenius trace; require the transported-double identity still holds. Deliberately substitute a non-2-torsion correction and a translated, nonhomomorphic map: each must be detected.
4. Fail closed under normal and `python3 -O` (same canonical JSON). In source-bound mode require the original Rust Git blob `8016634385d76207b23a3eb3a4dae9b0366ac68d`, actual halves/2-torsion checks, original source norm and final norm predicate, and call CT125's pinned transformer; reject any changed source. Perform only syntax and source checks in free source-only CI; do not execute native ECDLP or paid compute.

## Acceptance / possible results

A passing F25 canary + pinned Rust structural checks establishes the *conditional* group-theoretic equivalence and the precise obligations of the unchanged CT125 implementation. It does not establish that the q223 rational maps globally preserve the group law, actual 695/701-record parity, Jacobian norm identity, complete single-target cost, or independent signed PCC. A failed check is a negative/inconclusive finding; preserve failure and do not waive it. Next: admitted native full 695/701 parity, then same-host C169/C13a/C13b/D ABBA timing and matched strongest cold rho/BSGS/IC including setup, transfer, LA, verification and RSS.

## Sources reviewed before implementation

- cryptanalysis #1533 source `fixed-jacobian-chain-evaluator-01/src/lib.rs` Git blob `8016634` and `build_norm_reuse.py`; `src/rational.rs` uses actual composed rational maps; #1584 CT145 trace counterexample/canary.
- cryptanalysis #1562 cost envelope; #1553 gated native pricing; #1581 projective BSGS negative and #1576 complete-cost work (avoid concurrent branches).
- crypto #3877 (root, current ledger divergence), #4215 prior cost model; GPU IC #4178 prior control.
- Repository AGENTS.md and current open-PR scan; KB service not exposed in this tool environment. No novelty/absence claim.

No protocol change after observing implementation results; amendments, if needed, must be separately versioned. [pcc:unverified]
