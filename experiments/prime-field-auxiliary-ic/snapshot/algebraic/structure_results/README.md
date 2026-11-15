# Direct use of the isogeny chain: measured relation-solving speedup

The earlier implementation expressed the auxiliary maps as a generic
multivariable Groebner system. That did not exploit their composition as a
computational circuit. The new solver pushes a quadratic through the chain
directly, using univariate modular polynomial arithmetic.

This rerun demonstrates a limited, measured auxiliary-structure advantage
against an independent random factor base. It is a relation-solving result,
not a completed full-field DLP speed comparison.

## Main result over F_(2^31-1)

The target remains y^2=x^3+2x+14 with prime order 2147505293. The auxiliary
curve is y^2=x^3+x with cyclic order 2^31, supplying fifteen degree-two maps.
The two-point comparison uses 32768 membership roots, near sqrt(p), with
16342 liftable x-coordinates in each base. The bases were fixed before the
same 16 uniform finite target points were sampled. No solution coordinates
were planted.

| Median per target, seconds | Auxiliary chain | Same roots, explicit | Independent random base |
|---|---:|---:|---:|
| Elimination | 0.06945 | 0.12221 | 0.12410 |
| Polynomial gcd | 0.28027 | 0.28153 | 0.28265 |
| Full relation solve | 0.35603 | 0.40507 | 0.40438 |

Thus the auxiliary version has about 1.79 times the elimination throughput
and 1.14 times the full relation throughput of the random-base version.
Median elapsed time falls by approximately 12 percent overall. All methods
completed all 16 tasks; the auxiliary and random bases each had relations
on four targets. The two encodings of the identical base returned identical
resultant polynomials and verified point decompositions on every target.

The random baseline uses a balanced product tree, not a deliberately slow
Horner or quadratic-time expansion. Both implementations use the same native
prime-field arithmetic, gcd, root extraction, and point verification. Method
execution order rotates between targets. These are in-process timings with
membership preparation amortized across targets; setup is recorded separately.

## Why the earlier implementation missed this advantage

1. A low-degree map description is not itself an efficient elimination
   algorithm. The old solver introduced an auxiliary variable at each stage
   and asked a generic Groebner engine to discover the elimination.
2. The direct solver retains only the three coefficients of one quadratic
   at every isogeny stage. It never constructs that multivariable system.
3. The first eight-root tests were correctness-sized examples, much smaller
   than p^(1/m). This two-point benchmark uses a meaningful near-sqrt(p) base.
4. In the improved solver, the common gcd now takes about 79 percent of the
   auxiliary run. That masks much of the faster elimination in the total.

The auxiliary isogenies stay in an isogeny class of order 2^31; the target's
different prime order is preserved on its own curve. The useful shortcut
here is in constructing and solving the membership constraints. It is not
an isogeny transporting the target DLP into the smooth auxiliary group.

## Exact chain-aware elimination

Write F(x,y)=S3(x,y,x(target))=alpha*y^2+beta*y+gamma. Initially set

```text
D = alpha, C = -beta, H = gamma,
Q(z) = D*z^2 - C*z + H.
```

For each map f(z)=u+A+B/u, u=z-r, perform

```text
U  = H - r*C + r^2*D
V  = C - 2*r*D
D' = U*D
C' = V*(U+B*D) + 2*A*D'
H' = (U-B*D)^2 + B*V^2 + A*C' - A^2*D'.
```

This is an exact resultant pushforward of the weighted quadratic Q. After
the final map, with terminal value c,

```text
R(x) = H - c*C + c^2*D
     = resultant_y(S3(x,y,x(target)), P(y)).
```

P is the monic membership polynomial of degree S. There are log2(S) stages
of growing-degree polynomial arithmetic, using four main polynomial
products per stage. Coefficient degrees grow to O(S); this is not a claim
of logarithmic total runtime. The resultant degree is at most 2S.

The solver computes gcd(P(x),R(x)), extracts its F_p roots, solves the
remaining quadratic for y, checks y membership, and checks all point signs.
The degenerate leading-coefficient case x=x(target) is handled explicitly.

The explicit-root comparator computes the same polynomial by

```text
R(x) = product_(v in V) S3(x,v,x(target)),
```

using a balanced multiplication tree. On the identical V, the full
polynomials are compared coefficient for coefficient, not just by checking
one returned relation. A second, independent norm/division implementation
also agrees in the unit tests.

## Original three-point setup

The faster two-point solver is also used in a complete three-point search:
enumerate one factor-base point P3 and solve R-P3=P1+P2 algebraically. This
hybrid enumerates one base coordinate; it is not a monolithic Groebner solve
and constructs no point-pair table. Both comparison versions use the same
strategy, ordering, and stop-at-first-relation rule.

For the original 1024-root, 1000-signed-point setup, four untouched uniform
targets gave median times of 3.294 seconds with the chain versus 4.850 with
the independent random base, about 1.47 times the search throughput. All
four targets had no decomposition, and all searches completed. This is a
small sample of complete rejections, not an estimate of positive-relation
throughput over many targets.

The exact historical known-positive fixture that previously timed out under
generic Groebner solving now returns a verified relation in about 0.169
seconds. The same-root explicit version took about 0.322 seconds. Both
examined 69 identical third-point choices and returned the same relation.
This is a correctness/performance regression fixture, not a randomly
selected performance population. See `original_three_point_case/`.

## 61-bit arithmetic check

With p=2^61-1 and 2048 roots, 16 untouched targets completed at median
0.01484 seconds with the chain versus 0.01867 with the independent random
base. All 16 tasks had no relation. This base is much smaller than sqrt(p),
so these are native 61-bit arithmetic and negative-search measurements,
not a practical 61-bit prime-order DLP demonstration. Unlike the earlier
Groebner implementation, both sides now use native modular polynomials
directly rather than a general coefficient-ring Groebner backend.

## Validation and scope

The full suite has 20 passing tests. They include exhaustive two-point
checks for every finite target on two F_127 curves, an exhaustive three-point
oracle, exact polynomial identities in the 31-bit and 61-bit fields, and
complete index-calculus tests recovering k=37 with both bases for m=2 and
m=3. No DLP oracle is used in relation collection.

The saved runs contain 192 complete two-point computations and 12 complete
three-point searches. `verify_structure.py` audits model hashes, target
independence, point memberships, sums, paired polynomial identities, and
summary arithmetic, and recomputes representative full resultants outside
the timed benchmark. The larger prime-field key was not recovered by this
new engine; the demonstrated benefit concerns its relation-search stage.

## Reproduce

The new engine needs SymPy and python-flint, and does not need Singular.
The local vendor fallback is supported, but vendor binaries are omitted
from the archive. To install the Python dependencies normally:

```sh
python -m pip install sympy python-flint
```

```sh
cd /workspace/index_calculus_demo/algebraic
python test_resultants.py
python benchmark_resultants.py --bits 31 --depths 10 12 15 --targets 16
python benchmark_resultants.py --bits 61 --depths 11 --targets 16
python benchmark_resultants.py --bits 31 --depths 10 --targets 4 --three
python rerun_original_three.py
python verify_structure.py
```

A successful full-size two-point relation from the main benchmark:

```text
(1916797719,1333619539) + (1330482039,2034306337)
  = (517345024,47385547)
```

All coordinates are on the original target curve modulo 2147483647. It is
one of the four relations found among the 16 unmodified benchmark targets.

```sh
python relation_solver.py --engine resultant --m 2 --public ../public.json \
  --auxiliary structure_results/field31_s15/auxiliary.json --encoding chain \
  --x 517345024 --y 47385547 --output structure_example
```

Run full small index calculus with the new engine:

```sh
python index_calculus.py --engine resultant --m 3 \
  --public fixtures/toy_public.json --roots fixtures/toy_roots.json \
  --auxiliary fixtures/toy_auxiliary.json --encoding chain \
  --output full_toy/resultant_chain_m3
```

The resultant engine runs in-process; the total pipeline budget is checked
between calls. The Groebner per-call subprocess limits apply only to that
older engine. Use explicit `--engine groebner` to reproduce those earlier
experiments. The primary implementation is `../resultant_solver.py` and the
benchmark driver is `../benchmark_resultants.py`.
