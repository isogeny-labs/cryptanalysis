//! Generic symmetric-cryptanalysis techniques over the
//! [`sym_ir`](super::sym_ir) cipher IR (work package WP3 of
//! `docs/plans/2026-11-21-generic-symmetric-cryptanalysis.md`).
//!
//! Each technique here is a plain function of a
//! [`Primitive`](super::sym_ir::Primitive); none reads a cipher name.
//! Results are structural statements about a description, not claims about
//! the cipher's security; every number they produce is `[pcc:unverified]`
//! until the repository's PCC gate signs it.

pub mod impossible;
pub mod mitm;
pub mod zero_correlation;
