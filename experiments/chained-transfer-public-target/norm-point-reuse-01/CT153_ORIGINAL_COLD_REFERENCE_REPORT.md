# CT153 — real original-q223 cold public-target DLP reference: source BSGS versus ordinary three-way rho

16 November 2026 UTC. Root: [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877). Branch/PR: [cryptanalysis #1589](https://github.com/isogeny-labs/cryptanalysis/pull/1589). Standing: **[pcc:unverified]**. This is a source-only *complete logarithm recovery* correctness and exploratory timing control, NOT the Jacobian norm-reuse candidate or a complete transferred solver. Protocol [CT153_ORIGINAL_COLD_REFERENCE_PROTOCOL.md](CT153_ORIGINAL_COLD_REFERENCE_PROTOCOL.md) was committed as `682c9a0` before this implementation and its final measured replay.

## New implementation, scope and identities

An independent C++17 implementation performs native full group operations on `E/K`, `K=F223[z]/(z³-3)`; `E:y²=x³+a2x²+a4x+a6`, with `a2=(127,56,199)`, `a4=(152,35,36)`, `a6=(212,109,150)`, `G=((162,197,140),(45,11,207))`, prime subgroup order `ell=2773073` and CT152-checked total `4ell=11092292`. The six deterministic known-scalar fixture Qs are generated outside either solver and passed to the solvers only as public curve points. The source-only algorithms are (A) fresh-table BSGS and (B) a *nonoptimized* deterministic three-partition restarted Pollard rho (Floyd collision and full mod-ell logarithm recovery), with hard bounds of 12 restarts × 50,000 iterations. Both require complete recovery and source-group verification, not matching a selected intermediate component.

The independent Python verifier reimplements `F223³` arithmetic and group law without sharing C++ arithmetic, independently recomputes Q and [recovered]G, verifies order and receipts for all completed executions, and confirms no fixture scalar passes into the source solver function. The C++ complete-solver tests reject mutated `a6`, off-curve points, wrong subgroup order and on-curve Q outside the ell subgroup; CLI controls reject five invalid inputs. **Nine deliberate negative controls passed.** This is a finite explicit original cubic-extension curve; it does not establish an arbitrary `F_p` ECDLP source or any map into the destination Jacobian.

## Exact committed-source developer replay (not independent PCC)

Built with `g++ -std=c++17 -O3 -Wall -Wextra -Werror` on `Linux-6.18.57-x86_64-with-glibc2.41`; non-isolated developer CPU, 6 public targets, 4 alternating ABBA/BAAB blocks each, 4 *fresh OS processes* per block: **96/96 answers recovered and independently verified** (48 BSGS, 48 rho). Each process includes only its source-curve arithmetic and solver; harness wall includes process launch but not the harness's independent postcheck. No public target from the actual Jacobian transfer has been solved in this cohort.

| Measured diagnostic (96 total executions) | Fresh BSGS | Three-way rho |
|---|---:|---:|
| Median process-spawn wall time | 2.471 ms | 3.753 ms |
| Median solver-only time | 0.635 ms | 2.084 ms |
| Median field inversions within solver | 1,804.5 | 6,389.5 |
| Maximum Linux current-process `VmHWM` | 1,776 KiB | 1,692 KiB |

**Paired median (BSGS minus rho)** = **−1.473 ms** over the 24 frozen ABBA/BAAB blocks. Fixed-case 4,000-resample block bootstrap 95% interval = **[−2.441 ms, +0.035 ms]**; **the interval includes zero**. Median within-arm A/A absolute process-wall difference = **0.270 ms**. This is an exploratory fixed-fixture bootstrap, not population confidence; scheduler noise, A/A drift and process-overhead effects preclude a robust faster-algorithm claim. Nevertheless both algorithms completed every source logarithm with explicit public-output checks. Raw output has 96 records; `rows_sha256=773ad483087f9630c23f58449ce7268d333af365e25896d72cd9b0a9420a3fc7`. C++ binary SHA256 `bc2339635b3fdba4a6b2edf697be7ef2bdab127dfec1f19645699050652e3a60`. Original C++ Git blob `d814a99e9d98b66d37ba1ceeefbd4e819d7b68a8`; independent Python verifier blob `34cc4e00a0df401e241980c642f70c819b061df7`. These blob IDs matched GitHub readback. No speedup ratio over a *transferred* complete solver can be computed because no transferred solve was run.

A preliminary developer replay mistakenly attributed `getrusage` under an inherited process accounting context to C++ child memory; corrected to direct Linux child `/proc/self/status:VmHWM` **before this final replay**, preserving older diagnostic as superseded. The final source also rejects noncanonical coordinate values and has explicit whole-source membership controls. Do not treat preliminary raw timing as primary acceptance evidence.

## Reproduce, local bounded CPU only

```sh
D=experiments/chained-transfer-public-target/norm-point-reuse-01
g++ -std=c++17 -O3 -Wall -Wextra -Werror "$D/ct153_original_cold_reference.cpp" -o /tmp/ct153-original
/tmp/ct153-original --self-test-negative
python3 "$D/ct153_reference_audit.py" /tmp/ct153-original --quick
python3 "$D/ct153_reference_audit.py" /tmp/ct153-original --output /tmp/ct153-raw.json
```

Small bounded source-only GitHub CI executes only `--quick` and 9 negative controls, not a scientific speedup benchmark. Hosted exact-head execution must be separately inspected. Full raw local capture (including transient wall clocks) is not a code-derived invariant and is not claimed to be signed or uploaded to S3 by GitHub CI.

## Negative standing and decisive follow-up

The CT153 result **does not** price `C169`, `C13a`, `C13b`, `D`, verify the frozen 695/701 original/reuse norm-point parity independently, run genuine `E(F223³)`→Jacobian cold target solve, measure cold IC or a tuned negation-map rho, count actual setup/transfer/LA/verification/memory, or satisfy independent PCC. Its independent-source benchmark may be useful as a cheap correctness and performance control only. The existing CT129 cold-BSGS screen #1537 is *nu12* and source-isogeny only, so it is not substituted for this original-source cohort.

Next unblocked work after this source reference: independently bind and replay the already producer-reported whole-695 norm-reuse evidence, then execute owner-admitted same-host paired **native** prices and same-input complete target solve versus strongest tuned rho/BSGS/IC, including full setup/cost/uncertainty. Do not rerun CT129 as if it were the original source. Any actual measured loss must be logged, not reinterpreted as an efficiency win. No EKS/Spot/GPU/paid job, protected merge, PCC ledger edit or frozen corpus change was made.

Sources checked: root crypto #3877, cryptanalysis #1589 CT152, #1537 CT129, #1562 primitive pricing, crypto #4215 / GPU IC #4178, and original repo `AGENTS.md`. Shared research-KB and checkout-local lead atlas unavailable here; no novelty or absence-of-prior-art claim. **[pcc:unverified]**


## Hosted exact-source CI and independent PCC observation (2026-11-16 UTC)

Hosted bounded [CT153 job #43814397691](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43814397691), job `133123018309`, **passed** after compiling the exact source from head `8d9f4f786fa0c35d010973a4284d2f5efd0b8f5d`. Decoded job log explicitly executes C++ `--self-test-negative`, the Python `--quick` eight-complete-solve cross-check, and checks 9 negative controls. Source SHA256 `a687e28dd543435af9b47a51fa52cc5ba227c9d1dbf97345aa3bbd0d89be988a`, Python SHA256 `041583961e2005689143ad64fb6b9b9a387f9cfd4b8f64e131ded923dd11e92d`. The hosted compiler's binary hash is naturally distinct from developer-local and is not used for cross-host timing. This verifies a **bounded 8-solve correctness subset**, not the separate local 96-solve timing or independent scientific PCC.

At final then-current PR head `fe03d5d9c3c9abdffbc8486d5983cd2888e5c2e7`, the [PCC gate #43814481786](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43814481786) **failed** on historical `not_covered` attestation population and a Lean kernel backend absent from PATH; its `sign` job was skipped. This failure remains outstanding and is not bypassed by CT153 source-only CI. Full-stack checks include other inherited failures. [pcc:unverified].
