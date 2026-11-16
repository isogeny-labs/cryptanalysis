//! Cross-backend checks for the public Rust auxiliary-IC re-export.
use cryptanalysis::auxiliary_ic::{BatchScratch, Curve, Point};
use cryptanalysis::{Elem, Group};

fn element(point: Option<Point>) -> Elem {
    point.map_or_else(Elem::ec_infinity, |p| Elem::ec(p.x(), p.y()))
}

fn parity<const B: u32>(a: u64, b: u64, x: u64, order: u64) {
    let curve = Curve::<B>::new(a, b).unwrap();
    // An unknown order is allowed for these group-operation-only checks.
    let reference = Group::ec(curve.modulus(), a, b, order).unwrap();
    let generator = curve.lift_x(x).unwrap().unwrap();
    let mut scratch = BatchScratch::default();
    let mut points = Vec::new();
    let mut steps = Vec::new();
    let scalars = [0, 1, 2, 3, 17, 31, 123456789, u64::MAX];
    for scalar in scalars {
        let p = curve.mul(Some(generator), scalar).unwrap();
        let expected = reference.mul(&element(Some(generator)), scalar).unwrap();
        assert_eq!(element(p), expected);
        for next in [
            None,
            Some(generator),
            p,
            p.map(|v| curve.negate(v).unwrap()),
        ] {
            assert_eq!(
                element(curve.add(p, next).unwrap()),
                reference.op(&element(p), &element(next)).unwrap()
            );
            points.push(p);
            steps.push(next);
        }
    }
    let expected: Vec<_> = points
        .iter()
        .zip(&steps)
        .map(|(&p, &q)| reference.op(&element(p), &element(q)).unwrap())
        .collect();
    curve.batch_add(&mut points, &steps, &mut scratch).unwrap();
    assert_eq!(
        points.into_iter().map(element).collect::<Vec<_>>(),
        expected
    );
}

#[test]
fn mersenne31_matches_c_montgomery_arithmetic() {
    parity::<31>(2, 14, 1, 2147505293);
}

#[test]
fn mersenne61_matches_c_montgomery_arithmetic() {
    parity::<61>(0, 3, 1, 0);
}
