//! Actual rational-lift controls under prospective5be5e0, published3422ccb4.
#![allow(dead_code, static_mut_refs)]
use isogeny_algos::{
    curve::{self, Curve, Pt},
    field::{Field, Rng},
    fpr::{FpR, ER},
    poly,
};
use serde_json::{json, Value};

pub fn lift3(x: ER) -> ER {
    assert!(x[3..].iter().all(|&v| v == 0));
    let mut out = [0; 16];
    for i in 0..3 {
        out[2 * i] = x[i];
    }
    out
}
pub fn frob(f: &FpR, mut x: ER, n: usize) -> ER {
    for _ in 0..n {
        x = f.frobenius(x);
    }
    x
}
pub fn frob_point(f: &FpR, p: Pt<ER>, n: usize) -> Pt<ER> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => Pt::Aff(frob(f, x, n), frob(f, y, n)),
    }
}
pub fn lift_curve(e: &Curve<ER>) -> Curve<ER> {
    Curve {
        a: lift3(e.a),
        b: lift3(e.b),
    }
}
pub fn point_key(p: Pt<ER>) -> Option<(ER, ER)> {
    match p {
        Pt::Inf => None,
        Pt::Aff(x, y) => Some((x, y)),
    }
}
pub fn point_json(p: Pt<ER>) -> Value {
    match p {
        Pt::Inf => Value::Null,
        Pt::Aff(x, y) => json!([&x[..6], &y[..6]]),
    }
}

/// All E[4] by solving the four halves of each nonzero branch point.
/// Roots, square roots and group laws are the original field/curve operations.
pub fn four_torsion(f3: &FpR, f6: &FpR, e3: &Curve<ER>) -> Vec<Pt<ER>> {
    let roots = poly::roots(
        f3,
        &vec![e3.b, e3.a, f3.zero(), f3.one()],
        &mut Rng::new(0x7301),
    );
    assert_eq!(roots.len(), 3, "actual full source E[2]/K required");
    let e6 = lift_curve(e3);
    let roots: Vec<_> = roots.into_iter().map(lift3).collect();
    let mut out = vec![Pt::Inf];
    for i in 0..3 {
        let branch = Pt::Aff(roots[i], f6.zero());
        assert!(curve::on_curve(f6, &e6, &branch));
        assert_eq!(curve::pmul(f6, &e6, &branch, 2), Pt::Inf);
        out.push(branch);
        let d = f6.mul(
            f6.sub(roots[i], roots[(i + 1) % 3]),
            f6.sub(roots[i], roots[(i + 2) % 3]),
        );
        let s = f6.sqrt(d).expect("branch half x-discriminant in actual L");
        assert!(!f6.is_zero(s));
        for dx in [s, f6.neg(s)] {
            let x = f6.add(roots[i], dx);
            let rhs = f6.add(f6.add(f6.mul(f6.sq(x), x), f6.mul(e6.a, x)), e6.b);
            let y = f6.sqrt(rhs).expect("actual branch half y in L");
            assert!(!f6.is_zero(y));
            for yy in [y, f6.neg(y)] {
                let p = Pt::Aff(x, yy);
                assert!(curve::on_curve(f6, &e6, &p));
                assert_eq!(curve::pmul(f6, &e6, &p, 2), branch);
                out.push(p);
            }
        }
    }
    out.sort_by_key(|p| point_key(*p));
    out.dedup();
    assert_eq!(out.len(), 16);
    for p in &out {
        assert_eq!(curve::pmul(f6, &e6, p, 4), Pt::Inf);
    }
    out
}

/// Base-change the actual published rational isogeny certificate, not a DLP table.
pub struct Rational6 {
    xn: Vec<ER>,
    xd: Vec<ER>,
    yn: Vec<ER>,
    yd: Vec<ER>,
}
impl Rational6 {
    pub fn new(v: &Value) -> Self {
        let read = |key: &str| {
            v[key]
                .as_array()
                .unwrap()
                .iter()
                .map(|row| {
                    let a = row.as_array().unwrap();
                    assert_eq!(a.len(), 3);
                    let mut x = [0; 16];
                    for i in 0..3 {
                        x[i] = a[i].as_u64().unwrap();
                        assert!(x[i] < 223);
                    }
                    lift3(x)
                })
                .collect()
        };
        Self {
            xn: read("x_num"),
            xd: read("x_den"),
            yn: read("y_multiplier_num"),
            yd: read("y_multiplier_den"),
        }
    }
    pub fn eval(&self, f: &FpR, p: Pt<ER>) -> Pt<ER> {
        match p {
            Pt::Inf => Pt::Inf,
            Pt::Aff(x, y) => {
                let xd = poly::eval(f, &self.xd, x);
                let yd = poly::eval(f, &self.yd, x);
                assert!(
                    !f.is_zero(xd) && !f.is_zero(yd),
                    "four-torsion is coprime to degree13 kernel"
                );
                Pt::Aff(
                    f.div(poly::eval(f, &self.xn, x), xd),
                    f.mul(y, f.div(poly::eval(f, &self.yn, x), yd)),
                )
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chained_n4_odd_source::OddSourceIsogeny;
    use chained_n4_public_target::CheckedInstance;

    #[test]
    fn actual_four_torsion_and_frobenius_hypothesis_controls() {
        let c = CheckedInstance::construct().unwrap();
        let iso = OddSourceIsogeny::construct(&c);
        let f3 = &c.independent_field;
        let f6 = FpR::new(223, 6);
        let mut w = [0; 16];
        w[1] = 1;
        assert_eq!(f6.pow(w, 6), f6.from_u64(3));
        let v = f6.pow(w, 3);
        assert_eq!(f6.sq(v), f6.from_u64(3));
        assert_eq!(frob(&f6, v, 2), v);
        assert_ne!(frob(&f6, v, 1), v);
        let gamma = Rational6::new(&iso.certificate["forward"]);
        let delta = Rational6::new(&iso.certificate["actual_dual"]);
        let mut panels = vec![];
        let all: Vec<_> = [iso.source(), iso.target()]
            .iter()
            .map(|e| four_torsion(f3, &f6, e))
            .collect();
        for (side, e3) in [iso.source(), iso.target()].into_iter().enumerate() {
            let e6 = lift_curve(e3);
            let points = &all[side];
            let mut rows = vec![];
            let mut naive_offcurve = 0;
            for p in points {
                let fp = frob_point(&f6, *p, 3);
                assert!(curve::on_curve(&f6, &e6, &fp));
                assert!(points.contains(&fp));
                assert_eq!(frob_point(&f6, *p, 6), *p);
                let doubled = curve::pmul(&f6, &e6, p, 2);
                assert_eq!(frob_point(&f6, doubled, 3), doubled);
                if !curve::on_curve(&f6, &e6, &frob_point(&f6, *p, 1)) {
                    naive_offcurve += 1;
                }
                let image = if side == 0 {
                    gamma.eval(&f6, *p)
                } else {
                    delta.eval(&f6, *p)
                };
                assert!(all[1 - side].contains(&image));
                let back = if side == 0 {
                    delta.eval(&f6, image)
                } else {
                    gamma.eval(&f6, image)
                };
                assert_eq!(back, curve::pmul(&f6, &e6, p, 13));
                rows.push(json!({"point":point_json(*p),"double":point_json(doubled),"base_Frobenius_F3":point_json(fp),"odd_isogeny_image":point_json(image),"both_composition_13":true}));
            }
            assert!(
                naive_offcurve > 0,
                "mutation control: coordinateF does not preserve this K curve"
            );
            let mut addition = vec![];
            for p in points {
                for q in points {
                    let sum = curve::padd(&f6, &e6, p, q);
                    let index = points.iter().position(|x| *x == sum).unwrap();
                    addition.push(index);
                    let (mp, mq, ms) = if side == 0 {
                        (
                            gamma.eval(&f6, *p),
                            gamma.eval(&f6, *q),
                            gamma.eval(&f6, sum),
                        )
                    } else {
                        (
                            delta.eval(&f6, *p),
                            delta.eval(&f6, *q),
                            delta.eval(&f6, sum),
                        )
                    };
                    assert_eq!(
                        curve::padd(
                            &f6,
                            &lift_curve([iso.target(), iso.source()][side]),
                            &mp,
                            &mq
                        ),
                        ms
                    );
                }
            }
            panels.push(json!({"side":side,"a":&e3.a[..3],"b":&e3.b[..3],"all16_points":rows,"all256_addition_table":addition,"naive_coordinate_F_offcurve_count":naive_offcurve,"F3_is_the_base_Frobenius":true,"all16_four_torsion_and_both13_compositions":true}));
        }
        println!(
            "N4_BETA_ACTUAL_E4 {}",
            json!({"q":223,"K_modulus":[220,0,0,1],"L_modulus":[220,0,0,0,0,0,1],"K_embedding":"z=w^2","quadratic_subfield":"v=w^3,v^2=3","ell":c.inst.ell,"source_order":c.inst.order,"panels":panels,"scope":"actual finite coordinates and subgroup maps; no Picard-basechange/beta coordinates yet"})
        );
        let add = |a: (u32, u32), b: (u32, u32)| ((a.0 + b.0) % 4, (a.1 + b.1) % 2);
        let f = |a: (u32, u32)| ((a.0 + 2 * a.1) % 4, (a.1 + a.0) % 2);
        let elems: Vec<_> = (0..4).flat_map(|a| (0..2).map(move |b| (a, b))).collect();
        let mut images = vec![];
        let mut bad_kernel = vec![];
        for a in &elems {
            assert!(elems.contains(&f(*a)));
            images.push(f(*a));
            for b in &elems {
                assert_eq!(f(add(*a, *b)), add(f(*a), f(*b)));
                assert_eq!(add(*a, *b).0 % 2, (a.0 % 2 + b.0 % 2) % 2);
            }
            assert_eq!(f(*a).0 % 2, a.0 % 2);
            if a.0 % 2 == 0 {
                assert_eq!(add(*a, *a), (0, 0));
                if f(f(f(*a))) != *a {
                    bad_kernel.push(*a);
                }
            } else {
                assert_ne!(f(f(*a)), *a);
            }
        }
        images.sort();
        images.dedup();
        assert_eq!(images.len(), 8);
        assert!(!bad_kernel.is_empty());
        println!(
            "N4_BETA_KERNEL_HYPOTHESIS_CONTROL {}",
            json!({"source":"C4xC2","phi":"a mod2","F":"(a+2b mod4,b+a mod2)","all8_source_points":elems,"kernel_F3_counterexamples":bad_kernel,"all4_lifts_of_nonzero_target_reject_F2_fixed":true,"scope":"abstract finite-group control only, not abelian-variety counterexample"})
        );
    }
}
