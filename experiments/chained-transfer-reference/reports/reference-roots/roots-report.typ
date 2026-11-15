#set page(paper:"a4",margin:16mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= Canonical roots without eager quadratic-field enumeration
2026-11-12 · CT26 · exact accepted models · scientific standing unsigned

The Richelot reference evaluator now defers its root table until a degree2
support actually needs it. Its typed input is a validated polynomial over
Fp, so every queried discriminant is real. Enumerating the two coordinate
axes preserves the original exhaustive table's first root for every query.
The original builder remains a test reference; no field, polynomial,
Cantor, correspondence or infinity formula is replaced. Native control01
and strictClippy pass, PCC3f015c. Complete changed guard02 now passes,
PCC3c6362.
[pcc:unverified]

#image("roots.svg",width:100%)

== Why the first root is unchanged
Write Fp²=Fp[s]/(s²-n), n nonsquare and p odd. The square of a+b s has
second coefficient2ab. A real square therefore forces a=0 or b=0. Filtering
the old lexicographic enumeration to those axes gives all(0,b) first,
then(a,0) for a=1..p-1. This is exactly the new order, with the origin once.
Every matching candidate survives, so the first matching root is unchanged.
[pcc:unverified]

RootTable.first_match_filter/PCC1da835 proves that ordered-search
implication with an explicit match-implies-keep hypothesis. The local
kernel/axiom gate audits one theorem, propext only, zero trusted native.
Actual finite fields, basis/no-zero-divisors and concrete grid equality
remain written bridges. ROOT_TABLE.md/PCC4ce55c is identical to upstream
ROOT_TABLE_PROOF.md/718425. Formalization is partial. [pcc:unverified]

== Static enumeration counts, not timings
#table(columns:3,stroke:0.5pt,align:(left,right,right),
 [Prime],[Original candidates],[Axis candidates],
 [17],[289],[33],
 [101],[10,201],[201],
)

The counts are p² and2p-1 candidate squares. The restricted table has p
real keys, while the original table also stores nonreal square keys that
this typed API never queries. This does not implement a general Fp²
square-root table or establish a wall-clock, memory or DLP speed ratio.
[pcc:unverified]

#pagebreak()
= Whole-map controls and evidence boundaries

== Lazy initialization is part of the tested behavior
The immutable map owns std::sync::OnceLock. Construction leaves it empty.
Degree0/1 returns and zero/unsupported-degree errors occur before its
initializer. The first degree2 pointwise or fallback call initializes the
restricted table; later calls reuse it. The two returned polynomial roots
have the same order and sign as before, including a repeated zero root.
All original pointwise and geometric fallback formulas remain.
[pcc:unverified]

Native01 compares EVERY base discriminant at17/101 against the original
exhaustive p² builder. It checks exact canonical first roots, both returned
polynomial zeros, every stored key/root and low-degree/error cache state.
Three source01 snapshots and their hash manifest are frozen, PCC3f015c.
The accepted field/model scope is unchanged; no larger-prime catalog
acceptance is inferred from the general written argument. [pcc:unverified]

== Complete graph acceptance
The full R0/R1/R2 graph tests use separate fresh production/reference
instances. Each closed production call must leave its own cache empty;
actual pointwise quadratic references initialize theirs. Both directions
retain complete domains, exact output equality, dual2, bijections, paired
additions, descent, wrong-model rejection and geometric boundaries.
All Phi/Psi/generic/naive/source controls remain in the whole guard.
Complete changed check.sh02 passes25native/82reference unit plus five
integrations, one pre-existing ignored benchmark, all guards/fmt/strictClippy.
All six domains have239 lower-degree/12078 quadratic/zero fallback calls;
every no-cache/reference-initialization assertion passes. Exact final three
hashes match source01. Complete100487-byte raw→standard-xz11812bytes,
raw/archive SHA256 and exact roundtrip are pinned by PCC3c6362. [pcc:unverified]

== Negative findings and retained failures
The initial proposal to remove lower-degree Richelot root finding was a
recorded no-op: those fibre and infinity formulas are already algebraic.
Upstream source audit325922 retains the exact old sources. This work instead
changes table setup and queried-key scope. The first Lean parse used reserved
token matches as a binder; source/error01 are retained, corrected hit in02
passes. No test, validator, frozen subject or ledger history is weakened.
[pcc:unverified]

== Limits and next step
No stage, pipeline, index-calculus or rho advantage is measured. Matched
cold protocols must include constructor/setup, conversion, transfer, solver,
recovery and verified answers after S3/livebudget admission. Current locked
atlas, frozen-ledger forks and parent CI findings remain separate blockers.
Parent1496 exact65a focusedCI43136703928 succeeds25/81+five; its full
archive/PCCe2187d remains separate. Own final-head CI/review and bottom-up merge
requirements remain owed.
[pcc:unverified]

Next CT27 prepares arbitrary balanced-class replay with the existing second
Cantor engine, including the explicit infinity correction missing from the
fixed49-class corpora. It is prospective. Independent isogeny evaluation/
kernel membership, larger-prime catalog support and full geometric Lean
remain open. Reproduce using source01, the original exhaustive test builder,
ROOT_TABLE.md and the ordinary check.sh; raw correctness receipts are in
`evidence/ct26-*`. [pcc:unverified]
