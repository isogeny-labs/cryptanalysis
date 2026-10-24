# A second inert-2 holdout adds 20 independent conductor-2 rows

**Contribution.** The first eligible larger-surface inert-2 class under the frozen rule is $D=-131$ over $\mathbf F_{13723}$, with class numbers $5,15,10,30$ at conductors $1,2,3,6$. On the 120 rational $X_0(11)$ points, 70 verified degree-2 and degree-3 Hecke rows have rational rank **60**. The 30 conductor-2 degree-3 rows add **20** to the rank of the other 40 rows. Ten exact three-descendant commutator relations account for the ten dependent rows. This repeats the positive-increment result on a surface class more than twice as large as the preceding $D=-35$ holdout.

| Quantity | Frozen prediction | Checked result |
| --- | ---: | ---: |
| Rational points by conductor $1,2,3,6$ | $10,30,20,60$ if the two-sheet gate passes | $10,30,20,60$ |
| Eligible rows by source $c=1,2,3$ | $20,30,20$ | $20,30,20$ |
| Distinct downward degree-2 descendants per $c=1$ point | 3 | 3, covering all 30 conductor-2 points once |
| Conductor-2 rank increment after other rows | Positive, versus zero | **20** full; **16** after nonfloor projection |
| Full rational rank / nonfloor rank | Outcome to measure | **60 / 56** |
| Exact local commutator relations | 10 | **10**, with disjoint conductor-2 row triples |
| Conductor-2 horizontal degree-3 cycles | Outcome to measure | Two cycles of length **15** |

The [selection protocol](selection_protocol.json) fixed the first eligible squarefree $d\equiv11\pmod{24}$ with $4\le h(-d)\le12$, the conductor class-number ratios, a nonzero square Frobenius discriminant modulo 11, and the least prime $p=v^2+9d$ in the stated interval. Checked Sage inspected five discriminants and selected $d=131$, $v=112$, $p=13723$, $|u|=224$ in [selection.json](selection.json). The [fiber gate](fiber_gate.json) found two rational lifts for every class-polynomial root, with no exceptions. [sage_runtime.json](sage_runtime.json) records the checked repository launcher before the Sage runs. [producer_protocol_v2.json](producer_protocol_v2.json) fixed the row-count and rank-increment predictions before the successful producer ran.

For each conductor-1 point $P$, the degree-2 correspondence gives $T_2P=Q_1+Q_2+Q_3$ with three distinct conductor-2 descendants. Set $R_2=T_2+2I$ and $R_3=T_3+I$. Since $T_2T_3=T_3T_2$, the four degree-3 neighbors $W_i$ of $P$ satisfy

```
R3(Q1) + R3(Q2) + R3(Q3)
    = R2(W1) + R2(W2) + R2(W3) + R2(W4) + R2(P) - 2 R3(P).
```

The ten conductor-1 sources have disjoint triples of conductor-2 rows, so these relations are independent and bound the full rank by $70-10=60$. The [certificates](certificates.json) record all ten identities coefficient by coefficient. The independent [standard-Python validator](validate.py) checks them, computes exact rational ranks, and confirms rank 60 modulo each of three primes. It also verifies 14 independent left-kernel vectors after nonfloor projection, bounding that rank by 56; exact and modular elimination attain 56. The 30 conductor-2 rows alone have full rank 30 and nonfloor rank 26. Their horizontal graph is two 15-cycles, each with a two-dimensional kernel for $I+P+P^{-1}$. The [validation receipt](validation.json) preserves these checks and all six rank values.

The [proof map](PROOF_MAP.json) identifies two checked abstract Lean results. `ThreeDescendants.three_downward_commutator` proves the displayed identity for commuting additive operators under the exact three- and four-neighbor hypotheses. `GeneralCycleKernel.recurrence_has_two_parameters` and `periodicPair_cycle` show that rational solutions to the three-term recurrence on a 15-cycle have two free parameters. Both modules rebuilt with the pinned Lean and mathlib versions; the [build receipt](formal/build.json) records the commands, output, source hashes, and `#print axioms` audits. The standard foundations used are `propext` for the commutator theorem and `propext`, `Classical.choice`, and `Quot.sound` for the cycle module. The bridge that defines these particular finite-field Hecke correspondences and graph incidence in Lean remains open; the computational certificates establish the instance-specific premises and ranks.

The first frozen producer used the preceding experiment's field prime when initializing its reduced model and stopped at its initial class-polynomial root-count assertion, before constructing any rows. Its [source](produce.py), [protocol](producer_protocol.json), and [failure receipt](producer_failure.json) remain in the bundle. The corrected [producer](produce_v2.py) and newly frozen protocol supply the measured matrix in [full_matrix.json](full_matrix.json).

This is a relation-stage result with `candidate_id: null` and `timing_claim: null`. The next experiment should vary the conductor-2 horizontal cycle lengths away from multiples of three while keeping 2 inert and the same two-sheet gate. That separates the three-descendant full-rank increment from the projected cycle-kernel effect.
