# First-hit time and prefix fibers yield an aggregate bound

The checked `aggregate_bucket_bound` theorem combines two earlier results:
an exact stopping partition of a finite execution space and the weighted
one-step inequality for each visible-prefix bucket. If `N ≤ m`, each stage
has at most `m` old forms, every designated first hit lies in its eligible
next-candidate set, and the execution counts equal the sums of their
visible-prefix encoding fibers, then

`(q − m²) · (first-hit executions through N stages) ≤ m² · (initial executions)`.

The theorem derives the live-mass flow equation from each execution's
first-hit time. Its bucket mass identities are explicit hypotheses. They
are the remaining runtime connection for an arbitrary adaptive program;
the result does not infer them from the program syntax alone.

A frozen adaptive Z/7 control tested that connection. It starts from
`G,Q=wG` with every `w≠1` and every bijective group encoding. The first
command chooses `G+Q` or `G−Q` from the two visible labels. The next two
commands append `G−G` twice; the final command appends `G+G`, allowing the
third-stage prefix to contain a known repeated form. Every execution stops
at its first informative equality.

| Stage | Old forms | Visible-prefix buckets | Live pairs | First hits | Continuing pairs | Buckets with a known repeat |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 2 | 42 | 30,240 | 7,560 | 22,680 | 0 |
| 1 | 3 | 210 | 22,680 | 2,520 | 20,160 | 0 |
| 2 | 4 | 840 | 20,160 | 0 | 20,160 | 0 |
| 3 | 5 | 840 | 20,160 | 7,560 | 12,600 | 840 |

The independent audit reconstructed every bucket from the affine forms,
visible label pattern, eligible scalar set, and factorial encoding weight.
All 840 repeated-prefix buckets have six encodings per eligible scalar.
Across the four stages, 17,640 first hits plus 12,600 continuing pairs
account for all 30,240 initial pairs. The stage-0 local factor `q−n²=3`
is positive; the later local factors and the global `q−m²` factor truncate
to zero in this field. The control establishes the partition identities
for this exact program and input law, not a large-field rate.

Protocol v1 ended immediately after creating the repeat, so it could not
check a prefix containing that repeat. Its source, protocol, raw rows, and
result are retained as pilot artifacts. Protocol v2 added the final
command before measurement and binds the reported control.

The next formal step is to derive the two bucket mass identities for every
finite label-adaptive add/sub program from `runGroup`,
`formsFromTranscript`, and the uniform bijective-encoding law. The initial
`G=Q` case can then be charged separately to the complete one-target
bound. A coordinate-guided xedni construction needs a separate observation
model.
