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
