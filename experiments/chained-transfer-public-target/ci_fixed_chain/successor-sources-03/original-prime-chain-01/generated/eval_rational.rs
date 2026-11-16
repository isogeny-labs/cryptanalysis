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

