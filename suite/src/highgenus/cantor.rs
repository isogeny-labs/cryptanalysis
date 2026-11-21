//! Genus-generic hyperelliptic Jacobian arithmetic over `F_p` (odd `p`):
//! Mumford representation and Cantor's algorithm on dense [`Poly`]s.
//!
//! Model: `C : y² = f(x)`, `f` monic squarefree of degree `2g + 1`
//! (imaginary model, one rational point `∞`). A reduced divisor is a pair
//! `(u, v)` with `u` monic, `deg v < deg u ≤ g`, `u | v² − f`; the identity
//! is `(1, 0)`, negation is `(u, −v)`. Every class has exactly one reduced
//! representative, so structural equality is class equality.
//!
//! Composition (Cantor, odd characteristic):
//! ```text
//!   d₁ = gcd(u₁, u₂) = e₁u₁ + e₂u₂
//!   d  = gcd(d₁, v₁ + v₂) = c₁d₁ + c₂(v₁ + v₂)
//!   s₁ = c₁e₁, s₂ = c₁e₂, s₃ = c₂
//!   u  = u₁u₂ / d²
//!   v  = (s₁u₁v₂ + s₂u₂v₁ + s₃(v₁v₂ + f)) / d   mod u
//! ```
//! Reduction, while `deg u > g`: `u ← monic((f − v²)/u)`, `v ← −v mod u`.
//!
//! Costs grow like `O(g²)` field multiplications per polynomial operation
//! and `O(g)` reduction steps, i.e. `O(g³)` per group operation at genus
//! `g` with schoolbook polynomials (Karatsuba above the threshold in
//! [`Poly::mul`]). At `g = 131` a group operation is a few million field
//! multiplications; this is the reference path, not a tuned one.
//!
//! Compared with [`crate::prime_hyperelliptic`] (BigUint coefficients,
//! genus-2 counting utilities), this engine is the `p < 2^32` fast path
//! for any genus; both implement the same mathematics and the tests check
//! them against each other.

use std::cell::Cell;

use rand::RngCore;

use super::ext::{mth_roots, Fq};
use super::fp::Fp;
use super::poly::Poly;
use super::{HgError, JacobianGroup};

/// `C : y² = f(x)` over `F_p`, `deg f = 2g + 1`, `f` monic squarefree.
#[derive(Clone, Debug)]
pub struct HyperellipticCurve {
    pub field: Fp,
    pub f: Poly,
    pub genus: u32,
    ops: Cell<u64>,
}

/// A reduced Mumford divisor `(u, v)`.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct Divisor {
    pub u: Poly,
    pub v: Poly,
}

impl Divisor {
    pub fn identity() -> Self {
        Self {
            u: Poly::one(),
            v: Poly::zero(),
        }
    }

    pub fn is_identity(&self) -> bool {
        self.u.is_one()
    }

    /// Degree of the effective part (`deg u`).
    pub fn degree(&self) -> usize {
        self.u.degree().unwrap_or(0)
    }
}

impl HyperellipticCurve {
    /// Checked construction. `p` odd prime `< 2^32`, `f` monic squarefree of
    /// odd degree `2g + 1 ≥ 3`.
    pub fn new(field: Fp, f: Poly) -> Result<Self, HgError> {
        if !field.is_odd() {
            return Err(HgError::BadPrime(field.p()));
        }
        let d = f.degree().ok_or(HgError::BadCurve("f is zero"))?;
        if d < 3 || d.is_multiple_of(2) {
            return Err(HgError::BadCurve("deg f must be odd and at least 3"));
        }
        if !f.is_monic() {
            return Err(HgError::BadCurve("f must be monic"));
        }
        if !f.is_squarefree(&field) {
            return Err(HgError::BadCurve("f must be squarefree"));
        }
        Ok(Self {
            field,
            f,
            genus: ((d - 1) / 2) as u32,
            ops: Cell::new(0),
        })
    }

    /// A random curve of the requested genus (random monic squarefree `f`).
    pub fn random(field: Fp, genus: u32, rng: &mut impl RngCore) -> Result<Self, HgError> {
        if genus == 0 {
            return Err(HgError::BadCurve("genus must be positive"));
        }
        let f = Poly::random_squarefree_monic(2 * genus as usize + 1, &field, rng);
        Self::new(field, f)
    }

    /// Validate a reduced divisor against this curve.
    pub fn validate(&self, d: &Divisor) -> Result<(), HgError> {
        if d.u.is_zero() || !d.u.is_monic() {
            return Err(HgError::BadDivisor("u must be monic and nonzero"));
        }
        if d.degree() > self.genus as usize {
            return Err(HgError::BadDivisor("deg u exceeds the genus"));
        }
        if d.v.deg() >= d.u.deg() {
            return Err(HgError::BadDivisor("deg v must be below deg u"));
        }
        let rhs = d.v.sqr(&self.field).sub(&self.f, &self.field);
        if !rhs.rem(&d.u, &self.field).is_zero() {
            return Err(HgError::BadDivisor("u does not divide v² − f"));
        }
        Ok(())
    }

    fn bump(&self) {
        self.ops.set(self.ops.get() + 1);
    }

    /// Divisor of the rational point `(x0, y0)` as `[P] − [∞]`.
    pub fn from_point(&self, x0: u64, y0: u64) -> Result<Divisor, HgError> {
        let k = &self.field;
        if self.f.eval(x0, k) != k.sqr(y0) {
            return Err(HgError::BadDivisor("point is not on the curve"));
        }
        Ok(Divisor {
            u: Poly::from_coeffs(vec![k.neg(x0), 1], k),
            v: Poly::constant(y0),
        })
    }

    /// The semi-reduced divisor of a place of degree `deg π` above the
    /// monic irreducible `π`: `(π, v)` with `v² ≡ f (mod π)`, if `f` is a
    /// square modulo `π`. Returns both signs when `v ≠ 0`.
    pub fn places_above(&self, pi: &Poly, rng: &mut impl RngCore) -> Vec<Divisor> {
        let k = &self.field;
        let fq = Fq::new(*k, pi.clone());
        let fbar = fq.reduce(&self.f);
        let mut out = Vec::new();
        for v in mth_roots(&fbar, 2, &fq, rng) {
            out.push(Divisor { u: pi.clone(), v });
        }
        out
    }

    /// Cantor composition followed by reduction.
    pub fn add_divisors(&self, a: &Divisor, b: &Divisor) -> Divisor {
        self.bump();
        let k = &self.field;
        if a.is_identity() {
            return b.clone();
        }
        if b.is_identity() {
            return a.clone();
        }
        let (d1, e1, e2) = a.u.xgcd(&b.u, k);
        let (u, v) = if d1.is_one() {
            // Common case: coprime u's. u = u₁u₂, v = CRT of v₁, v₂.
            let u = a.u.mul(&b.u, k);
            // v ≡ v₁ (mod u₁), v ≡ v₂ (mod u₂): v = v₁ + u₁·e₁·(v₂ − v₁) mod u
            // since e₁u₁ ≡ 1 (mod u₂).
            let diff = b.v.sub(&a.v, k);
            let t = Poly::mulmod(&e1.mul(&a.u, k), &diff, &u, k);
            let v = a.v.add(&t, k).rem(&u, k);
            (u, v)
        } else {
            let vsum = a.v.add(&b.v, k);
            let (d, c1, c2) = d1.xgcd(&vsum, k);
            let s1 = c1.mul(&e1, k);
            let s2 = c1.mul(&e2, k);
            let s3 = c2;
            let dd = d.sqr(k);
            let u = a.u.mul(&b.u, k).div_exact(&dd, k).expect("d² | u₁u₂");
            let t1 = s1.mul(&a.u, k).mul(&b.v, k);
            let t2 = s2.mul(&b.u, k).mul(&a.v, k);
            let t3 = s3.mul(&a.v.mul(&b.v, k).add(&self.f, k), k);
            let num = t1.add(&t2, k).add(&t3, k);
            let v = num.div_exact(&d, k).expect("d | v numerator").rem(&u, k);
            (u, v)
        };
        self.reduce(u, v)
    }

    /// Reduce a semi-reduced pair `(u, v)` (`u | v² − f`, `deg v < deg u`)
    /// to the unique reduced representative.
    pub fn reduce(&self, mut u: Poly, mut v: Poly) -> Divisor {
        let k = &self.field;
        let g = self.genus as usize;
        while u.degree().unwrap_or(0) > g {
            let num = self.f.sub(&v.sqr(k), k);
            let u_new = num.div_exact(&u, k).expect("u | f − v²").monic(k);
            let v_new = v.neg(k).rem(&u_new, k);
            u = u_new;
            v = v_new;
        }
        if !u.is_monic() {
            u = u.monic(k);
        }
        Divisor { u, v }
    }

    /// Doubling via the general composition (specialised later if needed).
    pub fn double_divisor(&self, a: &Divisor) -> Divisor {
        self.add_divisors(a, a)
    }

    pub fn neg_divisor(&self, a: &Divisor) -> Divisor {
        Divisor {
            u: a.u.clone(),
            v: a.v.neg(&self.field),
        }
    }

    /// A random element of the group generated by the rational places of
    /// degree `≤ max_place_degree`: a random sum of random places, reduced.
    /// With `max_place_degree ≥ g` this samples the whole Jacobian uniformly
    /// enough for walks and planted instances (it is not a proof of
    /// uniformity, and the tests only need a random-looking element).
    pub fn random_element(&self, max_place_degree: usize, rng: &mut impl RngCore) -> Divisor {
        let k = &self.field;
        let mut acc = Divisor::identity();
        let mut total = 0usize;
        let g = self.genus as usize;
        let mut guard = 0;
        while total < g {
            guard += 1;
            if guard > 10_000 {
                break;
            }
            let d = 1 + (rng.next_u64() as usize) % max_place_degree.max(1);
            let pi = Poly::random_irreducible(d, k, rng);
            let places = self.places_above(&pi, rng);
            if places.is_empty() {
                continue;
            }
            let pick = (rng.next_u64() as usize) % places.len();
            let place = self.reduce(places[pick].u.clone(), places[pick].v.clone());
            acc = self.add_divisors(&acc, &place);
            total += d;
        }
        acc
    }
}

fn mix64(mut h: u64) -> u64 {
    h ^= h >> 33;
    h = h.wrapping_mul(0xff51_afd7_ed55_8ccd);
    h ^= h >> 33;
    h = h.wrapping_mul(0xc4ce_b9fe_1a85_ec53);
    h ^= h >> 33;
    h
}

/// A fast structural hash of coefficient vectors.
pub fn hash_polys(polys: &[&Poly]) -> u64 {
    let mut h = 0x9e37_79b9_7f4a_7c15u64;
    for p in polys {
        h = mix64(h ^ (p.c.len() as u64).wrapping_mul(0x1000_0000_01b3));
        for &c in &p.c {
            h = mix64(h ^ c);
        }
    }
    h
}

impl JacobianGroup for HyperellipticCurve {
    type Elem = Divisor;

    fn identity(&self) -> Divisor {
        Divisor::identity()
    }

    fn add(&self, a: &Divisor, b: &Divisor) -> Divisor {
        self.add_divisors(a, b)
    }

    fn neg(&self, a: &Divisor) -> Divisor {
        self.neg_divisor(a)
    }

    fn is_identity(&self, a: &Divisor) -> bool {
        a.is_identity()
    }

    fn hash64(&self, a: &Divisor) -> u64 {
        hash_polys(&[&a.u, &a.v])
    }

    fn negation_class_key(&self, a: &Divisor) -> u64 {
        // (u, ±v): hash u and the sign-normalised v.
        let v = if self.is_negation_representative(a) {
            a.v.clone()
        } else {
            a.v.neg(&self.field)
        };
        hash_polys(&[&a.u, &v])
    }

    fn is_negation_representative(&self, a: &Divisor) -> bool {
        // v = 0 or leading coefficient of v in the lower half.
        a.v.is_zero() || a.v.leading() <= (self.field.p() - 1) / 2
    }

    fn group_ops(&self) -> u64 {
        self.ops.get()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::prime_hyperelliptic::{FpPoly, HyperellipticCurveP, MumfordDivisorP};
    use num_bigint::BigUint;
    use num_traits::{One, Zero};
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    fn to_big(c: &HyperellipticCurve, cb: &HyperellipticCurveP, d: &Divisor) -> MumfordDivisorP {
        let p = BigUint::from(c.field.p());
        let u = FpPoly::from_coeffs(d.u.c.iter().map(|&x| BigUint::from(x)).collect(), p.clone());
        let v = FpPoly::from_coeffs(d.v.c.iter().map(|&x| BigUint::from(x)).collect(), p.clone());
        MumfordDivisorP::try_from_polynomials(cb, u, v).unwrap()
    }

    fn from_big(c: &HyperellipticCurve, d: &MumfordDivisorP) -> Divisor {
        let k = &c.field;
        let conv = |f: &FpPoly| {
            Poly::from_coeffs(
                f.coeffs
                    .iter()
                    .map(|b| b.iter_u64_digits().next().unwrap_or(0))
                    .collect(),
                k,
            )
        };
        Divisor {
            u: conv(&d.u),
            v: conv(&d.v),
        }
    }

    #[test]
    fn agrees_with_the_biguint_reference_at_genus_two_three_five() {
        let mut rng = StdRng::seed_from_u64(1);
        for &(p, g) in &[(23u64, 2u32), (31, 3), (101, 5), (1009, 7)] {
            let k = Fp::new(p).unwrap();
            let c = HyperellipticCurve::random(k, g, &mut rng).unwrap();
            let big_f = FpPoly::from_coeffs(
                c.f.c.iter().map(|&x| BigUint::from(x)).collect(),
                BigUint::from(p),
            );
            let cb = HyperellipticCurveP::try_new(BigUint::from(p), big_f, g).unwrap();
            for _ in 0..20 {
                let a = c.random_element(g as usize, &mut rng);
                let b = c.random_element(g as usize, &mut rng);
                c.validate(&a).unwrap();
                c.validate(&b).unwrap();
                let s = c.add_divisors(&a, &b);
                c.validate(&s).unwrap();
                let sb = to_big(&c, &cb, &a).add(&to_big(&c, &cb, &b), &cb);
                assert_eq!(s, from_big(&c, &sb), "p={p} g={g}");
                let dbl = c.double_divisor(&a);
                assert_eq!(dbl, from_big(&c, &to_big(&c, &cb, &a).double(&cb)));
                let k7 = BigUint::from(12345u32);
                let m = c.scalar_mul(&k7, &a);
                assert_eq!(m, from_big(&c, &to_big(&c, &cb, &a).scalar_mul(&k7, &cb)));
            }
        }
    }

    #[test]
    fn group_axioms_at_sampled_genera() {
        let mut rng = StdRng::seed_from_u64(2);
        for &(p, g) in &[
            (3u64, 5u32),
            (7, 11),
            (1579, 23),
            (3, 47),
            (5, 97),
            (3, 131),
        ] {
            let k = Fp::new(p).unwrap();
            let c = HyperellipticCurve::random(k, g, &mut rng).unwrap();
            assert_eq!(c.genus, g);
            let a = c.random_element(6, &mut rng);
            let b = c.random_element(6, &mut rng);
            let d = c.random_element(6, &mut rng);
            c.validate(&a).unwrap();
            c.validate(&b).unwrap();
            c.validate(&d).unwrap();
            let ab = c.add_divisors(&a, &b);
            let ba = c.add_divisors(&b, &a);
            assert_eq!(ab, ba, "commutative p={p} g={g}");
            let abd = c.add_divisors(&ab, &d);
            let adb = c.add_divisors(&a, &c.add_divisors(&b, &d));
            assert_eq!(abd, adb, "associative p={p} g={g}");
            let zero = c.add_divisors(&a, &c.neg_divisor(&a));
            assert!(zero.is_identity(), "inverse p={p} g={g}");
            assert_eq!(c.add_divisors(&a, &Divisor::identity()), a);
            // (m + n) a = m a + n a
            let m = BigUint::from(97u32);
            let n = BigUint::from(1_000_003u32);
            let lhs = c.scalar_mul(&(&m + &n), &a);
            let rhs = c.add_divisors(&c.scalar_mul(&m, &a), &c.scalar_mul(&n, &a));
            assert_eq!(lhs, rhs, "distributive p={p} g={g}");
            assert!(c.group_ops() > 0);
            assert!(!BigUint::zero().is_one());
        }
    }

    #[test]
    fn rejects_bad_curves() {
        let k = Fp::new(7).unwrap();
        // x^5 is not squarefree.
        let f = Poly::monomial(5, 1);
        assert!(HyperellipticCurve::new(k, f).is_err());
        // even degree
        let f = Poly::from_coeffs(vec![1, 0, 0, 0, 0, 0, 1], &k);
        assert!(HyperellipticCurve::new(k, f).is_err());
        assert!(HyperellipticCurve::new(
            Fp::new(2).unwrap(),
            Poly::from_coeffs(vec![1, 1, 0, 1], &Fp::new(2).unwrap())
        )
        .is_err());
    }
}
