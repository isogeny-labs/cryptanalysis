#set page(paper:"a4",margin:17mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= Explicit elliptic coordinates for the rational groups
2026-11-11 · Chained ECDLP Transfers · CT17

*Unsigned/unverified standing.* All285 F17 and12,317 shiftedF101 classes
pass both quotient norms,reciprocal completion and odd-component
reconstruction. Accepted target source points have coordinates([4]P,0).
PCC036d81/96b1e2 bind correctness evidence,no DLP solver or measured gain.
[pcc:unverified]

#image("split-quotients.svg",width:100%)

== Complete reciprocal chart
For C:y²=x⁶+a2*x⁴+a4*x²+b,b=s² nonzero,set T=s/x,Y=b*y/x³.
The second monic cover is Y²=T⁶+a4*T⁴+a2*b*T²+b²,with inverse
x=s/T,y=s*Y/T³. The two elliptic quotient cubics are
[b,a4,a2,1] and[b²,a2*b,a4,1]. No twist is silently substituted.
[pcc:unverified]

The actual balanced divisor map transforms whole finite support. Degree lost
at x=0 maps to the correct target infinity,including multiplicity2. Old
infinities map to(T=0,Y=±b); their hyperelliptic fiber carries K to the new K.
The completed class retains all finite/infinity coefficients before reducing.
Every rational class,both reciprocal inverses and paired additions pass;
zero-support multiplicities0/1/2 are all covered. [pcc:unverified]

== Full rational-group coordinates
The involutions sigma:(x,y)→(−x,y) and iota*sigma define the two quotients.
Hyperelliptic iota induces−1 on Jac(C),so pull/norm operators are1+sigma
and1−sigma. Thus their sum is[2],each norm/pull is[2],and cross-norms are0.
This geometric bridge remains a written primary input. [pcc:unverified]

All285/12,317 classes satisfy these identities and reconstruction by halving
each elliptic component. Independently counted component orders are19/15
and109/113. Norm pairs are distinct and exhaust the complete product.
These are rational-group isomorphisms,not an assertion that the abelian
varieties are isomorphic to products. Incorrect odd annihilators and
unsupported scales/constants are rejected. [pcc:unverified]

#pagebreak()
= Target coordinates and direct source controls

Let N=(N1,N2),P=P1+P2. With accepted Richelot R and dual Rhat,
M=N*Rhat and S=R*P satisfy MS=SM=[4]. Their odd rational groups therefore
have an explicit inverse by quartering elliptic components. This follows
from the complete individual pull/norm/dual identities. [pcc:unverified]

For every original r19/r109 source scalar,coordinates are([4]P,0). Both
components,zero second factor,source inverse5/82 and reversed-class
reconstruction pass. No map reads a DLP scalar. The other elliptic factor
supplies no extra DLP equation for this subgroup. Generic algorithms still
face order r;a larger ambient Jacobian alone gives no generic-query gain.
A non-generic solver would need separate complete cost evidence.
[pcc:unverified]

== Compiled algebra and exact receipts
Seven SplitQuotients.lean lemmas pass gate7,PCCfffa35: cleared reciprocal
curve/inverse,complementary norm sum,odd-annihilator halving,conditional
split reconstruction and target first/other components. Two broad tactic
failures remain preserved; explicit local power identities give the pass.
No new axioms,no finite-field/Picard geometry or group orders formalized.
Total62 written project lemmas. [pcc:unverified]

Primary inputs remain Galbraith corrected ch.8§8.3/ch.10 and the existing
bielliptic cover/pull-push family. No prior-art novelty claimed; KB/ecdb
unavailable. Group arithmetic and harnesses remain producer-authored Cantor
checks,without signed independent whole-map standing. [pcc:unverified]

New targeted full decomposition,source-component controls,formatting and
strict Clippy pass. Current full49-test CI pending. Prior63cf80560 exact-head
focused43024621372 passes native25/reference47,one old benchmark ignored,
formatting/Clippy/guards(PCCbfa6ff); its exact scope is retained.
[pcc:unverified]

Receipts: split-quotients-proposal-01,split-quotients-01,
split-target-components-01,split-quotients-clippy-01. Source:
src/balanced.rs,src/nonsplit_map.rs. Run consumer check.sh with Rust1.99.1
and unchanged crypto75a737b8 guards,or select the two new correctness tests.
Run upstream proof-gate.sh on SplitQuotients.lean. Full account:
SPLIT_QUOTIENTS.md. [pcc:unverified]

== Next route and cost boundary
The rational Richelot next neighbors are already closed by forced dual
backtracks. Next assess rational odd-prime maximal-isotropic kernels without
pre-accepting a map. Retain original-source/direct elliptic controls for
any candidate. Production/catalog/large fields stay open.

No benchmark,solver comparison,paid allocation or computational advantage
was demonstrated. All future comparisons must include construction,transport,
solver,recovery and verification. S3/live-budget,KB/vault and crypto frozen
ledger/archive blockers remain; no cross-prime descent or cost edge promoted.
[pcc:unverified]
