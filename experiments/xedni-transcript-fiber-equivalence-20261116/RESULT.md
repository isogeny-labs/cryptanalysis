# Adaptive transcript fibers equal symbolic fibers

The checked `dlp_labels_iff_symbolic_fiber` theorem gives an exact path
characterization for any finite label-adaptive add/sub program on public
`G,Q=wG`: an encoding produces a complete visible label transcript exactly
when it assigns those labels to the affine forms reconstructed from that
transcript. The proof covers repeated forms and every scalar. Its converse
uses the fact that reconstructed forms preserve the current prefix, so the
observed labels select the same command at each program node.

`actual_fiber_count_eq_symbolic` transports that equivalence to exact
encoding counts. `actual_fiber_partition` shows that, at a fixed scalar,
actual complete-transcript fibers partition all bijective encodings. These
are structural ingredients for the execution-to-bucket identities used by
the preceding aggregate first-hit theorem.

A frozen Z/7 control used the adaptive program from PR #1641 without
stopping early: it starts with `G,Q`, branches to `G+Q` or `G−Q` by the two
seed labels, appends `G−G` twice, and then appends `G+G`. It enumerated all
seven scalars, all 7! bijective encodings, and all 7^6 proposed complete
label tuples. Symbolic fiber counts were computed from the affine forms
selected by each proposed tuple, including tuples reached by no execution.

| Scalar–label cells checked | Positive fibers | Zero fibers | Encoding pairs accounted for | Fiber-count mismatches |
| ---: | ---: | ---: | ---: | ---: |
| 823,543 | 8,820 | 814,723 | 35,280 | 0 |

The independent audit generated every positive fiber by assigning distinct
labels to the distinct group elements in each algebraic branch. Its 8,820
weighted rows agree exactly with the producer's rows and total 35,280.
The deterministic compressed rows, protocol, source, audit, and 3,147-job
Lean build receipt are sealed.

The next formal step is to extract the program prefix at every stage and
apply this full-transcript equivalence to each truncated program. That will
identify stage live and first-hit execution counts with the prefix-fiber
sums in `aggregate_bucket_bound`. The initial informative `G=Q` case and
an explicit output rule remain separate obligations for a complete
success bound. Coordinate-dependent observations require a different
program model and encoding law.
