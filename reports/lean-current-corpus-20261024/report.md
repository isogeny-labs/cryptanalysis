# Current cryptanalysis Lean corpus evidence — 24 October 2026

**Status:** source-bound proof-build audit. This is not a review of every
historical mathematical claim or experiment. No scientific run, curve identity,
performance measurement, or research status changes in this report.

## Question and pinned inputs

Can the 94 research Lean files from cryptanalysis main
`9d320ae7df3b8aa15d4497d6895f63644daa92d5`, with this PR's two added
GLV axiom print directives, be accounted for by native build and axiom evidence without calling source-hash
metadata a proof? The earlier [full corpus audit](../lean-evidence-audit-20261021/report.md)
compiled 93 files at `6d83c09bc224472fedbfa5c1baa7e65b20502573`.
Its [source index](../lean-evidence-audit-20261021/evidence/corpus/cryptanalysis-corpus-index-20261021.json)
and retained logs are the immutable prior evidence.

## Method and result

`tools/lean/current-corpus-gate.py` checks the archived index, all group
summaries, 13 successful experiment proof checks, and the direct build logs.
It compares current source SHA-256 and each effective `lean-toolchain` byte
against the earlier build. **91 files are byte identical with unchanged pins.**
The two changed Orbit files and the one new GLV file are locked to reviewed
hashes and checked afresh:

| Current source | Native evidence |
| --- | --- |
| `experiments/orbit-quotient-summation/lean/OrbitPairIndex.lean` and `AxiomAudit.lean` | [Current build and axiom output](orbit-current-build.log): `lake build` succeeds, and all three named theorems use only `propext` and `Quot.sound`. The audit file itself is a print script. |
| `experiments/glv-table-rule-confirm-20261022/TableBudget.lean` | [Current axiom output](glv-current-axioms.log) exactly matches the corrected Lean receipt for all eight public theorems; both pinned and live C selector bindings match their recorded JSON. The prior receipt omitted axiom printouts for `tableSize_cases` and `table48_le_table12`. |

The deterministic [receipt](receipt.json) records 91 inherited plus three
fresh file checks. The [editable figure source](render_figure.py) generates
the [diagram](coverage.svg). Its denominator is **tracked research Lean files
outside the gate's own fixtures**, not
historical experiment claims. A current-head proof or claim coverage
percentage cannot be inferred from that bar.

## Adverse control and remaining gap

The historical generic `proof-gate.sh` passed two positive and five negative
fixtures ([self-test transcript](selftest.log)) but failed on a real imported proof, `TopRank.lean`, with `unknown
module prefix 'DigitCover'` ([native control log](import-prerequisite-control.log)).
Its automatic corpus discovery was therefore
removed. The new CI workflow runs the source-bound corpus bridge and the
fixture self-test. The existing metadata audit excludes those intentionally
failing fixtures from its research-source inventory. Any file or pin outside the reviewed set fails until new
native evidence is supplied. This bridge reuses 91 prior builds by exact bytes
and pins; it is not a fresh rebuild of those 91 files. A deliberately changed
source hash was rejected by the bridge ([control log](drift-control.log)).

The archived 91 files reuse the earlier audit's recorded axiom checks; this
bridge does not add an exhaustive transitive axiom audit of every declaration.
Native acceptance also does not establish that a theorem faithfully formalizes the
paper's or experiment's statement, that a recorded run executed, or that every
historical claim has a Lean theorem. The cross-repository claim-to-theorem-to-run
matrix remains open. The existing Orbit and GLV diagrams and the previous
corpus audit diagram were checked; their mathematical findings did not change,
so this report adds a coverage diagram and leaves those canonical figures as
they were.

## Reproduce

```sh
tools/lean/selftest/run.sh
python3 tools/lean/current-corpus-gate.py --check-receipt reports/lean-current-corpus-20261024/receipt.json
python3 reports/lean-current-corpus-20261024/render_figure.py --check
```

The [PDF](report.pdf) contains the diagram and the scoped verdict.
