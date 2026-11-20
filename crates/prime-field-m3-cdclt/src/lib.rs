//! Arity-three disjoint-window chained-S3 prime-field CDCL(Fp) propagator.
#![allow(dead_code)]

pub mod cdclt;
pub mod curve;
pub mod field;
pub mod proof;
pub mod selector;

pub use cdclt::{
    enumerate_all_models_compact_cdclt, CdclOutcome, CdclSolver, CdcltStats, ChainedS3LambdaTheory,
    PreparedChainedS3Setup, ProofEvent, ProofSink, TranscriptProofSink,
};
pub use curve::{
    canonical_ir, canonical_ir_sha256, exhaustive_fp2_models, generate_instance_for_class,
    generate_rung_curve_and_windows, make_development_fixture, sample_random_curve_point,
    validate_instance, CurveFp, M3Instance, PointFp, PointFp2, PreparedTwoWindow, SignedWitness,
    TargetClass,
};
pub use field::{
    is_square_mod, sqrt_mod_canonical, DeterministicRng, FpOps, MontDomain,
};
pub use proof::{
    verify_signed_group_replay, verify_unsat_transcript, ChunkedProofBuffer,
    IndependentFpExplanationChecker, MutationKind, ProofVerifyStats, StreamingDrattChecker,
    VerificationError,
};
pub use selector::{
    sizing_comparison_row, CompactBinarySelector, Lit, SinzOneHotSelector, SizingComparisonRow,
};
