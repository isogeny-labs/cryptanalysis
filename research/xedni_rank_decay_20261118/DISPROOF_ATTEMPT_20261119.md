# Xedni decay-heuristic disproof attempt

Date: 2026-11-19

User request: `Disprove the decay heuristic`.

## Binding acceptance criteria

This attempt retains the already frozen experiment and does not redefine a
small control, mechanism signal, or underpowered sentinel as a disproof.
[pcc:unverified]

| Requirement | Binding evidence for a disproof | Initial state |
| --- | --- | --- |
| Prime range | Natural rows at the prospectively frozen even bit sizes from 16 through 32 | No natural rows |
| Independent variables | Lift strategy, selected-point count `r`, and Silverman/JKSST small-prime local conditions crossed independently | Frozen design exists |
| Endpoint | Doubly certified nontrivial useful target recovery with exact rational and source replay; rank and dependence remain separate | No natural outcome |
| Decay decision | Simultaneous signed `beta` lower bound above `-0.8` under every admitted unresolved allocation | Not measured |
| Event support | At least 30 certified high-bit useful events globally, with events at 20, 22, and 24 bits in each stage | Zero events |
| Replication | Fresh prospectively frozen replication seed and prime identities | Unallocated |
| Work | Complete construction, failed attempts, duplicates, rank, relation, recovery, verification, storage, and timeout accounting | No natural work |
| Tool agreement | Pinned PARI rank bounds plus licensed pinned Magma 2-descent for every event/unresolved row required by the protocol | Magma previously absent |
| Evidence | Pushed-head checkpoint, clean authorizing freeze, exact row provenance, and trusted independently signed execution receipts | Previously blocked |

## Execution order

1. Recheck checkpoint transport, licensed Magma/Sage, trusted verifier, and
   committed compute without bypassing any gate.
2. Close every remaining locally implementable natural-run integration and
   freeze obligation.
3. If all gates pass, checkpoint the pushed head and run the excluded 1,080-row
   16/18-bit calibration exactly as frozen.
4. Freeze resources and fresh replication identities separately; calibration
   outcomes may not choose or downscale the discovery design.
5. Run discovery and replication to the frozen stopping rule, retaining every
   row and cost.

Passing a control, completing code, or observing a toy relation does not satisfy
the request. The claim changes only if the full decision rule passes on natural
discovery and fresh replication evidence. [pcc:unverified]

## Recheck and a two-torsion lead

At pushed commit `ec89f4eb634fe31fd1cac30a7812a4175a826be9`, the mandatory
checkpoint upload and gate failed: neither the configured AWS profile nor the
checkpoint upload token was available. No natural row was started. A separate
runtime audit found the pinned PARI image and passed its known-rank controls,
but found no licensed Magma executable or image, and no Sage/eclib constructor.
No real PARI/Magma agreement control was possible. The freeze remains
`BLOCKED_PRE_EXECUTION`; the remaining launch obligations in
[`CONTINUATION_RESULTS_20261119.md`](CONTINUATION_RESULTS_20261119.md) still
apply. [pcc:unverified]

Cheon, Lee, Hahn, and Chee give a construction for a source curve with
rational two-torsion that produces lifts containing two selected points and
having rank at most two under suitable primality conditions. Their own
factorization forces two nonunit factors in one descent term, so the displayed
construction yields the upper bound two, not the rank at most one needed to
force those two selected points to be dependent. The simultaneous primality
search and all failed candidates must be charged; primality testing alone
does not establish a polynomial search bound. This is a potentially useful
special-family experiment, not a counterexample to the decay heuristic or a
generic prime-order-curve attack. Source: [Cheon et al., *Elliptic Curve
Discrete Logarithms and Wieferich Primes*, section 4](https://citeseerx.ist.psu.edu/document?doi=15735a41b4d124d07ffe3589198cc8e1391b17b7&repid=rep1&type=pdf).

The mathematical question for this lead is whether a public modification can
force rank at most one, or supply a third independently chosen source point,
without embedding an already known source relation. It would need a fresh
prospective protocol, exact reduction and dependence certificates, matched
controls, and full construction costs before any slope claim. No such
modification or empirical result has been established here. [pcc:unverified]

## Exact boundary audit

The follow-up audit is retained in
[`TWO_TORSION_BOUNDARY_REPORT_20261120.md`](TWO_TORSION_BOUNDARY_REPORT_20261120.md)
and its [rendered PDF](TWO_TORSION_BOUNDARY_REPORT_20261120.pdf). It implements
the paper's one-parameter integral family, exactly replays reduction of both
selected points, verifies the published discriminant factorization, and checks
the two named `p=353` parameter values. Pinned PARI/GP 2.17.2 confirms that
`|B_n|`, `F_plus(n)`, and `F_minus(n)` are prime in each fixed row. The two
discriminant factors are coprime. [pcc:unverified]

Consequently, the cited descent expression is exactly `1+2-1=2` on both
published rows. It does not supply the rank-at-most-one certificate needed to
force dependence of the two selected points. The exact factor-difference
boundary is also formalized in Lean: a nonzero first lifted ordinate forces
the two discriminant factors to be distinct. This rules out treating the
paper's three-prime construction itself as the requested nonlinear dependent
anchor construction. It does not rule out actual Mordell--Weil rank one.
[pcc:unverified]

The remaining public, non-circular variants are now precise: make the two
nonunit discriminant factors share a single prime support, obtain a stronger
descent than the displayed bound, or independently lift a third selected
non-torsion source point so that rank at most two forces a selected relation.
None has yet produced a target-bearing relation, and the decay heuristic
therefore remains undisproved. [pcc:unverified]
