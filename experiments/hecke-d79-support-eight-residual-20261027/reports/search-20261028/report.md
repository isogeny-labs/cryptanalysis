# D79 support-eight residual: retrospective evidence report

**Evidence window:** saved experiment `2026-10-27`; this retrospective report was assembled on `2026-10-28`. No trials were run for this report. The repository records no dedicated RUN IDs or exact start timestamps for these cases.

## Question and result

Can a signed support-eight relation close the single rank deficit left by the 40-source p=1825517, q=6091 live support-seven collector?

The frozen initial search stopped at its 12,000,000 signed-quintuple-probe cap with rank 38 and 168 verified rows. A separate full-space follow-up used the same 40 sealed source equations and frozen rank-38 row set. It found a novel outside-trace direction after 12,323,269 probes, with 225 verified rows and final F_6091 rank 39. The independent audit reports an anchored solve and PASS for all 40 scalar replays. These are distinct executions; the probe counts are not added together.

The selected relation uses sources `(0, 3, 4, 6, 8, 9, 30, 31)` with signs `(+,+,-,-,-,+,-,-)`. Adding its assembled class-point row to the frozen base plus support-four through support-seven relations raises rank from 38 to 39. The matched row and replay are algebraically audited; the local wall times are exploratory and lack Tier 0/1 isolation.

## Saved evidence

- Parent protocol and receipts: [`PROTOCOL.md`](../../PROTOCOL.md), [`pre-run.json`](../../pre-run.json), [`result.json`](../../result.json), [`audit.json`](../../audit.json), [`post-audit.json`](../../post-audit.json).
- Separate full-space follow-up: [`full/PROTOCOL.md`](../../full/PROTOCOL.md), [`full/pre-run.json`](../../full/pre-run.json), [`full/result.json`](../../full/result.json), [`full/run-stdout.jsonl`](../../full/run-stdout.jsonl).
- Producer and independent verifier: [`run_sage.py`](../../run_sage.py), [`full/run_sage.py`](../../full/run_sage.py), [`audit_sage.py`](../../audit_sage.py), [`verify.py`](../../verify.py).
- The upstream live-seven record is linked from the neighboring experiment: [`live-seven-20261027/`](../../../hecke-d79-live-seven-20261027/).
- Source digests and the figure data are in [`sources.json`](sources.json); vector figures are [`probe-rank.svg`](probe-rank.svg) and [`relation-flow.svg`](relation-flow.svg).
- Printable report with a vector summary visual: [`report.pdf`](report.pdf).

The `full/PROTOCOL.md` contains a parenthetical typo in the complete-space probe count. The correct identity is `binomial(40,5) * 2^5 = 21,056,256`; the frozen cap of 22,000,000 and the producer stopping rule are correct. This report preserves that discrepancy rather than editing the frozen protocol.

## Interpretation and limits

This demonstrates that one verified support-eight relation closes the retained class's rank deficit under the frozen construction. It does not show that support-eight is generally useful across D79 classes, improve end-to-end ECDLP cost, beat rho, or establish a speedup. `candidate_id` and `target_online_ms` are null. All 40 replays are scoped to these q-projected class-point logarithms.

The receipts do not provide a dedicated RUN ID, exact start timestamp, or hardware identity. Sage runtime metadata remains in the experiment directory. No matching D79 canonical frontier graph existed in `knowledge/frontiers/ecdlp/` in the inspected branch tree; no canonical graph source was changed because this retrospective result does not verify a new isogeny, transfer, or frontier edge.

## Next discriminating step

Freeze a disjoint live panel comparing support-seven and support-eight collectors under identical source order, stop rule, and complete accounting. Require exact row audits and anchored replay for each class, and retain censored cases. Do not count this retained class as fresh evidence.
