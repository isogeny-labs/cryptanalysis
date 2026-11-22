# Exploratory D=-2631 mixed floor-kernel record

Start with the [reviewed report](RESULT_REVIEWED.md) and [PDF](report.pdf).
This is an **exploratory** relation-stage record: an earlier public protocol
has not been established. The original protocols and [sealed report](RESULT.md)
are retained as historical evidence, including their prospective wording.
The current qualification supersedes that wording without changing the saved
768-point matrix, ranks, witnesses or mathematical proof obligations.

The [evidence diagram](evidence.svg) has editable [Graphviz source](evidence.dot).
The [rank plot](ranks.svg) uses the saved exact values in `validation.json`.
Regenerate the visual report with `python3 build_review_report.py` from this
directory (Graphviz, ReportLab and PyMuPDF are required).

## Sealed source and current audit version

The original `SEAL.json` and `seal.py` are unchanged. Before this review,
`seal.py --check` failed because `formal/MixedSix.lean` had changed from
`710bbf06...` to `217d9a05...`. The difference removes `public` from the two
theorem declarations and moves qualified axiom-print commands inside their
namespace. The theorem statements and proof bodies are unchanged; this
does not make the two source byte streams identical.

The exact original source is preserved as
[`review-20261030/MixedSix.sealed.lean.txt`](review-20261030/MixedSix.sealed.lean.txt),
recovered from published revision `b33318c17e91cd4fd597c55ae99bf810ceb18b3d`
and checked against the original seal. The
[version record](review-20261030/provenance.json) binds both sources and explains
the transition. The original seal still validates the historical source;
it is not relabeled as a seal of the current Lean file.

Run `python3 verify_review.py --self-test` to check every original sealed
digest against its original source bytes, the explicitly pinned current
Lean source, the unchanged statements/proofs, and the new visual/report
manifest. This additive checker does not replace, edit or relax the original
seal checker or the hosted Lean corpus gate. The old `seal.py --check` command
continues to report the documented source-version mismatch in the live tree.

Hydrate `producer.stdout` with the repository artifact tool before checking
the original bundle. In this session that command could not run because the
AWS CLI was absent. The exact 82,025 bytes were instead recovered from the
same immutable published GitHub revision and matched both the artifact
manifest and the original seal. No remote object or frozen file was changed.

## Graph and scope review

Checked `experiments/volcano-ic/figures/census.svg` and `ecdlp.svg`, the D39
`evidence.dot` and `result.dot` rank/control diagrams, and the curve catalog.
Their Koblitz descendant or F367 source data and claims do not change under
this documentation qualification. No new curve identity, isogeny route,
subgroup transport or ISO1 admission is added. The new diagram concerns the
saved F23743 matrix and separates external exact checks from the conditional
Lean implication and the missing full correspondence bridge.

This review renders saved evidence and checks provenance only. It does not
rerun Sage or Lean, execute a new experiment, establish a timing comparison,
or close the full class-action-to-rational-lift formalization obligation.
