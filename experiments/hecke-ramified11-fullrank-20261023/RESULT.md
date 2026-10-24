# The full ramified level-11 relation matrix has 38 commutator redundancies

**Contribution.** The complete $D=-1199$, $p=10891$ conductor-6 class has **228 rational $X_0(11)$ points and 190 verified degree-2/3 Hecke rows**. Its exact rational row rank is **152**; after removing the 76 conductor-6 floor columns, the rank is **150**. The 38 conductor-2 degree-3 rows retain rank 38 by themselves but add **zero** rank to the other 152 rows. Each has an exact eight-term certificate explained by degree-2/3 Hecke commutation. Two independent floor-only row directions are alternating sums on the conductor-3 degree-2 cycles.

| Frozen or measured quantity | Value |
| --- | ---: |
| Points by conductor $1,2,3,6$ | $38,38,76,76$ |
| Eligible verified degree-2 rows | $38+76=114$ |
| Eligible verified degree-3 rows | $38+38=76$ |
| Full row rank over $\mathbf Q$ | **152 of 190** |
| Nonfloor projected rank over $\mathbf Q$ | **150 of 152 columns** |
| Conductor-2 degree-3 block rank / increment after other rows | **38 / 0** |
| Floor-only row-space directions | **2** |

[protocol.json](/Volumes/SSD990/cryptanalysis/experiments/hecke-ramified11-fullrank-20261023/protocol.json) froze the point and eligible-row counts, exact source hashes, and the rank questions before the full producer ran. It left the full rank, conductor-2 increment, and floor-only dimension unknown. The checked repository Sage launcher saved [runtime information](/Volumes/SSD990/cryptanalysis/experiments/hecke-ramified11-fullrank-20261023/sage_runtime.json) before the run. [produce.py](/Volumes/SSD990/cryptanalysis/experiments/hecke-ramified11-fullrank-20261023/produce.py) reconstructed every CM $j$-root, checked trace magnitude 20, endomorphism conductor, and the one-point rational level-11 fiber, then verified each eligible Hecke row against the classical modular polynomial, rational root count, and elliptic-curve group-sum identity. The complete points, rows, metadata, root counts, and exact ranks are in [full_matrix.json](/Volumes/SSD990/cryptanalysis/experiments/hecke-ramified11-fullrank-20261023/full_matrix.json).

Let $T_2,T_3$ act on the free abelian group of level-11 points, and put $R_2=T_2+2I$, $R_3=T_3+I$, using the measured $X_0(11)$ eigenvalues $a_2=-2$, $a_3=-1$. For a conductor-1 point $P$, the saved incidence has $T_2P=Q+U+V$, with the unique conductor-2 descendant $Q$ and two conductor-1 neighbors $U,V$. Write $T_3P=W_1+W_2+W_3+W_4$. Commutation gives the local eight-term identity

```
R3(Q) = R2(W1) + R2(W2) + R2(W3) + R2(W4) + R2(P)
        - R3(U) - R3(V) - 2 R3(P).
```

The 38 conductor-1 points have 38 distinct conductor-2 descendants. [certify.py](/Volumes/SSD990/cryptanalysis/experiments/hecke-ramified11-fullrank-20261023/certify.py) solved the exact rational row combinations and saved [certificates.json](/Volumes/SSD990/cryptanalysis/experiments/hecke-ramified11-fullrank-20261023/certificates.json). Every conductor-2 row has exactly eight nonzero terms; [validate.py](/Volumes/SSD990/cryptanalysis/experiments/hecke-ramified11-fullrank-20261023/validate.py) rebuilds all 38 identities directly from the saved neighbor incidences and verifies every coefficient over $\mathbf Q$. This is the concrete instance of the commuting-Hecke identity, whose general operator rule is described in [Snowden's Hecke lecture](https://websites.umich.edu/~asnowden/teaching/2013/679/L16.html).

The same validator reconstructs the conductor-3 degree-2 horizontal graph as two cycles of length 38. Alternating $+1,-1$ coefficients around each cycle cancel all nonfloor columns; each resulting row vector has 38 nonzero conductor-6 coordinates. The two vectors are independent. Exact rational elimination gives ranks 152 and 150; the independent replay verifies 38 row-span certificates, the two floor vectors, and matching modular-rank lower bounds at three primes. These lower bounds plus the exact combination certificates prove the stated rational ranks without accepting a single rank routine as an oracle. The [validation receipt](/Volumes/SSD990/cryptanalysis/experiments/hecke-ramified11-fullrank-20261023/validation.json) binds the inputs and verifier.

The [Lean module](/Volumes/SSD990/cryptanalysis/experiments/hecke-ramified11-fullrank-20261023/formal/HeckeCommutator.lean) proves both that the residual operators commute when $T_2,T_3$ commute and that a unique $Q$ in $T_2P$ obeys the displayed eight-term identity. Its [build receipt](/Volumes/SSD990/cryptanalysis/experiments/hecke-ramified11-fullrank-20261023/formal/build.json) pins the toolchain and mathlib revision; both declarations built, with `#print axioms` reporting only `propext`. The remaining geometric Lean bridge is the identification of these abstract endomorphisms and incidence hypotheses with the saved finite-field $X_0(11)$ Hecke action. The graph and row certificates verify that bridge for this exact field, while its general formalization remains open.

This is a relation-stage result with `candidate_id: null` and `timing_claim: null`. The next experiment should test whether a different conductor and level can break the local commutator redundancy or alter the parity of the degree-2 cycles; for this field, the additional conductor-2 block cannot increase global useful row rank.
