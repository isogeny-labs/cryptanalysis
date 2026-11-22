# Three attempts to combine known labels with structured coordinates

The prototypes establish cheap auxiliary lifts, exact trace-aware divisor
identities, and an exact coset block certificate. They do **not** establish
an efficient complete attack. The key obstruction identified here is precise:
in either lift, a prescribed set of B orbit-parameter values covers at most
2B nonzero prime-field trace points. Allowing a free parameter makes lifting
cheap; restricting that parameter to a small prescribed domain restores the
rare-hit problem for an independent uniform labeled sampler.

All performance curves have full prime order, are nonanomalous, and use toy
fields. The anomalous fields p=17 and p=97 occur only in construction and
exhaustive correctness checks. No novelty is claimed for rational-map factor
bases, divisor/norm formulations, resultants, or baby/giant indexing.

## 1. Quadratic fixed-norm lifts

Let E be `y^2=x^3+A*x+b`, let `T=(X,Y)=uP+vQ` be known-labeled, and fix
nonzero nu and a nonsquare Delta. Solve

```text
X*s^2 + 2*Y*s + X^2 + A - nu = 0.
a = (s^2-X)/2,
beta^2 = (a^2-nu)/Delta,
R = (a+beta*sqrt(Delta), s*(a-X)-Y+s*beta*sqrt(Delta)).
```

For a returned nonrational abscissa, `N(x(R))=nu` and `R+pi(R)=T`.
The first discriminant reduces to `b+nu*X`. The construction handles X=0
separately. Labels remain on T. The norm domain has approximately p abscissae
in F_(p^2); fixing the norm does not make it a B-point domain.

Write t=`x(R)+x(pi(R))`. Eliminating the line slope gives the exact
correspondence in the trace abscissa:

```text
G_nu(X,t) = X^2*(t^2-4*nu)
           -2*((A+nu)*t+2*b)*X +(A-nu)^2-4*b*t = 0.
```

If three chosen trace points sum to O, their six conjugate points have a
principal divisor. Its normalized function has the form

```text
g(Z)+k(Z)*y,   deg g=3 (monic), deg k<=1.
H(Z)=g(Z)^2-k(Z)^2*(Z^3+A*Z+b).
H(Z)=product_i (Z^2-t_i*Z+nu).
```

Reciprocity imposes exactly the coefficient conditions
`H0=nu^3`, `H1=nu^2*H5`, `H2=nu*H4`. In particular, for
`K(U)=product_i(U-t_i)`, `H(Z)=Z^3*K(Z+nu/Z)`.
This gives a concrete five-coefficient surface on which to seek a better
direct solver. The current implementation verifies that surface and performs
exact orbit projection followed by univariate line fibers; it does not claim
a faster solver directly on the five-coefficient surface.

The trace-zero condition is essential. Across the checked quadratic relations,
302 of 304 conjugate choices had a **nonidentity** extension sum whose trace
was zero. Replacing the trace condition by `sum R_i=O` would discard valid
relations. The reciprocal identity itself does not eliminate chosen-base
membership: its parameter polynomial is `V(U)=product_{t in base}(U-t)`.

## 2. Cubic fixed-coefficient Frobenius lifts

Fix c!=0 and d; the orbit polynomial is `q(Z)=Z^3+h*Z^2+d*Z-c`.
In the four-point divisor identity, put

```text
v = w*Y-X^2-u*X,
g(Z) = Z^2+u*Z+v,
g(Z)^2-w^2*(Z^3+A*Z+b) = (Z-X)*q(Z).
```

The two prescribed coefficients reduce to

```text
D(w) = 2*(Y*w-X^2),
N(w) = (2*X^2+A)*w^2-4*X*Y*w+2*X^3+X*d-c,
K(w) = X*w^2-2*Y*w+X^2+d,
N(w)^2-D(w)^2*K(w)=0.
```

This is a quartic. For D!=0 recover `u=N/D`; zero-denominator fibers are
handled explicitly. Keep only irreducible q. A formal root x of q and
`y=-g(x)/w` supplies a Frobenius orbit with elliptic trace T.

Two representations are measured on the same accepted points. The common-field
variant extracts a root in one fixed F_(p^3), allowing actual extension sums.
The formal variant stores `(q,u,w)` and verifies the degree-four divisor
identity over F_p. That is sufficient for trace computations and F_p divisor
equations, and avoids charging an unnecessary common-field embedding. It
does not pretend that unrelated formal roots can be added directly.

For a zero relation among three traces, all nine conjugates form the divisor
of `g_4(Z)+k_3(Z)*y`, with k_3 monic. Its norm is

```text
k_3(Z)^2*(Z^3+A*Z+b)-g_4(Z)^2 = product_i q_{h_i}(Z).
```

Writing `D(Z)=Z^3+d*Z-c`, the right-hand side is
`D^3+S1*D^2*Z^2+S2*D*Z^4+S3*Z^6`. This is a degree-three rational-map
pullback; the selected h_i still need their actual degree-B membership
polynomial. A symmetric S_4 resolvent projects one h to a degree-four trace
abscissa polynomial. The chosen-set projection has degree 4B before
F_p-root and trace filtering.

The quartic prototype checked 8,568 target/constant pairs, exhaustively matched
632 systems against an independent (u,w) enumeration, and verified 2,796
returned orbits in common cubic fields. At p=65,537 the four constants tested
lifted 64, 70, 81 or 93 of the same 256 targets. These are construction counts,
not evidence of faster relation finding.

## 3. A small-domain bound for both lifts

**Proposition.** In the quadratic construction, require nonrational abscissae
and prescribe B values of t. At most 2B nonzero traces can occur. In the cubic
construction, fix c,d, require irreducible orbit polynomials and prescribe B
values of h. Again at most 2B nonzero traces can occur.

**Proof.** For a fixed quadratic t, the irreducible polynomial
`Z^2-t*Z+nu` determines one conjugate pair of abscissae. At one abscissa the
curve equation has at most two ordinates. Frobenius determines the ordinate
at the other abscissa. The resulting traces are T and -T. Similarly a fixed
irreducible cubic q determines one orbit of three abscissae; at a chosen root
there are at most two ordinates, whose Frobenius orbits have opposite traces.
Take a union over the prescribed B values. This proves both claims.

Consequently an independent uniform labeled group point has nonzero
restricted-lift success probability at most `2B/r`, even if it may choose
any of its lifts. Independent rejection sampling needs at least `r/(2B)`
draws on average for one hit. This bound does **not** rule out a genuinely
nonuniform label-construction algorithm, an adaptive domain, or a new direct
solver exploiting the covers.

The bound was exhaustively checked on five fields. At p=1153, r=1193,
the unrestricted quadratic and cubic lifts covered respectively 454 and 334
targets. Restricting t or h to the fixed 16-element multiplicative subgroup
left respectively 12 and 4 targets. A sampled set of B=48 parameters in the
largest benchmark had all 49 coefficients nonzero in every membership
polynomial, for both families. There is no two-term vanishing polynomial
for those selected bases.

## 4. Arithmetic-progression block certificates

Let `M=2*b0*g0`, `H=[1/2]P`,

```text
S_i = H+[i]P,                 0<=i<b0,
R_k = T+[2*b0*k+b0-1/2]P,    0<=k<g0.
```

Then `R_k-S_i` and `R_k+S_i` cover exactly `T+[j]P`, `0<=j<M`.
There are no missing centers or duplicated endpoints. Half scalars are modulo
the odd group order. Setup, point-at-infinity cases and doubling cases count.

For fixed U=`x(S_i)` and V=`x(R_k)`, write S_3(V,U,Z) as
`a2*Z^2+a1*Z+a0`. The raw coset constraint is `Z^B=c0`.
Set `s1=-a1`, `v1=a2*a0`. When B is a power of two, repeatedly use

```text
s_(2n) = s_n^2-2*v_n,   v_(2n)=v_n^2.
Res_Z(Z^B-c0,S_3(V,U,Z)) = a0^B-c0*s_B+c0^2*a2^B.
```

This homogeneous identity remains valid at a2=0; it requires no denominator
inversion and never expands Z^B into roots. Compute it modulo the giant-point
polynomial `G(V)=product_k(V-x(R_k))`, multiply over babies modulo G, and
evaluate at the giants with remainder trees. A zero localizes a matching baby
through the product tree. Recover both signed indices and verify the actual
curve points and labels. Identity indices are also detected by the baby/giant
points and recorded as legitimate early DLP opportunities.

This preserves the binomial and composition throughout the calculation. Its
current cost is `O~(b0*g0*log B)` field work, approximately M, plus
`b0+g0` group work and output recovery. The conjectural `O~(B+sqrt(M))`
total bound is still missing. A separate coordinate-product implementation
uses `product_i S_3(V,x(S_i),z)` for each usable coordinate z and costs
`O~(s*(b0+g0))`; it is also benchmarked.

## 5. Matched validation and cost accounting

The exhaustive block audit compared all four algorithms on 3,978 blocks,
verifying 6,000 hit indices, 1,080 identity indices, 1,620 recovered pole
cases and 11,124 independent ordinary resultant evaluations.

The lift benchmark uses 64 sampled bases, 18 with no relation. Batched pairs,
trace fibers and orbit-projected trace fibers produce identical relation sets.
All 78 resulting degree-six or degree-nine principal divisors are checked.
Construction counts every rejected lift, sampler setup, formal or common-field
point representation, root extraction and point verification. At B=48 the
quadratic chosen-set projection has degree 96 and the cubic projection degree
192; projection returns exactly the original 48 trace coordinates.

For the block construction benchmark, all four methods receive identical
known-labeled random progression starts and collect all 33 usable coordinates
of the same 64-element coset at p=65,537. There are eight complete trials,
515 progression blocks per algorithm in total, including 58 failed blocks.
Each recovered label is independently re-evaluated using P and Q and its
cost is charged. Input generation, shared setup and index recovery count.
The BSGS table is tuned for the predicted total number of reused blocks, not
just one block; it has 2,048 points in this complete-construction experiment.
The checked-in `results.json` contains the actual total CPU seconds and group
counts; the two certificates use fewer group additions while BSGS is faster
in total CPU time. Early identity and antipodal solutions are recorded. These
full-base experiments deliberately continue collecting the domain; they are
not counted as complete DLP attack benchmarks.

The standalone audit replays the transcripts independently. Timings are toy
implementation observations and vary with the host. Exact identities, counts,
accepted sets and transcript hashes are reproducibility targets. No scaling
fit or held-out attack prediction is asserted.

## Reproduction and remaining work

From this submission directory, use Python 3.12 and install `requirements.txt`,
then run `bash run.sh`. In the original workspace dependencies were installed
under `/workspace/research-deps`; that path is optional and not required by
the scripts. `python3 experiments/ideas/audit_results.py` audits checked-in
data without rerunning the timed experiments and uses no third-party package.

All source and raw data are included. `results.json` summarizes measured
totals; `manifest.json` records hashes. The scripts never use a discrete-log
table in a construction or solver. Planted secrets belong to the toy input
driver and its verification, not to the construction routines.

The unresolved tasks are a faster direct solver on the reciprocal divisor
surface with chosen-base membership intact, or a block certificate that avoids
the current M-scale field work while recovering indices. A nonuniform
construction that biases known labels into a small usable coordinate domain
is still required for the original combined attack.

The rational-map factor-base framework already appears in
[Petit–Kosters–Messeng, PKC 2016](https://people.maths.ox.ac.uk/petit/files/16PKC_primeECDLP.pdf).
The known-label single-relation setting is related to
[Amadori–Pintore–Sala](https://eprint.iacr.org/2017/609).
The present note assesses explicit constructions, restrictions and complete
component costs, rather than claiming those general map families as new.
