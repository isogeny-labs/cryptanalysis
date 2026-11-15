#set page(paper:"a4",margin:16mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= Direct elliptic norms for the Jacobian chain
2026-11-11 · CT22 arithmetic engineering · unsigned standing

The actual Phi/Psi coordinate evaluators now use direct base-field
elliptic norms. Both outputs match the unchanged generic norms on every
12317-class C0 and C1 domain. The complete changed guard passes native25,
reference66 and three integrations, with one old benchmark ignored.
PCC b6af61/3f2084; no measured computational advantage is claimed.
[pcc:unverified]

#image("direct-norms.svg",width:100%)

== Exact domain and rational formulas
Runtime accepts only the two actual F101 models
C:y²=x⁶+d·x⁴+c·x²+b, with (b,c,d)=(56,13,6) or(68,42,26).
Both are checked canonical balanced classes using the existing validator.
The short elliptic covers are (x²+d/3,y) and
(b/x²+c/3,b·y/x³). The existing cubic-to-short, field and elliptic
group engines are reused; no new Cantor or extension engine is written.
[pcc:unverified]

For u=x²+A·x+B and v=V0+V1·x, the symmetric pair sum at
(X,Y)=(lambda·x²+s,V0+V1·x), when A is nonzero, is

    m=−V1/(lambda·A)
    Xsum=m²−lambda·(A²−2B)−2s
    Ysum=m·(s−lambda·B−Xsum)−V0.

Valid repeated support supplies the ordinate jet, so this also gives
the elliptic tangent sum away from the explicit zero case. No individual
support root is chosen. [pcc:unverified]

For the second quotient with B nonzero, use A'=A/B, B'=1/B and
the reduced ordinate of b·(V0·t³+V1·t²) at t=1/x. This gives the
same pair formula with lambda=b and s=c/3. Exact remainder identities,
curve maps and all denominator cases are proved in DIRECT_NORMS.md.
[pcc:unverified]

#pagebreak()
= Exceptions, proof scope and exact checks

== Complete balanced support
When A=0, source validity gives V0·V1=0. Constant ordinate gives an
actual elliptic double; odd ordinate gives opposite points and the origin.
This includes repeated support at x=0. For the second norm, a zero
support root maps to the origin; the remaining root is evaluated when
present. Degree1 and degree0 are handled directly. No invalid denominator
is inverted. [pcc:unverified]

The first cover sends both source infinities to the origin. The second
sends infinity± to ±Q, Q=(c/3,b). Its balanced correction is
(2n+m−2)Q for finite degree m and plus count n. The identity and both
infinity differences are included. Each actual model has 118 repeated
supports and 238 nonzero infinity corrections in its complete corpus.
[pcc:unverified]

== Whole-map correctness and independent arithmetic
Both direct norms match both generic outputs on all C0 and C1 classes,
with point validity, actual109/113 orders, paired additions, identity and
wrong-model rejection. The direct u64 field/elliptic route is compared
with the existing BigUint divisor-norm route. These remain producer-run
certificates, not a signed independent verdict. [pcc:unverified]

Original generic coordinate evaluators remain available. Both complete
Phi/PhiHat domains agree with them, and all complete Psi/R1/R0 corpora,
109-source scalar relations, norm14/28 recoveries and direct target
coordinates pass in the changed guard. The naive chain uses generic
norms explicitly. No production table or unknown DLP label is introduced.
Strict Clippy, formatting and immutable source guards pass.
[pcc:unverified]

== Faithful partial formalization
Seven DirectNorms.lean lemmas pass gate and all local declaration bindings:
symmetric squares, slope inverse, ordinate support reduction, reciprocal
support/ordinate, even-support remainder and zero-factor consequence.
RootPCC8eaf58; source census97, zero trusted native. The existing reciprocal
and infinity lemmas are reused in the proof map. [pcc:unverified]

Actual finite fields, valid Mumford jets, elliptic addition, projective
completion and Picard norm functoriality remain written bridges. The
generic written field argument does not expand the two-model runtime
coverage. The full theorem is not replaced by a weaker helper.
[pcc:unverified]

== Evidence and continuing work
Read DIRECT_NORMS.md/status and immutable files with the evidence/direct-norms- prefix.
The source is src/direct_norms.rs with integration in seven_glue.rs and
seven_chain.rs. Run check.sh on Rust1.99.1; root Lean4.35.0 checks
DirectNorms.lean. API/iteration compile and Clippy failures are retained.
The core field, gluing and Cantor source guards remain unchanged.
[pcc:unverified]

Next: whole-fibre Richelot evaluation without quadratic support splitting,
then a further nondual odd hop with genuine new kernel/target/global
proof and direct elliptic controls. Existing chart/forced-backtrack
negatives remain. S3/livebudget block timing, solver and paid work;
frozen-ledger forks, root archival gates and locked KB/atlas integration
persist. No speedup, rho/BSGS/index-calculus gain, novelty or cross-prime
claim follows from this arithmetic correctness result. [pcc:unverified]
