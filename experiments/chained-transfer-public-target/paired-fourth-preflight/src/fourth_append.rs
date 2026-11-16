// Prospective PAIRED_FOURTH_EDGE_PROTOCOL_01, publishedfa3c50b5 before this code.
fn fourth_kernel_gate(f: &FpR, previous: &RatIsogeny<FpR>, composite: &Rational) -> Value {
    assert_eq!(
        (poly::deg(f, &composite.xn), poly::deg(f, &composite.xd)),
        (169, 168)
    );
    assert_eq!(poly::gcd(f, &composite.xn, &composite.xd), vec![f.one()]);
    let psi = square(f, &division_poly(f, &previous.dom, 13));
    let intersection = poly::monic(f, &poly::gcd(f, &composite.xd, &psi));
    let wanted = poly::monic(f, &previous.den);
    let accepted = intersection == wanted;
    let record = json!({"protocol":"paired-fourth01","composite":composite.json(),"psi13_squared":coefficients(&psi),"psi13_squared_monic":coefficients(&poly::monic(f,&psi)),"actual_gcd":coefficients(&intersection),"previous_forward_denominator":coefficients(&wanted),"actual_gcd_degree":poly::deg(f,&intersection),"expected_gcd_degree":12,"accepted_nondual":accepted,"scope":"actual middle169 denominator intersection; cyclic group-scheme interpretation remains a written bridge"});
    println!("N4_FOURTH_KERNEL_GATE {}", record);
    assert!(
        accepted,
        "actual old third dual must fail fourth-edge acceptance"
    );
    record
}

fn checked_fourth_pair(
    f: &FpR,
    dom: &Curve<ER>,
    cod: &Curve<ER>,
    forward: &Rational,
    dual: &Rational,
    kernel: &Poly<FpR>,
    dual_kernel: &Poly<FpR>,
    eigenvalues: [u64; 2],
) -> Value {
    let mut identities = vec![];
    for (a, b, map, h, expected) in [
        (dom, cod, forward, kernel, eigenvalues[0]),
        (cod, dom, dual, dual_kernel, eigenvalues[1]),
    ] {
        assert!(curve::is_smooth(f, a) && curve::is_smooth(f, b));
        assert_eq!((poly::deg(f, &map.xn), poly::deg(f, &map.xd)), (13, 12));
        assert_eq!(poly::gcd(f, &map.xn, &map.xd), vec![f.one()]);
        let residual = rational_curve_residual(f, a, b, map);
        assert!(residual.is_empty());
        let derivative = derivative_numerator(f, &map.xn, &map.xd);
        assert!(!derivative.is_empty());
        let eigenvalue = elkies_eigenvalue(f, a, h, 13);
        assert_eq!(eigenvalue, Some(expected));
        let altered = Curve::new(b.a, f.add(b.b, f.one()));
        let bad = rational_curve_residual(f, a, &altered, map);
        assert!(!bad.is_empty());
        identities.push(json!({"domain":equation(a),"codomain":equation(b),"map":map.json(),"kernel":coefficients(h),"whole_curve_residual":coefficients(&residual),"derivative_numerator":coefficients(&derivative),"actual_SEA_eigenvalue":eigenvalue,"actual_altered_target_nonzero_residual":coefficients(&bad)}));
    }
    let left = compare_rationals(f, &dual.after(f, forward), &multiplication_13(f, dom));
    let right = compare_rationals(f, &forward.after(f, dual), &multiplication_13(f, cod));
    json!({"all_whole_identities":identities,"dual_after_forward13":left,"forward_after_dual13":right})
}

pub struct PairedFourth<'a> {
    pair: &'a TwistedPair,
    original: RatIsogeny<FpR>,
    forward: Rational,
    dual: Rational,
    twist: RatIsogeny<FpR>,
    twist_forward: Rational,
    twist_dual: Rational,
    original_source_generator: Pt<ER>,
    original_target_generator: Pt<ER>,
    twist_target_generator: Pt<ER>,
    pub certificate: Value,
}
impl<'a> PairedFourth<'a> {
    pub fn construct(c: &CheckedInstance, pair: &'a TwistedPair) -> Self {
        let f = pair.field();
        let previous = &pair.old.third;
        let (h, kernel_data_record) = kernel_data(f, pair.old_target(), 2);
        let old_dual_kernel = poly::monic(f, &pair.old.normalized_third_dual.ker);
        assert_eq!(poly::gcd(f, &h, &old_dual_kernel), vec![f.one()]);
        let original = kohel(f, pair.old_target(), &h, 13);
        let (hd, dual_kernel_record) = kernel_data(f, &original.cod, 4);
        let reverse = kohel(f, &original.cod, &hd, 13);
        let thirteen = f.from_u64(13);
        let inv2 = f.inv(f.pow(thirteen, 2));
        let inv3 = f.inv(f.pow(thirteen, 3));
        assert_eq!(reverse.cod.a, f.mul(f.pow(thirteen, 4), original.dom.a));
        assert_eq!(reverse.cod.b, f.mul(f.pow(thirteen, 6), original.dom.b));
        let forward = Rational::normalized(f, &original);
        let dual = Rational::normalized(f, &reverse).scaled(f, inv2, inv3);
        let original_checks = checked_fourth_pair(
            f,
            &original.dom,
            &original.cod,
            &forward,
            &dual,
            &h,
            &hd,
            [2, 4],
        );
        let middle = forward.after(f, &Rational::normalized(f, previous));
        let residual = rational_curve_residual(f, &previous.dom, &original.cod, &middle);
        assert!(residual.is_empty());
        let derivative = derivative_numerator(f, &middle.xn, &middle.xd);
        assert!(!derivative.is_empty());
        let nondual = fourth_kernel_gate(f, previous, &middle);
        let old_dual =
            Rational::normalized(f, &pair.old.normalized_third_dual).scaled(f, inv2, inv3);
        let backtrack = old_dual.after(f, &Rational::normalized(f, previous));
        let psi = square(f, &division_poly(f, &previous.dom, 13));
        let backtrack_gcd = poly::monic(f, &poly::gcd(f, &backtrack.xd, &psi));
        assert_eq!(poly::deg(f, &backtrack_gcd), 168);
        assert_eq!(backtrack_gcd, poly::monic(f, &psi));
        let v = f.from_u64(12);
        let twist_target = Curve::new(
            f.mul(f.pow(v, 2), original.cod.a),
            f.mul(f.pow(v, 3), original.cod.b),
        );
        let ht = poly::monic(f, &scaled_argument(f, &h, f.inv(v)));
        let hdt = poly::monic(f, &scaled_argument(f, &hd, f.inv(v)));
        let twist = kohel(f, pair.target(), &ht, 13);
        assert_eq!(twist.cod, twist_target);
        let twist_reverse = kohel(f, &twist.cod, &hdt, 13);
        assert_eq!(twist_reverse.cod.a, f.mul(f.pow(thirteen, 4), twist.dom.a));
        assert_eq!(twist_reverse.cod.b, f.mul(f.pow(thirteen, 6), twist.dom.b));
        let twist_forward = Rational::normalized(f, &twist);
        let twist_dual = Rational::normalized(f, &twist_reverse).scaled(f, inv2, inv3);
        let recipe_forward =
            compare_degree13_recipe(f, &twist_forward, &twist_rational(f, &forward, v));
        let recipe_dual = compare_degree13_recipe(f, &twist_dual, &twist_rational(f, &dual, v));
        let twist_checks = checked_fourth_pair(
            f,
            &twist.dom,
            &twist.cod,
            &twist_forward,
            &twist_dual,
            &ht,
            &hdt,
            [11, 9],
        );
        let g0 = match c.inst.g {
            EP::Inf => panic!("original nonzero generator required"),
            EP::A(x, y) => Pt::Aff(f.add(er(x), er(c.short_shift)), er(y)),
        };
        let g2 = pair.old.original_to_source(g0).unwrap();
        let original_source_generator = pair.old.forward(g2).unwrap();
        let original_target_generator = original.eval(f, &original_source_generator);
        let twist_target_generator = twist.eval(f, &pair.target_generator);
        let mut certificates = vec![];
        for (class, ec, ell, order, generator) in [
            (
                "original-source",
                &original.dom,
                c.inst.ell,
                c.inst.order,
                original_source_generator,
            ),
            (
                "original-target",
                &original.cod,
                c.inst.ell,
                c.inst.order,
                original_target_generator,
            ),
            (
                "twist-source",
                &twist.dom,
                pair.ell,
                pair.order,
                pair.target_generator,
            ),
            (
                "twist-target",
                &twist.cod,
                pair.ell,
                pair.order,
                twist_target_generator,
            ),
        ] {
            let good = certify_group(f, ec, ell, order, generator).unwrap();
            let wrong_order = certify_group(f, ec, ell, order + 1, generator).unwrap_err();
            let zero_generator = certify_group(f, ec, ell, order, Pt::Inf).unwrap_err();
            certificates.push(json!({"class":class,"actual_certificate":good,"actual_wrong_order_rejection":wrong_order,"actual_zero_generator_rejection":zero_generator}));
        }
        let jorbit = |ec: &Curve<ER>| {
            let j = curve::jinv(f, ec);
            [three(j), three(f.pow(j, 223)), three(f.pow(j, 223 * 223))]
        };
        let previous_curves = [
            pair.old.previous.first.source(),
            pair.old.previous.source(),
            pair.old.source(),
            pair.old.target(),
        ];
        let js = jorbit(&original.cod);
        let orbits = previous_curves.map(jorbit);
        let intersections = orbits.map(|old| js.iter().any(|x| old.contains(x)));
        let certificate = json!({"protocol":"paired-fourth01","original_source":equation(&original.dom),"original_target":equation(&original.cod),"original_target_id":format!("N4-E13x13x13x13-short-{}",digest(&equation(&original.cod))),"twist_source":equation(&twist.dom),"twist_target":equation(&twist.cod),"twist_target_id":format!("N4-nu12-E13x13x13x13-short-{}",digest(&equation(&twist.cod))),"nu":12,"new_kernel":kernel_data_record,"actual_dual_kernel":dual_kernel_record,"old_third_dual_kernel":coefficients(&old_dual_kernel),"new_and_old_dual_kernel_gcd":[[1,0,0]],"fourth_forward":forward.json(),"fourth_actual_dual":dual.json(),"twist_fourth_forward":twist_forward.json(),"twist_fourth_actual_dual":twist_dual.json(),"original_whole_checks":original_checks,"twist_whole_checks":twist_checks,"independent_twisted_forward_recipe":recipe_forward,"independent_twisted_dual_recipe":recipe_dual,"middle169_nondual":nondual,"middle169_whole_curve_residual":coefficients(&residual),"middle169_derivative":coefficients(&derivative),"actual_old_third_dual_backtrack_gcd":coefficients(&backtrack_gcd),"actual_old_third_dual_gcd_degree":168,"all_actual_source_target_order_certificates_and_controls":certificates,"E4_j_conjugates":js,"all_previous_E0_E1_E2_E3_j_orbits":orbits,"E4_j_orbit_intersections":intersections,"scope":"one original fixed fourth edge and exact same-nu12 twist; no whole2197/28561 expansion, Jacobian evaluation, isomorphism classification or performance inference"});
        Self {
            pair,
            original,
            forward,
            dual,
            twist,
            twist_forward,
            twist_dual,
            original_source_generator,
            original_target_generator,
            twist_target_generator,
            certificate,
        }
    }
    pub fn branch(&self, twisted: bool) -> FourthBranch<'_> {
        let (map, forward, dual, generator, ell) = if twisted {
            (
                &self.twist,
                &self.twist_forward,
                &self.twist_dual,
                self.pair.target_generator,
                self.pair.ell,
            )
        } else {
            (
                &self.original,
                &self.forward,
                &self.dual,
                self.original_source_generator,
                2773073,
            )
        };
        FourthBranch {
            field: self.pair.field(),
            map,
            forward_map: forward,
            dual_map: dual,
            generator,
            ell,
            certificate: json!({"new_kernel":{"kernel":coefficients(&map.ker)},"fourth_forward":forward.json()}),
        }
    }
}
pub struct FourthBranch<'a> {
    field: &'a FpR,
    map: &'a RatIsogeny<FpR>,
    forward_map: &'a Rational,
    dual_map: &'a Rational,
    generator: Pt<ER>,
    ell: u64,
    pub certificate: Value,
}
impl FourthBranch<'_> {
    pub fn field(&self) -> &FpR {
        self.field
    }
    pub fn source(&self) -> &Curve<ER> {
        &self.map.dom
    }
    pub fn target(&self) -> &Curve<ER> {
        &self.map.cod
    }
    pub fn forward(&self, p: Pt<ER>) -> Result<Pt<ER>, String> {
        if !curve::on_curve(self.field, self.source(), &p) {
            return Err("off fourth source".into());
        }
        Ok(eval_rational(
            self.field,
            self.source(),
            self.target(),
            self.forward_map,
            p,
        ))
    }
    pub fn dual(&self, p: Pt<ER>) -> Result<Pt<ER>, String> {
        if !curve::on_curve(self.field, self.target(), &p) {
            return Err("off fourth target".into());
        }
        Ok(eval_rational(
            self.field,
            self.target(),
            self.source(),
            self.dual_map,
            p,
        ))
    }
}
pub fn paired_fourth_old_dual_control() {
    let c = CheckedInstance::construct().unwrap();
    let pair = TwistedPair::construct(&c);
    let f = pair.field();
    let n = f.from_u64(13);
    let old_dual = Rational::normalized(f, &pair.old.normalized_third_dual).scaled(
        f,
        f.inv(f.pow(n, 2)),
        f.inv(f.pow(n, 3)),
    );
    fourth_kernel_gate(
        f,
        &pair.old.third,
        &old_dual.after(f, &Rational::normalized(f, &pair.old.third)),
    );
    panic!("old third dual must never accept");
}
