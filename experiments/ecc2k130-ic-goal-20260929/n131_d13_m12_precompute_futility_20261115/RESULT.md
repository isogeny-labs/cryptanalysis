# A fully prospective 23-query yield gate bounds N131 preparation

The first **eight** completed d13/m12 preparation queries are preserved as
an exact append-only prefix: eight ordinary timeouts, zero verified relations,
and rank 0/4,134. The [current protocol](protocol_v4.json) froze at
**07:57:58 UTC**, while query nine was running and **before query ten
started**. It excludes the in-flight query nine and tests the 23 wholly
unstarted queries **10–32**. The [independent archive auditor](audit_v4.py)
replays compressed XCNF and solver-output hashes, formula counts, stop
reasons, and 4-GiB RSS gates for zero-yield rows. An OOM or producer failure
cannot count as low relation yield. The first [v4 audit](freeze_audit_v4.json)
passed for the eight archived prefix rows and returned `PENDING`.

The earlier v1/v2 panel included query eight, which was already underway at
its freeze. Both protocols and the [audited query-eight outcome](first_prospective_audit.json)
remain preserved. Version 3 corrected the panel to queries 10–32, but its
auditor stopped before execution on a copied hash-key error. The
[failure receipt](audit_v3_failure.json), [v3 protocol](protocol_v3.json),
and source remain intact. Version 4 fixes that lookup without changing the
future panel; its successful pre-panel audit is the authoritative gate.

## Operational decision rule

The frozen candidate permits at most four verified relations per preparation
query and asks for 4,390 verified rows at its first rank check. It therefore
needs at least **1,098 productive queries** among at most 8,192 attempts,
even if every productive query returns four rows. The arithmetic is checked
in [FutilityArithmetic.lean](FutilityArithmetic.lean).

The first eight completed failures were observed before the final rule; query
nine was already running. All nine are **excluded** from the statistical
panel. If all **23 future queries 10–32** complete as audited timeouts with
zero verified relations, the [auditor](audit_v4.py) returns
`RECOMMEND_STOP_AFTER_AUDITED_ZERO_YIELD_PANEL`. If any returns a verified
relation, it returns `CONTINUE_PRODUCTIVE_QUERY_OBSERVED`. A productive
query nine also cancels the stop recommendation. The auditor is read-only
and does not signal or alter the live candidate process.

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
| Observed prefix | [first_eight.jsonl](first_eight.jsonl), distinct scalar fixtures, eight `timeout` rows |
| In-flight at freeze | Query 9; excluded from the statistical panel |
| Prospective panel | Query indices 10–32; one completed query is productive iff it has at least one verified relation |
| Maximum per query | Four verified relations; 600-second parent solver cap; 4-GiB combined RSS cap |
| Frozen gate state | [freeze_audit_v4.json](freeze_audit_v4.json): `PENDING_PROSPECTIVE_QUERIES` after eight completed attempts |

The [version history](protocol.json) preserves each amendment and the
pre-execution auditor failure. The current v4 gate changes no live candidate
source, input, limit, or run identity. Re-run `python3 audit_v4.py` from this
directory to inspect the authoritative append-only log. If the panel reaches its stop
condition, independently audit the complete terminal prefix and record any
process intervention separately; the present artifact authorizes no automatic
termination.

The checked Lean 4.35.0 [output](lean_check.stdout.txt) reports no axioms for
the two arithmetic declarations. [PROOF_MAP.md](PROOF_MAP.md) records their
exact statements and the conditional statistical bridge.
