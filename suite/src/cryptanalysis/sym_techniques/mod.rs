//! Technique library over the [`sym_ir`](super::sym_ir) cipher IR
//! (`docs/plans/2026-11-21-generic-symmetric-cryptanalysis.md`, section 2.2).
//!
//! Each submodule is one family of techniques written once against
//! [`Primitive`](super::sym_ir::Primitive) descriptions. WP5 contributes
//! [`hash`].

pub mod hash;
