# Collision-exact aligned W29 public-point circuit and bounded query

The aligned N131 W29 five-pair formula now encodes **ten distinct
Frobenius-folded source columns exactly** while retaining the original
28-bit full-domain source variables, source-validity witnesses, and
frozen public target. A constructed five-pair relation satisfies all
274,794 clauses and 42,402 native XOR rows and passes an independent
Sage group replay. The ordinary public query reached its frozen
600-second cap with status `BOUNDED_UNKNOWN`; its last flushed restart
was near 671,000 reported conflicts.

## Instance and construction

The field is `GF(2)[u]/(u^131+u^13+u²+u+1)` on
`EC1N131Ckb1heb5f1998f20b`, with curve `y²+xy=x³+1`, fixed seed
mask `898618`, and 28 canonical W29 code bits per pair. The five
pair-output slots have Frobenius rotations `(0,0,36,36,72)`.
The public raw point is
`(877610862732227974378969808549299291499,
2063336771837286479337213121437715536874)`; its fourfold
subgroup point is in the [public protocol](../n131_w23_sixpair_public_sat_20261017/protocol.json).

The [build](build_result.json) retains the earlier five source-inverse
validity constraints, five reciprocal pair quadratics, four balanced
S3 sum links, and the public-target trace parity equation. It adds:

- ten pairwise same-code exclusions;
- 41,860 orientation-specific clauses covering both orders of each of
  the [2,093 valid cross-code folded-orbit collisions](../n131_w29_folded_collision_20261018/RESULT.md)
  for every pair of five slots;
- strict code ordering in the two equal-rotation pairs, `(0,1)` and
  `(3,4)`.

The exact collision list follows from all 524 affine Frobenius
endpoint systems and an independent Sage replay of every enumerated
valid pair. The equal-rotation first-pair identity and two-torsion
charts are excluded by the separately checked
[pair-exception result](../n131_w29_pair_exception_20261018/RESULT.md).
Other intermediate reciprocal charts are not encoded in this formula;
a satisfying model is checked in the full curve group.

| Frozen build measure | Value |
| --- | ---: |
| AND gates / variables | 77,023 / 121,268 |
| CNF clauses / native XOR rows | 274,794 / 42,402 |
| Formula bytes | 20,644,230 |
| Build and constructed-control wall | 35.554 s |
| Build self peak RSS | 221,626,368 B |
| Constructed assignment check | All 274,794 clauses and 42,402 XOR rows |
| Independent constructed group replay | Two matching sign choices; ten distinct folded columns |

The [build protocol](build_protocol.json) froze the source code,
collision table, public point, constructed control, checked
[Sage runtime](sage_runtime_info.json), 240-second build cap and
4-GiB RSS envelope before construction. The independent
[control replay](control_replay.json) reconstructs all ten source
points from the canonical masks and sums the selected rotated pairs
in Sage's curve group.

## Frozen ordinary public query

The [query protocol](query_protocol.json) pins the exact XCNF,
solver binary, input wires, public point, one worker, 590-second
solver limit, 600-second parent wall cap and 4-GiB combined RSS cap.
The raw stdout and stderr streams and [receipt](query_result.json)
retain the cap outcome:

| Charged stage component | Value |
| --- | ---: |
| Target-independent circuit build and constructed-control check | 35.554 s |
| Public query launch, solver search, and parent stop | 600.084 s |
| Build plus public query stage wall | 635.638 s |
| Sampled peak combined query RSS | 457,261,056 B |
| RSS samples / monitor errors | 5,621 / 0 |
| Last flushed restart / approximate conflicts | 1,216 / 671,000 |
| Query status / stop | `BOUNDED_UNKNOWN` / `WALL_CAP` |

The stream has no terminal SAT, UNSAT, or INDETERMINATE line.
This conflict count is bounded solver progress and does not estimate
ordinary relation yield. The prepared [group replay](replay_model_sage.py)
parses a SAT model, checks every source and folded orbit, reconstructs
signed pair outputs, and verifies the raw and fourfold subgroup target.
The [terminal audit](verification_result.json) binds the previously
verified unpinned N41 ordinary relation, the full N131 collision
table, constructed group control, frozen source hashes, and capped
query streams. `candidate_id` remains `null` until a complete IC
pipeline is specified and measured. These wall measurements are
ordinary-host algorithmic diagnostics, without an isolation-tier
speedup claim.

The next discriminator is a compact target-conditioned predicate on
multiple unresolved partial-sum families that preserves the N41
ordinary relation and reduces the N131 public search before branch
enumeration. The paired same-point rho and single-target online
comparison follow a verified N131 relation and complete target
recovery path.
