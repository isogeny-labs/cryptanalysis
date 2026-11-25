# Cold Rust public-table results

Producer-run observations with independent PCC standing pending. [pcc:unverified]

Command from the repository root:

```sh
python3 experiments/prime-field-auxiliary-ic/m31-public-reflected-build/replay.py --implementation rust --cold
```

Each observation starts a fresh Rust process on the same supplied public basis.
The elapsed clock charges loading, validation, signed expansion, allocation,
table construction, complete reference verification, output and teardown.
The protocol was written before collection. All 96 expected-valid observations
completed; both modes also passed collision and rejected-input controls.
[pcc:unverified]

| Fixture | Flat wall median ms | Reflected wall median ms | Median paired wall ratio | Reflected wins |
| --- | ---: | ---: | ---: | ---: |
| Auxiliary | 13.473 | 12.603 | 1.079 | 21/24 |
| Plain | 13.432 | 12.031 | 1.106 | 20/24 |

| Fixture | Flat CPU median ms | Reflected CPU median ms | Median paired CPU ratio | Reflected wins |
| --- | ---: | ---: | ---: | ---: |
| Auxiliary | 11.885 | 10.653 | 1.100 | 21/24 |
| Plain | 11.536 | 10.538 | 1.099 | 20/24 |

These are exploratory measurements on one shared Apple M4 Pro host. CPU time
is child user plus system time. Ratios use matched observations, so they can
differ from ratios of the displayed medians. Raw observations are rust-cold.csv.
Toolchain, source HEAD and file hashes are in rust-cold-environment.json.
[pcc:unverified]

The basis is supplied as input. Basis generation, compilation and Python
reference generation are outside the clock. OS file caches were allowed to
remain warm. This measures the public fixture-to-table operation through exit.
Relation collection and elimination are absent from this benchmark, so solver
end-to-end performance remains unmeasured. The Lean proof establishes functional
equivalence and the documented abstract cost model; these timing observations
are empirical.
