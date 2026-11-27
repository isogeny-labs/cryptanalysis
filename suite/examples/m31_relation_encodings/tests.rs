use super::*;
use cryptanalysis_suite::cryptanalysis::f4_fp;

fn control() -> Input {
    Input {
        p: 31,
        a: 1,
        b: 0,
        base: vec![[0, 0], [1, 8]],
        target: Some([1, 8]),
    }
}
fn group_points(curve: &PrimeCurve) -> Vec<PrimePoint> {
    let mut out = vec![PrimePoint::INFINITY];
    for x in 0..curve.p {
        if let Some(y) = curve.sqrt(curve.rhs(x)) {
            let q = PrimePoint::affine(x, y);
            out.push(q);
            if y != 0 {
                out.push(curve.neg(q));
            }
        }
    }
    out
}
fn as_poly(r: &Ring, p: PrimePoint) -> PointP {
    PointP {
        x: r.c(if p.infinity { 0 } else { p.x }),
        y: r.c(if p.infinity { 0 } else { p.y }),
        inf: r.c(u64::from(p.infinity)),
    }
}

#[test]
fn explicit_all_branches_match_independent_group_arithmetic() {
    let input = control();
    input.validate().unwrap();
    let curve = input.curve();
    let points = group_points(&curve);
    let ring = Ring {
        p: 31,
        n: 7,
        domains: vec![None; 7],
        deadline: Instant::now() + Duration::from_secs(30),
        term_cap: 50000,
    };
    let selectors: Vec<_> = (0..5).map(|i| ring.v(i)).collect();
    let mut seen = [0; 5];
    for &a in &points {
        for &b in &points {
            let mut ops = GroupOps::default();
            let output = curve.add(&mut ops, a, b);
            let branch = if a.infinity {
                0
            } else if b.infinity {
                1
            } else if a.x == b.x && (a.y + b.y) % 31 == 0 {
                2
            } else if a.x == b.x {
                3
            } else {
                4
            };
            seen[branch] += 1;
            let mut assignment = vec![0; 7];
            assignment[branch] = 1;
            if branch == 3 || branch == 4 {
                let den = if branch == 3 {
                    2 * a.y % 31
                } else {
                    (b.x + 31 - a.x) % 31
                };
                assignment[6] = pow(den, 29, 31);
                let numerator = if branch == 3 {
                    (3 * mul(a.x, a.x, 31) + curve.a) % 31
                } else {
                    (b.y + 31 - a.y) % 31
                };
                assignment[5] = mul(numerator, assignment[6], 31);
            }
            for proposed in [
                output,
                if output.infinity {
                    points[1]
                } else {
                    PrimePoint::INFINITY
                },
            ] {
                let mut eq = addition(
                    &ring,
                    &as_poly(&ring, a),
                    &as_poly(&ring, b),
                    &as_poly(&ring, proposed),
                    &selectors,
                    &ring.v(5),
                    &ring.v(6),
                    curve.a,
                )
                .unwrap();
                eq.extend(
                    point_equations(&ring, &as_poly(&ring, proposed), curve.a, curve.b).unwrap(),
                );
                assert_eq!(
                    eq.iter().all(|p| ring.eval(p, &assignment) == 0),
                    proposed == output,
                    "a={a:?} b={b:?} proposed={proposed:?}"
                );
            }
        }
    }
    assert!(seen.iter().all(|&n| n > 0));
}

#[test]
fn monolithic_s3_s4_s5_agree_with_finite_signed_group_oracle() {
    let input = control();
    for m in 2..=4 {
        let sys = build(&input, m, Encoding::Monolithic, Duration::from_secs(30)).unwrap();
        for mask in 0..1usize << m {
            let assignment: Vec<_> = (0..m).map(|i| input.base[mask >> i & 1][0]).collect();
            let zero = sys
                .blocks
                .iter()
                .flatten()
                .all(|f| f4_fp::eval(f, &assignment, input.p) == 0);
            let mut raw = assignment.clone();
            raw.push(input.target.unwrap()[0]);
            assert_eq!(
                numeric_summation_root(input.p, input.a, input.b, &raw, Duration::from_secs(2))
                    .unwrap(),
                zero
            );
            assert_eq!(
                zero,
                verify_leaves(&input, &assignment).is_some(),
                "m={m} xs={assignment:?}"
            );
        }
    }
}

#[test]
fn serial_balanced_and_partial_hold_on_finite_native_witnesses() {
    let base = control();
    let curve = base.curve();
    for m in 3..=4 {
        for encoding in [Encoding::Serial, Encoding::Balanced, Encoding::Partial] {
            for word in 0..1usize << (2 * m) {
                let leaves: Vec<_> = (0..m)
                    .map(|i| {
                        let p = base.base[word >> (2 * i) & 1];
                        let q = PrimePoint::affine(p[0], p[1]);
                        if word >> (2 * i + 1) & 1 == 0 {
                            q
                        } else {
                            curve.neg(q)
                        }
                    })
                    .collect();
                let mut ops = GroupOps::default();
                let target = leaves
                    .iter()
                    .fold(curve.identity(), |s, &q| curve.add(&mut ops, s, q));
                if target.infinity {
                    continue;
                }
                let mut input = base.clone();
                input.target = Some([target.x, target.y]);
                let nodes = tree(m, encoding == Encoding::Balanced);
                let mut points = leaves.clone();
                let mut finite = true;
                for node in &nodes {
                    let q = curve.add(&mut ops, points[node.left], points[node.right]);
                    points.push(q);
                    if q.infinity {
                        finite = false;
                    }
                }
                if !finite {
                    continue;
                }
                let sys = build(&input, m, encoding, Duration::from_secs(30)).unwrap();
                let mut assignment: Vec<_> = leaves.iter().map(|q| q.x).collect();
                if encoding == Encoding::Partial && m == 4 {
                    assignment.push(curve.add(&mut ops, leaves[0], leaves[1]).x);
                } else if encoding != Encoding::Partial {
                    assignment.extend(points[m..2 * m - 2].iter().map(|q| q.x));
                }
                assert!(
                    sys.blocks
                        .iter()
                        .flatten()
                        .all(|f| f4_fp::eval(f, &assignment, input.p) == 0),
                    "encoding={encoding:?}, m={m}"
                );
            }
        }
    }
}

#[test]
fn full_explicit_system_accepts_generic_and_infinity_targets_and_rejects_bad_input() {
    let mut input = control();
    input.target = None;
    let system = build(&input, 2, Encoding::Explicit, Duration::from_secs(5)).unwrap();
    // P + (-P) = O, inverse branch; inactive slope/inverse are canonical zero.
    let mut x = vec![0; system.names.len()];
    x[0] = 1;
    x[1] = 1;
    for (i, name) in system.names.iter().enumerate() {
        match name.as_str() {
            "y0" => x[i] = 8,
            "y1" => x[i] = 23,
            "branch2_2" => x[i] = 1,
            _ => {}
        }
    }
    assert!(system
        .blocks
        .iter()
        .flatten()
        .all(|f| f4_fp::eval(f, &x, 31) == 0));
    assert!(build(&input, 2, Encoding::Serial, Duration::from_secs(1))
        .unwrap_err()
        .contains("identity"));
    input.p = 30;
    assert!(input.validate().is_err());
}

#[test]
fn native_f4_and_bounded_root_recovery_find_verified_finite_control() {
    let input = control();
    let system = build(&input, 2, Encoding::Serial, Duration::from_secs(5)).unwrap();
    let result = run(&system, Schedule::Global, Duration::from_secs(5), 8);
    assert!(result["verified"].as_array().unwrap().len() > 0, "{result}");
}

#[test]
fn up_to_returns_basepoint_when_exact_three_point_affine_chart_misses_cancellation() {
    // T=(0,0) has order two. Three copies sum to T, but the finite
    // S3 chart cannot represent the intermediate T+T=O.
    let input = Input {
        p: 31,
        a: 1,
        b: 0,
        base: vec![[0, 0]],
        target: Some([0, 0]),
    };
    let exact = build(&input, 3, Encoding::Serial, Duration::from_secs(2)).unwrap();
    let exact_report = run(&exact, Schedule::Global, Duration::from_secs(2), 8);
    assert_eq!(exact_report["status"], "refuted_encoded_system_only");
    assert!(exact_report["scope"].as_str().unwrap().contains("chart"));
    let result = run_up_to(
        &input,
        3,
        Encoding::Serial,
        Schedule::Global,
        Duration::from_secs(2),
        8,
        Duration::from_secs(1),
    )
    .unwrap();
    assert_eq!(result["status"], "found_shorter");
    assert_eq!(result["first_found_length"], 1);
    assert_eq!(result["verified_witness"]["x"], serde_json::json!([0]));
    assert_eq!(result["length_reports"].as_array().unwrap().len(), 2);
}

#[test]
fn up_to_finds_genuine_two_point_relation_in_original_domain() {
    // P=(1,8), 2P=(0,0); the target is not ±P.
    let input = Input {
        p: 31,
        a: 1,
        b: 0,
        base: vec![[1, 8]],
        target: Some([0, 0]),
    };
    let result = run_up_to(
        &input,
        3,
        Encoding::Serial,
        Schedule::Staged,
        Duration::from_secs(2),
        8,
        Duration::from_secs(1),
    )
    .unwrap();
    assert_eq!(result["status"], "found_shorter");
    assert_eq!(result["first_found_length"], 2);
    assert_eq!(result["verified_witness"]["x"], serde_json::json!([1, 1]));
    assert_eq!(
        result["verified_witness"]["signs"],
        serde_json::json!([1, 1])
    );
    let reports = result["length_reports"].as_array().unwrap();
    assert_eq!(
        reports.last().unwrap()["input"]["base"],
        serde_json::json!([[1, 8]])
    );
    assert!(result["total_f4_ns"].as_u64().unwrap() > 0);
    assert!(result["total_construction_ns"].as_u64().unwrap() > 0);
}

#[test]
fn up_to_identity_and_exhausted_budget_have_explicit_outcomes() {
    let mut input = control();
    input.target = None;
    let result = run_up_to(
        &input,
        4,
        Encoding::Serial,
        Schedule::Global,
        Duration::from_secs(1),
        8,
        Duration::from_secs(1),
    )
    .unwrap();
    assert_eq!(result["status"], "found_shorter");
    assert_eq!(result["first_found_length"], 0);
    let censored = run_up_to(
        &input,
        4,
        Encoding::Serial,
        Schedule::Global,
        Duration::ZERO,
        8,
        Duration::from_secs(1),
    )
    .unwrap();
    assert_eq!(censored["status"], "incomplete");
    assert!(censored["verified_witness"].is_null());
    assert_eq!(
        censored["unresolved_lengths"][0]["reason"],
        "shared_total_deadline"
    );
}

#[test]
fn up_to_chart_refutations_do_not_become_general_absence_claims() {
    // The subgroup generated by T has only O,T; P is outside it. Preserve
    // exact encoded refutations while the dispatcher remains conservative.
    let input = Input {
        p: 31,
        a: 1,
        b: 0,
        base: vec![[0, 0]],
        target: Some([1, 8]),
    };
    let report = run_up_to(
        &input,
        3,
        Encoding::Serial,
        Schedule::Global,
        Duration::from_secs(2),
        8,
        Duration::from_secs(1),
    )
    .unwrap();
    assert_eq!(report["status"], "incomplete");
    assert!(report["verified_witness"].is_null());
    let lengths = report["length_reports"].as_array().unwrap();
    assert_eq!(lengths.len(), 4);
    assert_eq!(lengths[2]["status"], "refuted_encoded_system_only");
    assert_eq!(lengths[3]["status"], "refuted_encoded_system_only");
}
