# CT322 — Bounded live cold BSGS control on the exact ordinary prime31 source (2026-11-22)

**Status:** prospective protocol committed before implementation; [pcc:unverified]. This adds a genuinely executed, self-contained Rust *reference* solver to the existing CT321 challenge system. It is **not** the transferred candidate, not the fastest verified BSGS, and not an admitted seven-arm CT315 comparison.

## Prior evidence and nonduplication

Read crypto #3877, #4215, #4178, cryptanalysis #1523, existing draft #1920 CT315–CT321, crypto's `research/prime31_ic_20261115/native/README.md` and CT304 source-parity/access problem. Crypto #4188 and #4715 already measured separate index-calculus/BSGS controls, with the F103 norm collector materially slower; they are not superseded by this source-only control. Existing CT321 tested four toy F97 public challenges against entirely fabricated full-panel timing, so it has not run a live full prime31 DLP. The shared KB tool was not available; absence/novelty claims are prohibited.

## Exact immutable source parameters

- `p=2147483647` (2^31-1).
- `E: y^2=x^3+847514846*x+2087444724`.
- Full prime group order `n=2147446831`; `G=(625037715,2100627251)`.
- These values are copied from the *existing* crypto prime31 fixture, not a deliberately weak or new curve. Primality, nonsingularity, G membership and `[n]G=O` are checked before live runs.
- Four unique nonzero, CSPRNG-selected `Q=[k]G` with CT321 public commitments; scalars/salts only in the private `0600` reveal file, never in solver argv/environment/stdin.

## Scope and prospective execution gate

1. New bounded std-only Rust executable `ct322_prime31_bsgs.rs` accepts **only public** `p,a,b,n,Gx,Gy,Qx,Qy` and solves the complete target via ordinary Shanks baby-step/giant-step on E(Fp), with no target scalar, transfer, index calculus or cached precomputation. Validate all public parameters; use at most `ceil(sqrt(n))` baby records and `ceil(n/m)` giant trials; verify `[k]G=Q` independently of hash lookup before success. Report counters, `k`, elapsed in-child nanoseconds. No purported asymptotic gain: O(sqrt(n)) time/memory.
2. Issue four fresh CT321 challenges in a private temporary location. Invoke the compiled executable **once per Q as a new child process** with only public point/curve integers, sterile environment and fixed CPU affinity. Enforce 20-second wall timeout per child and RSS cap 256 MiB. Record external monotonic wall ns, child-specific Linux `wait4` maxrss, exit code, exact argv, native binary SHA-256 and raw output digests. Treat nonzero/timeout/bad JSON/RSS overflow as a refusal. Do not launch cloud/EKS/Spot/S3 or request credentials.
3. Only after all four child processes exit, parse the private CT321 reveal and compare recovered scalars against the commitments and CT317 independently recomputed source-group equations. No solver receives an expected scalar from a CT315 panel. Strictly reject altered answers and wrong challenge binding. Keep a transcript summary with only counts, hashes, measured aggregate and process counters, not secret salts or target scalars.
4. Add toy F97 known-answer native positive and altered target/invalid subgroup/invalid curve negative controls. Add source-only no-reveal metadata assertions and a sabotage test against changed recovered output. Run actual native p31 cold trials in GitHub Actions with pinned exact PR head in both normal Python and `-O`; compilation uses `rustc --edition=2021 -O`. Limit CI job to 4 minutes. No source-output based fake timing is accepted as physical execution.
5. **Caveats:** The parent still has read access to the secret manifest and controls the solver binary, so independent blindness, external execution attestation and challenge timestamp escrow are not established. A single GHA host and this new Rust BSGS are not calibrated references for the strongest frontier. No CT315 candidate/retained/rho/IC run, physical `C169,C13a,C13b,D,N2_actual`, original 695/701 fixture, or signed PCC can be inferred. Report only observed source-CI execution with explicitly scoped producer-reported measurements and no speedup.

## Pass / failure / next gate

Pass only if all four fresh exact-prime31 DLPs recover scalars after the child process exit with positive measured wall and per-process RSS, exact binary+stdout receipts, bound challenge public hashes and successful Rust native/independent Python cross-check. A negative outcome is retained without relabelling it a speedup. Future stronger comparison still requires original six-object artifact-tool/config selection, authorized STS/S3 custody, native C169/C13/D replay and matched same-host cold complete candidate versus optimized rho/BSGS/frontier IC with all setup/transfer/LA/recovery/memory and independent PCC.

[pcc:unverified]
