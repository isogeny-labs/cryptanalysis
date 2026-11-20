# prime-field-m3-cdclt (Lead 2B)

Compact binary-selector arity-three disjoint-window chained-S3 CDCL(`F_p`) propagator.

## Status (2026-11-20)

Modules `cdclt`, `curve`, `field`, `proof`, `selector` are present, but **do not yet compile together**:
`proof.rs` was authored against a different `FpOps`/`ProofSink`/`CurveFp` surface than `field.rs`/`curve.rs`/`cdclt.rs` expose (14 compile errors: associated `FpOps::{add,sub,mul,neg}_mod`, missing `PointFp::INFINITY`, `CurveFp::is_on_curve`, `ProofSink::emit_*`, unresolved `curve::semaev_s3`).

Next actions: unify the arithmetic/API surface, add `lib` unit tests + `m3-cdclt-screen` s=5..12 panel, then mark PR ready.
