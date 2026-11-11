//! Differential fixture using pre-existing cryptanalysis arithmetic unchanged.
//! Both implementations use Cantor reduction; agreement is not a signed verdict.
// Compatibility with the pinned unmodified reference's Fp2Ctx::from_fp(&self).
#[allow(dead_code, unused_imports, clippy::wrong_self_convention)]
#[path = "../../../suite/src/prime_hyperelliptic/mod.rs"]
mod reference;

use chained_jacobian_transfer as chain;
use num_bigint::BigUint;
use reference::{FpPoly, HyperellipticCurveP, MumfordDivisorP};

fn polynomial(c: &[i64]) -> FpPoly {
    FpPoly::from_coeffs(
        c.iter().map(|x| BigUint::from(*x as u64)).collect(),
        BigUint::from(101_u32),
    )
}
fn curve(f: &[i64]) -> HyperellipticCurveP {
    let a = chain::inv(*f.last().unwrap());
    let coeffs: Vec<_> = f
        .iter()
        .enumerate()
        .map(|(i, c)| chain::fp(c * chain::pow(a, i as u64) * chain::inv(chain::pow(a, 4))))
        .collect();
    HyperellipticCurveP::try_new(BigUint::from(101_u32), polynomial(&coeffs), 2).unwrap()
}
fn convert(d: &chain::Divisor, c: &HyperellipticCurveP, f: &[i64]) -> MumfordDivisorP {
    let a = chain::inv(*f.last().unwrap());
    let lead = chain::pow(a, (d.u.len() - 1) as u64);
    let u: Vec<_> =
        d.u.iter()
            .enumerate()
            .map(|(i, x)| chain::fp(x * chain::pow(a, i as u64) * chain::inv(lead)))
            .collect();
    let v: Vec<_> =
        d.v.iter()
            .enumerate()
            .map(|(i, x)| chain::fp(x * chain::pow(a, i as u64) * chain::inv(chain::pow(a, 2))))
            .collect();
    MumfordDivisorP::try_from_polynomials(c, polynomial(&u), polynomial(&v)).unwrap()
}
fn check() {
    let f = chain::quintic();
    let c = curve(&f);
    let classes = chain::rational_classes();
    for (i, d) in classes.iter().enumerate() {
        let h = &classes[(7919 * i + 37) % classes.len()];
        let a = convert(d, &c, &f);
        let b = convert(h, &c, &f);
        assert_eq!(
            a.checked_add(&b, &c).unwrap(),
            convert(&d.add(h), &c, &f),
            "pair {i}"
        );
        assert_eq!(
            a.checked_neg(&c).unwrap(),
            convert(&d.neg(), &c, &f),
            "inverse {i}"
        );
    }
    println!("PASS {} canonical additions and inverses against pre-existing cryptanalysis BigUint implementation",classes.len());
    println!("Development correctness only; no timing or independent signed verification");
}
fn main() {
    check();
    check_richelot_target();
    check_full_richelot_image();
}

#[test]
fn compares_every_canonical_source_class() {
    check();
}

fn check_richelot_target() {
    use chain::richelot;
    let f = richelot::target_quintic();
    let c = curve(&f);
    let mut images = vec![];
    for k in 0..17 {
        images.push(
            richelot::transfer(&chain::pull(chain::ec_mul(chain::point(4, 41), k, 0, 0)).unwrap())
                .unwrap(),
        );
    }
    let converted = |image: &richelot::Image| {
        let (u, v) = image.coefficients();
        // Coordinates belong to the target curve; Divisor here is only a data
        // container for conversion, never passed to source arithmetic/valid().
        convert(&chain::Divisor { u, v }, &c, &f)
    };
    for a in &images {
        for b in &images {
            assert_eq!(
                converted(a).checked_add(&converted(b), &c).unwrap(),
                converted(&a.add(b))
            );
        }
    }
    println!(
        "PASS all 289 Richelot target subgroup additions against pre-existing BigUint arithmetic"
    );
}
#[test]
fn compares_all_richelot_target_subgroup_additions() {
    check_richelot_target();
}

fn check_full_richelot_image() {
    use chain::richelot;
    let f = richelot::target_quintic();
    let c = curve(&f);
    let classes = chain::rational_classes();
    let translation = &classes[111];
    let converted = |image: &richelot::Image| {
        let (u, v) = image.coefficients();
        convert(&chain::Divisor { u, v }, &c, &f)
    };
    let tr = converted(&richelot::transfer(translation).unwrap());
    for d in &classes {
        let image = converted(&richelot::transfer(d).unwrap());
        let expected = converted(&richelot::transfer(&d.add(translation)).unwrap());
        assert_eq!(image.checked_add(&tr, &c).unwrap(), expected);
    }
    println!("PASS all 10404 rational Richelot source images plus fixed-translation addition against BigUint");
}

#[test]
fn compares_full_rational_richelot_image() {
    check_full_richelot_image();
}

#[test]
fn independent_point_count_orders_of_both_models() {
    for f in [chain::quintic(), chain::richelot::target_quintic()] {
        let c = curve(&f);
        assert_eq!(
            reference::brute_force_jac_order_via_lpoly(&c),
            BigUint::from(10404_u32)
        );
    }
}
