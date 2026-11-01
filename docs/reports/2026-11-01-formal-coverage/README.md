# Cryptanalysis formal path inventory, 1 November 2026

This additive snapshot pins cryptanalysis `main` at
`a2898178b11434a4fca9c6c73cf2b0845c4abfb5` and compares its complete
tracked Git tree with the frozen [31 October inventory](../2026-10-31-formal-coverage/README.md)
at `7aa40f92aacc4651793974c0a7d8ac06c333a2eb`.

| Tracked-path count | 31 October | 1 November | Change |
| --- | ---: | ---: | ---: |
| Experiment directories | 425 | 432 | +7 |
| Directories with a co-located `.lean` file | 116 | 116 | 0 |
| `.lean` files | 184 | 184 | 0 |
| `.lean` files under `experiments/` | 167 | 167 | 0 |
| Lexical `theorem` or `lemma` pointers | 1,191 | 1,191 | 0 |

The seven new experiment directories are `glv-table-confirm-above40-20261102`,
`p2-halving-carry-20261101`, `p2-lift-defect-20261101`,
`prime-field-m3-cdclt-20261031`, `prime-ic-jacobian-relations-20261031`,
`rho-ec-step-20261101`, and `torsion-division-derivative-20261031`.
None has a co-located Lean path in this tree. No previously inventoried Lean
blob changed.

The [machine-readable inventory](inventory.json) lists every experiment
directory and tracked Lean path with its Git blob ID and lexical declaration
pointers. The [graph source](render.py) produces [coverage.svg](coverage.svg)
and [report.typ](report.typ); the [one-page PDF](report.pdf) was rendered and
visually inspected.

## Reproduction

`tools/formal_coverage_inventory.py` has SHA-256
`8e8ddf105753b50902d40cbc209470b8aa81e69cf0fe6df3fa3969a618df16a9`.
It reads the complete Git tree through `git ls-tree -r -z` and tracked Lean
blobs through `git cat-file --batch`, including paths absent from a sparse
checkout. The generated `inventory.json` has SHA-256
`5b8ad120880a611301e6fe3664c48ff137b1d6c6dd0b810d67c2c591e01099a5`.

```sh
python3 tools/formal_coverage_inventory.py \
  a2898178b11434a4fca9c6c73cf2b0845c4abfb5 \
  docs/reports/2026-11-01-formal-coverage/inventory.json
python3 docs/reports/2026-11-01-formal-coverage/render.py
python3 -c "import typst; typst.compile('docs/reports/2026-11-01-formal-coverage/report.typ', output='docs/reports/2026-11-01-formal-coverage/report.pdf')"
```

## Scope

Path co-location is navigation evidence. It does not establish that a Lean
statement matches an experiment claim, compiles under the pinned toolchain,
has an acceptable axiom set, or validates empirical rows. A directory without
a co-located Lean file may have a shared formalization or no mathematical
proposition to prove. The next formal review should bind each substantive
claim to its exact statement and assumptions, then run a named-module build,
axiom audit, and independent evidence replay where applicable.
