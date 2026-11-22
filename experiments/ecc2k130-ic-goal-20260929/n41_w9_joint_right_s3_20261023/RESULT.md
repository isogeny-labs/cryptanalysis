# An alternate target-linked S3 association preserves the N41 relation but raises solver work

An exact **joint right-family constraint** was added to the aligned five-pair N41 circuit. It introduces the reciprocal of the sum of the last two pair outputs and links that sum directly to the public target and the first-three-pair partial sum. Both implementations preserve the archived ordinary relation. On the 33-row frozen control panel, the target link vanishes for the relation and for none of the 32 source-valid controls. The existing preceding gate makes the same 1-of-33 split on this panel, so it does not establish additional rejection. Independent Sage group arithmetic agrees with every emitted circuit gate.

The fixed-work solver result is unfavorable. At the frozen 20,000-conflict boundary, the baseline used **31,602 decisions** and about **36 million** reported propagations. The compact joint circuit used **35,089 decisions** and about **79 million** propagations in both ABBA arms. Removing the old quartic made the formula slightly smaller than baseline, but did not improve propagation or decisions. This result redirects the next iteration toward a compact *family* predicate evaluated before introducing extra partial-coordinate variables.

## Exact instance and two circuits

The field is `GF(2)[u]/(u^41+u³+1)` on `E: y²+xy=x³+1`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`. The aligned W9 source has 71 canonical pair codes and four signed states per code in each of five slots, with rotations `(0,0,12,12,24)`. The public point at frozen Frobenius orientation 6 is `(1936680952394,910597499030)`; its raw preimage is `(2026560328086,1928332930914)`. The independently replayed relation uses state IDs `(105,244,66,47,111)`.

Let `z` be the reciprocal of the first-three-pair sum, `u,v` the reciprocals of the last two pair outputs, `y` the reciprocal of their sum, and `t` the public-point reciprocal. In the nonexceptional chart, the new necessary equations are `S₃(u,v,y)=0` and `S₃(z,y,t)=0`. The circuit also constrains `u` by its fixed-seed source quadratic. One version retains the previous quartic for the preceding pair; the compact version replaces that quartic with its explicit pair quadratic and `S₃(z,u,w)=0`. The new target link therefore binds the two still-free right source families through one shared partial sum. A complete point-decomposition solver needs a separate path for source assignments whose right sum has no reciprocal x coordinate.

The 33 frozen panel rows have distinct source columns and defined reciprocal coordinates for the alternate right sum. The first row is the archived relation. The other 32 use a frozen target-side `w` root that can differ from the actual first-four-pair sum; the initial control producer incorrectly equated them and stopped. [The failure receipt](freeze_failure_v1.json) retains that assertion and source digest. The corrected frozen controls and independent [group audit](audit_result.json) keep those two coordinates separate. Both `S₃(u,v,y)` and the source quadratic hold on all 33 rows; `S₃(z,y,t)` holds only on the relation row. Both builders check the positive assignment against all clauses and native XOR rows.

| Circuit | AND gates | Variables | Clauses | Native XOR rows | Formula bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Frozen baseline final-pair quadratic | 111,680 | 128,017 | 336,899 | 16,174 | 11,020,550 |
| Joint with previous quartic retained | 120,495 | 138,185 | 363,508 | 17,445 | 11,602,670 |
| Compact joint, preceding quartic replaced | **110,073** | **126,515** | **332,201** | 16,197 | **10,826,624** |

## Frozen fixed-work probes

Both ABBA protocols use the same public point and source, one CryptoMiniSat 5.14.7 worker, a requested 20,000-conflict boundary, 180-second parent wall cap per arm, and 4-GiB combined RSS cap. Every completed arm ended `INDETERMINATE_CONFLICT_CAP`; no arm returned a SAT or UNSAT line. Values below are stage diagnostics on an ordinary shared host.

| Comparison and arm order | Decisions | Reported propagations | Parent wall seconds | Sampled combined peak RSS |
| --- | ---: | ---: | ---: | ---: |
| Retained-quartic probe: baseline 1/4 | 31,602 / 31,602 | 36M / 36M | 1.445 / 1.237 | 128.8 / 129.7 MB |
| Retained-quartic probe: joint 2/3 | 34,472 / 34,472 | 77M / 77M | 2.463 / 2.476 | 161.4 / 162.0 MB |
| Compact retry: baseline 1/4 | 31,602 / 31,602 | 36M / 36M | 1.228 / 1.246 | 116.8 / 117.9 MB |
| Compact retry: joint 2/3 | 35,089 / 35,089 | 79M / 79M | 2.461 / 2.475 | 127.5 / 126.7 MB |

The first compact probe's monitor lost process-control authority after its second arm printed `s INDETERMINATE`; its exact exit code and combined RSS peak remain unknown in [the failure receipt](compact_probe_failure_v1.json). The retry used a fresh frozen protocol, distinct raw streams, direct-child termination, and a process-control environment in which all four arms had healthy monitors. The predeclared promotion gate required both joint arms to use at most 90% of adjacent baseline decisions and at most 125% of their wall time. The retained-quartic circuit used 109% of baseline decisions; the compact circuit used 111%. Their wall readings were also above the threshold. The gate therefore stops promotion of these two encodings to the frozen N131 public query. The current stage has `candidate_id: null`.

## Reproduction and next discriminator

The checked repository Sage launcher produced [sage_runtime_info.json](sage_runtime_info.json) before the group controls and audit. [JointAssociation.lean](JointAssociation.lean) proves the regrouping and conditional target-link implication; [PROOF_MAP.md](PROOF_MAP.md) records the concrete chart bridge. Run `python3 verify.py` for a read-only check of the frozen sources, formula hashes, control decisions, probe statuses, monitor receipts, Lean output, and gate verdict.

The next experiment should eliminate or screen the right two-pair family **without allocating the extra 82 reciprocal-coordinate bits** used here. It must show a complete whole-family rejection rule on an unpinned N41 public query, with all failed work charged, before a source-bound N131 projection. The broader goal's N131 ordinary-relation, useful-rank, and matched one-target rho gates remain active.
