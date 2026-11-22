# Generic group + factor-base-membership oracle: an Ω(√p) lower bound (proof sketch)

**Status:** PROVEN sketch (Shoup-style), NOT a formalized Lean proof. It pins down
*why* a cleverer factor base (B3 lattice/hashed bases, interval bases) cannot by itself
beat rho, and names the exact loophole index calculus must exploit. [pcc:unverified only
in that it is not yet machine-checked; the argument itself is standard.]

## Model
Group G = ⟨P⟩ of prime order r ≈ p (one EC subgroup). Adversary is generic (Shoup 1997):
it manipulates group elements only through the group oracle (handles are random labels),
given P and Q = xP, and must output x. We ADD one non-generic affordance:
- a **membership oracle** `MEM(e) → {0,1}` that answers "is the element e in the fixed
  factor base V ⊆ G?", where |V| = p^a, 0 < a < 1.
This is the *most generous* abstraction of a factor base: it charges nothing to test
membership and hides how V was chosen (hashed, lattice-reduced, interval — all the same here).

## Claim
Any algorithm in this model that outputs x with constant probability makes
**T = Ω(√p)** group operations. A factor base, however cleverly constructed, does not
lower the exponent — *unless membership of one element is algebraically correlated with
the discrete logs of others* (the structure the model forbids and index calculus needs).

## Proof sketch
After T steps the adversary has formed T elements e_i = α_i P + β_i Q with known (α_i,β_i).
Two independent effects, each already Ω(√p):

1. **Collisions (the classical bound).** Nontrivial information about x appears only when
   e_i = e_j with (α_i,β_i) ≠ (α_j,β_j), giving x ≡ -(α_i-α_j)/(β_i-β_j). Over the random
   labelling the probability that any of the ≤ C(T,2) pairs collides is ≤ T²/r. For
   constant success T² = Ω(r) = Ω(p), i.e. T = Ω(√p). The membership oracle does not create
   collisions; it only reads a set.

2. **Membership yields no shortcut.** Condition on no collision. Then the handles are a
   uniformly random injection on the ≤ T formed combinations, so each `MEM(e_i)` is a
   Bernoulli(|V|/r) = Bernoulli(p^{a-1}) variable **independent** of x given (α_i,β_i),
   *as long as V is a uniformly random set of its size* — a "1" tells the adversary only
   that this particular combination landed in V, not a relation among logs. Expected hits
   after T queries ≈ T·p^{a-1}; collecting the p^a hits a relation search would want needs
   T = Ω(p^{a}/p^{a-1}) = Ω(p). So the membership route is strictly worse than (1).

Both bottlenecks are Ω(√p). ∎(sketch)

## What it does and does NOT cover — the loophole
The independence in step 2 is exactly what breaks when V is **algebraic**: for a real
Semaev factor base, membership of e is decided by a *polynomial* relation, so one point's
membership is correlated with others' logs through a solvable system. That correlation is
not a group operation and is invisible to this model — which is why it escapes the bound.
This is the precise, provable form of the lab's empirical law *"algebraic bases help only
through lower solving degree, never through yield"*: yield (membership density) is p^{a-1}
for every base, so the only exploitable quantity is the solving degree of the membership
system — routing all hope back to the D_reg question (artifact #2) and the Graeffe/F4 cost.

## Falsifier
Exhibit a factor base V and an algorithm using only group ops + MEM(·) that outputs x in
o(√p) operations with V chosen *without* an algebraic membership predicate (i.e. V given
only as an unstructured set / black-box hash). The bound predicts this is impossible; any
such construction refutes it (and would be a major result).

## Formalization hook
This is the natural extension of the lab's existing Lean generic-model cores from "pure
generic" to "generic + membership oracle". Step 1 is already in those cores; step 2 adds
one independence lemma (Bernoulli(|V|/r) ⟂ x | no-collision). Worth a formal pass — it
would close B3 and all non-algebraic factor-base directions *for all parameters at once*,
which no amount of toy-rung benchmarking can do.
