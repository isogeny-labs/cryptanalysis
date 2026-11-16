# Adaptive fresh-oracle labels have equal branch-event counts

The checked `adaptive_fresh_event_count_eq` theorem extends the random-label
coupling to a label-dependent next addition. For two injective indexed group
traces, a deterministic chooser may inspect the entire old label tuple and
select a pair of indices. If every candidate output is fresh in both traces,
the count of bijective encodings satisfying any full old-plus-new label event
is equal after summing over selected branches. This retains the actual branch
choice in the count; it is not a fixed-command assumption.

An exhaustive `Z/7Z` control used traces `(1,2)` and `(1,3)`. It selected
addition `(0,1)` when the first observed label was smaller and `(1,1)`
otherwise. Both outputs are fresh in both traces. Across all **5,040**
bijective encodings per trace, each branch occurred **2,520** times, and the
complete histograms of **210** distinct branch-and-label events agreed.
`run.py` saved the histogram; `audit.py` independently enumerated all
encodings and checked it exactly.

This gives a checked adaptive fresh-step component of the generic-group
argument. The next step is an induction that couples successive branch
choices until the first collision, then bounds the collision event. A
coordinate-guided rational-lift search requires a separate model because
its observations include curve coordinates as well as abstract labels.

The formal project pins Lean v4.35.0-rc4 and Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9. `lake build
AdaptiveOracleCoupling` completed 3,140 jobs. The three new `#print axioms`
reports list only standard Lean foundations; the module has no proof
placeholder or custom axiom. `SEAL.sha256` binds the protocol, source,
histogram, independent audit, proof map, and build receipt.
