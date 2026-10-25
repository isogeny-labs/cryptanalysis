# Current Lean corpus gate

`current-corpus-gate.py` checks the 94 tracked research Lean files at the reviewed
source versions. It binds 91 byte-identical files and their effective Lean pins
to the [October 21 native build archive](../../reports/lean-evidence-audit-20261021/report.md),
then rebuilds and audits the two changed orbit files and the new GLV theorem.
The gate's own fixture and audit sources under `tools/lean/` are checked by
the separate self-test and excluded from the research-file count.
It compares the result with the [committed receipt](../../reports/lean-current-corpus-20261024/receipt.json).
The [workflow](../../.github/workflows/lean-proof-gate.yml) runs on Lean changes.
Any new or changed source outside the reviewed set fails until it receives new
native evidence and a reviewed gate update.

The older `proof-gate.sh` is used only for explicit standalone positive and
negative [fixtures](selftest/run.sh). Its automatic target discovery was removed:
it cannot build repository files that import local modules before their
prerequisites. The corpus gate uses the archived dependency-chain builds and
current dedicated checks instead.

Passing this gate establishes source-bound compilation and the recorded axiom
checks at the stated versions. It does not show that every Lean declaration's
transitive axioms were exhaustively audited, that every statement faithfully models
its research claim, that a historical experiment ran as reported, or that all
historical claims have proofs.
