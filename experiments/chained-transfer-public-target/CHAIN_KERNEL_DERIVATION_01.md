# Geometric chain kernels and same-product collapse

2026-11-13. Unsigned written argument using native29830a and previously
published7cf45856/7c9bf4/5f7e4c. No actual J[4] divisor basis is constructed.
The full finite-group/Picard/polarization bridges are not formalized in Lean.
[pcc:unverified]

Let A=Res(K/F223)E. Let Phi0:A→J0 and N0:J0→A be the original dual
polarized degree8 maps, with both compositions[2]. Their kernels lie in
geometric2-torsion and have8 points, since characteristic223 is prime to8.
Write G0=ker(Phi0). For any rational maximal-isotropic G⊂A[2], let
PhiG:A→BG=A/G be the polarized quotient, and NG its dual. These again
have degree8 and both compositions[2]. BG need not be a Jacobian over F223;
product kernels and the two nonsquare HLP cases remain distinguished.
[pcc:unverified]

Set F=PhiG*N0:J0→BG and R=Phi0*NG. Then RF=[4],FR=[4] and deg(F)=64.
Thus ker(F) is an etale group of64 geometric points killed by4. Moreover
F*lambda_BG=4lambda_J0 by composing the two polarization identities.
Its kernel is therefore isotropic for e4 by the standard polarization
descent criterion. These conclusions use the actual global maps, not
sampled scalar fits. [pcc:unverified]

Restrict N0 to J0[2]. Its kernel is ker(N0), with8 geometric points.
The image lies in G0 because Phi0*N0=[2]. Since #J0[2]=2^6=64, that
image has8 points and equals G0. The inverse image of G0∩G under this
restriction is precisely ker(F)∩J0[2]=ker(F)[2]. Hence for
d=dim_F2(G0∩G),

    #ker(F)[2] = 8*2^d.

This is a geometric exact-sequence/cardinality argument. It is not a
count of rational cofactor points, nor explicit coordinates for J0[4].
[pcc:unverified]

By the classification of finite abelian groups, every group killed by4
is (Z/4)^a × (Z/2)^b. Its order64 gives2a+b=6 and its2-torsion cardinality
gives a+b=3+d. Thus a=3−d,b=2d. In particular the kernel is free rank3
over Z/4 exactly when d=0; together with polarization multiplier4 this
gives a free maximal-isotropic (4,4,4) kernel. Degree64 or both[4]
compositions alone do not establish this free-kernel condition.
[pcc:unverified]

Native29830a independently obtains all135 original Lagrangians, matches
the model panel's entire set, and records every intersection with G0.
The dimension0/1/2/3 histogram is64/56/14/1. The whole9x9 rational table
contains actual A[2] coordinate triples and every vector, with closure,
isotropy, Frobenius, symmetry and diagonal checks. The literal original
candidate(1,0) identifies G0 as mask9232380353346274305. [pcc:unverified]

| Eligible candidate | d | Geometric ker(F) | Scope |
| --- | --- | --- | --- |
| (0,0) | 0 | (Z/4)^3 | Free (4,4,4) case |
| (0,1) | 1 | (Z/4)^2 × (Z/2)^2 | Degree64, nonfree |
| (1,0) | 3 | (Z/2)^6 | Literal original[2] control |
| (2,0) | 0 | (Z/4)^3 | Free (4,4,4) case |

All entries use the written geometric bridges above and unsigned native
intersection premises. In contrast, the actual rational cofactor kernel
of F has only2 points in all four cases. That rational count alone cannot
distinguish the geometric kernel types. All product and nonsquare cases
remain in the complete native table. [pcc:unverified]

For eligible Jacobians Ji over the SAME A, put Fji=Phij*Ni. For three
nodes i,b,c,

    Fcb*Fbi = Phic*Nb*Phib*Ni = Phic*[2]_A*Ni
            = [2]_Jc*Phic*Ni = [2]_Jc*Fci.

The commutation follows either from homomorphisms or directly from the
two dual[2] factorizations of Phic,Nc. Repeating this reduction shows a
path ofL≥1 such edges through the same fixed A is [2^(L−1)] times its direct
endpoint transfer. No path-dependent scalar is fitted. [pcc:unverified]

The native test checks all four eligible interior and final nodes and
the first eight canonical rational-point classes of J0: all128 actual
composed maps equal the doubled direct map, with complete class outputs.
Thus increasing path length within this same product supplies no new
homomorphism after known odd-subgroup scalar normalization. This is not
a lower bound on implementation cost; an intermediate representation
might still compute the same map more cheaply, requiring measurement.
It also does not invalidate the three distinct one-step targets.
[pcc:unverified]

Next, preserve these positive free-kernel cases and the collapse result,
then test a genuinely different product or degree. For example, an actual
odd-degree source isogeny E→Eprime/K and its dual would induce A→Aprime;
with completed target gluings the resulting Jacobian compositions would
be[4*l] for degree-l source isogeny. This is only a proposed next route:
the degree, maps, fields, source points and duals require a separate frozen
protocol and native validation. Full cost/benchmark admission and strongest
algorithm comparisons remain open. [pcc:unverified]
