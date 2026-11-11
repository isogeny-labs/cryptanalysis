//! Differential fixture using pre-existing cryptanalysis arithmetic unchanged.
//! Both implementations use Cantor reduction; agreement is not a signed verdict.
// Compatibility with the pinned unmodified reference's Fp2Ctx::from_fp(&self).
#[allow(dead_code, unused_imports, clippy::wrong_self_convention)]
#[path = "../../../suite/src/prime_hyperelliptic/mod.rs"]
mod reference;

use chained_jacobian_transfer as chain;
use num_bigint::BigUint;
use reference::{FpPoly, HyperellipticCurveP, MumfordDivisorP};

#[cfg(test)]
mod balanced;
#[cfg(test)]
mod cubic_transfer;
#[cfg(test)]
mod small_prime_oracle;

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
    check_successor();
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

// This continuation is bound to a newer upstream checkpoint in source-pin.json.
// The original baseline receipts remain unchanged and retain their old scope.
fn check_successor() {
    use chain::richelot::model::Richelot;
    let r = Richelot::new([[-1, 0, 1], [4, 1, 1], [4, -1, 1]], 1, 2).unwrap();
    for (model, expected_two) in [(r.source(), 4), (r.target(), 16)] {
        let f = model.quintic();
        let c = curve(&f);
        assert_eq!(
            reference::brute_force_jac_order_via_lpoly(&c),
            BigUint::from(9216_u32)
        );
        let classes = model.classes();
        assert_eq!(classes.len(), 9216);
        let converted = |d: &chain::richelot::model::Class| {
            let (u, v) = d.coefficients();
            convert(&chain::Divisor { u, v }, &c, &f)
        };
        let mut two = 0;
        for (i, d) in classes.iter().enumerate() {
            let a = converted(d);
            let inverse = a.checked_neg(&c).unwrap();
            if inverse == a {
                two += 1;
            }
            let h = &classes[(7919 * i + 37) % classes.len()];
            assert_eq!(
                a.checked_add(&converted(h), &c).unwrap(),
                converted(&d.add(h).unwrap()),
                "successor addition root={} class={i}",
                model.root()
            );
            let composed = if model == r.source() {
                r.dual(&r.transfer(d).unwrap()).unwrap()
            } else {
                r.transfer(&r.dual(d).unwrap()).unwrap()
            };
            assert_eq!(
                a.checked_add(&a, &c).unwrap(),
                converted(&composed),
                "successor dual norm root={} class={i}",
                model.root()
            );
        }
        assert_eq!(two, expected_two);
        println!("PASS successor root={}: 9216 classes, Fp/Fp² Jacobian order9216, BigUint self-inverse count{two}, paired additions and dual norm",model.root());
    }
}

#[test]
fn successor_both_complete_models_against_biguint() {
    check_successor();
}

#[test]
fn predeclared_second_hop_target_against_biguint() {
    use chain::richelot::model::{Class, Richelot};
    let first = Richelot::new([[-1, 0, 1], [4, 1, 1], [4, -1, 1]], 1, 2).unwrap();
    let second = Richelot::new([[36, -20, 1], [-56, -26, 1], [10080, 920, 20]], 2, 11).unwrap();
    assert_eq!(first.target(), second.source());
    let model = second.target();
    let f = model.quintic();
    let c = curve(&f);
    assert_eq!(
        reference::brute_force_jac_order_via_lpoly(&c),
        BigUint::from(9216_u32)
    );
    let classes = model.classes();
    assert_eq!(classes.len(), 9216);
    let converted = |d: &Class| {
        let (u, v) = d.coefficients();
        convert(&chain::Divisor { u, v }, &c, &f)
    };
    let mut two = 0;
    for (i, d) in classes.iter().enumerate() {
        let a = converted(d);
        if a.checked_neg(&c).unwrap() == a {
            two += 1;
        }
        let h = &classes[(7919 * i + 37) % classes.len()];
        assert_eq!(
            a.checked_add(&converted(h), &c).unwrap(),
            converted(&d.add(h).unwrap())
        );
        assert_eq!(
            a.checked_add(&a, &c).unwrap(),
            converted(&second.transfer(&second.dual(d).unwrap()).unwrap())
        );
    }
    assert_eq!(two, 8);
    let source = first.source();
    let sf = source.quintic();
    let sc = curve(&sf);
    let mut kernel = vec![];
    for d in source.classes() {
        let image = second.transfer(&first.transfer(&d).unwrap()).unwrap();
        if image == model.zero() {
            let (u, v) = d.coefficients();
            kernel.push(convert(&chain::Divisor { u, v }, &sc, &sf));
        }
    }
    let two_kernel = kernel
        .iter()
        .filter(|d| d.checked_neg(&sc).unwrap() == **d)
        .count();
    assert_eq!((kernel.len(), two_kernel), (8, 4));
    println!("PASS second-hop target: independent point-count order9216, 9216 paired additions/dual norms, self-inverse count8; rational composite kernel8 with4 self-inverse elements");
}
