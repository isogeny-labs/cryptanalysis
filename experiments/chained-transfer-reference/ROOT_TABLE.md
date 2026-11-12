# CT26: canonical roots from a lazy coordinate-axis table

Scientific standing unsigned. This proves canonical root selection for
validated base-field quadratic support. Native canonical control01 passes
at17/101,consumer3f015c. Whole-map acceptance belongs to the living CT26
checkpoint;no performance result is inferred from this proof.
[pcc:unverified]

Let p be odd and K=Fp[s]/(s²-n),where n is a nonsquare. The old ordered
candidate sequence is every(a,b) in lexicographic order,0≤a,b<p;its table
stores the first candidate with each square key. The typed root API is
only called on validated monic degree2 support over Fp,so its discriminant
lies in the real subfield. No arbitrary K-input square-root API is claimed.
[pcc:unverified]

The square of a+b*s is (a²+n*b²)+(2ab)*s. By the uniqueness of the basis
and 2 invertible,an element whose square is real has ab=0,hence a=0 or
b=0. The parent DirectNorms.even_support_zero_factor expresses exactly
this zero-factor implication with explicit inverse2/domain hypotheses.
Thus every candidate matching a queried real discriminant is on an axis.
[pcc:unverified]

Filtering the old sequence to a0 or b0 gives,IN ORDER,all(0,b) for b0..p-1,
then(a,0) for a1..p-1. Candidate enumeration is exactly that sequence:
the origin occurs once. There are2p-1 candidate squares. Removing elements
that cannot match cannot change the first matching candidate. The Lean
RootTable.first_match_filter is a faithful generic statement of this
ordered-search implication,with explicit match-implies-keep hypothesis.
Its exact statement is bound by theorem PCC1da835;the kernel/axiom gate
checks one theorem with propext only and zero trusted native. Actual finite
fields/basis and the concrete grid/filter equality remain written bridges;
the formalization is partial. [pcc:unverified]

Every d∈Fp has a square root in Fp². Choose a root r in the algebraic
closure. Frobenius permutes the roots r,-r of X²-d,so r^p=±r and
r^(p²)=r. The root is therefore in Fp²,including d0. The nonsquare
quadratic presentation K is that field. Thus the restricted table has
exactly p real keys. [pcc:unverified] For d0 both returned quadratic roots
coincide,just as before. The same canonical first root yields the identical
ordered pair(-a±sqrt(discriminant))/2 and the same downstream pointwise map.

std::sync::OnceLock owns the immutable table per map. Construction does
not enumerate roots or allocate the BTreeMap. Degree0/1 returns and zero/
unsupported-degree errors occur before get_or_init. The first actual degree2
reference/fallback call initializes the table;all later calls share it.
All existing field,polynomial,Cantor,correspondence,infinity and fallback
formulas are unchanged. Closed-path no-initialization remains an actual
whole-graph acceptance obligation,not a consequence asserted from the cache
API alone. Existing geometric boundary/fallback behavior remains in scope.
[pcc:unverified]

The old p² builder remains byte-for-byte as the TEST reference. Native01
compares canonical roots for EVERY real discriminant at17/101,checks both
polynomial roots really vanish,all stored keys/roots,zero/repeated roots,
and low-degree/error cache behavior. Three exact source01 snapshots pin
this result. The enhanced complete R0/R1/R2 graph tests use distinct fresh
production/reference maps to assert every closed call leaves its own cache
empty while actual pointwise quadratic calls initialize theirs. Their actual full
result is recorded in the living checkpoint;do not infer it from the small
control. [pcc:unverified]

Static candidate counts and table cardinalities are not wall-clock ratios.
The broader Richelot constructor and DLP pipeline include other costs.
No stage,pipeline,index-calculus or rho advantage is measured;matched cold
protocols remain required after S3/livebudget admission. Large-field/catalog
support and independent isogeny-map/kernel-membership replay remain open.
[pcc:unverified]

A first Lean parse attempt used reserved token matches as a binder;source/
error01 are preserved. Binder hit in02 compiles with propext only. This source/error custody
is retained with the theorem gate and exact source snapshots. No old
proof or frozen statement is edited and no gate is weakened.

[pcc:unverified]