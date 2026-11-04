# Current Lean corpus gate

`current-corpus-gate.py` preserves a frozen 97-source bridge and separately
checks admitted additions. It binds 91 byte-identical files and their effective Lean pins
to the [October 21 native build archive](../../reports/lean-evidence-audit-20261021/report.md),
then rebuilds and audits the two changed orbit files, the new GLV theorem,
the fixed cubic-gluing certificate, the CM degree-partition arithmetic, and
the PQC modular-arithmetic assay.
The latter two are partial finite proofs, not formalizations of their full
geometric interpretations.
The gate's own fixture and audit sources under `tools/lean/` are checked by
the separate self-test and excluded from the research-file count.
It compares the result with the [November 1 size-dependent GLV cap receipt](../../reports/lean-current-corpus-20261101-glv-cap/receipt.json).
The [October 25 main-update receipt](../../reports/lean-current-corpus-20261025-main-update/receipt.json)
remains unchanged as the record of the fixed-cap (32) binding, which the gate still replays with its own
negative controls; it is no longer the receipt the gate compares against.
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

## Known-label proposed algebra source

At main `47865467f9cc28c316a12ddab017017047815f19`, the tracked research set
contains 167 Lean files: the frozen 97, 68 Hecke additions, the Hasse-square
module, and [Algebra.lean](../../docs/known-label-next-leads-20261028/Algebra.lean).
That count is a source inventory, not a semantic proof-coverage measure.
The [original checks](../../docs/known-label-next-leads-20261028/CHECKS.json)
explicitly record that the last source was unbuilt. They remain unchanged.

The gate now attempts this exact source SHA-256:
`d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d`.
It uses Lean `leanprover/lean4:v4.35.0-rc4` and Mathlib
`021c46bdd042f67b538b9f9871d556a93713a9a9` through the existing
`experiments/hecke-432-formal-ci-20261025` project. All three project input
files are hash-bound independently of the historical producer report.

| Declaration in `KnownLabelLeads` | Statement scope |
| --- | --- |
| `triangle_identity` | `2*a = (a+b) - (b+c) + (c+a)` |
| `signed_second_moment` | `(a+b-c)^2 - (a^2+b^2-c^2) = 2*(a-c)*(b-c)` |
| `signed_third_moment` | `-(a+b-c)^3 + 3*(a+b-c)*(a^2+b^2-c^2) - 2*(a^3+b^3-c^3) = 6*c*(a-c)*(b-c)` |
| `positive_pair_product` | `2*a*b = (a+b-c)^2 - (a^2+b^2-c^2) + 2*c*(a+b-c)` |

Every statement quantifies over arbitrary `a b c : K` with `[CommRing K]`.
The gate compiles original bytes into an isolated temporary module, requires
all four fully qualified native axiom printouts, and invokes
`AuditHeckeAxioms.lean` on the module. The latter enumerates every non-internal
theorem in that module and accepts only `propext`, `Classical.choice`, and
`Quot.sound` as transitive axioms. It rejects an empty or failing audit and
requires the four named theorems to occur in its output. Source hashes are
checked before and after compilation/audit.

These ring identities do not formalize an elliptic-group interpretation,
graph-label recovery (including invertibility assumptions), a probability
theorem, or a performance result. The local Python refusal controls mock
compiler output and establish gate behavior only. A passing native hosted
run at the exact PR head is still required; see the
[open admission record](../../problems/lean-corpus-known-label-admission.md).

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

### Integration reconciliation (2026-10-29)

The separate main-branch correction is documented in
`docs/known-label-next-leads-20261028/CI_INTEGRATION.md`. Its requirement of
exactly four audited theorems is retained alongside fully qualified theorem
identity checks and before/after checks of all three pinned project inputs.
All main-branch refusal cases remain tested through the final known-label route;
neighboring documentation modules remain unreviewed and rejected. Historical
producer reports and native receipts remain bound to their original revisions.

## Coordinate pair-index path/cycle lemmas

`docs/known-label-pair-index-20261029/PairIndex.lean` is separately source-bound
and must natively compile in the same pinned workspace. Its seven explicit
theorems, including the folded affine path and label-recovery statements, must
pass the existing exhaustive module audit with exactly seven audited theorems
and zero failing/trusted exceptions. The previous four-theorem source binding
and all historical receipts remain unchanged. Refusal-control mocks are not
native proof evidence. See that note for the concrete elliptic instantiation,
executable-algorithm and cost formalizations still missing.

## Exact CI engineering regression source

All tracked Lean sources outside the separately tested `tools/lean/` fixtures
are discovered, including `reports/ci-*`. That directory prefix is not an
exemption. A new unregistered report source fails admission.

The original `XedniCoreCompatibility` control file in
`reports/ci-xedni-proof-elaboration-repair-20261030/` is registered at its exact
SHA256 `19dd7b84d1d90d5e7eb81efdb84899f8b08370d5c7d87c87052934349b619947`.
Its bytes remain unchanged. Its explicit build context is the bounded-witness
formal project, with Lean4.35.0-rc4 and Mathlib021c46bdd042f67b538b9f9871d556a93713a9a9;
its three declarations must actually compile and produce all three allowed
foundation audits. Their indented declarations are recognized; a static census
found no declaration-set changes for the existing admitted experiment modules.
Changed source, build pins, missing/extra/duplicate outputs and nonstandard
foundations are refused. The source count rises from173to174; the frozen97-file
bridge remains unchanged. Software mocks test orchestration, not native proofs.
See [the admission record](../../problems/lean-ci-evidence-source-admission.md)
for actual source-f3aa native success:77 added modules, including all three original engineering controls.

After complete declaration and foundation validation, the checker now prints the original native axiom output lines into the successful job log too; complete raw command evidence remains retained. This improves readable custody without changing proof admission.

## Dependency-free core-Lean projects

`CORE_LEAN_PROJECTS` registers self-contained Lake projects that pull no
package (no Mathlib) and pin their own toolchain. For every tracked `.lean`
source under such a project the gate refuses, before any native command, a
changed toolchain pin, a `[[require]]` or non-empty manifest package list, a
source outside the registered library, a root module that does more than
import every other module exactly once, and any proof escape
(`sorry`, `admit`, `sorryAx`, `native_decide`, `axiom`, `unsafe`,
`implemented_by`, `extern`). It then runs `lake build` in the project, requires
the `.olean` of every module, recompiles each module with `lake env lean`, and
admits it only when every `theorem`/`lemma` has its own `#print axioms` line
whose native output stays within `propext`, `Classical.choice`, `Quot.sound`.
`main` routes these paths away from the Hecke Mathlib checker. Controls:
`CoreLeanProjectControls` in `test_current_corpus_gate.py`.

Registered: `research/handbook-ff-ic-ideas-20261103/formal` (library
`HandbookIC`, toolchain `leanprover/lean4:v4.34.1`): the claim statements and
supporting lemmas of the Handbook-of-Finite-Fields idea catalogue. Those
theorems are cost-model and counting lemmas over abstract definitions; none
models the elliptic-curve group law, and none proves a speedup.

## Receipt-bound standalone modules

`RECEIPT_BOUND_SOURCES` registers single `import Init` modules that carry
their own receipt-bound checker (`research/xedni_lift_optimizer_20261101/lean/
XedniAffineCoset.lean` with `check.py`, landed by #1376 under the
`Xedni affine-coset Lean proof` workflow, which left this gate red on `main`
until it was admitted here). The gate pins the source and the checker by
SHA-256, refuses any proof escape and any theorem without its own
`#print axioms` line, runs the checker natively, and admits the module only
when the printed axiom sets name exactly the registered theorems within the
standard foundations and the checker reports verification. A changed proof or
checker is a gate change. Controls: `ReceiptBoundSourceControls`.
