# Cost-accounting correction, 2026-10-27

The original archive is frozen. This correction supersedes its statements that
the block benchmark records complete construction costs, including the same
wording in the first publication wrapper and PDF. Numerical records are unchanged.

## Observed implementation boundary

In [benchmark_blocks.py](archive/experiments/ideas/benchmark_blocks.py):

- Lines 121-126 time sampling, solver work, and `scalar_verify()` separately.
  Lines 147-151 add sampler setup and the raw-domain/catalog preparation charged
  by each method. Lines 159-160 sum only those recorded components.
- Lines 127-139 execute outside those timers and counters. They update block
  counters, sort hits, look up and maintain `known`, recover antipodal scalars,
  and construct the transcript. The complete-domain stopping test at line 118
  is outside the component timers too.
- Lines 134-135 recover and verify an antipodal scalar using modular inversion
  and an uncounted `E.mul(recovered, P)`. The archived rows record 353 antipodal
  opportunities per method across eight trials. Neither recovery CPU time nor
  its group operations enter `complete_cpu_s` or `construction_group_ops`.

The trials reached all 33 usable coordinates. That stopping outcome does not
make their partial cost sums complete. Solver-side index recovery and the
separate hit/identity-label checks are counted; collection bookkeeping and
antipodal scalar recovery/verification are excluded. Other uninstrumented
fixture, ambient-relation and harness work is not converted into a measured
component by this correction.

## Effect on interpretation

The README table, timing figure and PDF now label the unchanged numbers as
recorded component sums. Complete construction CPU time, complete construction
group operations, and ratios of complete costs remain unknown. Missing time
is not imputed from counts or assigned zero. The historical transcripts and
correctness evidence remain available; no new scientific run was performed.

A future measurement must freeze its accounting boundary before execution,
time the entire declared collection interval through its stopping condition,
and count every recovery and verification operation, including antipodal
opportunities. Report any excluded fixture/setup and transcript-audit work
separately. This publication correction does not launch that experiment or
change official hypothesis status.

Review source: [PR #1215, comment 4390993815](https://github.com/isogeny-labs/cryptanalysis/pull/1215#discussion_r4390993815).
