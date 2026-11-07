#!/usr/bin/env python3
"""Render two pinned cryptanalysis path inventories without changing either."""

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "2026-10-28-formal-coverage" / "inventory.json"
NEW = HERE / "inventory.json"
old = json.loads(OLD.read_text())
new = json.loads(NEW.read_text())
assert old["schema"] == new["schema"] == "formal-coverage-inventory/v1"
assert old["source_commit"] == "f6dda22f74168b6578eb47c80a969273db8753ab"
assert new["source_commit"] == "7aa40f92aacc4651793974c0a7d8ac06c333a2eb"


def check_inventory(data):
    c = data["counts"]
    assert c["experiment_directories_with_colocated_lean"] + c[
        "experiment_directories_without_colocated_lean"
    ] == c["experiment_directories"] == len(data["experiments"])
    assert c["lean_files_total"] == len(data["lean_files"])
    assert c["lean_files_under_experiments"] == sum(
        row["path"].startswith("experiments/") for row in data["lean_files"]
    )
    assert c["lexical_theorem_lemma_pointers"] == sum(
        len(row["declarations"]) for row in data["lean_files"]
    )


check_inventory(old)
check_inventory(new)
a, b = old["counts"], new["counts"]
old_dirs = {row["directory"] for row in old["experiments"]}
new_dirs = {row["directory"] for row in new["experiments"]}
assert old_dirs <= new_dirs
old_lean_dirs = {row["directory"] for row in old["experiments"] if row["lean_paths"]}
new_lean_dirs = {row["directory"] for row in new["experiments"] if row["lean_paths"]}
assert old_lean_dirs <= new_lean_dirs

scale = 690 / b["experiment_directories"]
bars = []
for y, label, c in ((108, "28 Oct 2026", a), (206, "31 Oct 2026", b)):
    with_count = c["experiment_directories_with_colocated_lean"]
    without_count = c["experiment_directories_without_colocated_lean"]
    w1 = round(with_count * scale, 1)
    w2 = round(without_count * scale, 1)
    bars.append(
        f'<text x="42" y="{y - 16}" font-size="15" fill="#172b4d">'
        f'{label} · {c["experiment_directories"]} directories</text>'
        f'<rect x="42" y="{y}" width="{w1}" height="39" fill="#166a8c"/>'
        f'<rect x="{42 + w1}" y="{y}" width="{w2}" height="39" fill="#b4bdc9"/>'
        f'<text x="{48 + w1 + w2}" y="{y + 26}" font-size="14" fill="#42526e">'
        f'{with_count} / {without_count}</text>'
    )

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="920" height="350" viewBox="0 0 920 350">
<rect width="920" height="350" fill="white"/>
<g font-family="DejaVu Sans, sans-serif">
<text x="42" y="40" font-size="21" fill="#172b4d">Cryptanalysis tracked experiment paths</text>
<text x="42" y="65" font-size="12" fill="#42526e">Same Git-tree inventory method at two pinned commits; path co-location only</text>
{''.join(bars)}
<rect x="42" y="272" width="15" height="15" fill="#166a8c"/>
<text x="65" y="285" font-size="13" fill="#42526e">with a co-located .lean file</text>
<rect x="355" y="272" width="15" height="15" fill="#b4bdc9"/>
<text x="378" y="285" font-size="13" fill="#42526e">without a co-located .lean file</text>
<text x="42" y="324" font-size="11" fill="#536273">These counts do not classify claims, theorem validity, or execution evidence.</text>
</g></svg>
'''
(HERE / "coverage.svg").write_text(svg)

typ = f'''#set page(width: 210mm, height: 297mm, margin: 18mm)
#set text(font: "DejaVu Sans", size: 10pt)
= Cryptanalysis formal path inventory: 31 October 2026

Source commit `{new['source_commit']}`; tree `{new['source_tree']}`. The comparison uses the frozen 28 October source commit `{old['source_commit']}`. Both inventories were produced by `tools/formal_coverage_inventory.py` from complete Git trees.

#image("coverage.svg", width: 100%)

== Observed change

- Tracked experiment directories: {a['experiment_directories']} to {b['experiment_directories']} (+{b['experiment_directories'] - a['experiment_directories']}). Exactly {len(new_dirs - old_dirs)} directory paths were added and none removed.
- Directories with a co-located `.lean` file: {a['experiment_directories_with_colocated_lean']} to {b['experiment_directories_with_colocated_lean']} (+{b['experiment_directories_with_colocated_lean'] - a['experiment_directories_with_colocated_lean']}). Exactly {len(new_lean_dirs - old_lean_dirs)} directory paths entered this group.
- Tracked `.lean` files: {a['lean_files_total']} to {b['lean_files_total']} (+{b['lean_files_total'] - a['lean_files_total']}); files under `experiments/`: {a['lean_files_under_experiments']} to {b['lean_files_under_experiments']} (+{b['lean_files_under_experiments'] - a['lean_files_under_experiments']}).
- Lexical `theorem` or `lemma` pointers: {a['lexical_theorem_lemma_pointers']} to {b['lexical_theorem_lemma_pointers']} (+{b['lexical_theorem_lemma_pointers'] - a['lexical_theorem_lemma_pointers']}). The regex can include comments and omit other declaration forms.

== Interpretation and next check

The figure is an inventory of where tracked paths reside. A co-located Lean file does not show that it proves an experiment claim; an experiment without one may have a shared formalization or no mathematical proposition. The next check is to bind each substantive claim to its exact declaration and premises, run the pinned named-module build and axiom audit, and independently validate any empirical inputs.

== Reproduction

From a checkout containing the pinned commit, run `python3 tools/formal_coverage_inventory.py {new['source_commit']} docs/reports/2026-10-31-formal-coverage/inventory.json`, then `python3 docs/reports/2026-10-31-formal-coverage/render.py`. The complete per-file inventory and Git blob IDs are in `inventory.json`. The earlier report at `docs/reports/2026-10-28-formal-coverage/` remains frozen.
'''
(HERE / "report.typ").write_text(typ)
print(f"rendered {HERE / 'coverage.svg'} and {HERE / 'report.typ'}")
