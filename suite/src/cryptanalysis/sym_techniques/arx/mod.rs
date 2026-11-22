//! ARX techniques (work package WP4) over [`sym_ir`](crate::cryptanalysis::sym_ir)
//! primitives.
//!
//! * [`diff_linear`]: differential-linear distinguishers, `xdp+` and the
//!   linear correlation of modular addition;
//! * [`pnb`]: the probabilistic-neutral-bits key-recovery framework;
//! * [`rotational`]: rotational and rotational-XOR probability estimation;
//! * [`machine`]: a compiled word-level evaluator (forward and backward) for
//!   key-free ARX primitives, shared by the techniques above and checked
//!   against [`eval_rounds`](crate::cryptanalysis::sym_ir::eval_rounds).
//!
//! Nothing here is a claim about any cipher's security: every number is a
//! measurement or an estimate, labelled as such where it is produced.

pub mod diff_linear;
pub mod machine;
pub mod pnb;
pub mod rotational;

#[cfg(test)]
mod tests;
