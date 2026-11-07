# Continuation: reuse pair-index collisions before base-log preparation

2026-10-30. Fixed before collision enumeration; exploratory on the existing
four frozen fields, not a fresh-target holdout. Preserve all prior evidence.

## Objective and controls

The goal is useful Hecke constraints or target decompositions beyond what
same-budget generic arithmetic supplies. The prior scalar-only control uses
only multipliers2,3. Strengthen it by reusing a computation the candidate
already requires: its signed pair index. This tests whether its collisions
provide additional base-log relations without additional curve sums.

For each original field use the same normalized base, generator, public
target and subgroup. Enumerate every unordered pair, with replacement, of
the signed base plus zero in the same order as the original target_query.
Retain the first expression for each pair-sum point. On a collision, subtract
the two expressions; discard identically zero coefficient vectors after
negation folding, normalize nonzero rows modulo r and retain a rank basis
with explicit four-point witnesses. Continue enumerating every pair even
after rank saturates. Hash the complete stream and the complete pair point
set; the large-f6 point-set digest must match the earlier arity receipt.

Compare original Hecke+scalar rows; generic pair-collision rows; and their
union, all on the same folded columns. Independently check ranks and every
retained group relation. Recompute all base labels using only the free logs
of each system, with the same reusable sqrt(r)-size BSGS table as before.
Verify every label against the independently obtained prior labels and with
the separate short-model group law. Then materialize labels in the already
built pair index and repeat the same256-offset target query, preserving its
prior success or bounded failure. Do not count a generic fallback as IC success.

## Accounting and limits

One pair index per field. Count every curve addition in index construction,
each generic log query, verification and target query separately. Capture
relation-harvest bookkeeping and LA time as exploratory diagnostics. Reuse
means no additional curve sums; coefficient tracking, memory and LA are not
free and must not be described as zero-cost. There is no qualified timing
ratio or matched-rho claim. A reduction in required generic queries is a
stage result within this declared pipeline, not a full-pipeline speedup.

Cap600 seconds per field and2400 seconds total; one CPU process; same15GiB
limit and required checkpoint rules as before. Keep unique run outputs,
source/input hashes and unsuccessful attempts. Unit tests must reject an
invalid collision witness and distinguish zero identities from independent
relations. The independent verifier uses short-Weierstrass arithmetic and
a separate elimination implementation. All four fixed cells must run; do
not select a favorable one for the headline.

If pair reuse closes a generic system, explicitly correct the interpretation
of the earlier scalar-only comparison while preserving its measured values.
If Hecke still adds information, quantify its marginal rank over this
stronger generic control. A same-total-budget advantage remains unresolved
until geometric arithmetic, bookkeeping and LA are fully priced against a
strong generic collector on an accepted benchmark host. No arbitrary generic
lower bound follows from testing these particular collectors.
