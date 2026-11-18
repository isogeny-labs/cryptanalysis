# CT198 — prospective frozen-48 route-counter comparison
Date: 2026-11-17 America/Denver. Standing: [pcc:unverified].

## Scope, reuse, and no paid work
Use only the original CT125 source-frozen 48 selected public Jacobian packets, Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`, at `experiments/chained-transfer-public-target/evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json`. Validate its original bytes using CT192's existing `source_contract.py` before interpretation. Source CT125 blob is `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc`. Preserve both verbatim. This is a counter audit, not a new target, benchmark, native replay, or 695/701 custody replacement. No EKS/GPU or paid compute.

## Preregistered audit
- Check all 48 unique direction × sector × external-label public rows, original 21 counter names and 3 route dictionaries; verify row-level complete output equality (the source fixture's original `whole_outputs_equal` field is *producer-asserted*, not independently replayed).
- Independently sum each counter for the original `direct_composite`, `literal_sequential_Jacobian_maps`, and `strongest_retained_lift_chain`; split identity (label 0, 8 packets) and generic (40) without blending identities into generic cost claims.
- Calculate exact pairwise **integer counter vectors** and assert for every row that direct composite vs strongest retained chain differ only in `degree169_elliptic_evaluation` and `degree13_elliptic_evaluation`. Expected direct: one C169 / zero C13; strongest retained: zero C169 / two C13. All remaining 19 counter fields must agree exactly, including `transported_norm_doubling == 1`.
- Assert literal sequential and strongest retained both evaluate degree13 twice, but literal sequential uses two norm-point doublings versus one for retained; all other counter differences must be nonnegative, including generic-halving/reconstruction. Identify **which** entries change, not just their sum.
- Negative controls: mutate source fixture blob, change one counter, alter a route, lose an identity or generic row, and reverse a dominance sign. Original source is not modified to test mutations.

## Interpretation and thresholds
For a static additive primitive cost model with unchanged other named counters, direct-versus-retained change per packet is **C13a + C13b − C169** (retained minus direct). A retained chain is less expensive under this model only if C169 > C13a+C13b; any setup, branch or memory differences require their *additional* actual prices and may reverse this condition. Norm-point reuse cannot, by itself, change the direct-versus-retained comparison because each route already performs one transported norm. Relative to *literal sequential* the retained chain saves one norm and duplicate halving/correction passes, but that does not establish an advantage over the strongest direct arm.

Do not infer which arm is faster in wall time or claim a DLP improvement. Next accepted evidence must be *real* same-host paired C169/C13a/C13b/N2_actual/D with native arithmetic/counter parity, complete cold prime-field target rho/BSGS/IC comparisons, RSS/CI/PCC and authenticated 695/701 custody. Every claim here stays [pcc:unverified].
