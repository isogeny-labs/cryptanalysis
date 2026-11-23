# Connected components in the archived M31 three-point comparison

The six recorded relation matrices all have a single connected component after repeatedly removing rows that touch a column of degree one. A connected-component split therefore offers no partition of the remaining factor-base matrix on these inputs. These counts concern the signed factor-base columns only. The two scalar coefficients in the relation records serve a different purpose and are excluded.

| Arm | Seed | Recorded rows | Original components (rows × used columns) | Remaining component (rows × used columns) | Elimination share of setup-charged time |
|---|---:|---:|---|---|---:|
| Auxiliary | 0 | 455 | 453 × 457 and 2 × 4 | 317 × 316 | 2.355% |
| Auxiliary | 1 | 456 | 456 × 468 | 318 × 317 | 2.383% |
| Auxiliary | 2 | 465 | 465 × 475 | 324 × 324 | 2.691% |
| Plain | 0 | 461 | 461 × 469 | 353 × 352 | 2.718% |
| Plain | 1 | 468 | 468 × 472 | 346 × 345 | 2.729% |
| Plain | 2 | 463 | 463 × 473 | 305 × 304 | 2.373% |

The signed codes are summed per column before constructing the incidence graph, so opposite signs on the same column cancel. A column used by one remaining row forces that row's coefficient in every row dependence to be zero. Leaf.lean proves this local implication over a field, including the case where rows previously shown to have zero weight also touch the column. The table comes from a Python replay of the archived JSONL at f9c7b49e7. Component sizes do not certify arithmetic rank or rule out separators in a connected graph.

Run `python3 audit.py` to reproduce component counts (rows first), and `lake env lean /absolute/path/to/Leaf.lean` in the project's mathlib environment to replay the lemma. Timing shares use elimination_seconds divided by solver_seconds + input_setup_seconds from the archived comparison/runs.json. Giving the whole measured elimination phase zero cost would yield at most 1.0281× end-to-end speedup across these six runs if all other costs and stopping points stayed fixed.

## Could the same sequence have stopped earlier?

A separate replay uses FLINT modular ranks over the fixture's prime order 2147505293, binary ranks, and SciPy maximum bipartite matchings. The columns below are one-based relation positions. “First unmatched” means that a matching from all prefix rows into distinct used columns is impossible. A missing match forces a dependence over any field. A full matching can coexist with arithmetic dependence.

| Arm | Seed | First nonempty core | First binary dependence | First unmatched | First dependence mod 2147505293 | Rank immediately before / after |
|---|---:|---:|---:|---:|---:|---:|
| Auxiliary | 0 | 402 | 452 | 455 | 455 | 454 / 454 |
| Auxiliary | 1 | 402 | 452 | 456 | 456 | 455 / 455 |
| Auxiliary | 2 | 407 | 465 | none | 465 | 464 / 464 |
| Plain | 0 | 411 | 461 | 461 | 461 | 460 / 460 |
| Plain | 1 | 419 | 462 | 468 | 468 | 467 / 467 |
| Plain | 2 | 405 | 457 | 463 | 463 | 462 / 462 |

For each archive of length n, the first n−1 rows have rank n−1, and the full matrix also has rank n−1. Every earlier prefix is therefore independent. The first exact row dependence occurs on the last recorded row in all six archives. Preserving the emitted rows and order, an earlier graph trigger cannot save a single collected row while still requiring an exact dependence. This comparison says nothing about changing which rows are emitted or reducing time per trial.

Run `python3 -B prefix_audit.py` with python-flint and SciPy. The script reads the signed codes only. The finite ranks are independently computed by FLINT. Leaf.lean also proves the general consequence that any nonzero dependence at this boundary has nonzero weight on the last row.

Exact rational rank from the signed integer matrix agrees with the full target-field rank in each row of the table. In particular, auxiliary seed 2 gives a concrete 465-row matrix with a matching covering every row and rational rank 464. Its dependence survives in characteristic zero, so reduction modulo the target order is unnecessary to explain this example.

## Size of coefficients in the first dependence

Every nonzero dependence on each archived terminal matrix needs at least one centered coefficient of magnitude greater than 8,388,608. This excludes a direct signed 24-bit representation of the whole dependence, even allowing an arbitrary common rescaling modulo 2147505293. The bound concerns final coefficients in this specific representation. Bit-sliced arithmetic, multi-limb encodings, intermediate representations and changes to the input rows lie outside the result.

The archived weight vectors have 317, 306 and 323 nonzero entries on the auxiliary arm and 353, 346 and 305 on the plain arm. Identifying each nonzero value with its negative gives respectively 179, 179, 186 and 206, 206, 175 distinct classes. A nonzero common scalar permutes these signed classes. In particular a single nonzero magnitude cannot encode these dependences.

The stronger bit-width bound uses the normalized final coordinate, which is one in all six certificates. The full left nullspace has dimension one. If every centered coefficient of another nonzero dependence had magnitude at most 8388608, its final coordinate would force its scale, up to an overall sign, into [1,8388608]. For every such scale in each archive, at least one of the first five distinct nonzero magnitudes has scaled residue strictly between 8388608 and 2147505293−8388608. Negation preserves that open interval.

Run `python3 -B weight_audit.py` to verify the archived weights against all 500 signed columns, recompute the rank in FLINT, check the Lean witness values against the archive, and enumerate scales with exact 64-bit arithmetic. Replay `ScaleBound.lean` in the mathlib environment for the independent finite exclusion proof using native_decide. The link between the checked witness constants and the archived files is verified by Python.
