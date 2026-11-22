#set page(width: 210mm, height: 297mm, margin: 18mm)
#set text(font: "DejaVu Sans", size: 10pt)
= Cryptanalysis formal path inventory: 7 November 2026

Source commit `6277e82689b6cd576f2de3cadda5548e34cf2367`; tree `874af058ea5a9201b53778aa2be8b898482f80be`. The comparison uses the frozen 1 November source commit `a2898178b11434a4fca9c6c73cf2b0845c4abfb5`. Both inventories were produced by `tools/formal_coverage_inventory.py` from complete Git trees. Producer claim PCC-20261107-bff5b3 has unverified standing #raw("[pcc:unverified]").

#image("coverage.svg", width: 100%)

== Observed change

- Tracked experiment directories: 432 to 456 (+24). Exactly 24 directory paths were added and none removed.
- Directories with a co-located `.lean` file: 116 to 117 (+1). Exactly 1 directory paths entered this group.
- Tracked `.lean` files: 184 to 198 (+14); files under `experiments/`: 167 to 168 (+1).
- Lexical `theorem` or `lemma` pointers: 1191 to 1689 (+498). The regex can include comments and omit other declaration forms.

== Interpretation and next check

The figure is an inventory of where tracked paths reside. A co-located Lean file does not show that it proves an experiment claim; an experiment without one may have a shared formalization or no mathematical proposition. The next check is to bind each substantive claim to its exact declaration and premises, run the pinned named-module build and axiom audit, and independently validate any empirical inputs. #raw("[pcc:unverified]")

== Reproduction

From a checkout containing the pinned commit, run `python3 tools/formal_coverage_inventory.py 6277e82689b6cd576f2de3cadda5548e34cf2367 docs/reports/2026-11-07-formal-coverage/inventory.json`, then `python3 docs/reports/2026-11-07-formal-coverage/render.py`. The complete per-file inventory and Git blob IDs are in `inventory.json`. The earlier report at `docs/reports/2026-11-01-formal-coverage/` remains frozen.
