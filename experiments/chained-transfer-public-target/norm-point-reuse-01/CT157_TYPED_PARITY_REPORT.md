# CT157 — typed parity repair of original 695-record comparator

2026-11-16 · [pcc:unverified]. Existing CT125 PR #1533; prospective protocol `CT157_TYPED_PARITY_PROTOCOL.md` committed before source change.

## Defect and correction

The previous `compare_norm_reuse.py` compared supposedly immutable original/reuse JSON objects with Python `==`. A mathematical field containing integer 0 can be replaced with JSON `false` and still compare equal; integer 1 with `true` or `1.0` also passes. The six legacy mutations did not detect type aliases. This is not CT128's separate optimized-Python assertion bug.

The additive patch implements recursive strict type-preserving JSON equality, including nested objects/arrays and finite numeric validation; rejects nonstandard NaN/Infinity JSON parsing; requires the three original/optimized map evaluation counters to be actual integers; and retains all original 695-record, 672-exceptional, 48-row and route-counter limits.

## Reproducible tests and failure injection

From the repository checkout:

```sh
D=experiments/chained-transfer-public-target/norm-point-reuse-01
python3 -S "$D/compare_norm_reuse.py" --self-test
python3 -O -S "$D/compare_norm_reuse.py" --self-test
```

The unchanged original six sabotage controls are retained. New checks: five legacy-accepted aliases (exception index 0→false, selected input 0→false, modified count 1→true and 1→1.0, unchanged count 0→false), one original-side count 2→2.0, plus three NaN/Infinity token rejections. Exact-head CI outcome must be read separately; no success is inferred before execution.

## Sources and scientific standing

Read the actual CT125 comparator Git blob `d8e1b8a6c9615310439411831df847739682eb5d`, CT125 source-guard workflow, crypto #3877/#4215, cryptanalysis #1523/#1533/#1562/#1589 and previous CT128 finding. Research-KB/Conductor unavailable in connector runtime; consulted repository source instead.

This fixes evidence-validation semantics only. It does NOT independently verify either whole native 695/701 raw output, identify a prime-field source transfer, price genuine C169/C13a/C13b/D, or verify a transferred complete public-Q ECDLP. Original norm tests, source curves, PCC ledger, frozen artifacts, owner-admitted paid workflow and root producer branch unchanged. [pcc:unverified]

## Actual exact-source hosted gate and secondary selected-vector audit

[CT157 source-only GitHub Actions run #43859795026](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43859795026), job #133273299385, finished **success** at `7a77cf046af8a80cbe8f3516260be66575d86233`. Read back its decoded job log: normal Python and optimized Python each printed `{"mutations_rejected":11,"non_json_numeric_tokens_rejected":3,"original_counter_type_mutations_rejected":1,"synthetic_695_record_control":"pass"}`, and exact old Rust source derivation passed. This is actual hosted source execution, not genuine native or signed scientific verification. [pcc:unverified]

Separately inspected *both actual published selected-vector JSON source blobs* from crypto #3877: frozen original `19bc5c1ad37d55daa51a9ec95fa0af90296385c6` (`public-n4-complete-chain-checkpoint-01/01-literal-setup-and-selected-vectors.json`), versus published reuse `9ac741668dd1ffa9632ff0d58e6f4dd18c3` (`public-n4-norm-point-result-01/literal-selected-vectors.json`), under `research/chained-jacobian-transfer-20261110`. A separately authored JavaScript comparison of 48 corresponding rows checked their nonroute public fields, route non-map counters, route-call transformations, additional doubling counters, 24/24 direction balance, and four sectors with 12 each. All 144 route-pair checks matched; no deviations. Totals: direct169 evaluation reduction 48, literal two-hop C13 reduction 96, retained-lift C13 reduction 96. The comparison used decoded JSON numbers, not lexical numeric-token identity, and is **not a whole-695 native or signed PCC replay**. These two source blobs originate from producer-controlled artifacts; independent algorithmic inspection does not establish independent execution custody.

Corresponding traceable discussion: [CT157 owning PR #1533](https://github.com/isogeny-labs/cryptanalysis/pull/1533#issuecomment-6915416427) and [root PR #3877](https://github.com/isogeny-labs/crypto/pull/3877#issuecomment-6915421667). [pcc:unverified]
