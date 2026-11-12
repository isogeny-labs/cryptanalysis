#set page(paper:"a4",margin:16mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= A direct F101 quartic quotient evaluator
2026-11-12 · fixed T0→E109 · scientific standing unsigned

The existing quotient H=N0 R0 dual now has an explicit direct evaluator
overF101. It agrees with the retained route on all12,317 balanced T0
classes,all negations and predetermined paired sums,including the actual
closed poles,repeated support and every infinity case,PCC585f35.
The old route remains the reference. This is the first elliptic component;
the rest of the Jacobian chain retains its existing evaluation paths.
[pcc:unverified]

#image("cover.svg",width:100%)

== Exact coefficients and complete finite identity
Source F=[31,75,74,54,71,55,1];target Y²=X³+X+46,overF101.
All lists are low to high. The cover is(X,Y)=(N/Q²,y M/Q³),where

#table(columns:2,stroke:0.4pt,
 [N],[14,0,88,97,14],
 [Q],[63,0,1],
 [M],[41,40,69,73],
 [infinity+ image q],[(14,73)],
)

The exact polynomial identity is F M²=N³+N Q⁴+46Q⁶. Existing
field/polynomial engines check every coefficient,gcd,smoothness and
nonzero derivative. The reduced rational x-map has degree4;the complete
curve map therefore has degree4. The infinities map to±q. Each of the
four simple geometric pole branches maps to the elliptic origin.
Native constructionad6883 and separate flat-field replay5ab2bd retain
the source and all118 finite rational witness points. [pcc:unverified]

== Every balanced class and exceptional route
The input finite degree is m and plus-infinity count n. The finite trace
needs the exact correction(2n+m-2)q. Degree0 plus0/1/2 yields-2q/O/+2q.
Finite quadratic support uses the existing polynomial inverse modulo u,
then the actual elliptic secant or its coincident-image limit. NonunitQ
uses gcd(u,Q²),including multiplicity,so poles are never inverted.
[pcc:unverified]

#table(columns:4,stroke:0.4pt,
 [Degree0],[Linear support],[Closed-pole support],[Generic quadratic],
 [3],[236],[2],[11,842],
 [Same image: double],[Opposite images],[Repeated supports],[Total classes],
 [126],[108],[118 (overlapping count)],[12,317],
)

#pagebreak()
= A global certificate rather than an interpolation assumption

The old quotient has HH†=[4],from the accepted Richelot dual norm and
elliptic norm/pullback identities. Its Abel–Jacobi curve map has degree4.
Centre it by q=H(infinity+-infinity-)/2,using the actual odd elliptic
order109 and scalar55. The centred map is odd under the hyperelliptic
involution. Irreducibility of the source sextic and the degree bound force
its finite denominator to be a square;finite infinity values give the
displayed degree bounds. [pcc:unverified]

For two degree4 curve maps f,g to E,Milne AVv2 ChapterI Corollary5.3,
applied to f,g,-g and the symmetric line bundle O_E(O),gives

    deg(f+g)+deg(f-g)=2deg f+2deg g=16.

A nonconstant curve map has at most its degree many distinct points in
one fibre. Hence17 distinct agreements force f-g to be constant,and one
agreement fixes that constant to zero. The frozen certificate has118
distinct agreements. This uses a proved degree bound,not density of
rational samples. The old H expected-value provenance is retained as an
explicit dependency. QUARTIC_COVER_PROOF.md/PCC6afa9c contains the full
written argument and complete balanced finite-algebra formulas.
[pcc:unverified]

== Independent replay and a discriminating negative control
A separate checker imports existing flatFpR/polynomial operations and
no producer Balanced,Richelot or interpolation code. It checks the exact
identity,source irreducibility,degree/separability,all118 complete finite
rational points,both infinity limits and all four geometric poles.
Mutated numerator and codomain controls reject. Negating M still gives
the exact curve equation but disagrees on118 witness points. This shows
why the equation alone cannot identify the intended quotient.
Checker04 passes2tests/strictClippy5ab2bd;the complete standalone10
passes15tests with prior class/kernel controls,c3a4b7. [pcc:unverified]

== Existing code, integration and continuation
All field,polynomial,elliptic,Richelot and class arithmetic is reused.
The private existing Sutherland Lagrange body is extracted byte-exact
with visibility-only custody. Compiler01 used the wrong SevenEdge field;
its source/error7137fa remains. No degree bound or test was weakened.
First-component actual consumer integration05 passes2targeted tests/
strictClippy86b79a. Complete changed guard07 passes25native/85reference
unit+five integrations,one old ignored benchmark,all source guards/fmt/
strictClippy301fbe. Complete108004-byte raw standard-XZ12816bytes has
raw/archive hashes and exact roundtrip;post-run source05 hashes match.
Parent1501 exact5ceb focused43157257094 succeeds25/83+five,fullf74e9e.
Own final-headCI and bottom-up integration remain separate.
[pcc:unverified]

Formalization remains partial:the existing134 written Lean declarations
are unchanged;actual Picard,polarization,curve degree and line-bundle
geometry are written dependencies here. The second T0→E113 norm
has separate full12317 acceptance2fcf0b and joint H0 forward comparison
19b3bd;all four T0/T1 pullbacks pass5143f5. Broader isolated evaluation
work is separate from this first-component consumer change. Matched cold costs await S3/livebudget admission;
this report supplies no measured cost ratio. [pcc:unverified]

Primary sources read:Milne AVv2 Corollary5.3(the arbitrary-map cube
identity);Galbraith corrected Chapter8 Lemma8.1.9,Theorem8.2.12/
Corollary8.2.13 and Theorem8.3.8. Exact source links/hash and old global
dependencies are in6afa9c. KB/ecdb unavailable;atlas vault locked.
[pcc:unverified]
