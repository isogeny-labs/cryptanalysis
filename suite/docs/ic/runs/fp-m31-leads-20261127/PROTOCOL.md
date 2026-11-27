# Actual M31 relation-lead comparison, prospective local protocol

This continues the user's original five-lead request. The previous 56-cell
native auxiliary-IC experiment was only a baseline and did not evaluate the
proposed encodings. Keep that immutable run separate. Field p=2147483647,
curve y^2=x^3+2x+14, scalar modulus N=2147505293, G=(1,814455902).
The user authorized local execution and storage. No qualified speedup,
independent signed verification or new PCC ID is requested or claimed.

## Freeze and controls

Commit this protocol, panel.json, seeds.json and twelve public input files
before solving the panel. The panel helper performs only native fixture
preparation. Seeds, public coordinates, all failures and resource caps are
retained. The canonical experiment-protocol schema/tools could not be read:
GitHub returned INVALID_ARGUMENT, non-UTF-8 response; the local checkout is
unpopulated. This is an explicitly local descriptive protocol, not a claim
to canonical protocol admission. Shared KB tool is unavailable and wrapper
reports no executable; use primary native source inspection.

1. Native finite-control tests cover polynomial construction and exceptional
   addition branches. Do not infer a new theorem from these producer tests.
2. Transport control uses a deliberate failed native invocation followed by
   a successful panel invocation under the same watcher. Failure must not
   silently skip the second process; stdout belongs to separate log files.
3. Every worker gets a 20-second/2-GiB watchdog. Every capped/missing report
   remains an attempted cell. Native solver soft caps may overrun one batch.

## Lead 1: target roots, witnesses and cache (one native process)

Construct a signed Fp2 decomposition with one rational lift and three
non-rational lifts whose contribution T sums to O; verify conjugation,
2T=O, 2R=2A and cofactor h=1 projection natively. This is a correctness
control for salvage, not a relation-generation rate. Retain the actual
coordinate root, extension lifts and group equations.

On rational signed tuples of m=2,3,4,8 distinct interval lifts, compare
balanced-tree local sign recovery with bare-root exhaustive sign search.
Count actual group additions; replay recovered sums. Test paired R,-R
requests against a real x-target cache: one miss, one hit, both replayed.
This cache/sign stage is isolated from F4 and is not an end-to-end speedup.

## Leads 2 and 3: actual polynomial systems (120 processes)

Use the existing native f4_fp engine over Fp. Inputs are the first k=2 or4
rational x-lifts from x=0,1,..., with m=3 or4. Each (k,m) has a planted
finite sum and the two fixed ordinary public targets from the baseline.
Every encoding/schedule receives identical coordinate inputs.

Cross five encodings (monolithic S4/S5, serial S3, balanced S3, partial
S4/S3, explicit guarded x,y,slope equations) with global versus incremental
staged solving. Total 2*k choices *2*m choices *3targets *5encodings *2
schedules =120. Use degree cap8 and one shared 2000-ms engine deadline per
cell. Charge construction separately within the external process budget.
Monolithic construction may cap; record it rather than replacing its arm.
Root splitting uses bounded deterministic native polynomial factoring,
never enumeration of 0..p. Retain original equations when staging bases.

Explicit addition includes guards and branches for identity, inverse pairs,
doubling and distinct-x addition, including canonical infinity coordinates.
Report selector/branch costs. Affine S3 charts may miss cancellation cases:
identify chart coverage and do not call chart-unsatisfiable a proof of no
group decomposition. Exhaustive tiny-domain group enumeration supplies a
separate correctness oracle; it must not be relabeled a Gröbner solve.
Report recovered roots only after original-equation and group-sign replay.

## Lead 4: signed partial relations (one control +24 collection processes)

An explicit outside-point coefficient matrix H is eliminated over N.
Carry original-row weights; verify w^T H=0 and the resulting group equation.
Control: reject the all-positive triangle as a dependency modulo101 and
combine64 synthetic signed partial rows on16 actual outside points. These
planted accepted partials demonstrate cancellation only, never generation
cost or acceptance probability.

For actual generation, sample R=aG+bQ with public SplitMix64 coefficients.
Compare direct full decompositions over a final base with decompositions
over a larger ambient base, retaining rows with one or two outside terms.
Eliminate accepted outside coefficients and locally replay every combined
row. Retain raw hits having three/four outside terms as rejected outcomes.
The final base is the first floor(3B/4) representatives of the ambient base.
Do not call zero outside terms a partial relation. Do not infer uniformity.

Cross bases torus/interval/random, m3/m4, two public targets, full/partial
methods:24 processes. Each has max256 queries and5000-ms native soft cap.
Costs include actual generation/rejections and elimination. If no accepted
partial or full relation exists, its per-accepted cost is undefined, not0.
Only compare identical completed public query prefixes; caps are censored.

## Lead 5: factor-base selection

The torus base uses the existing depth7 fiber and actual rational columns.
Interval and ordinary random subgroup controls have the same column count;
random construction uses a separate frozen base seed and native cofactor
checks. All three use the same direct decomposition backend to isolate
selection in the collection matrix. Record exact coordinates, setup, query
prefixes and yields. The ambient torus is the concrete algebraically
convenient larger-pool candidate, not an assumed cheap partial generator.

Binary trace restrictions and Koblitz orbit gains do not transfer to this
Fp experiment. Frobenius fixes these Fp-rational points, so no nontrivial
orbit compression is claimed. More elaborate prime-field base constraints
and their solver membership circuits remain a separate experiment.

## Analysis and flow

Planned146 processes =120 polynomial cells +24 collection cells +2 native
target/cancellation controls (transport checks and unit tests separate).
Report attempted/completed/capped/invalid/missing counts with no exclusions
based on result. Plot recorded solver work and collection prefixes/yields.
Archive raw records, source revisions, native binaries' hashes, commands,
inputs, errors, resource counters, correctness checks and PDF/report source.
All producer observations remain [pcc:unverified]. No ratio to Pollard rho
is defined for an IC run without recovery; the prior matched references
remain baseline context, not a new comparable end-to-end measurement.
