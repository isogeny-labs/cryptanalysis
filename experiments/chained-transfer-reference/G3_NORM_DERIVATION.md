# Canonical divisor-class norm on the three fixed Ciani descents

This derives the actual map evaluated by `g3-norm-checker`, for the frozen
q=5,7,11 historical instances, K=Fq³ and the producer's exact cubic bases.
It is a written geometric argument with partial Lean formalization. The
finite native checks are c19a2e; additional controls, independent replay and
signed main standing are separate. No computational advantage is established.
[pcc:unverified]

The source is the smooth historical plane quartic C/Fq, with rational base
point P0 and canonical divisor class K_C. The original Picard representation
uses Dinf~K_C-P0 of degree3. A typical class is [D-Dinf], where D is the
noncollinear degree-three divisor defined by its three canonical conics.
An exceptional class is Exc(P)=[P0-P]. The quotient pi0:C_K→E0/K is the
actual completed degree-two Ciani cover. The proposed norm is
`n=pi0_*:Jac(C)(Fq)→E0(K)`. It is a map of Picard classes, rather than an
inverse point map C→E→C. [pcc:unverified]

## Actual divisor algebra, including nilpotents

Let I2 be the span of the three typical conics, R the homogeneous plane
coordinate ring and I4=I2·R2. The original linear-kernel routine constructs
coordinates on Q2=R2/I2 and Q4=R4/I4. Both have dimension3 for the typical
degree-three scheme. Choose three degree-two monomials forming a basis of
Q2. Choose an Fq-linear form L avoiding D; multiplication by L² then gives
an invertible map Q2→Q4. This supplies the algebra
`A=H⁰(D,O_D)= { F2/L² : F2∈Q2 }`. For basis elements its product is computed
by multiplying the original homogeneous forms in R4, projecting to Q4 and
solving the multiplication-by-L² system with the original kernel routine.
The unit is L²/L², and plane coordinates are W_i/L=(W_i L)/L².
[pcc:unverified]

For a length-three scheme on the smooth curve, this construction retains its
scheme structure. It never replaces its ideal by the radical. A form L
avoiding all geometric support exists over these fields: at most three
geometric support points exclude rational projective lines; a rational
point excludes q+1 lines, whereas a nonrational closed point excludes at
most that many. The union has at most3(q+1) lines, strictly less than
q²+q+1 for q≥3. The native admission checks Q2/Q4 dimensions, invertibility,
the unit, commutativity and associativity, every conic and the actual
quartic in A. These conditions are checked in the possibly nonreduced
algebra. The smooth-curve/Hilbert-function identification is a written
bridge, not a Lean implementation of algebraic geometry. [pcc:unverified]

Every length-three algebra of a divisor on a smooth curve over these finite
fields is monogenic. Its possibilities are an irreducible cubic field, a
quadratic field times Fq, three distinct rational factors, one rational
length-three local algebra, or a rational length-two algebra times Fq.
Choose distinct residues at different rational factors and a parameter
with nonzero first derivative at a repeated factor. For q≥5 all these
choices exist. The runtime searches T in the three-dimensional algebra and
requires1,T,T² to be a basis. It solves
`T³=c0+c1 T+c2 T²`, yielding
`h(t)=t³-c2 t²-c1 t-c0` and degree≤2 expressions for every W_i/L.
[pcc:unverified]

Each irreducible factor of h has degree1,2 or3. Consequently Fq⁶ contains
all its geometric roots. Original polynomial roots return distinct roots;
the adapter repeatedly divides h by each linear factor with the original
exact division routine. Its multiplicity is the local length of D at
that geometric point. Evaluating the coordinate polynomials at a root
recovers the point in the actual historical plane model. The resulting
weighted cycle has degree exactly3. Multiplicity is not multiplied again
by the ramification index of pi0: pushforward of geometric divisor cycles
keeps each coefficient; ramification indices belong to pullback.
[pcc:unverified]

Changing L or the monogenic coordinate T changes a presentation of A,
without changing D or its weighted cycle. Therefore every admissible
choice gives the same pointwise pushforward. This is a general written
chart-independence argument. Native unit01 sampled a second affine and
monogenic choice for eight typical classes per field; that finite control
is not an exhaustive enumeration of all pairs of chart choices. Its scope
must remain explicit in reports and CI. [pcc:unverified]

## Completed cover and the geometric origin

Apply the producer's actual historical Moore transport to obtain Ciani
coordinates (X,Y,Z). With the frozen quadratics u0,u1,u2, the finite cover
has parameter t=s1/s0 and ordinate y=u0(t)Y/Z. At u0=0 use Z=0 and y=0.
At s0=0 the ratio Y/Z is+1 or-1 and gives the two quartic infinities.
All coefficients are embedded explicitly in Fq⁶ using a root of the exact
frozen cubic modulus. Coefficient arrays in different bases are never
reinterpreted as equal elements. [pcc:unverified]

For `u0 u2=(t²+B t+s)²+alpha t+beta`, the completed short-model formulas are
`x=2(y+t²+B t+s)`, `Yshort=2xt+B x+alpha` and
`Xshort=x+(B²-4s)/3`. Positive infinity maps to O and negative infinity to
`((B²-4s)/3,-alpha)`. The two x=0 branches are distinct: the finite branch
has t=-beta/alpha,Yshort=alpha; the other is negative infinity. All fixed
instances have alpha≠0. The original producer's algebraic Lean identities
and native completion checks are retained separately. [pcc:unverified]

Take any actual plane line H through P0. Its section on the plane quartic
is a canonical divisor, so `D_H=(H·C)-P0 ~ K_C-P0=Dinf` has degree3.
Restrict the actual quartic to P0+tR on that line, remove exactly one
factor at P0, preserve every remaining root multiplicity and account for
the projective parameter infinity. Define `b_H=sum pi0(D_H)` in E0.
Every line gives the same b_H, since the difference of its section and
another plane section is principal. The runtime computes all q+1 such
lines and requires their offsets to agree. It does not fit a shift from
scalar samples. A degree-four tetragonal infinity divisor is not silently
substituted for a plane canonical section. [pcc:unverified]

Thus a typical class has the computable norm
`n([D-Dinf])=sum_P multiplicity_D(P) pi0(P)-b_H`.
For an exceptional class, use
`[(K_C-P)-(K_C-P0)]=[P0-P]`, giving
`n(Exc(P))=pi0(P0)-pi0(P)`. In particular Exc(P0) maps to O. The sum is
K-rational: it is the pushforward under a K-defined cover of a divisor
defined over Fq⊂K. Runtime additionally checks q³-Frobenius fixedness,
solves the explicit cubic-subfield embedding and checks the original
elliptic model before encoding the answer. [pcc:unverified]

## Well-definedness, both compositions and DLP transport

For a finite morphism of smooth projective curves, the divisor identity
`pi_* div(f)=div(N_function_fields(f))` sends principal divisors to
principal divisors. Hence cycle pushforward descends to an additive map
on Pic⁰. The constructed quotient algebra gives the actual cycle and the
plane section gives the actual Dinf correction. Together they identify
the runtime norm with pi0_* on every admitted class. The identities do
not depend on divisor splitting or on its multiplicities being one.
The actual function-field norm/divisor identity remains a written
geometric bridge in the partial formalization. [pcc:unverified]

Over an algebraic closure let p_i=pi_i^* and n_i=pi_i_* for the three
degree-two Ciani quotients. The standard divisor pullback/pushforward
identity gives n_i p_i=[2]. For i≠j, the distinct V4 characters give an
involution acting by opposite signs on p_j and the i-th quotient, so
n_i p_j=-(n_i p_j). The group of homomorphisms of abelian varieties is
torsion free; hence this off-diagonal homomorphism is zero. For the
product maps P=sum p_i and N=(n_i), this proves NP=[2]. The kernel of P
is finite and both abelian varieties have dimension3. Consequently P is
geometrically surjective. On a point P(a),
`PN(P(a))=P([2]a)=[2]P(a)`; surjectivity gives PN=[2] everywhere. The
surjectivity used here is geometric and does not assert surjectivity on
Fq-rational points. [pcc:unverified]

Galois descent identifies the rational points of the conjugate product
with E0(Fq³). The descended P is the producer's sum of the three completed
Frobenius-conjugate pullbacks, denoted phi. The first component of N is
exactly this consumer's norm n. Both identities therefore descend to
`n phi=[2]` on E0(Fq³) and `phi n=[2]` on Jac(C)(Fq). The native checks
test both on the independently enumerated full rational groups, rather
than assuming coprime conjugate group orders or checking only a scalar
table. [pcc:unverified]

On an order-ell subgroup with ell odd, choose u,v with2u+ell v=1. Then
`[u]n phi(x)=x` and `[u]phi n(j)=j`. Here the public u values are19,45,166
for ell37,89,331. This proves injection on those odd subgroups and
preserves the unknown scalar:phi([k]G)=[k]phi(G). It does not give a
global inverse on the even parts; native norm kernels have size2 in
these fixtures. The same subgroup-preserving argument composes with
other homomorphisms whose known multiplication factors are coprime to
ell. [pcc:unverified]

## Independent domain completeness and cost boundary

Count C over Fq,Fq²,Fq³ independently using the original extension-field
and polynomial routines, including both projective boundary charts.
Writing N_i=#C(Fq^i), the number of effective rational degree-three
divisors is `(N1³+3N1 N2+2N3)/6`. Riemann–Roch gives one such divisor per
typical rational class and q+1 for every exceptional class K_C-P, of which
there are N1. Hence `#Jac=(N1³+3N1 N2+2N3)/6-q N1`. An independent Newton
calculation of the reciprocal Weil polynomial at1 agrees. BFS with the
original canonical group law reaches exactly that count and is closed
under every rational-point-class generating edge. Thus all rational
classes, including the exceptional and nonreduced classes, are covered.
These counting/Riemann–Roch/Weil identifications are written geometry,
with concrete complete native counts. [pcc:unverified]

The correctness prototype uses support roots over Fq⁶ and computes all
plane-line offsets during setup. Every such cost must be charged in a
future computational comparison. A destination DLP solver, eligibility,
full setup/transfer/solve/recovery/verification costs and matched rho and
index-calculus references remain required. The q=5 source has the known
special j=1728 behavior; it remains in this fixed correctness panel and
does not establish a generic large-prime-field cost comparison.
[pcc:unverified]

Sources: original producer `G3_DESCENT_DERIVATION.md`, `G3_PROOF_MAP.md`
and frozen historical case catalog; original Picard W1 README and
`plane_quartic_pic.rs`; original Diem `Core`, cover and polynomial engines;
consumer source catalog and pre-code `G3_NORM_REPLAY_PROTOCOL.md`.
KB access failures/source fallback and atlas/vault limits remain recorded
in the proposal. No novelty claim follows from missing search access.
[pcc:unverified]
