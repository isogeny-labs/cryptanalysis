# W33 deferred-source positive screen

Deferring inverse-trace source eligibility in two of the five pair slots
reduced the constructed N131 formula by **8,384 AND gates (10.4%)** and
**25,418 clauses (10.4%)** relative to the exact W33 encoding. The known
five-pair relation assignment still passes all **218,561 clauses** and
**42,735 native XOR rows**. A one-worker 120-second positive search ended
`BOUNDED_UNKNOWN` at its parent wall cap; this screen supplies no SAT-returned
model or solver-speed conclusion.

| Constructed positive stage | Exact W33 | Deferred slots 3 and 4 |
| --- | ---: | ---: |
| AND gates | 80,709 | 72,325 |
| Variables | 125,987 | 116,661 |
| Clauses | 243,979 | 218,561 |
| Native XOR rows | 43,415 | 42,735 |
| XCNF bytes | 7,923,553 | 6,683,815 |
| Positive search | `BOUNDED_UNKNOWN` at 600.065 s | `BOUNDED_UNKNOWN` at 120.072 s |

The two search rows have different frozen caps and establish only their
respective capped outcomes. The deferred run sampled 172,605,440 bytes
combined peak RSS against a 4-GiB limit. The checked Sage build used
13.621 seconds and verified the constructed assignment directly. The
checked-Sage runtime, source/formula/solver hashes, raw stdout and stderr,
and exact cap are in this directory; `python3 verify.py` audits their
consistency. `candidate_id` is null.

The circuit still enforces the target reciprocal, balanced three-plus-two
addition tree, pair-output quadratic, and exact source eligibility in slots
0, 1, and 2. Slots 3 and 4 retain source-mask and pair-output constraints;
their endpoint trace tests would be checked independently for every returned
model. A model failing either test would be excluded by a source-mask cut
before continuing search. The known complete relation satisfies all five
source laws, so this relaxation retains that witness. This is a circuit
implementation observation, not a new mathematical theorem.

The next method gate is a frozen unpinned N41 public-point control for
deferred validity and exact exclusion cuts. A positive SAT-returned model
and independent group replay are required before this circuit family can
advance to an N131 public query. A later N131 relation would need complete
factor-base, rank, target descent, and paired same-point rho accounting to
test the single-target objective.
