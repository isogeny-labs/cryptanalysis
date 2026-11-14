//! BigUint chart adapter and group checks. All chart arithmetic here uses
//! BigUint, rather than the producer's field helpers. The Fp2 point counter
//! and producer field backend share the same pre-existing algorithm lineage;
//! this is not independent validation of that field layer or a signed verdict.
use super::{chain, reference};
use chain::small_prime::{Class, Model, Projection, Richelot};
use num_bigint::BigUint;
use reference::{FpPoly, HyperellipticCurveP, MumfordDivisorP};

struct Adapter {
    model: Model,
    curve: HyperellipticCurveP,
    p: BigUint,
    powers: Vec<BigUint>,
    inverse_powers: Vec<BigUint>,
}
impl Adapter {
    fn new(model: &Model) -> Self {
        let p = BigUint::from(model.prime());
        let exponent = &p - BigUint::from(2_u32);
        let f = model.quintic();
        let a = BigUint::from(*f.last().unwrap()).modpow(&exponent, &p);
        let mut powers = vec![BigUint::from(1_u32)];
        for i in 0..5 {
            powers.push((&powers[i] * &a) % &p);
        }
        let inverse_powers: Vec<_> = powers.iter().map(|v| v.modpow(&exponent, &p)).collect();
        let coeffs: Vec<_> = f
            .iter()
            .enumerate()
            .map(|(i, c)| (BigUint::from(*c) * &powers[i] * &inverse_powers[4]) % &p)
            .collect();
        let curve =
            HyperellipticCurveP::try_new(p.clone(), FpPoly::from_coeffs(coeffs, p.clone()), 2)
                .unwrap();
        Self {
            model: model.clone(),
            curve,
            p,
            powers,
            inverse_powers,
        }
    }
    fn convert(&self, d: &Class) -> MumfordDivisorP {
        assert_eq!(d.model(), &self.model);
        let (u, v) = d.coefficients();
        let degree = u.len() - 1;
        let u = u
            .iter()
            .enumerate()
            .map(|(i, c)| {
                (BigUint::from(*c) * &self.powers[i] * &self.inverse_powers[degree]) % &self.p
            })
            .collect();
        let v = v
            .iter()
            .enumerate()
            .map(|(i, c)| (BigUint::from(*c) * &self.powers[i] * &self.inverse_powers[2]) % &self.p)
            .collect();
        MumfordDivisorP::try_from_polynomials(
            &self.curve,
            FpPoly::from_coeffs(u, self.p.clone()),
            FpPoly::from_coeffs(v, self.p.clone()),
        )
        .unwrap()
    }
}

fn elliptic_order(p: u64, coefficients: (u64, u64, u64)) -> usize {
    let modulus = BigUint::from(p);
    let (a, b, c) = coefficients;
    let (a, b, c) = (BigUint::from(a), BigUint::from(b), BigUint::from(c));
    let mut count = 1;
    for x in 0..p {
        let x = BigUint::from(x);
        let rhs = (((&x + &a) * &x + &b) * &x + &c) % &modulus;
        for y in 0..p {
            let y = BigUint::from(y);
            if &y * &y % &modulus == rhs {
                count += 1;
            }
        }
    }
    count
}

#[test]
fn four_fields_complete_models_against_biguint() {
    for (prime, expected_two) in [(13, (4, 4)), (29, (4, 16)), (31, (16, 4)), (101, (4, 16))] {
        let r = Richelot::new(prime, [[-1, 0, 1], [4, 1, 1], [4, -1, 1]], 1, 2).unwrap();
        for (model, two_expected) in [(r.source(), expected_two.0), (r.target(), expected_two.1)] {
            let adapter = Adapter::new(model);
            let classes = model.classes().unwrap();
            assert_eq!(
                reference::brute_force_jac_order_via_lpoly(&adapter.curve),
                BigUint::from(classes.len())
            );
            let mut two = 0;
            for (i, d) in classes.iter().enumerate() {
                let a = adapter.convert(d);
                if a.checked_neg(&adapter.curve).unwrap() == a {
                    two += 1;
                }
                let h = &classes[(7919 * i + 37) % classes.len()];
                assert_eq!(
                    a.checked_add(&adapter.convert(h), &adapter.curve).unwrap(),
                    adapter.convert(&d.add(h).unwrap())
                );
                let composed = if model == r.source() {
                    r.dual(&r.transfer(d).unwrap()).unwrap()
                } else {
                    r.transfer(&r.dual(d).unwrap()).unwrap()
                };
                assert_eq!(
                    a.checked_add(&a, &adapter.curve).unwrap(),
                    adapter.convert(&composed)
                );
            }
            assert_eq!(two, two_expected);
            let mut orders = vec![];
            for projection in [Projection::First, Projection::Second] {
                let order = elliptic_order(prime, model.elliptic_coefficients(projection).unwrap());
                assert_eq!(order, model.elliptic_points(projection).unwrap().len());
                orders.push(order);
            }
            println!("PASS BigUint family p={prime}, root={}, #J={}, self-inverse={two}, independent elliptic orders={orders:?}; all paired additions and dual norm",model.root(),classes.len());
        }
    }
}
