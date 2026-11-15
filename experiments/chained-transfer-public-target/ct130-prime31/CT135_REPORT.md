# CT135 — bounded cold ECDLP with optimized affine inversions

2026-11-15 · [pcc:unverified] · CT134 #1545 child; originally CT133 #1542; crypto root #3877.

## Technical advance

Built a **second C++17 implementation** of the exact CT133 three-arm, single-public-target
cold-solve experiment. All source/destination elliptic additions now use an explicit
extended-Euclidean finite-field inverse; CT133 originally used Fermat powering.
The two rho arms share that same optimized primitive rather than timing different
inversion implementations. Each target still gets fresh jump tables or BSGS baby table,
source public-point input, target point maps (inside time), recovered logarithm and
source postverification. Source BSGS vs source negation-fold rho vs mapped target
fourfold rho; no curve/order/target re-selection.

Original p=2147483033, q=536857417, E: y²=x³+622683939x²+2147483024x,
G=(911976709,415929193); target T: y²=x³+9x,
H=(180482573,1535800095). Explicit degree-2 isogeny; both prime-order
public point images checked. Source has j=287496, not j=1728; this is a
**specially selected CM-neighbor toy**, not a general reduction of ECDLP.

## Actual producer-local measurement

Host: Linux x86_64, AMD EPYC 9V74, Debian g++ 14.2.0, CPU cgroup 400000/100000,
~6 GiB visible memory. Compile: `g++ -O3 -std=c++17 -Wall -Wextra -Werror
ct135_native.cpp -o ct135_native`.

The first four seeds 20261210–13 were run before the CT135 protocol was
committed and are **retrospective exploratory** (same target seeds as CT133).
They returned per-panel source-best / target ratios 1.42180, 1.42193, 1.22479,
1.26588, pooled 1.33427x. They are retained, *not* promoted as fresh holdouts.

The **prospective** exact seeds 20261220–23 were frozen in CT135_PROTOCOL.md
(commit 5fc38647) **before** the bounded local run. Each seed used 64 public
targets, six complete cold logarithms per target (384 solves/panel).
The 256-source-Q / 1,536-complete-solve population was all postverified.
Each arm is counted twice per target in alternating ABCCBA/CBAABC order.

| Prospective seed | Source BSGS (ns) | Source neg-rho (ns) | Target 4fold rho incl. map (ns) | Best source / target | peak process RSS (KiB) |
|---|---:|---:|---:|---:|---:|
| 20261220 | 519145431 | 410623928 | 361411849 | 1.136166 | 5628 |
| 20261221 | 526990352 | 440582520 | 284906911 | 1.546409 | 5624 |
| 20261222 | 526443209 | 445195206 | 316514427 | 1.406556 | 5756 |
| 20261223 | 512611635 | 424665175 | 309619602 | 1.371571 | 6048 |
| **Pooled** | 2085190627 | 1721066829 | 1272452789 | **1.352558** | per process above |

Independent Python arithmetic implementation validated all 1,536 recovered source
logarithms, source/target curve points, map(G), map(Q), q-torsion identities,
fresh table widths/counters, ABCCBA/CBAABC schedules, totals and the scalar
eigenvalue; explicit exceptions (not assertions) rejected nine deliberately
corrupted evidence variants in both `python -S` and `python -O -S`.
Both audit modes produced byte-identical JSON.
Descriptive paired-target bootstrap range (2.5–97.5%, fixed cohort): 1.235–1.477.
This is **producer-local** and not a calibrated EKS host, signed PCC,
strongest-source reference, or cost-complete Jacobian proof.

Raw prospective CSV SHA256:
- 20261220 `55460a9f28e2f52b618e4949986240d2babb8429e702490188b6fdb527bd0639`
- 20261221 `cd36a9024998f1d26122dc16c15e0f64186de3111bb9e2292dd638923143cf34`
- 20261222 `7475608af4f3bc1986a1342322efa3e79d9fec4c6c1246f558f0422d089318bb`
- 20261223 `5ce7718ec3658f4cf98a91114ff8b3f1c2522bc5ebba75d3a12a411bce6baeb3`

Executed source SHA256: `ct135_native.cpp=5422e02524850bfb0f595901c063a07326079e9dd82a483e6085996ce97bbdb0`;
`ct135_verify.py=0849be74cc81072c4ee71eb2f2f266112d58fb7ded83f1077ece76372a2ea5ab`.
Both **exact executed bytes** were uploaded to GitHub and their Git blob SHA1
compared with locally computed `git hash-object`: C++ `4d94fc9163e86689a09c6d6685dd017c5c4c9698`;
Python `34a171a71bb597f431c9b0842a799eb861d18fc4`.

## Reproduce

```sh
cd experiments/chained-transfer-public-target/ct130-prime31
g++ -O3 -std=c++17 -Wall -Wextra -Werror ct135_native.cpp -o ct135_native
for seed in 20261220 20261221 20261222 20261223; do
  /usr/bin/time -f 'wall=%e RSS=%M' -o "$seed.time" ./ct135_native 64 "$seed" > "$seed.csv"
done
python3 -S ct135_verify.py 2026122{0,1,2,3}.csv > audit.json
python3 -O -S ct135_verify.py 2026122{0,1,2,3}.csv > audit-O.json
cmp audit.json audit-O.json
sha256sum 2026122*.csv ct135_native.cpp ct135_verify.py
```

GitHub Actions `ct135-fast-inverse-cold.yml` is an independent-host **proposed**
replay; its exact run/pass/artifact status is not asserted before observation.
Producer-local raw files are retained in a conversation ZIP, **not copied into
the Git repository**; the Action uploads its separately generated raw records
and audit for 30 days if the workflow executes.

## Decision and obligations

The limited CM-neighbor advantage **survives replacing Fermat inversion
with faster extended Euclid in both rho arms**, but it remains a
non-general 4-orbit versus 2-orbit rho win. It does not constitute
the owner's complete single-target ECDLP acceptance result.
The source still lacks optimized projective/batched inversion rho,
source-side optimized endomorphism comparison, matched cold IC and paid-host
isolation. Furthermore the full original-prime 695/701 Jacobian chain,
all correction classes, real native C169/C13a/C13b/D pricing, construction,
linear algebra/setup and peak memory across all phases remain separate.

**Next decisive gate:** on a pinned isolated host compare strongest projective
or batched-inverse source rho against target GLV rho on the same public targets,
then execute CT126 #1534 and source norm-reuse #1523 with all 695/701 records and
matched rho/BSGS/IC. Record negative outcomes and switch to non-generic IC if
optimized source closes the ratio. Do not extrapolate this CM toy to NIST
curves or claim a generic asymptotic improvement.

Prior art/read: CT133/CT134 reports, cryptanalysis #1534/#1523, root #3877,
GPU IC #4178; classical Vélu, GLV and rho folding. Shared KB/lead atlas
checkout unavailable here; no novelty or exhaustion claim. [pcc:unverified].
