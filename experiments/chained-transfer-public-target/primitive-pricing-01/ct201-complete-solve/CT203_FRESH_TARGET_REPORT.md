# CT203 — distinct-target hardcoding confound and source-only correction

2026-11-18 UTC. **[pcc:unverified]**. Tracked in draft [cryptanalysis #1766](https://github.com/isogeny-labs/cryptanalysis/pull/1766).

## New finding

The existing [CT201](PROTOCOL.md) and [CT202](CT202_ORDER_BINDING_PROTOCOL.md) source validators accept exactly the **same** public Q in every matched block. Therefore a candidate that returns a hard-coded valid scalar for that one Q could pass their independent group-law correctness checks; order balancing and identical rho-sham binary digests do not resolve that generalization confound. This is a mathematical property of the prior input schema, not evidence that any genuine solver cached a logarithm. It does **not** invalidate the correctly limited source-only CT201/CT202 claims.

The new [prospectively frozen protocol](CT203_FRESH_TARGET_PROTOCOL.md) was committed at `16c606efef9f8e0440f7e7c60070ed87077b05f8` **before** the new checker or test fixture. CT203's [separate adjudicator](ct203_fresh_target_gate.py) requires ten or more different public Q values (no repetition even up to sign), while each matched five-arm block solves **one** shared Q. It verifies [k]G=Q independently for every block; recomputes each block-specific input digest; retains chronological ten-block Williams balance, one binary SHA per arm, rho/sham equality, one declared host, fresh-process declarations, full external wall, per-phase accounting and memory caps. It computes the matched fastest of rho/BSGS/IC per block and the same explicitly diagnostic geometric-mean/bootstrap/A/A score. It rejects a constant scalar for distinct target points.

A distinct-target roster **is not itself blind**. Target provenance, executable freeze before external target choice, absence of hidden scalar leakage, and execution receipts must be independently attested by a signed verifier; the source checksum is self-reported and not authentication. CT203 does not modify the frozen CT201/CT202 protocols or re-adjudicate earlier evidence.

## Exact reproduction and scope

Commits:
- protocol `16c606efef9f8e0440f7e7c60070ed87077b05f8`
- checker `5fa9e6fe25139fc24949b82da4aa895084b673fd`
- test suite `36807d152a23371cce34523c6ae895f3ac8edd8a`

```bash
D=experiments/chained-transfer-public-target/primitive-pricing-01/ct201-complete-solve
python3 -S -m unittest discover -s "$D" -p 'test_ct20*_*.py' -v
python3 -O -S -m unittest discover -s "$D" -p 'test_ct20*_*.py' -v
python3 "$D/ct203_fresh_target_gate.py" /path/to/real-prospective-evidence.json
```

[Exact-source CI run #44270456433](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44270456433) completed successfully for commit `36807d15`. Decoded `source-contract` job #134685459250 reports **44/44 normal and 44/44 optimized tests passed**. These include 16 CT203 tests: ten different true toy points over E(F97) with r=97, a programmed 1.5 synthetic-only ratio, slow negative, a constant-scalar falsifier, duplicated/negated targets, corrupted target/input hashes, incomplete or reordered schedule, executable drift and sham substitution, wrong logarithm, memory/phase overflow, false primes, coldness/Boolean invalidity and two complete cycles.

**The 1.5 synthetic number is not a measured ECDLP performance ratio.** No Rust executable, Jacobian fixture, native benchmark or external verifier was involved. The test suite's implementation is a producer-authored source check, not independent PCC.

## Next decisive work

1. Recover authenticated original-model access; CT200 [native typecheck run #44247758448](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44247758448) previously stopped at original S3 HeadObject HTTP 403 *before* compilation. Do not substitute a model or bypass the storage policy.
2. Native Rust all-48 CT125/CT192 parity with authenticated 695/701 fixture and same-host `C169,C13a,C13b,N2_actual,D` measurement; compare direct-vs-retained without double-counting norm reuse.
3. Freeze real independently chosen unseen target roster **after** binary/source pinning, then perform complete cold one-target-per-process transfer/rho/BSGS/IC on identical points within each balanced block. Preserve raw external times and memory, startup/teardown, setup/transfer/relations/LA/descent/recovery/verification, A/A controls, source/candidate hashes, uncertainty and signed independent PCC.
4. If measured candidate is slower than the strongest matched baseline, record the negative result and switch to the next registered lead, rather than promoting this source-only gate.

Sources checked: merged [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [GPU IC #4178](https://github.com/isogeny-labs/crypto/pull/4178), [CT198 #1748](https://github.com/isogeny-labs/cryptanalysis/pull/1748), [CT199 #1756](https://github.com/isogeny-labs/cryptanalysis/pull/1756), [CT200 #1761](https://github.com/isogeny-labs/cryptanalysis/pull/1761), current PR head, cryptanalysis AGENTS and the 2026-11-18 session log. Repo code search found earlier fresh-roster material in CT179/CT186; this change is scoped to the separate CT201 full-cold-varying-Q schema, not asserted novel cryptanalysis. Research-KB and plaintext autoresearcher contract not available through this connector session; no absence claim.

**Standing: [pcc:unverified]. No paid compute, protected merge, original data rehydration, native timing, or complete verified ECDLP advantage.**
