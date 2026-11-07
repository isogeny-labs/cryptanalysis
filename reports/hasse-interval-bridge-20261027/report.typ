#set page(paper: "a4", margin: 1.2cm)
#set text(font: "Liberation Sans", size: 9pt)
#set heading(numbering: "1.")
= Centered Hasse interval bridge: scoped proof review
*27 October 2026 UTC · T-503 · source `f448907`*

`CurveAudit.unique_multiple_from_center_bounds` proves a conditional natural-number result: two multiples of `r` in the same center-radius interval agree when `2*radius < r`. It does not prove the full P-192/P-224 curve-order certificate.

#figure(image("proof-boundary.svg", width: 100%), caption: [Verified Nat implication and separate curve-order obligations. No performance data were generated.])

== Separate verdicts
#table(columns: (2.2fr, 1fr, 1fr, 1fr), inset: 5pt,
[*Claim*], [*Machine*], [*Fidelity*], [*Overall*],
[Centered Nat interval uniqueness], [passed], [two reviews], [validated scoped],
[Full P-192/P-224 order proof], [missing bridges], [partial], [not verified])

== Exact evidence
Source SHA-256: `f72e23b6d89fa7259b2502348b5af850bc18b8cf5f429b143a7292427358c400`. Pinned Lean: 4.34.1. The isolated source build and transitive audit passed. Both named theorems showed only `propext` and `Quot.sound`; the audit reported zero failures and zero `native_decide` exceptions. The `sorry` false theorem and missing module controls were rejected by the audit.

The first boundary fixture contained literal backslash-u escape text and failed to parse. Its logs and negative receipt are preserved. A corrected fixture was built and audited in a separate receipt. The sharp boundary case is `r=6`, `radius=center=3`, `n=0`, `m=6`, where `2*radius=r` and the values differ.

== Review and limit
A blind reviewer re-derived the arithmetic statement. A separate reviewer checked the Lean source against the proof map. The source reviewer disclosed generic process-skill and unrelated memory reads beyond the plan's literal source list; no sibling report was read. This limits a strict file-isolation assertion and is retained in the review record. Attestations were self-reported.

A full certificate still needs exact point order and Lagrange divisibility, Hasse for the actual curve, integer-bound conversions, and binding to concrete inputs. The machine trust boundary is the pinned Lean kernel; no independent `lean4checker --fresh` run was available. No experiment or performance data were generated, so no quantitative dashboard values changed. Raw logs, commands, hashes, and both reviewer reports accompany this PDF.
