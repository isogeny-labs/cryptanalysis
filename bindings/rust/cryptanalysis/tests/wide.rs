//! Groups above 2^53 (where an f64 stops holding every integer) up to the
//! library's 64-bit limit, through the safe API; the same instances as
//! `tests/test_wide.c`. Answers are checked against u128 arithmetic as well as
//! against the planted secret.

use cryptanalysis::index_calculus::{self, IcParams};
use cryptanalysis::{factorize, is_prime, primitive_root, Elem, Error, Group, Options};

const WIDE_P: u64 = u64::MAX - 3058; // 2^64 - 3059
const WIDE_Q: u64 = (WIDE_P - 1) / 4;
const WIDE_X: u64 = (1 << 62) - 904;
const SMOOTH_P: u64 = 18_412_301_237_266_326_539; // p - 1 is 2^28-smooth
const EC64_P: u64 = 18_446_744_056_529_682_403;
const EC64_N: u64 = 18_446_744_051_100_303_869; // 7 * EC64_Q
const EC64_Q: u64 = 2_635_249_150_157_186_267;

fn powmod_u128(b: u64, mut e: u64, m: u64) -> u64 {
    let mut r = 1u128;
    let mut base = u128::from(b % m);
    while e > 0 {
        if e & 1 == 1 {
            r = r * base % u128::from(m);
        }
        base = base * base % u128::from(m);
        e >>= 1;
    }
    r as u64
}

#[test]
fn zp_prime_subgroup_intervals() {
    let z = Group::zp(WIDE_P, WIDE_Q).unwrap();
    let g = z.find_generator(3).unwrap();
    assert_eq!(powmod_u128(g.0[0], WIDE_Q, WIDE_P), 1);
    let h = z.mul(&g, WIDE_X).unwrap();
    assert_eq!(h.0[0], powmod_u128(g.0[0], WIDE_X, WIDE_P));
    let opts = Options {
        seed: 7,
        ..Options::default()
    };
    let (lo, hi) = (WIDE_X - (1 << 30), WIDE_Q - 1);
    assert_eq!(z.bsgs(&g, &h, lo, hi, &opts).unwrap().0, WIDE_X);
    assert_eq!(z.kangaroo(&g, &h, lo, hi, &opts).unwrap().0, WIDE_X);
    assert_eq!(z.grumpy(&g, &h, lo, hi, &opts).unwrap().0, WIDE_X);
    assert!(matches!(
        z.bsgs(&g, &h, 1 << 51, (1 << 51) + (1 << 20), &opts),
        Err(Error::NotFound(_))
    ));
}

#[test]
fn zp_full_group_pohlig_hellman() {
    assert!(factorize(SMOOTH_P - 1).iter().all(|&(q, _)| q < 1 << 28));
    let z = Group::zp(SMOOTH_P, 0).unwrap();
    assert_eq!(z.order(), SMOOTH_P - 1);
    let root = primitive_root(SMOOTH_P);
    for x in [SMOOTH_P - 2, (1 << 53) + 1, (1 << 63) + 12345] {
        let h = z.mul(&Elem::zp(root), x).unwrap();
        assert_eq!(h.0[0], powmod_u128(root, x, SMOOTH_P));
        assert_eq!(
            z.dlog(&Elem::zp(root), &h, &Options::default()).unwrap().0,
            x
        );
    }
}

#[test]
fn ec_64bit_curve() {
    assert_eq!(Group::ec_count_points(EC64_P, 5, 5).unwrap(), EC64_N);
    assert_eq!(factorize(EC64_N), vec![(7, 1), (EC64_Q, 1)]);
    let mut e = Group::ec(EC64_P, 5, 5, EC64_Q).unwrap();
    e.set_order(EC64_Q, EC64_N / EC64_Q);
    let g = e.find_generator(5).unwrap();
    assert_eq!(e.elem_order(&g).unwrap(), EC64_Q);
    let x = EC64_Q - 123_456_789;
    let h = e.mul(&g, x).unwrap();
    // The curve equation in u128: y^2 == x^3 + 5x + 5 (mod p).
    let (hx, hy, p) = (u128::from(h.0[0]), u128::from(h.0[1]), u128::from(EC64_P));
    let rhs = (hx * hx % p * hx % p + 5 * hx + 5) % p;
    assert_eq!(hy * hy % p, rhs);
    let opts = Options {
        seed: 9,
        ..Options::default()
    };
    let (lo, hi) = (x - (1 << 30), EC64_Q - 1);
    assert_eq!(e.bsgs(&g, &h, lo, hi, &opts).unwrap().0, x);
    assert_eq!(e.kangaroo(&g, &h, lo, hi, &opts).unwrap().0, x);
    assert_eq!(e.grumpy(&g, &h, lo, hi, &opts).unwrap().0, x);
}

#[test]
fn index_calculus_above_2_50() {
    let p = 4_503_599_627_370_023u64; // 52-bit safe prime
    assert!(is_prime(p) && is_prime((p - 1) / 2));
    let g = primitive_root(p);
    let h = powmod_u128(g, (1 << 51) + 7, p);
    let (x, _) = index_calculus::solve(p, g, h, &IcParams::default()).unwrap();
    assert_eq!(powmod_u128(g, x, p), h);
    assert!(matches!(
        index_calculus::solve(WIDE_P, primitive_root(WIDE_P), 99, &IcParams::default()),
        Err(Error::Unsupported(_))
    ));
}
