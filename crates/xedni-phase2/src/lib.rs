//! Xedni Phase 2 native Rust research & benchmark crate.
//!
//! Evaluates all three surviving geometric and arithmetic escapes from the
//! Phase 1 prime-field Xedni ceiling:
//! 1. [`cayley_bacharach`] (Escape 7A): Cayley-Bacharach 9-point cubic pencils
//!    (`dim ker_Q B(P_1..P_9) = 2`), rational `lambda` chord-tangent specialization,
//!    shared `CoordinateFb` abscissa splitting, and `8..14`-bit non-collinear hit rates.
//! 2. [`nodal_bezout`] (Escape 7B): Singular / nodal degree-`d >= 4` plane Bezout
//!    curves (`g = (d-1)(d-2)/2 - delta <= 2`) across off-base and on-base
//!    `[2]`-multiplicity nodes, including genus-2 hyperelliptic node-projection
//!    and Mumford Jacobian kernel LLL on `(d=4, delta=1, s=11 => g=2, r=12)`.
//! 3. [`l4_selector`] (Escape 7C / `CH-L4` `L4-check F1`): Scalar-blind public
//!    small-height lift selector (`NaiveBox`, `Pgl3Lll`, `MultiShiftKummerTorsion`),
//!    `8..12`-bit conditioned vs unconditioned canonical height & `rho_G` separation,
//!    and `24..28`-bit `r = 7..9` height scaling vs Theorem X / JKSST thresholds.

pub mod cayley_bacharach;
pub mod field_ec;
pub mod l4_selector;
pub mod linalg_lll;
pub mod nodal_bezout;
pub mod plane_cubic;
