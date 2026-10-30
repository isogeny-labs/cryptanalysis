# Pair indexing reproduces every four-source D79 relation with far fewer group operations

The new pure-Python pair-index enumerator returned exactly the same signed support-at-most-four relation sets as the pinned exhaustive enumerator in **30 of 30 paired replays** across ten sealed D79 classes. Across the classes, each exhaustive pass tested 772,240 signed supports and made about 3.05 million group additions. The index inserted 3,120 signed distinct pairs and made 3,120 complement-bucket probes; its measured group-add count was 9,480–10,136. Every derived class row was checked in the group, including zero-row cases.

| p | Verified rows | Exhaustive median interval (ms) | Pair-index median interval (ms) | Exploratory interval ratio |
| ---: | ---: | ---: | ---: | ---: |
| 102077 | 202 | 1704.34 | 10.86 | 156.9 |
| 103357 | 218 | 1640.42 | 9.23 | 177.7 |
| 108557 | 198 | 1633.28 | 12.10 | 134.9 |
| 115237 | 199 | 1668.55 | 8.13 | 205.3 |
| 122117 | 196 | 1668.78 | 8.45 | 197.6 |
| 123517 | 208 | 1638.42 | 8.53 | 192.0 |
| 129197 | 195 | 1682.05 | 8.68 | 193.8 |
| 137957 | 198 | 1678.94 | 8.44 | 199.0 |
| 145477 | 199 | 1700.47 | 8.15 | 208.5 |
| 151637 | 190 | 1673.02 | 8.20 | 204.1 |

The median of the ten paired median interval ratios is 195.7. The group-add reduction is 301–322 fold by exact instrumented calls. Both methods used the same Python curve group law, source-equation verification, row construction, and final row-group verification. The interval comparison is **exploratory on this local host** because no Tier 0 or Tier 1 CPU isolation receipt was collected. It establishes a component implementation improvement and exact-output identity on these inputs; it is not a single-target online measurement. `candidate_id` and `target_online_ms` remain null.

The match is output-sensitive: hash buckets hold O(s²) signed pairs for s sources, and complement lookups avoid the exhaustive O(s⁴) signed-support scan when the number of matching candidates is moderate. The formal group identities and written strict-index proof are mapped in `PROOF_MAP.md`. The first benchmark attempt stopped at a mismatch between prior audit schema field names after the earlier cases; its partial result and stderr are retained. The corrected code and input seal preceded the complete 30-pair run. Raw per-pair intervals, exact operation counts, digests, status, and peak RSS are in `result.json`.

The next implementation step is to use the pair index in a rank-stopped source collector and test it prospectively on fresh classes. That run must charge source lifts, index updates, rank checks, and worker effects before making a scheduler-level wall-time comparison.
