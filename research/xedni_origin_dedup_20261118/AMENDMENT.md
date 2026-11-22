# Analysis amendment for fixed-coordinate deduplication

Date: 2026-11-18

Status: prospective analysis-only correction, written before any natural panel
rows. This amendment leaves the source-instance generator, full-pencil and
deduplicated algorithms, candidate order, semantic checks, grid, seed,
release binary, and runner unchanged. `PROTOCOL.md`, `runner.py`, `analyze.py`,
and `FREEZE.json` remain the immutable version-1 record. [pcc:unverified]

## Reasons for the amendment

The version-1 analyzer requires `ok == 1600`. That is incompatible with the
inherited source law: feasibility exclusions such as a small source subgroup
or absence of an integral lift are legitimate retained outcomes. Conversely,
checking only `len(rows) == 1600` does not prove the exact frozen roster;
duplicate keys can replace missing keys. [pcc:unverified]

The version-1 name `valid_stage_optimization` also overstates what its metric
establishes. Fewer exact characteristic-zero checks are a genuine component
reduction, but the runner still constructs and transports the full pencil and
adds hashing. No prospectively calibrated weighting converts those counters
or ordinary host wall diagnostics into total work. [pcc:unverified]

`analyze-v2.py` is authoritative for any future natural output. It requires
exactly one row for every frozen `(p, family, lift, r, idx)` key, verifies
semantic parity and accounting invariants per valid row, and reports full-cell
as well as aggregate results. [pcc:unverified]

## Frozen status classification

The admissible retained feasibility exclusions are:

```text
no_point
small_order
identity
no_integer_solution
rank_deficient
```

`ok` is the only analyzed paired-arm outcome. Every other status, including
`internal_not_on_curve`, `lift_error`, `lift_cert_failed`, `group_error`,
`relation_cert_failed`, `origin_pencil_internal_error`, either lost-baseline
status, `origin_dedup_internal_error`, `origin_dedup_semantic_mismatch`, and
any unknown or missing status, invalidates promotion. This classification is
fixed before natural rows are observed. [pcc:unverified]

## Corrected result names and boundary

`exact_check_reduction_observed` is true only when the exact roster is
complete, there are no invalid statuses or invariant failures, at least one
paired `ok` row exists, every such row has dedup exact checks no greater than
reference exact checks, and at least one row (hence the aggregate) is strictly
smaller. The analyzer separately reports per-cell counters so an aggregate
cannot conceal a regression. [pcc:unverified]

`complete_work_optimization_established` is always false under this freeze.
Establishing it requires a new prospective protocol with a calibrated total
cost model or isolated benchmark design that charges construction, transport,
hashing, memory, exact checks, and source replay. The existing `wall_ns`
fields remain diagnostics only. [pcc:unverified]

This amendment can validate a narrow exact-check reduction; it cannot supply
new relations, a recovery advantage, or an end-to-end ECDLP improvement.
[pcc:unverified]
