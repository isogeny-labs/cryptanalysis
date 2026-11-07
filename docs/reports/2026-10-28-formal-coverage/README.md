# Frozen cryptanalysis Lean path inventory

This is a **syntactic navigation aid**, frozen at cryptanalysis commit
`f6dda22f74168b6578eb47c80a969273db8753ab` (tree recorded in
[`inventory.json`](inventory.json)). It does not certify an experiment, prove
that a result has or lacks a Lean theorem, or establish that a theorem states
the research claim. The readable [report source](report.typ), [graph](coverage.svg),
and [inspected PDF](report.pdf) summarize the machine-readable inventory.

## Method and observations

The script [formal_coverage_inventory.py](../../../tools/formal_coverage_inventory.py)
uses `git ls-tree -r -z` and `git cat-file --batch` at the frozen commit. This
enumerates the complete tracked tree, including files absent from a sparse
checkout. GitHub's recursive tree API returned `truncated: true` for this
commit, so that response is not the source. Every `.lean` row includes its Git
blob ID. The `theorem` and `lemma` line pointers come from a regular expression;
they may include commented text or omit other Lean declaration forms.

At this commit the complete tree has 59,789 tracked blobs, 375 tracked
`experiments/*` directories, 137 `.lean` files (125 under `experiments/`),
and 1,027 lexical theorem or lemma pointers. Of the experiment directories,
79 have at least one co-located `.lean` file and 296 do not. The latter number
is **not** a count of missing proofs: many directories record operational work,
and formalizations may live in a shared library or another repository. The
inventory does not parse Lean, build proofs, inspect axioms, replay trials, or
check statement-to-claim fidelity.

## Reproduce

From any checkout that has the frozen commit object:

```sh
python3 tools/formal_coverage_inventory.py \
  f6dda22f74168b6578eb47c80a969273db8753ab \
  docs/reports/2026-10-28-formal-coverage/inventory.json
python3 docs/reports/2026-10-28-formal-coverage/render.py
```

Compile `report.typ` with Typst to regenerate the PDF. The graph's editable
source is `render.py`; it reads the frozen JSON. The existing scientific graphs
under `experiments/` were checked for scope: this inventory adds no new
measurement or verified mathematical finding, so it changes none of them.

## Next validation gate

For each substantive result, map the exact written claim and hypotheses to an
actual Lean declaration, build the pinned target, audit its axioms, and
independently check the evidence. A green Lean build alone does not establish
claim fidelity. Keep unresolved results explicitly open rather than converting
these path counts into a scientific coverage percentage.
