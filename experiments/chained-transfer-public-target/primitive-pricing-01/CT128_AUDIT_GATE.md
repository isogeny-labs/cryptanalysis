# CT128 — pricing audit rejection integrity [pcc:unverified]

## Exact defect and reproduction (2026-11-15)

The original CT126 `check_pair.py` (Git blob `a1c2fe6ae04a1e6ba1bcf6eb9243dc02e71b7561`, SHA-256 `ae12cde1960b64213e2aca589a288b1e14683d7dedd9da8b03df6a5e59d88c48`) used `assert` for *all* input validation, ABBA sequence checks and equality of public outputs. Python `-O` deletes these statements. A local synthetic ABBA fixture with an altered `reuse-1.identity_checks[0].output_public` was rejected with exit 1 under `python3 -S` but **accepted with exit 0** and produced `diagnostic.json` under `python3 -O -S`. No real solver measurement was affected or examined; this is a producer-local reproducible defect demonstration, not independent PCC validation.

## Source repair

The CT128 replacement uses an explicit `InvalidEvidence` exception and `require` guard, independent of Python optimization. It checks source/group constants, schema, original/reuse identity, exact fixed scalar ordering, positive integer block samples, setup and Linux VmHWM, all six measured operation labels, exact ABBA input order, and unambiguous warm-only scope. It rejects constant-key substitution and adds SHA-256 provenance for the four input JSON blobs and host receipt to the output report. None of these hashes independently verifies a GPU/CPU execution or the correctness of an EC discrete log.

The unchanged diagnostic per-operation median, bootstrap and A/A formulas still describe **warm primitives only**, not complete cold ECDLP. Source-case validation is not proof of public-key arithmetic; an independent verifier must actually check all source logs.

## Local bounded replay

```sh
python3 -m py_compile experiments/chained-transfer-public-target/primitive-pricing-01/check_pair.py
python3 -S experiments/chained-transfer-public-target/primitive-pricing-01/check_pair.py --self-test
python3 -O -S experiments/chained-transfer-public-target/primitive-pricing-01/check_pair.py --self-test
```

Both interpreters passed the positive self-test and rejected the same eight deliberate input mutations: changed public output, missing block, negative time, schema substitution, missing memory, wrong scalar, constant public outputs, and false cold-EC-DLP scope. A separately constructed local ABBA directory with five synthetic known scalars was accepted under both modes. When one actual JSON output key was modified, both modes exited nonzero with `InvalidEvidence: public output mismatch across ABBA arms`. Byte-identical report output was observed between the two modes on this synthetic valid case. Exact committed-byte CI and independent PCC are separate gates.

## Prior evidence and scope

Read repo `AGENTS.md`, crypto root [#3877](https://github.com/isogeny-labs/crypto/pull/3877), crypto cost frontier [#4215](https://github.com/isogeny-labs/crypto/pull/4215), cryptanalysis [#1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [#1533](https://github.com/isogeny-labs/cryptanalysis/pull/1533), [#1534](https://github.com/isogeny-labs/cryptanalysis/pull/1534) and GPU IC [#4178](https://github.com/isogeny-labs/crypto/pull/4178). The full research-KB MCP and checkout-local wrapper, Conductor, full Rust checkout and Rust toolchain were not available in this session. No new algebraic novelty is claimed.

## Next executable cost gate

1. Confirm actual CT125 compiled derivation and complete 695-record parity at the exact benchmark source revision (including 672 exceptional classes and the original whole-record omission controls).
2. Run CT126 ABBA pair using approved same-host resources; save raw JSON, stderr, host/toolchain and build source hashes, check the exact head with both Python modes, and price C169, C13-first, C13-second, D and both warm routes. Do not interpret these timings as a cold ECDLP win.
3. Implement and measure a separate complete **single-target** source-to-target-DLP benchmark: include fresh setup, public encoding/admission, norm corrections, transfers, all target solving and linear algebra, verification, peak memory and a matched optimized rho/BSGS/IC baseline on identical public logs; repeat and independently reproduce. The existing native population and static 48-counter frontier cannot substitute for this.
4. If the complete, uncertainty-qualified cost ratio baseline/candidate is not greater than 1, record the loss and prioritize the next benchmarkable lead.

No paid compute launched, no protected merge, no claimed ECDLP speedup. Scientific standing remains **[pcc:unverified]**.
