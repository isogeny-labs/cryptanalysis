//! Technique library over the [`sym_ir`](crate::cryptanalysis::sym_ir)
//! cipher IR (plan `docs/plans/2026-11-21-generic-symmetric-cryptanalysis.md`,
//! section 2.2).
//!
//! This module currently declares the work-package 2 techniques only:
//!
//! * [`trails`]: minimum-active-S-box search for differential and linear
//!   trails, by branch and bound, MILP and SAT.
//! * [`integral`]: division-property integral distinguishers.
//!
//! Every technique is a plain function of a
//! [`Primitive`](crate::cryptanalysis::sym_ir::Primitive); numbers they
//! return are `[pcc:unverified]` until the repository gate signs them.

pub mod integral;
pub mod trails;
