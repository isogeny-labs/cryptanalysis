# Native qualification and next solver gate

Revision 2, 2026-11-15. Track: algebraic. Current deliverable is a Rust
implementation and development qualification, with no timing comparison.
The earlier Python system/measurements remain historical. Changing languages
and coefficient backends does not itself establish a cost reduction.

## Completed development scope

Compile the five files in cases/ over p=2^255-19, A=486662: two M=1 controls,
one planted and two historical uniform-affine cases at
M=25606137078333158825. The historical sampling seed was 2026111508; these
are public regression fixtures, not fresh beacon challenges or unbiased
held-out performance data. All calculations are on the raw Montgomery curve,
before cofactor clearing and with one torus coset.

The exact-case hashes and qualifier binary digest precede compilation in
qualification-pre-call.json. Compilation writes canonical sparse coefficients
and native Singular source without the historical kind hint or generation
labels. Only afterwards parse known-triples.json and check the witness and
signed group sum. Qualification writes a distinct post-call file and cannot
reuse an existing output directory. A source change builds a new qualifier;
the old copied binary is read-only and retained separately.

Development acceptance: all six library controls, two consumer input controls,
one process-level immutable-manifest regression, every known triple, exact
quadratic degree/count and equality against the three historical coefficient
fixtures. These are producer observations until independently signed.
The optional native backend test checks only the two M=1 basis classifications.
It does not recover roots from a Groebner basis or certify an empty variety.

## Full-M solver pilot: pending, not launchable yet

Question: can native std and subsequent native root recovery find a checked
triple for the frozen full-M input under the registered short resource limit?
A positive control must succeed before any interpretation of the three pilot
cases. Output roots require independent membership, lift, sign and [8] checks.

Proposed limit inherited from the prior route card: five seconds wall per job,
four seconds aggregate CPU, 768 MiB per-process address space, three full-M
cases and two M=1 controls, maximum one concurrent solver, 35 seconds total
trial wall allowance plus separate setup. The development backend test uses a
per-process four-second hard cap; it is not the aggregate-CPU campaign runner.
Implement/validate aggregate accounting and native triangular-root recovery
before launching the campaign. Std(dp), followed by std(lex) when needed;
do not assume FGLM or SlimGB supports the arbitrary-modulus coefficient ring.

Before an EKS launch: register the exact source/image/binary, spec and absolute
deadline, copy and hash an immutable qualifier, fix a finite cost ceiling
including builds/failures/storage, and read live charged/reserved daily and
monthly cost plus pool/quota capacity. Stop new launches while the remaining
allowance is unknown. No allowance is inferred from a historical USD limit.
An EKS native Singular image/command and live cost readback are absent here;
the existing GitHub workflow/image runs ecbench specs. No job was submitted.

Pilot success means at least one returned, checked full-M decomposition within
its frozen budget and all positive/negative controls passing. Unit ideals for
uniform cases remain engine reports unless an independent certificate is
checked. Timeouts/OOMs park the implementation at that budget. Failed controls
invalidate interpretation. See ROUTE_CRITERIA.md for wider rejection rules.

A subsequent yield or scaling campaign must be separately registered with
fresh targets and complete phase costs under crypto/docs/ic/SUCCESS_CRITERIA.md.
The present qualification supplies no samples for its exponent fit.
