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
