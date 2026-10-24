# A non-three-divisible cycle removes the projected conductor-2 kernel

**Contribution.** The frozen inert-2 selection rule chose $D=-227$ over $\mathbf F_{12043}$, where the norm-3 ideal class has order **5** in the conductor-2 ring class group. The 30 conductor-2 degree-3 rows form six horizontal 5-cycles and have **full rank 30 after nonfloor projection**. The complete 70-row matrix has rank **60** both before and after that projection. Ten exact three-descendant commutator relations remain, so the full rank increment of the conductor-2 rows is **20**. This separates the local commutator dependency from the three-term cycle kernel.

| Quantity | $D=-131$, norm-3 order 15 | Prospective $D=-227$, norm-3 order 5 |
| --- | ---: | ---: |
| Class numbers at conductors $1,2,3,6$ | $5,15,10,30$ | $5,15,10,30$ |
| Rational points and eligible rows | $120,70$ | $120,70$ |
| Conductor-2 horizontal degree-3 cycles | Two of length 15 | Six of length 5 |
| Conductor-2 block rank, full / nonfloor | $30/26$ | **$30/30$** |
| Entire relation rank, full / nonfloor | $60/56$ | **$60/60$** |
| Conductor-2 rank increment, full / nonfloor | $20/16$ | **$20/20$** |
| Exact local three-descendant relations | 10 | **10** |

The [selection protocol](selection_protocol.json) was fixed before class search. It required squarefree $d\equiv11\pmod{24}$, the conductor class-number ratios, a nonzero square Frobenius discriminant modulo 11, and norm-3 form order prime to three at discriminant $-4d$. Checked Sage inspected nine discriminants and selected $d=227$, $v=100$, $p=v^2+9d=12043$, $|u|=200$ in [selection.json](selection.json). An independent [form-order audit](order_audit.json) records powers one through 15 of the norm-3 form: precisely powers 5, 10, and 15 are principal. The [fiber gate](fiber_gate.json) found two rational $X_0(11)$ points over every class-polynomial root, giving conductor counts $10,30,20,60$ with no exception. [sage_runtime.json](sage_runtime.json) records the checked repository launcher before the Sage jobs.

The [matrix protocol](producer_protocol.json) froze 70 eligible rows, the prediction of six 5-cycles and full conductor-2 projected rank, and the competing nonzero-kernel outcome before matrix production. The checked-Sage [producer](produce.py) reconstructed all 120 points and 70 rows, checked class strata, trace magnitude, modular-polynomial root counts, explicit rational neighbor sums, and elliptic-curve group-sum identities. [full_matrix.json](full_matrix.json) preserves the point columns, sparse relation rows, and row metadata.

For each of the ten conductor-1 points $P$, the degree-2 correspondence has three distinct conductor-2 descendants $Q_1,Q_2,Q_3$. With $R_2=T_2+2I$ and $R_3=T_3+I$, commutation of $T_2$ and $T_3$ yields

```
R3(Q1) + R3(Q2) + R3(Q3)
    = R2(W1) + R2(W2) + R2(W3) + R2(W4) + R2(P) - 2 R3(P),
```

where $W_1,\ldots,W_4$ are the degree-3 neighbors of $P$. The ten triples have disjoint conductor-2 row support and give ten independent full-matrix relations, bounding rank by 60. The [certificates](certificates.json) record all ten identities and a ten-vector basis of the projected left kernel. The [independent standard-Python audit](validate.py) recomputes exact rational ranks, confirms the six 5-cycles and every certificate coefficient, and checks the same ranks modulo three primes. Its [receipt](validation.json) has status `PASS_NON3_CYCLE_KERNEL_ABSENCE_CERTIFIED`.

The [proof map](PROOF_MAP.json) links the abstract steps to rebuilt Lean modules. `ThreeDescendants.three_downward_commutator` proves the exact three-descendant identity for commuting additive operators. `GeneralCycleKernel.nonmultiple_trivial` proves that a rational three-term recurrence on a cycle of length not divisible by three has only the zero solution; it applies to a 5-cycle once the saved graph is identified with the projected block. The [build receipt](formal/build.json) records the pinned toolchain and mathlib revision, source and output hashes, and `#print axioms` audits. Standard Lean foundations are `propext` for the commutator theorem and `propext`, `Classical.choice`, and `Quot.sound` for the cycle theorem. The Lean bridge from the finite-field $X_0(11)$ incidence to those abstract hypotheses remains open; the saved producer and independent audit check this instance computationally.

The comparison holds class numbers, two-sheet counts, row counts, and the local degree-2 branching pattern fixed while changing the horizontal norm-3 order and field. It is a relation-stage result with `candidate_id: null` and `timing_claim: null`. The next proof step is a formal incidence map from the saved finite-field points and Hecke rows to the two Lean operator models; the next empirical check should seek another norm-3 order prime to three with a different surface class number.
