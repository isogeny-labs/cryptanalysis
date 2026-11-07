# Cryptanalysis formal path inventory, 7 November 2026

This additive snapshot pins cryptanalysis `main` at `6277e82689b6cd576f2de3cadda5548e34cf2367` (tree `874af058ea5a9201b53778aa2be8b898482f80be`) and compares its complete tracked Git tree with the frozen [1 November inventory](../2026-11-01-formal-coverage/README.md) at `a2898178b11434a4fca9c6c73cf2b0845c4abfb5`. Producer claim `PCC-20261107-bff5b3` has unverified standing; all counts below are `[pcc:unverified]`.

| Tracked-path count | 1 November | 7 November | Change |
| --- | ---: | ---: | ---: |
| Experiment directories | 432 | 456 | +24 |
| Directories with a co-located `.lean` file | 116 | 117 | +1 |
| `.lean` files | 184 | 198 | +14 |
| `.lean` files under `experiments/` | 167 | 168 | +1 |
| Lexical `theorem` or `lemma` pointers | 1,191 | 1,689 | +498 |

The sole new experiment directory with a co-located Lean file is `experiments/hecke-432-dual-map-formalization-20261107`. Thirteen of the fourteen added Lean files are under `research/`. One pre-existing Lean blob changed: `experiments/glv-table-rule-confirm-20261022/TableBudget.lean`. No experiment directory or Lean path in the older inventory was removed. [pcc:unverified]

The [machine-readable inventory](inventory.json) lists every tracked experiment directory and Lean path with its Git blob ID and lexical declaration pointers. Its SHA-256 is `240a8067835329282475ea2739ae2f63df91d7bb18526d2d52b90e2bb483ef71`. The generator `tools/formal_coverage_inventory.py` has SHA-256 `8e8ddf105753b50902d40cbc209470b8aa81e69cf0fe6df3fa3969a618df16a9`. The [graph](coverage.svg), [source](render.py) and one-page [PDF](report.pdf) were regenerated; the PDF was rendered to an image and visually inspected. [pcc:unverified]

## Reproduction

```sh
python3 tools/formal_coverage_inventory.py \
  6277e82689b6cd576f2de3cadda5548e34cf2367 \
  docs/reports/2026-11-07-formal-coverage/inventory.json
python3 docs/reports/2026-11-07-formal-coverage/render.py
python3 -c "import typst; typst.compile('docs/reports/2026-11-07-formal-coverage/report.typ', output='docs/reports/2026-11-07-formal-coverage/report.pdf')"
```

## Scope and next checks

Path co-location is navigation evidence. It does not establish that a declaration matches an experiment claim, compiles under the pinned toolchain, has an acceptable axiom set, or validates empirical rows. A directory without a co-located Lean file may use a shared formalization or have no mathematical proposition to prove. The changed GLV table-selector module already has a [cap-128 independent review packet](../../../experiments/glv-table-rule-confirm-20261022/reviews/cap128-20261107/REPORT.md) at its pinned revision. The added dual-map module has a [separate review PR](https://github.com/isogeny-labs/cryptanalysis/pull/1421); its canonical independence check and current-head merge remain open. Empirical claims still need independent raw-row replay and provenance checks. [pcc:unverified]
