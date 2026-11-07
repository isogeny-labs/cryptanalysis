#!/usr/bin/env python3
"""Render the frozen inventory summary as an SVG and Typst report source."""

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "inventory.json").read_text())
counts = data["counts"]
with_lean = counts["experiment_directories_with_colocated_lean"]
without = counts["experiment_directories_without_colocated_lean"]
total = counts["experiment_directories"]
assert with_lean + without == total
assert len(data["experiments"]) == total
assert len(data["lean_files"]) == counts["lean_files_total"]

scale = 700 / total
width_a = round(with_lean * scale, 1)
width_b = round(without * scale, 1)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="250" viewBox="0 0 900 250">
<rect width="900" height="250" fill="#fff"/>
<text x="40" y="36" font-family="DejaVu Sans" font-size="20" fill="#172b4d">Tracked experiment directories at frozen main</text>
<text x="40" y="69" font-family="DejaVu Sans" font-size="13" fill="#42526e">Git tree {data['source_commit'][:12]} · path co-location only · n={total} directories</text>
<rect x="40" y="94" width="{width_a}" height="48" fill="#166a8c"/>
<rect x="{40 + width_a}" y="94" width="{width_b}" height="48" fill="#b4bdc9"/>
<text x="40" y="178" font-family="DejaVu Sans" font-size="15" fill="#166a8c">■ {with_lean} with a co-located .lean file</text>
<text x="40" y="207" font-family="DejaVu Sans" font-size="15" fill="#536273">■ {without} without a co-located .lean file</text>
<text x="40" y="231" font-family="DejaVu Sans" font-size="11" fill="#536273">This chart does not count unproved claims or validate theorem fidelity.</text>
</svg>
'''
(HERE / "coverage.svg").write_text(svg)

typ = f'''#set page(width: 210mm, height: 297mm, margin: 18mm)
#set text(font: "DejaVu Sans", size: 10pt)
= Cryptanalysis formal coverage: frozen path inventory
28 October 2026 · source commit `{data['source_commit']}` · tree `{data['source_tree']}`

This report inventories tracked paths and lexical Lean declaration pointers. It makes no judgment about whether a Lean statement faithfully represents an experiment result, whether Lean builds, or whether the underlying experiment is valid.

#image("coverage.svg", width: 100%)

== Method and observations
`tools/formal_coverage_inventory.py` runs `git ls-tree -r -z` on the frozen commit and reads every tracked `.lean` blob with `git cat-file --batch`. The local command completed without an API truncation limit. `inventory.json` records exact paths, blob object IDs, and line numbers for lines lexically matching `theorem` or `lemma` declarations.

- {counts['tracked_blobs']} tracked Git blobs; {total} experiment directories.
- {counts['lean_files_total']} `.lean` files across the repository; {counts['lean_files_under_experiments']} under `experiments/`.
- {with_lean} experiment directories contain at least one `.lean` file; {without} do not.
- {counts['lexical_theorem_lemma_pointers']} lexical declaration pointers. Regex extraction can include comments or omit other declaration forms, and does not parse Lean syntax.

== Interpretation and next gate
The gray segment is an inspection queue, not a missing-proof count: an operational experiment may have no mathematical proposition to formalize, while a result may be proved in a shared file elsewhere. Review each substantive claim against its exact Lean statement and hypotheses, run the pinned theorem build and axiom audit, then independently validate its empirical evidence before promoting any result. The repository's existing Lean gate also does not establish statement-to-claim fidelity.

== Reproduction
From this commit's checkout: `python3 tools/formal_coverage_inventory.py {data['source_commit']} docs/reports/2026-10-28-formal-coverage/inventory.json`, then `python3 docs/reports/2026-10-28-formal-coverage/render.py`. Source data are the frozen Git tree, not a GitHub recursive API response.
'''
(HERE / "report.typ").write_text(typ)
print(f"rendered {HERE / 'coverage.svg'} and {HERE / 'report.typ'}")
