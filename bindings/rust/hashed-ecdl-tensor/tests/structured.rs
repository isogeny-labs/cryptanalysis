//! Exact small-field software controls; no benchmark or attack-cost evidence.
use hashed_ecdl_tensor::arithmetic::{inverse, Seeded};
use hashed_ecdl_tensor::contraction::Counter;
use hashed_ecdl_tensor::curve::{Curve, Point};
use hashed_ecdl_tensor::structured::{IsogenyFibres, MembershipMessage, Prepared};
use hashed_ecdl_tensor::{BigUint, Error, Limits, Meter};
use std::sync::Arc;

fn point(x: u8, y: u8) -> Point {
    Point::Affine {
        x: x.into(),
        y: y.into(),
    }
}
fn fixture(meter: &mut Meter) -> (Curve, IsogenyFibres) {
    let curve = Curve::with_cofactor(
        5u8.into(),
        0u8.into(),
        1u8.into(),
        3u8.into(),
        2u8.into(),
        point(0, 1),
        meter,
    )
    .unwrap();
    let fibres = IsogenyFibres::new(&curve, 4u8.into(), vec![1u8.into()], meter).unwrap();
    (curve, fibres)
}
fn group(curve: &Curve, meter: &mut Meter) -> Vec<Point> {
    (0..3u8)
        .map(|i| curve.mul(curve.generator(), &i.into(), meter).unwrap())
        .collect()
}
fn brute(
    curve: &Curve,
    base: &[Point],
    arity: usize,
    target: &Point,
    meter: &mut Meter,
) -> Vec<Vec<Point>> {
    fn walk(
        curve: &Curve,
        base: &[Point],
        left: usize,
        sum: Point,
        tuple: &mut Vec<Point>,
        target: &Point,
        out: &mut Vec<Vec<Point>>,
        meter: &mut Meter,
    ) {
        if left == 0 {
            if sum == *target {
                out.push(tuple.clone());
            }
            return;
        }
        for p in base {
            tuple.push(p.clone());
            walk(
                curve,
                base,
                left - 1,
                curve.add(&sum, p, meter).unwrap(),
                tuple,
                target,
                out,
                meter,
            );
            tuple.pop();
        }
    }
    let mut out = Vec::new();
    walk(
        curve,
        base,
        arity,
        Point::Infinity,
        &mut Vec::new(),
        target,
        &mut out,
        meter,
    );
    out
}
#[test]
fn exact_counts_and_prefix_witnesses_match_all_subgroup_targets_with_and_without_messages() {
    let mut meter = Meter::new(Limits::default());
    let (curve, fibres) = fixture(&mut meter);
    let message = Arc::new(
        MembershipMessage::from_fibres(&curve, &fibres, &mut Seeded(1), &mut meter).unwrap(),
    );
    assert_eq!(message.assignments_examined(), 0);
    assert_eq!(message.candidate_points_checked(), 4);
    assert!(message.node_count() > 0 && message.node_count() < 64);
    let targets = group(&curve, &mut meter);
    let base = targets
        .iter()
        .filter(|p| fibres.contains(&curve, p, &mut meter).unwrap())
        .cloned()
        .collect::<Vec<_>>();
    assert_eq!(base, vec![point(0, 1), point(0, 4)]);
    for arity in [2, 3] {
        for compiled in [false, true] {
            let prepared = Prepared::new(
                &curve,
                &fibres,
                arity,
                compiled.then(|| Arc::clone(&message)),
                &mut meter,
            )
            .unwrap();
            let mut counter = Counter::default();
            for target in &targets {
                // Each independent correctness query has its own explicit
                // envelope; this is not a cold end-to-end IC cost total.
                let mut meter = Meter::new(Limits {
                    steps: 500_000_000,
                    ..Limits::default()
                });
                let expected = brute(&curve, &base, arity, target, &mut meter);
                assert_eq!(
                    prepared.count(target, &mut counter, &mut meter).unwrap(),
                    BigUint::from(expected.len())
                );
                let witness = prepared.witness(target, &mut counter, &mut meter).unwrap();
                assert_eq!(witness.is_some(), !expected.is_empty());
                assert!(expected.contains(&witness.unwrap()));
                println!(
                    "{}",
                    serde_json::json!({"arity":arity,"compiled_membership":compiled,"target":target,"count":expected.len(),"graph_edges":prepared.network().edge_count(),"graph_vertices":prepared.network().vertex_count(),"maximum_degree":prepared.network().maximum_degree(),"membership_encodings":message.assignments_examined(),"fibre_lift_candidates":message.candidate_points_checked(),"membership_nodes":message.node_count(),"charged_diagnostic_steps":meter.used,"backend":format!("{:?}",counter.statistics.last_backend)})
                );
            }
            assert!(counter.statistics.contractions > 0);
        }
    }
}
#[test]
fn empty_fibres_are_exact_zero_and_limits_are_unknown() {
    let mut meter = Meter::new(Limits::default());
    let (curve, _) = fixture(&mut meter);
    let fibres = IsogenyFibres::new(&curve, 4u8.into(), vec![0u8.into()], &mut meter).unwrap();
    for compiled in [false, true] {
        let message = compiled
            .then(|| Arc::new(MembershipMessage::compile(&curve, &fibres, &mut meter).unwrap()));
        let prepared = Prepared::new(&curve, &fibres, 2, message, &mut meter).unwrap();
        let mut counter = Counter::default();
        for target in group(&curve, &mut meter) {
            assert_eq!(
                prepared.count(&target, &mut counter, &mut meter).unwrap(),
                0u8.into()
            );
            assert_eq!(
                prepared.witness(&target, &mut counter, &mut meter).unwrap(),
                None
            );
        }
        let mut tiny = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            prepared.count(curve.generator(), &mut counter, &mut tiny),
            Err(Error::Limit(_))
        ));
        let mut tiny = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            prepared.witness(curve.generator(), &mut counter, &mut tiny),
            Err(Error::Limit(_))
        ));
    }
    let mut tiny = Meter::new(Limits {
        steps: 1,
        ..Limits::default()
    });
    assert!(matches!(
        MembershipMessage::compile(&curve, &fibres, &mut tiny),
        Err(Error::Limit(_))
    ));
    let mut tiny = Meter::new(Limits {
        vector: 1,
        ..Limits::default()
    });
    assert!(matches!(
        MembershipMessage::compile(&curve, &fibres, &mut tiny),
        Err(Error::Limit(_))
    ));
    let message =
        MembershipMessage::from_fibres(&curve, &fibres, &mut Seeded(1), &mut meter).unwrap();
    let mut tiny = Meter::new(Limits {
        vector: 1,
        ..Limits::default()
    });
    assert!(matches!(
        message.contains(curve.generator(), &mut tiny),
        Err(Error::Limit(_))
    ));
    let mut tiny = Meter::new(Limits {
        bits: 1,
        ..Limits::default()
    });
    assert!(matches!(
        MembershipMessage::from_fibres(&curve, &fibres, &mut Seeded(1), &mut tiny),
        Err(Error::Limit(_))
    ));
}
#[test]
fn membership_checks_rational_map_poles_canonical_coordinates_and_actual_subgroup() {
    let mut meter = Meter::new(Limits::default());
    let (curve, fibres) = fixture(&mut meter);
    assert!(!fibres
        .contains(&curve, &Point::Infinity, &mut meter)
        .unwrap());
    assert!(!fibres.contains(&curve, &point(4, 0), &mut meter).unwrap());
    assert!(!fibres.contains(&curve, &point(5, 1), &mut meter).unwrap());
    let mut outside = 0;
    for x in 0..5u8 {
        for y in 0..5u8 {
            let p = point(x, y);
            let expected = if x == 4 || !curve.in_subgroup(&p, &mut meter).unwrap() {
                false
            } else {
                let u = BigUint::from((x + 5 - 4) % 5);
                let image = (&u
                    + BigUint::from(2u8)
                    + BigUint::from(3u8) * inverse(&u, &5u8.into()).unwrap())
                    % BigUint::from(5u8);
                image == BigUint::from(1u8)
            };
            assert_eq!(fibres.contains(&curve, &p, &mut meter).unwrap(), expected);
            if curve.contains(&p) && !curve.in_subgroup(&p, &mut meter).unwrap() {
                outside += 1;
            }
        }
    }
    assert!(outside > 0);
}
fn free_input(curve: &Curve, summands: &[Point], target: &Point) -> Vec<bool> {
    let mut out = Vec::new();
    for p in summands.iter().chain(std::iter::once(target)) {
        let target_slot = out.len() == summands.len() * 2 * curve.modulus().bits() as usize;
        let (flag, x, y) = match p {
            Point::Infinity => (true, 0u8.into(), 0u8.into()),
            Point::Affine { x, y } => (false, x.clone(), y.clone()),
        };
        if target_slot {
            out.push(flag);
        }
        for c in [x, y] {
            out.extend((0..curve.modulus().bits()).map(|i| c.bit(i)));
        }
    }
    out
}
#[test]
fn circuit_and_compiled_membership_accept_the_same_complete_signed_relation_language() {
    let mut meter = Meter::new(Limits::default());
    let (curve, fibres) = fixture(&mut meter);
    let message = Arc::new(MembershipMessage::compile(&curve, &fibres, &mut meter).unwrap());
    let plain = Prepared::new(&curve, &fibres, 2, None, &mut meter).unwrap();
    let compiled = Prepared::new(&curve, &fibres, 2, Some(message), &mut meter).unwrap();
    // Every coordinate encoding in the first summand: rational/nonrational,
    // noncanonical, kernel, outside subgroup, and both accepted signs.
    for x in 0..8u8 {
        for y in 0..8u8 {
            let p = point(x, y);
            let q = curve.generator().clone();
            let target = if curve.contains(&p) {
                curve.add(&p, &q, &mut meter).unwrap()
            } else {
                Point::Infinity
            };
            let expected = fibres.contains(&curve, &p, &mut meter).unwrap();
            let input = free_input(&curve, &[p, q], &target);
            for prepared in [&plain, &compiled] {
                let assignment = prepared
                    .network()
                    .witness_from_input_bits(&input, &mut meter)
                    .unwrap();
                assert_eq!(assignment.is_some(), expected);
                if let Some(a) = assignment {
                    assert!(prepared.network().evaluate(&a, &mut meter).unwrap());
                }
            }
        }
    }
    // A genuine intermediate identity chart; inverse pairs are accepted by
    // this ordered language, not silently assigned the archive oracle policy.
    let prepared = Prepared::new(&curve, &fibres, 3, None, &mut meter).unwrap();
    let inverse = curve.negate(curve.generator()).unwrap();
    let input = free_input(
        &curve,
        &[
            curve.generator().clone(),
            inverse,
            curve.generator().clone(),
        ],
        curve.generator(),
    );
    assert!(prepared
        .network()
        .witness_from_input_bits(&input, &mut meter)
        .unwrap()
        .is_some());
}
#[test]
fn invalid_parameters_targets_and_cross_curve_messages_are_rejected() {
    let mut meter = Meter::new(Limits::default());
    let (curve, fibres) = fixture(&mut meter);
    for (kernel, images) in [
        (0u8, vec![1u8]),
        (5, vec![1]),
        (4, vec![]),
        (4, vec![5]),
        (4, vec![1, 1]),
    ] {
        assert!(IsogenyFibres::new(
            &curve,
            kernel.into(),
            images.into_iter().map(BigUint::from).collect(),
            &mut meter
        )
        .is_err());
    }
    assert!(Prepared::new(&curve, &fibres, 1, None, &mut meter).is_err());
    let message = Arc::new(MembershipMessage::compile(&curve, &fibres, &mut meter).unwrap());
    let other_fibres =
        IsogenyFibres::new(&curve, 4u8.into(), vec![0u8.into()], &mut meter).unwrap();
    assert!(Prepared::new(&curve, &other_fibres, 2, Some(message), &mut meter).is_err());
    let other = Curve::new(
        5u8.into(),
        2u8.into(),
        1u8.into(),
        7u8.into(),
        point(0, 1),
        &mut meter,
    )
    .unwrap();
    assert!(Prepared::new(&other, &fibres, 2, None, &mut meter).is_err());
    let prepared = Prepared::new(&curve, &fibres, 2, None, &mut meter).unwrap();
    assert!(prepared
        .count(&point(4, 0), &mut Counter::default(), &mut meter)
        .is_err());
}

#[test]
fn second_field_multiple_fibres_and_all_signed_subgroup_relations_match() {
    let mut meter = Meter::new(Limits::default());
    let curve = Curve::with_cofactor(
        19u8.into(),
        1u8.into(),
        0u8.into(),
        5u8.into(),
        4u8.into(),
        point(5, 4),
        &mut meter,
    )
    .unwrap();
    let fibres =
        IsogenyFibres::new(&curve, 0u8.into(), vec![7u8.into(), 9u8.into()], &mut meter).unwrap();
    let message = Arc::new(MembershipMessage::compile(&curve, &fibres, &mut meter).unwrap());
    assert_eq!(message.assignments_examined(), 1024);
    let plain = Prepared::new(&curve, &fibres, 2, None, &mut meter).unwrap();
    let compiled = Prepared::new(&curve, &fibres, 2, Some(message), &mut meter).unwrap();
    let subgroup = (0..5u8)
        .map(|i| curve.mul(curve.generator(), &i.into(), &mut meter).unwrap())
        .collect::<Vec<_>>();
    let base = &subgroup[1..];
    assert!(base
        .iter()
        .all(|p| fibres.contains(&curve, p, &mut meter).unwrap()));
    for a in base {
        for b in base {
            for target in &subgroup {
                let expected = curve.add(a, b, &mut meter).unwrap() == *target;
                let input = free_input(&curve, &[a.clone(), b.clone()], target);
                for prepared in [&plain, &compiled] {
                    assert_eq!(
                        prepared
                            .network()
                            .witness_from_input_bits(&input, &mut meter)
                            .unwrap()
                            .is_some(),
                        expected
                    );
                }
            }
        }
    }
    // Independent rational-map evaluation on every affine rational point.
    // The codomain here is y²=x³-4x; no general identity proof is asserted.
    for x in 1..19u64 {
        for y in 0..19u64 {
            if y * y % 19 != (x * x * x + x) % 19 {
                continue;
            }
            let inv = (1..19u64).find(|k| k * x % 19 == 1).unwrap();
            let image_x = (x + inv) % 19;
            let image_y = y * (20 - inv * inv % 19) % 19;
            assert_eq!(
                image_y * image_y % 19,
                (image_x * image_x * image_x + 15 * image_x) % 19
            );
            let p = Point::Affine {
                x: x.into(),
                y: y.into(),
            };
            assert_eq!(
                fibres.contains(&curve, &p, &mut meter).unwrap(),
                curve.in_subgroup(&p, &mut meter).unwrap() && [7, 9].contains(&image_x)
            );
        }
    }
}

#[test]
fn sparse_root_compilation_matches_exhaustive_messages_for_every_single_fibre_in_two_fields() {
    let mut meter = Meter::new(Limits::default());
    let (small, _) = fixture(&mut meter);
    let larger = Curve::with_cofactor(
        19u8.into(),
        1u8.into(),
        0u8.into(),
        5u8.into(),
        4u8.into(),
        point(5, 4),
        &mut meter,
    )
    .unwrap();
    for (curve, prime, kernel) in [(small, 5u8, 4u8), (larger, 19, 0)] {
        for image in 0..prime {
            let fibres =
                IsogenyFibres::new(&curve, kernel.into(), vec![image.into()], &mut meter).unwrap();
            let exhaustive = MembershipMessage::compile(&curve, &fibres, &mut meter).unwrap();
            let sparse =
                MembershipMessage::from_fibres(&curve, &fibres, &mut Seeded(99), &mut meter)
                    .unwrap();
            assert_eq!(sparse.assignments_examined(), 0);
            for x in 0..prime + 1 {
                for y in 0..prime + 1 {
                    let p = point(x, y);
                    let expected = fibres.contains(&curve, &p, &mut meter).unwrap();
                    assert_eq!(exhaustive.contains(&p, &mut meter).unwrap(), expected);
                    assert_eq!(sparse.contains(&p, &mut meter).unwrap(), expected);
                }
            }
            assert!(!sparse.contains(&Point::Infinity, &mut meter).unwrap());
        }
    }
}
