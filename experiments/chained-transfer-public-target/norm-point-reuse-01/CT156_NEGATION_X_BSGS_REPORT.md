# CT156 — signed-x-coordinate BSGS for the original q223 public source

2026-11-16. Existing stacked PR #1589; scientific standing **[pcc:unverified]**. Frozen prospective protocol: CT156_NEGATION_X_BSGS_PROTOCOL.md (commit d41a0842); this experiment executed full paired timing only after that commit. Pilot formula/debug/quick tests were exploratory. Raw full developer-host logs are kept in the separate CT156 evidence archive, not GitHub/PCC-signed.

## Finding (scoped)

Complete fresh-table public-Q DLP solving for the fixed original cubic source E(F_(223^3)), order ell=2773073. This is *not* a prime-field elliptic curve, Jacobian chain, degree-169 transfer or novel non-generic algorithm. A signed giant-step stride 2m and x-only batch normalization reuse the CT155 Jacobian arithmetic, with m=1178, storing jG for 0<=j<=1178; each x match tests the actual source equality kG=Q for both signs. A separate Python field/group law checked all outputs. This is a standard negation-map optimization (Galbraith–Wang–Zhang, AMC 2017, DOI 10.3934/amc.2017038); it makes the *source reference* harder for a transferred algorithm to beat.

## Developer-local complete public-source diagnostic [pcc:unverified]

C++17 g++ -O3 -Wall -Wextra -Werror on Linux 6.18.57 x86_64 (glibc 2.41), non-isolated. Six preexisting CT155 public Qs, four alternating ABBA/BAAB blocks each, 96 fresh OS process executions total; 48 CT155 unchanged baseline, 48 CT156 signed-x candidate. Every answer independently verified through Python original-field source multiplication.

| Metric (median except peak RSS) | CT155 baseline | CT156 signed x |
|---|---:|---:|
| Harness fresh-process wall | 1.856407 ms | 1.720412 ms |
| Solver only | 0.476495 ms | 0.2796765 ms |
| Field multiplications | 45,477.5 | 24,912.5 |
| Field inversions | 91 | 93.5 |
| Baby table entries | 1,666 | 1,179 |
| Peak VmHWM | 1,920 KiB | 1,836 KiB |
| Correct full public-Q source solves | 48/48 | 48/48 |

24 blockwise paired baseline-minus-candidate wall averages: median **+0.172618 ms**; 4,000-seed fixed-cohort bootstrap median interval [+0.076503,+0.240629] ms. Paired block median baseline/candidate wall ratio 1.10138, median absolute within-arm A/A drift 0.116471 ms. These are *fixed cohort, same developer host* diagnostics, NOT confidence intervals across curves/hosts or independent PCC certification. There are no matched source optimized rho/IC reruns in CT156.

Additionally: 272 independently generated public source targets, 16 deterministic boundary/log checks, eight invalid-input controls rejected. An independent integer arithmetic exhaustive coverage loop confirmed every k=0..2773072 has some (i,j) with k=2mi+j and |j|<=m inside implemented range. This checks representation, not a complete group-map proof.

## Reproduction

```sh
D=experiments/chained-transfer-public-target/norm-point-reuse-01
g++ -std=c++17 -O3 -Wall -Wextra -Werror "$D/ct155_projective_bsgs.cpp" -o /tmp/ct156-old
g++ -std=c++17 -O3 -Wall -Wextra -Werror "$D/ct156_negation_bsgs.cpp" -o /tmp/ct156-new
/tmp/ct156-new --self-test
python3 -S "$D/ct156_negation_audit.py" --baseline /tmp/ct156-old --candidate /tmp/ct156-new --quick
python3 -S "$D/ct156_negation_audit.py" --baseline /tmp/ct156-old --candidate /tmp/ct156-new --output /tmp/ct156-raw.json
```

Raw canonical JSON rows SHA256: `6c98516c45d3722c491e4d970de0f2fd0476bdf00d0c0ab0428a9172380851bd` (hash over sorted compact row objects). Git blob SHA-1 C++: `392423b3ca94f48d47dbedc5587a2babac8161dc`; independent Python: `85933305f88bc2f6d4549415f37e7ac446101053`. No original native 695/701, signed PCC, root ledger or budget gate was changed.

## Priority after this comparator

Owner-admitted same-host C169/C13a/C13b/D real primitive pricing and *independent* original/reuse parity on the complete unchanged Jacobian fixture remain with CT125/CT142 (do not duplicate concurrent branches). Then require a **complete cold transferred public-target DLP** vs strongest same-host rho/BSGS/IC, including setup, source/target transport, norms, corrections, full verification, linear algebra, memory, A/A, uncertainty and signed PCC. A stage speedup or this stronger generic source comparator is not a transfer win. [pcc:unverified]
