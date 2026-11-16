#set page(paper:"a4",margin:15mm)
#set text(font:"DejaVu Sans",size:9.5pt)
#set par(justify:false)
= Actual prime-field second hop and compressed chain
2026-11-12 · fixed F101 models · scientific standing unsigned

The complete changed check passes:25 native tests,98 reference unit tests
and five integrations,with one historical ignored benchmark. All13 source02
hashes stay unchanged. PCC3be24d preserves the entire155,019-byte raw log as
standard XZ16,056 bytes,with raw/archive hashes,exact roundtrip and after-source
receipt. The run started09:35:04UTC and ended10:22:08UTC;these intervals are
correctness-run provenance,not performance measurements. [pcc:unverified]

#image("chain.svg",width:100%)

== What changed in the actual consumer
SuccessorChain.forward and dual now select cached standalone prime-field
contexts. Exact previous bodies remain forward\_reference and dual\_reference;
the new complete comparisons call them explicitly. Old generic,quarter,
naive and original test bodies remain unchanged. Accepted T2 data,norm/pullback
and forward/reverse evaluator bodies are reused after paths,visibility and
reference-name adaptations. Existing field,polynomial,elliptic,Kohel and
Balanced engines are reused. Source custody isd0ad0a. [pcc:unverified]

The standalone evaluators construct no Richelot or extension-field map.
The retained comparison context still constructs those old maps for its
reference,generic,naive and geometric tests. Redirecting the existing methods
does not remove these cold construction costs. This is fixed public-fixture
coverage,not a production catalog or general-prime implementation.
[pcc:unverified]

#table(columns:2,stroke:0.4pt,
 [New acceptance component],[Complete retained controls],
 [Two T2 norms],[Each12,317 oldH2 outputs;group,model,poles,repeated support,infinities],
 [Two T2 pullbacks],[All109/113 oldR2P2 outputs;norm4,offdiagonal0;24,650 ordered sums],
 [Second forward and adjoint],[Each12,317 old outputs;both full norm7 compositions;actual beta/betaHat],
 [Compressed forward and reverse],[Each12,317 old/staged outputs;both full norm49 compositions],
 [Original elliptic sources],[Every109/113 point/scalar,direct endpoint,reverse196,recovery104/64],
)

All components retain identity,bijection,negation,fixed-partner addition,
wrong-model and wrong-quarter controls. The original92 tests remain,including
generic/naive,geometric kernels,branch automorphisms,independent7 certificates
and chained transport. No case was filtered from the complete guard.
[pcc:unverified]

== Exact custody and failures
Thirteen source snapshots and before/after hashes bind this run. The initial
missing reverse-child registration E0433/a749e8 remains with its full source
and diagnostic;native tests did not run on that failed version. A custody
comparison first mistook rustfmt wrapping after reference renaming for a
source change;the failed driver/status are retained,and the accepted guard
formats the reference-name adaptation before exact comparison. Arithmetic
and acceptance criteria stayed unchanged. [pcc:unverified]

#pagebreak()
= Global formulas,exceptions and recovery
SECOND\_CHAIN\_PROOF.md retains the admitted Picard/quotient/polarization
dependencies. Write K\_i for the old product-to-Jacobian pulls and H\_i for
their adjoint norms. H\_iK\_i and K\_iH\_i are[4]. The old maps satisfy
4Psi1=K1 alpha H0 and4Psi2=K2 beta H1. The middle relation gives
16Psi2Psi1=4K2 beta alpha H0;cancel4 in Hom to obtain4F=K2 beta alpha H0.
Taking adjoints gives4FHat=K0 alphaHat betaHat H2. Point groups are not
assumed torsion-free. [pcc:unverified]

On rational groups of order12,317=109 times113,the single public quarter
is82 modulo109 and85 modulo113. Compressed forward takes T0 norms,alpha
then beta,and T2 pulls;reverse takes T2 norms,betaHat then alphaHat,and T0
pulls. No middle T1 class occurs in these expressions. The composite retains
geometric degree2,401 and both adjoint norms49. [pcc:unverified]

#table(columns:3,stroke:0.4pt,
 [T2 component],[N,Q,M coefficient vectors,low first],[Infinity image],
 [(59,27),order109],[[97,93,7,0,97];[55,0,1];[71,49,20,63]],[(97,63)],
 [(23,7),order113],[[74,0,81,42,64];[23,0,1];[37,9,9,35]],[(64,35)],
)

Exact curve identities and the old norm4/degree argument identify these
quartics globally using a difference-degree bound16. Independent flat replay
checks finite points,infinities and every geometric pole. The first T2 pole
orbit has degree4 and is absent from F101^6;it creates no degree≤2 rational
pole support. The second has rational poles(49,12)/(49,89). Native exception
counts keep both outcomes. Finite-fibre units and jets handle repeated
supports;the signed infinity degree drops are[2,1]. [pcc:unverified]

== Reverse normalization and public recovery
BetaHat uses cubics[13,62,81,1]/[11,64,23,1] and alphaHat uses
[58,26,58,1]/[29,88,45,1]. Each normalized Kohel dual needs checked scale29
before the next stage. Since49 times4776 equals1+19 times12317,the rational
inverse is[4776]FHat. For an original embedded elliptic source,H0K0 adds4,
so the returned source norm is[196],recovered with104 modulo109 or64
modulo113. These are public scalars,not logarithm labels. [pcc:unverified]

Faithful upstream Lean modules cover conditional norm49/source196,two-hop
clearing and rational recovery. Actual varieties,Picard maps,projective
extension,global kernel degree and geometric distinction remain written or
partial. Full rational replay does not prove those geometric properties.
Independent whole-map/kernel replay is separate upstream work. [pcc:unverified]

== Integration and next checks
This child starts immediate ready parent1507 at93587b9,tree0f032e. Parent
exact CI43191178913 succeeds25native/92reference+five;whole225,939-byte log
to XZ29,088/API/hash/roundtrip isf72285/root5bbe4d. This98-test head needs
its own exact-head CI and review. Integrate bottom-up,retarget/rerun after
parents land,and respect the frozen-ledger forks and actual merge gates.
[pcc:unverified]

Global sources are crypto b351d685:T2\_QUARTIC\_PROOF/f9cf19,
CHAIN\_COMPRESSION\_PROOF\_V2/89e13d,REVERSE\_CHAIN\_PROOF/001dff and old
Picard/quotient proofs. Old proofs,reports and negative controls remain frozen.
Cold construction/transfer/solve/recovery/verification costs await actual
S3/live-budget admission9e1812;no paid run,solver,novelty or measured advantage
is claimed. Atlas vault remains locked and KB/ecdb unavailable.
[pcc:unverified]
