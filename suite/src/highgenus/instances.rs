//! Planted DLP instances at a requested genus, with a known prime
//! subgroup order, on both engines.
//!
//! Known-order curves come from the Jacobi-sum families ([`super::jacobi`]):
//!
//! - hyperelliptic, any genus `g`: `y² = x^{2g+1} + a` over `p ≡ 1 (mod 2(2g+1))`;
//! - non-hyperelliptic, `g = (m−1)(n−1)/2` with `gcd(m,n) = 1`, `m ≥ 3`:
//!   `y^m = x^n + a` over `p ≡ 1 (mod mn)`;
//! - non-hyperelliptic, any odd `m = 2g+1`: `y^m = x (1−x)^b` over
//!   `p ≡ 1 (mod m)` (rank-`m` ideal arithmetic, slow but general).
//!
//! An instance is `(curve, D₁, D₂ = k·D₁, N, k)` with `D₁` of prime order
//! `N` chosen inside a requested bit range; `k` is kept so a solver's
//! answer can be checked by the caller as well as by the solver.

use num_bigint::BigUint;
use num_traits::{One, Zero};
use rand::rngs::StdRng;
use rand::{RngCore, SeedableRng};

use super::cantor::{Divisor, HyperellipticCurve};
use super::fp::{next_prime_congruent, Fp};
use super::jacobi::{find_prime_subgroup_order, jacobian_order_with_orbit_norms, JacobiSumCurve};
use super::kummer::{Ideal, SuperellipticCurve};
use super::poly::Poly;
use super::rho::random_below;
use super::{HgError, JacobianGroup};

/// A planted instance on a group `G`.
#[derive(Clone, Debug)]
pub struct Instance<G: JacobianGroup> {
    pub group: G,
    pub d1: G::Elem,
    pub d2: G::Elem,
    /// Prime order of `D₁`.
    pub n: BigUint,
    /// `#Jac(F_p)`.
    pub jacobian_order: BigUint,
    /// The planted logarithm.
    pub k: BigUint,
    pub p: u64,
    pub genus: u32,
    pub description: String,
}

fn pick_subgroup(
    order: &BigUint,
    norms: &[BigUint],
    n_bits: (u32, u32),
) -> Result<(BigUint, BigUint), HgError> {
    let lo = BigUint::one() << n_bits.0;
    let hi = BigUint::one() << n_bits.1;
    find_prime_subgroup_order(order, norms, &lo, &hi, 2_000_000).ok_or(HgError::Exhausted(
        "no prime subgroup order in the requested bit range",
    ))
}

fn plant<G: JacobianGroup>(
    group: &G,
    random: impl Fn(&mut StdRng) -> G::Elem,
    n: &BigUint,
    cofactor: &BigUint,
    rng: &mut StdRng,
) -> Result<(G::Elem, G::Elem, BigUint), HgError> {
    for _ in 0..64 {
        let r = random(rng);
        let d1 = group.scalar_mul(cofactor, &r);
        if group.is_identity(&d1) {
            continue;
        }
        if !group.is_identity(&group.scalar_mul(n, &d1)) {
            return Err(HgError::BadCurve("N·D₁ ≠ 0: the group order is wrong"));
        }
        let mut k = random_below(rng, n);
        if k.is_zero() {
            k = BigUint::one();
        }
        let d2 = group.scalar_mul(&k, &d1);
        return Ok((d1, d2, k));
    }
    Err(HgError::Exhausted("cofactor multiples were all zero"))
}

/// Smallest usable prime `p ≥ start` with `p ≡ 1 (mod modulus)`.
pub fn prime_one_mod(modulus: u64, start: u64) -> Result<u64, HgError> {
    next_prime_congruent(start.max(3), modulus, 1)
        .ok_or(HgError::Unsupported("no prime ≡ 1 mod modulus below 2^32"))
}

/// Hyperelliptic planted instance of genus `g`: `y² = x^{2g+1} + a` over the
/// smallest prime `p ≥ min_p`, `p ≡ 1 (mod 2(2g+1))`, with `N` of
/// `n_bits.0 ..= n_bits.1` bits.
pub fn hyperelliptic_instance(
    genus: u32,
    min_p: u64,
    n_bits: (u32, u32),
    seed: u64,
) -> Result<Instance<HyperellipticCurve>, HgError> {
    let n_exp = 2 * genus + 1;
    let mut rng = StdRng::seed_from_u64(seed);
    let mut p = prime_one_mod(2 * n_exp as u64, min_p)?;
    for _attempt in 0..64 {
        let field = Fp::new(p)?;
        let a = 1 + rng.next_u64() % (p - 1);
        let curve = JacobiSumCurve::PowerSum { m: 2, n: n_exp, a };
        curve.validate(p)?;
        let (order, norms) = jacobian_order_with_orbit_norms(&curve, p)?;
        if let Ok((n, cof)) = pick_subgroup(&order, &norms, n_bits) {
            let f = Poly::from_coeffs(curve.rhs_poly(p), &field);
            let group = HyperellipticCurve::new(field, f)?;
            let g2 = genus as usize;
            let (d1, d2, k) = plant(
                &group,
                |r| group.random_element(g2.min(3), r),
                &n,
                &cof,
                &mut rng,
            )?;
            return Ok(Instance {
                group,
                d1,
                d2,
                n,
                jacobian_order: order,
                k,
                p,
                genus,
                description: format!("y^2 = x^{n_exp} + {a} over F_{p}"),
            });
        }
        p = prime_one_mod(2 * n_exp as u64, p + 1)?;
    }
    Err(HgError::Exhausted(
        "no hyperelliptic Jacobi-sum instance with a subgroup in range",
    ))
}

/// Non-hyperelliptic planted instance `y^m = x^n + a` (`m ≥ 3`, `gcd(m,n)=1`).
pub fn superelliptic_power_instance(
    m: u32,
    n_exp: u32,
    min_p: u64,
    n_bits: (u32, u32),
    seed: u64,
) -> Result<Instance<SuperellipticCurve>, HgError> {
    if m < 3 {
        return Err(HgError::Unsupported(
            "m ≥ 3 for the non-hyperelliptic family",
        ));
    }
    let mut rng = StdRng::seed_from_u64(seed);
    let modulus = m as u64 * n_exp as u64;
    let mut p = prime_one_mod(modulus, min_p)?;
    for _attempt in 0..64 {
        let field = Fp::new(p)?;
        let a = 1 + rng.next_u64() % (p - 1);
        let curve = JacobiSumCurve::PowerSum { m, n: n_exp, a };
        curve.validate(p)?;
        let genus = curve.genus()?;
        let (order, norms) = jacobian_order_with_orbit_norms(&curve, p)?;
        if let Ok((n, cof)) = pick_subgroup(&order, &norms, n_bits) {
            let f = Poly::from_coeffs(curve.rhs_poly(p), &field);
            let group = SuperellipticCurve::from_squarefree(field, m, f)?;
            let (d1, d2, k) = plant(&group, |r| group.random_element(2, r), &n, &cof, &mut rng)?;
            return Ok(Instance {
                group,
                d1,
                d2,
                n,
                jacobian_order: order,
                k,
                p,
                genus,
                description: format!("y^{m} = x^{n_exp} + {a} over F_{p}"),
            });
        }
        p = prime_one_mod(modulus, p + 1)?;
    }
    Err(HgError::Exhausted(
        "no superelliptic Jacobi-sum instance with a subgroup in range",
    ))
}

/// Non-hyperelliptic planted instance of genus `g` from the three-point
/// family `y^{2g+1} = x (1−x)^b` with `b` chosen coprime as required;
/// rank-`(2g+1)` ideal arithmetic.
pub fn three_point_instance(
    genus: u32,
    min_p: u64,
    n_bits: (u32, u32),
    seed: u64,
) -> Result<Instance<SuperellipticCurve>, HgError> {
    let m = 2 * genus + 1;
    if m < 5 {
        return Err(HgError::Unsupported("genus ≥ 2 for the three-point family"));
    }
    // b with gcd(b, m) = gcd(b+1, m) = 1 and (1, b, −(1+b)) pairwise distinct up to scaling.
    let b = (2..m)
        .find(|&b| {
            gcd(b, m) == 1
                && gcd(b + 1, m) == 1
                && gcd(b - 1, m) == 1
                && gcd(b + 2, m) == 1
                && gcd(2 * b + 1, m) == 1
        })
        .ok_or(HgError::Unsupported("no admissible exponent b for this m"))?;
    let mut rng = StdRng::seed_from_u64(seed);
    let mut p = prime_one_mod(m as u64, min_p)?;
    for _attempt in 0..64 {
        let field = Fp::new(p)?;
        let curve = JacobiSumCurve::ThreePoint { m, a: 1, b };
        curve.validate(p)?;
        let (order, norms) = jacobian_order_with_orbit_norms(&curve, p)?;
        if let Ok((n, cof)) = pick_subgroup(&order, &norms, n_bits) {
            let x = Poly::from_coeffs(vec![0, 1], &field);
            let x_minus_one = Poly::from_coeffs(vec![p - 1, 1], &field);
            let group = SuperellipticCurve::new(field, m, vec![(x, 1), (x_minus_one, b)])?;
            let (d1, d2, k) = plant(&group, |r| group.random_element(1, r), &n, &cof, &mut rng)?;
            return Ok(Instance {
                group,
                d1,
                d2,
                n,
                jacobian_order: order,
                k,
                p,
                genus,
                description: format!("y^{m} = x (1-x)^{b} over F_{p}"),
            });
        }
        p = prime_one_mod(m as u64, p + 1)?;
    }
    Err(HgError::Exhausted(
        "no three-point instance with a subgroup in range",
    ))
}

fn gcd(mut a: u32, mut b: u32) -> u32 {
    while b != 0 {
        let t = a % b;
        a = b;
        b = t;
    }
    a
}

/// Convenience: the Mumford divisor type of hyperelliptic instances.
pub type HyperellipticInstance = Instance<HyperellipticCurve>;
/// Convenience: the ideal type of superelliptic instances.
pub type SuperellipticInstance = Instance<SuperellipticCurve>;

#[allow(dead_code)]
fn _types(_: &Divisor, _: &Ideal) {}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn plants_small_instances_on_both_engines() {
        let inst = hyperelliptic_instance(5, 3, (8, 24), 1).unwrap();
        assert_eq!(inst.genus, 5);
        assert_eq!(inst.group.scalar_mul(&inst.k, &inst.d1), inst.d2);
        assert!(inst
            .group
            .is_identity(&inst.group.scalar_mul(&inst.n, &inst.d1)));
        let inst = superelliptic_power_instance(3, 4, 3, (4, 20), 1).unwrap();
        assert_eq!(inst.genus, 3);
        assert_eq!(inst.group.scalar_mul(&inst.k, &inst.d1), inst.d2);
        let inst = three_point_instance(5, 3, (4, 20), 1).unwrap();
        assert_eq!(inst.genus, 5);
        assert_eq!(inst.group.scalar_mul(&inst.k, &inst.d1), inst.d2);
    }
}
