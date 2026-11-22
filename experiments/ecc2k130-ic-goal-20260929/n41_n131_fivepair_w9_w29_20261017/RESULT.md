# Five-pair W9/W29 target-conditioned source and join

An **unpinned five-pair source found an ordinary relation on the archived N41
public point**. The exact three-plus-two native join hit at Frobenius
orientation 3 after 20.629 seconds inside the worker (22.410 seconds parent
wall inside the checked-Sage runner, including input validation and monitoring).
Independent checked
Sage reconstructed all ten signed leaves from their masks, verified ten
distinct folded columns, transported the sum back through inverse
Frobenius, and matched raw point `(2026560328086,1928332930914)` and
cofactor-four subgroup point `(1654986373106,1310318707590)`. This is a
complete point-decomposition relation control for the wider five-pair
topology.

The corresponding W29 N131 five-pair circuit uses **76,859 AND gates**,
**121,204 variables**, **232,429 clauses**, and **42,502 native XOR rows**
on the frozen public workload. Its constructed control satisfies every
clause and XOR row; an independent Sage group replay finds one complete
signed combination and ten distinct columns. The prior W23 six-pair
circuit used 86,937 AND gates and 263,060 clauses on this same public
point. The 10,078-AND and 30,631-clause reductions change both source
width and summand count, so they are circuit-size diagnostics for a new
source, not paired solver speedups.

## Source and N41 public relation

The field is `GF(2)[t]/(t^41+t^3+1)` and the curve is
`y²+xy=x³+1`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`. The W9 mask
`a` represents `w=a·t` in the declared polynomial basis. An endpoint is
admissible when `Tr(w)=Tr(1/w)=0`; the fixed seed is mask 56. The exact
checked-Sage census found **259 admissible masks**, **71 usable canonical
seed edges**, and **251 orbit labels among the admissible masks**. The
edges use 142 endpoint masks occupying 139 of those labels. Each of the
five slots has 284 signed states after rotations `(0,6,12,18,24)`.

The native worker hashed all **21,868,032** internally column-disjoint
left triples, then queried right pairs with the target-conditioned key
`target−right`. The first raw orientation completed all **79,424**
column-disjoint right pairs without a hit. A separately frozen orbit run
reused one left table across successive Frobenius target orientations.
Orientations 0, 1, and 2 completed; orientation 3 hit after **79,297**
right probes in that orientation, with state IDs `(0,130,233,283,152)`.
The run used one native worker and sampled **1,286,029,312 bytes** peak
worker RSS, below its 4-GiB cap. The [relation replay](orbit_audit_result.json)
checks the source trace law, every leaf and pair sum, the fixed-seed
quadratic, all ten columns, the target-orbit sum, inverse transport, and
the declared subgroup target.

The first run's parent monitor lost macOS process-list permission after
launch. Its native worker completed the raw orientation; the frozen stdout,
empty stderr, confirmed terminal process state, and independent source
triple/pair recount support the `COMPLETE_MISS` row in
[`single_result.json`](single_result.json). The unknown native exit code
and monitor failure remain explicit in [MONITOR_FAILURE.md](MONITOR_FAILURE.md).
The orbit run has separate source, binary, protocol, raw logs, and receipt.

## W29 source and constructed circuit

For N131 the field is `GF(2)[t]/(t^131+t^13+t²+t+1)`, the curve is
`y²+xy=x³+1`, and the prime subgroup order is
`680564733841876926932320129493409985129`. The W29 mask uses the same
polynomial coordinate rule with seed 898618; clearing its highest seed bit
leaves 28 free canonical mask bits. Five pair slots have rotations
`(0,18,36,54,72)`. A frozen SplitMix64 sample of 65,536 distinct
canonical masks found **16,677** pairs with both endpoint inverse traces
zero and **zero** same-column pairs. An independent checked-Sage replay of
all 131,072 inversions, trace tests, and surviving orbit comparisons
matched every count. Scaling the observed sample fraction to the full
`2^28` canonical-mask domain gives **68,308,992** edges as a sample-based
projection; it is not a census or an actual factor-base count.

Each N131 circuit enforces the exact product-inverse source law,
`(1+h²)z²+pz+h²=0` for each pair output reciprocal, and four S3 links
to the target reciprocal. The four-plus-one links are
`(0,1,5),(2,3,6),(5,6,7),(7,4,8)`; the three-plus-two links are
`(0,1,5),(5,2,6),(3,4,7),(6,7,8)`. Both constructed controls have the
same five source pairs and raw target. Their complete assignments pass
232,429 clauses and 42,502 XOR rows. The three-plus-two public formula
has identical structural counts, while its different incidence changes
the exact XCNF hash.

## Same-point N131 public-point search

The N131 workload ID is `cc09e7eb202a`; its subgroup target is
`(1052727368764798954359115163823647684025,
2071227447786120917960296877345506689833)`. Both topologies use the
archived raw preimage zero and its **standard reciprocal** x coordinate
`770794657550069419943936485965613853151`. Each full query has one
CryptoMiniSat worker, a 600-second target-dependent cap, and a 4-GiB
combined-RSS cap. Formula construction and serialization are charged
inside that target-dependent interval.

| Frozen W29 topology | Public result | Target-dependent seconds | Peak combined RSS | Solver restarts |
| --- | --- | ---: | ---: | ---: |
| Four-plus-one | `BOUNDED_UNKNOWN` at parent cap; no SAT/UNSAT line | 595.045 | 541,933,568 B | 3,454 |
| Three-plus-two | `BOUNDED_UNKNOWN` at parent cap; no SAT/UNSAT line | 595.039 | 488,374,272 B | 3,024 |

The four-plus-one phase record charges 0.006 s target conversion, 2.482 s
formula construction, 0.007 s serialization, 592.547 s solver search and
stop, and 0.003 s terminal parsing. The exact nanosecond sum and raw logs
are in [n131_query_result.json](n131_query_result.json). The three-plus-two
record charges 0.004 s conversion, 2.601 s construction, 0.021 s
serialization, 592.410 s search and stop, and 0.003 s terminal parsing.
Both capped solver rows stay censored; neither is counted as a
relation-yield observation. The independently frozen
[terminal audit](verification.json) checks both query protocol hashes, formula
hashes, all 232,429 CNF and 42,502 XOR rows per XCNF, raw solver logs,
single-worker resource limits, target binding, and exact phase sums.

At a separate fixed 100,000-conflict diagnostic boundary, both layouts
ended `INDETERMINATE` with 336 restart rows. In first order,
three-plus-two took 7.382 s and four-plus-one 10.423 s. In reversed order,
four-plus-one took 9.706 s and three-plus-two 6.449 s. The independent
[topology log audit](topology_audit_result.json) checks both formulas,
100,001/100,002 recorded conflicts respectively, terminal status, raw
logs, and a benign direct-PID monitor race after the second reversed run
exited normally. These ordinary-host conflict screens select a layout for
a full query; they are not isolated full-solve timing evidence.

## Proof and reproducibility

The pinned Lean 4.34.1 [proof map](PROOF_MAP.md) covers the two exact
five-pair addition trees, three-plus-two target lookup, and transport of
an orbit hit through an additive inverse map. `lean_v2.stdout` records
axiom-free `#print axioms` output for all four theorems. Existing checked
pair-output and shared-inverse lemmas cover the other structural field
identities; the concrete curve and circuit bridges are checked by Sage
reconstruction and complete assignment evaluation.

All new local Sage jobs used the repository's checked `./sage` launcher;
its saved runtime receipt is `sage_runtime_info.json`. The native source,
join, sample, full public queries, topology probes, and independent audits
retain their own code, input hashes, caps, raw output, and result JSON in
this directory. The CPU wall measurements here are ordinary-host stage
diagnostics. `candidate_id` remains null while exact W29 factor-base
enumeration, full relation matrix and rank, target descent, and paired
same-point rho are unresolved.

## Next algorithmic gate

The balanced addition tree was quicker in both fixed-conflict screens, yet
its complete capped public query also remained `BOUNDED_UNKNOWN`.
The next test should change the source-to-target search constraint itself.
A concrete option is to retain exact inverse-trace eligibility in three
W29 pair slots and defer the remaining two eligibility checks to an
independent model audit, adding exact exclusion cuts for failed models.
The measured source sample gives a roughly `(16677/65536)^2 ≈ 6.48%`
two-slot eligibility fraction for uniformly drawn canonical masks; this
is a sampling projection, not a model-yield prediction. Freeze and test
the same policy first on the unpinned N41 public point, accounting for
all rejected models and source checks, before another one-worker N131
public query. A target-conditioned partial-sum family predicate that
prunes before source-state enumeration remains the broader algorithmic
requirement.
