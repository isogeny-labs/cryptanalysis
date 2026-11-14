use super::*;
use chained_n4_completed_v2::{AdapterV2, NormV2};
use chained_n4_odd_product_models::SourceE;
use chained_n4_odd_product_models::{construct_all, er, even::lift6, k, three};
use chained_n4_odd_source::OddSourceIsogeny;
use chained_n4_public_target::{ghs::EP, CheckedInstance};
use ghs_original_engines::{
    cover,
    pic::{self, PicClass},
};
use isogeny_algos::{
    curve::{self, Pt},
    field::{Field, Rng},
    fpr::ER,
    poly,
};
use serde_json::json;
fn ep(p: Point) -> Pt<ER> {
    match p {
        None => Pt::Inf,
        Some((x, y)) => Pt::Aff(er(x), er(y)),
    }
}
fn kp(p: Pt<ER>) -> Point {
    match p {
        Pt::Inf => None,
        Pt::Aff(x, y) => Some((three(x), three(y))),
    }
}
fn add(c: &SourceE, p: Point, q: Point) -> Point {
    kp(curve::padd(c.field(), c.curve(), &ep(p), &ep(q)))
}
fn gamma(t: &OddSourceIsogeny, p: Point) -> Point {
    kp(t.forward(ep(p)).unwrap())
}
fn delta(t: &OddSourceIsogeny, p: Point) -> Point {
    kp(t.dual(ep(p)).unwrap())
}
fn short(c: &CheckedInstance, p: EP) -> Point {
    match p {
        EP::Inf => None,
        EP::A(x, y) => Some((c.inst.kf.add(&x, &c.short_shift), y)),
    }
}
fn plane_from_ciani(n: &NormNew, xyz: [ER; 3]) -> [ER; 3] {
    let f = &n.f;
    let pivot = xyz.iter().position(|&x| !f.is_zero(x)).unwrap();
    let rows: Vec<[ER; 3]> = (0..3)
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
    std::array::from_fn(|i| {
        let j = (i + 1) % 3;
        let k = (i + 2) % 3;
        f.sub(f.mul(rows[0][j], rows[1][k]), f.mul(rows[0][k], rows[1][j]))
    })
}

#[test]
fn all_three_actual_odd_product_gluings_complete_maps_both52_and_public_targets() {
    let c = CheckedInstance::construct().unwrap();
    let old = NormV2::new(AdapterV2::new(&c).unwrap()).unwrap();
    let transfer = OddSourceIsogeny::construct(&c);
    let source = SourceE::degree13_target(&c, &transfer);
    let f = source.field();
    let ec = source.curve();
    let old_ec = &c.independent_curve;
    let old_sg = short(&c, c.inst.g);
    let sg = kp(source.generator());
    assert_eq!(gamma(&transfer, old_sg), sg);
    let old_g = old.a.transfer_point(&old_sg).unwrap();
    assert!(!old.a.pic.is_zero(&old_g));
    let (models, product_summary) = construct_all(&source, &old.a);
    let mut roots = poly::roots(
        f,
        &vec![ec.b, ec.a, f.zero(), f.one()],
        &mut Rng::new(0x6031),
    );
    roots.sort();
    let sylow: Vec<_> = std::iter::once(None)
        .chain(roots.iter().map(|&x| Some((three(x), [0; 3]))))
        .collect();
    let mut old_roots = poly::roots(
        f,
        &vec![old_ec.b, old_ec.a, f.zero(), f.one()],
        &mut Rng::new(0x6331),
    );
    old_roots.sort();
    let old_sylow: Vec<_> = std::iter::once(None)
        .chain(old_roots.iter().map(|&x| Some((three(x), [0; 3]))))
        .collect();
    let old_kernel: Vec<_> = old_sylow
        .iter()
        .enumerate()
        .filter_map(|(i, p)| {
            old.a
                .pic
                .is_zero(&old.a.transfer_point(p).unwrap())
                .then_some(i)
        })
        .collect();
    assert_eq!(old_kernel, vec![0, 3]);
    let j = curve::jinv(f, ec);
    let js = [j, f.frobenius(j), f.frobenius(f.frobenius(j))];
    assert!(js.iter().all(|&x| x != f.zero() && x != k(1728)));
    assert_eq!(
        js.iter().collect::<std::collections::BTreeSet<_>>().len(),
        3
    );
    let requests = c
        .parse(include_bytes!("../../fixtures/public-five.json"))
        .unwrap();
    let answers: Vec<serde_json::Value> =
        serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
            .unwrap();
    let old_points = old.a.pic.rational_points_bruteforce();
    let mut source_panel = vec![];
    for scalar in [1, 3, 5, 7, 17, 31, 101, c.inst.ell - 2] {
        let x = kp(curve::pmul(f, ec, &ep(sg), scalar as u128));
        for &t in &sylow {
            source_panel.push(add(&source, x, t));
        }
    }
    source_panel.extend(&sylow);
    assert_eq!(source_panel.len(), 36);
    let oldj = curve::jinv(f, old_ec);
    let oldjs = [oldj, f.frobenius(oldj), f.frobenius(f.frobenius(oldj))];
    assert!(js.iter().all(|x| !oldjs.contains(x)));
    println!(
        "N4_ODD_PRODUCT_MAP_INPUT {}",
        json!({"protocol":"56fbbb","old_source_kernel":old_kernel,"source_j_conjugates":js.map(three),"source_j_pairwise_distinct_and_not0or1728":true,"source_panel":source_panel,"target_source":source.identity(),"old_j_conjugates":oldjs.map(three),"original_curve":c.inst.f,"old_P0":old.a.pic.base_point(),"product_stable_count":product_summary["stable_count"],"foreign_source_conjugate_A_B_rejections":2,"actual_mismatched_chain_target_rejection":true,"original_order":c.inst.order,"ell":c.inst.ell})
    );
    let (mut foreign_models, _) = construct_all(&source, &old.a);
    let index = foreign_models
        .iter()
        .position(|m| m.p0.is_some() && m.square_root.is_some())
        .unwrap();
    let mut foreign_a = foreign_models.remove(index);
    foreign_a.source_a[1] = f.add(foreign_a.source_a[1], f.one());
    assert!(Adapter::new(&source, &old.a, foreign_a).is_err());
    let index = foreign_models
        .iter()
        .position(|m| m.p0.is_some() && m.square_root.is_some())
        .unwrap();
    let mut foreign_b = foreign_models.remove(index);
    foreign_b.source_b[2] = f.add(foreign_b.source_b[2], f.one());
    assert!(Adapter::new(&source, &old.a, foreign_b).is_err());
    let original_source = SourceE::original(&c);
    let (mut original_models, _) = construct_all(&original_source, &old.a);
    let index = original_models
        .iter()
        .position(|m| m.p0.is_some() && m.square_root.is_some())
        .unwrap();
    let wrong_target = NormNew::new(
        Adapter::new(&original_source, &old.a, original_models.remove(index)).unwrap(),
    )
    .unwrap();
    assert!(Chain::new(&c, &old, &wrong_target, &transfer).is_err());
    let mut outcomes = vec![];
    let mut negatives = vec![];
    for model in models {
        let id = (model.root_index, model.sign_index);
        let expected_pid = model.row["actual_local_Q_P_R_indices"][1].as_u64().unwrap() as usize;
        let original_control = model.normalized == c.inst.f;
        let kernel_mask = model.kernel_mask;
        if model.p0.is_none() || model.square_root.is_none() {
            assert!(Adapter::new(&source, &old.a, model).is_err());
            negatives.push(id);
            continue;
        }
        eprintln!("complete gluing map candidate {id:?}");
        let n = NormNew::new(Adapter::new(&source, &old.a, model).unwrap()).unwrap();
        let runtime_chain = Chain::new(&c, &old, &n, &transfer).unwrap();
        let p = &n.a.pic;
        let points = p.rational_points_bruteforce();
        assert_eq!(points.len(), 224);
        let g = n.a.transfer_point(&sg).unwrap();
        assert!(!p.is_zero(&g));
        assert!(p.is_zero(&p.mul_scalar(&g, c.inst.ell as u128)));
        assert_eq!(n.norm(&g).unwrap(), add(&source, sg, sg));
        let mut source_rows = vec![];
        let mut infinity = 0;
        for &q in &source_panel {
            let h = n.a.quartic_point(&q).unwrap();
            assert_eq!(h, n.a.quartic_point_with_sign(&q, true).unwrap());
            assert_eq!(n.a.source_point(h).unwrap(), q);
            if matches!(h, QuarticPoint::Infinity(_)) {
                infinity += 1;
            }
            let image = n.a.transfer_point(&q).unwrap();
            let doubled = add(&source, q, q);
            assert_eq!(n.norm(&image).unwrap(), doubled);
            let raw = p.reduce_deg6(&n.a.trace_space(&q).unwrap());
            assert_eq!(p.sub(&raw, n.a.origin_shift()), image);
            let gauge = [1, 1, 0];
            let gauged = p.reduce_deg6(&n.a.trace_space_gauged(&q, Some(gauge)).unwrap());
            assert_eq!(gauged, raw);
            source_rows.push(json!({"source":q,"H":format!("{h:?}"),"PhiPrime":image.key().0.to_vec(),"NPrimePhiPrime":doubled}));
        }
        let mut explicit_infinities = vec![];
        let leading_in_K =
            n.a.sqrt_alpha
                .iter()
                .enumerate()
                .all(|(i, &v)| i == 0 || i == 2 || i == 4 || v == 0);
        let alpha_square = f.pow(n.a.alpha, (223u128.pow(3) - 1) / 2) == f.one();
        assert_eq!(leading_in_K, alpha_square);
        if leading_in_K {
            let u0 = match n.a.raw_p0 {
                Pt::Inf => Pt::Inf,
                Pt::Aff(x, y) => Pt::Aff(
                    er(chained_n4_odd_product_models::three(
                        chained_n4_odd_product_models::even::back6(x),
                    )),
                    er(chained_n4_odd_product_models::three(
                        chained_n4_odd_product_models::even::back6(y),
                    )),
                ),
            };
            let minus_u0 = curve::neg(f, &u0);
            let t = Pt::Aff(n.a.root, f.zero());
            for (label, raw) in [
                ("plusInfinity", minus_u0),
                ("minusInfinity_xNzero", curve::padd(f, ec, &t, &minus_u0)),
            ] {
                let q = kp(raw);
                let h = n.a.quartic_point(&q).unwrap();
                assert!(matches!(h, QuarticPoint::Infinity(_)));
                assert_eq!(h, n.a.quartic_point_with_sign(&q, true).unwrap());
                assert_eq!(n.a.source_point(h).unwrap(), q);
                let image = n.a.transfer_point(&q).unwrap();
                assert_eq!(n.norm(&image).unwrap(), add(&source, q, q));
                explicit_infinities.push(json!({"branch":label,"source":q,"H":format!("{h:?}"),"both_sign_roundtrip_and_NPhi2":true}));
            }
        } else {
            assert_ne!(f.pow(n.a.alpha, (223u128.pow(3) - 1) / 2), f.one());
        }
        let new_kernel: Vec<_> = sylow
            .iter()
            .enumerate()
            .filter_map(|(i, q)| p.is_zero(&n.a.transfer_point(q).unwrap()).then_some(i))
            .collect();
        assert_eq!(new_kernel, vec![0, expected_pid]);
        let new_classes: Vec<_> = points.iter().map(|&x| p.point_class(x)).collect();
        let mut point_rows = vec![];
        let mut group = vec![p.zero()];
        for (&point, y) in points.iter().zip(&new_classes) {
            let norm = n.norm(y).unwrap();
            assert_eq!(n.a.transfer_point(&norm).unwrap(), p.double(y));
            let delta_norm = delta(&transfer, norm);
            let reverse = old.a.transfer_point(&delta_norm).unwrap();
            let old_norm_reverse = old.norm(&reverse).unwrap();
            let gamma_old_norm_reverse = gamma(&transfer, old_norm_reverse);
            let forward = n.a.transfer_point(&gamma_old_norm_reverse).unwrap();
            assert_eq!(forward, p.mul_scalar(y, 52));
            let cof = p.mul_scalar(y, c.inst.ell as u128);
            assert!(p.is_zero(&p.mul_scalar(&cof, 4)));
            let old_len = group.len();
            for t in group.clone() {
                let mut z = t;
                for _ in 0..4 {
                    if !group.contains(&z) {
                        group.push(z.clone());
                    }
                    z = p.add(&z, &cof);
                }
            }
            assert!(group.len() <= 4);
            let _ = old_len;
            point_rows.push(json!({"P":point,"class":y.key().0.to_vec(),"norm":norm,"cofactor":cof.key().0.to_vec(),"delta_norm":delta_norm,"reverse_G":reverse.key().0.to_vec(),"old_norm_G":old_norm_reverse,"gamma_old_norm_G":gamma_old_norm_reverse,"FG":forward.key().0.to_vec(),"PhiNprime2_and_FG52":true}));
        }
        group.sort_by_key(|x| x.key());
        let mut orders = vec![];
        let mut table = vec![];
        for x in &group {
            orders.push((1..=4).find(|&i| p.is_zero(&p.mul_scalar(x, i))).unwrap());
            table.push(
                group
                    .iter()
                    .map(|y| group.iter().position(|z| *z == p.add(x, y)).unwrap())
                    .collect::<Vec<_>>(),
            );
        }
        let mut old_chain_rows = vec![];
        for &point in &old_points {
            let x = old.a.pic.point_class(point);
            let old_norm = old.norm(&x).unwrap();
            let gamma_old_norm = gamma(&transfer, old_norm);
            let forward = n.a.transfer_point(&gamma_old_norm).unwrap();
            let new_norm_forward = n.norm(&forward).unwrap();
            let delta_new_norm_forward = delta(&transfer, new_norm_forward);
            let back = old.a.transfer_point(&delta_new_norm_forward).unwrap();
            assert_eq!(back, old.a.pic.mul_scalar(&x, 52));
            old_chain_rows.push(json!({"P":point,"original_class":x.key().0.to_vec(),"F":forward.key().0.to_vec(),"old_norm":old_norm,"gamma_old_norm":gamma_old_norm,"new_norm_F":new_norm_forward,"delta_new_norm_F":delta_new_norm_forward,"GF":back.key().0.to_vec(),"GF52":true}));
        }
        let chained_g =
            n.a.transfer_point(&gamma(&transfer, old.norm(&old_g).unwrap()))
                .unwrap();
        assert_eq!(chained_g, p.double(&g));
        assert!(!p.is_zero(&chained_g));
        assert!(p.is_zero(&p.mul_scalar(&chained_g, c.inst.ell as u128)));
        let mut publics = vec![];
        for (i, &raw) in requests.iter().enumerate() {
            let q = short(&c, raw);
            assert!(curve::on_curve(f, old_ec, &ep(q)));
            let scalar = answers[i]["original_native_recovered_scalar"]
                .as_u64()
                .unwrap();
            assert!(c.verify_recovered(raw, scalar));
            assert_eq!(curve::pmul(f, old_ec, &ep(old_sg), scalar as u128), ep(q));
            let gamma_q = gamma(&transfer, q);
            let image = n.a.transfer_point(&gamma_q).unwrap();
            assert_eq!(image, p.mul_scalar(&g, scalar as u128));
            let x = old.a.transfer_point(&q).unwrap();
            let old_norm_x = old.norm(&x).unwrap();
            let fx = n.a.transfer_point(&gamma(&transfer, old_norm_x)).unwrap();
            assert_eq!(fx, p.mul_scalar(&chained_g, scalar as u128));
            let back = old
                .a
                .transfer_point(&delta(&transfer, n.norm(&fx).unwrap()))
                .unwrap();
            assert_eq!(back, old.a.pic.mul_scalar(&x, 52));
            assert_eq!(old.a.pic.mul_scalar(&back, 159985), x);
            assert_eq!(runtime_chain.forward_old(&x).unwrap(), fx);
            assert_eq!(runtime_chain.reverse_new(&fx).unwrap(), back);
            assert_eq!(runtime_chain.from_source_odd_coords(q).unwrap(), fx);
            assert_eq!(runtime_chain.recover_source_odd_coords(&fx).unwrap(), q);
            let source_packet = runtime_chain.encode_source(q);
            let target_packet = runtime_chain.from_source(&source_packet).unwrap();
            assert_eq!(n.decode(&target_packet).unwrap(), fx);
            let recovered_packet = runtime_chain.recover_source(&target_packet).unwrap();
            assert_eq!(recovered_packet.coordinates, q);
            assert_eq!(recovered_packet.model, source_packet.model);
            let mut bad_source_packet = source_packet.clone();
            bad_source_packet.model.push('x');
            assert!(runtime_chain.from_source(&bad_source_packet).is_err());
            let mut bad_source_packet = source_packet.clone();
            bad_source_packet.field.push('x');
            assert!(runtime_chain.from_source(&bad_source_packet).is_err());

            publics.push(json!({"index":i,"public_original_short_Q":q,"outside_runtime_scalar":scalar,"gamma_Q":gamma_q,"PhiPrime_gamma_Q":image.key().0.to_vec(),"F_oldPhiQ":fx.key().0.to_vec(),"GF":back.key().0.to_vec(),"inverse159985_GF_recovers_original":true,"reusable_runtime_forward_reverse_source_and_tagged_source_recovery_all_agree":true,"independent_source_and_both_known_answer_equalities":true}));
        }
        for &x in &source_panel[..10] {
            for &y in &source_panel[..10] {
                assert_eq!(
                    n.a.transfer_point(&add(&source, x, y)).unwrap(),
                    p.add(
                        &n.a.transfer_point(&x).unwrap(),
                        &n.a.transfer_point(&y).unwrap()
                    )
                );
            }
        }
        for x in &new_classes[..10] {
            for y in &new_classes[..10] {
                assert_eq!(
                    n.norm(&p.add(x, y)).unwrap(),
                    add(&source, n.norm(x).unwrap(), n.norm(y).unwrap())
                );
            }
        }
        let mut variants = 0;
        for y in new_classes
            .iter()
            .filter(|x| matches!(x, PicClass::Typ(_)))
            .take(16)
        {
            let expected = n.norm_ext(y, 0).unwrap();
            for chart in 1..4 {
                assert_eq!(n.norm_ext(y, chart).unwrap(), expected);
                variants += 1;
            }
        }
        let mut packet = n.a.encode(sg);
        packet.model.push('x');
        assert!(n.a.transfer(&packet).is_err());
        let mut wrong = n.a.encode(sg);
        wrong.field.push('x');
        assert!(n.a.transfer(&wrong).is_err());
        let mut bad = sg.unwrap();
        bad.0[0] += 223;
        assert!(n.a.transfer_point(&Some(bad)).is_err());
        let mut offcurve = sg.unwrap();
        while curve::on_curve(f, ec, &ep(Some(offcurve))) {
            offcurve.1[0] = (offcurve.1[0] + 1) % 223;
        }
        assert!(n.a.transfer_point(&Some(offcurve)).is_err());
        assert!(n.a.trace_space_gauged(&sg, Some([0; 3])).is_err());
        let mut cp = n.encode(&g);
        cp.model.push('x');
        assert!(n.decode(&cp).is_err());
        let mut cp = n.encode(&g);
        cp.key[1] = 223;
        assert!(n.decode(&cp).is_err());
        let mut geometric = vec![];
        let mut raw_infinity_counts = [0usize; 2];
        let mut doubled_jet_mutations = 0;
        let mut rng = Rng::new(0x6032);
        let f6 = &n.f;
        for axis in 0..3 {
            let j = (axis + 1) % 3;
            let l = (axis + 2) % 3;
            let q = &n.a.ciani;
            let diag = [q[0], q[1], q[2]];
            let cross = if j == 0 && l == 1 || j == 1 && l == 0 {
                q[3]
            } else if j == 1 && l == 2 || j == 2 && l == 1 {
                q[4]
            } else {
                q[5]
            };
            let polynomial = vec![
                lift6(diag[j]),
                f6.zero(),
                lift6(cross),
                f6.zero(),
                lift6(diag[l]),
            ];
            let rs = poly::roots(f6, &polynomial, &mut rng);
            assert_eq!(rs.len(), 4);
            for r in rs {
                let mut xyz = [f6.zero(); 3];
                xyz[j] = f6.one();
                xyz[l] = r;
                let w = plane_from_ciani(&n, xyz);
                assert!(n.point_on_quartic(w));
                let image = n.cover(w).unwrap();
                assert!(curve::on_curve(f6, &n.elliptic, &image));
                assert!(!f6.is_zero(poly::eval(f6, &poly::derivative(f6, &polynomial), r)));
                if axis == 2 {
                    match image {
                        Pt::Inf => raw_infinity_counts[0] += 1,
                        Pt::Aff(x, y) => {
                            assert_eq!(x, lift6(n.a.root));
                            assert!(f6.is_zero(y));
                            raw_infinity_counts[1] += 1;
                        }
                    }
                }
                let mut jets: [Vec<ER>; 3] = std::array::from_fn(|i| vec![xyz[i]]);
                jets[axis] = vec![f6.zero(), f6.one()];
                let mut curve_jet = vec![];
                for (ex, co) in [
                    [4, 0, 0],
                    [0, 4, 0],
                    [0, 0, 4],
                    [2, 2, 0],
                    [0, 2, 2],
                    [2, 0, 2],
                ]
                .into_iter()
                .zip(n.a.ciani)
                {
                    let mut term = vec![lift6(co)];
                    for (i, count) in ex.into_iter().enumerate() {
                        for _ in 0..count {
                            term = poly::mul(f6, &term, &jets[i]);
                        }
                    }
                    curve_jet = poly::add(f6, &curve_jet, &term);
                }
                let eps2 = vec![f6.zero(), f6.zero(), f6.one()];
                assert!(poly::divrem(f6, &curve_jet, &eps2).1.is_empty());
                let conic = poly::scale(
                    f6,
                    &poly::mul(f6, &jets[axis], &jets[axis]),
                    f6.mul(k(2), lift6(diag[axis])),
                );
                assert!(!f6.is_zero(diag[axis]));
                assert!(poly::divrem(f6, &conic, &eps2).1.is_empty());
                assert!(!poly::divrem(f6, &jets[axis], &eps2).1.is_empty());
                doubled_jet_mutations += 1;
                geometric.push(json!({"sign_axis":axis,"Ciani":xyz.map(chained_n4_odd_product_models::six),"ordinary_branch_local_index":2,"source_cover":format!("{image:?}")}));
            }
        }
        let mut triple_trials = vec![];
        let mut found_triple = false;
        for &point in &points {
            let class = triple_jet(&n, point).unwrap();
            if let Ok((mult, changed)) = n.multiplicity_audit(&class) {
                triple_trials.push(json!({"P":point,"multiplicities":mult,"omitting_multiplicity_changes_norm":changed}));
                if mult.contains(&3) && changed {
                    found_triple = true;
                    break;
                }
            }
        }
        assert!(found_triple);
        assert_eq!(raw_infinity_counts, [2, 2]);
        assert_eq!(doubled_jet_mutations, 12);
        let (mut alternate_models, _) = construct_all(&source, &old.a);
        let position = alternate_models
            .iter()
            .position(|m| (m.root_index, m.sign_index) == id)
            .unwrap();
        let alternate_model = alternate_models.remove(position);
        let alternate =
            Adapter::with_base_point(&source, &old.a, alternate_model, Some(points[1])).unwrap();
        assert_ne!(alternate.model_tag, n.a.model_tag);
        assert!(alternate.transfer(&n.a.encode(sg)).is_err());
        assert!(n.a.transfer(&alternate.encode(sg)).is_err());
        assert!(alternate
            .pic
            .is_zero(&alternate.transfer_point(&None).unwrap()));
        println!(
            "N4_ODD_PRODUCT_MAP_COVERAGE {}",
            json!({"candidate":id,"alpha_square_K":alpha_square,"both_inverse_infinities":explicit_infinities,"unreachable_reason_if_empty":if alpha_square{None}else{Some("alpha nonsquare in K; neither infinity H point is K-rational")},"geometric_raw_infinity_plus_minus_counts":raw_infinity_counts,"all12_dualnumber_doublefibre_vs_wronglinear_mutations":doubled_jet_mutations,"alternate_actual_P0":alternate.pic.base_point(),"alternate_model_tag":alternate.model_tag,"both_cross_P0_tag_rejections_and_new_geometric_zero_origin":true,"independent_offcurve_rejection":true})
        );
        assert!(
            !original_control,
            "new source product unexpectedly has literal old quartic"
        );
        let trivial_sign: Option<i32> = None;
        let mut old_group = vec![old.a.pic.zero()];
        for &point in &old_points {
            let cof = old
                .a
                .pic
                .mul_scalar(&old.a.pic.point_class(point), c.inst.ell as u128);
            for start in old_group.clone() {
                let mut z = start;
                for _ in 0..4 {
                    if !old_group.contains(&z) {
                        old_group.push(z.clone());
                    }
                    z = old.a.pic.add(&z, &cof);
                }
            }
            assert!(old_group.len() <= 4);
        }
        old_group.sort_by_key(|x| x.key());
        assert_eq!(old_group.len(), 4);
        assert_eq!(group.len(), 4);
        let old_cofactor_F: Vec<_> = old_group
            .iter()
            .map(|x| {
                n.a.transfer_point(&gamma(&transfer, old.norm(x).unwrap()))
                    .unwrap()
            })
            .collect();
        assert!(runtime_chain.from_source_odd_coords(old_sylow[1]).is_err());
        assert!(runtime_chain
            .from_source_odd_coords(Some(([0; 3], [0; 3])))
            .is_err());
        let mut noncanonical = old_sg.unwrap();
        noncanonical.0[0] += 223;
        assert!(runtime_chain
            .from_source_odd_coords(Some(noncanonical))
            .is_err());
        for x in group.iter().filter(|x| !p.is_zero(x)) {
            assert!(runtime_chain.recover_source_odd_coords(x).is_err());
        }
        assert!(p.is_zero(&runtime_chain.from_source_odd_coords(None).unwrap()));
        assert_eq!(
            runtime_chain.recover_source_odd_coords(&p.zero()).unwrap(),
            None
        );
        let F_kernel: Vec<_> = old_cofactor_F
            .iter()
            .enumerate()
            .filter_map(|(i, x)| p.is_zero(x).then_some(i))
            .collect();
        let new_cofactor_G: Vec<_> = group
            .iter()
            .map(|x| {
                old.a
                    .transfer_point(&delta(&transfer, n.norm(x).unwrap()))
                    .unwrap()
            })
            .collect();
        let G_kernel: Vec<_> = new_cofactor_G
            .iter()
            .enumerate()
            .filter_map(|(i, x)| old.a.pic.is_zero(x).then_some(i))
            .collect();
        let outcome = json!({"candidate":id,"quartic":n.a.core.quartic,"P0":p.base_point(),"Jacobian_model_tag":n.model_tag,"raw_actual_P0_image_over_L6":format!("{:?}",n.a.raw_p0),"raw_actual_trace_origin":n.a.origin_shift().key().0.to_vec(),"actual_geometric_Dinf_offset":format!("{:?}",n.offset),"all224_line_offsets_equal":true,"all36_source_rows":source_rows,"all224_new_class_rows":point_rows,"all224_old_chain_rows":old_chain_rows,"allfive_public_targets":publics,"all100_Phi_addition_and100_Norm_addition_pairs":true,"all48_alternate_chart_checks":variants,"source_rational_PhiPrime_kernel_indices":new_kernel,"HLP_kernel_mask":kernel_mask,"cofactor_classes":group.iter().map(|x|x.key().0.to_vec()).collect::<Vec<_>>(),"cofactor_orders":orders,"cofactor_table":table,"old_cofactor_classes":old_group.iter().map(|x|x.key().0.to_vec()).collect::<Vec<_>>(),"all4_old_cofactor_F":old_cofactor_F.iter().map(|x|x.key().0.to_vec()).collect::<Vec<_>>(),"F_rational_cofactor_kernel_indices":F_kernel,"all4_new_cofactor_G":new_cofactor_G.iter().map(|x|x.key().0.to_vec()).collect::<Vec<_>>(),"G_rational_cofactor_kernel_indices":G_kernel,"geometric_12_branch_points":geometric,"triple_trials":triple_trials,"multiplicity_omission_control_changes_norm":true,"reachable_infinity_source_panel_count":infinity,"literal_original_quartic_control":original_control,"literal_control_fixed_source_sign":trivial_sign,"endpoint_distinction":"written unique old F223 polarized2kernel plus disjoint elliptic j-conjugates exclude Aprime isomorphic to A;not coefficient differences;no mutual new or extension-field Jacobian claim","field_model_gauge_noncanonical_rejections":6,"reusable_runtime_odd_source_forward_and_recovery_with_tag_subgroup_and_roundtrip_checks":true,"status":"actualrationalgroupmaps/both2/both52/nativefinitepanels;globalgeometrywritten/partialformal/costopen"});
        println!("N4_ODD_PRODUCT_MAP_CANDIDATE {}", outcome);
        outcomes.push(json!({"candidate":id,"original_control":original_control,"kernel":kernel_mask,"source_kernel":new_kernel,"cofactor_orders":orders}));
    }
    assert_eq!(outcomes.len(), 3);
    assert_eq!(negatives, vec![(0, 0), (0, 1), (2, 0)]);
    println!(
        "N4_ODD_PRODUCT_MAP_SCOPE {}",
        json!({"all_three_eligible_models":outcomes,"three_nonsquare_rejections":negatives,"source_maps":"no scalar witness in runtime","both_compositions2_and_both_chain_compositions52":true,"allfive_public_targets_each":true,"full_geometric_formalization":"open","accounting":"not a benchmark/allmapcostcountersnotadmitted","scope":"finitecorrectness observations/globalCianiandendpointproofwrittennext"})
    );
}

fn series_mul(f: &cover::Fq, a: [u64; 3], b: [u64; 3]) -> [u64; 3] {
    std::array::from_fn(|k| (0..=k).fold(0, |s, i| f.add(s, f.mul(a[i], b[k - i]))))
}
fn restriction(f: &cover::Fq, coords: [[u64; 3]; 3], mon: (u8, u8, u8)) -> [u64; 3] {
    let mut result = [1, 0, 0];
    for (i, power) in [mon.0, mon.1, mon.2].into_iter().enumerate() {
        for _ in 0..power {
            result = series_mul(f, result, coords[i]);
        }
    }
    result
}
fn curve_series(n: &NormNew, coords: [[u64; 3]; 3]) -> [u64; 3] {
    let f = &n.a.field.f;
    let mut value = [0; 3];
    for (mon, c) in pic::mons_of_degree(4).into_iter().zip(n.a.core.quartic) {
        let term = restriction(f, coords, mon);
        for i in 0..3 {
            value[i] = f.add(value[i], f.mul(c, term[i]));
        }
    }
    value
}
fn triple_jet(n: &NormNew, p: [u32; 3]) -> Result<PicClass, String> {
    let f = &n.a.field.f;
    let pivot = p.iter().position(|&x| x != 0).unwrap();
    let free: Vec<_> = (0..3).filter(|&i| i != pivot).collect();
    let (mut x, mut y) = (free[0], free[1]);
    let base: [[u64; 3]; 3] = p.map(|v| [v as u64, 0, 0]);
    let mut varying = base;
    varying[x][1] = 1;
    let mut fx = curve_series(n, varying)[1];
    varying = base;
    varying[y][1] = 1;
    let mut fy = curve_series(n, varying)[1];
    if fy == 0 {
        std::mem::swap(&mut x, &mut y);
        std::mem::swap(&mut fx, &mut fy);
    }
    if fy == 0 {
        return Err("singular affine jet".into());
    }
    let mut coords = base;
    coords[x][1] = 1;
    coords[y][1] = f.neg(f.mul(fx, f.inv(fy)));
    coords[y][2] = f.neg(f.mul(curve_series(n, coords)[2], f.inv(fy)));
    assert_eq!(curve_series(n, coords), [0; 3]);
    let columns: Vec<_> = pic::mons_of_degree(2)
        .into_iter()
        .map(|m| restriction(f, coords, m))
        .collect();
    let equations = (0..3)
        .map(|i| columns.iter().map(|v| v[i] as u32).collect())
        .collect();
    let rows = n.a.pic.linear_kernel(equations, 6);
    if rows.len() != 3 {
        return Err("jet rank".into());
    }
    Ok(n.a.pic.class_from_conics(rows))
}
