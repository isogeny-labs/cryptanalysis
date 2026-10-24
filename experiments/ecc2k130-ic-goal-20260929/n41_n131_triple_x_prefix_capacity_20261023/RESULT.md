# Triple-sum x-affine capacity across source-code prefixes

The x-coordinate affine hull of a three-pair source family filled the N41 field after **two** first-slot codes and the N131 field after **five** first-slot codes on frozen, source-valid panels. This gives an exact capacity boundary for the linear whole-family screen on those panels. The N131 frozen public residual is rejected by the hull through four codes; with the fifth, the hull accepts every field element while exact x-coordinate membership still rejects that residual.

| Field and first-slot code families pooled | 1 | 2 | 3 | 4 | 5 | 6–8 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| N41 affine rank of triple-sum x values | 31 | **41** | 41 | 41 | 41 | 41 |
| N131 affine rank of triple-sum x values | 31 | 63 | 95 | 127 | **131** | — |
| N131 frozen public residual in the hull | no | no | no | no | **yes** | — |
| N131 frozen public residual in the exact x set | no | no | no | no | **no** | — |

Each individual code triple has 64 signed source-state combinations and exactly 32 distinct x coordinates. The N41 first-slot masks are `[217,2,3,5,6,7,16,18]`, with masks 196 and 157 fixed in slots 1 and 2. Mask 217 belongs to the independently audited public relation; its target residual appears in the first 32-coordinate set. The N131 W23 first-slot mask pairs are `(3,898617)`, `(10,898608)`, `(41,898579)`, `(46,898580)`, and `(47,898581)`, with archived edges 1 and 2 fixed in the next slots. The fifth pair is the first source-valid, folded-column-disjoint choice after mask 46 under the frozen ascending rule. A constructed six-pair sum supplies the positive target control. The ordinary N131 raw public point comes from the frozen W23 protocol; a second archived public point is also evaluated.

For each prefix of first-slot codes, the worker unions its exact triple-sum x values and computes the GF(2) rank of all differences from one base coordinate. A target residual can be an exact group match only if its x coordinate lies in that affine hull. Once rank equals the field degree, that linear condition accepts every x coordinate; the full exact set may still reject. This is the point at which a linear affine summary loses pruning on the measured panel.

## Frozen measurements and correction

The corrected checked-Sage worker took **1.461 seconds** inside its measured interval and reported 262,144,000 bytes of process peak RSS on this host. The interval starts after frozen-input hash checks and includes source reconstruction, all group sums, ranks, target residuals, and artifact writes. The protocol declared one worker and a 120-second alarm; memory was observed but not host-enforced. These are ordinary-host component diagnostics, with `candidate_id: null`. The independent Sage matrix audit took 0.031 seconds inside its own interval and recomputed 13 prefix ranks and 23 target-membership decisions from the retained x-coordinate sets.

The first frozen producer stopped after computing ranks because it incorrectly treated an archived N131 public point as a constructed positive sum. Its [failure receipt](failure_v1.json) and source remain intact. A pre-run v2 freeze then referenced a nonexistent `protocol_v2.json` in a prior directory; its [freeze failure](freeze_failure_v2.json) is also retained. The corrected v2 protocol derives the positive target by adding the six archived source states and keeps both public points separate. The N41 public relation control and N131 constructed control pass exact x membership at the first prefix.

## Algorithmic consequence and next gate

The N41 and N131 rank sequences are exact for these selected panels. They do not assert that every W23 or W29 prefix saturates at the same size. They show that simply widening a first-code family can erase the strong affine rejection previously measured for fixed three-code families. A scalable projector must obtain more than one field-linear feature from each partial sum, or use an algebraic condition that retains structure after the affine hull fills.

The next cheapest test is a quadratic coordinate-feature hull on these same frozen x sets, followed by an extension to enough source-valid codes to locate its saturation point. Charge feature construction, rank updates, and target tests, then compare the required block count and per-block work with the one-worker N131 budget. The N41 unpinned relation and N131 ordinary-relation promotion rules remain in force for any candidate built from that feature.

Run `python3 verify.py` in this directory for the hash and status audit. The checked-Sage runtime is in `sage_runtime_info.json`; `protocol_v2.json`, `result_v2.json`, `x_sets_v2.json`, `audit_protocol.json`, and `audit_result.json` retain exact inputs, coordinates, and outcomes.
