# Two next leads for known-label construction

2026-10-28. **Research proposals with derived algebra and correctness controls;
no attack improvement or new timing result is claimed.** The original goal
remains an efficient construction into a small usable coordinate domain, with
lower complete cost. Repeating its blocker is not the next research step.

This note develops two alternatives to the earlier fixed-norm/cubic lifts.
It does not change PR #1215, its historical archive, or official hypothesis
status. No new elliptic-curve experiment or performance run was launched.
The setting is a short Weierstrass curve over F_p with p>3, a prime-order
subgroup G=<P> of odd order r>3, and Q in G. Parameters are symbolic; this
note registers no new curve/candidate ID or measured run ID.

## 1. Obtain individual labels from pair relations

Choose the coordinate domain first, enumerate its actual subgroup-usable curve points, and
fix one orientation R_i per usable abscissa. The points initially have unknown
representations. A verified decomposition

    R_i + R_j = T_e = [a_e]P + [b_e]Q

is an edge in a label graph. It supplies a linear equation for the two unknown
labels, rather than requiring either label in advance. For a triangle:

    2 R_1 = T_12 - T_23 + T_31.

Thus R_1 has label ((a_12-a_23+a_31)/2,
(b_12-b_23+b_31)/2), modulo the odd prime group order r. The other two
labels follow. More generally, a connected non-bipartite component determines
labels from any odd cycle; a bipartite component needs one labeled anchor.
If different cycles yield inconsistent coefficient pairs, their discrepancy
is a zero relation [a]P+[b]Q=O. For b != 0 it yields a candidate DLP solution,
which must be independently verified and counted as an early success.

This directly attacks the previously unresolved u_i,v_i construction. The
domain need not move, and its original sparse membership equation is retained;
only actual curve points become graph vertices. The technique is related to
classical relation linear algebra and large-prime graphs, not a claim that graph
methods are new.
B denotes usable abscissae, not raw ambient-domain size. Charge lift and
subgroup filtering. An ambient binomial may be retained with curve/subgroup
and exact chosen-base checks; it is not the filtered set's two-term vanishing
polynomial. The sparse ambient equation alone never certifies a labeled vertex.
The atlas already tracks rank-aware large-prime graphs in
[LEAD-ICE-relation-graph-rank-large-prime](https://github.com/isogeny-labs/crypto-autoresearcher/blob/3df4a9ffdbbf9e2c797c279e9ddfc6518c9a91e9/knowledge/leads/ecdlp/ic-engine/LEAD-ICE-relation-graph-rank-large-prime.yaml).
The proposed variant uses pair equations to create labels inside the chosen
domain, not only to cancel outside large primes from an existing relation pool.

### Complete first implementation

1. Enumerate and verify the B usable vertices. Build a dictionary of all
   distinct pair-sum targets with their full edge lists; do not discard pair
   collisions. This costs O(B^2) group additions and storage in this control.
2. Generate labeled T=Q+[u]P with the existing charged window sampler. Look up
   every target, record failed queries, and insert every verified matching edge.
3. Propagate labels with `label_graph.py`. Stop at the declared sufficient
   labeling/rank criterion or an independently verified earlier DLP solution.
4. Verify recovered labels in the curve group, then use the existing chosen-base
   relation solver. Do not report the graph update cost as the whole constructor.

If K distinct targets are indexed, a uniform query hits the dictionary with
probability exactly K/r. Graph connectivity and edge distribution must be
measured, not assumed. Under the explicit additional random-edge model with
K=Theta(B^2), collecting O(B log B) edges suggests O(r log B/B) queries and
an O~(B^2+r/B) construction scale. This is a heuristic cost model, not an
established bound for multiplicative-coset points and not a rho improvement.
The optimized interval/multi-target BSGS constructor is a mandatory control.

The first discriminating question is whether this complete constructor beats
the best existing one on the same saved point domain. If not, keep its pair
table as a control and investigate a compressed pair-decomposition oracle;
do not recycle an old coset as a new mechanism or claim the O(B^2) table is free.

## 2. A four-seed cubic base with signed-moment reconstruction

Let r>3 be prime and I={0,...,B-1} with B<=r. Sample four independent uniform
label pairs (a_j,b_j), and construct T_j=[a_j]P+[b_j]Q. Define

    F(i) = T_0 + [i]T_1 + [i^2]T_2 + [i^3]T_3.

Every point is labeled by the same scalar polynomials in a_j and b_j.
Forward differences require three group additions per index after charged
seed/initialization work. The previous degree-five construction required five;
this comparison is an operation count for that generator alone. An optimized
independent window sampler is already cheaper per point and remains a control.

Keep the signed events F(i)+F(j)-F(k)=O, with three distinct indices and the
positive pair unordered. Put s_m=i^m+j^m-k^m for m=1,2,3 and

    D = (s_1^2-s_2)/2 = (i-k)(j-k).
    k = (-s_1^3+3 s_1 s_2-2 s_3)/(6D).
    i+j = s_1+k,       i*j = D+k s_1.

D is nonzero for distinct indices. The negative index and the unordered
positive pair are therefore uniquely determined by the three moments;
the pair is recovered from a quadratic. Index bounds, discriminant and the
actual point relation still have to be checked. This is a Prony/Padé-style
signed-moment reconstruction, not a novel general reconstruction theorem.

### Written probability argument, scoped to one-minus triples

Each event has coefficient vector (1,s_1,s_2,s_3) on four uniform seed points.
The reconstruction above makes distinct event vectors distinct and hence
nonproportional. Their zero-sum events are pairwise independent. Conditional
on the group relation, the Q-label coefficient is uniform. Thus useful-event
probability is q=(r-1)/r^2, and useful-event indicators are pairwise independent
too, by applying the rank-two coefficient map to independent seed label pairs.

For M=3*binomial(B,3), the second-moment bound gives

    Pr(at least one useful event) >= M*q/(1+(M-1)*q) - B^2/r.

The final subtraction excludes identity vertices and F(i)=+/-F(j), by the
pairwise-independent evaluation bound. Truncate a negative bound at zero.
For B asymptotic to r^(1/3), this gives 1/3-o(1). This is a derived written
bound, not a measured relation rate or a checked Lean probability theorem.

Do not assume the all-plus events are independent of this family. There is
an explicit counterexample modulo 11: the moment vector of (0,1,2), all plus,
equals three times that of (3,10; negative 1). Restricting to one-minus events
keeps 3 of the 4 global-sign classes, a transparent 4/3 event-count loss.

### Dedicated-solver opportunity

Compile the cubic Horner generator using shared index bits and complete curve
arithmetic; use signed-moment reconstruction as a propagation/decoding rule.
The scalar field F_r and coordinate field F_p remain distinct. Compare this
with the previous degree-five circuit, independent window sampling, direct
pair search and the existing trace-fiber solver on matched inputs. Enlarging
the base by (4/3)^(1/3) equalizes the leading signed-event count, but does not
establish a timing improvement. Full-width moment scalar multiplication may
cost more than direct small-index Horner evaluation and must be charged.

This lead changes the domain to the explicitly generated set of B abscissae;
it does not assert a small multiplicative coordinate product set. Its possible
advantage is a more structured generator circuit and exact signed decoding.
Small circuit size alone does not imply efficient solving. A useful solver must
reduce complete cost against the optimized pair baseline, not merely remove
variables or display low-degree equations.

## Validation and next decision

`test_algebra.py` checks symbolic identities and abstract-group graph controls,
including a cycle that exposes a logarithm. These are correctness controls;
they contain no empirical elliptic-curve performance comparison. Run:

    python -m unittest discover -s docs/known-label-next-leads-20261028 -p test_algebra.py -v

`Algebra.lean` contains proposed proofs of four ring identities. The initial publication had
no native build and was rejected by the active corpus-admission check. The
corrective gate integration binds the exact source SHA to the existing pinned
Lean/Mathlib compiler and exhaustive axiom auditor. Local Lean/Lake remain
unavailable: a successful current-head `corpus` CI job is required before
claiming native verification. See [CI_INTEGRATION.md](CI_INTEGRATION.md) for
the original failure, fixed build path and proof map. The full graph-to-elliptic-
group bridge, signature injectivity and probability statement remain
unformalized. Ring identities and symbolic checks do not replace those proofs.

Before any new benchmark, freeze the protocol and full cost boundaries, obtain
the repository checkpoint receipt, and follow current curve-identity, execution,
isolation and matched-baseline rules. No experiment is scheduled by this note.
Prioritize the graph constructor; the second test is the cubic circuit with
the one-minus decoder. Preserve failures, memory and scalar replay costs.

## Sources and novelty scope

- Existing code/data and exact unresolved requirement:
  [Frobenius/block publication](https://github.com/isogeny-labs/cryptanalysis/pull/1215),
  including its later accounting correction. No historical archive is edited.
- The program atlas was consulted and matched; see `atlas-matches.json` and
  its pinned source revision. Graph algebra, relation linear algebra,
  polynomial sampling and Prony reconstruction are established tools. These
  are concrete next variants for this prototype, not claims of global novelty.
  Its 147 lead files and 52 known-result files were downloaded at a frozen
  revision and Git-blob hashes checked. The first matcher invocation failed
  because the snapshot root was absent from PYTHONPATH; that log is retained.
  The successful invocation used the same unchanged matcher and catalog.
- Petit, Kosters, Messeng, PKC 2016: sparse/composed coordinate domains already
  occur in prior work. A better complete construction/solver cost is still owed.
- [Diem, double-large-prime index calculus](https://arxiv.org/abs/math/0606607):
  related graph methods for curves; its genus>=2 result is not a result for
  this prime-field elliptic-curve proposal.

No new curve, isogeny or verified map is asserted. The existing volcano-IC graph
set and curve-catalog roles were checked for applicability; no canonical edge
or curve record changes. The diagram in this note is algorithm/data flow only.
