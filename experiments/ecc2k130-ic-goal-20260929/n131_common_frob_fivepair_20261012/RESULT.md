# Source-bound five-pair query on the transformed N131 public point

**The common-Frobenius five-pair method now has a complete N131 constructed assignment and a frozen unpinned public query.** The constructed formula passes all **1,075,479 CNF clauses and 641,054 native-XOR rows** on independently checked Sage source points. The public formula keeps ten W18 masks and all four transformed raw target fibers free. It built inside the one-worker, 4-GiB envelope and searched until the **600-second parent cap**, with process status `PARENT_TIME_CAP` and mathematical outcome `BOUNDED_UNKNOWN`. The public solver stream contains no SAT/UNSAT terminal line.

## Instance and circuit

The curve is `EC1N131Ckb1heb5f1998f20b` over `GF(2)[t]/(t^131+t^13+t²+t+1)`, with equation `y²+xy=x³+1`, subgroup order `680564733841876926932320129493409985129`, and frozen workload `cc09e7eb202a`. The public point is `(1052727368764798954359115163823647684025,2071227447786120917960296877345506689833)`. The preceding [checked target projection](../n41_common_frob_factor_20261012/n131_projection_result.json) applies the invertible subgroup map `(1+Frobenius¹⁶)⁻¹` to obtain `Q′=(1011194589287210738281611435711478792573,464867644853173232674848580669299498572)` and checks four raw points whose fourfold projections equal `Q′`.

Each of five free pair blocks chooses two supported W18 diagonal source masks, computes their product, and enforces the exact reciprocal pair equation. Ten masks must occupy ten distinct folded columns. Four upper S3 links combine the five free pair outputs through three nonzero intermediate reciprocals to one of the four transformed raw target preimages. The [circuit](circuit.py) uses the previously audited W18 source BDD, sparse pair multiplication, and native XOR arithmetic. A solver model would still require signed point and quotient-row replay; the constructed control supplies that group-level check for one known assignment.

The [constructed fixture](fixture.json) was produced through the checked repository Sage launcher under [its frozen protocol](fixture_protocol.json). It selects the first nonexceptional ten-mask window among 96 distinct-column source masks, verifies all five signed diagonal pair points, three intermediate sums, their raw total, its subgroup projection, and the factored Frobenius image. The [control protocol](control_protocol.json) froze source and fixture hashes before compiling the formula. The [complete assignment receipt](control_result.json) checks every emitted CNF and XOR row.

| Exact circuit profile | Constructed control | Public query |
| --- | ---: | ---: |
| Variables | 993,071 | 1,002,291 |
| AND gates | 350,789 | 356,208 |
| CNF clauses | 1,075,479 | 1,091,743 |
| Native-XOR rows | 641,054 | 644,851 |
| XCNF bytes | 42,354,147 | 42,767,135 |
| Exact source masks / folded columns | 131,307 / 131,068 | 131,307 / 131,068 |
| Full constructed assignment | `PASS` | — |

## Frozen public attempt and accounting

The [query protocol](query_protocol.json) fixed the code, solver, source support, prior control, exact target and four raw fibers, one worker, **600 seconds total**, a 4-GiB combined RSS ceiling, and CryptoMiniSat's `--maxtime=480` flag before execution. The independent parent enforced the total limit; the solver flag did not produce a terminal response before that parent limit. The public builder reported 23.412 seconds of formula construction and 0.344 seconds of serialization inside its 25.058-second monitored process interval. The solver ran for 574.959 monitored wall seconds, recorded 879 restart rows, and was killed by the parent at the declared cap. Sampled combined RSS peaked at **609,779,712 bytes**.

| Exclusive parent interval | Nanoseconds |
| --- | ---: |
| Target-dependent public build process | 25,058,223,209 |
| Solver process, including capped work | 574,958,555,667 |
| Receipt parsing and bookkeeping | 43,984,290 |
| **Public circuit-plus-solver attempt** | **600,060,763,166** |

The 60.763-ms overrun is the monitor's polling/termination latency. The checked Sage computation of `Q′` and its raw preimages was completed and frozen before this interval; its arithmetic cost was not captured as a phase in this run. The full target-dependent total is therefore **unknown** and exceeds the displayed circuit-plus-solver attempt. This run is a point-decomposition stage (`candidate_id: null`), and local CPU timing is exploratory without an isolation receipt.

The [terminal audit](audit_result.json) rebuilt the control and public formulas byte for byte, repeated the full control assignment check, and verified the saved solver transcript, stop reason, memory cap, and exclusive phase sum. Both original XCNFs remain recoverable from the [deterministic archive](archive_result.json); the [read-only verifier](verify.py) checks every compressed file against its raw hash and the frozen receipts after the raw files were removed. The public formula has no decoded model or group relation row at this cap.

## Next method gate

The N41 common-factor design found an unpinned rank-increasing relation, and the N131 five-pair source has ample exact labeled support under the [source-count bound](../n41_common_frob_factor_20261012/RESULT.md). This query shows that feeding the full source and transformed target to the present Boolean solver does not select a witness within its frozen cap. The next falsifiable change is **output-first, target-conditioned pair proposal**: use the existing 131-by-53 W18 pair inverse to reject proposed outputs before expanding source masks, while at least two partial sums remain jointly constrained by the public target. Freeze an unpinned N41 family-rejection test and a source-bound N131 work projection before another 600-second public query. Any ordinary N131 model then needs independent signed group replay, a novel relation row, and complete relation/linear-algebra/target timing before the single-target rho comparison.
