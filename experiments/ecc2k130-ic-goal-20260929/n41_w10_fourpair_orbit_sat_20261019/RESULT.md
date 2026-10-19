# Exact four-pair orbit circuit and bounded public searches

The W10 four-pair point-decomposition circuit accepts the independently audited N41 public relation as a complete assignment: all 34,602 fixed-orientation clauses and 2,125 native XOR rows pass. A 41-orientation target selector accepts the same relation, and an exhaustive evaluation of all 64 selector codes confirms that codes 0–40 select their respective Frobenius target and codes 41–63 are excluded. Unpinned CryptoMiniSat searches of these formulas ended `BOUNDED_UNKNOWN` at 105.497 s and `WALL_CAP` at 590.016 s, respectively. These measured search boundaries select a stronger source/target coupling for the next iteration.

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[u]/(u^41+u^3+1)` with `y²+xy=x³+1`, cofactor four, subgroup order `549756390943`, and frozen raw public point `(1936680952394, 910597499030)`. The W10 source has seed mask 56, 130 eligible pair codes, 520 distinct subgroup-usable base points, and 255 folded columns. Its four pair rotations are `[0,12,24,36]`. The archived ordinary relation at target orientation 29 has source codes `[177,16,267,284]`; the SAT queries contain its public target and exact source constraints, with no witness assignments pinned.

For each slot, nine free source-code bits determine `a`, `b=a+s`, and their product `p=ab`. The circuit uses one field inverse witness `v` to impose `pv=1` and both endpoint inverse-trace conditions. Its pair-output reciprocal `z=1/x(P+Q)` obeys `Cz²+pz+H=0`. Three balanced S3 links connect the four pair outputs and two intermediate reciprocals to the raw public target. Code inequality and the five additional folded-column conflicts found in the exact W10 base are excluded. The orbit variant adds a six-bit selector and shares the four pair constraints across all 41 Frobenius images of the target.

| Frozen stage | Fixed orientation 29 | Shared 41-orientation circuit |
| --- | ---: | ---: |
| Variables | 13,928 | 15,878 |
| AND gates | 11,357 | 13,098 |
| CNF clauses | 34,602 | 39,826 |
| Native XOR rows | 2,125 | 2,328 |
| Complete archived-relation assignment | Pass | Pass |
| Selector semantic check | — | 41 valid and 23 excluded six-bit codes |
| Unpinned solver status | `BOUNDED_UNKNOWN` | `WALL_CAP` |
| Parent solver wall | 105.497 s | 590.016 s |
| Sampled combined peak RSS | 379,043,840 B | 498,352,128 B |

Both searches used one solver thread and a 4 GiB sampled parent-plus-child RSS cap. The fixed-orientation solver requested `--maxtime=100` under a 110 s parent; it returned without a SAT or UNSAT line. The orbit solver requested `--maxtime=560` under a 590 s parent; the parent terminated it at the declared wall cap, exit `-15`, with no terminal answer. These statuses preserve a satisfiable control formula as censored search outcomes. Formula construction took 0.075 s for the fixed variant and 0.084 s for the orbit variant in their checked-launcher control runs, recorded separately from solver wall. This is an ordinary-host point-decomposition comparison; `candidate_id` remains `null` pending a complete IC pipeline.

The first selector auditor tried to capture the last circuit `linear_element` call, which belonged to later arithmetic rather than the target selector. Its raw assertion stderr is retained as `selector_attempt1.stderr`. The version-two auditor located the target call by its 41 pinned constants and checked all 64 selector settings against the actual emitted Boolean gate definitions. The solver stdout files are archived as `solver.stdout.gz` and `orbit_solver.stdout.gz`; decompression reproduces the exact bytes hashed in the run receipts. `archive_verify.py` checks frozen input and binary hashes, formula headers, control assignment counts, selector result, decompressed solver transcripts, parent caps, and terminal classifications after path relocation. Run `python3 archive_verify.py` from this directory; the final archive check returned `PASS_ARCHIVE_VERIFICATION`.

The next width-controlled experiment is a W11 four-pair orbit circuit on the same public point. Its independently audited source has 281 codes and 1,124 usable base points, and the existing exact join found a relation at orientation 3. The uniform-group relation-count heuristic rises by about `(1124/520)^4 ≈ 21.8` relative to W10, so this is a concrete test of whether solution density changes SAT search. Freeze the W11 circuit, validate a complete public assignment and all selector values, then search under the same one-worker, 600 s, 4 GiB cap. A successful unpinned W11 solver result would permit a measured N131 W33/W34 circuit projection; the N131 ordinary relation, useful rank, factor-base logs, single-target recovery, and same-point rho comparison remain the active goal gates.
