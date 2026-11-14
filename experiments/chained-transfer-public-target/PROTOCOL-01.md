# Public-target index calculus after the completed genus-three transfer

2026-11-13. Prospective implementation and bounded correctness protocol. Parent:
ready cryptanalysis PR1521, checkpoint1e4f1292, scientific069644bf. This protocol
must be committed, normally published and present in a ready child PR before
new instance generation or solver implementation. No timing experiment or
computational-advantage claim is admitted by this document.

## Question and existing baseline

Can the existing N4/B2 end-to-end relation-matrix/individual-descent solver take
only a public elliptic target, with a checkable bridge to the completed
coordinate transfer and canonical-class norm? The baseline is the original
N4/B2 implementation, not a newly named algorithm. Its historical measurements
are source assertions until their original records, independent verdicts and
accounting boundaries are actually checked. [pcc:unverified]

Primary source review b992d8 retains twelve WHOLE original files at crypto
5c527ee19276d1d9282a9a8884f4f8ec15b2364d, in the genuinely published
69,520-byte archive `chained-transfer-reference/evidence/g3-norm-destination-primary-01`.
The adjacent source catalog pins each file. Original N4/B2 already includes
relation collection, linear algebra, target descent and source verification.
Its `k_true` argument is used only to construct Q inside each IC/rho body;
it is not used by subsequent solving steps. `Kf::new` asserts q mod12=7.
The old q<=11 "pure IC" subgroup-enumeration smokes were withdrawn; preserve
that negative history. Do not call the original N4/B2 solver absent or adopt
its legacy ratios as a new result. [pcc:unverified]

The fixed q5/7/11 forward/norm controls remain immutable. They are not silently
replaced by the following new constructor case or promoted to a performance
panel. Candidate identity remains null until the exact admitted maps and
input curve/subgroup identities exist. [pcc:unverified]

## Frozen P1: public-target plumbing and original arithmetic

1. Use the original `Inst::search(223,1,200000)` constructor, only after the
   protocol is published. A constructor failure is retained; no replacement
   field or seed is selected after observing it. The first case is a bounded
   development fixture, not a held-out performance instance.
2. Copy the original `common.rs`, `ghs.rs`, `ic.rs` and `solver.rs` whole, with
   source hashes and literal derivative diffs. Reuse the original canonical
   Picard engine via its existing normal Rust dependency. Keep the old N4
   study and all old producer/consumer source, manifests, workflow prefixes,
   theorem statements, verifiers and trust files unchanged.
3. Derive public IC and plain-rho functions by replacing ONLY their scalar
   parameter with `target: EP` and removing their target-construction line.
   No relation, LA, descent, random stream or verification body change belongs
   to this plumbing derivative. Retain the original functions as controls.
   Put admission in a separate wrapper. A later algorithm change needs its
   own frozen correction and literal diff.
4. Require exact schema/field/model tags and canonical coordinates. Public
   input contains Q, not k. Reject unknown scalar or witness fields. Construct
   known-answer public Q outside both solving intervals, retain the witness
   separately for the test harness, and never pass it to the public solver.
   Moving target construction changes accounting; it is not an algorithmic gain.
5. Check field modulus with the original irreducibility checker; validate
   nonsingularity and G, prime ell, nonzero G and ellG=O using original engines.
   Independently check short-model coordinates and recovered kG=Q with the
   original producer engine. For #E use the exact Hasse interval: ell divides
   #E, and when the interval contains a unique multiple of ell it determines
   #E. Do not treat a second random annihilated point as a general order proof.
   If uniqueness fails, retain the gap instead of claiming a certificate.
6. Five frozen correctness targets are generated from witness residues
   1,2,17,floor(ell/2),ell-1. Their public encodings go to the actual public
   interface; witness residues stay outside its requests. For each, run the
   legacy and public IC bodies with the same original B2 retry schedule:
   attempts1..6, c=2+0.4*(attempt-1), nfb=ceil(c*sqrt(223)), rows_mult1.2,
   max_desc100000, sge=false, maxw12, lp2=true, verify_rel=true;
   solver seed=100+attempt. Retain EVERY attempt, including wrong answers,
   degenerate denominators and exhaustion. No generic-DLP fallback is allowed
   in IC. Plain rho is an explicitly separate control, never a fallback.
7. Require literal derivative equivalence and independent source verification
   of every reported success. All five public IC solves must succeed within
   the frozen retry cap before P1 is accepted as a complete five-target smoke.
   If any fails, preserve that result and diagnose it; passing plumbing alone
   does not discharge the solver acceptance criterion. No stage ratio is
   computed from these correctness runs.

Public CLI: bounded JSON (<=65536 bytes), one fixed case and at most five
targets; create_new output, no overwrite, exit2 for invalid schema/tag/field,
noncanonical/off-curve point, bad subgroup or unknown scalar/witness input.
Actual process controls must retain exit codes, output absence and unchanged
overwrite bytes. The original plain-rho walk omits negation; it is not the
strongest-reference admission for a future speed claim. [pcc:unverified]

## Frozen P2: completed maps and explicit representation bridges

P2 is additive V2. Never instantiate the old V1 adapter with altered q while
retaining private old `normal6`/origin data; do not relax its exact fixture
admission. Derive and document a versioned constructor using the same original
field, polynomial and Picard engines. Build the actual q223 normal forms and
completed origin fibre afresh; no fitted scalar shift or DLP table.

- Field: record the exact N4 binomial modulus and an explicit isomorphism to
  the producer field. Coefficient reinterpretation requires a checked basis
  identity; otherwise evaluate coefficients through a root of the exact
  modulus. Check basis products, Frobenius and inverse transport.
- Elliptic model: N4 uses y²=v³+a2 v²+a4 v+a6. The source algebra suggests
  X=v+a2/3, Y=y for the short model. Its quartic ordinate convention differs
  from the completed adapter: audit the sign and both infinities through
  the actual common quartic. Prove the polynomial identities and origin
  identification; do not infer the divisor-map sign from equal j-invariants.
- Plane model: compare all fifteen quartic coefficients under the explicit
  Moore coordinate transport and scale. Check actual completed finite,
  ramified, exceptional and infinity fibres. Preserve repeated multiplicity.
- Basepoint: for old/new P0, delta=[P0_new-P0_old]=Exc_new(P0_old).
  The same raw typical/exceptional divisor key in the new representation
  differs by +delta; the SAME actual old class is raw_new-delta. Compute
  delta geometrically using the original Picard law, never fit from labels.
  Check zero, addition and the inverse bridge with distinct actual P0 values.
- Connect the complete coordinate map and canonical-class norm to the public
  solver's transported subgroup, including its actual sign/origin convention.
  Require both [2] compositions, exact odd order and scalar recovery on a
  bounded explicit point/class panel. Exhaustive enumeration at q223 is not
  promised by this protocol; the earlier q5/7/11 exhaustive controls remain.

Before P2 is accepted, give readable proofs and feasible Lean lemmas for the
basepoint translation, affine-shift cancellation in the three-target descent,
and the model polynomial identity. Bind exact declarations through the
unchanged original PCC gate; expose the remaining actual-geometry bridges.
An abstract additive-group lemma alone does not prove the concrete maps.

## Predictions, falsification and custody

H1: the literal public-target derivative preserves the original algorithm
after Q construction. A forbidden body diff, unverified recovered scalar or
failed admission control falsifies that implementation claim.

H2: geometric field/model/basepoint bridges identify the same Picard classes
and preserve the actual odd subgroup. Any polynomial, origin, branch,
multiplicity, group-law or round-trip mismatch rejects that bridge; repair
only after freezing the observed failure and corrected construction.

Alternatives include an API-only accounting change with no algorithmic gain,
an unsupported model/sign convention, a legacy IC failure at the fixed small
case, or a genuine transfer-bridge defect. Keep these explanations separate.

For each bounded local development attempt: freeze sources/commands/inputs and
controls before launch; keep build cache outside raw; use a 900-second process
limit and 2GiB address-space envelope where supported. Run static/unit/proof
checks unfiltered with zero ignored tests. Retain WHOLE raw trees as one
standard tar/XZ, every-member/raw/archive hashes and exact round trip; publish
through the genuine existing artifact workflow when its policy requires it.
Never substitute excerpts, split/prune a capture or change thresholds.

No comparative experiment launches without the original checkpoint gate and
live admitted execution/budget/capacity state. Local routine static/unit/Lean
development does not establish benchmark admission. Future comparisons must
freeze the best verified IC baseline and strongest applicable ECDLP references,
all cold setup/transfer/relations/LA/descent/norm/recovery/verification costs,
memory, reuse policy, isolation and controls. Existing elapsed correctness
times and legacy source tables cannot establish a gain. [pcc:unverified]

## Sources checked and resume

Source catalog `evidence/primary-01/catalog.json`; whole primary archiveb992d8,
actual publication5327f4; canonical norm derivation/proof map in parent1521;
old N4/B2 protocol and README (including q223 failures); original Picard engine.
Current KB tool discovery has no configured KB tool; prior six actual127 CLI
fallback receipts remain in the parent. This is source fallback, not evidence
of novelty or absence. crypto-autoresearcher remains vault8edec422 locked; do
not unlock, print ciphertext, or edit its inaccessible instructions. [pcc:unverified]

Next: normally publish this protocol and open a ready child under1521. Then
implement P1, retain complete successes/failures and independently check them;
advance to P2 and subsequent admitted computational comparisons. Keep root
fixture access and main ledger/signing/conflict/review gates separate.
