#set page(paper:"a4",margin:16mm)
#set text(font:"DejaVu Sans",size:9.4pt)
#set par(leading:.45em)
#let data=json("render-inputs.json")
#let blue=rgb("#365e87")
#let green=rgb("#267044")
#let gray=rgb("#bbc4cf")
#text(size:17pt,weight:"bold")[Quotient transfer norms and DLP linearity derived from source data]
#v(4pt)
#text(fill:green,weight:"bold")[CONDITIONAL ALGEBRA · eddc37 · NINE NAMED ROOTS · UNSIGNED]

Both unchanged original Lean4.34.1/4.35.0 gates pass the new module on its first attempt. All nine planned mathematical statements and all nine exact local bindings pass. Each gate audits21 declarations in total: the nine named conclusions, ten explicit proof-field projections and two generated sizeOf specifications. All21 have zero trusted assumptions.

== Hypotheses stay at the source
#table(columns:(1fr,1fr),inset:7pt,stroke:.5pt+gray,
 [*Explicit presentation*],[*Explicit compatible edge*],
 [Phi:A→J and r:J→A\ Phi(r(x))=x],[g:A→B; additive/subtraction/zero/Z-linear],
 [Phi additive/subtraction/zero/Z-linear],[Phi(a)=0 implies Psi(g(a))=0],
 [r arbitrary; no linearity or rationality],[Reverse gh with the analogous kernel condition],
 [Geometric-point IntModules],[Source duals gh(g(a))=n·a; g(gh(b))=n·b],
)
#align(center)[#text(fill:blue,weight:"bold")[T(x)=Psi(g(r(x)))  ·  S(y)=Phi(gh(s(y)))]]

No structure field assumes a desired T/S commuting square, linearity, reverse norm, recovery or injectivity. The full source is retained and pinned along with the exact theorem statements. Kernel transport is required on the entire stated source kernel; finite mask evidence is a separate bridge to its actual geometric instance.

== Derived path through the proof
#table(columns:(1.05fr,1.65fr),inset:7pt,stroke:.5pt+gray,
 [*Representation independence*],[Phi(a)=Phi(b) gives Psi(g(a))=Psi(g(b)).],
 [*Source identity*],[T(Phi(a))=Psi(g(a)) follows from the section.],
 [*Linearity*],[Compare r(x+y) with r(x)+r(y), and r(z·x) with z·r(x). The section itself is never assumed linear.],
 [*Both reverse norms*],[S(T(x))=Phi(gh(g(r(x))))=Phi(n·r(x))=n·x; likewise T(S(y))=n·y.],
 [*Two-edge collapse*],[The middle derived source identity removes the intermediate section. One initial section and final quotient suffice.],
 [*Recovery / injectivity*],[A Bezout inverse recovers each annihilated input; equality of transfer images then gives equality of those inputs.],
)

Integer linearity supplies T(d·G)=d·T(G). Injectivity is proved on the stated annihilator carrier, so the scalar relation has unique recovery there. The proof does not receive an unknown logarithm witness. Adjacent n=13 norms can be fed into the existing two_pair_norm theorem, together with the derived linearity, to obtain the169 endpoint norm.

Recovery assumes order·x=0 only for its input; injectivity assumes it for each of the two compared inputs. There is no finite-order assumption on every geometric point and no inverse-two operation on the full cofactor group.

#text(size:8pt)[Prospective2de4aa publisheda0ec881 before source; proof source publisheddbdfd52; original full-group finite nativee245d0/whole701 and prior7b5f49-da2fe7 remain separately scoped. All1,440 version03 references and343 original producer science hashes remain unchanged. Standard quotient algebra, no novelty or calibrated advantage claim.]

#pagebreak()
#text(size:17pt,weight:"bold")[Exact statement bindings and the remaining bridges]
#v(4pt)
#text(fill:blue,weight:"bold")[BOTH GATES:21 DECLARATIONS · NINE LOCAL BINDINGS · ZERO TRUSTED]

#table(columns:(1.8fr,.65fr),inset:6pt,stroke:.5pt+gray,
 [*Named mathematical conclusion*],[*Binding*],
 ..data.bindings.map(row=>([#row.label],[#row.claim_id])).flatten(),
)

The original gate also audits the ten propositional structure projections and the two generated sizeOf specifications. Those12 declarations are explicitly listed in the coverage receipt. No planned root is omitted, no gate is replaced and no desired transfer identity is inserted as an input. The local binding passes remain unsigned, as do all project claims without the required backend standing.

== Actual integer witnesses
Ordinary kernel reduction checks3,413,013×13−4×11,092,292=1 and9,648,325×169−147×11,092,292=1, together with both coprimalities. These are the published original full-order witnesses. They certify arithmetic, not a field model or Jacobian order.

== Geometric sections do not assert rational sections
The generic presentations concern geometric points over an algebraic closure. The section can choose a non-rational representative. Rational output is obtained separately from equivariance and full kernel transport, as represented by the earlier ChainDescent.corrected_output_fixed argument. Identifying the generic source modules, kernels, sections and edges with actual HLP quotients and runtime lifts remains explicit.

The actual field/HLP/geometry/Frobenius/Picard/order/program bridges are not discharged by the generic algebra alone. The source degree13 maps and signed duals, unique original supported triple, finite full-group701 study and known-point controls provide separate evidence. HLP section4.1/Lemma13/Propositions14–15 retain their separably closed and quadratic base-field qualifications.

== Checkpoint and computational scope
The isolated induced-map branch preserves the exact25801fe native CI revision while its complete replay runs. It is the sole active consumer ledger. Normal fast-forward to this branch must precede any acceptance-ledger append on the original research branch; no rebase, rechain or force update is permitted.

This closes a conditional proof step before the existing composite-norm and inverse statements. It constructs no new curve and makes no calibrated cost or computational-advantage claim. Prime-field index calculus on the fixed original models, complete primitive/setup/online costs, strongest references and known-point baselines remain next work. Native failure99d448/all693 records and all older negatives remain preserved. Future custody is NEW26.

#text(size:8pt)[Sources: full InducedFullTransfer.lean, both original gate logs/coverage, all nine exact binding records, proofeddc37, prospective2de4aa/a0ec881, original ChainDescent/FullGroupNorm sources, HLP math/9809210v1 and the unchanged nativee245d0 record. All source/raw/proof/report bytes are retained; no signed-standing promotion.]
