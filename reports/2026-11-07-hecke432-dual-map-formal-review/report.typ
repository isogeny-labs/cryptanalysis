#set page(paper: "a4", margin: 15mm)
#set text(font: "DejaVu Sans", size: 9pt)
#set heading(numbering: "1.")

= Level 432 dual-coordinate formal review

2026-11-07 · producer revision `06335430add4198a2b82efe8db3f0f5c75f03043` · review plan `bda2f489b631aff48860e12fa2616c3d4cdbd068`

== Claim under review

The Lean file declares an integral numerator identity and a conditional affine curve-equation implication for the archived rational formula. The domain is a field with source equation `Y² = X³ − 16` and `X ≠ 0`; the target equation is `V² = U³ + 432`. These declarations do not assert a complete curve morphism, isogeny, degree, duality, or modular-map identity.

#figure(image("proof-boundary.svg", width: 92%), caption: [The solid arrow is the affine equation obligation. Dashed arrows mark separate geometric and modular obligations.])

== Independent checks

The blind round-two reviewer derived the polynomial difference as `432 X⁶`, then derived the rational defect after substituting the source equation. The 128-to-127 mutation fails at the source point `X = 3`, `Y = sqrt(11)` over a real field: its target-equation defect is `−1133/243`. Dropping the source equation fails at `X = 1`, `Y = 0` over the rationals. At `X = 0`, the rational formulas are undefined. These controls bound the equation claim precisely.

The source reviewer matched the Lean coefficients, denominators, hypotheses and pins to the archived Sage script and RESULT at their SHA-256 hashes. The reviewer did not execute Lean and explicitly marked machine status unverified. The proof source has `#print axioms` requests, which are not an axiom audit until their output is captured from the pinned build.

== Review protocol

The first plan had an invalid scalar `review_plan` field; the canonical checker exited 2 before inspecting the first reports. A fresh, precommitted round-two plan preceded two new reviewers. Its `T-1805` and `T-1806` Conductor IDs do not satisfy the checker’s `TASK-*` syntax, so the canonical run exited 1 with five identifier errors. A post hoc temporary alias diagnostic passed all remaining joint, blindness and control checks. That diagnostic is *not* a passing canonical audit of the frozen plan. The original plan, reports, attestations and both failed checker outputs are preserved.

== Open proof boundaries

+ Extend the rational coordinates at `X = 0` and infinity; prove regularity and the characteristic assumptions needed for elliptic curves.
+ Construct the global point map; prove group homomorphism, kernel, degree three, separability and the claimed dual relationship.
+ Formalize the quarter-shift modular construction, q-series comparison, applicable Sturm bound, and cusp normalization that eliminates a constant difference between maps.
+ Replay the archived finite-field enumeration under its own controls if those image/gap claims are to be cited.

== Current verdict

The two independent human/agent reviews support source fidelity and the scoped affine algebra, with the exact counterexamples above. The machine Lean build, named axiom output and canonical independence audit remain pending. This packet does not promote the modular or global-isogeny claims.
