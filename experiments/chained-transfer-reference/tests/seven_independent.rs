//! Frozen degree7 certificate replay with the pre-existing Montgomery
//! field/poly/kernel engine. No producer Kohel or new transfer code imported.
use chained_seven_reference::{
    curve::{self, Model},
    field::{Fe, Field},
    kernel,
    poly::{self, Poly},
};
use num_bigint::BigUint;
use std::collections::HashSet;

const FIXTURE: &str = include_str!("../evidence/elliptic-seven-witness-01.tsv");
type Point = Option<(Fe, Fe)>;

fn polynomial(f: &Field, input: &str) -> Poly {
    input
        .trim()
        .trim_start_matches('[')
        .trim_end_matches(']')
        .split(',')
        .filter(|s| !s.trim().is_empty())
        .map(|s| {
            let n: u64 = s.trim().parse().unwrap();
            assert!(n < 101);
            f.from_u64(n)
        })
        .collect()
}

fn cube(f: &Field, a: &Poly) -> Poly {
    poly::mul(f, &poly::mul(f, a, a), a)
}

fn equation(f: &Field, source: &Model, target: &Model, n: &Poly, d: &Poly) {
    let s = poly::sub(
        f,
        &poly::mul(f, &poly::derivative(f, n), d),
        &poly::mul(f, n, &poly::derivative(f, d)),
    );
    let d2 = poly::mul(f, d, d);
    let rhs = poly::add(
        f,
        &poly::add(
            f,
            &cube(f, n),
            &poly::scale(f, &poly::mul(f, n, &d2), &target.a),
        ),
        &poly::scale(f, &cube(f, d), &target.b),
    );
    let source_polynomial = vec![source.b, source.a, f.zero(), f.one()];
    assert_eq!(poly::gcd(f, n, d), vec![f.one()]);
    assert_eq!(
        poly::mul(f, &source_polynomial, &poly::mul(f, &s, &s)),
        poly::mul(f, d, &rhs)
    );
}

fn homogeneous(f: &Field, a: &Poly, n: &Poly, d: &Poly) -> Poly {
    let degree = a.len() - 1;
    let mut ns = vec![vec![f.one()]];
    let mut ds = vec![vec![f.one()]];
    for i in 0..degree {
        ns.push(poly::mul(f, &ns[i], n));
        ds.push(poly::mul(f, &ds[i], d));
    }
    let mut out = vec![];
    for (i, coefficient) in a.iter().enumerate() {
        out = poly::add(
            f,
            &out,
            &poly::scale(f, &poly::mul(f, &ns[i], &ds[degree - i]), coefficient),
        );
    }
    out
}

fn composition(f: &Field, outer: (&Poly, &Poly), inner: (&Poly, &Poly)) -> (Poly, Poly) {
    assert_eq!((outer.0.len(), outer.1.len()), (8, 7));
    (
        homogeneous(f, outer.0, inner.0, inner.1),
        poly::mul(f, inner.1, &homogeneous(f, outer.1, inner.0, inner.1)),
    )
}

fn multiplication(f: &Field, e: &Model) -> (Poly, Poly) {
    // No reduction occurs below degree64. This is the existing independent
    // division-polynomial recurrence,not producer coefficients.
    let mut modulus = vec![f.zero(); 65];
    modulus[64] = f.one();
    let values = kernel::division_polys_mod(f, e, 8, &modulus);
    let denominator = poly::mul(f, &values[7], &values[7]);
    let support = vec![e.b, e.a, f.zero(), f.one()];
    let correction = poly::scale(
        f,
        &poly::mul(f, &support, &poly::mul(f, &values[6], &values[8])),
        &f.from_u64(4),
    );
    (
        poly::sub(f, &poly::mul(f, &poly::x(f), &denominator), &correction),
        denominator,
    )
}

fn evaluate(f: &Field, n: &Poly, d: &Poly, point: Point) -> Point {
    point.map(|(x, y)| {
        let nv = poly::eval(f, n, &x);
        let dv = poly::eval(f, d, &x);
        let nd = poly::eval(f, &poly::derivative(f, n), &x);
        let dd = poly::eval(f, &poly::derivative(f, d), &x);
        let coordinate = f
            .div(&nv, &dv)
            .expect("rational source point outside kernel");
        let slope = f
            .div(&f.sub(&f.mul(&nd, &dv), &f.mul(&nv, &dd)), &f.sqr(&dv))
            .unwrap();
        (coordinate, f.mul(&y, &slope))
    })
}

fn points(f: &Field, e: &Model) -> Vec<Point> {
    let mut out = vec![None];
    for x in 0..101 {
        let x = f.from_u64(x);
        for y in 0..101 {
            let y = f.from_u64(y);
            if e.on_curve(f, &x, &y) {
                out.push(Some((x, y)));
            }
        }
    }
    out
}

fn multiply_point(f: &Field, e: &Model, point: Point, scalar: u64) -> Point {
    point.and_then(|(x, y)| curve::scalar_mul(f, e, &x, &y, &BigUint::from(scalar)))
}

fn main() {
    let f = Field::new(&BigUint::from(101_u64)).unwrap();
    let mut records = 0;
    let mut models: Vec<(Model, Model)> = vec![];
    for line in FIXTURE.lines().skip(2) {
        let fields = line.split('\t').collect::<Vec<_>>();
        assert_eq!(fields.len(), 14);
        let number = |i: usize| -> u64 { fields[i].parse().unwrap() };
        let element = |i: usize| f.from_u64(number(i));
        let source = Model {
            a: element(0),
            b: element(1),
        };
        let target = Model {
            a: element(4),
            b: element(5),
        };
        let dual_target = Model {
            a: element(11),
            b: element(12),
        };
        assert!(!f.is_zero(&source.discriminant(&f)));
        assert!(!f.is_zero(&target.discriminant(&f)));
        assert!(!f.is_zero(&dual_target.discriminant(&f)));
        assert_ne!(source.j(&f), target.j(&f));
        assert_eq!(curve::isomorphism(&f, &source, &target), None);
        for (old_source, old_target) in &models {
            if *old_source == source {
                assert_ne!(old_target.j(&f), target.j(&f));
                assert_eq!(curve::isomorphism(&f, old_target, &target), None);
            }
        }
        models.push((source, target));
        let (h, n, d) = (
            polynomial(&f, fields[3]),
            polynomial(&f, fields[6]),
            polynomial(&f, fields[7]),
        );
        let (dual_h, dual_n, dual_d) = (
            polynomial(&f, fields[8]),
            polynomial(&f, fields[9]),
            polynomial(&f, fields[10]),
        );
        assert_eq!(kernel::verify_kernel(&f, &source, 7, &h).unwrap(), target);
        assert_eq!(
            kernel::verify_kernel(&f, &target, 7, &dual_h).unwrap(),
            dual_target
        );
        assert_eq!(d, poly::mul(&f, &h, &h));
        assert_eq!(dual_d, poly::mul(&f, &dual_h, &dual_h));
        equation(&f, &source, &target, &n, &d);
        equation(&f, &target, &dual_target, &dual_n, &dual_d);
        let u = element(13);
        assert_eq!(f.mul(&u, &f.from_u64(7)), f.one());
        let u2 = f.sqr(&u);
        let u3 = f.mul(&u2, &u);
        assert_eq!(f.mul(&f.sqr(&u2), &dual_target.a), source.a);
        assert_eq!(f.mul(&f.sqr(&u3), &dual_target.b), source.b);
        let scaled = poly::scale(&f, &dual_n, &u2);
        let composed = composition(&f, (&scaled, &dual_d), (&n, &d));
        let expected = multiplication(&f, &source);
        assert_eq!(
            poly::mul(&f, &composed.0, &expected.1),
            poly::mul(&f, &expected.0, &composed.1)
        );
        let composed = composition(&f, (&n, &d), (&scaled, &dual_d));
        let expected = multiplication(&f, &target);
        assert_eq!(
            poly::mul(&f, &composed.0, &expected.1),
            poly::mul(&f, &expected.0, &composed.1)
        );
        let reverse = |point| {
            evaluate(&f, &dual_n, &dual_d, point).map(|(x, y)| (f.mul(&u2, &x), f.mul(&u3, &y)))
        };
        let forward = |point| evaluate(&f, &n, &d, point);
        let (sp, tp) = (points(&f, &source), points(&f, &target));
        assert_eq!((sp.len() as u64, tp.len() as u64), (number(2), number(2)));
        let mut image = HashSet::new();
        for point in sp {
            let mapped = forward(point);
            assert_eq!(reverse(mapped), multiply_point(&f, &source, point, 7));
            image.insert(mapped);
        }
        assert_eq!(image, tp.iter().copied().collect());
        for point in tp {
            assert_eq!(
                forward(reverse(point)),
                multiply_point(&f, &target, point, 7)
            );
        }
        records += 1;
    }
    assert_eq!(records, 4);
    println!("PASS4 frozen degree7 forward/dual kernel certificates,exact curve and both globalx[7] identities,all109/113 source/target points and bijections using pre-existing Montgomery field/poly/kernel engines;no producer Kohel code imported,no solver/speed claim");
}

#[test]
fn independent_seven_certificate_replay() {
    main();
}
