#set page(paper: "a4", margin: 16mm)

#set text(size: 10pt, font: "DejaVu Sans")

#set par(justify: false, leading: 0.6em, spacing: 0.8em)

#set heading(numbering: none)

= Constructive projection of the synthetic LP graph cases

#text("Both unchanged original Lean gates accept the eight named statements in LPGraphCases02: ten audited declarations including two generated defining equations, zero trusted declarations. The complete source, original outputs and eight exact PCC statement bindings are in the immutable proof evidence, data be98f8. These are scalar relation-system statements over Lean.Grind.CommRing; inverse-of-two and nonzero hypotheses are explicit. All new claims remain unsigned. [pcc:unverified]")

#image("projections.svg", width: 100%)

#text("Write f,g,eta for the two nonbasepoint factor-base coordinates and the final target coordinate. Each raw edge contributes its two LP endpoint occurrences, its factor-base terms, and -eta. An LP variable is a nuisance coordinate: the projection asks which f,g,eta admit a complete LP lift. The definitions below match the indicated synthetic equations by inspection; no formal original-program-to-matrix bridge is claimed. [pcc:unverified]")

== Relation to the completed native controls

#text("The original gated CI at Consumer source c045dfdf, run43793694178, retained all fourteen complete synthetic F101 inputs, presentations and projection certificates. The ungrounded even cycle, shared-root odd triangles and parallel edges each have projected-image dimension2 and rooted-uncapped kernel dimension3. The literal original rooted routine starts from grounds; these three fixtures have none. Their behavior is a known small-system control, with no novelty inference. The new separately coded raw reconstruction has compiled and passed strict Clippy; its native equality checks still await the changed-source gated CI. Data8af458 concerns the earlier native source only. [pcc:unverified]")

#text("The Lean module has no concrete F101 or F2773073 instance and does not prove the numerical dimensions, execution of the original routine, geometric membership, a global character, or a cost result. The existing finite certificate replayer checks numerical matrices; the new direct statements supply complete existential scalar lifts instead of assuming image completeness. [pcc:unverified]")

== Reproduction and retained failures

#text("Run the unchanged Consumer proof gate under Lean4.34.1 and the unchanged Root gate under Lean4.35.0 with one compiler worker and the original static proof-workflow memory defaults, 120 seconds per gate. Only propext, Classical.choice and Quot.sound occur in the audits. lean4checker is unavailable. Native/full-population limits remain unchanged. [pcc:unverified]")

#text("The two earlier 2GiB virtual-memory startup aborts, minimal compiler startup diagnostic, added managed-heap auditor failure, and resumed PATH failures are retained in bf5b6e,760a08,f7c1f5,201752,ef3e5f. Attempt04 passed seven named results; attempt06 adds the parallel-edge result and passes all eight. No earlier failure was replaced by a passing log. [pcc:unverified]")

#text("Sources checked: frozen prospective protocol; fourteen literal raw fixtures; whole original cycle source; finite projection producer and separate Euclidean replay; source-review receipt and primary Diem2012 pages644–645/653–654. KB MCP is absent and repository wrapper status exits127; the atlas repository remains locked. These access gaps do not establish absence. Canonical geometric transfer graphs remain current because the results concern these synthetic scalar graph systems. [pcc:unverified]")

#pagebreak()

== Written proofs and exact hypotheses

#text("1. Even four-cycle: the four equations have factor terms f,g,f,2f. Their alternating sum is -g, so every lift has g=0. Conversely, when g=0, use LP coordinates (0, eta-f, f, eta-2f). This proves the complete equivalence over any commutative ring, without a span assumption or inverse of two. Declaration even_four_projection_iff, claim c49a93. [pcc:unverified]\n2. One odd triangle: each edge has factor term f. If 2*half=1, assign every LP coordinate half*(eta-f). This lifts every f,eta. Declaration triangle_has_lift, claim ac4358. [pcc:unverified]\n3. Two odd triangles sharing a root: alternating the three equations of each triangle gives 2a+f-eta=0 and 2a+g-eta=0 at the shared LP coordinate a, hence f=g. If f=g and 2*half=1, reuse the single-triangle lift for both. Declaration shared_odd_projection_iff, claim c14509. [pcc:unverified]\n4. Two disconnected odd triangles: their roots are different variables. Under the same inverse-of-two hypothesis, apply the single-triangle lift separately to f and g. There is no equality constraint between them. Declaration disconnected_odd_has_lifts, claim 18029c. [pcc:unverified]\n5. Ordinary ground on an odd triangle: the ground fixes a=eta. The triangle identity gives eta+f=0. Conversely, (a,b,c)=(eta,-f,eta) is a lift under this condition, in any commutative ring. Declaration grounded_triangle_projection_iff, claim cef04b. [pcc:unverified]\n6. Half ground and one tree edge: the equations are 2a+2f-eta=0 and a+b+f+g-eta=0. Under 2*half=1, take a=half*(eta-2f) and b=eta-f-g-a. Every f,g,eta lifts. Declaration half_ground_edge_has_lift, claim ae9438. [pcc:unverified]\n7. Two parallel edges: subtract a+b+f-eta=0 and a+b+g-eta=0 to obtain f=g. Conversely use (a,b)=(0,eta-f). No inverse of two is required. Declaration parallel_edges_projection_iff, claim 6aee73. [pcc:unverified]\n8. Excluded vector: in a nonzero ring, the even-cycle projected vector (f,g,eta)=(0,1,0) has no lift by statement 1. Declaration even_four_no_unit_lift, claim e95a78. [pcc:unverified]")
