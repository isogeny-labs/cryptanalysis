# Complete balanced-class transport to the existing odd-model engine

Scientific standing unsigned. This extends the covered representation scope
of the frozen kernel-only INDEPENDENT_GROUP_REPLAY_V2.md/40a568. That
record and its49-class claims remain unchanged. The new formulas cover
degree0/1/2 finite support and every balanced infinity count on the accepted
T0/T1 rational-class corpora. Runtime acceptance and CI live in the current
checkpoint;no isogeny-map or performance claim is inferred. [pcc:unverified]

## Exact curves and existing engine

Over F101 use T0=[31,75,74,54,71,55,1] and
T1=[95,26,19,27,94,91,1]. Both smooth monic sextics have the accepted
12317 rational Jacobian classes. The separate checker uses the existing
flat field K=F101[gamma]/(gamma⁶+12gamma⁵+56gamma⁴+18gamma³+2gamma²+
46gamma+33),existing polynomial operations and the pre-existing generic
odd-model Cantor engine extracted from jv_cover.rs. All input coefficients
are already in F101,so their flat-field embedding is unambiguous.
[pcc:unverified]

The full original engine SHA256 is
1ecd62c4282402e3411635e0487d0bb36a5d57e15a547f352a7cab1fda7309cc,
last changed cfa4ef08bccfb509c89f8d0bb0c6c5baf662ff11. Frozen extraction
ranges40–52/464–690 and the earlier tuple-equivalent alias/signature-only
repair are retained. All arithmetic bodies remain unchanged. Both the
old49-class and new complete-class replays import the single same engine
module;strictClippy and exact source-extraction guards remain required.
No producer Balanced,tower,Richelot or elliptic-map implementation is
imported by the new checker. [pcc:unverified]

## Same global curve chart,including infinity

Choose a simple branch a with F(a)=0 and L=F'(a) nonzero. Define

    H(z)=z⁶F(a+1/z),  w=L/(x-a),  V=y*w³/L,
    G(w)=L⁴ H(w/L).

H has degree5 and leading coefficient L,so G is a monic quintic. Its
constant is L⁴. The inverse is x=a+L/w,y=V*L/w³. This is the same
function-field isomorphism and smooth projective completion justified in
the frozen kernel chart proof. It identifies the geometric Picard groups
over K. No square-root-of-L or F101-rational Weierstrass point is assumed.
[pcc:unverified]

The unique quintic infinity W is the old branch point(a,0). The old source
infinities,oriented by y/x³ tending to±1,map to B±=(w0,V=±L²).
They are distinct because L nonzero and characteristic101 is not2.
The coordinate w has simple zeros at B+ and B- and a double pole at W:

    div(w)=B+ + B- -2W.

Consequently Q+=[B+-W] and Q-=[B--W] satisfy Q-=-Q+. This is a
principal-divisor relation in Picard,not a torsion-free claim on points.
The chart is over K;its quintic is not asserted to be an F101 model,or
its class images fixed by plain coefficient Frobenius. [pcc:unverified]

## Finite support of every degree

Require u(a) nonzero. For degree2 support u=x²+b*x+c,put A=u(a).
The transformed monic support is

    U=w²+L(2a+b)*w/A+L²/A.

For degree1 support u=x+u0,the transformed support is

    U=w+L/(a+u0).

For degree0 there is no finite contribution. These follow from the exact
finite-algebra substitution U=w^m*u(a+L/w)/u(a). The old KernelChart
quadratic identities2026a6 cover degree2;BalancedChart.linear_support_transform/
db2184 checks the degree1 implication with explicit inverse/chart hypotheses.
No individual support root is chosen. [pcc:unverified]

For v=v0+v1*x,with missing coefficients zero,the transformed ordinate is
the remainder of

    v1*w²+v(a)*w³/L

modulo U. KernelChart.ordinate_support_transform proves the cleared identity
with inverse L explicit. It applies also to degree1,where v1=0. The
finite support algebra is transported isomorphically,so repeated support
and its ordinate jet are retained. Source validity and transformed curve
validity are independently checked on every input. [pcc:unverified]

For these actual rational corpora,the source branch polynomial is the
accepted irreducible sextic over F101. A degree≤2 F101 polynomial cannot
vanish at a branch of degree6. The implementation additionally checks
u(a) nonzero for every class when selecting the common chart. Failure
would reject that chart;no class is omitted. This does not accept general
geometric supports containing a,or broader field/catalog models.
[pcc:unverified]

## Correct ordinary-Mumford baseline for balanced classes

The input representation means

    D=D_fin+(n-1)*infinity+ +(1-m-n)*infinity-,
    m=degree(u),  0≤n≤2-m.

Let D' be its transformed finite divisor,and let Fclass=[D'-mW],the
ordinary Mumford class of(U,V). The induced Picard image is exactly

    Fclass+(n-1)Q+ +(1-m-n)Q-
      =Fclass+(2n+m-2)Q+.

This follows by substituting Q±=[B±-W] and the principal-divisor relation
above. BalancedChart.balanced_infinity_images/9fd61b proves the integer-
module implication with Q-=-Q+ explicit. It requires no torsion-freeness
or division by2. In particular degree0 inputs with n0/n2 map to-2Q/+2Q;
only n1 is the identity. The old degree2,n0 kernel inputs have correction0,
so their frozen special case remains exact. [pcc:unverified]

Pushforward by the smooth projective isomorphism preserves principal
divisors and is additive on Picard. Thus the formula is a group
isomorphism on its stated representation domain,including multiplicities
and infinities. The mathematical justification is the same standard
projective/Picard functoriality and ordinary/balanced divisor definitions
from Galbraith corrected Chapters8/10 cited in40a568 and the prior balanced
proof. Finite output agreement is not used as a density argument.
[pcc:unverified]

## Exact runtime evidence and boundaries

Producer fixtures dca7d7/6f943f enumerate all12317 classes of each model,
degree counts[3,236,12078],infinity correction counts[1,118,12079,118,1]
and identity index239. Header pins field/model/count/schema. Five-byte
class rows retain degree/plus,implicit monic support and both ordinate
coefficients. Separate complete operator tables contain negation,doubling
and partner(37i+7)%12317 sum indices. These are producer data,not DLP
labels used by the independent arithmetic. [pcc:unverified]

Complete standalone03/4b2aa9 passes12tests/strictClippy/source guards.
The separate old Cantor engine checks all source/quintic validities,all
12317 images distinct,identity and every negation,double and predetermined
paired addition for BOTH models. Wrong field/model/schema,noncanonical
padding/degree,duplicate/truncated classes and out-of-range operator
indices are rejected. The two old49-kernel tests remain. This is not
exhaustive151-million-pair coverage or independent isogeny evaluation/
kernel membership. Actual producer integration/whole guard is separate.
[pcc:unverified]

Two new BalancedChart statements pass the Lean4.35.0 kernel/axiom gate,
zero trusted native,with individually bound theorem records. Together
with the four prior KernelChart identities,they faithfully formalize the
feasible algebra. Actual finite fields,projective completion,valuations,
principal divisors and Picard functoriality remain written bridges. Full
formalization is open and all scientific standing unsigned. [pcc:unverified]

StrictClippy01 duplicate-module/chunk-parser failure7b2f01 and formal
scalar-normalization failures efc7e5/affe42 are immutable. Final shared
module routing/parser02 and explicit module-law proof03 use no exemption,
ignored test,custom axiom or accepted hole. Original subjects and ledger
histories are unchanged. No measured stage,pipeline or ECDLP advantage,
large-prime support or novelty/absence claim follows. [pcc:unverified]
