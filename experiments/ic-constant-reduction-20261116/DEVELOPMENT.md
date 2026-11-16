# Constant-polynomial SIMD reduction

Requested scope remains specialized native IC arithmetic and algorithm performance.
The vector-query profile assigns57590428exclusive guestIr to table builder/flush/
cached kernel on its single N27 development point; this is an unsigned descriptive
component result, not native latency. [pcc:unverified]

Proposed engineering: five exact (degree,tail) encodings (15,3),(18,9),(21,5),
(24,27),(27,39), guarded before dispatch. Compile-time polynomial data in the
ordinary four-lane PCLMUL kernel removes runtime term loops and shift loads.
Same carryless products and two sparse folds, same first-witness ordering and
query schedule; no default promotion. Other fields retain general dispatch.
The new vector_prepare=3 opt-in reports executed constant-field pair counts.
It deliberately uses ordinary PCLMUL even on VPCLMUL-capable hosts, so the first
comparison must require the same ordinary backend for the dynamic control.

Before timing: portable and actual x86 equivalence checks including exceptional
pairs, cache mismatch, append, reused scratch, zero/short/nonmultiple lengths;
exact complete witness-map comparison at five chunk sizes and five fields;
existing full-walk/scalar checks. Native preparation includes forced ordinary
PCLMUL controls. Freeze source, inputs and a fresh-point protocol before timings.
Do not edit Rust/dependencies while Cargo compiles. Preserve every failed run.

Sources checked: KB source11ec372510e56feb8af143622c2222a8, crypto:docs/ic/
ENGINE_AUDIT_AND_DESIGN.md, published internal-analysis/evidence none/not
superseded; owning primary file read via git show. Reuse SIMD dispatch and field
arithmetic; this report is contextual, not proof of present performance. Atlas
match constant polynomial SIMD field reduction reviewed; no new DLP mechanism
or prior-art absence claim. Owning Simd256 reduction, cached table and oracle
source read. Canonical curve/volcano/isogeny-route graphs have no changed facts.

Predecessor profile: ../ic-vector-query-20261116/REPORT-profile001.md.
No arithmetic performance result for this new source is established yet.
