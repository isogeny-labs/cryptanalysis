# Indexed two-block public-target join on N41

**A target-conditioned quadratic inversion reduced this frozen N41
four-slot panel from 369,600 left/right root-pair tests to 1,200
indexed probes per public target while preserving the archived
eight-column witness.** An independent carryless-field audit checked
all 739,200 root pairs across the witness target and an independent
public control and matched both query results. A separate Sage
group-law audit rebuilt all 2,432 signed block sums and verified the
positive hit through cofactor-four transport.

The [frozen protocol](protocol.json) uses curve
`EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[t]/(t^41+t^3+1)`, with `y²+xy=x³+1`. Four diagonal
two-atom slots have rotations `(0,7,14,21)` and nine source-pair
options each: the archived positive pair and eight deterministic
same-seed alternatives per slot. This witness-centered law makes the
positive run a correctness and pruning control. Two-slot combinations
are retained only when all four folded columns are distinct. The
resulting 75 left and 77 right families each have eight distinct
field roots of the [universal block polynomial](../n131_w15_rotated_fouratom_inverse_20261010/resultant.json), giving 600 and 616 cached roots. The second target is the independent frozen public point from the [cofactor-four protocol](../n41_cofactor4_public_equation_20261016/circuit_protocol.json).

## Exact join

Let `u` and `v` be reciprocal x coordinates of left and right
four-atom sums, and let `t` be the reciprocal x coordinate of the
raw target. The upper Semaev condition on this chart is

`U(u,v,t) = (1+(uv)²)t² + uvt + (u+v)² = 0`.

In characteristic two, regrouping it as a polynomial in `v` gives

`(1+(ut)²)v² + (ut)v + (u²+t²) = 0`.

For every cached left root, solve this quadratic completely and
look each solution up in an index of cached right roots. Recheck
eight-column disjointness and the original equation at each hit.
The implementation handles a zero polynomial by probing every
indexed right root. As every cached block polynomial here splits
into eight simple field roots, the index preserves every root-pair
solution for this frozen panel. The checked [proof map](PROOF_MAP.md)
establishes the characteristic-two polynomial identity; the
independent field and group replays cover the current concrete
instance.

| Public target | Left/right roots | Quadratic solutions and index probes | Exhaustive pairs | Indexed hits | Target query |
| --- | ---: | ---: | ---: | ---: | ---: |
| Archived positive control | 600 / 616 | 1,200 | 369,600 | 1 | 447.189 ms |
| Independent public control | 600 / 616 | 1,200 | 369,600 | 0 | 492.642 ms |

The **308-fold reduction is in root-pair candidates tested**
(`369,600/1,200`); it is not a wall-time speedup estimate. The
reusable root-table construction took 558.454 ms, separate from
the recorded target-dependent query intervals. The main Sage process
reported peak self RSS 254,328,832 B. The [result](result.json),
[root table](root_table.json), [exhaustive audit](pair_audit_result.json),
and [group audit](group_result.json) retain the exact hits, times,
and provenance. Both target queries were ordinary-host stage
diagnostics under a one-worker, 180 s, 4-GiB observational envelope;
the CPU timing has no host-isolation receipt. The checked repository
Sage [runtime receipt](sage_runtime_info.json) was saved before work.
`candidate_id` is `null` because the index is a decomposition-stage
component, not a fully specified IC pipeline.

## W18 N131 source-size screen

The [frozen source census](projection_protocol.json) reads the
canonical W18 projected-root table and its exact column support. It
counts 33,191 eligible source codes and 66,318 distinct folded
columns. Among 550,804,645 unordered pairs of distinct codes,
65 share a column. This leaves **1,101,609,160 ordered,
column-disjoint code pairs**. The collision count agrees by both
vertex-incidence counting and an independent per-edge degree sum.

Under the explicitly stated materialization model, one uncompressed
17-byte field-root key for each ordered pair needs 18,727,355,720 B
(17.44 GiB); eight keys per pair need 149,818,845,760 B
(139.53 GiB), before indexes and other objects. Both exceed the
4-GiB N131 worker envelope. This is a source-size screen of that
materialized design, not a count of actual N131 block roots or a
bound on implicit and batched indexes. The exact census and model
are in [projection_result.json](projection_result.json).

## Next iteration

Retain the quadratic target inversion and test an implicit or
streamed two-slot root generator on unpinned N41 controls. Measure
complete source-generation and failed-attempt cost, peak process-tree
memory, verified natural relation yield, and whether batches preserve
every independently audited witness. A direct N131 promotion needs
a bounded 4-GiB implementation and an unpinned N41 gate, then the
frozen ordinary N131 public point can be queried within the goal's
600-second cap. The [terminal verifier](verify.py) binds the frozen
source hashes, all result counts, independent audits, projection,
Lean axioms transcript, and empty error streams.
