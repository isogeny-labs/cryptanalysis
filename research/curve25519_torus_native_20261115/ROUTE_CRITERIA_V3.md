# When this index-calculus route is rejected

A route is a quantified algorithmic claim, not a coordinate name. Register
its curve family and parameter path, factor base, target distribution,
allowed preprocessing, decomposition rule, solver, cost model, success
probability, and memory budget before testing. Version the card when any
of those change; preserve previous cards and outcomes.

| Status | Evidence required | Scope of the decision |
|---|---|---|
| Proved exclusion | A checked theorem or exhaustive finite argument whose hypotheses cover the registered claim | Only the specified family/model/range; a finite calculation does not establish an asymptotic statement |
| Counterexample to a universal claim | A reproducible instance satisfying all hypotheses but violating the conclusion | Rejects that universal statement; not all alternatives or a probabilistic claim |
| Quantitative promise rejected | Preregistered statistical test, fixed samples and all outcomes, corrected across the registered family | Rejects the stated finite-range probability/cost promise at the stated confidence |
| Implementation parked | Frozen resource limits reached, unfavorable measurements, or no informative progress | This implementation at these budgets; route remains open |
| Invalid experiment | Failed controls, wrong target distribution, leaked labels, unchecked roots, or missing cost/provenance | No mathematical or performance conclusion |
| Open | No evidence meeting a rejection rule | Requires another discriminating action |

Do not upgrade an implementation parked by timeout into a proved exclusion.
Do not upgrade a producer-written proof or Boolean to a signed PCC verdict.
A standard-basis engine reporting the unit ideal is a solver observation;
an independently checked ideal-membership certificate is needed for an
absence claim, and its mathematical scope still has to be established.

## Specific hypotheses for the torus/S4 route

1. **Construction claim.** The proposed cosets, recognition equation and
   point map define an admissible base on the named curve. Reject an exact
   construction lemma if an explicit input satisfies its hypotheses and
   violates the asserted cardinality, recognition, lifting, or injectivity.
   Degenerate charts and cofactor fibers must appear in those hypotheses.
2. **Circuit claim.** The quadratic circuit projects to the stated rational
   membership and S4 equations on the declared chart. Reject an equivalence
   claim with a checked extraneous or missing solution in its domain.
   Auxiliary degree two and fewer terms are structural properties; neither
   implies a lower solving degree. Roots still need rational point/sign checks.
3. **Solver claim.** The registered solver finds and checks a decomposition
   within cost C(b) with probability at least q(b) for the frozen target law.
   Count timeouts and memory failures as failures of the budgeted promise;
   invalid runs trigger investigation, not selective deletion. Planted controls
   cannot estimate yield on uniform or beacon-derived targets.
4. **Scaling claim.** The named complete pipeline has a lower exponent on
   the named family and parameter path. Apply crypto/docs/ic/SUCCESS_CRITERIA.md
   T2: at least six sizes covering at least 24 group-order bits, held-out
   predictions, family-wise correction, complete cold operation counts and
   all phase upper bounds. An unfavorable fit can reject that registered
   finite-range model. It does not prove an asymptotic lower bound.

## An explicit probability rejection rule

For independent trials, a claim of per-trial success probability at least q
is rejected by zero successes in N fixed trials when `(1-q)^N <= alpha`.
Equivalently the exact one-sided upper confidence limit after zero successes
is `1-alpha^(1/N)`. Choose alpha with the registered multiple-attempt correction
before observing data. For nonzero successes use the preregistered exact
binomial test; state dependence assumptions and keep every sampled target.
This rejects the stated budgeted success promise, not the existence of some
other solver or a different target distribution. Adaptive tuning starts a new
attempt with held-out targets.

## Closure record

Record the exact rejected proposition, proof or raw-data hashes, assumptions,
parameter range, confidence and multiplicity rule where applicable, PCC
standing, exceptions, and the minimal change that would reopen it. Link the
successor experiment. If a hypothesis remains untested, write `pending`.

## Four-point exponent route: explicit boundaries

The current candidate uses four torus cosets and four signed summands on
actual Curve25519. Its proposed randomized-base collision theorem, solver
promise and complete attack-cost claim are separate propositions.
The [crypto proof/cost record](https://github.com/isogeny-labs/crypto/blob/98b6b736a53412ef86f02f9e789edc393af1fc20/problems/curve25519-torus-four-point-decomposition.md)
lists their checkable exit conditions. They are open. [pcc:unverified]

- A verified counterexample satisfying the energy draft's admissibility,
  distinct-index and target definitions would reject that exact bound.
  A high-energy fixed base alone does not refute an average-over-bases bound.
- The proposed planted-to-uniform transfer requires an oracle receiving only
  the public base and target. Exposing the planted tuple or reproducible
  generation labels invalidates that experiment; it does not refute the
  inequality. A synthetic basis isolating a known witness tests recovery only.
- A cost claim must name the budgeted solver and all its phases. To move the
  four-point balance below rho requires gamma<1 for D=soft-O(B^gamma), under
  the stated distribution/rank/family assumptions. A measured slope at one
  Curve25519 divisor cannot establish or disprove that asymptotic statement.
- A solver timeout can reject a frozen finite probability promise if the
  registered sampling and statistical conditions apply. It does not establish
  gamma>=1 for every solver, every representation or every twist.

For example, seven independent failures reject a frozen per-trial promise
q>=3/4 at alpha=1/10000, since (1/4)^7=1/16384<1/10000. A family of at most
100 such preregistered tests has union-bound error at most 1/100. This is an
example rejection design, not a test already run or a claim that q>=3/4
holds. Adaptive tuning needs a new card and held-out trials.
