# Cryptanalysis formal path inventory, 31 October 2026

This is a new pinned navigation report for cryptanalysis `main` at
`7aa40f92aacc4651793974c0a7d8ac06c333a2eb`. It compares the complete
tracked Git tree with the frozen [28 October inventory](../2026-10-28-formal-coverage/README.md)
at `f6dda22f74168b6578eb47c80a969273db8753ab`. The earlier report and
its graph remain unchanged.

| Tracked-path count | 28 October | 31 October | Change |
| --- | ---: | ---: | ---: |
| Experiment directories | 375 | 425 | +50 |
| Directories with a co-located `.lean` file | 79 | 116 | +37 |
| `.lean` files | 137 | 184 | +47 |
| `.lean` files under `experiments/` | 125 | 167 | +42 |
| Lexical `theorem` or `lemma` pointers | 1,027 | 1,191 | +164 |

The [machine-readable inventory](inventory.json) contains every experiment
directory, Lean path, Git blob ID, and lexical declaration pointer. The
[editable graph source](render.py) produces [coverage.svg](coverage.svg) and
[report.typ](report.typ); the [one-page PDF](report.pdf) embeds the graph.
The PDF was rendered and visually inspected at 120 dpi, and text extraction
confirmed the counts and pinned commit IDs.

## Reproduction and checks

`tools/formal_coverage_inventory.py` has SHA-256
`8e8ddf105753b50902d40cbc209470b8aa81e69cf0fe6df3fa3969a618df16a9`.
It reads the complete Git tree with `git ls-tree -r -z` and the tracked Lean
blobs with `git cat-file --batch`, including paths absent from a sparse
checkout. The same script reproduced the old committed `inventory.json`
**byte for byte** before creating this snapshot. The new `inventory.json` has
SHA-256 `680c9548e9285c97d601c99cb1912897d079ffed799f3234d740f33d779b2bda`.

```sh
python3 tools/formal_coverage_inventory.py \
  7aa40f92aacc4651793974c0a7d8ac06c333a2eb \
  docs/reports/2026-10-31-formal-coverage/inventory.json
python3 docs/reports/2026-10-31-formal-coverage/render.py
python3 -c "import typst; typst.compile('docs/reports/2026-10-31-formal-coverage/report.typ', output='docs/reports/2026-10-31-formal-coverage/report.pdf')"
```

## Interpretation

The graph counts path co-location, not proof coverage. The regular expression
can include commented declarations and omit other Lean declaration forms. A
co-located file can state a weaker proposition than the experiment claim, and
an experiment without one can have a shared formalization. No Lean build,
axiom audit, execution replay, or claim-fidelity decision is made here.

The next review should bind each substantive claim to its exact statement and
premises, run the pinned named-module gate and axiom audit, and separately
check the raw experiment evidence. This inventory changes no measured result
or scientific decision, so the earlier experiment performance graphs were not
recomputed for this path-only update.
