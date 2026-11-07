use crate::{bigint::BigInt, Result};

/// Result of filtering a quartic by a source quadratic. All integers are
/// arbitrary precision, so cryptographic field sizes need no overflow handling.
#[derive(Clone, Debug)]
pub struct Filter {
    pub q: BigInt,
    pub source_trace: BigInt,
    pub coefficients: [BigInt; 4],
    pub quotient: [BigInt; 3],
    pub remainder: [BigInt; 2],
    pub divides: bool,
    pub reciprocal: bool,
    pub quotient_elliptic_shape: bool,
    pub quotient_hasse_bound: bool,
}

impl Filter {
    pub fn passes_necessary_conditions(&self) -> bool {
        self.divides && self.reciprocal && self.quotient_elliptic_shape && self.quotient_hasse_bound
    }
}

/// Filter T^4+c1*T^3+c2*T^2+c3*T+c4 by T^2-trace*T+q.
/// Inputs are supplied field sizes and polynomials, not constructed varieties.
/// Passing does not construct a homomorphism or certify its action on a subgroup.
pub fn filter(
    q: impl Into<BigInt>,
    trace: impl Into<BigInt>,
    coefficients: [impl Into<BigInt>; 4],
) -> Result<Filter> {
    let q: BigInt = q.into();
    let trace: BigInt = trace.into();
    let coefficients = coefficients.map(Into::into);
    if q.is_negative() || q.bit_len() < 2 {
        return Err("q must be at least 2.".into());
    }
    let hasse = BigInt::from(4).mul(&q);
    if trace.mul(&trace) > hasse {
        return Err("The source trace violates the elliptic Hasse bound.".into());
    }
    let [c1, c2, c3, c4] = &coefficients;
    let u = c1.add(&trace);
    let v = c2.add(&trace.mul(&u)).sub(&q);
    let r1 = c3.add(&trace.mul(&v)).sub(&q.mul(&u));
    let r0 = c4.sub(&q.mul(&v));
    let divides = r1.is_zero() && r0.is_zero();
    let reciprocal = *c3 == q.mul(c1) && *c4 == q.mul(&q);
    let quotient_elliptic_shape = v == q;
    let quotient_hasse_bound = u.mul(&u) <= hasse;
    Ok(Filter {
        q,
        source_trace: trace,
        coefficients,
        quotient: [BigInt::from(1), u, v],
        remainder: [r1, r0],
        divides,
        reciprocal,
        quotient_elliptic_shape,
        quotient_hasse_bound,
    })
}
