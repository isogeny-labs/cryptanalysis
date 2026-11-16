# CT155 — Public-Q projective BSGS strengthens the original-q223 cold source reference

2026-11-16 UTC. Root crypto [#3877](https://github.com/isogeny-labs/crypto/pull/3877); stacked cryptanalysis [#1589](https://github.com/isogeny-labs/cryptanalysis/pull/1589). **[pcc:unverified]**. This is a source-only generic comparator improvement, **not a transferred Jacobian ECDLP**, not a result for arbitrary Fp elliptic curves, and not a benchmark promotion. The [protocol](CT155_PROJECTIVE_BSGS_PROTOCOL.md) was committed as d8dfbd4f **before** final 96-row paired timing; initial exploratory arithmetic debugging was retrospective.

## Exact source and implementation

Reuse the unchanged CT153/CT154 C++17 original source: K=F223[z]/(z^3-3), E:y²=x³+a2x²+a4x+a6, a2=(127,56,199), a4=(152,35,36), a6=(212,109,150), G=((162,197,140),(45,11,207)), prime ell=2773073, full 4ell. The new C++ file includes the untouched original CT153 arithmetic, accepts only six canonical public Q coordinate limbs, and independently verifies every output [k]G=Q; **no source scalar passes into the solver**.

Translate to short Weierstrass with x'=x+a2/3, A=a4−a2²/3. Build baby and giant steps in Jacobian X:Y:Z, with mixed addition and exceptional H=0 doubling/inverse handling. Normalize the 1666 baby points with one Montgomery batch inversion, and giant points in 64-point batches. Preserve point-at-infinity and duplicate-key rejection. New cost instrumentation counts entire complete solver including subgroup validation and verified recovery. The direct affine source and public-point baseline remain byte-identical.

## Local correctness and negative controls

The C++ self-test checks ten separate affine/projective scalar identities including zero, double, 1666 and ell−1, both mixed-add H=0 branches, and six complete public-Q solves. The separate CT153 Python field/group law independently reconstructed another **268 complete candidate logarithms** (12 edge cases, 256 seed-selected public cases) using its own group arithmetic. Eight malformed/off-curve/out-of-subgroup public-input controls were rejected. The extra 268 answers are correctness checks, **not extra timing population**.

Source Git blob readback confirms the local C++ content is identical to committed SHA-1 9440e841a51bd3e5c672418102bf2231311352b3 and auditor to 846a5e51a491b5d11071ded53557d239ab062486. C++ baseline SHA256 a687e28dd543435af9b47a51fa52cc5ba227c9d1dbf97345aa3bbd0d89be988a; CT154 source SHA256 8943e4aeddcadabaca3b130f4d21daba2178d6d330ca54363f01da42d11cc75a. This is **source identity**, not independent signed PCC.

## Producer-local exploratory complete source comparison (96 records)

Host Linux-6.18.57-x86_64-with-glibc2.41; g++ C++17 -O3 -Wall -Wextra -Werror. Six CT154 public source targets, four forward/reversed ABBA-style blocks per target, 96 fresh OS processes (48 per arm), with every recovered logarithm independently recomputed. Record SHA256 over canonical rows: 44ca8cbcd7ed85a963dec6d38e6634150ac7f3a677829fccbb81422e64a8c754.

| Fixed-cohort local diagnostic | CT154 affine fresh BSGS | CT155 projective/batched BSGS |
|---|---:|---:|
| Median harness spawn-inclusive wall | 2.351 ms | **2.101 ms** |
| Median solver clock | 0.660 ms | **0.559 ms** |
| Median field inversions | 1,804.5 | **91** |
| Median field multiplications | 70,521.5 | **45,477.5** |
| Max child VmHWM RSS | **1,792 KiB** | 1,920 KiB |
| Complete public Q answers | 48/48 | 48/48 |

24 blockwise paired differences (affine minus projective) have **median +0.270 ms** and fixed-fixture 4,000-resample bootstrap95 **[+0.135,+0.352] ms**. Median blockwise affine/candidate ratio **1.122**, median within-arm absolute A/A drift **0.168 ms**. This is a non-isolated developer-host diagnostic with six fixed targets: its fixed-case interval is not a population CI and neither signed independent PCC nor isolation-class calibration is present. The candidate uses more memory in the sampled process; do not report an end-to-end transfer or universally faster baseline. The existing rho and IC comparisons were **not re-run**, so this only improves a generic reference arm.

The new source/binary/row digests and every raw process line are retained in the local CT155 evidence archive, not written to GitHub's immutable claim ledger. Only bounded source CI, not full timing, is published.

## Commands

```sh
D=experiments/chained-transfer-public-target/norm-point-reuse-01
g++ -std=c++17 -O3 -Wall -Wextra -Werror "$D/ct154_public_point_reference.cpp" -o /tmp/ct155-base
g++ -std=c++17 -O3 -Wall -Wextra -Werror "$D/ct155_projective_bsgs.cpp" -o /tmp/ct155-new
/tmp/ct155-new --self-test
python3 "$D/ct155_projective_audit.py" --candidate /tmp/ct155-new --baseline /tmp/ct155-base --quick
python3 "$D/ct155_projective_audit.py" --candidate /tmp/ct155-new --baseline /tmp/ct155-base --output /tmp/ct155-raw.json
```

## Unmet decisive transfer gates

CT125 original/reuse full 695/701-record **actual Jacobian** corpus is not independently replayed here. Owner-admitted C169/C13a/C13b/D and same-host cold **transferred** public-point solve against strongest matched rho/BSGS/IC, counting construction, mapping, Jacobian arithmetic, corrections, linear algebra, verification, all setup and peak RSS, are still missing. Prior root #4215 is only prospective counts; CT142 #1562 preserves the native pricing admission and rejection gates. CT151/152 prime-field Frobenius source obstruction also remains. No new paid EKS/GPU job, no original fixture mutation, no protected merge or claimed complete transfer advantage.

Sources checked: CT153/154 source/report and primary EFD (Bernstein–Lange, https://www.hyperelliptic.org/EFD/g1p/index.html), Stanford explicit affine group-law note (https://crypto.stanford.edu/pbc/notes/elliptic/explicit.html), prior chained-transfer root #3877, CT125 #1533, CT142 #1562, #4215 and #4178. Research-KB MCP/CLI and local lead atlas unavailable; no novelty or absence-of-prior-art assertion. **[pcc:unverified]**.
