# CT179 — offline cold-transfer panel adjudication

Date: 2026-11-17 UTC. **[pcc:unverified]**. This is NOT a native timing result.

## New implementation

CT179 adds ct179_panel_adjudicator.py, a separate offline reader of a future complete 2,304-record CT176/CT178 JSONL transcript. It never executes Rust or launches a measurement. It checks the original 48-row fixture Git blob, independently reconstructs the eight-block A/B/B/A/A/A roster, rejects duplicate JSON keys and nonfinite numbers, checks manifest/executable/child command binding, and compares every child output against the frozen public 19-word source/target and 21 original counters. It checks pipe base64 and SHA-256, positive external wall time, zero exit/capture flags, every expected sample and terminal; any missing, reordered, failed or altered record refuses the entire panel.

The frozen statistic is log((A0+A3)/(B1+B2)) from external process-wall nanoseconds. Per-packet medians across eight blocks are summarized separately within 16 direction/sector/identity strata. Single-packet identity strata receive **no cross-packet CI**; the five-packet generic strata get deterministic 2,000-resample packet-cluster bootstrap 95% intervals. A/A drift p95, reported peak RSS and missing-memory counts are retained. Complete single-target ECDLP advantage is always marked false, regardless of any component ratio. [pcc:unverified]

Protocol was committed **before implementation** at 31712e3d; implementation 9063d90b; argv/pipe fix 317b2a69; tests 67fa2cb5 and isolation fix 7a32551a; source-only workflow addition daa87d41.

## Validation and retained negative test

Initial [exact-head source gate](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44050648874) **failed**: a mutation test changed a shared in-memory fixture counter dictionary and contaminated a subsequent positive-control test. Test construction now copies arrays and dictionaries before mutation.

Corrected [source CI #44050792557](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44050792557) **passed** at 7a32551a: nine of nine normal and nine of nine optimized Python tests. A full **synthetic** 2,304-record panel recovers the deliberately programmed 1.5 transfer-route ratio while never claiming a complete solver speedup. Additional tests refuse tampered stdout digest, changed public target, altered native counter, forged executable argv, censored sample, duplicate JSON keys and nonfinite numbers. The 1.5 value is **not measured evidence**. Original CT176 source tests also passed in that job. [pcc:unverified]

## Reproduction (offline source only)

    root=experiments/chained-transfer-public-target/primitive-pricing-01
    python3 -S -m unittest discover -s "$root" -p 'test_ct179_panel_adjudicator.py' -v
    python3 -O -S -m unittest discover -s "$root" -p 'test_ct179_panel_adjudicator.py' -v
    python3 -S "$root/ct179_panel_adjudicator.py" --fixture experiments/chained-transfer-public-target/evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json --panel /path/to/authorized-complete-raw.jsonl --output /path/to/fresh-adjudication.json

A real panel must not be replaced with synthetic data when reporting scientific results.

## Remaining gates

No original authenticated 695/701 whole-corpus independent replay, Rust typecheck/link, native 48-case arithmetic parity, admitted same-host C169/C13a/C13b/N2_actual/D pricing, or complete cold source-prime rho/BSGS/IC/transfer solve was performed. Host fields and executable digests are producer-asserted, not independent execution attestation. Full solves must include setup, transfer, corrections, target DLP, inverse/recovery, LA, verification, cold startup, uncertainty and memory on identical public targets; independent signed PCC is still necessary. The EKS/Spot budget STOP remains; no paid job ran.

Sources inspected: [crypto root #3877](https://github.com/isogeny-labs/crypto/pull/3877) (merged), [queue #3904](https://github.com/isogeny-labs/crypto/issues/3904), [cryptanalysis #1700](https://github.com/isogeny-labs/cryptanalysis/pull/1700), [#1706](https://github.com/isogeny-labs/cryptanalysis/pull/1706), [crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [GPU IC #4178](https://github.com/isogeny-labs/crypto/pull/4178), AGENTS.md, CT178 session log and CT176 protocol. KB MCP and local Rust/Cargo not accessible; no novelty claim. [pcc:unverified]
