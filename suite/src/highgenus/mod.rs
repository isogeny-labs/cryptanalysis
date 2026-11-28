//! # Higher-genus Jacobians: genus-generic arithmetic, Pollard rho and
//! index calculus for hyperelliptic and non-hyperelliptic curves.
//!
//! Scope (owner request, 2026-11-21): genus `5 ..= 131`, curves over a
//! prime field `F_p` with `p < 2^32`, in two model families that share one
//! polynomial substrate:
//!
//! | model | curve | group law | genera |
//! |:--|:--|:--|:--|
//! | [`cantor`] | hyperelliptic `y² = f(x)`, `deg f = 2g+1`, odd `p` | Mumford pairs, Cantor composition and reduction | every `g ≥ 1` |
//! | [`kummer`] | superelliptic one-point model `y^m = ∏ f_i(x)^{e_i}`, `p ∤ m`, `gcd(m, deg) = 1` | ideals of the maximal order (Hermite form over `F_p[x]`), Arita-style reduction by the minimal pole-order element | every `g ≥ 1`; `m ≥ 3` is non-hyperelliptic for `g ≥ 5` (Castelnuovo–Severi) |
//!
//! The canonical representative of a divisor class is the unique effective
//! divisor of minimal degree in `[D] + n·∞` (a complete linear system of
//! dimension ≥ 1 always has a member through `∞`, so the minimal-degree
//! member is unique); both engines return it, so class equality is
//! structural equality.
//!
//! On top of the group law:
//!
//! - [`rho`]: distinguished-point `r`-adding Pollard rho with the negation
//!   map, over any [`JacobianGroup`], returning only a verified logarithm;
//! - [`ic`]: Enge–Gaudry large-genus index calculus with a factor base of
//!   places of degree `≤ B`, relation collection by a random walk, the
//!   subgroup order from the relation lattice when it is unknown, and the
//!   logarithm from a sparse-then-dense solve modulo the prime subgroup
//!   order; every logarithm is verified by a scalar multiplication;
//! - [`jacobi`]: exact `#Jac(F_p)` for the Jacobi-sum families
//!   `y^m = x^n + a` (`p ≡ 1 mod mn`, `gcd(m,n)=1`) and
//!   `y^m = x^a (1−x)^b` (`p ≡ 1 mod m`), which supply planted instances
//!   with a known prime-order subgroup at every genus;
//! - [`instances`]: planted `D₂ = k·D₁` instances at a requested genus.
//!
//! Costs are counted in group operations and field multiplications where
//! the engines count them; this module measures and verifies, it claims
//! no speed-up. Everything here is `[pcc:unverified]` until a claim record
//! says otherwise.

pub mod cantor;
pub mod ext;
pub mod fp;
pub mod ic;
pub mod instances;
pub mod jacobi;
pub mod kummer;
pub mod plane_trigonal;
pub mod poly;
pub mod rho;

use std::fmt;

/// Errors shared by the higher-genus engines.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum HgError {
    /// The modulus is not a prime below `2^32` (or is `2` where an odd prime is required).
    BadPrime(u64),
    /// A curve-definition check failed; the string names the check.
    BadCurve(&'static str),
    /// A divisor / ideal is not a valid reduced element of the given curve.
    BadDivisor(&'static str),
    /// A parameter is out of the supported range.
    Unsupported(&'static str),
    /// An algorithm ran out of its budget without an answer.
    Exhausted(&'static str),
}

impl fmt::Display for HgError {
    fn fmt(&self, out: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::BadPrime(p) => write!(out, "{p} is not a prime below 2^32 usable here"),
            Self::BadCurve(what) => write!(out, "invalid curve: {what}"),
            Self::BadDivisor(what) => write!(out, "invalid divisor: {what}"),
            Self::Unsupported(what) => write!(out, "unsupported: {what}"),
            Self::Exhausted(what) => write!(out, "budget exhausted: {what}"),
        }
    }
}

impl std::error::Error for HgError {}

/// A finite abelian group with the operations the generic solvers need.
///
/// Elements are canonical (structural equality is class equality), so a
/// `Hash`/`Eq` key can be derived from them; `negation_class_key` returns
/// the same key for `x` and `−x` so a walk can run on the quotient by `±1`.
pub trait JacobianGroup {
    type Elem: Clone + Eq + std::hash::Hash + fmt::Debug;

    fn identity(&self) -> Self::Elem;
    fn add(&self, a: &Self::Elem, b: &Self::Elem) -> Self::Elem;
    fn neg(&self, a: &Self::Elem) -> Self::Elem;
    fn double(&self, a: &Self::Elem) -> Self::Elem {
        self.add(a, a)
    }
    fn is_identity(&self, a: &Self::Elem) -> bool {
        *a == self.identity()
    }
    /// A 64-bit hash of the element, used for walk branching and
    /// distinguished-point tests. Must be a function of the element only.
    fn hash64(&self, a: &Self::Elem) -> u64;
    /// A hash shared by `a` and `−a` (for the negation map).
    fn negation_class_key(&self, a: &Self::Elem) -> u64 {
        let h = self.hash64(a);
        let hn = self.hash64(&self.neg(a));
        h ^ hn
    }
    /// Whether `a` is the lexicographically smaller of `{a, −a}` under
    /// some fixed total order; used to pick the negation-class representative.
    fn is_negation_representative(&self, a: &Self::Elem) -> bool;
    /// Number of group operations (adds + doubles) performed so far.
    fn group_ops(&self) -> u64;

    /// Left-to-right double-and-add; counts as `bits + weight` group ops.
    fn scalar_mul(&self, k: &num_bigint::BigUint, a: &Self::Elem) -> Self::Elem {
        use num_traits::Zero;
        if k.is_zero() {
            return self.identity();
        }
        let bits = k.bits();
        let mut acc = self.identity();
        let mut started = false;
        for i in (0..bits).rev() {
            if started {
                acc = self.double(&acc);
            }
            if k.bit(i) {
                if started {
                    acc = self.add(&acc, a);
                } else {
                    acc = a.clone();
                    started = true;
                }
            }
        }
        acc
    }
}
