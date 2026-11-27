//! Evaluator fixture preparation only. Never linked into the recovery worker.
use prime_field_auxiliary_ic::Curve;
fn main() {
    let seed: u64 = std::env::args()
        .nth(1)
        .expect("evaluator seed")
        .parse()
        .unwrap();
    let n = 2147505293u64;
    let scalar = seed % (n - 1) + 1;
    let curve = Curve::<31>::new(2, 14).unwrap();
    let g = curve.point(1, 814455902).unwrap();
    assert!(curve.mul(Some(g), n).unwrap().is_none());
    let q = curve.mul(Some(g), scalar).unwrap().unwrap();
    println!("{{\"public\":{{\"p\":2147483647,\"a\":2,\"b\":14,\"n\":{n},\"P\":[1,814455902],\"Q\":[{},{}]}},\"evaluator\":{{\"scalar\":{scalar}}}}}",q.x(),q.y());
}
