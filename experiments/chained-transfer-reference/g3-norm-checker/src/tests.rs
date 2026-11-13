use super::*;
use std::collections::{HashMap, HashSet};

fn ep(p: Point) -> Pt<ER> {
    match p {
        None => Pt::Inf,
        Some((x, y)) => Pt::Aff(er(x), er(y)),
    }
}
fn kp(p: Pt<ER>) -> Point {
    match p {
        Pt::Inf => None,
        Pt::Aff(x, y) => {
            assert!(x[3..].iter().chain(y[3..].iter()).all(|&v| v == 0));
            Some(([x[0], x[1], x[2]], [y[0], y[1], y[2]]))
        }
    }
}
fn source(n: &Norm) -> (FpR, Curve<ER>) {
    (
        FpR::from_modulus(n.a.q, &n.a.modulus),
        Curve::new(er(n.a.core.ea), er(n.a.core.eb)),
    )
}
fn generator(n: &Norm, ps: &[Point]) -> Point {
    let (f, c) = source(n);
    ps.iter()
        .find_map(|&p| {
            let g = curve::pmul(&f, &c, &ep(p), 4);
            (g != Pt::Inf && curve::pmul(&f, &c, &g, n.a.ell as u128) == Pt::Inf).then_some(kp(g))
        })
        .unwrap()
}
fn norm_table(n: &Norm, classes: &[PicClass]) -> HashMap<PicKey, Point> {
    classes
        .iter()
        .map(|x| (x.key(), n.norm(x).unwrap()))
        .collect()
}
fn plane_from_ciani(n: &Norm, xyz: GeoPoint) -> GeoPoint {
    let f = &n.f;
    let pivot = xyz.iter().position(|&x| !f.is_zero(x)).unwrap();
    let rows: Vec<GeoPoint> = (0..3)
        .filter(|&i| i != pivot)
        .map(|i| {
            std::array::from_fn(|j| {
                f.sub(
                    f.mul(xyz[pivot], n.embed(n.a.core.omi[i][j])),
                    f.mul(xyz[i], n.embed(n.a.core.omi[pivot][j])),
                )
            })
        })
        .collect();
    // Intersection of the two actual plane linear forms, using original field ops.
    std::array::from_fn(|i| {
        let j = (i + 1) % 3;
        let k = (i + 2) % 3;
        f.sub(f.mul(rows[0][j], rows[1][k]), f.mul(rows[0][k], rows[1][j]))
    })
}

#[test]
fn independent_curve_counts_fields_models_and_complete_generator_bfs() {
    for (q, expected) in [(5, [6, 26, 192]), (7, [8, 50, 380]), (11, [12, 122, 1308])] {
        let n = Norm::new(q).unwrap();
        let (counts, order) = n.curve_counts().unwrap();
        assert_eq!(counts, expected);
        assert_eq!(order, n.a.expected_order);
        assert_eq!(n.source_points().len(), order as usize);
        let (classes, generators) = n.jacobian_domain().unwrap();
        assert_eq!(classes.len(), order as usize);
        assert!(!generators.is_empty());
        assert!(isogeny_algos::field::is_prime(n.a.ell));
        assert_eq!(order, 4 * n.a.ell);
        let offsets = n.line_offsets().unwrap();
        assert_eq!(offsets.len(), q as usize + 1);
        assert!(offsets.iter().all(|&p| p == n.offset));
        let f3 = FpR::from_modulus(q, &n.a.modulus);
        for i in 0..q.pow(3) {
            let x = coeffs(q, i, 3);
            let x3 = [x[0], x[1], x[2]];
            assert_eq!(n.project_k(n.embed(x3)).unwrap(), x3);
            assert_eq!(
                n.embed([f3.frobenius(x)[0], f3.frobenius(x)[1], f3.frobenius(x)[2]]),
                n.f.pow(n.embed(x3), q as u128)
            );
        }
        println!(
            "G3_NORM_COUNTS {}",
            serde_json::json!({"q":q,"curve_counts_q_q2_q3":counts,"independent_RR_Newton_Jac_order":order,"BFS_classes":classes.len(),"rational_point_generators":generators.len(),"plane_line_offsets":offsets.len(),"source_points":n.source_points().len()})
        );
    }
}
#[test]
fn every_jacobian_class_algebra_norm_and_all_generating_edges() {
    for q in [5, 7, 11] {
        let n = Norm::new(q).unwrap();
        let (classes, gens) = n.jacobian_domain().unwrap();
        let values = norm_table(&n, &classes);
        let (f, c) = source(&n);
        let mut exceptional = 0;
        let mut nilpotent = 0;
        let mut wrong_reduced_diff = 0;
        let mut alternate = 0;
        for x in &classes {
            let nx = values[&x.key()];
            assert!(curve::on_curve(&f, &c, &ep(nx)));
            assert_eq!(
                n.norm(&n.a.pic.neg(x)).unwrap(),
                kp(curve::neg(&f, &ep(nx)))
            );
            assert_eq!(
                n.norm(&n.a.pic.double(x)).unwrap(),
                kp(curve::padd(&f, &c, &ep(nx), &ep(nx)))
            );
            for g in &gens {
                let sum = n.a.pic.add(x, g);
                assert_eq!(
                    values[&sum.key()],
                    kp(curve::padd(&f, &c, &ep(nx), &ep(values[&g.key()])))
                );
            }
            match x {
                PicClass::Exc(_) => exceptional += 1,
                PicClass::Typ(m) => {
                    let a = Algebra::new(&n, m, 0).unwrap();
                    let cycle = a.cycle(&n).unwrap();
                    assert_eq!(cycle.iter().map(|x| x.1).sum::<usize>(), 3);
                    if cycle.iter().any(|x| x.1 > 1) {
                        nilpotent += 1;
                        let reduced: Vec<_> = cycle.iter().map(|&(p, _)| (p, 1)).collect();
                        let wrong = curve::padd(
                            &n.f,
                            &n.elliptic,
                            &n.weighted_sum(&reduced).unwrap(),
                            &curve::neg(&n.f, &n.offset),
                        );
                        wrong_reduced_diff += usize::from(wrong != n.norm_ext(x, 0).unwrap());
                    }
                    if alternate < 8 {
                        assert_eq!(n.norm_ext(x, 1).unwrap(), n.norm_ext(x, 0).unwrap());
                        alternate += 1;
                    }
                }
            }
        }
        assert_eq!(exceptional, n.a.pic.rational_points_bruteforce().len());
        assert!(nilpotent > 0);
        assert!(wrong_reduced_diff > 0);
        assert!(alternate > 0);
        let kernel = values.values().filter(|p| p.is_none()).count();
        let images: HashSet<_> = values.values().copied().collect();
        println!(
            "G3_NORM_CLASSES {}",
            serde_json::json!({"q":q,"all_classes":classes.len(),"all_generating_edges":classes.len()*gens.len(),"exceptional":exceptional,"nonreduced_typical":nilpotent,"wrong_reduced_cycle_valid_different":wrong_reduced_diff,"alternate_affine_monogenic_charts":alternate,"observed_norm_kernel":kernel,"distinct_norm_images":images.len()})
        );
    }
}
#[test]
fn both_actual_compositions_every_point_class_and_all_odd_scalars() {
    for q in [5, 7, 11] {
        let n = Norm::new(q).unwrap();
        let ps = n.source_points();
        let (f, c) = source(&n);
        let (classes, _) = n.jacobian_domain().unwrap();
        let values = norm_table(&n, &classes);
        for &p in &ps {
            let image = n.a.transfer_point(&p).unwrap();
            assert_eq!(n.norm(&image).unwrap(), kp(curve::pmul(&f, &c, &ep(p), 2)));
        }
        for j in &classes {
            let p = values[&j.key()];
            assert_eq!(n.a.transfer_point(&p).unwrap(), n.a.pic.double(j));
        }
        let g = generator(&n, &ps);
        let h = n.a.transfer_point(&g).unwrap();
        assert!(!n.a.pic.is_zero(&h));
        assert!(n.a.pic.is_zero(&n.a.pic.mul_scalar(&h, n.a.ell as u128)));
        let half = n.a.ell.div_ceil(2);
        let mut odd_images = HashSet::new();
        for k in 0..n.a.ell {
            let p = kp(curve::pmul(&f, &c, &ep(g), k as u128));
            let j = n.a.pic.mul_scalar(&h, k as u128);
            assert_eq!(n.a.transfer_point(&p).unwrap(), j);
            let recovered = kp(curve::pmul(&f, &c, &ep(n.norm(&j).unwrap()), half as u128));
            assert_eq!(recovered, p);
            odd_images.insert(j.key());
        }
        assert_eq!(odd_images.len(), n.a.ell as usize);
        let mut odd_domain = HashSet::new();
        for j in &classes {
            let x = n.a.pic.mul_scalar(j, 4);
            let p = values[&x.key()];
            let halfp = kp(curve::pmul(&f, &c, &ep(p), half as u128));
            assert_eq!(n.a.transfer_point(&halfp).unwrap(), x);
            odd_domain.insert(x.key());
        }
        assert_eq!(odd_domain, odd_images);
        println!(
            "G3_NORM_COMPOSITIONS {}",
            serde_json::json!({"q":q,"source_points_norm_phi_2":ps.len(),"Jac_classes_phi_norm_2":classes.len(),"ell":n.a.ell,"all_odd_scalars":odd_images.len(),"independent_odd_class_domain":odd_domain.len(),"half_recovery_coefficient":half,"source_generator":g})
        );
    }
}
#[test]
fn strict_encoded_classes_origin_infinity_and_nontrivial_controls() {
    for q in [5, 7, 11] {
        let n = Norm::new(q).unwrap();
        let (classes, _) = n.jacobian_domain().unwrap();
        let typ = classes
            .iter()
            .find(|x| matches!(x, PicClass::Typ(_)))
            .unwrap();
        let exc = classes
            .iter()
            .find(|x| matches!(x,PicClass::Exc(p) if *p!=n.a.pic.base_point()))
            .unwrap();
        let zero = n.a.pic.zero();
        assert_eq!(n.norm(&zero).unwrap(), None);
        let packets = vec![n.encode(&zero), n.encode(typ), n.encode(exc)];
        for x in &packets {
            assert_eq!(n.decode(x).unwrap().key().0, x.key);
            n.evaluate(x).unwrap();
        }
        let mut bad = n.encode(typ);
        bad.field.push('x');
        assert!(n.decode(&bad).is_err());
        let mut bad = n.encode(typ);
        bad.model.push('x');
        assert!(n.decode(&bad).is_err());
        let mut bad = n.encode(typ);
        bad.key[1] = q as u32;
        assert!(n.decode(&bad).is_err());
        let mut bad = n.encode(typ);
        bad.key[0] = 2;
        assert!(n.decode(&bad).is_err());
        let mut bad = n.encode(&zero);
        bad.key[4] = 1;
        assert!(n.decode(&bad).is_err());
        let mut bad = n.encode(typ);
        bad.key[1..].fill(0);
        assert!(n.decode(&bad).is_err());
        let wrong_shift = n
            .cover(n.a.pic.base_point().map(|x| n.f.from_u64(x as u64)))
            .unwrap();
        let algebra = Algebra::new(
            &n,
            match typ {
                PicClass::Typ(m) => m,
                _ => unreachable!(),
            },
            0,
        )
        .unwrap();
        let push = n.weighted_sum(&algebra.cycle(&n).unwrap()).unwrap();
        let correct = n.norm_ext(typ, 0).unwrap();
        let wrong_plane_origin =
            curve::padd(&n.f, &n.elliptic, &push, &curve::neg(&n.f, &wrong_shift));
        let omitted_origin_differs = push != correct;
        assert_eq!(omitted_origin_differs, n.offset != Pt::Inf);
        let wrong_plane_origin_differs = wrong_plane_origin != correct;
        assert_eq!(wrong_plane_origin_differs, wrong_shift != n.offset);
        let f = &n.f;
        let mut infinity_controls = 0;
        for x in [f.one(), f.neg(f.one())] {
            for y in [f.one(), f.neg(f.one())] {
                let w = plane_from_ciani(&n, [x, y, f.one()]);
                assert!(n.point_on_quartic(w));
                let positive = Pt::Inf;
                let negative = Pt::Aff(n.shift, f.neg(n.alpha));
                let (expected, wrong) = if y == f.one() {
                    (positive, negative)
                } else {
                    (negative, positive)
                };
                assert_eq!(n.cover(w).unwrap(), expected);
                assert!(curve::on_curve(f, &n.elliptic, &wrong));
                assert_ne!(wrong, expected);
                infinity_controls += 1;
            }
        }
        let u0 = vec![n.embed(n.a.uc), n.embed(n.a.ub), f.one()];
        let u1: Vec<_> = u0.iter().map(|&v| f.pow(v, q as u128)).collect();
        let u2: Vec<_> = u0.iter().map(|&v| f.pow(v, q.pow(2) as u128)).collect();
        let mut finite_branch_controls = 0;
        for t in poly::roots(f, &u0, &mut Rng::new(2026111301 + q)) {
            let ratio = f.div(poly::eval(f, &u1, t), poly::eval(f, &u2, t));
            for x in poly::roots(
                f,
                &vec![f.neg(ratio), f.zero(), f.one()],
                &mut Rng::new(2026111302 + q),
            ) {
                let w = plane_from_ciani(&n, [x, f.one(), f.zero()]);
                assert!(n.point_on_quartic(w));
                let xx = f.mul(f.from_u64(2), f.add(f.add(f.sq(t), f.mul(n.b, t)), n.s));
                let yy = f.add(
                    f.add(f.mul(f.mul(f.from_u64(2), xx), t), f.mul(n.b, xx)),
                    n.alpha,
                );
                assert_eq!(n.cover(w).unwrap(), Pt::Aff(f.add(xx, n.shift), yy));
                finite_branch_controls += 1;
            }
        }
        assert_eq!(infinity_controls, 4);
        assert_eq!(finite_branch_controls, 4);
        let cube = poly::mul(
            f,
            &poly::mul(
                f,
                &vec![f.neg(f.one()), f.one()],
                &vec![f.neg(f.one()), f.one()],
            ),
            &vec![f.neg(f.one()), f.one()],
        );
        assert_eq!(
            n.roots_with_multiplicity(&cube).unwrap(),
            vec![(f.one(), 3)]
        );
        let offcurve = [f.one(), f.zero(), f.zero()];
        assert!(!n.point_on_quartic(offcurve));
        assert!(n.cover(offcurve).is_err());
        let mut bad = n.encode(&zero);
        bad.key[1..4].copy_from_slice(&[1, 0, 0]);
        assert!(n.decode(&bad).is_err());
        let g = generator(&n, &n.source_points());
        let gp = match g {
            None => panic!("nonzero generator"),
            Some((x, y)) => Pt::Aff(n.embed(x), n.embed(y)),
        };
        let wrong = curve::padd(&n.f, &n.elliptic, &n.norm_ext(&zero, 0).unwrap(), &gp);
        assert_ne!(wrong, Pt::Inf);
        assert!(curve::on_curve(&n.f, &n.elliptic, &wrong));
        let request = serde_json::json!({"schema":"g3-canonical-norm/v1","q":q,"classes":packets});
        assert_eq!(
            parse_request(&serde_json::to_vec(&request).unwrap())
                .unwrap()
                .classes
                .len(),
            3
        );
        let mut bad = request.clone();
        bad["scalar"] = serde_json::json!(7);
        assert!(parse_request(&serde_json::to_vec(&bad).unwrap()).is_err());
        let mut bad = request.clone();
        bad["schema"] = serde_json::json!("unknown");
        assert!(parse_request(&serde_json::to_vec(&bad).unwrap()).is_err());
        assert!(parse_request(&vec![b' '; MAX_INPUT_BYTES + 1]).is_err());
        println!(
            "G3_NORM_CONTROLS {}",
            serde_json::json!({"q":q,"foreign_field_model_noncanonical_rank_tag_reject":true,"wrong_origin_valid_different":true,"actual_omitted_origin_differs":omitted_origin_differs,"actual_pi0P0_wrong_origin_differs":wrong_plane_origin_differs,"completed_infinity_sign_controls":infinity_controls,"geometric_u0_zero_branch_controls":finite_branch_controls,"triple_root_multiplicity":3,"offcurve_point_and_packet_rejected":true,"plane_offset_nonzero":n.offset!=Pt::Inf,"pi0_basepoint":format!("{wrong_shift:?}"),"bounded_cli_request":request})
        );
    }
}
