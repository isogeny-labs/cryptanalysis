# Current Lean corpus gate

`current-corpus-gate.py` checks the 96 tracked research Lean files at the reviewed
source versions. It binds 91 byte-identical files and their effective Lean pins
to the [October 21 native build archive](../../reports/lean-evidence-audit-20261021/report.md),
then rebuilds and audits the two changed orbit files, the new GLV theorem,
the fixed cubic-gluing certificate, and the CM degree-partition arithmetic.
The latter two are partial finite proofs, not formalizations of their full
geometric interpretations.
The gate's own fixture and audit sources under `tools/lean/` are checked by
the separate self-test and excluded from the research-file count.
It compares the result with the [October 25 main-update receipt](../../reports/lean-current-corpus-20261025-main-update/receipt.json).
The [previous CM receipt](../../reports/lean-current-corpus-20261025-cm/receipt.json)
remains unchanged. Main's reviewed C analysis repairs have a new whole-file
hash; the gate checks that source against its current live binding, while
replaying the original selector assertions and both negative controls on
the old pinned source and its byte-frozen receipt in
`reports/ghs-pr-1104-main-integration-20261025/`. No Lean theorem, selector
assertion or historical receipt is overwritten.
The earlier [95-source receipt](../../reports/lean-current-corpus-20261025/receipt.json)
remains preserved.
The [October 24 receipt](../../reports/lean-current-corpus-20261024/receipt.json)
remains unchanged as historical evidence.
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
