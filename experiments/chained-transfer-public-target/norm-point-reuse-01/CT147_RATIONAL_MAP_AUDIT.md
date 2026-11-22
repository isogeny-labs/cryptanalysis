# CT147 — real rational isogeny, dual, pole and correction-kernel audit

Date: 2026-11-15. Root crypto #3877; cryptanalysis #1589. Status **[pcc:unverified]**.

## Finite contract and mathematical correction

CT146's finite canary uses multiplication maps only. CT147 adds a genuine nontrivial degree-two rational isogeny with actual poles and a nontrivial kernel. Over F25 = F5[u]/(u²−2), let E be y²=x³+x²+x and E' be y²=x³−2x²+2x. Define
`phi(x,y)=(x+1+1/x, y(1−1/x²))`, with phi(O)=phi((0,0))=O.

For any group homomorphism gamma, [2]P=Q and arbitrary correction T, the **exact** algebraic discrepancy is

    [2]gamma(P+T) − gamma(Q) = gamma([2]T).

Therefore gamma([2]T)=O is necessary and sufficient for this elliptic equality. The CT125 source's explicit [2]T=O is a **sufficient** condition. Do not falsely claim it is necessary when gamma has a kernel. This does not replace a proof of actual q223 gamma, actual Jacobian norm or faithful descent. [pcc:unverified]

The normalized dual isogeny sends E' back to E using the second map with coefficients a'=-2,b'=2 followed by scaling x by 1/4 and y by 1/8; it composes with phi to [2] on the finite test. The program checks all actual rational-map pairs rather than assuming homomorphism from its formula.

## Bounded development execution

An exploratory stand-alone Python prototype was executed locally before protocol publication. After fixing a component-negation bug in the development field encoding and a second erroneous reduction of the scalar 16, the exact finite experiment returned under ordinary and optimized Python, with matching canonical JSON:

| Check | Count |
| --- | ---: |
| E(F25) and E'(F25) points | 32 each |
| Image points | 16 |
| Full geometric E[2] | 4 |
| Ordered rational-map addition identities | 1,024 |
| Corrected-half identities (T in E[2]) | 128 |
| Frobenius commuting checks | 32 |
| Dual composition equals [2] | 32 |
| Non-E[2] corrections with phi([2]T)=O | 4 |
| Their additional corrected-half checks | 128 |
| Incorrect corrections with phi([2]T)≠O rejected | 32 |
| Translated on-curve nonhomomorphic map | Rejected |

The original development negative control incorrectly selected any non-E[2] T, but such a T can have [2]T inside ker(phi). It was tightened to choose phi([2]T)≠O and thus exposed the exact kernel-aware condition above. These development corrections were made **before** repository publication of the CT147 test. The new committed workflow must execute the *exact committed script* before any hosted result is asserted. No paid compute. [pcc:unverified]

Source-only commands:

    python3 experiments/chained-transfer-public-target/norm-point-reuse-01/ct147_rational_isogeny_canary.py
    python3 -O experiments/chained-transfer-public-target/norm-point-reuse-01/ct147_rational_isogeny_canary.py

The workflow compares canonical JSON and exact finite counts. It does not use the historical q223 models or EKS. It is a finite **mathematical stress test**, not an end-to-end complete ECDLP experiment.

## Translation to the actual q223 experiment

CT125 uses verified 2-torsion corrections at the source and gamma as a declared degree-13/169 rational map. To turn the abstract identity into an original-instance result, the six maps must be certified as K-defined pointed morphisms (all poles, infinity and base change), the original and reuse **unfiltered** 695/701 records must have identical classes, independently checked Jacobian norms and preserved error/exception descriptors, and the separately owner-admitted native C169/C13a/C13b/D runner must actually execute. The strongest cold original-prime rho, BSGS and IC must be compared on the same public targets including setup, transfer, LA, verification, memory and signed PCC. No such advantage is asserted. [pcc:unverified]

Primary references checked: Silverman *Arithmetic of Elliptic Curves* III.4.8 (pointed morphism implies group homomorphism), Harvard lecture notes https://abel.math.harvard.edu/~elkies/M223.24/index.html, Stanford rational-map reference https://crypto.stanford.edu/pbc/notes/elliptic/map.html. Prior work reviewed: cryptanalysis #1533, #1584, #1589 and crypto #3877/#4215, including the existing original `rational.rs` and `lib.rs`. Research-KB MCP and Conductor unavailable in this connector runtime. No novelty claim.

**Scientific standing: [pcc:unverified].** This is not a q223 speedup, independently signed result or benchmark admission.
