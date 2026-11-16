// Third-edge code follows prospective bbfd74, published9038f2b9 before code.
fn next_nondual_gate(f: &FpR, second: &RatIsogeny<FpR>, composite: &Rational) -> Value {
    assert_eq!(poly::deg(f, &composite.xn), 169);
    assert_eq!(poly::deg(f, &composite.xd), 168);
    assert_eq!(poly::gcd(f, &composite.xn, &composite.xd), vec![f.one()]);
    let psi = square(f, &division_poly(f, &second.dom, 13));
    let intersection = poly::monic(f, &poly::gcd(f, &composite.xd, &psi));
    let wanted = poly::monic(f, &second.den);
    let accepted = intersection == wanted;
    let record = json!({"composite":composite.json(),"psi13_squared":coefficients(&psi),"actual_gcd":coefficients(&intersection),"second_denominator":coefficients(&wanted),"actual_gcd_degree":poly::deg(f,&intersection),"expected_gcd_degree":12,"accepted_nondual":accepted,"scope":"exact middle169 denominator intersection; global geometric interpretation remains written"});
    println!("N4_NEXT13_KERNEL_GATE {}", record);
    assert!(
        accepted,
        "old second dual must fail next nondual kernel acceptance"
    );
    record
}

pub struct ThirdHop {
    previous: SecondHop,
    third: RatIsogeny<FpR>,
    normalized_third_dual: RatIsogeny<FpR>,
    pub certificate: Value,
}
impl ThirdHop {
    pub fn construct(c: &CheckedInstance) -> Self {
        let previous = SecondHop::construct(c);
        let f = previous.field();
        assert_eq!(
            previous.certificate["E2_id"],
            "N4-E13x13-short-2088c9e2bd44dfea66094a767e22a1f2ebffdd4e963244cb320d93408e58b4b5"
        );
        let prior_kernel: Vec<[u64; 3]> =
            serde_json::from_value(previous.certificate["new_kernel"]["kernel"].clone()).unwrap();
        let second = kohel(
            f,
            previous.source(),
            &prior_kernel.into_iter().map(er).collect(),
            13,
        );
        assert_eq!(second.dom, previous.second.dom);
        assert_eq!(second.cod, previous.second.cod);
        assert_eq!(second.ker, previous.second.ker);
        assert_eq!(second.num, previous.second.num);
        assert_eq!(second.den, previous.second.den);
        assert_eq!(
            Rational::normalized(f, &second).json(),
            previous.certificate["second_forward"]
        );
        let e2 = previous.target();
        let (h, kernel) = kernel_data(f, e2, 2);
        let old_dual_kernel = poly::monic(f, &previous.normalized_second_dual.ker);
        assert_eq!(poly::gcd(f, &h, &old_dual_kernel), vec![f.one()]);
        let third = kohel(f, e2, &h, 13);
        assert!(curve::is_smooth(f, &third.cod));
        let (hd, dual_kernel) = kernel_data(f, &third.cod, 4);
        let normalized_third_dual = kohel(f, &third.cod, &hd, 13);
        let mut checks = vec![];
        for map in [&third, &normalized_third_dual] {
            assert_eq!((poly::deg(f, &map.num), poly::deg(f, &map.den)), (13, 12));
            assert_eq!(poly::gcd(f, &map.num, &map.den), vec![f.one()]);
            assert!(identity_residual(f, map).is_empty());
            let derivative = derivative_numerator(f, &map.num, &map.den);
            assert!(!derivative.is_empty());
            let mut altered = map.clone();
            altered.cod.b = f.add(altered.cod.b, f.one());
            let residual = identity_residual(f, &altered);
            assert!(!residual.is_empty());
            checks.push(json!({"domain":equation(&map.dom),"codomain":equation(&map.cod),"kernel":coefficients(&map.ker),"num":coefficients(&map.num),"den":coefficients(&map.den),"whole_curve_residual":[],"derivative_numerator":coefficients(&derivative),"actual_altered_target_nonzero_residual":coefficients(&residual)}));
        }
        let thirteen = f.from_u64(13);
        assert_eq!(normalized_third_dual.cod.a, f.mul(f.pow(thirteen, 4), e2.a));
        assert_eq!(normalized_third_dual.cod.b, f.mul(f.pow(thirteen, 6), e2.b));
        let forward = Rational::normalized(f, &third);
        let dual = Rational::normalized(f, &normalized_third_dual).scaled(
            f,
            previous.first.inverse_13_squared,
            previous.first.inverse_13_cubed,
        );
        let source_roundtrip =
            compare_rationals(f, &dual.after(f, &forward), &multiplication_13(f, e2));
        let target_roundtrip = compare_rationals(
            f,
            &forward.after(f, &dual),
            &multiplication_13(f, &third.cod),
        );
        let composite = forward.after(f, &Rational::normalized(f, &second));
        let residual = rational_curve_residual(f, &second.dom, &third.cod, &composite);
        assert!(residual.is_empty());
        let derivative = derivative_numerator(f, &composite.xn, &composite.xd);
        assert!(!derivative.is_empty());
        let nondual = next_nondual_gate(f, &second, &composite);
        let old_dual = Rational::normalized(f, &previous.normalized_second_dual).scaled(
            f,
            previous.first.inverse_13_squared,
            previous.first.inverse_13_cubed,
        );
        let backtrack = old_dual.after(f, &Rational::normalized(f, &second));
        let psi = square(f, &division_poly(f, &second.dom, 13));
        let backtrack_gcd = poly::monic(f, &poly::gcd(f, &backtrack.xd, &psi));
        assert_eq!(poly::deg(f, &backtrack_gcd), 168);
        assert_eq!(backtrack_gcd, poly::monic(f, &psi));
        assert_ne!(backtrack_gcd, poly::monic(f, &second.den));
        let js = |ec: &Curve<ER>| {
            let mut j = curve::jinv(f, ec);
            let mut out = vec![];
            for _ in 0..3 {
                out.push(three(j));
                j = f.pow(j, 223);
            }
            assert_eq!(j, er(out[0]));
            out
        };
        let j0 = js(previous.first.source());
        let j1 = js(previous.source());
        let j2 = js(previous.target());
        let j3 = js(&third.cod);
        let certificate = json!({"protocol":"bbfd74","field_modulus":[220,0,0,1],"field_tag":c.field_tag,"previous_whole_certificate":previous.certificate,"actual_reconstructed_second":Rational::normalized(f,&second).json(),"E1":equation(previous.source()),"E2":equation(e2),"E2_id":previous.certificate["E2_id"],"E3":equation(&third.cod),"E3_id":format!("N4-E13x13x13-short-{}",digest(&equation(&third.cod))),"new_kernel":kernel,"old_second_dual_kernel":coefficients(&old_dual_kernel),"new_and_old_dual_kernel_gcd":[[1,0,0]],"actual_third_dual_kernel":dual_kernel,"third_forward":forward.json(),"third_actual_dual":dual.json(),"whole_curve_checks":checks,"third_dual_after_forward_13":source_roundtrip,"third_forward_after_dual_13":target_roundtrip,"middle_nondual_composite":nondual,"whole_middle169_curve_residual":coefficients(&residual),"middle169_derivative":coefficients(&derivative),"old_backtrack_gcd":coefficients(&backtrack_gcd),"old_backtrack_gcd_degree":168,"E0_j_conjugates":j0,"E1_j_conjugates":j1,"E2_j_conjugates":j2,"E3_j_conjugates":j3,"E3_j_intersects_E0":j3.iter().any(|x|j0.contains(x)),"E3_j_intersects_E1":j3.iter().any(|x|j1.contains(x)),"E3_j_intersects_E2":j3.iter().any(|x|j2.contains(x)),"scope":"single third elliptic edge and exact middle169 only; full2197 expansion, matched prime-field J3 and complete Jacobian maps not constructed"});
        Self {
            previous,
            third,
            normalized_third_dual,
            certificate,
        }
    }
    pub fn previous(&self) -> &SecondHop {
        &self.previous
    }
    pub fn source(&self) -> &Curve<ER> {
        &self.third.dom
    }
    pub fn target(&self) -> &Curve<ER> {
        &self.third.cod
    }
    pub fn field(&self) -> &FpR {
        self.previous.field()
    }
    pub fn original_to_source(&self, p: Pt<ER>) -> Result<Pt<ER>, String> {
        self.previous.forward(self.previous.first.forward(p)?)
    }
    pub fn forward(&self, p: Pt<ER>) -> Result<Pt<ER>, String> {
        let f = self.field();
        if !curve::on_curve(f, self.source(), &p) {
            return Err("off third source curve".into());
        }
        let q = self.third.eval(f, &p);
        if !curve::on_curve(f, self.target(), &q) {
            return Err("off third target curve".into());
        }
        Ok(q)
    }
    pub fn dual(&self, p: Pt<ER>) -> Result<Pt<ER>, String> {
        let f = self.field();
        if !curve::on_curve(f, self.target(), &p) {
            return Err("off third dual source curve".into());
        }
        let q = match self.normalized_third_dual.eval(f, &p) {
            Pt::Inf => Pt::Inf,
            Pt::Aff(x, y) => Pt::Aff(
                f.mul(x, self.previous.first.inverse_13_squared),
                f.mul(y, self.previous.first.inverse_13_cubed),
            ),
        };
        if !curve::on_curve(f, self.source(), &q) {
            return Err("off third dual target curve".into());
        }
        Ok(q)
    }
}
pub fn next_old_dual_backtracking_canary() {
    let c = CheckedInstance::construct().unwrap();
    let second = SecondHop::construct(&c);
    let f = second.field();
    let forward = Rational::normalized(f, &second.second);
    let dual = Rational::normalized(f, &second.normalized_second_dual).scaled(
        f,
        second.first.inverse_13_squared,
        second.first.inverse_13_cubed,
    );
    next_nondual_gate(f, &second.second, &dual.after(f, &forward));
    panic!("old second dual must not accept");
}

#[cfg(test)]
include!("../src/tests.rs");
