# CT177 implementation and evidence — in-flight bounded cold-process capture

Date: 2026-11-17 UTC. Scientific standing: **[pcc:unverified]**. Tracking: [cryptanalysis #1706](https://github.com/isogeny-labs/cryptanalysis/pull/1706), parent [merged #1700](https://github.com/isogeny-labs/cryptanalysis/pull/1700), coordination [crypto #3904](https://github.com/isogeny-labs/crypto/issues/3904).

## Finding and correction

The merged CT176 collector's `subprocess.run(... capture_output=True)` reads the complete child stdout and stderr into memory **before** checking `MAX_CAPTURE=131072`. The post-hoc rejection cannot protect the collector's peak memory. This was identified by source inspection, not by an observed producer memory failure. CT177's [prospective protocol](CT177_BOUNDED_CAPTURE_PROTOCOL.md) was committed at `d2c557b8` before implementation.

The patched `ct176_cold_process_collector.py` now launches each child in its own POSIX process group, uses nonblocking stdout/stderr and a selector to drain both pipes concurrently, retains at most `MAX_CAPTURE+1` bytes per stream, and on overflow or deadline SIGKILLs and reaps the child process group. Captured prefixes, SHA-256 digests, base64, exit codes, monotonic external wall, timeout and error labels survive as explicit refusal evidence. The `capture_complete` field is true only after normal pipe EOF/drain, including nonzero child exits; overflow, timeout and failed spawn are marked incomplete. A bounded prefix is **not** presented as lossless complete stderr/stdout.

The original `verify_native` arithmetic/counter consistency checks, exact selected-48 Git blob, native executable admission, 2,304-process prospective roster, per-arm public input and 19-word target, and 21-field counter scheme are unchanged.

## Reproduction scope

The original bounded CI job `.github/workflows/ct172-native48-source.yml` already runs normal and `python -O` tests and the full immutable fixture plan. Five additional synthetic tests exercise >1 MiB floods on each pipe, mixed-pipe drainage, an intentionally sleeping child and nonzero exit with retained stderr. The updated timeout test must refuse `capture_complete`. No actual CT125 native executable is invoked.

On the intermediate code head `b577d8a`, GitHub Actions [source workflow run 44034921574](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44034921574) reported success and its job log showed **29/29** tests in *each* of normal and optimized Python (the previous suite contained 24 tests), including the five new tests. A subsequent correction tightened timeout capture completeness (`3562da1`, `8143785`); the final exact-head rerun must be inspected before classifying that correction as passing. All results are producer/hosted source tests, not independent signed PCC.

Safe reproduction on an authorized clone:

```sh
root=experiments/chained-transfer-public-target/primitive-pricing-01
fixture=experiments/chained-transfer-public-target/evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json
python3 -S -m py_compile "$root/ct176_cold_process_collector.py" "$root/test_ct176_cold_process_collector.py"
python3 -S -m unittest discover -s "$root" -p 'test_ct176_cold_process_collector.py' -v
python3 -O -S -m unittest discover -s "$root" -p 'test_ct176_cold_process_collector.py' -v
python3 -S "$root/ct176_cold_process_collector.py" --fixture "$fixture"
```

These tests neither typecheck the Rust replay harness nor measure source or target curve operations.

## Scientific dependencies, no inferred gain

The original 695/701 custody remains unauthenticated independently; CT172/175 Rust arithmetic has not been natively linked and run in this runtime, and no owner-admitted same-host `C169`, `C13a`, `C13b`, `N2_actual`, `D_padd` or complete cold prime-field rho/BSGS/IC/transfer solve has been performed. Full setup, source transfers, inverses, linear algebra, recovery, verification, RSS, CI/PCC and uncertainty all remain required. No paid EKS, Spot or GPU run or protected merge. Current inherited artifact/PCC failures are not waived. This change improves integrity of a measurement tool, not the ECDLP algorithm. [pcc:unverified]

## Checked sources and access boundaries

- cryptanalysis `AGENTS.md`, latest `docs/ACTIVE.md`, original CT175/176 collector, test suite, report, source workflow, protocol and live #1700/#1706 states.
- crypto original [#3877](https://github.com/isogeny-labs/crypto/pull/3877), queue [#3904](https://github.com/isogeny-labs/crypto/issues/3904), norm symbolic [#4215](https://github.com/isogeny-labs/crypto/pull/4215), Richelot [#4514](https://github.com/isogeny-labs/crypto/pull/4514); cryptanalysis earlier #1523 and #1692.
- Shared research-KB MCP unavailable in this runtime and crypto-autoresearcher `AGENTS.md` file fetch returned a non-UTF8 decode error; no novelty assertion. No authenticated fixture-archive materialization.
