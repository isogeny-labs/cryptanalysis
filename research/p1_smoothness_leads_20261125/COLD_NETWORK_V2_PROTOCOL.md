# Frozen cold network target correction

This is an explicit amendment to `COLD_NETWORK_PROTOCOL.md`, frozen before
the second run. The first run, `cold_network.json`, remains archived. Its
target `137*G` lies inside the known-scalar precomputation scan range. Even
though scalar 137 was excluded from the relation stream, a nearby stored
point such as `138*G` can identify the target after one shift. Thus that
run's scalar recovery is a contaminated cold comparison and must not be
promoted as independent target recovery. `[pcc:unverified]`

For the new run, change only the target to `R = 7001*G`. Keep the same field,
curve, generator, coordinate bound, isogeny order, sign reduction, sum-table
oracle, ascending known-scalar relation stream, rank rule, and charged counts.
Exclude scalar 7001 from relation collection even though it is expected to
lie beyond every full-rank cutoff. The algorithm may use 7001 only to
construct the fixture and verify the final candidate. Report all six rank
cutoffs, all three descent routes, and whether any queried descent point
matches a known-scalar point already visited during precomputation in its
arm. A match invalidates that route as an independent target check; do not
silently replace the target or ignore the match. `[pcc:unverified]`

This remains a finite group-addition-oracle experiment. Full native F4,
isogeny, and sparse linear-algebra costs are separate subsequent gates.
