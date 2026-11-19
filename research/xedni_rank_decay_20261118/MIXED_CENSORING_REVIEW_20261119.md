# Mixed-censoring optimizer review

Date: 2026-11-19

Revision reviewed: `3009a9a82`

Question: can the signed decay-slope sensitivity minimize over every integer
per-prime unresolved allocation instead of checking only the two uniform
corners? [pcc:unverified]

## Retained implementation and command

- Implementation: [`mixed_censoring.py`](mixed_censoring.py)
- Tests: [`test_mixed_censoring.py`](test_mixed_censoring.py)
- Hardware/tool context: [`HARDWARE.json`](HARDWARE.json), Python 3.12

```text
cd research/xedni_rank_decay_20261118
python3 -m unittest -v test_mixed_censoring.py
```

Observed producer result: 9 tests passed in 1.281 seconds, with zero failures
or skips. The tests include an independent full-product brute-force comparison
on bounded boxes and an example whose worst allocation is not either uniform
corner. [pcc:unverified]

## Independent adversarial review

The reviewer separately checked the exchange argument used by the scalable
conditional-Poisson path and compared it with full enumeration on 200 small
random boxes across three alpha values and three simultaneous-hypothesis
counts. All 200 comparisons agreed. This is an unsigned reviewer report, not
an independently verified execution receipt. [pcc:unverified]

For fixed total selected events, moving an unresolved success from larger
`log(p)` to smaller `log(p)` minimizes the event-weighted mean. On one such
segment the lower-endpoint objective has the form
`x + c/T - C/sqrt(T)`, so its integer minimum is among segment endpoints and
integers neighboring its single stationary point. The implementation retains
the chosen allocation and a deterministic digest. [pcc:unverified]

## Result boundary

This closes neither the full inference gate nor the experiment:

- binomial-cloglog uses exhaustive enumeration and fails closed above its
  configured state limit;
- aggregate per-prime counts cannot determine within-cluster allocations, so
  cluster-bootstrap optimization returns `BLOCKED`;
- the module is not yet integrated into `analyze.py` or the natural executor;
- its digests are producer-generated integrity bindings, not signed PCC
  verification.

Therefore the only supported conclusion is that the aggregate
conditional-Poisson subproblem has a tested prospective optimizer. No natural
decay result or slope is reported. [pcc:unverified]

This scoped statement is registered as `PCC-20261119-f9077b`; its current
standing is unverified. [pcc:unverified]
