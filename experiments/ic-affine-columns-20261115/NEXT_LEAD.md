# Next complete-cost optimization candidate

The current source follow-up removes row transposition in affine queries; it
must be measured before inferring any speed benefit. Independently, the current
MITM constructor remains a concrete native specialization opportunity.

Owning sources inspected: PairTable::build_negation_folded in
suite/src/cryptanalysis/ic_boundary.rs performs g.add for every selected signed
pair; FastCurve::add_pairwise in suite/src/cryptanalysis/koblitz_fast.rs already
uses one Montgomery batch inversion for an entire slice, with exceptional pairs
handled by the existing exact add. It is not used by this generic pair-table
constructor. No new mathematical mechanism is asserted.

Hypothesis: build the binary negation-folded table with bounded ordered chunks
of pairwise additions, preserving the exact loop order and first witness for
each abscissa key. Chunking bounds memory; every preparation allocation, inversion,
map operation and exceptional addition belongs to cold setup. Price complete
native preparation instead of charging both batch nanoseconds and hypothetical
individual inversions. Expose it opt-in and preserve the generic oracle.

Required checks: compare every table witness/probe with the existing constructor,
identity/equal-x/doubling/inverse inputs, partial final chunk and empty bases;
complete registered target domains; scalar and deterministic collection counts.
A fresh binary/source receipt and fresh frozen targets are required before a
full setup/query/collection/matrix/verification comparison with current MITM and
the best measured affine arm. This is unimplemented and unmeasured; retain all
older negative, capped and noisy evidence. No host or PCC qualification follows.
