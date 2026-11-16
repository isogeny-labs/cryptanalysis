# Adaptive transcript fiber proof map

Lean 4 v4.35.0-rc4; Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9.

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Reconstructed final forms preserve the current node's original prefix | `formsFromTranscript_prefix` | Finite typed adaptive `Program`, prescribed complete labels, current affine forms |
| Symbolic label assignment forces the actual adaptive path | `labels_of_symbolic_fiber` | Field, group/module, bijective encoding, current point/form evaluation invariant, prescribed complete labels |
| Actual and symbolic label predicates are equivalent | `labels_iff_symbolic_fiber` | Same hypotheses; both directions |
| Public `G,Q=wG` specialization | `dlp_labels_iff_symbolic_fiber` | Field, group/module, finite `Program L 2 m`, bijective encoding, scalar and complete labels |
| Actual and symbolic encoding fibers have equal cardinality | `actual_fiber_count_eq_symbolic` | Finite group and label domains; current point/form invariant |
| Actual complete label fibers partition all encodings at fixed scalar | `actual_fiber_partition` | Finite group and label domains; any finite typed program and current points |

`actualFiberCount`, `symbolicFiberCount`, and `encodingCount` define the
finite cardinalities. The path-equivalence theorem has no collision-free
condition: a known repeated form simply gets its repeated label. The
full transcript is treated as a proposed label tuple in the converse;
that tuple controls each successive command by its prefix.

The still-open bridge to `aggregate_bucket_bound` is stage extraction:
for each stage, construct a typed prefix program, identify its actual
labels and reconstructed forms with that stage's bucket, and establish the
live/first-hit predicates correspond to eligibility and the new-root set.
The Z/7 census checks the full-transcript fiber identity for a fixed
program; it does not substitute for that universal stage construction.

`lake build TranscriptFiberEquivalence` completed 3,147 jobs. All nine
new `#print axioms` receipts contain only `propext`,
`Classical.choice`, and `Quot.sound` where applicable. The source has no
placeholder, custom research axiom, or native evaluation. `lean4checker
--fresh` is unavailable on this host.
