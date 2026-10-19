# Frozen public-Q three-leaf prefix panel

Sixteen valid three-leaf code prefixes were fixed in the archived Q1358 d10
15-summand XCNF for the ECC2K-130 public point. Each restricted query reached
its 25-second parent cap without a terminal SAT or UNSAT result. The invalid
code control reported UNSAT in 0.603 s. This is a measured failure of simple
input pinning to yield cheap prefix rejection under the tested solver settings;
the exact validity of the 16 ordinary prefixes remains `BOUNDED_UNKNOWN`.

## Method and identity

The field degree is 131, the curve ID is `EC1N131Ckb1heb5f1998f20b`, and
the frozen one-public-point workload ID is `3c1992b7c92f`. The archived
official-Q formula SHA-256 is
`0a2f4b3e3acc8e26049921567b3c3b04b2a1eace4e86ccb8a193bd4cca29fd41`.
The 16 ordinary triples were selected once from the audited 532 valid phi
codes per position by seed `2026101814`, before running the solver. Each
triple fixes only the first three ten-bit codes. Leaf signs, remaining 12
codes, all intermediate variables, and the target's four-way cofactor-fiber
selector remain free. The [protocol](protocol.json) retains every triple,
source hash, unit literal, and solver flag.

[mapping_audit_sage.py](mapping_audit_sage.py) rebuilt the exact original
formula from the pinned Q1358 source, matched its byte hash, and verified
that the first three leaf code bits occupy XCNF variables 2–11, 12–21, and
22–31. [run.py](run.py) deterministically appended the corresponding unit
clauses. [verify.py](verify.py) regenerates each query hash and checks all
solver logs and resource receipts.

| Arm | Count | Terminal observation | Parent wall per arm | Peak sampled combined RSS |
| --- | ---: | --- | ---: | ---: |
| Unpinned baseline | 1 | `BOUNDED_UNKNOWN_ARM_WALL_CAP` | 25.058 s | 483,868,672 B |
| Invalid selector `leaf0=0` | 1 | `UNSAT_REPORTED_NEEDS_PROOF_AUDIT` | 0.603 s | 146,915,328 B |
| Frozen valid three-leaf prefixes | 16 | all `BOUNDED_UNKNOWN_ARM_WALL_CAP` | 25.039–25.208 s | up to 1,183,350,784 B |

The sum of retry arm wall intervals was 427.331 s, with one solver worker at
a time. The campaign cap was 550 s, each parent arm cap 25 s, and combined
RSS cap 4 GiB. Fourteen of the 16 valid arms have solver-restart lines in
their raw logs; two ended after matrix setup and branch initialization with
no restart line. Native XOR matrices were built, including ten selected
matrices; the logs record additional unused matrices. No status here is a
certified contradiction for a valid prefix. A SAT report would require exact
model decoding and independent group replay before becoming a relation.

The first launch is retained separately as
[attempt1_failure.json](attempt1_failure.json): the sandbox denied `ps`
during live RSS sampling, the parent monitor exited, and its baseline child
was stopped and verified absent. Its exact parent wall time is null and its
raw output remains in `attempt1_failed_arms/`. The monitored retry used host
process visibility and produced all 18 arm receipts. The checked Sage
runtime used for freeze and formula-mapping audit is retained in
[sage_runtime_info.json](sage_runtime_info.json).

## Next constraint to test

The pair-occupancy study found no exact two-leaf point deduplication, while
this panel shows that simply pinning three codes in the full SAT formula does
not expose fast rejections. The next experiment should eliminate internal
variables from the archived native-XOR system and measure whether its exact
projection contains any target-dependent linear constraint on the first
three code words and endpoint selector. Such a constraint would reject
prefixes before the nonlinear SAT search while preserving every formula
solution. Record projected rank, surviving equations, rejected ordinary
prefixes, elimination cost and memory, and a planted formula witness check.
If the projected rank is zero, that is a specific negative result for this
linear gate and motivates a low-degree nonlinear partial-chain gate.
