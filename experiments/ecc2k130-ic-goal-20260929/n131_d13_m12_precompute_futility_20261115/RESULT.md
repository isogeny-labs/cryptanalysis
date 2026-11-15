# A prospective 23-query yield gate bounds the N131 preparation campaign

The first seven completed d13/m12 preparation queries are now preserved as an
exact append-only prefix: **seven ordinary timeouts, zero verified relations,
rank 0/4,134**, and **4,205.138 seconds** of charged query wall. The
[independent archive auditor](audit_v2.py) replayed their compressed XCNF and
solver-output hashes, formula counts, stop reasons, and 4-GiB RSS gates. A
prospective decision panel covering **queries 8–30** was frozen at
07:48:49 UTC, before query eight completed. The versioned
[amendment](protocol_v2.json), frozen at 07:51:01 UTC while query eight was
still running, requires every future zero-yield row used for a stop decision
to be an independently audited ordinary timeout. A producer failure or OOM
therefore leaves the yield decision ineligible.
Query eight completed at 07:52:30 UTC with status `timeout`; the
[first prospective audit](first_prospective_audit.json) independently checked
its archived formula and solver outputs and kept the gate `PENDING`.

## Operational decision rule

The frozen candidate permits at most four verified relations per preparation
query and asks for 4,390 verified rows at its first rank check. It therefore
needs at least **1,098 productive queries** among at most 8,192 attempts,
even if every productive query returns four rows. The arithmetic is checked
in [FutilityArithmetic.lean](FutilityArithmetic.lean).

The first seven failures were observed before this decision rule was chosen;
they are **excluded** from its statistical panel. If all **23 future queries
8–30** complete as audited timeouts with zero verified relations, the
[auditor](audit_v2.py) returns
`RECOMMEND_STOP_AFTER_AUDITED_ZERO_YIELD_PANEL`. If any returns a verified
relation, it returns `CONTINUE_PRODUCTIVE_QUERY_OBSERVED`. The auditor is
read-only and does not signal or alter the live candidate process.

Under the explicit exploratory model that these future query outcomes are
independent Bernoulli observations with a common productive probability
`p`, the minimum rate needed for 1,098 productive queries is
`p_min = 1098/8192 = 0.134033203125`. At `p ≥ p_min`, the chance of zero
productive queries in the prospective panel is at most

`(1 - p_min)^23 = (7094/8192)^23 = 0.0365198118678421 < 0.05`.

The checked Lean inequality uses exact integer arithmetic. The independence
and constant-rate premises are empirical assumptions; solver seeds and target
points differ across queries, and the bound is an operational futility signal,
not a deterministic impossibility result. An early stop would preserve the
frozen run and all completed rows as a separate censored terminal sidecar.

## Frozen evidence and verification

| Item | Frozen value |
| --- | --- |
| Curve / workload | `EC1N131Ckb1heb5f1998f20b` / `3c1992b7c92f` |
| Candidate | `IC1N131Ckb1fb1083108PDP12satRCdirectLAgaussTDdirectISO0h195ae7ea5e75` |
| Observed prefix | [first_seven.jsonl](first_seven.jsonl), distinct scalar fixtures, seven `timeout` rows |
| Prospective panel | Query indices 8–30; one completed query is productive iff it has at least one verified relation |
| Maximum per query | Four verified relations; 600-second parent solver cap; 4-GiB combined RSS cap |
| Frozen gate state | [freeze_audit_v2.json](freeze_audit_v2.json): `PENDING_PROSPECTIVE_QUERIES` after seven completed attempts |
| First prospective outcome | Query 8: independently audited `timeout`, zero verified relations; 22 future queries remain in the panel |

The original [protocol](protocol.json) and [v1 read-only auditor](audit.py)
remain preserved. The v2 amendment adds the independent timeout-archive gate
without changing the live candidate's source, inputs, limits, or run
identity. Re-run `python3 audit_v2.py` from this directory to inspect the
authoritative live append-only log. If a later panel reaches its stop
condition, independently audit the complete terminal prefix and record any
process intervention separately; the present artifact authorizes no automatic
termination.

The checked Lean 4.35.0 [output](lean_check.stdout.txt) reports no axioms for
the two arithmetic declarations. [PROOF_MAP.md](PROOF_MAP.md) records their
exact statements and the conditional statistical bridge.
