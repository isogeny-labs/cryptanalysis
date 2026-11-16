# CT132 — Three-arm CM-isogeny public cold DLP control

**2026-11-15 · [pcc:unverified] · producer-local L0, no independent signed execution or benchmark admission.** Frozen [prospective protocol](CT132_PROTOCOL.md) was committed at `b8545305` and clarified at `ade2656d` **before implementation or timing**. Child of CT131 #1540, rooted at crypto #3877. Existing CT130/CT131 solvers, frozen 695/672/701 Jacobian records and CT126 primitive-pricing branch were not modified.

## Question and measured diagnostic

CT131 compared only source negation-rho with a mapped target fourfold-rho. CT132 adds a second genuine, **cold fresh-table source BSGS** competitor, on the exact same public target points. The three arms run on the same portable Python affine arithmetic, each with new tables/jumps and original-source scalar verification. Existing CT131 rho is imported unchanged (exact Git blob `095cd6e2fd1d302803d2ce5e0d0a16e2c37b9604`). BSGS uses the already checked CT130 scalar-independent search; source `G,Q` are the only actual solver inputs. The planted k is generated for the public test and used **after** the solve.

Fixed p=2147483033; q=536857417 prime; source E: y²=x³+622683939x²+2147483024x, G=(911976709,415929193); target T: y²=x³+9x, H=(180482573,1535800095). The public degree-2 isogeny, j/CM constants and q-preservation are checked. Every BSGS starts a 23,171-point baby table; each rho starts 32 fresh jump classes. Each of two separate seed-panel processes (20261118, 20261119) uses 24 public targets, alternating ABCCBA/CBAABC order, two observations per arm. Thus 48 target logs, 288 actual cold solver invocations, all independently checked against original G. No arbitrary fixture exclusion.

| Per-process observation | Seed 20261118 | Seed 20261119 |
|---|---:|---:|
| Source BSGS total ns | 3,755,542,803 | 4,826,781,978 |
| Source neg-rho total ns | 3,509,130,458 | 4,554,979,378 |
| Transferred GLV-rho total ns | 3,062,623,084 | 3,981,520,751 |
| BSGS / transferred clock ratio | 1.22625 | 1.21230 |
| Neg-rho / transferred clock ratio | 1.14579 | 1.14403 |
| **Best total of two source arms / transferred total** | **1.14579** | **1.14403** |
| Source BSGS / source neg / GLV group additions | 1,687,488 / 1,103,674 / 802,038 | 1,816,780 / 1,146,114 / 897,484 |
| Median per-target A/A spread, BSGS/neg/GLV | 1.0524 / 1.0685 / 1.0811 | 1.0843 / 1.1147 / 1.0991 |
| Whole mixed-process peak RSS (KiB) | 24,500 | 20,912 |

**Result:** This toy transfer is faster than either tested source method in *both* observed processes. It is **not** a complete, independently verified ECDLP speedup: only two interpreted source algorithms, not strongest native rho, optimized BSGS or IC; one specially selected CM/isogeny curve, no native full-Jacobian transfer and no cold curve-discovery/setup/LA cost. Whole-process RSS is not arm-separated, and map inversions are charged in elapsed time but not all in the `Curve.ops` field counters. A/A noise is nontrivial; no confidence interval or host-isolation claim. The ~1.14x margin may vanish on optimized source arithmetic or a source-side transported-endo control. Do not merge historical ratio improvements from different runs.

## Audited raw files and scope

An independently written validator implements separate finite-field group arithmetic, Miller–Rabin primality and Hasse tests, subgroup/isogeny/GLV identities, reconstructs all 48 public source points and their images, checks all 288 scalar outputs, all schedules, the 23,171-entry fresh BSGS tables and deterministic within-arm operation counters. Both `python3 -S` and `python3 -O -S` produced byte-identical audit summaries, rejecting **14** synthetic corruptions. This is an **arithmetic/schema self-audit**, not independent timestamp, native timing or signed PCC evidence.

- Seed 20261118 full JSON SHA256: `50c6c10a231556510281acbdcd8e2175d89101cdc287ec4a0d5661f4ce2feb04`
- Seed 20261119 full JSON SHA256: `d2ef0e952569716d0786b8451a213cabb58f9ed62613cd090cb77a9beecc3f53`
- Both-mode audit JSON SHA256: `b90f8b254d3980821724b1ceb522056590b74bc557a5fd7043633a1a94c1508b`

The full raw JSON files are retained in this turn's downloadable local evidence archive, **not** signed or uploaded to the repository's PCC/object custody. Do not promote producer hash strings to attested evidence. Both committed scripts match the locally executed bytes by exact Git blob SHA `277d0ea2d32358a9cc77bd4f58700e5cc0cd81d7` (experiment) and `3b429c1ee9e8b0051365a98aac0a06e47ee61f70` (auditor).

### Reproduce

```sh
cd experiments/chained-transfer-public-target/ct130-prime31
python3 -S ct132_three_arm.py 20261118 > ct132_20261118.json
python3 -S ct132_three_arm.py 20261119 > ct132_20261119.json
python3 -S ct132_validate.py ct132_20261118.json ct132_20261119.json
python3 -O -S ct132_validate.py ct132_20261118.json ct132_20261119.json
```

The next discrimination is a **fresh independent same-host native** optimized source rho/BSGS/IC comparison, plus source-side transferred-endomorphism controls and complete 701-record Jacobian admission/correction, C169/C13a/C13b/D, full setup/verification/memory and signed PCC. Those native tasks are already tracked on concurrent #1534/#1523/#3877 and are not duplicated here. No paid EKS/Spot/pod launch or protected merge.

Prior work: [crypto root #3877](https://github.com/isogeny-labs/crypto/pull/3877), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [#1534](https://github.com/isogeny-labs/cryptanalysis/pull/1534), [#1537](https://github.com/isogeny-labs/cryptanalysis/pull/1537), [#1539](https://github.com/isogeny-labs/cryptanalysis/pull/1539), [#1540](https://github.com/isogeny-labs/cryptanalysis/pull/1540), [GPU IC #4178](https://github.com/isogeny-labs/crypto/pull/4178), [GLV 2001](https://www.iacr.org/archive/crypto2001/21390189.pdf), [rho automorphism-cycle study](https://eprint.iacr.org/2011/008.pdf). Research-KB MCP and checkout-local fallback unavailable here; no novelty/absence claim.
