//! # Prime-field hyperelliptic curves and Jacobian arithmetic.
//!
//! Companion to [`crate::binary_ecc::hyperelliptic`] for **odd
//! characteristic** (`p ≠ 2`).  Provides:
//!
//! - [`fp_poly::FpPoly`] — polynomial ring `F_p[x]` with the
//!   Euclidean machinery (add / mul / divrem / gcd / ext_gcd /
//!   evaluation / monic).
//! - [`curve::HyperellipticCurveP`] — `C : y² = f(x)` over a checked odd
//!   modulus, with `f` monic and squarefree of exact degree `2g+1`. The
//!   one-infinity backend is deterministic through 64 bits and retains a
//!   cached probable-prime screen for wider moduli.
//! - [`curve::MumfordDivisorP`] — reduced Mumford rep `(u, v)` with
//!   `u | v² − f`.
//! - [`balanced::SplitHyperellipticCurveP`] and
//!   [`balanced::BalancedDivisorP`] — a separate genus-two implementation
//!   for monic squarefree sextics with two rational infinity points.  Its
//!   canonical `(u, v, n_plus)` representation retains both infinity
//!   branches and must not be interchanged with the one-infinity pair. This
//!   backend accepts only primes proved by the complete word-sized test or
//!   the strict Sorenson--Webster `psi_13` bound.
//! - **Cantor's algorithm**, char-`p` form: composition `gcd(u_1,
//!   u_2) → d_1`, `gcd(d_1, v_1 + v_2) → d`, combine; reduce by
//!   `u_new = (f − v²)/u` until `deg u ≤ g`.  The "no `h(x)`"
//!   simplification — char-`p` Mumford reps don't carry an
//!   `h(x) y` term.
//! - [`curve::brute_force_jac_order`] — exhaustive `#Jac(C)(F_p)`
//!   via Mumford-rep enumeration.  Toy-only (`p ≤ a few hundred`).
//! - [`curve::brute_force_jac_order_via_lpoly`] — alternative
//!   counting via `#C(F_p)` and `#C(F_{p²})`, then the genus-2
//!   `L`-polynomial relation `#Jac = L(1)`.  Its present exhaustive
//!   `F_{p²}` point counter is `O(p²)`, versus `O(p⁴)` for the
//!   naive Mumford-pair enumerator.
//!
//! This module is the substrate for
//! [`crate::cryptanalysis::p256_isogeny_cover`] — the Phase-1
//! existence indicator for the Kunzweiler–Pope `(N, N)`-split-
//! cover question applied to the Weil restriction of an `F_p`
//! elliptic curve.
//!
//! ## Scope
//!
//! - [`curve`] supports one rational point at infinity only and rejects
//!   even-degree input.  [`balanced`] separately supports monic split sextics
//!   of genus two over checked odd prime fields.  Extension fields,
//!   non-split infinity, and higher-genus even-degree models remain
//!   unsupported.
//! - The checked Mumford arithmetic is genus-generic; exhaustive order
//!   enumeration and the `L`-polynomial counters remain genus-2 utilities.
//! - Counting and enumeration routines are toy-only (`O(p^c)` for small
//!   `c`, appropriate for `p ≤ ~10^3`). Ordinary checked group operations do
//!   not enumerate the field.

pub mod balanced;
pub mod cover_transfer;
pub mod curve;
pub mod fp2;
pub mod fp_poly;
pub mod model_transfer;
pub mod primality;

pub use balanced::{
    BalancedDivisorP, BalancedHyperellipticError, SplitHyperellipticCurveP,
    MAX_BALANCED_ENUMERATION_PRIME,
};
pub use cover_transfer::{
    PrimeEllipticPointP, PrimePullPushCertificate, PrimePushPullCertificate,
    PrimeQuadraticCoverError, PrimeQuadraticCoverP, PrimeSubgroupTransferStatus,
};
pub use curve::{
    brute_force_jac_order, brute_force_jac_order_via_lpoly, count_points, count_points_fp2,
    fast_frob_ab, fast_point_counts, frob_ab_and_jac, jac_order_via_lpoly, FrobABForJac,
    HyperellipticCurveP, MumfordDivisorP, PrimeHyperellipticError, MAX_CHECKED_PRIME_BITS,
    MAX_POINT_ENUMERATION_PRIME, MAX_QUADRATIC_POINT_COUNT_PRIME,
};
pub use fp2::{enumerate_fp2, Fp2, Fp2ContextError, Fp2Ctx, MAX_FP2_MODULUS};
pub use fp_poly::FpPoly;
pub use model_transfer::{
    PrimeMontgomeryAdapterError, PrimeMontgomeryAdapterP, PrimeMontgomeryPointP,
    PrimeProjectivePointP,
};
pub use primality::{
    prime_proof_evidence, prime_proof_status, PrimeProofEvidence, PrimeProofStatus,
    DETERMINISTIC_U64_BASES, PRIME_BASES_THROUGH_53, PSI13_EXCLUSIVE_BOUND_DECIMAL,
    PSI13_THEOREM_REFERENCE, U64_EXCLUSIVE_BOUND_DECIMAL,
};
