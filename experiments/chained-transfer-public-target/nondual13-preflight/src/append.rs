// Additive private-helper access after the exact original source prefix.
// Prospective protocol23ab48 was published in cf9ca8f5 before this file.
fn nondual_gate(f: &FpR, first: &RatIsogeny<FpR>, composite: &Rational) -> Value {
    assert_eq!(poly::deg(f, &composite.xn), 169);
    assert_eq!(poly::deg(f, &composite.xd), 168);
    assert_eq!(poly::gcd(f, &composite.xn, &composite.xd), vec![f.one()]);
    let psi_squared = square(f, &division_poly(f, &first.dom, 13));
    let intersection = poly::monic(f, &poly::gcd(f, &composite.xd, &psi_squared));
    let wanted = poly::monic(f, &first.den);
    let accepted = intersection == wanted;
    let record = json!({"composite":composite.json(),"psi13_squared":coefficients(&psi_squared),"actual_gcd":coefficients(&intersection),"first_denominator":coefficients(&wanted),"actual_gcd_degree":poly::deg(f,&intersection),"expected_gcd_degree":12,"accepted_nondual":accepted,"scope":"whole denominator intersection criterion after degree/coprime/curve/separability checks; cyclic geometric kernel interpretation requires written bridges"});
    println!("N4_NONDUAL13_KERNEL_GATE {}", record);
    assert!(
        accepted,
        "old dual must fail actual nondual kernel acceptance"
    );
    record
}

// Direct cleared curve identity for an arbitrary signed rational map.
fn rational_curve_residual(f: &FpR, dom: &Curve<ER>, cod: &Curve<ER>, map: &Rational) -> Poly<FpR> {
    let xd2 = square(f, &map.xd);
    let xd3 = poly::mul(f, &xd2, &map.xd);
    let right_cubic = poly::add(
        f,
        &poly::add(
            f,
            &poly::mul(f, &square(f, &map.xn), &map.xn),
            &poly::scale(f, &poly::mul(f, &map.xn, &xd2), cod.a),
        ),
        &poly::scale(f, &xd3, cod.b),
    );
    poly::sub(
        f,
        &poly::mul(f, &poly::mul(f, &cubic(f, dom), &square(f, &map.yn)), &xd3),
        &poly::mul(f, &right_cubic, &square(f, &map.yd)),
    )
}

pub struct SecondHop {
    first: OddSourceIsogeny,
    second: RatIsogeny<FpR>,
    normalized_second_dual: RatIsogeny<FpR>,
    pub certificate: Value,
}
impl SecondHop {
    pub fn construct(c: &CheckedInstance) -> Self {
        let first = OddSourceIsogeny::construct(c);
        let f = &first.field;
        let e1 = first.target();
        let (h, kernel) = kernel_data(f, e1, 2);
        let old_dual_kernel = poly::monic(f, &first.normalized_dual.ker);
        assert_eq!(poly::gcd(f, &h, &old_dual_kernel), vec![f.one()]);
        let second = kohel(f, e1, &h, 13);
        assert!(curve::is_smooth(f, &second.cod));
        let (hd, dual_kernel) = kernel_data(f, &second.cod, 4);
        let normalized_second_dual = kohel(f, &second.cod, &hd, 13);
        let mut curve_checks = vec![];
        for map in [&second, &normalized_second_dual] {
            assert_eq!((poly::deg(f, &map.num), poly::deg(f, &map.den)), (13, 12));
            assert_eq!(poly::gcd(f, &map.num, &map.den), vec![f.one()]);
            assert!(identity_residual(f, map).is_empty());
            let derivative = derivative_numerator(f, &map.num, &map.den);
            assert!(!derivative.is_empty(), "nonzero separability witness");
            let mut altered = map.clone();
            altered.cod.b = f.add(altered.cod.b, f.one());
            let rejection = identity_residual(f, &altered);
            assert!(!rejection.is_empty());
            curve_checks.push(json!({"domain":equation(&map.dom),"codomain":equation(&map.cod),"kernel":coefficients(&map.ker),"num":coefficients(&map.num),"den":coefficients(&map.den),"whole_curve_residual":[],"derivative_numerator":coefficients(&derivative),"actual_altered_target_nonzero_residual":coefficients(&rejection)}));
        }
        let thirteen = f.from_u64(13);
        assert_eq!(
            normalized_second_dual.cod.a,
            f.mul(f.pow(thirteen, 4), e1.a)
        );
        assert_eq!(
            normalized_second_dual.cod.b,
            f.mul(f.pow(thirteen, 6), e1.b)
        );
        let forward = Rational::normalized(f, &second);
        let dual = Rational::normalized(f, &normalized_second_dual).scaled(
            f,
            first.inverse_13_squared,
            first.inverse_13_cubed,
        );
        let source_composite =
            compare_rationals(f, &dual.after(f, &forward), &multiplication_13(f, e1));
        let target_composite = compare_rationals(
            f,
            &forward.after(f, &dual),
            &multiplication_13(f, &second.cod),
        );
        let first_forward = Rational::normalized(f, &first.forward);
        let composite = forward.after(f, &first_forward);
        let composite_curve_residual =
            rational_curve_residual(f, first.source(), &second.cod, &composite);
        assert!(
            composite_curve_residual.is_empty(),
            "whole composed169 curve identity"
        );
        let composite_derivative = derivative_numerator(f, &composite.xn, &composite.xd);
        assert!(!composite_derivative.is_empty());
        let nondual = nondual_gate(f, &first.forward, &composite);
        let old_dual = Rational::normalized(f, &first.normalized_dual).scaled(
            f,
            first.inverse_13_squared,
            first.inverse_13_cubed,
        );
        let backtrack = old_dual.after(f, &first_forward);
        let psi_squared = square(f, &division_poly(f, first.source(), 13));
        let backtrack_gcd = poly::monic(f, &poly::gcd(f, &backtrack.xd, &psi_squared));
        assert_eq!(poly::deg(f, &backtrack_gcd), 168);
        assert_eq!(backtrack_gcd, poly::monic(f, &psi_squared));
        assert_ne!(backtrack_gcd, poly::monic(f, &first.forward.den));
        let j_conjugates = |e: &Curve<ER>| {
            let mut j = curve::jinv(f, e);
            let mut out = vec![];
            for _ in 0..3 {
                out.push(three(j));
                j = f.pow(j, 223);
            }
            assert_eq!(j, er(out[0]));
            out
        };
        let e0_js = j_conjugates(first.source());
        let e1_js = j_conjugates(e1);
        let e2_js = j_conjugates(&second.cod);
        let certificate = json!({"protocol":"23ab48","field_modulus":[220,0,0,1],"field_tag":c.field_tag,"E0":equation(first.source()),"E1":equation(e1),"E1_id":first.certificate["target_id"],"E2":equation(&second.cod),"E2_id":format!("N4-E13x13-short-{}",digest(&equation(&second.cod))),"first_map":first.certificate,"new_kernel":kernel,"old_dual_kernel":coefficients(&old_dual_kernel),"new_and_old_dual_kernel_gcd":[[1,0,0]],"actual_second_dual_kernel":dual_kernel,"second_forward":forward.json(),"second_actual_dual":dual.json(),"whole_curve_checks":curve_checks,"second_dual_after_forward_13":source_composite,"second_forward_after_dual_13":target_composite,"nondual_composite":nondual,"whole_composite169_curve_residual":coefficients(&composite_curve_residual),"composite169_derivative":coefficients(&composite_derivative),"old_backtrack_gcd":coefficients(&backtrack_gcd),"old_backtrack_gcd_degree":168,"E0_j_conjugates":e0_js,"E1_j_conjugates":e1_js,"E2_j_conjugates":e2_js,"E2_j_intersects_E0":e2_js.iter().any(|x|e0_js.contains(x)),"scope":"actual elliptic phaseA only; j diagnostics do not classify Jacobians; full product64 transport and matched prime-field J2 model not constructed"});
        Self {
            first,
            second,
            normalized_second_dual,
            certificate,
        }
    }
    pub fn source(&self) -> &Curve<ER> {
        &self.second.dom
    }
    pub fn target(&self) -> &Curve<ER> {
        &self.second.cod
    }
    pub fn field(&self) -> &FpR {
        &self.first.field
    }
    pub fn forward(&self, p: Pt<ER>) -> Result<Pt<ER>, String> {
        let f = self.field();
        if !curve::on_curve(f, self.source(), &p) {
            return Err("off second source curve".into());
        }
        let q = self.second.eval(f, &p);
        if !curve::on_curve(f, self.target(), &q) {
            return Err("off second target curve".into());
        }
        Ok(q)
    }
    pub fn dual(&self, p: Pt<ER>) -> Result<Pt<ER>, String> {
        let f = self.field();
        if !curve::on_curve(f, self.target(), &p) {
            return Err("off second dual source curve".into());
        }
        let q = match self.normalized_second_dual.eval(f, &p) {
            Pt::Inf => Pt::Inf,
            Pt::Aff(x, y) => Pt::Aff(
                f.mul(x, self.first.inverse_13_squared),
                f.mul(y, self.first.inverse_13_cubed),
            ),
        };
        if !curve::on_curve(f, self.source(), &q) {
            return Err("off second dual target curve".into());
        }
        Ok(q)
    }
}

pub fn old_dual_backtracking_canary() {
    let c = CheckedInstance::construct().unwrap();
    let first = OddSourceIsogeny::construct(&c);
    let f = &first.field;
    let forward = Rational::normalized(f, &first.forward);
    let dual = Rational::normalized(f, &first.normalized_dual).scaled(
        f,
        first.inverse_13_squared,
        first.inverse_13_cubed,
    );
    nondual_gate(f, &first.forward, &dual.after(f, &forward));
    panic!("backtracking control must not accept");
}

#[cfg(test)]
mod second_hop_tests {
    use super::*;
    fn short(c: &CheckedInstance, p: EP) -> Pt<ER> {
        match p {
            EP::Inf => Pt::Inf,
            EP::A(x, y) => Pt::Aff(c.independent_field.add(er(x), er(c.short_shift)), er(y)),
        }
    }
    fn torsion(f: &FpR, e: &Curve<ER>) -> Vec<Pt<ER>> {
        let mut roots = poly::roots(f, &cubic(f, e), &mut Rng::new(0x2d13));
        roots.sort();
        let mut out = vec![Pt::Inf];
        out.extend(roots.into_iter().map(|x| Pt::Aff(x, f.zero())));
        assert_eq!(out.len(), 4);
        out
    }
    #[test]
    fn all_actual_nondual_elliptic_preflight() {
        let c = CheckedInstance::construct().unwrap();
        let second = SecondHop::construct(&c);
        let f = second.field();
        println!("N4_NONDUAL13_MAPS {}", second.certificate);
        let e0 = second.first.source();
        let e1 = second.source();
        let e2 = second.target();
        let g0 = short(&c, c.inst.g);
        let g1 = second.first.forward(g0).unwrap();
        let g2 = second.forward(g1).unwrap();
        assert_ne!(g2, Pt::Inf);
        assert_eq!(curve::pmul(f, e2, &g2, c.inst.ell as u128), Pt::Inf);
        let t0 = torsion(f, e0);
        let t1 = torsion(f, e1);
        let t2 = torsion(f, e2);
        let images = t1
            .iter()
            .map(|&p| {
                assert_eq!(curve::pmul(f, e1, &p, 2), Pt::Inf);
                let q = second.forward(p).unwrap();
                assert!(t2.contains(&q));
                assert_eq!(second.dual(q).unwrap(), p);
                q
            })
            .collect::<Vec<_>>();
        for (i, image) in images.iter().enumerate() {
            assert!(!images[..i].contains(image));
        }
        let mut source = vec![];
        for k in [1, 3, 5, 7, 17, 31, 101, c.inst.ell - 2] {
            let kg = curve::pmul(f, e0, &g0, k as u128);
            for t in &t0 {
                source.push(second.first.forward(curve::padd(f, e0, &kg, t)).unwrap());
            }
        }
        source.extend(&t1);
        assert_eq!(source.len(), 36);
        let mut source_rows = vec![];
        for &p in &source {
            let q = second.forward(p).unwrap();
            let back = second.dual(q).unwrap();
            assert_eq!(back, curve::pmul(f, e1, &p, 13));
            source_rows.push(json!({"source":point(p),"image":point(q),"dual_image":point(back)}));
        }
        let mut rng = Rng::new(0x16913);
        let mut targets = vec![Pt::Inf];
        for _ in 0..31 {
            targets.push(curve::random_point_f(f, e2, &mut rng));
        }
        targets.extend(&t2);
        assert_eq!(targets.len(), 36);
        let mut target_rows = vec![];
        for &p in &targets {
            let q = second.dual(p).unwrap();
            let back = second.forward(q).unwrap();
            assert_eq!(back, curve::pmul(f, e2, &p, 13));
            target_rows.push(
                json!({"target":point(p),"dual_image":point(q),"forward_dual_image":point(back)}),
            );
        }
        let mut addition_rows = vec![];
        for i in 0..32 {
            for j in 0..32 {
                let source_sum = curve::padd(f, e1, &source[i], &source[j]);
                let image = second.forward(source_sum).unwrap();
                assert_eq!(
                    image,
                    curve::padd(
                        f,
                        e2,
                        &second.forward(source[i]).unwrap(),
                        &second.forward(source[j]).unwrap()
                    )
                );
                let target_sum = curve::padd(f, e2, &targets[i], &targets[j]);
                let dual_image = second.dual(target_sum).unwrap();
                assert_eq!(
                    dual_image,
                    curve::padd(
                        f,
                        e1,
                        &second.dual(targets[i]).unwrap(),
                        &second.dual(targets[j]).unwrap()
                    )
                );
                addition_rows.push(json!({"i":i,"j":j,"source_sum":point(source_sum),"forward_sum":point(image),"target_sum":point(target_sum),"dual_sum":point(dual_image)}));
            }
        }
        println!(
            "N4_NONDUAL13_POINTS {}",
            json!({"all36_source":source_rows,"all36_target":target_rows,"all1024_each_addition_pairs":addition_rows,"source2":t1.iter().copied().map(point).collect::<Vec<_>>(),"target2":t2.iter().copied().map(point).collect::<Vec<_>>(),"actual_gamma2_torsion_images":images.iter().copied().map(point).collect::<Vec<_>>(),"nonzero_prime_ell_image":point(g2),"scope":"four torsion points on each elliptic curve; full64 product/conjugate transport remains phaseB"})
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
            let p0 = short(&c, p);
            let p1 = second.first.forward(p0).unwrap();
            let p2 = second.forward(p1).unwrap();
            assert_ne!(p2, Pt::Inf);
            assert_eq!(p2, curve::pmul(f, e2, &g2, k as u128));
            assert_eq!(curve::pmul(f, e2, &p2, c.inst.ell as u128), Pt::Inf);
            assert_eq!(second.dual(p2).unwrap(), curve::pmul(f, e1, &p1, 13));
            assert_eq!(
                second.first.dual(second.dual(p2).unwrap()).unwrap(),
                curve::pmul(f, e0, &p0, 169)
            );
            public_rows.push(json!({"index":i,"E0":point(p0),"E1":point(p1),"E2":point(p2),"outside_runtime_test_scalar":k}));
        }
        println!(
            "N4_NONDUAL13_PUBLIC {}",
            json!({"all_five":public_rows,"runtime":"coordinates only, no scalar witness or odd DLP table","elliptic_phase_only":true,"matched_prime_field_J2":"not constructed"})
        );
    }
}
