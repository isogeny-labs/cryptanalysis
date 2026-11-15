# CT144 — projective/batch-normalized source BSGS versus mapped rho (pre-code protocol)

Date: 2026-11-15. Standing: [pcc:unverified].
Root crypto #3877; CT138–140 source comparison #1550/#1552; actual q223 pricing #1562 is separate and owner-gated. This is a deliberately **free local 31-bit toy** comparator, not a claim about the unexecuted original q223 695/701 Jacobian workload.

## Question
The existing source BSGS makes roughly sqrt(r) affine additions with one extended-Euclidean inversion each. Can a source-side projective BSGS (one Montgomery batch normalization after computing baby and giant Jacobian point sequences) beat or overturn the transferred fourfold-rho speed ratio? Evaluate on exactly the already frozen CT140 public cohorts and preserve all exact CT140 C++ source/hash evidence. Do not tune source/candidate on per-target outcomes.

## Frozen algorithm and independent checks
1. Use the unchanged CT135 curve/point/target records: F_p, p=2147483033, q=536857417, source y²=x³+a x²+b x with a=622683939, b=2147483024, source G=(911976709,415929193), degree-2 mapped j=1728 target and verified scalar k. Derive all scalars from the unmodified MT64 CT140 seed sequence: seeds 20261340, 20261341, 20261342, 20261343; 32 distinct targets/seed.
2. Build an independent Jacobian mixed-add and doubling implementation for the **non-short** y²=x³+a x²+b x equation; must include the a*x² correction in addition/doubling. Normalization: one batch inverse per nonempty list and exact Z=0 handling. Validate all generated baby and giant points against the original independently used affine Curve.times/addition over at least 250 fixed randomized scalars and infinity/doubling/inverse/zero-coordinate edge cases. No trust in the resulting recovered scalar alone.
3. Complete source BSGS from projective baby sequence and projective giant sequence (including the final scalar/point verification), every target cold, with per-solve memory receipts. Compare against unchanged source rho batch4 and mapped rho batch16; source/target no hidden precomputation across targets, every setup/map/verify charged. A/A source and mapped controls interleaved in reversing order. Same public targets.
4. At least two independent 128-target complete executions, cap each child at 120 s and 2 GiB. Freeze source after preflight; source and binaries SHA-256, compiler version, CPU/VM identity, process elapsed/RSS, raw per-target ns, arithmetic answers, iterations/states, and failure controls. Explicitly distinguish wall clock, process and inner solver ns.
5. A separate Python verifier that does not import producer EC arithmetic must recompute source G*log=Q, isogeny map compatibility, target choice, exact target keys, row cardinality, per-arm sums, unique cohorts, expected order, and reject at least 6 mutations including source answer, coordinate, missing arm, fabricated total, wrong seed, duplicate row. Always run normal and python -O. All failures retained.
6. Compare fastest **fixed complete source arm** across source affine BSGS, projective BSGS, and batch4 rho versus fastest fixed mapped rho (batch16). If source BSGS wins, preserve that negative for the old transfer speedup. If mapped rho wins, report only its ratio to this limited named comparator. Provide descriptive paired bootstrap uncertainty, process RSS and host limitations; do not pool different hosts.
7. Do not use an offline BSGS lookup table or amortize precomputation; separately price that only as an exploratory future baseline. No EKS, Spot, GPU or paid native benchmark. Existing q223 CT141 owner-secret admission remains untouched.

## Required acceptance and caveats
- All public logs verified and 100% complete; mutation controls reject; pinned input sources and prospective protocol; full raw records.
- No public PR claim without [pcc:unverified] or signed independent PCC. No general ECDLP advantage, no 695/701 parity or q223 C169/C13/D from these 31-bit toy runs.
- Concurrent norm-point producer/consumer work and original source evaluators/fixtures unchanged. If the source BSGS is slower, record the negative and return priority to owner-admitted native pricing and original-prime IC/rho comparisons.
- Research-KB connector/catalog not accessible in this runtime; GitHub code search for projective BSGS checked, not an absence/novelty claim.
