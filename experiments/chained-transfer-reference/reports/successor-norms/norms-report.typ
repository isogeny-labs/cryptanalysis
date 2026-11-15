#set page(paper:"a4",margin:16mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= Direct C2 norms for the successor transfers
2026-11-12 · CT25 · exact F101 model · scientific standing unsigned

Both C2 elliptic norms now use direct base-field formulas on arbitrary
balanced classes. Every one of the 12,317 rational classes agrees with the
retained generic divisor norms, including repeated support and both balanced
infinities. The production and generic Phi2/Psi2 graphs also agree on every
input. This integrates the same mathematical maps with an explicit C2
factory. No measured speedup is claimed. PCC0355ab/d14c30/158476.
[pcc:unverified]

#image("norms.svg",width:100%)

== Exact model and matching
C2 is y²=x⁶+22x⁴+10x²+19. The covers are(x²,y) and
(19/x²,19y/x³). Their long cubics are[19,10,22,1] and[58,14,10,1].
Short shifts41/37 give curves(17,91)/(48,48), with orders113/109.
Scale18 identifies them with actual targets(23,7)/(59,27), respectively;
the chart swap orders the actual array E109'',E113''. The generic reciprocal chart uses25/x and19y/x³,
so its ordinate and sign are unchanged. [pcc:unverified]

The old C0/C1 constructor keeps its whitelist and still rejects C2. A
separate explicit factory supplies[19,10,22] to the existing formula
engine. Balanced validation, field, polynomial, elliptic and group engines
remain in place. No other field, curve family or catalog is accepted.
[pcc:unverified]

== Complete exceptional-case coverage
The disjoint degree/zero categories contain
[3,4,232,2,216,232,11628] classes. The comparison includes118 repeated
supports and238 nonzero infinity corrections. Degree0/1/2, A0/B0,
tangent/opposite cases and source x0 all have explicit formulas. Every
output is checked on its actual quotient; all paired additions, orders,
identity and wrong-model controls pass. Source01/receipt0355ab are frozen.
[pcc:unverified]

#pagebreak()
= Proof, references and final acceptance

== Why these are the generic Picard norms
For u=x²+A x+B and v=V0+V1 x, A nonzero gives a symmetric addition slope
-V1/A on the first quotient. The ordinate is eliminated using the support
relation, so individual support roots are not selected. Valid repeated
support carries its Mumford ordinate jet. At A0, parity forcesV0V1=0:
coincident images are doubled and opposite images sum to the origin.
[pcc:unverified]

For the second quotient with B nonzero, invert the support algebra and
reduce19(V0t³+V1t²) modulo t²+(A/B)t+1/B. At B0, the x0 point maps to
the origin and the remaining point is evaluated explicitly. Both source
infinities map to the first origin and to±Q on the second quotient,
Q=(37,19). Thus the second correction is(2n+m-2)Q. Finite-cover pushforward
and its projective completion identify the formulas with the generic Picard
norms, including multiplicities. Finite output equality is not used as a
density argument. [pcc:unverified]

Read SUCCESSOR_NORMS.md/PCC7fb16a, identical to upstream95693e, and the
frozen generic DIRECT_NORMS proof. Seven SuccessorNorms Lean lemmas
check exact C2 curve, reciprocal inverse, shift and scale identities,
PCCc2aaaa. The finite fields, balanced Picard objects and elliptic
functoriality remain written bridges. Formalization is partial.
[pcc:unverified]

== References remain genuine
The original C2 coordinate evaluator remains generic. Generic Phi2 and
quarter-Psi2 versions select old divisor norms; the naive halving route
keeps generic Phi2 evaluation. Complete Phi2/Psi2 tests compare production
and generic outputs on both12,317-class domains and retain dual7,
bijections, paired sums, descent and wrong-model rejection. Both original
109/113 source components retain naive comparisons, reverse196 with
inverses104/64, actual endpoint4 beta alpha and geometric controls.
[pcc:unverified]

== Complete changed guard and scope
Final check.sh04 passes25 native/81 reference unit plus five integration
tests, one pre-existing ignored benchmark, all source guards, formatting
and strictClippy. Three final arithmetic hashes match frozen source04.
Complete96,421-byte raw output is standard-xz archived11,612bytes, with
raw/archive SHA256 and exact roundtrip, PCC03b76b. Source/receipts and
negative history are retained without changing old claims. [pcc:unverified]

The constructor/endpoint change is implemented and locally checked; new
exact-head CI and stacked merge requirements remain separate. Prior CT24
head43a CI43125719626 succeeds25/80+five, gate passes/sign skips,
PCCd942e6. All scientific standing remains unsigned. [pcc:unverified]

No stage, pipeline or ECDLP algorithm improvement is measured here.
Matched comparisons with the index-calculus baseline and rho remain owed
under an admitted protocol. S3/livebudget and vault/ledger limits persist.
Next CT26 tests deferred construction of the quadratic table used by the
reference evaluator; the proposed lower-degree rewrite was a recorded
no-op because its existing formulas are already algebraic.
[pcc:unverified]
