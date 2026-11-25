#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.45em)
#text(size:17pt,weight:"bold")[The fixed second-hop model is unsupported]
#v(3pt)
#text(fill:rgb("#a14b35"),weight:"bold")[UNSIGNED NEGATIVE RESULT · claim27fb3a · protocol23ab48]

The actual second elliptic hop exists. Its full transported gluing kernel uniquely matches HLP(2,1), whose discriminant is D=12. This is nonsquare in K=F223[z]/(z³−3). The matched prime-field quartic is smooth and has a rational point, but the supplied-source Jacobian identification is unsupported. No second Jacobian map or computational gain follows.

#image("flow.svg",width:100%,height:60mm,fit:"contain")

#table(columns:(1fr,1fr,1fr,1.4fr),inset:3pt,align:left,
[*HLP case*],[*D in F223*],[*sqrt(D) in K*],[*Selection status*],
[[0, 0]], [100], [present], [retained],
[[0, 1]], [47], [present], [retained],
[[1, 0]], [10], [absent], [retained],
[[1, 1]], [109], [present], [retained],
[[2, 0]], [116], [present], [retained],
[[2, 1]], [12], [absent], [fixed match],)

== What was actually checked
One unfiltered native test passes with all64 coordinate transports, three actual coefficient-conjugate maps, Frobenius, all4096 addition/pairing rows and135 independent original masks. The pairing is the original alternating2-torsion form, not a Miller implementation. Both entire old model panels agree exactly. Original Adapter/NormNew checks the full starting J1 tag. The target mask is fixed before model construction and before reading smoothness or square-D.

All six whole records compare exactly without masks. Removing the actual complete MATCHED_MODELS record rejects101/no accepted output. Source guards and actual compile/runtime executable equality pass. These are local unsigned observations; a passing census does not mean endpoint acceptance.

== Independent arithmetic and the mathematical boundary
A separate Rust loop retains all223 base-field squares and excludes12; another gives12^111=222 modulo223. A quadratic root cannot lie in a degree3 extension by the tower law. Original quotient identities have coefficients D*A_i and D²*B_i and require sqrt(D) for the specified source. HLP Proposition15 gives its polarized identification after adjoining sqrt(T), with D=16*T. This records failure of the supplied-source construction, not universal nonexistence of any F223 Jacobian for the ppav.

== Frozen failure and the next experiment
No retwist or alternate square case is selected. A later fixed elliptic edge may be studied under a new prospective protocol, transporting the same full kernel and preserving this intermediate failure. Complete Jacobian maps, faithful global formalization, strict replay/CI and calibrated computational comparison remain open.

#text(size:7.6pt)[Exact quartic coefficients in the original15-monomial order: 1,164,176,127,109,75,91,157,56,179,142,133,28,43,94. P0=(1:0:181). Fixed transported mask1155175778390933505.]

#text(size:7.6pt)[Sources: source87b61e80; original checkpoint492150; native27fb3a; NONDUAL13_MODEL_NEGATIVE_DERIVATION_01.md; original odd-product-models quotient formulas; Howe–Leprévost–Poonen math/9809210 Proposition15 and following remark, printed24–26. All whole raw/actual binaries retained; large217960B/150556B XZ await genuine18. Primary PDF/text already genuine17. No signed execution, novelty or calibrated advantage.]
