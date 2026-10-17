# A complete seven-chart function selector for six N41 source slots

**A target-conditioned Riemann–Roch formula now searches all six source slots without fixing the known relation.** The compact selected-row variant is 3.78 MB, and a sequential-selector revision is 2.87 MB. Both admit the independently checked ordinary relation. All three full public-point queries reached their 185 s bounds with status `BOUNDED_UNKNOWN`. This identifies formula construction as cheap on this N41 source and unpinned solver search as the remaining local bottleneck.

## Exact query and algebra

The frozen source is the fixed-seed W8 input for `EC1N41Ckb1h7d5e80d3c4d0`: `GF(2)[t]/(t^41+t³+1)`, `y²+xy=x³+1`, six rotated slots with 160 signed pair states from 40 pair codes per slot. The public point is `Q=(2026560328086,1928332930914)`. Source SHA-256 is `7fc0362121ecc510d9ec9ea62a17c1efc878cd96fed7292246675c1951f006fb`. The selector chooses one state in each slot and enforces twelve distinct folded columns and seven distinct x coordinates including `−Q`.

At infinity, `x` and `y` have pole orders 2 and 3. Thus `L(7O)` has basis `1,x,y,x²,xy,x³,x²y`. A nonzero function in this space vanishing at six selected points and `−Q` has seven distinct affine zeros and pole divisor at most `7O`; degree forces its divisor to be exactly the seven points minus `7O`. Under the elliptic-curve identification with `Pic⁰`, their sum is `O`, so the six selected points sum to `Q`. Conversely, the group relation gives that principal divisor and a nonzero function in `L(7O)`. For rational input points, the function can be chosen over the finite field. This is the written curve/divisor bridge; its formalization status is in [PROOF_MAP.md](PROOF_MAP.md).

The seven function coefficients are projective. Exactly one of seven charts sets the first nonzero coefficient to 1 and all earlier coefficients to zero. [FunctionSelector.lean](FunctionSelector.lean) checks this normalization and the preservation of vanishing rows. The circuit keeps all seven charts; the known relation's chart-zero coefficient vector is a correctness control only. The SAT query leaves all six point selectors free.

## Three formula designs

Version 1 guards each of the 160 precomputed point-row equations per slot. Version 2 first chooses one row in each slot through native XOR and then evaluates six field-coordinate products for that selected row. Version 3 keeps that row computation and changes the one-hot condition from pairwise clauses to a sequential prefix encoding. Its soundness implication is checked as `sequential_amo_sound` in Lean. All builds evaluate every generated CNF and native-XOR row on the known relation; the independent [audit](audit.py) recomputes its curve-group sum with separate field arithmetic, checks selected-column/x distinctness, hashes raw logs, and recounts serialized formula rows.

| Version | Variables | CNF clauses | Native XOR rows | AND gates | Formula bytes | Build wall | Query wall cap | Query status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Guarded rows | 40,895 | 118,787 | 39,401 | 0 | 19,421,850 | 4.268 s | 185 s | `BOUNDED_UNKNOWN` |
| Selected row, pairwise one-hot | 56,603 | 181,409 | 21,197 | 33,912 | 3,780,534 | 0.491 s | 185 s | `BOUNDED_UNKNOWN` |
| Selected row, sequential one-hot | 57,557 | 107,945 | 21,197 | 33,912 | 2,868,879 | 0.466 s | 185 s | `BOUNDED_UNKNOWN` |

All three solver runs used the same hashed `/opt/homebrew/bin/cryptominisat5` binary, one thread, `--maxtime=180`, a parent 185 s wall cap, and a 4 GiB memory boundary on an ordinary local host. The three child peak RSS values were 130,809,856 B, 266,240,000 B, and 276,545,536 B. The measured query walls were 185.021 s, 185.010 s, and 185.038 s. None of the transcripts has a terminal satisfiable or unsatisfiable line; raw stdout/stderr and query receipts are retained. These are stage measurements, with `candidate_id: null` until a complete IC pipeline and workload are specified.

## Transfer decision and next experiment

The archived W23 N131 source has 4,196,872 signed states per slot. Directly transferring the version-2 pairwise one-hot constraint would require **52,841,191,162,536** exclusion clauses across six slots. The version-3 sequential encoding reduces that particular count to **75,543,672** clauses, plus 25,181,226 prefix and 25,181,232 selector variables before any point-row arithmetic. These are exact counts for the specified literal encodings, not a runtime projection. They show that one-hot encoding must be compact, but selecting from explicitly enumerated N131 point rows still leaves a large materialization problem.

The next constructive experiment is an **implicit pair-source selector**: encode each slot's two factor-base indices, root, and sign, compute its point row only after the compact source choices are set, and test the same seven-row function condition on an unpinned N41 query. Freeze the source and solver caps, retain the current selector as a paired control, and measure formula size, full query status, and exact source coverage before an N131 preflight. The complete projective chart set and distinct-point conditions remain part of that test.
