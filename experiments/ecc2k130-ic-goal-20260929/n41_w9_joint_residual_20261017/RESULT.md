# An exact joint residual prefix filters reachable N41 partial sums

The frozen target and final two signed pair states determine a
necessary pair of partial reciprocals `(w,z)`. Complete enumeration of
the column-disjoint source gives **79,424 distinct pairs**. A reduced
BDD over all 41 bits of `w` and the low 16 bits of `z` has **100,081
nodes**; it accepts every exact source pair and only **10 of 2,048**
independently reachable first-three-pair controls.

The source has 284 signed states in each final slot, yielding 80,656
raw combinations. Exactly 1,232 share a folded column. Every remaining
combination gives a nonidentity residual with nonzero x coordinate.
The archived public relation's `(w,z)` is in the table. A complete
independent checked-Sage replay matched all 79,424 table rows and all
2,048 controls in **49.907 s** of arithmetic, with self peak RSS
**231,800,832 bytes**. The first audit attempt timed out at its frozen
180 s cap while repeatedly converting identical source points; its
input and stderr are retained. Predecoding those points made the full
retry fit inside the same cap.

| Necessary filter | Distinct `(w,z-prefix)` rows | Uniform `z` acceptance conditional on valid `w` | Reachable controls passed / 2,048 | Reduced BDD nodes |
| --- | ---: | ---: | ---: | ---: |
| 8 low `z` bits | 48,399 | 66.57% | 1,372 | 17,831 |
| 12 low `z` bits | 76,799 | 6.60% | 143 | 54,940 |
| 16 low `z` bits | 79,262 | 0.426% | 10 | 100,081 |
| 20 low `z` bits | 79,413 | 0.0267% | 0 | 137,102 |

The reachable controls sample column-disjoint first-three-pair sums
and independently chosen final-pair states under seed 41018. Prefix
passes are filter outcomes; full group equality and all five-slot
column conditions still govern an ordinary relation. The 16-bit gate
passed 0.488% of controls, with a descriptive 95% Wilson interval of
0.265%–0.897% under that frozen control law. The exact support has no
full `(w,z)` hit in those 2,048 controls. The 16-bit gate
adds **367,135 CNF clauses** to the original target-coupled N41
five-pair XCNF. Its final formula has **223,299 variables**,
**706,619 constraints**, and **18,070,603 bytes**. The one-worker build
accepted all 79,424 positives and exactly the 10 expected controls in
**20.002 s**, with self peak RSS **203,554,816 bytes**.

The unpinned public-target query used one CryptoMiniSat worker, a
590-second solver cap, a 600-second parent cap, and 4 GiB combined RSS.
It reached the parent cap after **600.129 s** with status
**`BOUNDED_UNKNOWN`**, 5,767 RSS samples, and **156,401,664 bytes**
sampled peak combined RSS. The assembled target-dependent construction
and query intervals total **765.658 s**: 3.400 s frozen base build,
142.126 s source and control screen, 20.002 s BDD build, and the query.
The separate 28.941 s BDD selection screen and 49.907 s independent
Sage audit are retained. These are component and query diagnostics on an
ordinary host; the complete one-target IC online interval remains open.

A frozen bit-order screen confirmed the selected (w)-first BDD is the
smallest of the three tested orders:

| 16-bit BDD order | Nodes |
| --- | ---: |
| All `w` bits, then `z` prefix | 100,081 |
| All `z` prefix bits, then `w` | 112,012 |
| Interleaved first 16 `w,z` bits, then remaining `w` | 312,982 |

The exact filter is selective on the reachable controls, but this
explicit table encoding did not pass its unpinned N41 solver gate.
The N131 source has much larger free-pair lists, so a direct Cartesian
copy of this table is not selected for the 4-GiB N131 attempt. The
next concrete design gate is an implicit source-conditioned joint
residual representation with a measured N41 query, rather than another
bit order of the same explicit table. `candidate_id` remains null.
`python3 -B verify.py` checks frozen sources and terminal receipts;
`lean JointResidual.lean` checks the group-law and prefix implications.
