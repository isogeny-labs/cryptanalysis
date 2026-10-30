# Next comparison: polynomial pair index and signed labels

Prospective protocol, published before any performance or held-out run.
Status: NOT EXECUTED. This file schedules no experiment or compute resource.
The objective remains efficient known-label construction in the same small
usable domain, with lower complete verified cost. No acceptance criterion is
weakened by a polynomial operation count or a graph-only test.

## Workload and frozen inputs

Use the exact same curve/subgroup, P, public Q and usable coordinate set S
for every arm. Record EC1/UID, subgroup/order proofs, ambient membership
equation, root-to-curve filtering, orientation rule, cardinality n, and source
hashes before timing. Existing archived fixtures are correctness controls;
qualified timings need current machine and workload receipts. Select growing
sizes and the best current IC constructor on training data before held-out
fixtures are generated. Do not choose a favorable input panel after results.

The constructor receives no hidden target scalar or vertex logs. Known logs
may occur only in fixture generation and independent replay. Queries and batch
sizes, cached tables and memory budgets are frozen before each comparison;
each arm may use its declared best strategy, explicitly treating query order
and batching as controlled algorithm variables rather than pretending their
witness events are identical. Publish all seeds and unsuccessful cases.

## Arms and correctness

Compare (a) the coordinate polynomial index plus signed graph, (b) an explicit
signed pair dictionary plus the same graph core, (c) the best tuned reusable
multi-target/interval BSGS constructor, and (d) rejection scanning as a control.
Keep optimized label/window sampling and coordinate normalization in every arm.
Do not compare only against untuned or single-block BSGS.

Stop a trial when all prescribed vertices have independently verified labels,
or a recovered DLP is independently verified. Record those outcomes separately;
an earlier DLP is a success, not a discarded nuisance. Refuse unverifiable
labels and witnesses. Complete-set labeling and fractional-component labeling
are distinct workloads; do not silently replace the former by the latter.

## Charged costs

Retain exclusive wall/CPU/operation and memory records for input construction,
ambient roots, actual point lifting, subgroup filtering, index/table setup,
known-label query generation, all failed/empty batches, polynomial products,
division/remainders, pair localization, witness group verification, graph
bookkeeping, duplicate handling, anchors, scalar recovery and final replay.
Count allocations, sorting and collected-domain maintenance. Root extraction
avoided by one component does not make input-domain extraction free.
Report preprocessing separately and charge it to the cold constructor;
amortized workloads must name the exact target count and cache policy.

These are stage measurements. A later IC improvement also needs every
target-dependent phase, one unseen target, independently verified recovery,
the same-point strong rho and precomputation-rho controls, and current repository
accounting. A Q-dependent label constructor is target-dependent online work;
do not hide it in target-independent preparation.

## Execution and acceptance

Before a performance run: publish frozen parameters/resource/stop limits,
obtain the required S3 checkpoint receipt, use the approved execution host and
measurement tier, record exposed hardware/affinity/memory/isolation, and pass
the tier's preflight, A/A and positive controls. Follow GPU/ICMS requirements
where applicable. No benchmark is authorized by a unit-test CI selector.

Use repeated matched trials and report paired uncertainty, failures, OOMs,
timeouts and early DLPs. A stage improvement requires a lower complete verified
constructor cost against the best arm in the declared regime; the comparison
cannot combine mismatched phases or hosts. Otherwise retain a null/negative
result. A pipeline or sub-rho improvement remains a separate gate. Full
formalization of the broader elliptic and probability claims remains open.
