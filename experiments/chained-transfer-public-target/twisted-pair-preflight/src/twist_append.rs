// Prospective f10846, published3fad107a before this additive implementation.
fn certify_group(
    f: &FpR,
    ec: &Curve<ER>,
    ell: u64,
    order: u128,
    generator: Pt<ER>,
) -> Result<Value, String> {
    if f.size() != 223u128.pow(3) || !curve::is_smooth(f, ec) {
        return Err("field or smoothness".into());
    }
    if !isogeny_algos::field::is_prime(ell) || ell == 13 {
        return Err("prime subgroup distinct from13 required".into());
    }
    if generator == Pt::Inf || !curve::on_curve(f, ec, &generator) {
        return Err("actual nonzero on-curve generator required".into());
    }
    if curve::pmul(f, ec, &generator, ell as u128) != Pt::Inf {
        return Err("actual prime-order generator check".into());
    }
    let radius = ghs_original_engines::cover::isqrt_u128(4 * f.size());
    let first = (f.size() + 1 - radius).div_ceil(ell as u128);
    let last = (f.size() + 1 + radius) / ell as u128;
    if first != last || first * ell as u128 != order {
        return Err("unique Hasse multiple must equal full declared order".into());
    }
    Ok(
        json!({"equation":equation(ec),"ell":ell,"order":order,"cofactor":first,"generator":point(generator),"Hasse_radius":radius,"first_multiple":first,"last_multiple":last,"actual_prime_order_point":true,"scope":"original group arithmetic and written Hasse/Lagrange bridge; no encoded-field Lean proof"}),
    )
}

fn factor_order(mut n: u64) -> Vec<(u64, u32)> {
    let mut out = vec![];
    let mut p = 2;
    while p <= n / p {
        if n % p == 0 {
            let mut exponent = 0;
            while n % p == 0 {
                n /= p;
                exponent += 1;
            }
            assert!(isogeny_algos::field::is_prime(p));
            out.push((p, exponent));
        }
        p += 1;
    }
    if n > 1 {
        assert!(isogeny_algos::field::is_prime(n));
        out.push((n, 1));
    }
    out
}

fn scaled_argument(f: &FpR, p: &Poly<FpR>, inverse: ER) -> Poly<FpR> {
    let mut power = f.one();
    p.iter()
        .map(|&a| {
            let v = f.mul(a, power);
            power = f.mul(power, inverse);
            v
        })
        .collect()
}
fn twist_rational(f: &FpR, old: &Rational, v: ER) -> Rational {
    let inverse = f.inv(v);
    Rational {
        xn: poly::scale(f, &scaled_argument(f, &old.xn, inverse), v),
        xd: scaled_argument(f, &old.xd, inverse),
        yn: scaled_argument(f, &old.yn, inverse),
        yd: scaled_argument(f, &old.yd, inverse),
    }
}
fn eval_rational(f: &FpR, dom: &Curve<ER>, cod: &Curve<ER>, map: &Rational, p: Pt<ER>) -> Pt<ER> {
    assert!(curve::on_curve(f, dom, &p));
    let out = match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => {
            let d = poly::eval(f, &map.xd, x);
            if f.is_zero(d) {
                Pt::Inf
            } else {
                let yd = poly::eval(f, &map.yd, x);
                assert!(!f.is_zero(yd));
                Pt::Aff(
                    f.div(poly::eval(f, &map.xn, x), d),
                    f.mul(y, f.div(poly::eval(f, &map.yn, x), yd)),
                )
            }
        }
    };
    assert!(curve::on_curve(f, cod, &out));
    out
}

fn compare_degree13_recipe(f: &FpR, a: &Rational, b: &Rational) -> Value {
    let rx = poly::sub(f, &poly::mul(f, &a.xn, &b.xd), &poly::mul(f, &b.xn, &a.xd));
    let ry = poly::sub(f, &poly::mul(f, &a.yn, &b.yd), &poly::mul(f, &b.yn, &a.yd));
    assert!(rx.is_empty() && ry.is_empty());
    assert_eq!((poly::deg(f, &a.xn), poly::deg(f, &a.xd)), (13, 12));
    assert_eq!(poly::gcd(f, &a.xn, &a.xd), vec![f.one()]);
    json!({"actual_new_Kohel":a.json(),"independent_twisted_recipe":b.json(),"whole_x_cross_residual":coefficients(&rx),"whole_y_cross_residual":coefficients(&ry),"degrees":[13,12],"coprime":true})
}

pub struct TwistedPair {
    old: ThirdHop,
    source: Curve<ER>,
    target: Curve<ER>,
    forward_map: Rational,
    dual_map: Rational,
    pub ell: u64,
    pub order: u128,
    pub generator: Pt<ER>,
    pub target_generator: Pt<ER>,
    pub certificate: Value,
}
impl TwistedPair {
    pub fn field(&self) -> &FpR {
        self.old.field()
    }
    pub fn source(&self) -> &Curve<ER> {
        &self.source
    }
    pub fn target(&self) -> &Curve<ER> {
        &self.target
    }
    pub fn old_source(&self) -> &Curve<ER> {
        self.old.source()
    }
    pub fn old_target(&self) -> &Curve<ER> {
        self.old.target()
    }
    pub fn forward(&self, p: Pt<ER>) -> Pt<ER> {
        eval_rational(
            self.field(),
            &self.source,
            &self.target,
            &self.forward_map,
            p,
        )
    }
    pub fn dual(&self, p: Pt<ER>) -> Pt<ER> {
        eval_rational(self.field(), &self.target, &self.source, &self.dual_map, p)
    }
    pub fn construct(c: &CheckedInstance) -> Self {
        let old = ThirdHop::construct(c);
        let f = old.field();
        let v = f.from_u64(12);
        assert_eq!(f.frobenius(v), v);
        assert_eq!(f.pow(v, 111), f.neg(f.one()));
        let twist_curve =
            |ec: &Curve<ER>| Curve::new(f.mul(f.pow(v, 2), ec.a), f.mul(f.pow(v, 3), ec.b));
        let source = twist_curve(old.source());
        let target = twist_curve(old.target());
        let h = poly::monic(f, &scaled_argument(f, &old.third.ker, f.inv(v)));
        let hd = poly::monic(
            f,
            &scaled_argument(f, &old.normalized_third_dual.ker, f.inv(v)),
        );
        let forward = kohel(f, &source, &h, 13);
        assert_eq!(forward.cod, target);
        let reverse = kohel(f, &target, &hd, 13);
        let thirteen = f.from_u64(13);
        assert_eq!(reverse.cod.a, f.mul(f.pow(thirteen, 4), source.a));
        assert_eq!(reverse.cod.b, f.mul(f.pow(thirteen, 6), source.b));
        let forward_map = Rational::normalized(f, &forward);
        let dual_map = Rational::normalized(f, &reverse).scaled(
            f,
            f.inv(f.pow(thirteen, 2)),
            f.inv(f.pow(thirteen, 3)),
        );
        let old_forward = Rational::normalized(f, &old.third);
        let old_dual = Rational::normalized(f, &old.normalized_third_dual).scaled(
            f,
            f.inv(f.pow(thirteen, 2)),
            f.inv(f.pow(thirteen, 3)),
        );
        let recipe_forward =
            compare_rationals(f, &forward_map, &twist_rational(f, &old_forward, v));
        let recipe_dual = compare_degree13_recipe(f, &dual_map, &twist_rational(f, &old_dual, v));
        let mut identities = vec![];
        for (dom, cod, map, kernel, expected_eigenvalue) in [
            (&source, &target, &forward_map, &h, 11),
            (&target, &source, &dual_map, &hd, 9),
        ] {
            assert_eq!((poly::deg(f, &map.xn), poly::deg(f, &map.xd)), (13, 12));
            assert_eq!(poly::gcd(f, &map.xn, &map.xd), vec![f.one()]);
            let residual = rational_curve_residual(f, dom, cod, map);
            assert!(residual.is_empty());
            let derivative = derivative_numerator(f, &map.xn, &map.xd);
            assert!(!derivative.is_empty());
            let eigenvalue = elkies_eigenvalue(f, dom, kernel, 13);
            assert_eq!(eigenvalue, Some(expected_eigenvalue));
            let altered = Curve::new(cod.a, f.add(cod.b, f.one()));
            let bad = rational_curve_residual(f, dom, &altered, map);
            assert!(!bad.is_empty());
            identities.push(json!({"domain":equation(dom),"codomain":equation(cod),"map":map.json(),"kernel":coefficients(kernel),"whole_curve_residual":coefficients(&residual),"derivative_numerator":coefficients(&derivative),"actual_SEA_eigenvalue":eigenvalue,"altered_target_nonzero_residual":coefficients(&bad)}));
        }
        let source_norm = compare_rationals(
            f,
            &dual_map.after(f, &forward_map),
            &multiplication_13(f, &source),
        );
        let target_norm = compare_rationals(
            f,
            &forward_map.after(f, &dual_map),
            &multiplication_13(f, &target),
        );
        let order = 2 * (f.size() + 1) - c.inst.order;
        let factors = factor_order(u64::try_from(order).unwrap());
        assert_eq!(
            factors
                .iter()
                .fold(1u128, |a, &(p, e)| a * (p as u128).pow(e)),
            order
        );
        let ell = factors.last().unwrap().0;
        assert_ne!(ell, 13);
        println!(
            "N4_TWIST_ORDER_CANDIDATE {}",
            json!({"nu":12,"new_instance":true,"untwisted_order":c.inst.order,"quadratic_twist_candidate_order":order,"factorization":factors,"largest_prime_fixed_before_models":ell,"source":equation(&source),"target":equation(&target)})
        );
        let cofactor = order / ell as u128;
        let mut attempts = vec![];
        let mut generator = None;
        let mut rng = Rng::new(0x12fe);
        for i in 0..256u64 {
            let x = er([i / (223 * 223), (i / 223) % 223, i % 223]);
            let rhs = poly::eval(f, &cubic(f, &source), x);
            let mut roots = poly::roots(f, &vec![f.neg(rhs), f.zero(), f.one()], &mut rng);
            roots.sort();
            let mut row = json!({"lexicographic_index":i,"x":three(x),"all_y_roots":roots.iter().copied().map(three).collect::<Vec<_>>()});
            if let Some(&y) = roots.first() {
                let p = Pt::Aff(x, y);
                assert!(curve::on_curve(f, &source, &p));
                let g = curve::pmul(f, &source, &p, cofactor);
                row["cofactor_image"] = point(g);
                if g != Pt::Inf {
                    generator = Some(g);
                    attempts.push(row);
                    break;
                }
            }
            attempts.push(row);
        }
        println!(
            "N4_TWIST_GENERATOR_ATTEMPTS {}",
            json!({"all_attempts":attempts,"bound":256,"selected":generator.map(point)})
        );
        let generator = generator.expect(
            "fixed new subgroup certificate remains unimplemented after bounded generator attempts",
        );
        let source_certificate = certify_group(f, &source, ell, order, generator).unwrap();
        let target_generator = eval_rational(f, &source, &target, &forward_map, generator);
        let target_certificate = certify_group(f, &target, ell, order, target_generator).unwrap();
        let wrong_order = certify_group(f, &source, ell, order + 1, generator).unwrap_err();
        let zero_generator = certify_group(f, &source, ell, order, Pt::Inf).unwrap_err();
        let certificate = json!({"protocol":"f10846","nu":12,"old_whole_third_certificate":old.certificate,"source_id":format!("N4-E2-twist12-short-{}",digest(&equation(&source))),"target_id":format!("N4-E3-twist12-short-{}",digest(&equation(&target))),"source_certificate":source_certificate,"target_certificate":target_certificate,"wrong_order_actual_rejection":wrong_order,"zero_generator_actual_rejection":zero_generator,"forward_recipe_whole_identity":recipe_forward,"signed_dual_recipe_whole_identity":recipe_dual,"whole_rational_checks":identities,"dual_after_forward_13":source_norm,"forward_after_dual_13":target_norm,"scope":"new twisted ECDLP instance; not an original-logarithm transfer to a twist or complete Jacobian evaluator"});
        Self {
            old,
            source,
            target,
            forward_map,
            dual_map,
            ell,
            order,
            generator,
            target_generator,
            certificate,
        }
    }
}
