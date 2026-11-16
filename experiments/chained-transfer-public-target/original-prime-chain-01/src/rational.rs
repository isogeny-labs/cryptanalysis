//! Literal original elliptic composition/residual/evaluation helpers.
use isogeny_algos::{
    curve::{self, Curve, Pt, RatIsogeny},
    field::Field,
    find::divpoly::division_poly,
    fpr::{FpR, ER},
    poly::{self, Poly},
};
use serde_json::{json, Value};
include!("../generated/encoding.rs");
include!("../generated/polynomial.rs");
include!("../generated/rational.rs");
include!("../generated/curve_residual.rs");
include!("../generated/eval_rational.rs");
fn input(v: &Value) -> Rational {
    let coefficients = |name: &str| {
        let a: Vec<[u64; 3]> = serde_json::from_value(v[name].clone()).unwrap();
        assert!(a.iter().flatten().all(|&x| x < 223));
        a.into_iter().map(er).collect()
    };
    Rational {
        xn: coefficients("x_num"),
        xd: coefficients("x_den"),
        yn: coefficients("y_multiplier_num"),
        yd: coefficients("y_multiplier_den"),
    }
}
pub struct Maps {
    maps: [[Option<Rational>; 3]; 3],
    pub certificates: Value,
}
impl Maps {
    pub fn new(curves: &[Curve<ER>; 3], f: &FpR, third: &Value, fourth: &Value) -> Self {
        let first = input(&third["third_forward"]);
        let first_dual = input(&third["third_actual_dual"]);
        let second = input(&fourth["fourth_forward"]);
        let second_dual = input(&fourth["fourth_actual_dual"]);
        let composite = second.after(f, &first);
        let composite_dual = first_dual.after(f, &second_dual);
        let mut certificates = Vec::new();
        for (from, to, prior, map) in [
            (0, 2, &first, &composite),
            (2, 0, &second_dual, &composite_dual),
        ] {
            assert_eq!((poly::deg(f, &map.xn), poly::deg(f, &map.xd)), (169, 168));
            let coprime = poly::gcd(f, &map.xn, &map.xd);
            assert_eq!(coprime, vec![f.one()]);
            let residual = rational_curve_residual(f, &curves[from], &curves[to], map);
            assert!(residual.is_empty());
            let derivative = derivative_numerator(f, &map.xn, &map.xd);
            assert!(!derivative.is_empty());
            let psi = square(f, &division_poly(f, &curves[from], 13));
            let intersection = poly::monic(f, &poly::gcd(f, &map.xd, &psi));
            assert_eq!(poly::deg(f, &intersection), 12);
            assert_eq!(intersection, poly::monic(f, &prior.xd));
            let badmap = Rational {
                xn: poly::add(f, &map.xn, &vec![f.one()]),
                xd: map.xd.clone(),
                yn: map.yn.clone(),
                yd: map.yd.clone(),
            };
            let bad_map_residual = rational_curve_residual(f, &curves[from], &curves[to], &badmap);
            assert!(!bad_map_residual.is_empty());
            let altered = Curve::new(curves[to].a, f.add(curves[to].b, f.one()));
            let bad = rational_curve_residual(f, &curves[from], &altered, map);
            assert!(!bad.is_empty());
            certificates.push(json!({"from":from,"to":to,"whole_composite":map.json(),"whole_coprime":coefficients(&coprime),"whole_curve_residual":coefficients(&residual),"whole_derivative":coefficients(&derivative),"whole_psi13_squared":coefficients(&psi),"whole_nondual_intersection":coefficients(&intersection),"altered_target_residual":coefficients(&bad),"altered_map_residual":coefficients(&bad_map_residual),"scope":"actual elliptic169 map certificate; no geometric Jacobian norm13 claim or28561 expansion"}));
        }
        let mut maps = std::array::from_fn(|_| std::array::from_fn(|_| None));
        for (from, to, map) in [
            (0, 1, first),
            (1, 0, first_dual),
            (1, 2, second),
            (2, 1, second_dual),
            (0, 2, composite),
            (2, 0, composite_dual),
        ] {
            maps[from][to] = Some(map)
        }
        Self {
            maps,
            certificates: json!(certificates),
        }
    }
    pub fn eval(
        &self,
        f: &FpR,
        source: &Curve<ER>,
        target: &Curve<ER>,
        from: usize,
        to: usize,
        p: Pt<ER>,
    ) -> Pt<ER> {
        eval_rational(f, source, target, self.maps[from][to].as_ref().unwrap(), p)
    }
}
