//! Actual odd source isogeny, prospective protocol e9234b before implementation.
//! Field, polynomial, division-polynomial, Kohel, SEA and group engines are original.
#![allow(dead_code, static_mut_refs)]
use chained_n4_public_target::{ghs::EP, CheckedInstance};
use isogeny_algos::{
    curve::{self, Curve, Isogeny, Pt, RatIsogeny},
    field::{Field, Rng},
    find::{divpoly::division_poly, sea::elkies_eigenvalue},
    fpr::{FpR, ER},
    kernel::kohel::kohel,
    poly::{self, Poly},
};
use serde_json::{json, Value};

fn er(x: [u64; 3]) -> ER {
    let mut a = [0; 16];
    a[..3].copy_from_slice(&x);
    a
}
fn three(x: ER) -> [u64; 3] {
    assert!(x[3..].iter().all(|&v| v == 0));
    x[..3].try_into().unwrap()
}
fn coefficients(p: &Poly<FpR>) -> Vec<[u64; 3]> {
    p.iter().copied().map(three).collect()
}
fn point(p: Pt<ER>) -> Value {
    match p {
        Pt::Inf => Value::Null,
        Pt::Aff(x, y) => json!([three(x), three(y)]),
    }
}
fn equation(e: &Curve<ER>) -> Value {
    json!({"a":three(e.a),"b":three(e.b)})
}
fn digest(v: &Value) -> String {
    ghs_original_engines::digest::sha256(&serde_json::to_vec(v).unwrap())
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}
fn cubic(f: &FpR, e: &Curve<ER>) -> Poly<FpR> {
    vec![e.b, e.a, f.zero(), f.one()]
}
fn square(f: &FpR, p: &Poly<FpR>) -> Poly<FpR> {
    poly::mul(f, p, p)
}
fn quotient(f: &FpR, a: &Poly<FpR>, b: &Poly<FpR>) -> Poly<FpR> {
    let (q, r) = poly::divrem(f, a, b);
    assert!(r.is_empty());
    q
}
fn derivative_numerator(f: &FpR, n: &Poly<FpR>, d: &Poly<FpR>) -> Poly<FpR> {
    poly::sub(
        f,
        &poly::mul(f, &poly::derivative(f, n), d),
        &poly::mul(f, n, &poly::derivative(f, d)),
    )
}
fn identity_residual(f: &FpR, map: &RatIsogeny<FpR>) -> Poly<FpR> {
    let t = derivative_numerator(f, &map.num, &map.den);
    let left = poly::mul(f, &cubic(f, &map.dom), &square(f, &t));
    let d2 = square(f, &map.den);
    let d3 = poly::mul(f, &d2, &map.den);
    let d4 = square(f, &d2);
    let n3 = poly::mul(f, &square(f, &map.num), &map.num);
    let right = poly::add(
        f,
        &poly::add(
            f,
            &poly::mul(f, &n3, &map.den),
            &poly::scale(f, &poly::mul(f, &map.num, &d3), map.cod.a),
        ),
        &poly::scale(f, &d4, map.cod.b),
    );
    poly::sub(f, &left, &right)
}

/// Common-degree homogeneous substitution, with original polynomial operations.
fn homogeneous(f: &FpR, a: &Poly<FpR>, n: &Poly<FpR>, d: &Poly<FpR>, degree: usize) -> Poly<FpR> {
    assert!(a.len() <= degree + 1);
    let mut r = poly::constant(f, a.get(degree).copied().unwrap_or(f.zero()));
    let mut dp = poly::constant(f, f.one());
    for i in (0..degree).rev() {
        dp = poly::mul(f, &dp, d);
        r = poly::add(
            f,
            &poly::mul(f, &r, n),
            &poly::scale(f, &dp, a.get(i).copied().unwrap_or(f.zero())),
        );
    }
    r
}

#[derive(Clone)]
struct Rational {
    xn: Poly<FpR>,
    xd: Poly<FpR>,
    yn: Poly<FpR>,
    yd: Poly<FpR>,
}
impl Rational {
    fn normalized(f: &FpR, map: &RatIsogeny<FpR>) -> Self {
        Self {
            xn: map.num.clone(),
            xd: map.den.clone(),
            yn: derivative_numerator(f, &map.num, &map.den),
            yd: square(f, &map.den),
        }
    }
    fn scaled(&self, f: &FpR, sx: ER, sy: ER) -> Self {
        Self {
            xn: poly::scale(f, &self.xn, sx),
            xd: self.xd.clone(),
            yn: poly::scale(f, &self.yn, sy),
            yd: self.yd.clone(),
        }
    }
    fn after(&self, f: &FpR, first: &Self) -> Self {
        let dx = self.xn.len().max(self.xd.len()) - 1;
        let dy = self.yn.len().max(self.yd.len()) - 1;
        Self {
            xn: homogeneous(f, &self.xn, &first.xn, &first.xd, dx),
            xd: homogeneous(f, &self.xd, &first.xn, &first.xd, dx),
            yn: poly::mul(
                f,
                &first.yn,
                &homogeneous(f, &self.yn, &first.xn, &first.xd, dy),
            ),
            yd: poly::mul(
                f,
                &first.yd,
                &homogeneous(f, &self.yd, &first.xn, &first.xd, dy),
            ),
        }
    }
    fn json(&self) -> Value {
        json!({"x_num":coefficients(&self.xn),"x_den":coefficients(&self.xd),
            "y_multiplier_num":coefficients(&self.yn),"y_multiplier_den":coefficients(&self.yd)})
    }
}
fn multiplication_13(f: &FpR, e: &Curve<ER>) -> Rational {
    let g13 = division_poly(f, e, 13);
    assert_eq!(g13.last().copied(), Some(f.from_u64(13)));
    let xd = square(f, &g13);
    let xn = poly::sub(
        f,
        &poly::mul(f, &poly::x_poly(f), &xd),
        &poly::scale(
            f,
            &poly::mul(
                f,
                &cubic(f, e),
                &poly::mul(f, &division_poly(f, e, 12), &division_poly(f, e, 14)),
            ),
            f.from_u64(4),
        ),
    );
    let yn = poly::scale(f, &derivative_numerator(f, &xn, &xd), f.inv(f.from_u64(13)));
    Rational {
        xn,
        yn,
        yd: square(f, &xd),
        xd,
    }
}
fn compare_rationals(f: &FpR, a: &Rational, b: &Rational) -> Value {
    let rx = poly::sub(f, &poly::mul(f, &a.xn, &b.xd), &poly::mul(f, &b.xn, &a.xd));
    let ry = poly::sub(f, &poly::mul(f, &a.yn, &b.yd), &poly::mul(f, &b.yn, &a.yd));
    assert!(rx.is_empty(), "whole x-composition identity failed");
    assert!(ry.is_empty(), "whole y-composition identity failed");
    assert_eq!(poly::deg(f, &a.xn), 169);
    assert_eq!(poly::deg(f, &a.xd), 168);
    assert_eq!(poly::gcd(f, &a.xn, &a.xd), vec![f.one()]);
    json!({"actual":a.json(),"multiplication13":b.json(),
        "whole_x_cross_residual":coefficients(&rx),"whole_y_cross_residual":coefficients(&ry),
        "coprime":true,"degrees":[169,168]})
}

fn kernel_data(f: &FpR, e: &Curve<ER>, eigenvalue: u64) -> (Poly<FpR>, Value) {
    let raw = division_poly(f, e, 13);
    let psi = poly::monic(f, &raw);
    assert_eq!(poly::deg(f, &psi), 84);
    assert_eq!(
        poly::gcd(f, &psi, &poly::derivative(f, &psi)),
        vec![f.one()]
    );
    let x = poly::x_poly(f);
    let mut power = x.clone();
    let mut rows = vec![];
    let mut d3 = vec![];
    let mut d6 = vec![];
    for i in 1..=6 {
        power = poly::powmod(f, &power, f.size(), &psi);
        let d = poly::gcd(f, &psi, &poly::sub(f, &power, &x));
        assert_eq!(poly::deg(f, &d), [0, 0, 6, 0, 0, 12][i - 1]);
        if i == 3 {
            d3 = d.clone();
        }
        if i == 6 {
            d6 = d.clone();
        }
        rows.push(
            json!({"power":i,"x_q_power_mod_psi":coefficients(&power),"gcd":coefficients(&d)}),
        );
    }
    let h = if eigenvalue == 2 {
        quotient(f, &d6, &d3)
    } else {
        d3.clone()
    };
    assert_eq!(poly::deg(f, &h), 6);
    assert_eq!(poly::gcd(f, &h, &poly::derivative(f, &h)), vec![f.one()]);
    assert_eq!(elkies_eigenvalue(f, e, &h, 13), Some(eigenvalue));
    let mut xp = x.clone();
    let mut rationality = vec![];
    for i in 1..=6 {
        xp = poly::powmod(f, &xp, f.size(), &h);
        let d = poly::gcd(f, &h, &poly::sub(f, &xp, &x));
        let wanted = if i % (if eigenvalue == 2 { 6 } else { 3 }) == 0 {
            6
        } else {
            0
        };
        assert_eq!(poly::deg(f, &d), wanted);
        rationality.push(json!({"power":i,"gcd":coefficients(&d)}));
    }
    let info = json!({"raw_psi13":coefficients(&raw),"monic_psi13":coefficients(&psi),
        "all_six_Frobenius_steps":rows,"d3":coefficients(&d3),"d6":coefficients(&d6),
        "kernel":coefficients(&h),"SEA_eigenvalue":eigenvalue,"kernel_Frobenius_powers":rationality});
    (h, info)
}

pub struct OddSourceIsogeny {
    field: FpR,
    forward: RatIsogeny<FpR>,
    normalized_dual: RatIsogeny<FpR>,
    inverse_13_squared: ER,
    inverse_13_cubed: ER,
    pub certificate: Value,
}
impl OddSourceIsogeny {
    pub fn construct(c: &CheckedInstance) -> Self {
        c.check_field_basis().unwrap();
        let f = &c.independent_field;
        let e = &c.independent_curve;
        assert_eq!(f.size(), 223u128.pow(3));
        assert_eq!((f.size() + 1) as i128 - c.inst.order as i128, -2724);
        assert_eq!(f.size() % 13, 8);
        assert_eq!((-2724_i64).rem_euclid(13), 6);
        assert_eq!(c.inst.order % 13, 3);
        for lambda in [2u64, 4] {
            assert_eq!((lambda * lambda + 13 - 6 * lambda % 13 + 8) % 13, 0);
        }
        let (h, kernel) = kernel_data(f, e, 2);
        let forward = kohel(f, e, &h, 13);
        assert!(curve::is_smooth(f, &forward.cod));
        let (hd, dual_kernel) = kernel_data(f, &forward.cod, 4);
        let normalized_dual = kohel(f, &forward.cod, &hd, 13);
        for map in [&forward, &normalized_dual] {
            assert_eq!((poly::deg(f, &map.num), poly::deg(f, &map.den)), (13, 12));
            assert_eq!(poly::gcd(f, &map.num, &map.den), vec![f.one()]);
            assert!(identity_residual(f, map).is_empty());
            let mut wrong = map.clone();
            wrong.cod.b = f.add(wrong.cod.b, f.one());
            assert!(!identity_residual(f, &wrong).is_empty());
        }
        let thirteen = f.from_u64(13);
        assert_eq!(normalized_dual.cod.a, f.mul(f.pow(thirteen, 4), e.a));
        assert_eq!(normalized_dual.cod.b, f.mul(f.pow(thirteen, 6), e.b));
        let inverse_13_squared = f.inv(f.pow(thirteen, 2));
        let inverse_13_cubed = f.inv(f.pow(thirteen, 3));
        let fr = Rational::normalized(f, &forward);
        let dr = Rational::normalized(f, &normalized_dual).scaled(
            f,
            inverse_13_squared,
            inverse_13_cubed,
        );
        let old_comp = compare_rationals(f, &dr.after(f, &fr), &multiplication_13(f, e));
        let new_comp = compare_rationals(f, &fr.after(f, &dr), &multiplication_13(f, &forward.cod));
        let target = equation(&forward.cod);
        let target_id = format!("N4-E13-short-{}", digest(&target));
        let certificate = json!({"field_modulus":[220,0,0,1],"field_tag":c.field_tag,
            "source_quadratic_model":c.model_tag,"source_short":equation(e),"target_short":target,
            "target_id":target_id,"degree":13,"original_order":c.inst.order,"ell":c.inst.ell,
            "forward_kernel":kernel,"normalized_dual_kernel":dual_kernel,
            "forward":fr.json(),"actual_dual":dr.json(),"normalized_dual_codomain":equation(&normalized_dual.cod),
            "source_composition":old_comp,"target_composition":new_comp,
            "both_whole_curve_identity_residuals":[[],[]],"two_wrong_target_coefficients_rejected":true});
        Self {
            field: f.clone(),
            forward,
            normalized_dual,
            inverse_13_squared,
            inverse_13_cubed,
            certificate,
        }
    }
    pub fn source(&self) -> &Curve<ER> {
        &self.forward.dom
    }
    pub fn target(&self) -> &Curve<ER> {
        &self.forward.cod
    }
    pub fn forward(&self, p: Pt<ER>) -> Result<Pt<ER>, String> {
        if !curve::on_curve(&self.field, self.source(), &p) {
            return Err("off source curve".into());
        }
        let q = self.forward.eval(&self.field, &p);
        if !curve::on_curve(&self.field, self.target(), &q) {
            return Err("off target curve".into());
        }
        Ok(q)
    }
    pub fn dual(&self, p: Pt<ER>) -> Result<Pt<ER>, String> {
        if !curve::on_curve(&self.field, self.target(), &p) {
            return Err("off target curve".into());
        }
        let q = match self.normalized_dual.eval(&self.field, &p) {
            Pt::Inf => Pt::Inf,
            Pt::Aff(x, y) => Pt::Aff(
                self.field.mul(x, self.inverse_13_squared),
                self.field.mul(y, self.inverse_13_cubed),
            ),
        };
        if !curve::on_curve(&self.field, self.source(), &q) {
            return Err("off dual source curve".into());
        }
        Ok(q)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn short(c: &CheckedInstance, p: EP) -> Pt<ER> {
        match p {
            EP::Inf => Pt::Inf,
            EP::A(x, y) => Pt::Aff(c.independent_field.add(er(x), er(c.short_shift)), er(y)),
        }
    }
    #[test]
    fn actual_degree13_kernel_maps_duals_and_full_subgroup_transport() {
        let c = CheckedInstance::construct().unwrap();
        let m = OddSourceIsogeny::construct(&c);
        let f = &c.independent_field;
        println!("N4_ODD_SOURCE_MAPS {}", m.certificate);
        let g = short(&c, c.inst.g);
        let gp = m.forward(g).unwrap();
        assert_ne!(gp, Pt::Inf);
        assert_eq!(curve::pmul(f, m.target(), &gp, c.inst.ell as u128), Pt::Inf);
        let mut rng = Rng::new(0x6213);
        let mut torsion = vec![Pt::Inf];
        for x in poly::roots(f, &cubic(f, m.source()), &mut rng) {
            torsion.push(Pt::Aff(x, f.zero()));
        }
        assert_eq!(torsion.len(), 4);
        let mut target_torsion = vec![Pt::Inf];
        for x in poly::roots(f, &cubic(f, m.target()), &mut rng) {
            target_torsion.push(Pt::Aff(x, f.zero()));
        }
        assert_eq!(target_torsion.len(), 4);
        let mut image_torsion = vec![];
        for &t in &torsion {
            assert_eq!(curve::pmul(f, m.source(), &t, 2), Pt::Inf);
            let q = m.forward(t).unwrap();
            assert!(target_torsion.contains(&q));
            assert!(!image_torsion.contains(&q));
            image_torsion.push(q);
            assert_eq!(m.dual(q).unwrap(), t);
        }
        let mut source = vec![];
        for k in [1, 3, 5, 7, 17, 31, 101, c.inst.ell - 2] {
            let kg = curve::pmul(f, m.source(), &g, k as u128);
            for t in &torsion {
                source.push(curve::padd(f, m.source(), &kg, t));
            }
        }
        source.extend(&torsion);
        assert_eq!(source.len(), 36);
        let mut source_rows = vec![];
        for &p in &source {
            let q = m.forward(p).unwrap();
            let back = m.dual(q).unwrap();
            assert_eq!(back, curve::pmul(f, m.source(), &p, 13));
            source_rows.push(json!({"source":point(p),"image":point(q),"dual_image":point(back)}));
        }
        let mut target = vec![Pt::Inf];
        for _ in 0..31 {
            target.push(curve::random_point_f(f, m.target(), &mut rng));
        }
        target.extend(&target_torsion);
        assert_eq!(target.len(), 36);
        let mut target_rows = vec![];
        for &p in &target {
            let q = m.dual(p).unwrap();
            let back = m.forward(q).unwrap();
            assert_eq!(back, curve::pmul(f, m.target(), &p, 13));
            target_rows.push(
                json!({"target":point(p),"dual_image":point(q),"forward_dual_image":point(back)}),
            );
        }
        for i in 0..32 {
            for j in 0..32 {
                assert_eq!(
                    m.forward(curve::padd(f, m.source(), &source[i], &source[j]))
                        .unwrap(),
                    curve::padd(
                        f,
                        m.target(),
                        &m.forward(source[i]).unwrap(),
                        &m.forward(source[j]).unwrap()
                    )
                );
                assert_eq!(
                    m.dual(curve::padd(f, m.target(), &target[i], &target[j]))
                        .unwrap(),
                    curve::padd(
                        f,
                        m.source(),
                        &m.dual(target[i]).unwrap(),
                        &m.dual(target[j]).unwrap()
                    )
                );
            }
        }
        assert!(m.forward(Pt::Aff(f.zero(), f.zero())).is_err());
        assert!(m.dual(Pt::Aff(f.zero(), f.zero())).is_err());
        println!(
            "N4_ODD_SOURCE_POINTS {}",
            json!({"source36":source_rows,"target36":target_rows,"source_E2":torsion.iter().copied().map(point).collect::<Vec<_>>(),"target_E2":target_torsion.iter().copied().map(point).collect::<Vec<_>>(),"source_E2_images":image_torsion.iter().copied().map(point).collect::<Vec<_>>(),"homomorphism_pairs_each":1024,"off_curve_rejections":2,"nonzero_exact_ell_generator_image":point(gp)})
        );
        let public = c
            .parse(include_bytes!("../../fixtures/public-five.json"))
            .unwrap();
        assert_eq!(public.len(), 5);
        let expected: Value =
            serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
                .unwrap();
        let mut public_rows = vec![];
        for (i, p) in public.into_iter().enumerate() {
            let k = expected[i]["original_native_recovered_scalar"]
                .as_u64()
                .unwrap();
            assert!(c.verify_recovered(p, k));
            let q = short(&c, p);
            let image = m.forward(q).unwrap();
            assert_eq!(image, curve::pmul(f, m.target(), &gp, k as u128));
            assert_ne!(image, Pt::Inf);
            assert_eq!(m.dual(image).unwrap(), curve::pmul(f, m.source(), &q, 13));
            public_rows.push(json!({"index":i,"source":point(q),"image":point(image),"known_answer_checked_outside_runtime":k}));
        }
        println!(
            "N4_ODD_SOURCE_PUBLIC {}",
            json!({"all_five":public_rows,"runtime":"coordinates only; expected scalars are test-only outside map inputs"})
        );
        let conjugates = |e: &Curve<ER>| {
            let mut j = curve::jinv(f, e);
            let mut js = vec![];
            for _ in 0..3 {
                js.push(three(j));
                j = f.pow(j, 223);
            }
            assert_eq!(j, er(js[0]));
            js
        };
        let oldj = conjugates(m.source());
        let newj = conjugates(m.target());
        let disjoint = !oldj.iter().any(|x| newj.contains(x));
        println!(
            "N4_ODD_SOURCE_PRODUCT {}",
            json!({"source_j_conjugates":oldj,"target_j_conjugates":newj,"sets_disjoint":disjoint,"interpretation":"retain actual discriminator either way; ppav interpretation written, not a Jacobian construction or cost result","future_chain":"Res(gamma) degree13^3; proposed Jacobian maps expected both52 require separately constructed target maps","scope":"fixed actual source isogeny and exact polynomial compositions; original engines; unsigned; no benchmark or speed claim"})
        );
    }
}
