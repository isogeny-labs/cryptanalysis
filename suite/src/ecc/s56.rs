//! Parameters for the public synthetic S56 research fixture.
//!
//! The reported SHA-1 counter 1841 is provenance only: its seed encoding
//! and derivation transcript have not been supplied. This is a research
//! fixture, not a standardized cryptographic parameter set.

pub const NAME: &str = "icv1-fp56-tm132906245-e876a6ea";
pub const P: u64 = 71_776_123_356_250_111;
pub const A: u64 = P - 3;
pub const B: u64 = 11_246_936_090_499_842;
pub const N: u64 = 71_776_123_489_156_357;
pub const GX: u64 = 3;
pub const GY: u64 = 8_355_444_684_664_812;
pub const J: u64 = 51_515_385_884_595_611;
pub const TRACE: i64 = -132_906_245;
pub const TWIST_PRIME: u64 = 2_658_374_934_197_921;
pub const FROBENIUS_CONDUCTOR: u64 = 3;
pub const FUNDAMENTAL_DISCRIMINANT: i128 = -29_937_824_829_444_491;
/// Roots of the 3-division polynomial; these are kernel x-coordinates,
/// not affine points over F_p (their right-hand sides are nonsquares).
pub const THREE_KERNEL_X: [u64; 4] = [
    53_952_979_029_178_256,
    6_350_112_957_496_721,
    6_314_724_791_074_991,
    5_158_306_578_500_143,
];

#[cfg(test)]
mod tests {
    use super::*;

    fn mulmod(a: u64, b: u64, m: u64) -> u64 {
        (u128::from(a) * u128::from(b) % u128::from(m)) as u64
    }
    fn powmod(mut a: u64, mut k: u64, m: u64) -> u64 {
        let mut r = 1;
        while k > 0 {
            if k & 1 != 0 {
                r = mulmod(r, a, m);
            }
            a = mulmod(a, a, m);
            k >>= 1;
        }
        r
    }
    // Deterministic Miller-Rabin witness set for every unsigned 64-bit n.
    fn prime(n: u64) -> bool {
        if n < 2 {
            return false;
        }
        for q in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37] {
            if n.is_multiple_of(q) {
                return n == q;
            }
        }
        let s = (n - 1).trailing_zeros();
        let d = (n - 1) >> s;
        'witness: for a in [2, 325, 9375, 28178, 450775, 9780504, 1795265022] {
            if a % n == 0 {
                continue;
            }
            let mut x = powmod(a % n, d, n);
            if x == 1 || x == n - 1 {
                continue;
            }
            for _ in 1..s {
                x = mulmod(x, x, n);
                if x == n - 1 {
                    continue 'witness;
                }
            }
            return false;
        }
        true
    }
    type Point = Option<(u64, u64)>;
    fn add(a: Point, b: Point) -> Point {
        let (Some((x, y)), Some((u, v))) = (a, b) else {
            return a.or(b);
        };
        if x == u && (y + v) % P == 0 {
            return None;
        }
        let (num, den) = if x == u {
            ((3 * mulmod(x, x, P) + A) % P, (2 * y) % P)
        } else {
            ((v + P - y) % P, (u + P - x) % P)
        };
        let slope = mulmod(num, powmod(den, P - 2, P), P);
        let z = (mulmod(slope, slope, P) + 2 * P - x - u) % P;
        Some((z, (mulmod(slope, (x + P - z) % P, P) + P - y) % P))
    }
    fn scale(mut k: u64, mut a: Point) -> Point {
        let mut r = None;
        while k > 0 {
            if k & 1 != 0 {
                r = add(r, a);
            }
            a = add(a, a);
            k >>= 1;
        }
        r
    }
    fn rhs(x: u64) -> u64 {
        (mulmod(mulmod(x, x, P), x, P) + mulmod(A, x, P) + B) % P
    }

    #[test]
    fn s56_prime_shape_and_exact_order_witness() {
        assert_eq!(
            P,
            (1u64 << 56) - (1u64 << 48) + (1u64 << 32) + (1u64 << 16) - 1
        );
        assert_eq!(P % 4, 3);
        assert!(prime(P) && prime(N));
        let numerator = mulmod(1728, mulmod(4, mulmod(mulmod(A, A, P), A, P), P), P);
        let denominator = (4 * mulmod(mulmod(A, A, P), A, P) + 27 * mulmod(B, B, P)) % P;
        assert_eq!(mulmod(numerator, powmod(denominator, P - 2, P), P), J);
        assert_eq!(mulmod(GY, GY, P), rhs(GX));
        assert_ne!(
            (4 * mulmod(mulmod(A, A, P), A, P) + 27 * mulmod(B, B, P)) % P,
            0
        );
        assert_eq!(scale(N, Some((GX, GY))), None);
        // Nonzero G has prime order N. Hasse leaves only one multiple of N.
        assert!(u128::from(N) * u128::from(N) > 16 * u128::from(P));
        assert_eq!(i128::from(P) + 1 - i128::from(N), i128::from(TRACE));
        assert!(i128::from(TRACE).pow(2) <= 4 * i128::from(P));
    }

    #[test]
    fn s56_twist_has_a_52_bit_prime_factor() {
        assert!(prime(TWIST_PRIME));
        assert_eq!(2 * (P + 1) - N, 27 * TWIST_PRIME);
        assert_eq!(64 - TWIST_PRIME.leading_zeros(), 52);
    }

    #[test]
    fn s56_frobenius_discriminant_has_conductor_three() {
        for q in [109, 163, 1_685_024_192_573] {
            assert!(prime(q));
        }
        assert_eq!(FUNDAMENTAL_DISCRIMINANT, -109i128 * 163 * 1_685_024_192_573);
        assert_eq!(FUNDAMENTAL_DISCRIMINANT.rem_euclid(4), 1);
        assert_eq!(FUNDAMENTAL_DISCRIMINANT.rem_euclid(3), 1);
        assert_eq!(
            i128::from(TRACE).pow(2) - 4 * i128::from(P),
            i128::from(FROBENIUS_CONDUCTOR).pow(2) * FUNDAMENTAL_DISCRIMINANT
        );
    }

    #[test]
    fn s56_four_rational_three_isogeny_kernels() {
        let mut polynomial = vec![3];
        for (i, &x) in THREE_KERNEL_X.iter().enumerate() {
            assert!(!THREE_KERNEL_X[..i].contains(&x));
            assert_eq!(powmod(rhs(x), (P - 1) / 2, P), P - 1);
            let mut product = vec![0; polynomial.len() + 1];
            for (j, &c) in polynomial.iter().enumerate() {
                product[j] = (product[j] + mulmod(c, P - x, P)) % P;
                product[j + 1] = (product[j + 1] + c) % P;
            }
            polynomial = product;
        }
        assert_eq!(polynomial, vec![P - 9, (12 * B) % P, P - 18, 0, 3]);
    }
}
