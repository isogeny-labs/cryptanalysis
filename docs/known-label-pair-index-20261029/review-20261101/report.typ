#set page(paper: "a4", margin: 1.7cm)
#set text(font: "DejaVu Sans", size: 10pt)
#set par(justify: false)
= Independent known-label Lean proof review

*Task T-1299 · 2026-11-01 · producer `52baa40a`*

The pinned corpus gate run 41344355706 compiled and audited all four `KnownLabelLeads` and seven `KnownLabelPairIndex` declarations. Its named audit reported zero failing or trusted exceptions. The two reviewed source hashes and full theorem table are recorded in `REVIEW.md` beside this report.

#image("proof-boundary.svg", width: 100%)

== Independent result

The blind reviewer derived the triangle formula $2 R_0 = T_(01) - T_(12) + T_(20)$ from three verified edge equations and the affine cycle constraint $(1-A) z_0 = C$. In $bb(F)_5$, a two-step cycle with $A=1$ and $C=0$ closes for all starts, so closure alone does not recover a label. The source reviewer found the Lean identities faithful at their stated ring, field, and module hypotheses.

== Scope and next proof

The machine status of all eleven named declarations is *passed*. Four ring identities, affine composition and conditional module recovery are *validated_scoped* as algebra. Five other declarations are *partial* for a verified graph or executable interpretation: their hypotheses assume the edge, fixed-point, or label equalities instead of constructing them. The next theorem should map a checked signed elliptic edge into a point-group affine update, establish a closed walk and nonzero recovery coefficient, then replay the recovered scalar or point.

The Python fixture checks one supplied curve with deterministic controls. The stated $tilde(O)(n^2 + N + C)$ field-operation bound is a written model; this review did not measure a complete driver or run a new benchmark. The full local Python suite could not start because `sympy` was missing. The hosted Lean run is native, source-bound evidence; this task did not perform a second local build or independent kernel binary check.

== Review custody

The review plan was committed as `b182f5c4c` before the reviewers were dispatched. Each reviewer attested no access to the sibling report. The available independence checker requires a YAML plan and rejected the precommitted Markdown plan with `no review_plan block`; no automated independence pass is claimed. The complete review, plan, reports, controls and citations are in this directory.
