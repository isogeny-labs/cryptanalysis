# CT159 — C169/C13/D pricing evidence type-integrity audit

2026-11-16. Standing **[pcc:unverified]**. Scope: syntactic and structural validation of *raw microtiming JSON*, not original native measurement, 695/701 Jacobian parity or complete ECDLP.

## Concrete defect reproduced

The old CT126 `check_pair.py` (Git blob `1caf31daadc71b30be45e8e8e46224c03c6650a2`) used `runs[arm]['identity_checks'] == runs['original-1']['identity_checks']`. Python interprets `[1] == [True]` and `[1] == [1.0]` as true, even though these are distinct JSON values. Likewise `223 == 223.0` and fixture scalar `1 == True` silently passed equality. Standard `json.loads` silently accepts `NaN`, `Infinity`, an exponent `1e999` that decodes as infinity, and repeated object member names. The host-language/decoder repro was run locally. **No actual original native logs were available or alleged to be tampered.**

CT128 had repaired a separate `assert`-in-`-O` bug, but not this type alias. CT157 had already applied similar guards to a **different** 695-record parity comparator on #1533; CT159 applies the remedy to the standalone CT126 price auditor. The prospective [protocol](CT159_TYPED_PRICE_PROTOCOL.md) landed at `014fc68c` before implementation.

## Exact source and hosted check

The source is [`check_pair.py`](check_pair.py), commit `658dca512276c426d5e04c291193a49717824170`, blob `b7dea8593b90dfad3b7fc08a707a8ca858da528b`.

- `typed_json_equal` compares canonical JSON with finite numeric enforcement so true/1/1.0 remain distinct. Exact Python `int` checks bind all six fixed numeric identity fields and all five fixture scalars.
- `strict_json_loads` rejects duplicate keys, nonstandard NaN/Infinity tokens and finite-exponent overflow through its object-pair, constant, and float hooks.
- All original eight CT128 mutations plus seven additional type aliases are rejected, and five malformed JSON parser controls reject. The positive synthetic fixture remains accepted.
- [Hosted source-only workflow #43872145291](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43872145291) completed success on exact source commit, job `133315793074`. Decoded log independently shows **identical** JSON output for `python3 -S` and `python3 -O -S`: `positive=pass`, 15 named schema/mutation rejections, `invalid_json_rejected=5`. It parsed Rust syntax without linking/running native code.

Reproduction on a clean checkout of this branch (no paid compute):

```sh
D=experiments/chained-transfer-public-target/primitive-pricing-01
python3 -m py_compile "$D/check_pair.py"
python3 -S "$D/check_pair.py" --self-test > /tmp/ct159-plain.json
python3 -O -S "$D/check_pair.py" --self-test > /tmp/ct159-optimized.json
cmp /tmp/ct159-plain.json /tmp/ct159-optimized.json
```

## Explicit scientific limitations

These synthetic validators cannot independently verify that native public keys are valid source/destination elliptic points or that displayed durations were really incurred. Existing original/reuse [695/701-record] parity remains unexecuted independently, and the native C169, C13-first/second and doubling D cost measurements have not been admitted or executed. Even a positive warm primitive-time ratio would not be a complete single-target ECDLP result. Genuine cold source/rho/BSGS/IC, complete transferred public-target solves, setup/transport/correction/linear algebra/verification/RSS, paired uncertainty, source identity and independent signed PCC remain outstanding.

The CT141 manually gated workload still requires explicit owner/budget admission, and no paid EKS/Spot/GPU run, protected merge, root ledger rewrite, or PCC promotion took place. Reviewed root [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [CT126 #1534](https://github.com/isogeny-labs/cryptanalysis/pull/1534), [CT125 #1533](https://github.com/isogeny-labs/cryptanalysis/pull/1533), [CT129 #1537](https://github.com/isogeny-labs/cryptanalysis/pull/1537), [frontier #4215](https://github.com/isogeny-labs/crypto/pull/4215), [GPU IC #4178](https://github.com/isogeny-labs/crypto/pull/4178), Python JSON docs, and RFC 8259. Research-KB unavailable; no novelty/absence claim. **[pcc:unverified]**
