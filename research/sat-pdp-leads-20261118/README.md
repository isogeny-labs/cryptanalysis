# SAT-solver leads for point-decomposition relation search (2026-11-18)

Status: **desk proposals only.** Nothing here was run. Every statement about
cost or yield below is either a quote from a file on disk or a desk count, and
is `[pcc:unverified]`. The `research-kb` CLI was not available in this
container (`crypto/scripts/research-kb`: no executable), so the prior-work
check is a grep of both repositories, not a KB query.

## 1. Where the program already stands

Before proposing anything, I surveyed the SAT, SMT and XOR work in both
repositories. The conclusion, which the surveyed files support:

- No SAT, SMT or XOR arm goes below the leaf-scan or pair-scan floor on a
  generic target, for any m from 3 to 5, from N13 to N131, or on the prime
  fields tried. The lin21 2+1 leaf under CDCL needs 1.4 to 3 times the scan
  in conflicts and 120 to 270 times the fast native leaf in wall time
  (`crypto:research/sat_native_lin21_n131_20261116`). Dual-rail m=4
  converges to 3 to 4 times the pair scan
  (`crypto:research/sat_smt_leads_20261115`).
- The stated obstruction: the inverse lookup t -> (x1, x2) cannot be
  expressed as propagation, and shared certificates across leaf blocks or
  targets exist only for k = 0 by counting
  (`crypto:research/sat_leads_round4_20261116/PROPOSALS.md`, "Discarded by
  counting").
- Closed, do not re-run
  (`crypto:research/notes/index-calculus/RESEARCH_PDP_SAT_SMT_NAGAO_SURVEY.md` §7):
  a further solver on the subspace system, Riemann–Roch encodings, symmetry
  breaking, one-hot Frobenius phases, Crossbred as the oracle, and Hamming
  ideals under truncated Gröbner.
- Already proposed or piloted, so excluded here: the twelve ideas of
  2026-11-14, leads A–F of 2026-11-15, the exotic-B0 plan, and round-4 A–E.
  The open items are XOR-learning CDCL, Bosphorus-style ANF preprocessing,
  the RES(⊕) lower bound, and truncating the over-determined N131 leaf.
- Prime-field small roots: the Jochemsz–May reach for S3 is at most 1/6,
  against a need of 1/2 (`crypto:research/s5_small_roots_variants_20261018`).
  A lattice-in-CDCL(T) leaf for prime fields therefore inherits that ceiling
  and is not proposed.

The owner's success criterion counts constant-factor gains over the measured
baseline. So the leads below include constant-factor items, and each one says
whether it could change the exponent at all.

## 2. Leads

### L1. Inverted CDCL(T): the native lin21 leaf as the theory solver

- **Mechanism.** Today SAT carries the whole system, while the native leaf is
  120–270 times faster per leaf. Invert the roles. The SAT side holds only the
  constraints the scan cannot express cheaply, such as non-subspace
  factor-base membership (Hamming-weight normal-basis bases), slot coupling at
  m = 4, and orbit selectors. Through IPASIR-UP, a CaDiCaL external propagator
  calls the native leaf as soon as x3 is fully assigned. It returns either the
  (s, p) model or a conflict clause over x3's bits only.
- **Difference from prior work.** The existing propagators
  (`compact-s3-m4-20261003/*/theory_solver.cpp`, `insearch.cpp`) inject S3
  root lemmas once a leaf pair is fixed. This lead moves the whole linear leaf
  into the theory and uses SAT only for the side constraints.
- **Prediction.** On subspace bases: wall time within 2x of the native scan,
  against 120x for CDCL alone. On the Hamming-NB base, where no scan exists:
  below the 117–174x-floor refutation cost recorded in
  `pdp_followups_20261010`.
- **Cheapest test.** Run the existing `fastcdcl` lin21 instances at l ≤ 10
  with leaf calls counted, and the m = 2 Hamming-NB panel (n = 23) with the
  same targets.
- **Kill.** Wall time per decided target is at least 10x the native scan, or
  the Hamming-NB panel shows no improvement beyond the A/A band.
- **Prior.** 50% for a constant gain over SAT-only. About 0% for an exponent
  change on subspace bases. Its real value is opening up non-subspace bases.

### L2. Extension variables mined from the short scan proofs, plus SBVA preprocessing

- **Mechanism.** Lead E (2026-11-15) found that short extended-resolution
  proofs of the scan exist. Extract the extension definitions those proofs
  use and give them to the solver as defined variables. Separately, run
  structured bounded variable addition (SBVA) on the CNF part of the lin21
  and dual-rail instances. The only prior mention of BVA in either
  repository is as a CryptoMiniSat proof source (`01-proof-size-slope`), and
  it was never measured as a preprocessing step.
- **Prediction.** Conflicts fall by 1.3x or more. The exponent stays the same.
- **Cheapest test.** One hour on the existing instances: SBVA+CaDiCaL against
  CaDiCaL, plus the ER-definitions variant, with an A/A arm.
- **Kill.** Conflicts and wall time fall inside the A/A noise band.
- **Prior.** 30%.
- **Done (2026-11-18): KILL.** SBVA was tested on m = 4 dual-rail CNFs at
  l = 3 and l = 4, with 3 shuffles each and an A/A arm. On l = 4 UNSAT, its
  conflicts are 1.061× CaDiCaL's, 95% CI [0.979, 1.143]. That is inside the
  A/A band [0.793, 1.108]. On the dual encoding it is worse, at 1.121×.
  SBVA barely changes these CNFs (+6 variables, −10 clauses). The ER-mined
  extension variables half of L2 was not run. See
  [`l2_sbva/RESULT.md`](l2_sbva/RESULT.md).

### L3. Usefulness gate for round-4 lead A (torsion targets) before building it

- **Desk count.** R4-A decides relations P1 + P2 + P3 = ±T0 by factoring in
  F2[z]. Those relations are homogeneous. A fixed base of size 2^l has about
  2^(3l−n)/6 of them, which is O(1) at n = 3l. The relation phase needs about
  2^l relations. Raising the yield to 2^l needs n ≤ 2l, and then the base and
  the linear algebra (2^(2l) ≥ 2^n) lose to rho.
- **Consequence.** R4-A is a stage gain at best. It can only matter as a
  cheaper source of the few target-specific relations, not for the relation
  phase.
- **Test.** Before any implementation, count ±T0 relations by brute force at
  n ≤ 23 and compare with 2^(3l−n)/6.
- **Kill.** Count matches the estimate → mark R4-A "stage only".
- **Prior.** 85% that the count matches.
- **Done (2026-11-18): R4-A is "stage only".** Exact counts over 16 cells
  with n ≤ 23 and 40 curves each: 40 T0 x-sets observed against an estimate
  of 61.7. A random-target control gives 103 against 123.4. Every curve has
  at most 2 x-sets, against 2^l = 8 to 256 needed. The estimate above should
  read 2^(3l−n)/12, because the 2 global sign patterns double-count. See
  [`l3_torsion_count/RESULT.md`](l3_torsion_count/RESULT.md).

### L4. Support-minors MinRank on the lin21 leaf (refines round-4 D/E)

- **Mechanism.** For fixed x3, the leaf is linear in (s, p). Because squaring
  is F2-linear, the coefficient matrix M(x3) has entries of degree at most 2
  in x3's bits; only the x3^3-type monomials are quadratic. "Some x3 in V has
  a consistent leaf" is then a generalized MinRank instance on M(x3) with an
  augmented column. The support-minors modelling (Bardet et al. 2020) has
  never been tried here; D measures plain Macaulay ranks.
- **Cheapest test.** Build the support-minors Macaulay matrices at
  l = 4..8, measure the solving degree, and compare it with D's bidegrees.
- **Kill.** The solving degree grows linearly in l, so the cost is at least
  the 2^l scan.
- **Prior.** 5%. It is the only lead here with any exponent upside.

### L5. Discarded by counting: char-2 interpolating-conic encoding

- **The idea.** In characteristic 2, the four points cut out by
  y = αx² + βx + γ through −R give a quartic whose coefficients are F2-linear
  in the bits of (α, β, γ). With u = 1/α, the condition e1 ∈ V becomes an
  Artin–Schreier, F2-affine condition on u.
- **Why it fails.** For fixed u, the conditions e2 ∈ V·V and e3 ∈ V·V·V leave
  about 2^(2l−3) values of β. That makes about 2^(3l−2) relaxed survivors
  against O(1) genuine triples. Branching on (u, x3) jointly gives 2^(2l)
  leaves, against 2^l for lin21. Not proposed; recorded so it is not
  rediscovered.

### L6. Open infrastructure item: XOR-learning CDCL in `sat.rs`

This is not new. It is the top open item of the exotic-B0 plan (§3.1) and the
remaining way to test whether learning RES(⊕) clauses changes the
1.4–3x-scan conflict ratio. It is listed for completeness. Pair it with L1
so that both share one harness.

## 3. Recommended order

1. **L3.** Desk count plus brute force: minutes. It closes R4-A's scope.
2. **L2.** One hour on existing instances, with an A/A arm.
3. **L1.** A few days, and the most likely measurable gain. It reuses the
   CaDiCaL ExternalPropagator scaffolding in
   `experiments/compact-s3-m4-20261003`.
4. **L4.** Measurement only. It closes the MinRank question either way.

None of these is expected to make generic-target index calculus beat matched
rho. Under the success criterion, the gap to rho stays the distance remaining.
Any run must follow the repository's protocol and benchmark-record rules:
preregistration, resume checkpoint, `bench.record/v1`, the validation gate,
and §5a pricing.
