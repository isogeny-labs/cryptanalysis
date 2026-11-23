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
