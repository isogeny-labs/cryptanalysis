# Arithmetic coverage for exact norm-assisted Jacobian sampling

Prospective protocol, 2026-11-14. Publish this protocol before implementing
the taps. This is bounded native correctness development, with no timing,
operation price, stage improvement or end-to-end advantage claimed.
All observations and proposed acceptance criteria are unsigned.
[pcc:unverified]

## Question and frozen baseline

Can an isolated derivative account for executed field arithmetic throughout
the exact norm-assisted sampling panel, without changing its mathematical
outputs, random draws, decisions, final checks or published engines?
The baseline is consumer commit
`21afb40f425f89774fe3eaf77695f5f30342a186`, with producer
`3d49af7f3d0a28e76b79e4825c9d2324e85853d2` and the immutable
`ci_norm_sampling/reference-01.sha256`: 784 inputs plus the manifest itself.
The existing 86 whole JSON records, all 225 scalar pairs, 1125 triples and
60 paired IC attempts remain the finite acceptance panel. Retain all 15
shared FB30 failures, including the ten wrong tentative scalars rejected
by the unchanged final Picard and independent elliptic checks.
[pcc:unverified]

Native claim 9bc5e6, written claim e7a860, independent replay 333af1 and
source CI 42073d are prior unsigned evidence. The independent replay checked
all 785 inputs and ten ordered native/tee phase pairs; all 17 source
workflows completed, with 327 native records and 60 unique canonical PCC
digests across 62 actual verdict records. This audit does not change their
subjects, signatures, standing or mathematical scope. [pcc:unverified]

## Isolated implementation and custody

Add a separate `arithmetic-audit/` directory containing native Rust tap
support, primitive controls, a native JSON comparator, and thin shell
materialization/build commands. Materialize the original closure from the
two exact Git commits into fresh physical sibling directories outside the
repositories. Verify every original file against the frozen manifest.
Copy that closure into a separate derivative layout, and retain complete
literal patches and before/after hashes for every changed file.
[pcc:unverified]

The derivative may add pure counter hooks and dependencies on a new Rust
tap crate. It may append test-only access to private primitive methods.
It must not change arithmetic expressions, RNG, outputs, existing legacy
counters, solver control flow or acceptance checks. The original and
candidate class-solver bodies remain byte exact. In particular, no phase
hooks go inside either class-solver body: put scope hooks at test call
boundaries. The existing two-substitution sampler provenance check remains
operative. All original source files, verifiers, proof gates, checkpoints,
workflow rules and admission thresholds in the repositories remain intact.
[pcc:unverified]

Use the untouched original FpR body as an additional reference module in
the derivative build, with its origin recorded. Dependencies it shares
with the derivative are disclosed, so this is a primitive comparison,
not an independent replacement for the prior physical replay. No second
full engine build is required solely for this reference. Materialization
must be reproducible from the pinned blobs and literal patches; do not
commit another entire copy of the frozen research tree. [pcc:unverified]

## Coverage and units

Use a deterministic serial thread-local ledger keyed by scope, backend,
modulus and operation. Use checked integer increments; overflow is an
error. Reject or visibly flag work from an unexpected thread. Counter
resets in the original Picard code must not reset the new ledger.
Retain an explicit residual scope instead of dropping unscoped work.
Keep constructor/setup, maps/admission, original/candidate solver calls,
sample comparisons, independent verification and primitive controls
separate where the existing test boundaries permit. [pcc:unverified]

Count executed source-level field arithmetic and modular reductions,
with operation definitions and an exact hook inventory. These are not
hardware instructions: optimization can remove or combine operations.
Keep API-entry diagnostics separate from primitive totals. Do not add
legacy Picard `bump_*` aggregates to the primitive taps or count a logical
extension-field inverse as another base inverse when its implementation
already includes the base inverse. Nested field products and Frobenius
work remain counted at their actual leaves. [pcc:unverified]

Required inventory, with any unsupported executed path causing rejection
or an explicit incomplete result rather than an assumed zero:

- Native `common.rs` Fp arithmetic and inversion, direct modular products
  in exponentiation/primality, and `ic.rs` scalar-field `lm`, `la`, `ls`.
- Cover `diem_quartic.rs` Fq and Montgomery arithmetic; inspect fast
  extension-field paths and report whether they execute.
- Picard private Fq: both `mul` and `mulu`, both `sub` and `sub_nc`,
  addition, negation and the `invu` Euclidean leaf. `inv` delegates to
  `invu`; do not charge two base inverses. Constructor primality trial
  divisions are separate integer work.
- `isogeny_algos::field::Zp` arithmetic, reciprocal reductions and
  constructor/primality modular products; base inversion is counted at
  the delegated `fpm::inv_u64` leaf.
- FpR coefficient products, squares, additions, constant multiplications,
  fold reductions, Frobenius dot products, inverse scaling, and scalar,
  one and modulus construction. Exercise lazy, nonlazy and degree-one
  branches explicitly. Extension API counts remain diagnostics.
- All other executed field backends discovered during this inventory.
  Hashing, allocation, big-integer/exponent bookkeeping and auxiliary
  integer primality work remain explicit unpriced work. [pcc:unverified]

The published panel shares setup between some arms. Scope totals therefore
do not constitute two independently cold pipeline measurements. A later
protocol must execute separate cold arms and freeze online reuse before
pricing, together with strongest matched IC, rho, precomputation-rho and
fixed-base scalar references. Lower old descent counters alone do not
establish a stage improvement. [pcc:unverified]

## Primitive controls and falsification

Implement controls in Rust. Compare derivative results to the untouched
original FpR body over dense, sparse, zero and one inputs. Independently
derive expected source-level counts from the pinned expressions before
interpreting totals. In particular, for degree three over q=223 with
modulus x^3-3 and dense (1,1,1), inspect the expected 11 products/11
additions/5 u128 remainders for multiplication; for squaring inspect
5 products, 3 coefficient squares, 3 constant-two multiplications,
8 additions and 5 remainders. A dense Frobenius dot has 9 products,
9 additions and 3 remainders. These are prospective expectations to
check against the actual source, not established results.
[pcc:unverified]

Exercise degree one, q223 degree six, and a nonlazy degree-two field at
q=9223372036854775783 using x^2+1, subject to the original constructor
accepting it. Inspect the prospective dense nonlazy multiplication
expectation of 5 products/5 additions/14 u128 remainders. Preserve a
constructor rejection or expectation mismatch and correct the derivation
transparently rather than relabeling a failing control as a pass.
Include native, cover, Picard and Zp primitive controls; expose private
Picard primitives only through additive test support. Observe that a
legacy Picard reset leaves the new ledger intact. [pcc:unverified]

Require all 86 original native records to match the frozen baseline after
masking ONLY the already declared ATTEMPT original/candidate phase `wall`
and `stats.wall_total` fields. No counter, failure, tentative answer,
class, call vector, model identity or order may be masked. Emit new census
and primitive-control records under separate prefixes. Keep all raw
records, exits, commands, tool versions, literal diffs and source hashes.
[pcc:unverified]

Run an actual copied-source negative control omitting one coefficient
hook. The analytic primitive control must reject even if algebraic output
is unchanged. Retain the failure and restore the positive derivative
hashes. Do not add a production environment switch that disables taps.
A mismatch or uncovered executed backend rejects complete coverage;
partial coverage is reported as partial and advances to its specific gap.
[pcc:unverified]

## Execution limits and admission

One serial unfiltered derivative sampler unit test; at most 900 seconds
for its build and 900 seconds for its native test, with a 2 GiB native
address-space limit. Primitive controls and copied negative control use
their own retained records and at most 120 seconds native each. Use a
dedicated outside compiler cache. Keep all scientific source/raw data;
only closed derived compiler caches may be reclaimed with a receipt.
Available local disk is approximately 296 MiB at protocol drafting.
If this cannot fit, preserve the exact resource failure and pursue a
smaller development build without weakening the full panel requirement.
[pcc:unverified]

Before an experiment launch, use the original checkpoint mechanism and
gate. Builds and unit checks are development work, not performance data.
No paid cloud build or benchmark is authorized by a guessed budget.
The existing Iso Lab skill requires live budget remainder and capacity;
both are currently unknown. Its fixed failure-diagnosis workflow targets
three old jobs and supplies neither generic admission nor current budget.
The ordinary isolab workflow builds unrelated images. Do not dispatch
either as a substitute benchmark. A later deployment must bind both
actual source commits and a matching tested image. [pcc:unverified]

## Sources checked and remaining obligations

Retain `ct72-arithmetic-literature-01` receipts: research-KB tools are not
loaded, the original status/four distinct query fallbacks and lead-atlas
wrapper exited 127. This is an access limit, not an absence or novelty
result. The crypto-autoresearcher vault remains locked and untouched.
The source inventory pins FpR, field, fpm, cover and Picard files, plus
the original Iso Lab skill, access, cost, harness and workflow documents.
Original native common/ic and sampler call sites are primary sources.
[pcc:unverified]

This instrumentation adds no geometric theorem. Existing 60 conditional
Lean bindings retain their faithful hypotheses and unsigned standing.
Complete global beta coordinates, geometric/formal bridges, prime-field
descent costs, stronger growing-size transfers and admitted computational
advantages remain open. Root regression clock failures, main-ledger
lineage, reviews, signing and merge conflicts retain their existing
problem records and requirements. Continue to the next unblocked task
after recording each positive, negative or incomplete outcome.
[pcc:unverified]
