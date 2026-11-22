# Exact functional S3 branches on the N41 W11 public orbit

The four-pair orbit circuit now computes each of its two intermediate S3 roots from a branch bit and exact field inverse witnesses, including the exceptional linear chart. All **32** independently verified relations on the frozen N41 public point satisfy the regenerated formula: each complete assignment passes **102,722 CNF clauses and 4,308 native XOR rows**. The unpinned one-thread CryptoMiniSat query then reached its 590.021 s parent wall cap with status `WALL_CAP`, no terminal SAT or UNSAT line, and 422,969,344 B sampled combined peak RSS. The result preserves the public relations and bounds this solver representation; it directs the next experiment to reject source-code families before expanding S3 roots.

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[u]/(u^41+u^3+1)`, with `y²+xy=x³+1`, subgroup order `549756390943`, cofactor four, and raw public point `(1936680952394, 910597499030)`. The W11 source has 281 eligible codes, 1,124 distinct subgroup-usable points, and 557 folded columns; four pair slots use Frobenius rotations `[0,12,24,36]`. The target selector covers all 41 orientations. The source input, earlier exact 32-relation census, and independent Sage replay are linked by the hashes in the frozen protocols. `candidate_id` is `null` for this point-decomposition component.

For input pair reciprocals `a,b`, the S3 output `z` obeys `A z²+B z+D=0` with `A=(ab)²+1`, `B=ab`, and `D=(a+b)²`. Since the circuit requires nonzero reciprocals, `B≠0`. On `A≠0`, it computes `q=A D/B²`, imposes `Tr(q)=0`, takes the trace-shifted half-trace root `h` of `h²+h=q`, and chooses `z=(B/A)(h+e)` with one bit `e`. On `A=0`, it selects the exact linear root `D/B`. The witness equations in [the proof map](PROOF_MAP.md) specify the branch and inverse guards; Lean 4.34.1 checks soundness and completeness of both algebraic cases under explicit characteristic-two, inverse, and half-trace hypotheses.

The [chart audit](chart_result.json) reconstructed all 32 public group sums and checked their 96 S3 equations and root branches; the preceding archive contains their independent Sage replay. All 96 used the ordinary quadratic chart. The [assignment audit](all_witnesses_result.json) regenerated the circuit to the exact saved formula SHA-256 and evaluated a full assignment for every relation. Its first hash-check rerun passed a string to an API requiring a `Path`; [that stderr](all_witnesses_attempt2.stderr) is retained, and the corrected audit passed. The checked repository Sage launcher supplied the runtime receipt before circuit construction and audit runs.

| Same frozen W11 source and public orbit | Earlier free-middle circuit | Functional-S3 circuit |
| --- | ---: | ---: |
| Variables | 16,224 | 38,858 |
| AND gates | 13,426 | 33,926 |
| CNF clauses | 40,810 | 102,722 |
| Native XOR rows | 2,342 | 4,308 |
| Archived public assignments checked | 1 | 32 |
| Unpinned solver status | `WALL_CAP` | `WALL_CAP` |
| Parent solver wall | 590.024 s | 590.021 s |
| Sampled combined peak RSS | 393,969,664 B | 422,969,344 B |

Both solver runs used one thread, `--maxtime=560`, a 590 s parent cap, and a 4 GiB sampled RSS cap. The functional run's solver exit was `-15` after parent termination. The build took 0.205 s, with 0.081 s for its initial complete-assignment check outside solver wall. These are ordinary-host stage records; equal wall caps provide no relative solver-time measurement. The functional formula is larger and does not clear the unpinned N41 gate, so this representation is not selected for the N131 public query.

`python3 verify.py` returned `PASS_ARCHIVE_VERIFICATION`. It checks frozen source and solver hashes, formula counts, all 32 assignment records, the prior independent census verifier, Lean axiom output, query caps, and the gzip-decompressed solver transcript against the raw SHA-256. The solver transcript is saved as `solver.stdout.gz`; its decompressed bytes match the query receipt.

The next experiment should put an exact target-conditioned restriction on **multiple free source-code families before root enumeration**. The existing 13-term two-product eliminant rejects fixed-left-code families but requires serial left-code specialization on N131. A useful new rule must reject a block of left codes or bind at least three free products at once, retain all 32 W11 relations on this public point, and demonstrate a lower charged search cost than explicit pair-table joining on the N41 gate before an unpinned N131 run. The active end state remains the N131 ordinary relation, then useful rank, factor-base logs, single-target recovery, and matched same-point rho timing.
