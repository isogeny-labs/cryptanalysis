# Quadratic determinant-value certificates cover complete N41 code regions

**An exact quadratic Boolean functional certifies seven four-bit source-prefix buckets against the frozen N41 public target.** Those buckets contain **30 of 35** admissible first-pair codes, with both x roots and all 64 six-sign assignments checked for every code. A separate greedy certificate covers six complete codes (768 root/sign states); none of the other 29 codes can be added to that particular certificate. The known relation sits in the eighth prefix bucket at first-code mask 6, root 1, sign mask 15, so the screen preserves its independently replayed positive control.

This is the first complete-code nonlinear extension of the earlier sign-linear Riemann–Roch certificate on the same source panel. The preceding exact [linear census](../n41_rr_pairwise_certificate_20261017/RESULT.md) found no shared linear certificate even across both roots of one code. The present method constructs each quadratic certificate from the enumerated determinant values in its bucket. Its next gate is a symbolic or incremental construction that can reject unresolved source-code regions before those values are expanded.

## Exact method and frozen source

The curve is `y²+xy=x³+1` over `GF(2)[t]/(t⁴¹+t³+1)`, with subgroup order `549756390943`. The frozen raw public target is `(2026560328086,1928332930914)`. Five pair-code and x-root choices come from the independently replayed six-pair relation in the [source experiment](../n41_rr_pairwise_certificate_20261017/RESULT.md); their six y-sign bits remain free. This is a witness-derived fixed-five-slot certificate-capacity panel, not a search input selected by an unpinned algorithm. The first slot ranges over all 35 canonical seed-56 W8 pair codes whose folded columns avoid the five fixed pairs. For each first code, both x roots and all 64 sign assignments give 128 determinant values. The source audit checked every seven-point determinant and its distinct-x chart condition.

Write the 41 binary coordinates of a determinant value `D` as `d_i`. For coefficients `a_i,b_ij∈GF(2)`, the score is

`Q(D)=Σ_i a_i d_i + Σ_{i<j} b_ij d_i d_j`.

There are `41+binom(41,2)=861` Boolean features and no constant term, so `Q(0)=0`. Requiring `Q(D)=1` for every state in a code family is an exact linear system in the 861 coefficients. A solution proves that none of those states has determinant zero and therefore rejects the whole family on the audited distinct-x chart. This is a target-conditioned certificate: the determinant includes the negative public target as its seventh row.

The [frozen protocol](protocol.json) hashes the prior producer, independent Sage determinant audits, this runner, the Lean source and toolchain. [run.py](run.py) evaluates the saved sign ANF by a subset transform, constructs all 861-bit feature rows, and solves their binary systems with high-pivot elimination. The [independent verifier](verify.py) uses direct ANF subset sums, a separate feature evaluator, and low-pivot elimination; its own frozen source list is in [verification_protocol.json](verification_protocol.json).

## Measured finite-panel results

| Exact N41 panel check | Result |
| --- | ---: |
| Admissible first codes / determinant states per code | 35 / 128 |
| Individually quadratic-certifiable complete codes | 34 |
| Code with a zero determinant | mask 6, root 1, sign 15 |
| One greedy shared certificate | masks `2,3,5,7,16,18`; 768 states; feature rank 768 |
| Possible one-code extensions of that certificate | 0 of 29, independently checked |
| Coarsest nonempty high-bit prefix depth with a certifiable bucket | 4 of 8 bits |
| Four-bit buckets certified / all occupied buckets | 7 / 8 |
| Admissible codes inside those seven buckets | 30 / 35 |
| Largest certifiable four-bit bucket | 5 complete codes |
| Producer feature construction, certificate solves and bucket sweep | 1.627 s exploratory Python interval |

At depths zero through three, every occupied prefix bucket is inconsistent. At depth four, prefix values `1,4,5,8,9,12,13` have checked certificates; prefix zero contains the relation's zero determinant. The result file retains each bucket's exact code list, status, rank until decision, and coefficient vector for every certificate. The 1.627-second interval is an ordinary-host component diagnostic inside the Python worker; it excludes process launch and source-file loading. The 11.263-second independent replay checks every positive bucket and recomputes every negative bucket's inconsistent system. Neither interval measures an IC target query.

The [terminal receipt](terminal.json) reports `PASS_N41_QUADRATIC_RR_VALUE_CERTIFICATES`. It binds the exact [result](result.json), the independently audited coefficient inputs, the full witness checks, all 29 extension failures, every prefix-bucket decision, and the Lean axiom audit. The method is a research component with `candidate_id: null`.

## Proof and next experiment

The readable proof is the identity `Q(0)=0`: a family on which `Q(D)=1` cannot contain `D=0`. [QuadraticCertificate.lean](QuadraticCertificate.lean) proves this for the exact Boolean diagonal and off-diagonal monomials under pinned Lean 4.34.1; `#print axioms` reports only `propext` and `Quot.sound`. The [proof map](PROOF_MAP.md) separates that checked implication from the curve/determinant and finite-panel bridges supplied by the archived checked-Sage audits.

The next constructive test is to derive a four-bit-prefix certificate **from the source-code equations**, without enumerating all member codes or all 128 root/sign values per code. Then choose every fixed slot without consulting the known relation and run against this same public N41 target and matched exact join, charging synthesis, every failed region, and relation replay. An N131 trial requires a frozen source-bound projection under one worker, 600 seconds and 4 GiB: a four-bit W23 bucket may contain many more than the three-to-five admissible codes seen here, so the N41 bucket counts alone do not predict N131 rejection or cost.
