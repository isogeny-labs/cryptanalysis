#set page(paper:"a4",margin:15mm)
#set text(font:"DejaVu Sans",size:9.2pt)
#set par(leading:.4em)
#let data=json("render-inputs.json")
#let green=rgb("#267044")
#let blue=rgb("#365e87")
#let gray=rgb("#a1a8b0")
#text(size:15.5pt,weight:"bold")[One compatible full-group candidate in the original family]
#v(4pt)
#text(fill:blue,weight:"bold")[EXHAUSTIVE FINITE CENSUS · native88f828 · source8113951 · unsigned]

Exactly one of the216 triples in the original six-model HLP family has both compatible transported kernels and eligible supplied-source models. It uses cases(2,0) → (0,1) → (2,0), with factors116 →39 →36. The complete native census and a separate Lean finite-data calculation agree. This identifies a candidate for full-group construction; a complete Jacobian evaluator for these models is the next experiment.

== All18 models and all12 compatible edges
The graph retains every model and every compatible edge, including ineligible endpoints. Green is the unique supported path. Blue vertices are other eligible models; gray vertices are ineligible supplied-source models. Each label gives the original case and D value. Compatibility alone does not settle the base-field/supplied-source condition.

#let xs=(65pt,255pt,445pt)
#let ys=(38pt,72pt,106pt,140pt,174pt,208pt)
#box(width:510pt,height:234pt)[
  #for pair in data.compatible_pairs {
    let e=pair.edge
    let a=pair.source_index
    let b=pair.target_index
    place(top+left,dx:xs.at(e),dy:ys.at(a),line(start:(0pt,0pt),end:(xs.at(e+1)-xs.at(e),ys.at(b)-ys.at(a)),stroke:(if pair.supported_compatible {2.2pt+green}else{.65pt+gray})))
  }
  #for domain in range(3) {
    place(top+left,dx:xs.at(domain)-62pt,dy:0pt,box(width:124pt,align(center,text(weight:"bold")[Original E#(domain+2)])))
  }
  #for vertex in data.vertices {
    let chosen=data.selected_indices.at(vertex.domain)==vertex.index
    let ink=if chosen {green}else if vertex.eligible {blue}else{gray}
    let fill=if chosen {rgb("#e4f2e8")}else{white}
    place(top+left,dx:xs.at(vertex.domain)-62pt,dy:ys.at(vertex.index)-12pt,
      block(width:124pt,height:24pt,inset:4pt,fill:fill,stroke:.6pt+ink,
        align(center,text(size:8.8pt,fill:ink)[case(#vertex.case.at(0),#vertex.case.at(1)) · D#vertex.D])))
  }
]

Both adjacent transports come from the original degree13 elliptic maps and their actual three-factor conjugates. The census checks all64 coordinate rows, all4096 addition/pairing rows and the entire135-mask set per edge. It compares complete eight-vector kernel images with a separate basis-span reconstruction. The graph does not identify models by coefficient-array equality or introduce a twist.

#table(columns:(1.65fr,1fr),inset:6pt,stroke:.5pt+rgb("#bbc4cf"),
 [*Complete finite workload*],[*Actual result*],
 [Models / adjacent candidate pairs / triples],[18 /72 /216; none filtered out],
 [Eligible vertices at E2 /E3 /E4],[4 /2 /2],
 [Compatible pairs / supported compatible pairs],[6+6 /1+1],
 [Supported compatible triples],[Exactly1: indices[4,1,4]],
 [Whole records / malformed inputs],[311 /6 actual rejections],
 [Whole-class omissions],[4 actual removals reject101, no output],
)

#text(size:8pt)[Original ell2,773,073/order11,092,292 over F223[z]/(z³−3), with intended Jacobians over F223. The original fixed D12/D24/D67 supplied-source negatives remain intact. This is a finite-family result, not a classification of all possible Jacobians or quotient presentations.]

#pagebreak()
#text(size:15.5pt,weight:"bold")[Independent finite proof and the construction to test next]
#v(4pt)
#text(fill:green,weight:"bold")[BOTH ORIGINAL LEAN GATES · SIX ROOTS · ZERO TRUSTED ASSUMPTIONS]

The actual finite data are encoded independently in Lean: all18 masks, all D values and seven smoothness vectors per row, all stored eligibility flags, and both complete64-entry image tables. The proofs recompute eligibility from nonzero factors and an exhaustive F223 square test. For each candidate pair they compare every one of the64 kernel membership bits under the actual table, rather than assuming the native compatible-edge flags.

The six theorems check complete data shapes, both table bijections, all18 recomputed eligibility flags, coverage of every Fin6 triple, the actual supported pair/triple lists, and uniqueness of the accepted path. Both unchanged original Lean4.34.1/4.35.0 gates pass all six roots with zero trusted assumptions. Exact local statement bindings are retained in the accompanying evidence.

The first proof encoding stopped because ordinary reduction could not evaluate array operations. Its source and failed gate remain preserved in69d82d. The successful encoding uses the same literals as lists and ordinary kernel reduction. No trusted evaluator, user axiom or desired-path hypothesis is used.

== Freeze these original-source models for the next protocol
#table(columns:(.7fr,.6fr,.7fr,1.65fr),inset:6pt,stroke:.5pt+rgb("#bbc4cf"),
 [*Domain*],[*Case*],[*D /root*],[*Kernel /stored base point*],
 [Original E2],[(2,0)],[116 /89],[1155177839943778305\ (1:0:28)],
 [Original E3],[(0,1)],[39 /40],[5188291906266857505\ (1:0:90)],
 [Original E4],[(2,0)],[36 /6],[1155177839943778305\ (1:1:165)],
)

Under the explicit HLP quotient and geometric/program bridges, compatible product kernels allow the degree13 product maps to descend between these quotients. The next implementation must construct and check the actual prime-field/quadratic Jacobian backends, full-group correction and halving behavior, both adjacent dual norms and endpoint composite, and full-order inverse recovery. Edge13 is the elliptic degree and intended Jacobian dual-norm scalar; geometric degree13³ requires the stated three-dimensional quotient bridges.

The prospective successor will retain all full-cofactor sectors, all four halves and duplicate corrections, all exceptional descriptors under both outgoing maps, independent original elliptic checks, whole public/addition populations and actual entire-class omission controls. It must publish compiled source and obtain a fresh exact original checkpoint before native execution. No current full-group implementation result is inferred from the finite graph.

== Existing prime-only result and cost boundary
The original-prime reprojection976f50 at7a600a2 keeps its separately frozen cases(0,0)/(0,1)/(1,0), explicit [4] projection and strict cofactor rejection. Its complete1,077-record native result and report1f3c4c remain unchanged. The present census has its own protocol0158c5, publishedc1cbc188 before implementation, and does not revise those prior choices after observing this graph.

Known initial elliptic points remain a stronger presentation than opaque Jacobian inputs. A full-group implementation must keep that route and complete primitive setup/online accounting in its comparison. The selected source calls are unpriced; this census provides no timing or computational-advantage measurement.

#text(size:8pt)[Evidence: native88f828 at8113951/build01; original checkpoint43686905905/job132729176127/artifact14150917768, all28 matching members and immediate gate0; one unfiltered test0/worker0/supervisor0, all13 phases expected, all1172 input hashes and actual binaries exact; prospective0158c5; actual-data proof and bindings; HLP math/9809210v1 section4.1/Lemma13/Propositions14–15 and field qualification. KB remains unavailable and the autoresearcher vault stays locked. All whole source/raw/executables/proofs/failures/report drafts are retained for NEW24.]
