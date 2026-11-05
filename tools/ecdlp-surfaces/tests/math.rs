use ecdlp_surfaces::{
    bigint::BigInt,
    cli::Args,
    curve::{Curve, Point},
    frobenius::filter,
    json::text,
};

#[test]
fn default_example_matches_independent_reference() {
    let curve = Curve::new(101, 1, 46).unwrap();
    assert_eq!(curve.points().len(), 109);
    let subgroup = curve.select_subgroup().unwrap();
    assert_eq!(subgroup.order, 109);
    assert_eq!(subgroup.generator, Point::Affine(2, 37));
    assert_eq!(
        curve.multiply(37, subgroup.generator).unwrap(),
        Point::Affine(64, 19)
    );
    assert_eq!(
        curve.multiply(109, subgroup.generator).unwrap(),
        Point::Infinity
    );
    let quadrics: Vec<_> = (0..101).map(|lambda| curve.quadric(lambda)).collect();
    assert_eq!(quadrics.iter().filter(|q| q.smooth).count(), 101);
    assert_eq!(quadrics.iter().filter(|q| q.split).count(), 54);
}

#[test]
fn small_curve_group_axioms_include_exceptional_cases() {
    let curve = Curve::new(7, -1, 0).unwrap();
    let points = curve.points();
    assert_eq!(points.len(), 8);
    for &p in &points {
        assert_eq!(curve.add(p, Point::Infinity).unwrap(), p);
        assert_eq!(
            curve.add(p, curve.negate(p).unwrap()).unwrap(),
            Point::Infinity
        );
        for &q in &points {
            let sum = curve.add(p, q).unwrap();
            assert!(curve.contains(sum));
            assert_eq!(sum, curve.add(q, p).unwrap());
            for &r in &points {
                assert_eq!(
                    curve.add(sum, r).unwrap(),
                    curve.add(p, curve.add(q, r).unwrap()).unwrap()
                );
            }
        }
    }
    assert_eq!(
        curve.add(Point::Affine(0, 0), Point::Affine(0, 0)).unwrap(),
        Point::Infinity
    );
}

#[test]
fn rank_two_torsion_does_not_certify_subgroup_membership() {
    let curve = Curve::new(7, -1, 0).unwrap();
    let p = Point::Affine(0, 0);
    let q = Point::Affine(1, 0);
    assert_eq!(curve.multiply(2, p).unwrap(), Point::Infinity);
    assert_eq!(curve.multiply(2, q).unwrap(), Point::Infinity);
    assert!(curve
        .certify_transfer(p, q, 2, None)
        .unwrap_err()
        .contains("cyclic subgroup"));
    assert!(curve.certify_transfer(p, Point::Infinity, 2, None).is_ok());
}

#[test]
fn all_default_points_roundtrip_with_projective_scaling() {
    let curve = Curve::new(101, 1, 46).unwrap();
    for point in curve.points() {
        let encoded = curve.encode(point).unwrap();
        for scale in [1, 2, 7, 100] {
            let scaled = encoded.map(|c| c * scale % 101);
            assert_eq!(curve.decode(scaled).unwrap(), point);
        }
    }
    assert_eq!(curve.decode([0, 0, 0, 5]).unwrap(), Point::Infinity);
    assert!(curve.decode([0, 0, 0, 0]).is_err());
}

#[test]
fn surface_only_points_cannot_enter_the_curve_group() {
    let curve = Curve::new(101, 1, 46).unwrap();
    let surface_only = [1, 2, 0, 77];
    assert_eq!(curve.quadric_values(surface_only).1, 0);
    assert_ne!(curve.quadric_values(surface_only).0, 0);
    assert!(curve.decode(surface_only).is_err());
    assert!(curve.image_add(surface_only, [0, 0, 0, 1]).is_err());
}

#[test]
fn transfer_checks_known_scalar_and_identity() {
    let curve = Curve::new(101, 1, 46).unwrap();
    let p = Point::Affine(2, 37);
    let q = Point::Affine(64, 19);
    let certificate = curve.certify_transfer(p, q, 109, Some(37)).unwrap();
    assert_eq!(certificate.image_p, [1, 2, 37, 4]);
    assert_eq!(certificate.image_q, [1, 64, 19, 56]);
    assert_eq!(certificate.scalar, Some(37));
    assert!(curve.certify_transfer(p, q, 109, Some(38)).is_err());
    assert!(curve
        .certify_transfer(Point::Infinity, q, 109, None)
        .is_err());
    assert!(curve.certify_transfer(p, q, 108, None).is_err());
    let identity = curve
        .certify_transfer(p, Point::Infinity, 109, Some(0))
        .unwrap();
    assert_eq!(identity.image_q, [0, 0, 0, 1]);
    assert_eq!(
        curve
            .image_add(certificate.image_p, identity.image_q)
            .unwrap(),
        certificate.image_p
    );
}

fn determinant(mut matrix: [[u64; 4]; 4], p: u64) -> u64 {
    let mut value = 1;
    for col in 0..4 {
        let Some(pivot_row) = (col..4).find(|&row| matrix[row][col] != 0) else {
            return 0;
        };
        if pivot_row != col {
            matrix.swap(col, pivot_row);
            value = (p - value) % p;
        }
        let pivot = matrix[col][col];
        value = value * pivot % p;
        let inverse = (1..p).find(|&n| n * pivot % p == 1).unwrap();
        let pivot_values = matrix[col];
        for row in matrix.iter_mut().skip(col + 1) {
            let factor = row[col] * inverse % p;
            for (cell, &pivot_cell) in row.iter_mut().zip(pivot_values.iter()).skip(col) {
                *cell = (*cell + p - factor * pivot_cell % p) % p;
            }
        }
    }
    value
}

#[test]
fn quadric_determinants_match_matrix_elimination() {
    for curve in [
        Curve::new(101, 1, 46).unwrap(),
        Curve::new(7, -1, 0).unwrap(),
    ] {
        let p = curve.prime();
        let half = (p + 1) / 2;
        for lambda in 0..p {
            let off = (p - curve.a()) * half % p;
            let matrix = [
                [(p - curve.b()) % p, off, 0, lambda * half % p],
                [off, (p - lambda) % p, 0, p - half],
                [0, 0, 1, 0],
                [lambda * half % p, p - half, 0, 0],
            ];
            let quadric = curve.quadric(lambda);
            assert_eq!(quadric.determinant, determinant(matrix, p));
            assert_eq!(quadric.smooth, determinant(matrix, p) != 0);
            let has_nonzero_square_root = (1..p).any(|y| y * y % p == curve.rhs(lambda));
            assert_eq!(quadric.split, quadric.smooth && has_nonzero_square_root);
        }
    }
}

#[test]
fn singular_and_out_of_range_sources_are_rejected() {
    assert!(Curve::new(101, 0, 0).is_err());
    assert!(Curve::new(100, 1, 46).is_err());
    assert!(Curve::new(3, 1, 46).is_err());
    assert!(Curve::new(u64::MAX, 1, 46).is_err());
    let curve = Curve::new(101, -100, -55).unwrap();
    assert_eq!((curve.a(), curve.b()), (1, 46));
    assert!(curve.add(Point::Affine(101, 1), Point::Infinity).is_err());
}

#[test]
fn frobenius_accepts_compatible_products() {
    let square = filter(101, -7, [14, 251, 1414, 10201]).unwrap();
    assert!(square.passes_necessary_conditions());
    assert_eq!(square.quotient, [1, 7, 101]);
    assert_eq!(square.remainder, [0, 0]);
    let other_product = filter(101, -7, [7, 202, 707, 10201]).unwrap();
    assert!(other_product.passes_necessary_conditions());
    assert_eq!(other_product.quotient, [1, 0, 101]);
}

#[test]
fn frobenius_rejects_incompatible_or_invalid_candidates() {
    let other_square = filter(101, -7, [0, 202, 0, 10201]).unwrap();
    assert!(other_square.reciprocal);
    assert!(!other_square.divides);
    assert!(!other_square.passes_necessary_conditions());
    let wrong_shape = filter(101, -7, [7, 203, 714, 10302]).unwrap();
    assert!(wrong_shape.divides);
    assert!(!wrong_shape.reciprocal);
    assert!(!wrong_shape.passes_necessary_conditions());
    let wrong_hasse = filter(101, -7, [-23, -8, -2323, 10201]).unwrap();
    assert!(wrong_hasse.divides);
    assert!(!wrong_hasse.quotient_hasse_bound);
    assert!(!wrong_hasse.passes_necessary_conditions());
}

#[test]
fn polynomial_overflow_and_invalid_trace_are_errors() {
    // Former i128 overflow is now exact: no error, and the value is preserved.
    let huge = filter(101, -7, [i128::MAX, 0, 0, 0]).unwrap();
    assert_eq!(huge.quotient[1], i128::MAX - 7);
    assert!(filter(101, 21, [14, 251, 1414, 10201]).is_err());
    assert!(filter(1, 0, [0, 0, 0, 0]).is_err());
    assert!(filter(BigInt::pow2(83), BigInt::pow2(43), [0, 0, 0, 0]).is_err());
}

#[test]
fn cli_parses_negative_values_and_rejects_duplicates() {
    let args = Args::from_iter(["--a", "-1", "--b=2"].map(str::to_owned), &["a", "b"]).unwrap();
    assert_eq!(args.number("a", 0_i128).unwrap(), -1);
    assert_eq!(args.number("b", 0_i128).unwrap(), 2);
    assert!(Args::from_iter(["--a", "1", "--a=2"].map(str::to_owned), &["a"]).is_err());
    assert!(Args::from_iter(["--a"].map(str::to_owned), &["a"]).is_err());
    assert!(Args::from_iter(["--unknown=1"].map(str::to_owned), &["a"]).is_err());
}

#[test]
fn json_escapes_control_characters_and_preserves_unicode() {
    assert_eq!(
        text("\u{0}\"\\\n\t中文").pretty(),
        "\"\\u0000\\\"\\\\\\n\\t中文\""
    );
}

// q = 2^83 anchors (GF(2^83) Koblitz a=0 / a=1). Every literal below was
// computed with Python integers by research/frobenius_filter_bigint_n83_20261105/reference.py.
const Q83: &str = "2^83";
const T_A0: &str = "-6151469093347";
const T_A1: &str = "6151469093347";
const C4: &str = "93536104789177786765035829293842113257979682750464"; // q^2
const SQUARE_A0: [&str; 4] = [
    "12302938186694",
    "57183385120237428994961225",
    "118986717048137308772278645501462577152",
    C4,
];
const SQUARE_A1: [&str; 4] = [
    "-12302938186694",
    "57183385120237428994961225",
    "-118986717048137308772278645501462577152",
    C4,
];
const MIXED: [&str; 4] = ["0", "-18497758892569295404363593", "0", C4];

fn big(s: &str) -> BigInt {
    BigInt::parse(s).unwrap()
}
fn run83(trace: &str, c: [&str; 4]) -> ecdlp_surfaces::frobenius::Filter {
    filter(big(Q83), big(trace), c.map(big)).unwrap()
}

#[test]
fn q_2_pow_83_squares_pass_with_exact_quotients() {
    for (trace, c, u) in [
        (T_A0, SQUARE_A0, "6151469093347"),
        (T_A1, SQUARE_A1, "-6151469093347"),
    ] {
        let r = run83(trace, c);
        assert_eq!(r.q.to_string(), "9671406556917033397649408");
        assert!(r.passes_necessary_conditions());
        assert_eq!(r.quotient, [big("1"), big(c[0]).add(&big(trace)), big(Q83)]);
        assert_eq!(r.quotient[1], big(u).mul(&big("2")).sub(&big(u)));
        assert_eq!(r.remainder, [0, 0]);
    }
}

#[test]
fn q_2_pow_83_mixed_product_passes_for_either_factor() {
    for trace in [T_A0, T_A1] {
        let r = run83(trace, MIXED);
        assert!(r.passes_necessary_conditions(), "trace {trace}");
        // Quotient is the other factor T^2 - t1*T + q = T^2 + t*T + q.
        assert_eq!(r.quotient[1], big(trace));
        assert_eq!(r.remainder, [0, 0]);
    }
}

#[test]
fn q_2_pow_83_wrong_factor_fails() {
    // (T^2 - t0 T + q)^2 does not contain the a=1 factor T^2 - t1 T + q.
    let r = run83(T_A1, SQUARE_A0);
    assert!(r.reciprocal);
    assert!(!r.divides);
    assert!(!r.passes_necessary_conditions());
    // A Hasse-violating source trace is an error at this size too.
    assert!(filter(big(Q83), big("2^43"), SQUARE_A0.map(big)).is_err());
    // A reciprocity break (c4 off by one) is caught at 250 bits.
    let mut broken = SQUARE_A0.map(big);
    broken[3] = broken[3].add(&big("1"));
    let r = filter(big(Q83), big(T_A0), broken).unwrap();
    assert!(!r.reciprocal && !r.divides && !r.passes_necessary_conditions());
}

#[test]
fn args_accept_power_of_two_and_decimal_q() {
    assert_eq!(big("2^83"), big("9671406556917033397649408"));
    assert_eq!(big("-2^3"), -8);
}
