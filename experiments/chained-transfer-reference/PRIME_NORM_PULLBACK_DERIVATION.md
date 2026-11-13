# Independent T20 finite-algebra norm and completed pullback

Prospective written derivation before new consumer implementation/runs.
Exact functions/targets/source are frozen in PRIME_NORM_REPLAY_PROTOCOL.md.
This is not new native acceptance. Scientific standing is unsigned.
[pcc:unverified]

For source monic ordinate y,replace the parent's raw m by50*m modulo101.
This gives m0=[79,27,23,100],m1=[7,42,24,48]. The exact identity is
f_monic*m²=n³+a*n*q⁴+b*q⁶,with X=n/q²,Y_E=y*m/q³.
The source square coordinate change and literal identities must be checked
independently;parent values are data until those checks run.
[pcc:unverified]

For a valid support u=z²+a*z+b,reduce cover coordinates to X=A+Bz,Y=C+Dz.
When B≠0,the image finite algebra has monic support
T²+(aB−2A)T+(A²−aAB+bB²) and ordinate C−DA/B+(D/B)T.
The substitution T=A+Bz is an algebra isomorphism,including repeated
support. Existing genus1 Cantor reduction computes its degree-zero
elliptic class. B=0 gives coincident images if D=0 and opposite images
otherwise,including repeated jets. Pole removal uses the full denominator
gcd with multiplicity and the ORIGINAL infinity correction degree.
[pcc:unverified]

For P=(X,Y) on the elliptic target,the fibre has U=n−Xq² and
V=Yq³/m modulo U. The universal factorization is

    n³+a*n*q⁴+b*q⁶−(X³+a*X+b)q⁶
      =(n−Xq²)(n²+X*n*q²+(X²+a)q⁴).

Together with the cover/target equations and m invertible modulo U,
this proves V²=f_monic in the whole fibre algebra. It retains all
multiplicities and chooses no support root. Rational nonzero target
points have Y≠0 because their orders are odd;the exact equation and
coprime n/q then exclude nonunit m on that finite fibre.
[pcc:unverified]

Let K=infinity+ +infinity−. Elliptic O pulls back to the four simple
pole points,whose divisor is div(q)+2K. Thus pi*(P−O) is represented by
the completed degree4 P fibre minus2K. If its finite part has degree d,
delta=4−d lies at infinity. The two infinity images are opposite
non-two-torsion points,so a degree drop's delta points have one sign.
In the old reducer's representation the correct plus is n_plus−1:

    D_fin+n_plus*infinity+ +n_minus*infinity−−2K
      =D_fin+(plus−1)*infinity+ +(1−d−plus)*infinity−.

This includes plus=−1 for a generic finite degree4 fibre. It is the
existing src/quartic_pullback.rs convention,not a new balanced reduction
algorithm. Apply unchanged Balanced::reduce_support after validating
the complete semireduced fibre. [pcc:unverified]

The displayed coefficients predict n0−10q0²=z²+52z+56,so the two
E2 points with X=10 have two finite points and two equal signed
infinities. For F0,n1−71q1²=96z³+24z²=z²(96z+24),so X=71 has a
repeated finite point z=0 plus another finite point and one infinity.
V modulo the ORIGINAL U carries the repeated jet. These explicit
identities and the signed choices are prospective formal/native controls.
[pcc:unverified]

Galbraith8.3.8/8.3.10 gives the induced pushforward/pullback maps on
Picard groups. The true covers have degree4,so each same-component
norm-pullback is[4]. On the F101 rational groups,cross-component maps
vanish since109 and113 are coprime. Test both complete compositions on
all12317 classes and every rational target pair;finite tests are not
substituted for global Picard/polarization statements. [pcc:unverified]

Public recovery can either multiply Mdag(M(D)) by9238 on the Jacobian,
or apply inverse4 on the two elliptic groups BEFORE pullback,using82
and85. Both must agree with actual D on all12317 inputs. No inverse
lookup,discrete-log label or enumeration index is a map input. This is
a public finite rational-group inverse,not a global inverse isogeny.
[pcc:unverified]

Next after acceptance:combine this independent F101 norm/pullback with
the existing C0 two-cover norm/pullback and alpha49 bridge to compare
a complete F101 C0↔T20 coordinate adapter with the accepted degree196
chain. Preserve the already established equality with the normalized
direct norm/isogeny bridge;do not turn a new representation into an
unmeasured solving advantage. That extension is outside this frozen run.
[pcc:unverified]
