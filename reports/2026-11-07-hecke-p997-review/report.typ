#set page(margin: 19mm)
#set text(font: "DejaVu Sans", size: 9pt)
#set heading(numbering: none)
= p=997 Hecke fiber proof and source review

Technical review T-1791, 2026-11-07. Reviewed source revision
`927d1eada55ff51e87b89930cad48672147e0929`. The review plan was
committed before dispatch at `639fb3de7ae6558a8beed6c119a820edefc266b1`.

== Checked result

The blind reviewer independently derived all five natural-number statements
and found exact counterexamples to three weakened controls. The source
reviewer verified 17 of 17 seal entries, all 18 reviewed directory files
against Git, and a byte-identical scratch audit replay. An independent
finite-field reconstruction over all 997 j-values and ten special twists
recovered 62 generic source classes and 1,800 paired chains; 2,306 archived
edge occurrences were checked. Direct B-point enumeration confirmed both
curve orders are 1,008, each saved three-point preimage coset is complete,
and the archived E image has 72 points with fiber histogram
6 by 12, 60 by 24, and 6 by 48.

The archived audit still passed after changing a valid kernel root to an
invalid one, changing a source j value, or swapping projections between
two source rows. These controls delimit its consistency checks. They do
not contradict the unmodified records, which passed the independent finite
recheck. A full independent Sage quarter-shift reevaluation remains open.

#image("proof-boundary.svg", width: 100%)

== Proof scope

The Lean declarations state conditional arithmetic. The full B-image
interval 79 to 217 and complement 791 to 929 additionally use prior
degree-24 modular-map, reduction, and cusp-image arguments. These geometric
dependencies were not freshly proved in this packet. Explicit compatible
assignments use either 78 or 216 noncuspidal B points while respecting the
saved projected counts and cap; the histogram does not determine an exact
B-image count.

The five arithmetic declarations have fresh machine status passed and
faithful scoped fidelity. The concrete geometric image claim is partial
in this packet, with review outcome inconclusive until its prior bridges
are independently replayed. The archived audit's wider validation reading
needs revision. No official hypothesis or evidence status changes here.

The archived build log pins Lean v4.35.0-rc4 and Mathlib
021c46bdd042f67b538b9f9871d556a93713a9a9 and lists only standard
axioms. A fresh hosted pinned corpus run passed at review branch head
639fb3de7: GitHub Actions run 42339546067. The gate checked 32 added
modules, including this p=997 source. The exact toolchain is absent locally.

== Provenance and independent review

The prime screen was committed before the protocol's stated freeze. The
protocol and resulting census/image first entered Git together afterward,
so pre-execution protocol timing is declared rather than independently
authenticated by Git. The reviewers filed separate attestations and did
not read each other's reports. The existing independence checker returned
exit 2 because the precommitted plan's `review_plan` field is an ID rather
than the nested block its parser expects. The original plan and failure
are preserved instead of retroactively replacing that prior.
The diagram changes no canonical quantitative graph or dashboard input.

== Next checks

Recompute every source-to-quarter-shift projection in Sage. Independently
review the earlier degree,
reduction, and cusp-image arguments. Strengthen the source audit so the
three mutations fail, then rerun the affected source-to-claim review.

Full per-claim findings, code, controls, exact receipts and source-access
lists are in the adjacent `report.md`, `blind/`, and `source/` artifacts.
