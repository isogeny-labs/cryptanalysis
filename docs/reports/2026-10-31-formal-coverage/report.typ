#set page(width: 210mm, height: 297mm, margin: 18mm)
#set text(font: "DejaVu Sans", size: 10pt)
= Cryptanalysis formal path inventory: 31 October 2026

Source commit `7aa40f92aacc4651793974c0a7d8ac06c333a2eb`; tree `67dcf1b0d50fce3799fbf0776a26b95b9ecb6f04`. The comparison uses the frozen 28 October source commit `f6dda22f74168b6578eb47c80a969273db8753ab`. Both inventories were produced by `tools/formal_coverage_inventory.py` from complete Git trees.

#image("coverage.svg", width: 100%)

== Observed change

- Tracked experiment directories: 375 to 425 (+50). Exactly 50 directory paths were added and none removed.
- Directories with a co-located `.lean` file: 79 to 116 (+37). Exactly 37 directory paths entered this group.
- Tracked `.lean` files: 137 to 184 (+47); files under `experiments/`: 125 to 167 (+42).
- Lexical `theorem` or `lemma` pointers: 1027 to 1191 (+164). The regex can include comments and omit other declaration forms.

== Interpretation and next check

The figure is an inventory of where tracked paths reside. A co-located Lean file does not show that it proves an experiment claim; an experiment without one may have a shared formalization or no mathematical proposition. The next check is to bind each substantive claim to its exact declaration and premises, run the pinned named-module build and axiom audit, and independently validate any empirical inputs.

== Reproduction

From a checkout containing the pinned commit, run `python3 tools/formal_coverage_inventory.py 7aa40f92aacc4651793974c0a7d8ac06c333a2eb docs/reports/2026-10-31-formal-coverage/inventory.json`, then `python3 docs/reports/2026-10-31-formal-coverage/render.py`. The complete per-file inventory and Git blob IDs are in `inventory.json`. The earlier report at `docs/reports/2026-10-28-formal-coverage/` remains frozen.
