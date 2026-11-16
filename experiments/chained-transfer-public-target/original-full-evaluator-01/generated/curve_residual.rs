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

