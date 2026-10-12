# Nine free W18 pairs share one 524-choice N131 target selector

The exact nine-pair N131 circuit now searches all four raw preimages and all
131 Frobenius conjugates of **one** frozen public point with a single formula.
Its constructed nine-pair assignment satisfies all 802,767 clauses and
286,081 native-XOR rows. Independent checked Sage reconstructed every one
of the 524 choices for both the constructed control and the challenge point,
including the cofactor-four projection and reciprocal encoding. The
ordinary challenge query entered CryptoMiniSat search and ended
`BOUNDED_UNKNOWN` at the frozen 600-second target-dependent wall cap.

The exact field is `GF(2)[t]/(t^131+t^13+t²+t+1)` on
`y²+xy=x³+1`, curve `EC1N131Ckb1heb5f1998f20b`, subgroup order
`680564733841876926932320129493409985129`, cofactor four. The previously
published challenge workload is `cc09e7eb202a`, with public point
`Q=(1052727368764798954359115163823647684025,
2071227447786120917960296877345506689833)`. All nine W18 seed-212
pair selectors are free, at rotations `0,16,...,128`, with 33,191 admissible
canonical source codes per slot. The target-choice wire selects exactly one
of the four raw fibers times 131 conjugates. A relation for `τ^j U_i` pulls
back to `Q` because `[4]U_i=Q` and inverse Frobenius is additive; the
[Lean proof map](PROOF_MAP.md) gives the checked conditional theorem and the
remaining concrete-curve formalization obligation. The full signed-Frobenius
closure of the W18 folded columns has 34,339,816 usable points and 131,068
folded columns under the prior geometry audit.

The exact nine-pair distinct-column source census yields a labeled uniform
raw-point mean upper ceiling of **2,464,063,401.38** after multiplying its
single-fiber mean by 524. Families may overlap, and this count does not
measure fixed-point relation yield. This first formula enforces valid codes
within each pair but leaves cross-slot column reuse to post-model checking;
the [shielded variant](../n131_w18_ninepair_orbit_shield_20261012/PROOF_MAP.md)
adds those exact source constraints in a separately frozen formula.

| Frozen stage measure | Result |
| --- | ---: |
| Variables / AND gates | 510,022 / 221,160 |
| CNF clauses / native-XOR rows | 802,767 / 286,081 |
| Ordinary XCNF bytes / SHA-256 | 24,300,760 / `f3f64528dd6e9e9d31357d91dbef16d526f01e3459dae671ceed50c7e431b121` |
| Target orbit and fibers / formula build / write | 0.210 / 12.298 / 0.073 s |
| Solver search/stop / terminal parse | 587.471 / 0.001 s |
| **All target-dependent attempt wall** | **600.054 s** |
| Sampled peak parent-plus-solver RSS | 921,534,464 B |
| Actual restart rows / terminal status lines | 2,488 / 0 |
| Exit classification | `BOUNDED_UNKNOWN`, `TOTAL_QUERY_TIMEOUT` |

The [protocol](protocol.json) fixes the one-worker 600-second total cap,
4-GiB combined RSS cap, target and source hashes, solver binary, and flags
before the query. The [ordinary receipt](query_result.json) charges every
target-dependent phase, and the [audit](audit_result.json) rebuilds the
ordinary XCNF byte for byte, checks the phase sum and source hashes, and
confirms search began with empty stderr. The frozen runner field named
`restart_rows` counts 1,530 bracketed diagnostic lines; the audit separately
reports the actual 2,488 `c rst` lines without altering the raw receipt.
The [archive receipt](archive_receipt.json) binds deterministic gzip copies
of both XCNF files to their original SHA-256 hashes and byte counts; run
`python3 -B archive.py . --verify` here to replay those bytes.
The [Sage audit](sage_audit_result.json) binds the checked runtime and both
524-choice replays. The Lean 4.34.1 module passes with only `propext` and
`Quot.sound` in `#print axioms`.

This is a target-decomposition stage result on a previously used public
point. The next gate is the separately frozen exact distinct-column shield
on the same point, followed by an unseen N131 point only if the source
restriction or a compressed target-conditioned join produces a fully
replayed ordinary relation. `candidate_id` remains `null` while verified
relation rank, factor logs, scalar recovery, and same-point rho accounting
are outstanding. Local wall timings are exploratory on this unisolated host.
