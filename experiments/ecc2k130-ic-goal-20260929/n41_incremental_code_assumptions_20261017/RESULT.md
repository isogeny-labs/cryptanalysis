# Incremental assumption search across the N41 public first-code partition

**One CryptoMiniSat instance loaded the exact N41 public six-pair circuit once and queried all 40 permitted first-slot codes with incremental assumptions.** The complete frozen pass took 532.359 seconds and 335,642,624 bytes sampled peak combined RSS. Every call returned `UNKNOWN` under its five-second solver setting. Code 6, whose satisfiability is established by the archived independently checked relation assignment, also returned `UNKNOWN` after 7.380 seconds of wall time. This bounds the tested first-code-only reuse strategy on this instance and resource envelope.

## Method and result

The input is the public XCNF for raw point `(2026560328086,1928332930914)` on `EC1N41Ckb1h7d5e80d3c4d0`. The parser loaded 31,533 variables, 82,957 ordinary clauses, and 3,689 native XOR rows. The 40 allowed numeric codes and their seven wire IDs came from the prior exact partition protocol; the solver received only the frozen formula and code list. Each call asserted the seven first-slot wire values for one code, in sorted order, while retaining the same solver and its learned state. There was one solver worker, a five-second per-call solver limit, a 550-second parent wall cap, and a 4-GiB combined RSS cap. The candidate remains a stage-level design (`candidate_id: null`).

| Frozen run | Completed codes | Solver answers | Sum of call wall intervals | Parent wall | Sampled peak combined RSS |
| --- | ---: | --- | ---: | ---: | ---: |
| Ten-second single-code pilot | 1 | `UNKNOWN` | 19.438 s | 19.775 s | 206,880,768 B |
| Five-second incremental pass | 40 of 40 | 40 `UNKNOWN` | 532.166 s | 532.359 s | 335,642,624 B |

The 40 call walls range from 5.984 to 48.303 seconds (median 10.071 seconds) on the ordinary shared host. The solver setting and wall intervals are separate quantities; this experiment is a search-status diagnostic and does not establish a throughput improvement over the prior fresh-process cubes, which used a different cap. The parent interval includes formula loading and call overhead; the 0.193-second difference between the summed call walls and parent wall is recorded rather than assigned to a target solve. The source, compiled binary, library, header, formula, checked Sage runtime, code order, limits, raw output, and both run protocols are hash-bound in the local artifacts. The pilot remains a separate immutable receipt; the shortened full-pass protocol is version 2.

The prior [first-code partition](../n41_public_code_cube_20261017/RESULT.md) queried the same 40 codes with fresh solver processes and a 12-second parent wall cap each; all were censored. The prior [witness control](../n41_public_code_cube_20261017/witness_result.json) checks code 6 against every clause and XOR row of the exact formula. Thus the code-6 `UNKNOWN` here is a timeout on a satisfiable branch, not a counterexample to the circuit. Other `UNKNOWN` codes remain unresolved. [verify.py](verify.py) audits hashes, exact order, raw status lines, caps, and the retrospective witness binding; its output is [verification.json](verification.json).

## Next gate

Incremental reuse with only one seven-bit code fixed did not resolve an ordinary public decomposition within the tested envelope. The next design must constrain at least two partial sums jointly with the public point before expanding their signed state combinations. A cheap N41 gate is to construct a lossless family-level compatibility predicate, verify it retains the archived relation, and measure how many complete code families it rejects *before* enumerating state triples. Only a predicate with an exact proof or independent exhaustive check and a credible N131 one-worker, 600-second, 4-GiB projection should advance to an unpinned ordinary N41 relation run.
