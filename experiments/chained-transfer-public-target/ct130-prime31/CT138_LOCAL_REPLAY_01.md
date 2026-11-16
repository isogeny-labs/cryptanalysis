# CT138: no-cost local width-16/32/64 complete toy DLP replay (2026-11-15)

**Standing:** [pcc:unverified]. Exact experiment is the already prospectively frozen [CT138 protocol](CT138_PROTOCOL.md), on the existing [cryptanalysis PR #1550](https://github.com/isogeny-labs/cryptanalysis/pull/1550). This report does not modify CT135, CT136, protected 695/701 original-prime fixtures, or the CT138 source, verifier, and execution gate. This is one *developer-local* execution, not independent hosted replay or signed PCC.

## What executed and was audited

- Reconstructed historical `ct135_native.cpp` byte-identically (Git blob `4d94fc9163e86689a09c6d6685dd017c5c4c9698`) from earlier conversation evidence; reconstructed CT136 source byte-identically (Git blob `2d063737bae8262ef39d9af4a9df8b022ef2da60`; SHA-256 `20b0305d0b291602dd141a278c00459c47e78608f17e33bea6395a3106438921`). The locally copied CT138 generator/verifier and original independent CT136 verifier also match published Git blobs `0fac9ade980cf42b922a73c01661a9efac420352`, `7f953d04cab42c7300eadc62387bd5103393c4f8`, and SHA-256 `ce3a9e5af959ad5ec3a81ce78151587a099fa8f86029bc7fa059bf9a384abc2f`. [pcc:unverified]
- Compiled 16-, 32-, and 64-lane matched source/target native C++17 binaries with `g++ -O3 -std=c++17 -Wall -Wextra -Werror`. Generated-source SHA-256 values: `828c91d46c84538e585ad4922e7ae1b890531f0b9393ddaa97df0bcfc78d71a1` (16); `0e0c00c5a311adb769ac6773403e6d718bbe464cceaa866ecf5c0392e6c59eca` (32); `cba548819a9c9990a25ae73a8464b1d458ad2a096ef24c5147c48d2673bfca8d` (64). [pcc:unverified]
- Ran all twelve prospectively fixed 32-target width/seed processes in the exact 16/32/64; 32/64/16; 64/16/32; 64/32/16 order with `timeout 120` and process RSS receipts. Four frozen seeds 20261340–43, 128 distinct source targets across seeds, 10 complete cold solver executions per target per width = **3,840 independently arithmetic-audited toy DLP answers**. No missing rows or subprocess errors. [pcc:unverified]
- Original separately implemented CT136 Python verifier checked every public Q via MT19937-64 reconstruction, curve and 2-isogeny equalities, recovered scalar, all 10 duplicated cold arms, integer counters, source-group postverification, sums, and ratios. Exact CT138 auditor accepted both `python3 -S` and `python3 -O -S` with **byte-identical audit JSON**; 11 deliberate corruption controls rejected at each width (33) plus 3 invalid width-label mutations. Audit SHA-256 `99c89dfb7f3581e4dab75efe72bfd293088f641d69411473e0128c790b473517`. [pcc:unverified]

## Matched whole-cohort results

All values are sums of two *complete cold* executions per target, on the **same host**, with no per-target solver oracle; a ratio above 1 favors mapped CM rho over the *named* source alternatives. Timing is not extrapolated to the original-prime Jacobian. [pcc:unverified]

| Width | Best source total ns (batched rho) | Best target total ns (batched rho) | Source / target |
|---:|---:|---:|---:|
| 16 | 632,943,762 | 475,069,239 | **1.332319** |
| 32 | 672,154,765 | 517,612,642 | **1.298567** |
| 64 | 652,915,517 | 532,238,716 | **1.226734** |

The **prospectively fixed whole-cohort best-of-width ratio** is **1.332319**, selecting width **16** on both source and target. The paired-resampling descriptive 95% interval is [1.17581, 1.46937]; this is **not** a population confidence interval or signed PCC. Median duplicate-arm timing ratios are between 0.991 and 1.021 across the 15 arm/width combinations; process `VmHWM`-equivalent `/usr/bin/time` peak RSS is 7,428 KiB maximum. [pcc:unverified]

Host: developer-local Linux x86_64 container, AMD EPYC 9V74, Debian g++ 14.2.0, Python 3.13.5, cgroup 4-vCPU quota and 4 GiB memory cap. Each of the 12 processes finished in 0.88–1.10 wall seconds; subprocess time and inside-solver timer are separately retained. This is **not** a host isolation or dedicated CPU claim. No EKS/Spot/GPU/paid experiment was launched. [pcc:unverified]

## Raw-data custody and limits

Producer-local evidence is separately packaged for the conversation as `ct138_local_width_replay_20261115.zip` (SHA-256 `4fadd60f98c72b571dc1683bd030695a7527eafa19a508524e9fbcd96e2823fe`). It contains the five exact historical source/audit files, generated variants, all twelve raw CSVs, stderr/time receipts, exact execution order, compiler/host receipt, raw SHA256SUMS, and both identical audits. It is **not** yet hosted as a GitHub Actions artifact or placed in immutable project storage; hash declarations alone do not promote it to trusted PCC. [pcc:unverified]

Exact local reproducer after obtaining the existing repository source and preregistered files:

```bash
python3 -S ct138_generate.py generated
for width in 16 32 64; do
  g++ -O3 -std=c++17 -Wall -Wextra -Werror -I .      generated/ct138_width${width}.cpp -o width${width}
done
# Run width16/width32/width64 with count=32 and seeds 20261340..43
# in the exact rotating order declared in CT138_PROTOCOL.md; retain stdout and /usr/bin/time.
python3 -S ct138_verify.py results > audit.json
python3 -O -S ct138_verify.py results > audit-optimized.json
cmp audit.json audit-optimized.json
sha256sum -c raw-sha256.txt
```

Literature/prior work checked: existing CT135/CT136 source/protocol and [Bernstein et al., *On the correct use of the negation map*](https://eprint.iacr.org/2011/003.pdf); nothing here is asserted novel. Shared research-KB MCP/Conductor and full original-prime Rust checkout were unavailable in the local runtime. [pcc:unverified]

**Unresolved owner gate:** still no independent hosted CT138 replay or signed PCC; more importantly **no original-prime 695/701 warm and cold executable measurement**, no same-host `C169,C13a,C13b,D` norm-reuse pricing, strongest original-source rho/BSGS/IC, setup/linear algebra, and peak memory comparison. The #1523 known-prepared-source-G negative result continues to apply. Do not merge or promote this toy timing into a complete original-prime ECDLP speedup. [pcc:unverified]
