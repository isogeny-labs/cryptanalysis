//! Literal original composition and curve-residual bodies, plus typed inputs.
use chained_n4_beta_rational_lift::Rational6;
use chained_n4_fixed_jacobian_chain::FixedGeometry;
use isogeny_algos::{
    curve::{Curve, Pt, RatIsogeny},
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

fn input(v: &Value) -> Rational {
    let coefficients = |name: &str| {
        let values: Vec<[u64; 3]> = serde_json::from_value(v[name].clone()).unwrap();
        assert!(values.iter().flatten().all(|&x| x < 223));
        values.into_iter().map(er).collect()
    };
    Rational {
        xn: coefficients("x_num"),
        xd: coefficients("x_den"),
        yn: coefficients("y_multiplier_num"),
        yd: coefficients("y_multiplier_den"),
    }
}

pub fn prepare(geometry: &FixedGeometry) -> ([[Option<Rational6>; 3]; 3], Value) {
    let pair = &geometry.map_certificates["pair"];
    let fourth = &geometry.map_certificates["fourth"];
    let first = input(&pair["whole_rational_checks"][0]["map"]);
    let first_dual = input(&pair["whole_rational_checks"][1]["map"]);
    let second = input(&fourth["twist_fourth_forward"]);
    let second_dual = input(&fourth["twist_fourth_actual_dual"]);
    let f = geometry.models[0].source.field();
    let composite = second.after(f, &first);
    let composite_dual = first_dual.after(f, &second_dual);
    let mut records = Vec::new();
    for (source, target, prior, map) in [
        (0, 2, &first, &composite),
        (2, 0, &second_dual, &composite_dual),
    ] {
        let e = geometry.models[source].source.curve();
        let target_ec = geometry.models[target].source.curve();
        assert_eq!((poly::deg(f, &map.xn), poly::deg(f, &map.xd)), (169, 168));
        let coprime = poly::gcd(f, &map.xn, &map.xd);
        assert_eq!(coprime, vec![f.one()]);
        let residual = rational_curve_residual(f, e, target_ec, map);
        assert!(residual.is_empty());
        let derivative = derivative_numerator(f, &map.xn, &map.xd);
        assert!(!derivative.is_empty());
        let psi_squared = square(f, &division_poly(f, e, 13));
        let intersection = poly::monic(f, &poly::gcd(f, &map.xd, &psi_squared));
        let wanted = poly::monic(f, &prior.xd);
        assert_eq!(poly::deg(f, &intersection), 12);
        assert_eq!(intersection, wanted);
        let altered = Curve::new(target_ec.a, f.add(target_ec.b, f.one()));
        let bad_residual = rational_curve_residual(f, e, &altered, map);
        assert!(!bad_residual.is_empty());
        records.push(json!({"source":source,"target":target,"whole_composite":map.json(),"whole_curve_residual":coefficients(&residual),"actual_coprime":coefficients(&coprime),"whole_derivative":coefficients(&derivative),"whole_psi13_squared":coefficients(&psi_squared),"whole_actual_intersection":coefficients(&intersection),"whole_previous_denominator":coefficients(&wanted),"actual_altered_target_residual":coefficients(&bad_residual),"scope":"actual degree169 composite and nondual polynomial certificate; no degree28561 multiplication expansion"}));
    }
    let mut maps = std::array::from_fn(|_| std::array::from_fn(|_| None));
    for (from, to, map) in [
        (0, 1, &first),
        (1, 0, &first_dual),
        (1, 2, &second),
        (2, 1, &second_dual),
        (0, 2, &composite),
        (2, 0, &composite_dual),
    ] {
        maps[from][to] = Some(Rational6::new(&map.json()));
    }
    (maps, json!(records))
}
