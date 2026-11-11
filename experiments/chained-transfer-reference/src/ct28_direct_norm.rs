//! CT28: base-field elliptic quotient norms for smooth even genus-two sextics.
//! This is a bounded F_101 engineering candidate, not independently verified.
//! It bypasses extension-field factorization for degree <=2 balanced supports,
//! while retaining the unchanged native norm evaluator as a test oracle.
use crate::balanced::{Class, SplitQuotients};
use crate::reference::{HyperellipticCurveP as Curve, MumfordDivisorP as Divisor};
use num_bigint::BigUint;
use num_traits::ToPrimitive;

type Result<T> = std::result::Result<T, String>;

#[derive(Clone, Copy)]
struct F {
    p: u64,
}
impl F {
    fn add(self, a: u64, b: u64) -> u64 {
        (a + b) % self.p
    }
    fn neg(self, a: u64) -> u64 {
        (self.p - a % self.p) % self.p
    }
    fn sub(self, a: u64, b: u64) -> u64 {
        self.add(a, self.neg(b))
    }
    fn mul(self, a: u64, b: u64) -> u64 {
        a * b % self.p
    }
    fn pow(self, mut a: u64, mut n: u64) -> u64 {
        let mut b = 1;
        while n > 0 {
            if n & 1 == 1 {
                b = self.mul(b, a);
            }
            a = self.mul(a, a);
            n >>= 1;
        }
        b
    }
    fn inv(self, a: u64) -> Result<u64> {
        if a == 0 {
            return Err("CT28 division by zero".into());
        }
        let v = self.pow(a, self.p - 2);
        if self.mul(a, v) != 1 {
            return Err("CT28 coefficient has no inverse".into());
        }
        Ok(v)
    }
    fn div(self, a: u64, b: u64) -> Result<u64> {
        Ok(self.mul(a, self.inv(b)?))
    }
}
fn identity(curve: &Curve) -> Divisor {
    Divisor::identity(curve.p.clone())
}
fn point(curve: &Curve, x: u64, y: u64) -> Result<Divisor> {
    Divisor::try_from_point(curve, &BigUint::from(x), &BigUint::from(y))
        .map_err(|e| format!("CT28 invalid quotient point: {e}"))
}
fn double(curve: &Curve, x: u64, y: u64) -> Result<Divisor> {
    let d = point(curve, x, y)?;
    d.checked_add(&d, curve)
        .map_err(|e| format!("CT28 tangent failure: {e}"))
}
fn reciprocal_point(curve: &Curve, f: F, c: u64, x: u64, y: u64) -> Result<Divisor> {
    if x == 0 {
        return Ok(identity(curve));
    }
    let x2 = f.mul(x, x);
    let x3 = f.mul(x2, x);
    point(curve, f.div(c, x2)?, f.div(f.mul(c, y), x3)?)
}

/// Compute the direct norm to the even quotient and the reciprocal quotient.
/// No splitting choice or individually rationalized quadratic-support points
/// enter the evaluator; only base-field modular arithmetic is used here.
///
/// Inputs are validated by constructing the same *canonical* balanced class,
/// while native quotient norm computations are reserved for the regression.
fn direct_norms(split: &SplitQuotients, d: &Class) -> Result<(Divisor, Divisor)> {
    let (u, v, plus) = d.components();
    // Check the ORIGINAL curve tag. Re-wrapping only u/v/plus on this curve
    // would relabel a valid zero class from any other curve as our identity.
    split.first.balanced.check(d)?;
    let curve = &split.first.base;
    let reciprocal = &split.second.base;
    let f = F {
        p: curve.p.to_u64().ok_or("CT28 modulus too large")?,
    };
    if f.p != 101 {
        return Err("CT28 intentionally restricted to F_101".into());
    }
    let (sextic, _) = split.first.balanced.equation_and_infinity();
    let c = sextic.coeff(0).to_u64().unwrap();
    let b = sextic.coeff(2).to_u64().unwrap();
    let a = sextic.coeff(4).to_u64().unwrap();
    if c == 0 || sextic.coeff(6) != BigUint::from(1_u64) {
        return Err("CT28 requires a monic smooth even sextic with c!=0".into());
    }
    for i in [1, 3, 5] {
        if sextic.coeff(i) != BigUint::from(0_u64) {
            return Err("CT28 requires even sextic".into());
        }
    }

    let degree = u.degree().ok_or("CT28 zero support polynomial")?;
    let v0 = v.coeff(0).to_u64().unwrap();
    let v1 = v.coeff(1).to_u64().unwrap();
    let (even, mut rec) = match degree {
        0 => (identity(curve), identity(reciprocal)),
        1 => {
            let x = f.neg(u.coeff(0).to_u64().unwrap());
            (
                point(curve, f.mul(x, x), v0)?,
                reciprocal_point(reciprocal, f, c, x, v0)?,
            )
        }
        2 => {
            let s = u.coeff(1).to_u64().unwrap();
            let t = u.coeff(0).to_u64().unwrap();
            let even = if s != 0 {
                let m = f.neg(f.div(v1, s)?);
                let n = f.add(v0, f.mul(m, t));
                let sum_u = f.sub(f.mul(s, s), f.mul(2, t));
                let x = f.sub(f.sub(f.mul(m, m), a), sum_u);
                point(curve, x, f.neg(f.add(f.mul(m, x), n)))?
            } else if v1 != 0 {
                if v0 != 0 {
                    return Err("CT28 impossible even-conjugate support".into());
                }
                identity(curve)
            } else {
                double(curve, f.neg(t), v0)?
            };
            let rec = if t == 0 {
                if s == 0 {
                    identity(reciprocal)
                } else {
                    let x = f.neg(s);
                    reciprocal_point(reciprocal, f, c, x, f.add(v0, f.mul(v1, x)))?
                }
            } else {
                let sp = f.div(s, t)?;
                let tp = f.inv(t)?;
                let z0 = f.mul(f.mul(c, tp), f.sub(f.mul(v0, sp), v1));
                let z1 = f.mul(c, f.sub(f.mul(v0, f.sub(f.mul(sp, sp), tp)), f.mul(v1, sp)));
                if sp != 0 {
                    let m = f.neg(f.div(z1, f.mul(sp, c))?);
                    let n = f.add(z0, f.mul(m, f.mul(c, tp)));
                    let sum_v = f.mul(c, f.sub(f.mul(sp, sp), f.mul(2, tp)));
                    let x = f.sub(f.sub(f.mul(m, m), b), sum_v);
                    point(reciprocal, x, f.neg(f.add(f.mul(m, x), n)))?
                } else if z1 != 0 {
                    if z0 != 0 {
                        return Err("CT28 impossible reciprocal-conjugate support".into());
                    }
                    identity(reciprocal)
                } else {
                    double(reciprocal, f.neg(f.mul(c, tp)), z0)?
                }
            };
            (even, rec)
        }
        _ => return Err("CT28 degree outside bounded genus-two domain".into()),
    };

    // Finite support alone is insufficient for the reciprocal quotient.
    // Infinity_+ maps to (0,c), Infinity_- to (0,-c), while the
    // balanced class subtracts Infinity_+ + Infinity_-.
    let delta = 2 * i64::from(plus) + degree as i64 - 2;
    if delta != 0 {
        let t = point(reciprocal, 0, c)?;
        let mut correction = t
            .checked_scalar_mul(&BigUint::from(delta.unsigned_abs()), reciprocal)
            .map_err(|e| format!("CT28 infinity multiple: {e}"))?;
        if delta < 0 {
            correction = correction
                .checked_neg(reciprocal)
                .map_err(|e| format!("CT28 infinity sign: {e}"))?;
        }
        rec = rec
            .checked_add(&correction, reciprocal)
            .map_err(|e| format!("CT28 infinity correction: {e}"))?;
    }
    Ok((even, rec))
}

#[test]
fn ct28_complete_direct_norms_vs_frozen_generic_norms() {
    for (coefficients, name) in [([56_u64, 13, 6], "C0"), ([68_u64, 42, 26], "C1")] {
        let split = SplitQuotients::new(101, coefficients).unwrap();
        let classes = split.first.balanced.classes().unwrap();
        assert_eq!(classes.len(), 12317, "CT28 {name} class inventory");
        let mut counts = [0_usize; 5]; // degree0,degree1,split,nonsplit,repeated
        let mut s_zero = 0;
        let mut t_zero = 0;
        let field = F { p: 101 };
        for (i, d) in classes.iter().enumerate() {
            let (u, _, _) = d.components();
            match u.degree().unwrap() {
                0 => counts[0] += 1,
                1 => counts[1] += 1,
                2 => {
                    let s = u.coeff(1).to_u64().unwrap();
                    let t = u.coeff(0).to_u64().unwrap();
                    s_zero += usize::from(s == 0);
                    t_zero += usize::from(t == 0);
                    let disc = field.sub(field.mul(s, s), field.mul(4, t));
                    match field.pow(disc, 50) {
                        0 => counts[4] += 1,
                        1 => counts[2] += 1,
                        100 => counts[3] += 1,
                        x => panic!("CT28 invalid quadratic Legendre class {x}"),
                    }
                }
                _ => panic!("CT28 input degree"),
            }
            let new = direct_norms(&split, d)
                .unwrap_or_else(|e| panic!("CT28 {name} direct input {i}: {e}"));
            let old = split
                .norms(d)
                .unwrap_or_else(|e| panic!("CT28 {name} generic input {i}: {e}"));
            assert_eq!(new, old, "CT28 {name} norm mismatch input {i}");
        }
        assert_eq!(
            counts,
            [3, 236, 6844, 5116, 118],
            "CT28 {name} support census"
        );
        assert!(s_zero > 0 && t_zero > 0, "CT28 exceptional supports absent");
        let zero = split.first.balanced.zero();
        assert_eq!(
            direct_norms(&split, &zero).unwrap().0,
            identity(&split.first.base)
        );
        assert_eq!(
            direct_norms(&split, &zero).unwrap().1,
            identity(&split.second.base)
        );
        assert_ne!(
            direct_norms(&split, &split.first.balanced.delta())
                .unwrap()
                .1,
            identity(&split.second.base)
        );
        println!(
            "CT28 developmental native F101 {name}: {} direct/native norms; split={},nonsplit={},tangent={},s0={},t0={}",
            classes.len(), counts[2], counts[3], counts[4], s_zero, t_zero,
        );
    }

    // A class from another curve must fail before any coordinate evaluation.
    let source = SplitQuotients::new(101, [56, 13, 6]).unwrap();
    let other = SplitQuotients::new(101, [68, 42, 26]).unwrap();
    assert!(direct_norms(&other, &source.first.balanced.zero()).is_err());
}
