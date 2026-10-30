# D79 live seven-source collector: retrospective evidence report

**Evidence window:** saved experiment `2026-10-27`; this retrospective report was assembled on `2026-10-28`. No trials were run for this report. The repository records no dedicated RUN IDs or exact start timestamps for these cases.

## Question and result

On the frozen live-collector panel, does support-at-most-seven relation collection reach rank 39 on the fresh D79 classes, and how many source equations are used before the rank target or source cap?

The saved, independently audited index records eight fresh classes. Seven reached F_q rank 39 after 33–40 source equations; p=1825517, q=6091 reached only rank 38 at the 40-source cap. The separate known control p=103357, q=197 reached rank 39 after 14 source equations. These are source-count and rank observations, not a calibrated timing comparison or an end-to-end attack result. All nine audits are marked PASS; the p=1825517 case has no anchored replay in this seven-source result because rank 38 did not determine all 40 logs.

## Saved evidence

- Frozen protocol and inputs: [`PROTOCOL.md`](../../PROTOCOL.md), [`inputs.json`](../../inputs.json).
- Collector output and case summaries: [`index.json`](../../index.json), [`cases/`](../../cases/).
- Independent Sage audit: [`audit.json`](../../audit.json), [`audit_sage.py`](../../audit_sage.py), [`audit-stdout.jsonl`](../../audit-stdout.jsonl).
- Sealed post-audit record: [`post-audit.json`](../../post-audit.json).
- The chart source and file digests are recorded in [`sources.json`](sources.json). The vector figures are [`source-counts.svg`](source-counts.svg) and [`collector-flow.svg`](collector-flow.svg).
- Printable report with a vector summary visual: [`report.pdf`](report.pdf).

The audit covers the retained source equations, exact support-at-most-four through support-at-most-seven relation sets on retained prefixes, rank increments and stopping rules, journal hashes, phase accounting, and anchored replays where the rank target was reached. It reports PASS for all nine cases. The known-control row is kept separate from the eight-class fresh panel.

## Interpretation and limits

The seven-of-eight fresh-panel count is descriptive for this frozen panel. It does not establish a population success rate. The p=1825517 residual motivates the separately frozen support-eight follow-up documented in the neighboring experiment. Local component wall times lack Tier 0/1 isolation; no calibrated speedup is claimed. `candidate_id` and `target_online_ms` are null. No new run, curve search, or ECDLP attack was performed for this report.

The run receipts do not record a dedicated RUN ID, exact start timestamp, or hardware identity. Sage runtime metadata is retained in the linked experiment directory; this report does not infer missing identity or timing metadata. No matching D79 canonical frontier graph existed in `knowledge/frontiers/ecdlp/` in the inspected branch tree; no canonical graph source was changed because this report records a retrospective panel summary rather than a newly verified transfer or frontier edge.

## Next discriminating step

Use the existing support-eight residual as a hypothesis generator, then freeze a disjoint live panel before collecting any new sources. Pair support-seven and support-eight policies under the same source order and stopping rules; preserve separate source-count, relation-yield, rank, audit, replay, and total-cost outcomes. Do not reuse the retained p=1825517 class as a fresh panel member.
