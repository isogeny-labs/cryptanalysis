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
