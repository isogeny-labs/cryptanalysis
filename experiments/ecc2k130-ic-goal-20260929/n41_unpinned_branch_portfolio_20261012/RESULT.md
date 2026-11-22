# Branch-first portfolios cover the frozen N41 public formula under exact caps

Two one-worker branch-first portfolios were applied to the source-bound
N41 public XCNF with **all eight source masks free**. The file-per-slice
portfolio examined all 128 root patterns in **182.572 seconds total wall**;
each slice reached its short cap and the aggregate status is
`BOUNDED_UNKNOWN`. An incremental CryptoMiniSat harness loaded the native-XOR
formula once and reached patterns `0–79` in **190.071 seconds**, also
`BOUNDED_UNKNOWN`. Its fully pinned control solved pattern 73 in 1.058
seconds total and an independent parser checked its returned model against
every clause and XOR row. The evidence identifies source-mask selection,
after branch choice, as the unresolved search stage at these caps.

## Instance and exact coverage

- Curve: `EC1N41Ckb1h7d5e80d3c4d0`,
  `GF(2)[t]/(t^41+t^3+1)`, `y²+xy=x³+1`, subgroup order
  `549756390943`, cofactor four.
- Frozen public point: `(920359962848,755404565011)`; the formula binds
  the specified raw preimage reciprocal `344545435656`.
- Base XCNF: 217,778 variables, 361,813 CNF clauses, 97,546 native XOR
  rows. Each slice fixes seven root branch bits; no source mask or source
  pair is fixed. Branch order is numeric `0–127`, independent of the known
  positive chart. Candidate ID is null because this is a PDP stage.

| Run | Input loading | Charged interval | Coverage | Status | Peak combined RSS |
| --- | ---: | ---: | --- | --- | ---: |
| File-per-slice, one CLI process per branch | Repeated per slice | 182.572 s total including XCNF generation and all solver calls | All 128 patterns | 128 `BOUNDED_UNKNOWN` slices; aggregate `BOUNDED_UNKNOWN` | 131,792,896 B maximum |
| Incremental fully pinned control | 0.677 s within total | 1.058 s total | Known source masks, root pattern 73 | SAT; full model replay passed | 114,098,176 B |
| Incremental public query | 0.580 s within total | 190.071 s total | Patterns `0–79` | 80 `UNKNOWN` solves, parent `WALL_CAP`; aggregate `BOUNDED_UNKNOWN` | 182,370,304 B |

The file-per-slice [protocol](protocol.json) fixes the public formula and
solver hashes, order, one worker, 1.25-second per-slice parent cap,
190-second total cap and 4-GiB RSS cap. Its
[journal](slices.jsonl) retains all 128 input, stdout and stderr hashes,
individual timing and stop reasons; [audit.json](audit.json) verifies the
frozen source and every returned receipt. The observed aggregate remains
unknown because no slice supplied SAT or UNSAT under its cap.
Of the 182.572 seconds, recorded XCNF writes sum to 15.629 seconds and
solver calls to 165.543 seconds; the remaining time is parent bookkeeping.
The parent stopped 126 slices at their cap, while two returned without a
SAT/UNSAT terminal.

The incremental [protocol](incremental_protocol.json) hashes the C++ source,
compiled binary, installed CryptoMiniSat library and both exact formulas.
The harness uses the documented incremental assumption API, parses every
native-XOR row once, and calls `solve` serially with a one-CPU-second limit
per pattern. The parent enforces 190 seconds wall and 4 GiB combined RSS
for the public query. [control_audit.json](control_audit.json) independently
checks the SAT model against all 361,877 CNF clauses and 97,546 XOR rows
of the pinned control, plus the seven branch assumptions. The source-mask
and branch choices coincide with the independently checked
[Sage group chart](../n41_allseed_fourpair_forward_20261012/audit_result.json).
The [public receipt](query_result.json) and
[audit](query_audit.json) retain the 80 attempted patterns, loaded-row
counts, peak RSS, exact cap, stdout/stderr hashes, and terminal status.

The run is a point-decomposition stage measurement. Its intervals include
target-dependent search but do not include a recovered scalar or final
relation-matrix solve. CPU wall measurements are exploratory on this
unisolated host and are not an IC/rho ratio. The one-CPU-second solver limit
does not imply one wall second on a contended host; later incremental slices
show wider wall times in the raw log. All 48 unattempted root patterns in
the incremental run remain unclassified.

## Next constraint

The fixed-source branch portfolio already resolves every root pattern
quickly, while both public portfolios leave mask selection unresolved.
The next source-bound solver should index exact pair sums before entering
the seven-link field circuit, then use the public target to reject two
partial-sum families jointly. Freeze an N41 ordinary query first and
measure verified relation yield, index size, source-mask coverage and total
target-dependent work against the existing direct four-pair join. Only a
passing unpinned N41 gate warrants an N131 public-query promotion under
the 600-second/4-GiB envelope. Output-only affine and quadratic filters
are excluded by the earlier complete N41 rank censuses.
