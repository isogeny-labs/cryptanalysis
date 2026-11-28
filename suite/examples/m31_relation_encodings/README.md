# Bounded prime-field relation encoding comparison

This producer experiment uses the existing native `f4_fp::f4` engine over
the supplied prime field. It does not use binary-field arithmetic or the
binary chain-SAT implementation. It makes no performance or novelty claim.

The example entry point is `../m31_encoding_pilot.rs`:

```
cargo +1.88.0 build --manifest-path suite/Cargo.toml --example m31_encoding_pilot
suite/target/debug/examples/m31_encoding_pilot --input public.json --m 3 \
  --encoding serial --schedule global --budget-ms 2000 --degree 8
```

Input is `{ "p":2147483647, "a":2, "b":14,
"base":[[x,y],...], "target":[x,y] }`. A null target means the identity.
The wrapper also accepts `{ "public":{"p":...,"a":...,"b":...,"Q":[x,y]},
"base":[[x,y],...] }`. No generating scalar is passed to the engine.

All arms constrain each leaf abscissa to the same finite base using
`product(X-base_x)=0`. Polynomial construction reduces leaf powers modulo
these monic domain polynomials in every arm. Domain generators themselves
are retained unreduced. This preprocessing is part of construction time.

* `monolithic`: S3, S4, or S5 at fixed target x. S4 and S5 are actual
  Sylvester resultants, using a division-free subset-determinant recurrence.
* `serial` and `balanced`: simultaneous S3 equations, with unconstrained
  field-valued intermediate abscissae and the specified addition-tree shape.
* `partial`: S4 for m=3 (an intentional duplicate of the monolithic control),
  and S3 plus S4 for m=4. At m=2 it is S3.
* `explicit`: leaf x/y coordinates and complete guarded point-addition
  equations. Five disjoint branches cover left identity (including O+O),
  right identity with finite left, inverse pairs, ordinary doubling, and
  distinct-x addition. Intermediate infinity flags have canonical zero x/y;
  tangent/denominator inverses are enforced in their active branches, and
  inactive slope and inverse variables are zero. No exceptional branch is
  dropped. Its topology is serial; it is not labeled a balanced comparison.

The x-only arms are finite affine charts and reject an identity target at
construction. They may omit decompositions requiring an identity
intermediate in the chosen chart. A refutation therefore concerns the encoded
chart, never general decomposability. The explicit arm supports identity
targets and intermediate identities.

`global` sends all original equations to F4 at once. `staged` uses growing
equation-block prefixes, retaining all original prefix equations and adding
the preceding derived basis. Both share one deadline across all F4 stages
and recovery. Reported degrees are real native F4 step statistics. A
degree-truncated basis is not presented as a complete Gröbner basis.

Root recovery is bounded triangular substitution after F4. It uses finite
variable domains when available and the repository's native Fp univariate
polynomial arithmetic for gcd, modular powering, and a bounded deterministic
linear-factor splitter (shifts 0..63). It never calls `f4_fp::solve`, whose
small-prime implementation scans the whole field. Nontriangular unbounded
variables, node/solution/root caps, and deadlines yield explicit incomplete
outcomes. Finite-domain fallback branches are counted; finding a verified
witness by this pipeline is not described as F4 alone solving the system.

Every recovered assignment is checked against all original equations. Its
leaf coordinates must also produce an exact signed group sum equal to the
public target. At most 16 sign combinations are checked for this independent
validation; this check is not used as the polynomial solver. Test-only native
exhaustive enumeration is kept separate from experimental outputs.

Reports separate construction, the F4 phase, bounded root recovery, and
independent group-validation timings. Group-validation additions are counted.
Every F4 stage reports degree, basis, pair-bound and matrix dimensions. A
flushed JSON preflight is emitted to stderr before construction so an external
watchdog kill retains the cell identity and configured limits; stdout retains
one final report when the process completes.

`numeric_summation_root(p,a,b,xs,budget)` evaluates S2 through S5 directly on
raw field abscissae, without a rational-lift assumption or leaf-domain
reduction, for the separate Fp2 salvage control. It uses the same actual
resultant construction and does not itself claim a rational decomposition.

Construction defaults to a 10-second cooperative cap and a 50,000-term cap.
The frozen run protocol additionally imposes external per-process wall/RSS
limits. Timeout, construction failure, and degree truncation are not proofs
of impossibility. The fixed M31 public panel and orchestration are owned by
the parent task; no benchmarks should be inferred from correctness tests.

## Supplemental up-to-length dispatcher

`--up-to-m` is optional and leaves the default exact-m path intact. In this
mode `--budget-ms` is one total cooperative allowance for public length0/1
checks, construction, all F4 stages, root recovery and group validation
across lengths2..m. It does not renew the allowance at each length. A
candidate verified after that deadline is retained only as a late per-length
diagnostic and is not accepted as the dispatcher's witness.

The public identity is checked at length0 and signed-base membership at
length1. Later lengths use exactly the original leaf domain. Positive
outcomes are `found_shorter` or `found_decomposition`; a shorter witness
is not declared minimal if earlier solving was unresolved. Every nonpositive
outcome is conservatively `incomplete`, with per-length chart scopes,
construction failures, degree truncation, recovery limits and time limits
preserved. No output claims general absence.

Minimal rational decompositions contain no nonempty zero-sum subset, which
explains why checking shorter lengths addresses identity-cancellation
exceptions in affine summation charts. This supplemental dispatcher is
bounded solver coverage, not a general completeness proof. Its F31 controls
include the order-two singleton base: three copies of T sum to T, but an
affine S3 tree cannot represent T+T=O; the dispatcher returns length one.
A second control finds a genuine two-point witness outside the signed base.

This implementation/control supplement does not rerun or modify the frozen
146-cell exact-m experiment, which remains pinned to its original source,
protocol, limits and archived binary hashes.
