# Representation joins for index-calculus research

2026-10-21. Status: bounded native reference implementation and callable
relation-generation adapter; full asymptotic implementation and production
pipeline integration remain open. No measured performance claim.

## What the paper does

Delaplace, Fouque, Kirchner and May, *Solving ECDLP over F_p^ell with
Pre-computation via Representation Technique* (2020),
https://inria.hal.science/hal-02427655v1, sections 3--5.
The uploaded PDF has an extension-field exponent in the actual title.
It studies fixed small extension degree ell>=2, not ordinary prime fields.

Write Q=kP and seek k=k11+k12+k21+k22 modulo r. The four lists contain
k11*P, k12*P, Q-k21*P and -k22*P. Join the first two and last two lists,
keeping sums with x in F_p. A matching **full point** yields k; replay kP=Q.
Carefully chosen scalar sets provide many representations of each k, so
discarding roughly a 1-1/p fraction can leave a representation. This is a
heuristic density argument, not guaranteed coverage on each finite fixture.

The polynomial is built from the group-law necessary condition
G(x1,x2,T)=((x1-x2)^2*(x1+x2+T)-f(x1)-f(x2))^2-4*f(x1)*f(x2),
where f(x)=x^3+a*x+b. Set T in F_p, expand real/imaginary coefficients
over F_p, and eliminate T. A zero resultant is only a candidate: signs,
degree drops and exceptional points require exact group-law verification.
This code evaluates the padded Sylvester determinant at each pair and
explicitly checks its actual sum. It implements neither symbolic product
polynomial construction nor fast multipoint evaluation.

The paper improves the older p^1.314 algorithm to approximately p, then
separates precomputation from online work. At its quadratic-field balanced
point, ignoring logarithmic and arbitrarily small exponent overheads:

| Quantity | Paper bound for field size q=p^2 |
| --- | --- |
| Reusable setup | p^(6/5) = q^(3/5) |
| Per-target work | p^(4/5) = q^(2/5) |
| Memory | p^(4/5) = q^(2/5) |
| Pollard rho comparison | q^(1/2), without that setup |

The authors explicitly do not improve Bernstein--Lange's existing
precomputation tradeoff. The bound depends on Kedlaya--Umans evaluation.
Our pairwise reference remains O(|A||B|), with output storage and downstream
collision costs. No asymptotic paper bound is attributed to this implementation.

## Build and use

Run `sh check.sh` from this directory (C++17 compiler, no dependencies).
Include `representation_join.hpp` from a native collector. The implementation
is header-only so both repos can exercise exactly the same contracts. C++ was
chosen for the shared native module because this authoring environment has
g++ but no Rust toolchain; crypto's Rust production collector is not wired yet.

- `join(curve,A,B,backend,budget)` returns every retained ordered index pair
  and its exact point sum. Repeated input entries preserve distinct witnesses.
  Both `Backend::exhaustive` and `Backend::resultant` are available.
- `Prepared(curve,P,r,S11,S12,S21,S22)` builds target-independent lists and
  the left collision table. `solve(Q)` receives only Q, never its known log.
  A null optional means these constrained lists found no match. Scalar sets
  are supplied explicitly, not claimed to implement the paper's optimized
  digit partitions. Bounded subgroup-membership enumeration costs O(r) and
  must be charged if this reference is ever timed; it is not a fast DLP solver.
- `decompose4(curve,base,R)` returns ordered witnesses for
  R=B_i+B_j+B_k+B_l whose intermediate B_i+B_j has x in F_p.
- `collect_relations(curve,P,Q,a,b,base)` constructs R=aP+bQ and emits rows
  `(a,b,coefficients,witness)` satisfying the verified point equation. These
  become `a+b*k=sum coefficients[j]*log_P(B_j) mod r` at the collector boundary.
  It uses no factor-base logs. The caller must establish all points lie in
  the same prime-order subgroup before modular linear algebra.

The filtered PDP intentionally omits decompositions whose intermediate is
outside the subfield. Its yield must be measured on ordinary queries; never
claim it is a complete unrestricted PDP. Orbit compression, deduplication,
rank tracking and final LA remain downstream duties. Keep all witness signs
and multiplicities when connecting the existing collector.

## Domain and limits

Odd prime 3<p<=101, F_(p^2)=F_p[u]/(u^2-delta), nonsquare delta;
nonsingular short Weierstrass curves, canonical coordinates. Prime subgroup
order <=20000. Inputs and output sizes have explicit caps and fail closed.
Infinity has no x-coordinate and is excluded by the filter; exceptional
addition/doubling cases take the exact path. These bounds make correctness
enumeration feasible; they are not restrictions proved by the paper.

Prime fields such as P-192/P-224 have no proper subfield for this filter.
Embedding their points into a quadratic field makes x in F_p automatic on
that original subgroup and supplies no 1/p selectivity. Binary prime-degree
extensions require different arithmetic and a new complexity analysis.
The reference is variable-time research code, not a cryptographic library.

## Validation and reproducibility

`test.cpp` exhaustively checks all ordered point pairs on three exact curves,
compares the complete filtered join outputs with direct addition, and checks
all targets in the positive order-7 and order-137 fixtures. Four-point witness
sets are compared to an independently enumerated four-index oracle (sharing
the same field/point arithmetic). This is not independent arithmetic or
independent-host verification. Relation rows are replayed using fixture logs.

| p | delta | a | b | #E | subgroup | outcome |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | 2 | (1,1) | (2,0) | 35 | r=7, G=((0,0),(0,1)) | all 7 targets |
| 7 | 3 | (1,1) | (1,0) | 48 | r=3 selected by deterministic enumeration | zero admissible subgroup points, expected no match |
| 11 | 2 | (1,1) | (1,0) | 137 | r=137, G=((0,0),(1,0)) | all 137 targets |

See `records/final-check.txt`, `records/sanitizer.txt`, `records/environment.txt`
and `records/SHA256SUMS`. Earlier fixture failures remain recorded: a singular
p=5 fixture was rejected and corrected; p=7 was initially incorrectly assumed
to have an admissible subgroup and is retained as a negative test.
Address/undefined sanitizer checks pass with leak detection disabled: the
initial LeakSanitizer process failed to inspect sandbox `/proc`; its log is
retained separately. Leak checking is not claimed.
No random seeds, timings, memory benchmarks or promoted IC1 candidates.
No new curve registry or factor-base archive entry is claimed by these unit tests.

## Scope versus requested integration

| Requirement | Status |
| --- | --- |
| Explain supplied paper and IC connection | implemented in this report |
| Native join, four-list correctness path, IC row adapter | implemented, bounded tests |
| Both repositories | identical module and tests in paired PRs |
| Full paper asymptotic backend | not implemented: symbolic product and Kedlaya--Umans routines missing |
| Existing production Rust/C++ collector wiring, rank/LA/target descent | not implemented; adapter API is the current boundary |
| General ell>=2 and large/binary/prime fields | not implemented |
| End-to-end improvement and external-tool comparison | unmeasured |
| Root Cargo suite | blocked: cargo unavailable |
| Conductor reservation | blocked: conductor unavailable; docs/CONDUCTOR.md describes fail-open missing-client behavior |

Open implementation obligations are tracked in crypto's
`problems/representation-join-fast-backend-and-pipeline.md`.
The separate report PDF and diagram describe this same scope.
Canonical IC leaderboards, progress timelines, curve/isogeny graphs and
benchmark indexes remain unchanged: there is no admitted performance result,
new map, or catalog curve here. Sources inspected: crypto's PDP/SAT/SMT/Nagao
survey, cryptanalysis's IC candidate catalog and their root agent rules.

## Literature and next acceptance gates

- Supplied DFKM 2020 paper, especially Algorithms 1--5, Heuristic 1 and section 5.2.
- Delaplace--May 2019, https://eprint.iacr.org/2019/800 (publisher mirror
  https://casa.rub.de/fileadmin/img/2_Forschung/2.1_Publikationen_PDFs/2019_Can_we_Beat_the_Square_Root_Bound_for_ECDLP_over_Fp_2_via_Representations_Publication_ClusterofExcellence_CASA_Bochum.pdf).
  Its zero-join formulation is established prior art. Direct ePrint retrieval
  returned 403; the primary-author mirror was readable. No novelty claim.
- Repository search for `Delaplace` and `representation` did not identify an
  existing implementation of this exact paper; that is a bounded search,
  not an exhaustive repository novelty audit.

Before performance comparisons, implement the fast evaluation backend and
paper scalar-set construction, qualify it against these exact-output controls,
bind a production collector adapter to exact field/subgroup identities, and
freeze an ordinary-query protocol. Count setup, failures, verified rows,
duplicate/rank behavior, matrix solving, target descent and verification.
Use matched rho and Bernstein--Lange references for the relevant accounting
boundary. Merely obtaining a valid row is not evidence of lower total cost.
