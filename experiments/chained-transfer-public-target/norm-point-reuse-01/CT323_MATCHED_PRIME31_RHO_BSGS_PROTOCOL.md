# CT323 — Preregistered bounded same-host prime31 BSGS vs negation-quotient rho control
Date: 2026-11-22 (America/Denver). Standing: [pcc:unverified].

## Parent, evidence, prior art, and nonduplication
- Parent #1920 and CT322 real cold public-only BSGS, plus merged crypto #3877, #4215, GPU IC #4178 and cryptanalysis #1523 were read first.
- The frozen Jacobian 695/701-record original replay and physical C169, C13a, C13b, D, N2_actual remain blocked on owner-approved coherent historical artifact tool/config, authorized STS and six-object S3 custody. This experiment does **not** substitute for those.
- Bernstein–Lange–Schwabe, *On the correct use of the negation map in the Pollard rho method*, ePrint 2011/003, https://eprint.iacr.org/2011/003: naive negation-map additive walks have fruitless 2-cycles; restart and bound such walks. The initial affine solver here is a control, **not** the fully optimized branchless/batched-inversion method from that paper.
- No duplicate alternate producer branch, no reimplementation of the 695-model evaluator, no cloud, EKS, Spot, S3, secrets or protected merge.

## Frozen exact source problem
- Use CT322's existing p=2147483647, E: y^2=x^3+847514846x+2087444724, prime n=2147446831, G=(625037715,2100627251).
- Use the unchanged CT321 CSPRNG generator to issue four distinct public Q=[k]G, four private salted commitments and a 0600 private reveal file. Open private reveal only after all timed children exit.
- Compile the existing CT322 Rust BSGS executable and a separate new std-only Rust rho executable, both `rustc --edition=2021 -C opt-level=3 -C debuginfo=0`, in the same exact-head GitHub Actions job.
- For each Q execute four fresh children on the same pinned CPU, ABBA by pair (BSGS/RHO/RHO/BSGS for even block, RHO/BSGS/BSGS/RHO for odd block), pristine cwd each, sterile environment, no scalar argv/stdin/env, 20 s per child, Linux wait4 RSS, 256 MiB cap.
- Meter monotonic external child wall, CPU affinity, exact argv/binary/stdout/stderr SHA256, wait4 RSS, claimed native field/group counters. Verify each native k against independently recomputed Q=[k]G and post-exit private reveal. Preserve every failure with status and stderr digest; do not treat a fail or timeout as a fast observation. CI should reject tampered response and invalid subgroup/curve.
- Fixed internal rho scheme: deterministic **public-only** seeded additive partition jumps over negation classes, 32 jumps, canonical y=min(y,p-y), coherent signed coefficients a,b, distinguished-point table, bounded 8192-step walker restarts and cap at 64*ceil(sqrt(n)) total steps and 65536 stored distinguished points; no fallback to BSGS on failure. Record restarts, walk steps, distinguished entries, affine additions, inversions. Independently verify k and reject zero denominator and false collisions.
- Across four blocks record per-Q duplicate run consistency, median external wall per arm and RSS, and all receipts. Do not attribute differences to algorithmic superiority without repeated independent host runs with uncertainty, optimized rho/BSGS/IC parity and all-phase cold costing.

## Controls and admission
1. Native toy p=97 curve y²=x³+2x+3, n=5, G=(3,6), Q=(80,10), logarithm 2; normal/optimized Python replay through fixed Rust binary. Explicit invalid curve, off-curve Q, composite n and changed output are refused. Additional Prime31 four Q/arm 4x trial.
2. Run 4 ABBA blocks, total 16 native processes; all 16 source-target logs must check, plus challenge commit/reveal. Include both native solver hashes, per-child stdout/argv/host+CPU, wall/RSS, and native operation counters in stdout JSON. A/A repeat is an internal stability diagnostic.
3. Exact-head GHA source workflow runs normal and `python3 -O` source assertions and at most one 16-child panel within the 4-minute CI job. Report what was actually run and failures.
4. Negative outcomes, restarts, censored timeouts or missing memory cannot be dropped. This is **not** CT315 seven-arm cold admission, independently escrowed blindness, externally signed execution, original model work, or an ECDLP transfer win. No PCC signature inferred from own checks.

## Next decisive gate
Authorized original six-object S3 custody and coherent exact artifact tool/config revision; original 695/701 native parity; physical C169/C13a/C13b/D/N2_actual; then same-host full cold retained-lift/candidate/strongest rho/BSGS/frontier IC with setup, transfer, precomputation, relations, LA, recovery, verification, memory, uncertainty, signed independent PCC. [pcc:unverified]
