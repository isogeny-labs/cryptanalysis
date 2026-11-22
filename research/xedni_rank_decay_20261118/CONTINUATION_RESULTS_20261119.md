# Xedni continuation: six control gates

Date: 2026-11-19

## Outcome

All six locally actionable continuation items now have executable,
adversarially tested control implementations. None is in the authorizing
freeze, none is production eligible, and none generated a natural source,
lift, rank, relation, or recovery row. The 16--32-bit decay heuristic is still
neither defeated nor reproduced by this continuation. [pcc:unverified]

The original experiment remains unchanged: independently cross lift strategy,
selected-point count `r`, and Silverman's small-prime local conditions; retain
rank intervals and complete relation/recovery work; and apply the frozen
simultaneous signed-slope rule to fresh discovery and replication stages.
[pcc:unverified]

## Requirement-to-evidence ledger

| Continuation item | Implemented evidence | Exact boundary |
| --- | --- | --- |
| Bind row execution | `runner.py validate-executor` hashes and schema-checks nine committed components, checks explicit production flags and tool-pin shape, exercises failure canaries, and returns `BLOCKED_NON_PRODUCTION` with `natural_rows_started=0` | Diagnostic only; no natural-row command, checkpoint call, scientific tool call, stage adapter, clean freeze, or runtime tool identity |
| Finish mixed censoring | `mixed_censoring.py` exhausts bounded row-level unresolved allocations and a deterministic nested cluster bootstrap; caps states, fits, plan entries, and total row visits before iteration | Exact only inside declared ceilings; strict validated-row binding only; outside freeze; `production_eligible=false` |
| Support `r=7..9` transfer | `cubic_jacobian_map.py` verifies supplied homogeneous maps, inverse identities, selected points, origin translation, reduction, subgroup replay, and relations | Degree-one controls only; general nonlinear maps remain `SELECTED_POINTS_ONLY`; no pinned natural-family constructor or global exceptional-locus certificate |
| Certify dependence or absence | `relation_lattice.py` verifies a complete primitive relation kernel from exact point decompositions, torsion presentation, and a claimed full saturated Mordell--Weil basis | Conditional structure only; it does not find or independently certify the full basis, and no negative natural row is promoted |
| Strengthen verifier provenance | `verifier_receipts.py` verifies strictly bound, time-limited signed receipts and rejects key, payload, Git, replay, and small-order forgeries | Repository trust is `NOT_COVERED`: no trusted execution-verifier digest or producer-independent immutable keyring/base pin |
| Freeze power and cost | `allocation_planner.py` exactly regenerates `POWER_ALLOCATION_20261119.json`, separates observed-event rules from reference expected-event scales, binds discovery primes, and leaves replication primes/resources unallocated | Reference scale only; no event-rate lower bound, cluster power, committed workers, fresh replication manifest, or powered label |

Every row in this table describes producer-side control evidence rather than a
natural experimental result or independently signed execution proof.
[pcc:unverified]

## Adversarial corrections made during review

The final code removes several paths that initially looked harmless but were
not acceptable under the repository threat model: a caller-controlled cluster
binding label, then a mutable in-process receipt registry; an uncapped
`states × replicates × rows` loop; duplicate allocation scenarios; discovery
prime reuse for replication; a duplicate imported CLI entry point; unbounded
symbolic/lattice certificates; and direct-Python scalar subclasses that could
lie about equality, primality, or duplicate IDs. The final input boundaries
use exact plain-JSON types before scientific validation. [pcc:unverified]

These corrections do not make producer output independently trustworthy. They
make the control interfaces fail closed while the signed-verifier and freeze
gates remain open. [pcc:unverified]

## Transfer and relation boundary

The typed cubic correspondence is `f:C -> E` followed by
`psi(P)=f(P)-f(O)`. The verifier replays
`psi_bar(P_i)=[m_i-m_O]H_E` and any supplied relation. The source-linked
assessment, diagram, and printable report are
[`CUBIC_TRANSFER_REPORT_20261119.md`](CUBIC_TRANSFER_REPORT_20261119.md),
[`cubic_transfer.svg`](cubic_transfer.svg), and
[`CUBIC_TRANSFER_REPORT_20261119.pdf`](CUBIC_TRANSFER_REPORT_20261119.pdf).
No natural construction or cost measurement exists. [pcc:unverified]

For a supplied full saturated Mordell--Weil basis, the lattice verifier checks
the exact free-plus-torsion presentation, kernel rank, primitive maximal-minor
condition, point replay, and target-coefficient arithmetic. A bounded proposer
or arbitrary caller callback cannot promote absence. Basis search, saturation,
trusted verification, and their full costs remain open. [pcc:unverified]

## Prospective exposure, not an allocation

The optional stronger reference scale assigns five expected events to each
factor cell at each of bits 16, 18, 20, 22, and 24 in each stage. Across all
90 factor cells and both stages, the exact reference totals are:

| Reference exponent | Rows if the optional scale were executed |
| --- | ---: |
| `beta=-1` | 20,112,998,400 |
| `beta=-0.75` | 362,947,860 |
| `beta=-0.5` | 7,142,400 |

This optional scale is stronger than, and separate from, the protocol rule of
at least 30 *observed* high-bit useful events globally. Thirty expected events
does not power a probability of observing thirty. The one-cell independent
Bernoulli zero-event reference remains 50,260,046 trials at bits 32 and
`beta=-0.75`; it excludes multiplicity, clustering, and censoring.
[pcc:unverified]

The excluded 1,080-row 16/18-bit calibration has a rank-timeout ceiling of
2,656,800 worker-seconds, or an ideal 147.6 hours on five fully utilized
workers, before construction, relation, verification, storage, or failure
costs. No worker, wall-time, storage, Magma, or checkpoint commitment exists;
the manifest therefore remains `UNALLOCATED`. [pcc:unverified]

## Validation

Final producer validation is recorded after the last adversarial fix:

```text
python3 -m unittest discover -v
Ran 382 tests in 68.540s
OK (skipped=6)
```

The focused transfer/lattice suite passed 54 tests, the runner suite passed 25,
the verifier-receipt suite passed 26, and the allocation suite passed 15. The
mixed-censoring suite passed 18 tests.
These are local producer tests, not signed execution receipts.
[pcc:unverified]

The pinned Lean 4.34.1 project also rebuilt the four existing rank-decision
theorems, and `#print axioms` reported no axioms for each theorem. This proves
only the stated rank-bound implications; it does not verify a rank transcript,
cubic constructor, or relation-lattice basis. [pcc:unverified]

The deterministic allocation check is:

```sh
python3 allocation_planner.py --check POWER_ALLOCATION_20261119.json
```

It returns `PASS_PROSPECTIVE_UNALLOCATED` and manifest SHA-256
`fce59ef5b6d07004937a9b6aea9f5b8b0dfbe567f79d15086e3c8456f169cfe0`.
[pcc:unverified]

The committed-HEAD runner diagnostic is retained as
[`EXECUTOR_VALIDATION_20261119.json`](EXECUTOR_VALIDATION_20261119.json). At
implementation commit `0dc4f898135345f8047541b41a33b324b16dfef1`, all nine
component byte/schema checks matched; the command exited 2 with
`BLOCKED_NON_PRODUCTION`, validation SHA-256
`59741475ae28a9a4a653636aba68a511b9812bfb874ad61ceb8601e6e2c055f4`, and
`natural_rows_started=0`. It invoked no checkpoint, scientific tool, or stage
adapter. Exit 2 is the expected retained blocked result, not a passed
production preflight. [pcc:unverified]

## Remaining launch boundary

Natural execution still requires all of the following: successful checkpoint
upload/gate on the pushed head, a licensed pinned Magma runtime and controls, a
trusted independent execution verifier, complete freeze/tool/lift/local/rank
provenance, a clean authorizing freeze, a natural cubic constructor and global
map certificate for `r=7..9`, a proven full saturated basis route for negative
relation labels, and committed discovery/replication resources with fresh
replication primes. [pcc:unverified]

The next admissible natural work remains the excluded two-row-per-cell 16/18
bit calibration after every launch gate passes. It is not discovery and cannot
by itself decide the decay heuristic. [pcc:unverified]
