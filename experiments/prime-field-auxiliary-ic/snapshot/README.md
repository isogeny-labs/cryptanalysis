# Index calculus over F_(2^31 - 1)

**Latest:** [further native optimizations and the rho comparison](algebraic/optimized/README.md)
reduce IC recovery to **9.69 s median** on the original 31-bit instance.
Pollard rho with shared field and point arithmetic takes **18.3 ms median**,
about **530× faster** here. The fused IC solver improves identical search
sequences by 1.79× (median paired ratio); batching further reduces query costs.
All twelve fresh recoveries have independently checked certificates.

The earlier [complete native algebraic attacks](algebraic/end_to_end/README.md)
recover the original 31-bit discrete logarithm with a **2.75× median end-to-end
speedup** over the same factor base without auxiliary maps, and **3.08×** over
an independent random base. Three search seeds per method complete and have
independently verified certificates using distinct relation rows. New cached
GCD and direct circuit backends also improve the original large-base workload.
The earlier [chain-aware resultant measurements](algebraic/structure_results/README.md)
and point-table and generic Groebner experiments are preserved below.

This is a complete, reproducible index-calculus computation: auxiliary curve,
isogeny factor base, three-point relations, modular linear algebra, and recovery
of a test discrete logarithm. It implements the isogeny-factor-base idea in
Petit–Kosters–Messeng, PKC 2016, Section 3.4:
https://people.maths.ox.ac.uk/petit/files/16PKC_primeECDLP.pdf

A matched comparison against index calculus without an auxiliary curve is
recorded in [comparison/README.md](comparison/README.md). Both variants
performed about the same with the explicit pair-sum relation solver.

The subsequently implemented **actual Groebner-based relation solver** and
its algebraic comparisons are in [algebraic/README.md](algebraic/README.md).
It supports both requested fields and a complete small index-calculus test.
The original full-size algebraic attempts reached time or memory limits.

A subsequent [audit](algebraic/audit/README.md) fixes a missing projective
chart in the optional split solver and corrects the target-dependent ordinary
benchmark. The earlier ordinary algebraic timing comparison is withdrawn as
a general performance claim; corrected records are linked in the audit.

The original C++ relation search below uses a meet-in-the-middle pair-sum
table. Its verifier checks the Semaev equations for the relations actually
found. The subsequent algebraic implementation is linked above. No
target-group discrete-logarithm oracle or precomputed factor-base logarithms
are used by either pipeline.

## Run

Requires Python 3 with SymPy, and a C++17 compiler.

```sh
cd /workspace/index_calculus_demo
python prepare.py
g++ -O3 -std=c++17 -Wall -Wextra -o solve solve.cpp
./solve
python verify.py
```

`prepare.py` creates the test instance. `solve.cpp` reads only `public.txt`,
which contains p, curve coefficients, subgroup order, P, Q, and factor-base
representatives. It never reads `expected.json` or the test scalar.
`verify.py` independently audits the stored relations and a weighted linear
dependency certificate, then checks the recovered scalar against Q and the
test fixture. The BSGS computation in preparation certifies the public target
curve order in the Hasse interval; it is not used to compute log_P(Q).

## Target instance

All coordinates below are modulo p.

```text
p = 2147483647
E: y^2 = x^3 + 2x + 14
#E(F_p) = n = 2147505293 (prime)
P = (1, 814455902)
Q = (988441464, 1643383878)
```

Primality of n, a nonidentity point P with [n]P=O, and the Hasse bound certify
the curve order: n is the only multiple of n inside the Hasse interval.

## Auxiliary curve and maps

Use C: y^2 = x^3 + x. Since p = 3 mod 4, pairing x and -x in the quadratic
character sum proves #C(F_p)=p+1=2^31. There is just one nonidentity rational
2-torsion point, so this group is cyclic. This is a supersingular reduction of
the j=1728 CM curve; no ordinary-CM search or point counting is needed here.

```text
T = (3, 615668188),                 order 2^31
G = [2^21]T = (1106623295, 606392145), order 1024
V = {x(T + iG) : 0 <= i < 1024}
```

The coset T+<G> gives 1024 distinct x-coordinates, avoiding the loss of a
factor of two from identifying R with -R inside the subgroup itself.

Quotient by <G> using ten degree-two isogenies. Each x-map has the form

```text
f_j(z) = u + A_j + B_j/u,    u = z-r_j.
```

The complete `(r_j,A_j,B_j)` list is in `auxiliary_31.json`. Its first maps are

```text
f_1(z) = z + 1/z
f_2(z) = (z-2) + 6 + 8/(z-2).
```

For f = f_10 o ... o f_1, the terminal value is

```text
c = x(phi(T)) = 2009175221.
L(z) = f(z) - c.
V = {z in F_p : L(z) = 0}.
```

Use L_j=f_j for j<10 and L_10=f_10-c. The preparation checks all 1024 roots.
Their completeness follows from the degree-1024 composite map and distinctness.
At each step the translated domain is y^2=u^3+A_j*u^2+B_j*u; its quotient is
y^2=X^3-2*A_j*X^2+(A_j^2-4*B_j)*X, with the x-map above and
Y=y*(1-B_j/u^2). The code also checks these point maps and their homomorphism
property on concrete points. Poles are rejected, never treated as roots.

## Factor base and relations

The target-curve factor base consists of the points with x in V. Exactly 500
x-values lift to the target, giving 1000 signed points. The linear algebra
stores one representative per +/- pair, hence 500 columns.

For each random a,b, compute R=[a]P+[b]Q and search for

```text
R = epsilon_1 F_i + epsilon_2 F_j + epsilon_3 F_k.
```

A precomputed table of signed pair sums makes this a three-sum search. A
relation gives the equation

```text
epsilon_1 log_P(F_i) + epsilon_2 log_P(F_j)
  + epsilon_3 log_P(F_k) - a - b*k = 0 (mod n).
```

The exact low-degree system from the slides is available here as well. For
each of the three x-coordinates, introduce z_1,...,z_10. For j<10 impose

```text
(z_j-r_j) * (z_(j+1) - (z_j-r_j) - A_j) - B_j = 0,
```

and impose the terminal equation

```text
(z_10-r_10) * (c - (z_10-r_10) - A_10) - B_10 = 0.
```

Require every denominator z_j-r_j to be nonzero. Add
S_4(z_(1,1),z_(2,1),z_(3,1),x(R))=0 and check the y-coordinates/signs.
Equivalently, introduce w and use two S_3 quartics:

```text
S_3(z_(1,1), z_(2,1), w) = 0
S_3(w, z_(3,1), x(R)) = 0
S_3(x,y,z) = (x-y)^2*z^2
             - 2*((x+y)*(x*y+a)+2*b)*z
             + (x*y-a)^2 - 4*b*(x+y).
```

There are then 31 variables and 32 equations, plus nonzero-denominator
conditions. The solver searches the finite factor base directly instead of
feeding this polynomial system to a Groebner-basis implementation.

## Recorded result

The deterministic run constructed 499940 distinct signed pair sums and found
457 relations from 6334 random a,b trials. Modular elimination reached rank
456 and produced a relation canceling every factor-base variable:

```text
1013612214 + 1022807299*k = 0 (mod 2147505293)
k = 123456789
[k]P = Q
```

The relation-search and elimination run took about 3.11 seconds in this
environment, including the pair table. Setup and independent verification are
not included in that time. All relations are stored in `relations.jsonl`.
Signed code 2i means +F_i; code 2i+1 means -F_i, indexed from zero. In
`certificate.json`, the weights specify a linear combination of the stored
relation rows. The verifier checks that all 500 factor-base coefficients cancel
and the two remaining coefficients equal the displayed dependency.

## The 61-bit field

The same auxiliary curve works for p=2^61-1, with cyclic order 2^61. Preparation
also constructs a 20-step degree-two isogeny chain with a kernel of order 2^20,
appropriate to a three-point factor base of size about p^(1/3). Its parameters
are in `auxiliary_61.json`; 128 coset roots are checked and the full root count
follows mathematically. The original `solve.cpp` remains specialized to the
31-bit field.

A subsequent complete computation over the 61-bit field is documented in
[README61.md](README61.md). It uses a mixed-order target point with a 38-bit
largest prime factor, cofactor-projected factor-base points, and a separate
solver `solve61.cpp`. It recovers the full mixed-order test logarithm; it does
not claim to solve a 61-bit prime-order group.

Finding these maps is only the precomputation step. This small-parameter run
does not establish a speedup over generic DLP algorithms, nor does it solve
ECC2K-130, which uses a different, binary field.
