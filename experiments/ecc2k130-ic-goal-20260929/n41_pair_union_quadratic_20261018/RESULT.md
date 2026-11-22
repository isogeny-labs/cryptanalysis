# Full quadratic rank of N41 three-code pair unions

**All 1,554 admissible first-two-code pairs have full rank 862 in the
degree-at-most-two Boolean feature space of their complete third-code
output unions.** Thus, for this frozen W8 source, no nonzero quadratic
equation in the 41 bits of the raw-sum x-coordinate vanishes on every
output of any admissible pair union. The native census used one worker,
9.123 seconds of parent wall, and 25,460,736 bytes sampled combined
peak RSS. Three independent checked-Sage unions, including the
verified ordinary relation's pair `(24,37)`, reproduced the output
counts and full quadratic ranks.

The exact curve is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[t]/(t^41+t^3+1)`, with `y^2+xy=x^3+1`, subgroup order
`549756390943`, and cofactor four. The source is the frozen W8,
seed-56, seven-slot construction from the [ordinary N41 relation
control](../n41_w8_fixedseed_ordinary_join_20261013/RESULT.md).
The first three slots have 40 source codes each, four signed states
per code, and a six-distinct-folded-column condition. The native
program used the same exact field/group arithmetic and checked the
128 exported Sage addition references before its census.

For an output coordinate `x`, the row contains `1`, all 41 bit
coordinates `x_i`, and the 820 distinct products `x_i*x_j` for `i<j`:
`1+41+820=862` columns. For each fixed pair `(a,b)`, the census freed
every admissible third code and inserted its 32 sign-quotiented x
values into a binary row basis. A full column rank leaves only the
zero coefficient vector in the kernel, so there is no quadratic
whole-pair predicate to test against a target residual. The
[checked Lean theorem](NoQuadraticFilter.lean) proves the structural
full-span implication; the concrete feature/rank bridge is recorded
in the [proof map](PROOF_MAP.md).

| Panel | Admissible pairs | Empty pairs | Valid code triples | Quadratic rank |
| --- | ---: | ---: | ---: | ---: |
| Full native census | **1,554** | 46 | **58,596** | 862 for every admissible pair |
| Checked-Sage pair `(0,1)` | 1 | — | 38 | 862; first full at third code 28 |
| Checked-Sage pair `(0,2)` | 1 | — | 37 | 862; first full at third code 29 |
| Checked-Sage witness pair `(24,37)` | 1 | — | 38 | 862; first full at third code 27 |

The native rank reached 862 by third-code index 26–31 across all
admissible pairs. The full census generated 1,353,408 feature rows
before short-circuiting pairs whose rank was already 862. This is
valid because adding the remaining outputs cannot lower rank. The
separate Sage panel retained all 1,184–1,216 distinct x values per
pair and found full rank after 864 values in each case. A pure-Python
verifier recomputes those three ranks from the saved x-coordinate
lists and checks every native pair row against the frozen counts.

| Measured item | Result | Timing boundary |
| --- | ---: | --- |
| Full native census parent wall | 9.123 s | Checked-Sage wrapper after startup; includes child process and monitor |
| Full native sampled combined peak RSS | 25,460,736 B | Parent plus child, 4-GiB cap |
| Sage sample arithmetic and rank | 2.239 s | Inside checked-Sage process, excludes launcher startup |
| Sage sample peak self RSS | 261,996,544 B | Self resource high-water mark |

The [full protocol](full_protocol.json) froze source/binary/input
hashes, one worker, an 180-second parent cap and 4-GiB combined RSS
cap before the run. The [native receipt](full_result.json) retains all
1,600 pair rows, stdout/stderr hashes, exit status, wall, and sampled
RSS. The [build receipt](build_receipt.json) records the compiler
command, version hash, source hash and executed binary hash. The
[sample protocol](protocol.json), [Sage result](result.json),
and checked [runtime](sage_runtime_info.json) bind the three
independent controls. `python3 verify.py` passes and reports 1,554
full-rank pairs. These ordinary-host timings are algorithmic
diagnostics, with `candidate_id: null`.

The earlier affine-rank census showed that freeing the third code
removes affine screens. This census closes the next degree: freeing
the third code also removes every quadratic x-coordinate screen on
each complete first-two-code family. The next target-conditioned
construction should couple two unresolved partial sums, or use a
source-aware feature that does not require a literal table for each
first-code pair. Any N131 promotion still needs a source-bound
600-second/4-GiB projection, an unpinned ordinary relation, and
independent group/column replay.
