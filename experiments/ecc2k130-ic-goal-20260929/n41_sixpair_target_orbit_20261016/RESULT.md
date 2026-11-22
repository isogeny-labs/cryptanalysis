# One-table search across the N41 public target's Frobenius orbit

**One native three-plus-three table produced 41 independently replayed, rank-increasing six-pair relations for the same N41 public point.** It searched all 41 Frobenius conjugates of one raw public preimage in **54.640 s** parent wall, with **248,119,296 bytes** sampled peak combined RSS. Every orbit position yielded a twelve-distinct-column relation; inverse Frobenius and cofactor-four projection carry each to the original public point. Checked Sage rebuilt all twelve source leaves for every hit, verified their group sums, and found rank **41** for the 41 resulting relation rows modulo subgroup order `549756390943`.

## Method and source

The field is `GF(2)[t]/(t^41+t³+1)` and the curve is `y²+xy=x³+1` (`EC1N41Ckb1h7d5e80d3c4d0`). The six source slots use the frozen W8 seed-56 pair graph, rotations `(0,6,12,18,24,30)`, 160 signed states per slot, and twelve-distinct-column rule. The public raw point is `(2026560328086,1928332930914)`; its cofactor-four image is `(1654986373106,1310318707590)`. The 77 folded source columns define a signed-Frobenius-closed projected base of `77 × 2 × 41 = 6,314` distinct usable points. An independent [checked-Sage closure census](closure_audit.json) enumerated all 6,314 projected points and found no cross-column collision. Each orbit hit is pulled back by inverse Frobenius, leaving its folded columns in that base.

The native worker builds the exact 3,750,144-entry left three-slot table once. It then changes only the target to `τ^j U`, probes compatible right triples, and records the first verified hit for each `j=0,…,40`. The first-hit policy yields a **lower bound** on distinct relations available from each orbit position; it does not enumerate all decompositions. The worker made **31,209,000** target-dependent right probes across 41 positions, and its own complete interval was 54.134 s; the monitored parent interval includes launch, input loading, construction, all probes, and exit.

| Frozen N41 stage | Result |
| --- | ---: |
| Orbit positions completed / first hits | 41 / 41 |
| Distinct folded columns per relation | 12 |
| Independent group and cofactor replays | 41 / 41 |
| Rank of transported relation rows over `GF(r)` | 41 |
| Native left-table entries / right probes | 3,750,144 / 31,209,000 |
| Native parent wall / sampled combined peak RSS | 54.640 s / 248,119,296 B |
| Public orbit SAT formula | 28,577 AND gates; 33,351 variables; 88,698 clauses; 3,826 XOR rows |
| Public orbit SAT query | `BOUNDED_UNKNOWN` at 185.111 s parent cap; 3,006 restart rows; 337,379,328 B sampled peak |
| Exact constructed assignments against that public XCNF | 41 / 41, all clauses and XOR rows |

The SAT comparison holds the same six-slot source and public raw preimage as the earlier single-orientation shared-inverse circuit. Selecting one of 41 target reciprocals adds 1,640 AND gates, 1,818 variables, 5,741 clauses, and 137 XOR rows. The baseline and orbit queries both reached their 185-second caps; the cap observations establish neither a solver speed ordering nor an unsatisfiability result. The 41 exact relation assignments demonstrate that this orbit formula has many valid witnesses despite the capped search.

The frozen [SAT protocol](protocol.json) binds source and solver hashes, one worker, 180-second solver limit, 185-second parent cap and 4-GiB RSS cap. The [native join protocol](join_protocol.json) binds its source, binary, input, compiler, one worker, 300-second cap and 4-GiB RSS cap. [Checked Sage](sage_runtime_info.json) independently verifies the full target orbit in [orbit_audit.json](orbit_audit.json), all relations and rank in [join_audit.json](join_audit.json), and every satisfying XCNF assignment in [assignment_audit.json](assignment_audit.json). The [terminal replay](terminal.json) checks statuses, source hashes, row ranks, solver and join transcripts, and Lean output. An initial build with a system Python lacking `psutil` stopped at import before formula construction; its `attempt1_build.stderr.txt` is retained as an environment failure.

## N131 gate

For the archived W23 N131 source, the exact count is 1,049,218 usable pair edges per slot, or 4,196,872 signed states. Its 2,098,179 occupied folded columns expand under signed Frobenius closure to **549,722,898** distinct projected base points. The uniform subgroup-target mean for the six-slot source is between 8.028744720001 and 8.029318656726 labeled relations; summing over all 131 target conjugates makes the corresponding *orbit-summed uniform mean* between **1051.765558320131 and 1051.840744031106**. These are exact source-count consequences, not a measured yield for the frozen public point.

The direct three-slot table still requires **73,922,589,492,632,846,848** labeled states on each side before column filtering. The N41 orbit SAT control reached its cap even with 41 independently verified witnesses, so that solver variant does not pass the N41 promotion gate. The next constructive experiment must retain all target conjugates while rejecting whole W23 code or partial-sum families before three-slot expansion. Its unpinned N41 run must recover and replay a relation with complete target-dependent cost before the one-worker, 600-second, 4-GiB frozen N131 query. This orbit study is a relation-collection component with `candidate_id: null`.
