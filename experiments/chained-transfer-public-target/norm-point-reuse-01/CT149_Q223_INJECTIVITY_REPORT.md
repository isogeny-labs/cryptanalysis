# CT149 — q223 prime-subgroup and full-group 13-primary exclusion

15 November 2026 (America/Denver). Root crypto #3877; cryptanalysis PR #1589. All results are **[pcc:unverified]**. This is a short independent integer check of **already reported** source-order parameters, not a native q223 map certification or complete ECDLP measurement.

## Conditional result

The previously reported original fixed q223 source has ell=2,773,073 and #E(K)=11,092,292=4ell. The separate fixed-nu12 model has ell=2,771,711 and #E(K)=11,086,844=4ell (original #3877 session logs and CT129 #1537 protocol). The deterministic test exhaustively checks trial divisors up to integer sqrt for both ell values and gcd with 13 and 169 for both subgroup and full orders.

| Model | Prime ell | #E(K) | gcd(#E(K),169) | 13 inverse mod #E(K) | 169 inverse mod #E(K) |
| --- | ---: | ---: | ---: | ---: | ---: |
| original fixed | 2773073 | 11092292 | 1 | 3413013 | 9648325 |
| alternative fixed nu12 | 2771711 | 11086844 | 1 | 5117005 | 7216289 |

The last two alternative-model inverses **reproduce existing original root proof/session-log witnesses**. This is an independent cross-check, not a novel result. Both ell values are different and must not be substituted. Subgroup inverses for degree13/169 are respectively (639940,1329106) for original and (2345294,1672867) for alternative.

**Theorem (conditional, conventional isogeny algebra).** Given any genuine isogeny gamma:E -> E' of geometric degree d with d dividing 169 and a source subgroup H of order coprime to 13, the kernel intersection H∩ker(gamma) is trivial. Consequently gamma is injective on H and ord(gamma(G))=ord(G) for each G in H. If gamma has a dual with gamma_hat gamma=[d], multiplication by d^{-1} mod the exponent of H after gamma_hat gives a left inverse on H. This remains true across a chain of degree-13 hops. No explicit q223 map was inspected by this integer script.

**Therefore CT148's F229 order-104 -> image order-8 collision cannot occur on either of the reported q223 *rational source groups*, provided their orders and the maps' isogeny degrees are genuine.** Even the claimed full groups, not just their prime-order subgroups, have order coprime to 13. This does NOT rule out a kernel at another degree, a Jacobian cover transfer collapsing ℓ-torsion, an extension-field or Frobenius issue, incorrect map source code, or a failed cofactor/half-correction identity. It also does not prove any complexity improvement. No surjectivity onto the larger extension-field codomain is claimed.

## Local execution and negatives

Reproducible commands (no dependencies beyond Python standard library):

    python3 experiments/chained-transfer-public-target/norm-point-reuse-01/ct149_q223_injectivity_audit.py > /tmp/ct149-normal.json
    python3 -O experiments/chained-transfer-public-target/norm-point-reuse-01/ct149_q223_injectivity_audit.py > /tmp/ct149-opt.json
    cmp /tmp/ct149-normal.json /tmp/ct149-opt.json

Developer-local Python 3.13.5 produced byte-identical normal/-O output. Checked 1,664 and 1,663 candidate trial divisors, all four gcd/degree cases on both groups, and exact modular inverse identities. Three intentional invalid inputs were rejected: an order with 13-torsion (104), a wrong full-group count and a composite alleged prime. Script SHA-256 (local) a08651a55d69a4c6f50b8f2d38223752f1afd6c6187d14f6ab4c69bb996805d3; JSON SHA-256 b9e2ec3ee02b6cadc6bab78e2f455c962a77b1735cce7fff846fdbac0367604e. Exact GitHub head CI must be inspected before saying that hosted source executed.

## Status and cost priority

Root #3877's 2026-11-15 session log **already reports** a separate 695-record native norm-point parity result (producer-side claim 46008b), with expected selected-call substitutions. That is not independently re-run here; it should not be overwritten or described as absent without inspecting original raw evidence. This CT149 integer check is independent of that native parity and says nothing about C169,C13a,C13b,D measured cost.

Highest-value next work: source-bind both claimed point/group orders and all q223 actual rational maps' degrees/homomorphism/descent; inspect original whole-695 parity and already existing evidence; then execute owner-admitted paired native ABBA primitive timing and complete same-target cold source/candidate rho/BSGS/IC, counting setup, norm, LA, verification, RSS and uncertainty. The original budget/CI/PCC/review gates stay unchanged. No paid compute, merge, or performance claim in CT149.

Prior art and related work: crypto #3877 original root proofs/session logs, cryptanalysis #1537 CT129, #1533 CT125, #1589 CT146–148, crypto #4215, Silverman *Arithmetic of Elliptic Curves* III.4; research-KB and Conductor unavailable in this tool runtime, so no novelty or absence statement. [pcc:unverified]
