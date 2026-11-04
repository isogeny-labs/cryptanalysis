#set page(width: 210mm, height: 297mm, margin: 18mm)
#set text(font: "DejaVu Sans", size: 10pt)
= Cryptanalysis formal path inventory: 1 November 2026

Source commit `a2898178b11434a4fca9c6c73cf2b0845c4abfb5`; tree `85b098c19830b66bcdf5e5a1ac641d08a9174caa`. The comparison uses the frozen 31 October source commit `7aa40f92aacc4651793974c0a7d8ac06c333a2eb`. Both inventories were produced by `tools/formal_coverage_inventory.py` from complete Git trees.

#image("coverage.svg", width: 100%)

== Observed change

- Tracked experiment directories: 425 to 432 (+7). Exactly 7 directory paths were added and none removed.
- Directories with a co-located `.lean` file: 116 to 116 (+0). Exactly 0 directory paths entered this group.
- Tracked `.lean` files: 184 to 184 (+0); files under `experiments/`: 167 to 167 (+0).
- Lexical `theorem` or `lemma` pointers: 1191 to 1191 (+0). The regex can include comments and omit other declaration forms.

== Interpretation and next check

The figure is an inventory of where tracked paths reside. A co-located Lean file does not show that it proves an experiment claim; an experiment without one may have a shared formalization or no mathematical proposition. The next check is to bind each substantive claim to its exact declaration and premises, run the pinned named-module build and axiom audit, and independently validate any empirical inputs.

== Reproduction

From a checkout containing the pinned commit, run `python3 tools/formal_coverage_inventory.py a2898178b11434a4fca9c6c73cf2b0845c4abfb5 docs/reports/2026-11-01-formal-coverage/inventory.json`, then `python3 docs/reports/2026-11-01-formal-coverage/render.py`. The complete per-file inventory and Git blob IDs are in `inventory.json`. The earlier report at `docs/reports/2026-10-31-formal-coverage/` remains frozen.
