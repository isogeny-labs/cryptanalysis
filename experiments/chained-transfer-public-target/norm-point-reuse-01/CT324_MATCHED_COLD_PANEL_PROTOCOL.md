# CT324-B — matched cold native batched-rho comparison (prospective)

Standing: [pcc:unverified]. Frozen before comparative execution. Existing draft PR #1920. No original Jacobian or complete transfer claim.

## Exact source and arms
Use the identical original ordinary CT322 source E/Fp at p=2147483647, a=847514846, b=2087444724, subgroup prime 2147446831, G=(625037715,2100627251). Three native release-compiled public-only arms in one exact-head Actions job:
- unchanged CT322 native BSGS;
- unchanged CT323 single-walker affine distinguished-point rho;
- CT324 16-lane Montgomery-batched affine distinguished-point rho.

All built with rustc --edition=2021 -C opt-level=3 -C debuginfo=0. Check source and executable SHA-256. No target scalar supplied to children.

## Prospective fixed experiment
CT321 issues exactly four independently sampled distinct public targets Q=[k]G, with salted commitment and private reveal held until all children finish. For each Q run six fresh native processes, two per arm, with order BSGS/CT323/CT324/CT324/CT323/BSGS for even blocks; reverse order for odd blocks. One CPU affinity, same runner and executable versions. No dropping failed, censored or incorrect attempts. Preserve each child exit, raw stdout/stderr SHA-256, argv SHA-256, external monotonic wall nanoseconds, peak RSS, native counters and source/Q id. 20 seconds each, 256 MiB memory cap.

The only qualified result of this run is component-and-full-native-rho control timing on one 31-bit curve; it is not the complete original 695/701 norm-reuse ECDLP solver, strongest optimized rho, an independently signed claim, or a growing-size bound.

## Validation
Reject invalid schema, group equation, missing counter, wrong revealed scalar, same-target mismatch, changed CPU, wrong arm order, missing RSS/wall, or any process failure. Independently re-evaluate each Q=[k]G using the existing source-group auditor and check CT321 commitments after processes exit. Run fresh-source toy positive and corruption controls.

## Decision
If CT324 loses against CT323 on complete cold child wall, record negative and do not promote. If it wins on this setup, report only its bounded native control advantage and retain matched optimized branchless/batched-inversion rho, BSGS, index calculus, original Jacobian model, all setup phases, memory, uncertainty and external PCC as separate gates. No unapproved EKS/Spot, S3, model substitution, protected merge or speedup publication.
