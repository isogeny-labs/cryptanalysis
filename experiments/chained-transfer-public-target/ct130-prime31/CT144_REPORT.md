# CT144 — Projective source BSGS cold control (15 November 2026)

**Standing:** [pcc:unverified]. Original root: isogeny-labs/crypto#3877; predecessor cryptanalysis#1552; separate native original-prime primitive pricing cryptanalysis#1562.

## Protocol and scope

The CT144_PROJECTIVE_BSGS_PROTOCOL.md was committed at ebcc7b50ca53b295b0eb064e974fe296dc3c5628 **before** source implementation or measurements. The identical 31-bit CM-neighbor source/target, CT140 four seeds (20261340–43) and 128 source public targets were frozen in CT144_FROZEN_TARGETS.csv (SHA-256 ea17d4ae6d39bbc61f834d50967cceae37f69fdf04806bfd80ff2750c439a7e3). ct144_source_check.py pins the unchanged CT135/CT136 sources, source C++ and mathematically generated batch4/batch16 implementations. No original-prime Jac source, protected fixture or ledger changed. [pcc:unverified]

## Mathematical and implementation check

The source curve has non-short Weierstrass form y²=x³+a*x²+b*x. Our Jacobian mixed-add X3 includes -a*H²*Z², and doubling X3 includes -a*(2YZ)². The new source BSGS constructs a projective baby-point table per cold target; one Montgomery batch inversion normalizes it. It computes projective giants and normalizes in 256-point chunks. The previous affine reference and source batch4 rho and mapped batch16 GLV rho remain named controls; scalar verification is inside each timed arm. An independent Python arithmetic verifier recomputed every recovered source logarithm and the mapped target identities without importing the C++ arithmetic, normal and python -O outputs agreed, and seven altered-evidence controls rejected. This auditor was written in the same research session, and its checks are not independently signed PCC. [pcc:unverified]

## Local results, complete bounded toy solves

Two separate bounded local process repetitions × four fixed cohorts × 32 public targets × four cold arms × two interleaved repeats = **2,048 complete and arithmetic-checked scalar recoveries**. Eight processes exited zero with empty stderr; 120s and 2GiB per-process limits. GCC 14.2.0 -O3 -DNDEBUG on virtual AMD EPYC 9V74 with five visible CPUs (not physical-host independent). Total per-target *inner* time over the fixed cohort:

| Complete named arm | Inner time ns |
|---|---:|
| Source affine BSGS | 2,049,861,736 |
| Source projective/batched BSGS | 1,821,166,407 |
| Source batch-4 Pollard rho | **1,170,313,405** |
| Transferred target batch-16 GLV rho | **945,954,852** |

Source projective BSGS is 1.126× faster than the **affine BSGS stage** but remains considerably slower than the tested source rho. Best fixed tested source solver / mapped solver = **1.2371768×**, descriptive paired-bootstrap 95% interval **1.0979–1.3821×**; peak process RSS 6,220 KiB. These are one developer environment's per-arm inner times, not matched whole-process cold costs. Standalone process elapsed totals 6.0 s over eight jobs; their startup/preflight cannot be attributed per arm. [pcc:unverified]

## Reproducibility

Full local raw archive (separate from Git): CT144 local bundle sha256 cca03d645dbf68fff0f3ca712adbcd96e4a49ec76a82c3edfc8afd41edcc8bb9. It contains the C++ source, original CT135/136 source, full build_ct144.py generator, the 128-point manifest, all eight CSV process outputs, external process resource receipts, Python verifier, local report, and raw CT140 previous records. Verify checksums using MANIFEST.sha256 inside the archive. Run python3 -S ct144_source_check.py, compile g++ -std=c++17 -O3 -DNDEBUG ct144_projective_bsgs.cpp -o ct144_bsgs, run ./ct144_bsgs 32 <one-of-the-four-seeds> with bounded resources, and audit complete archive with python3 -S ct144_verify.py . and python3 -O -S ct144_verify.py .; outputs must match. The GitHub branch holds source, controls, frozen manifest and report, **not** the local raw timing records. Source-only CI is not a hosted scientific performance reproduction. [pcc:unverified]

## Negative outcome, limitations, next gate

**Negative for projective BSGS as a stronger source baseline:** projective batch normalization helps BSGS but does not beat matched source rho. CT140's toy mapped-rho advantage survives this specific additional control but is not a generalized or original-prime complete ECDLP speedup. The original q223 native C169/C13_first/C13_second/D ABBA pricing is still owner-secret admission-gated and unexecuted, with 695/701 original-prime Jacobian completeness, full setup, transfer, linear algebra, strongest independently matched rho/BSGS/IC, peak memory, uncertainty, and independent signed PCC unestablished. No paid compute or protected merge occurred. [pcc:unverified]
