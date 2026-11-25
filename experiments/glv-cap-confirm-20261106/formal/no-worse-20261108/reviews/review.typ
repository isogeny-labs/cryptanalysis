#set page(paper: "a4", margin: 18mm)
#set text(font: "DejaVu Sans", size: 9pt)
#set par(leading: 0.55em)

= Independent review: GLV cap no-worse logic

*Subject:* PCC-20261108-5903ae, cryptanalysis PR #1445, reviewed producer head
`8e8c49b6e50463988710f21c5253172176610fbf`.

*Machine:* Passed locally for seven named Lean declarations under Lean 4.34.1,
each with no axioms. The proof gate audited ten declarations with zero failing
and zero trusted native evaluations. One generated structure declaration uses
`propext`. *Fidelity:* faithful_scoped. *Outcome:*
validated_scoped for the printed interval-order counterexample. PCC standing
remains unverified at review time. This is a technical proof review, with no
official experiment decision.

== Observation and comparison

The frozen `analyze.py` rejects a pooled size exactly when its interval lower
endpoint exceeds one. The four published pooled lower endpoints are below one,
so the registered pooled check passes. The separately printed `j = 0` 95%
interval is [0.9860137324692078, 1.0186699532206690]; it crosses one.
Its point estimate is 1.0019840110118106. The pooled intervals are labelled
98.75%; these are distinct published summaries.

#figure(
  image("intervals.svg", width: 100%),
  caption: [Published ratio intervals against the 1.0 threshold. Source:
  `experiments/glv-cap-confirm-20261106/results.json`; printed aggregate
  endpoints, no raw-row replay.],
)

T-1911 independently derived the counterexample from the minimal blind card.
T-1912 directly compared the Lean predicate and exact decimal endpoints with
the frozen source, result JSON, erratum and PCC claim. Their reports agree:
pooled passage does not bound the separate family upper endpoint. All five
published intervals are well formed; the witness is nonvacuous.

== Checks, limits and custody

The binding script passed normally and under Python `-O`. Scratch source,
JSON, card and Lean endpoint mutations were rejected. Lean negative controls
for a pooled lower endpoint above one and a family upper endpoint below one
failed as expected. The source reviewer notes that textual predicate matching
alone is weak; exact frozen source/result hashes, direct inspection and the
pushed PR head bind this reviewed version.

The theorem does not establish bootstrap coverage, raw operation counts,
historical binary identity, actual family harm or solver correctness.
`lean4checker --fresh` was unavailable. The original erratum claim and this
PCC claim remain unverified. The pre-review plan was committed before dispatch;
both reviewers attest they did not read each other's report before filing.
No automated independence checker was present in this repository.

*Next action:* Archive the attestations and this report; rerun binding and Lean
on the publication head, then await every applicable hosted check before
merging. The historical chart is unchanged; this is a new explanatory visual.

*Full technical packet:* `reviews/REVIEW_REPORT.md`, `reviews/blind.md`,
`reviews/source-fidelity.md`, and `REVIEW_PLAN.md` beside the Lean module.
