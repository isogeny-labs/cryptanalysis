use super::*;
use isogeny_algos::{curve::Curve, field::Rng};
use std::collections::BTreeMap;
fn emit(tag: &str, value: Value) {
    println!("{tag} {value}")
}
fn offset_json(p: Pt<ER>) -> Value {
    use chained_n4_paired_fourth_preflight::models::six;
    match p {
        Pt::Inf => Value::Null,
        Pt::Aff(x, y) => json!([six(x), six(y)]),
    }
}
fn two_points(g: &Geometry) -> Vec<Pt<ER>> {
    let roots: Vec<[u64; 3]> =
        serde_json::from_value(g.summary["actual_source_2torsion_roots"].clone()).unwrap();
    assert_eq!(roots.len(), 3);
    let mut points = vec![Pt::Inf];
    points.extend(
        roots
            .into_iter()
            .map(|x| Pt::Aff(er(x), g.source.field().zero())),
    );
    for p in &points {
        assert!(curve::on_curve(g.source.field(), g.source.curve(), p));
        assert_eq!(
            curve::pmul(g.source.field(), g.source.curve(), p, 2),
            Pt::Inf
        )
    }
    points
}
fn independent(
    old: &ThirdHop,
    fourth: &PairedFourth<'_>,
    from: usize,
    to: usize,
    p: Pt<ER>,
) -> Pt<ER> {
    let edge = fourth.branch(false);
    match (from, to) {
        (0, 1) => old.forward(p).unwrap(),
        (1, 0) => old.dual(p).unwrap(),
        (1, 2) => edge.forward(p).unwrap(),
        (2, 1) => edge.dual(p).unwrap(),
        (0, 2) => edge.forward(old.forward(p).unwrap()).unwrap(),
        (2, 0) => old.dual(edge.dual(p).unwrap()).unwrap(),
        _ => panic!("unknown independent direction"),
    }
}
fn check_case(
    rt: &Runtime,
    old: &ThirdHop,
    fourth: &PairedFourth<'_>,
    from: usize,
    to: usize,
    class: &PicClass,
) -> Value {
    let s = &rt.geometry[from];
    let t = &rt.geometry[to];
    let input = rt.admit(from, &rt.encode(from, class)).unwrap();
    let p = curve::pmul(s.source.field(), s.source.curve(), &input.norm, HALF);
    let source_phi = s.prime.a.transfer_point(&kp(p)).unwrap();
    assert_eq!(
        &source_phi, class,
        "actual Phi normalized-norm must recover the whole prime class"
    );
    let output = rt.transfer_entry(&input, to).unwrap();
    let output_packet = rt.check_final(&output).unwrap();
    let public_inverse = rt.inverse_of(from, to, &output_packet).unwrap();
    assert_eq!(public_inverse.key, class.key().0);
    let old_point = independent(old, fourth, from, to, p);
    let old_phi = t.prime.a.transfer_point(&kp(old_point)).unwrap();
    assert_eq!(output.class, old_phi);
    assert_eq!(
        output.norm,
        curve::pmul(t.source.field(), t.source.curve(), &old_point, 2)
    );
    let back = rt.transfer_entry(&output, from).unwrap();
    rt.check_final(&back).unwrap();
    let n = degree(from, to);
    let expected = s.prime.a.pic.mul_scalar(class, n);
    assert_eq!(back.class, expected);
    let recovered = s.prime.a.pic.mul_scalar(&back.class, inverse(n));
    assert_eq!(&recovered, class);
    let mut chain = Value::Null;
    if from.abs_diff(to) == 2 {
        let seq = rt.sequential_entry(&input, to).unwrap();
        let retained = rt.retained_entry(&input, to).unwrap();
        rt.check_final(&seq).unwrap();
        rt.check_final(&retained).unwrap();
        assert_eq!(output.class, seq.class);
        assert_eq!(output.class, retained.class);
        assert_eq!(output.norm, seq.norm);
        assert_eq!(output.norm, retained.norm);
        chain = json!({"sequential":seq.class.key().0,"retained":retained.class.key().0});
    }
    json!({"from":from,"to":to,"input":class.key().0,"source_norm":point_json(input.norm),"normalized_source_point":point_json(p),"actual_source_phi_recovery":source_phi.key().0,"output":output.class.key().0,"actual_target_norm":point_json(output.norm),"independent_original_elliptic_image":point_json(old_point),"independent_original_target_phi":old_phi.key().0,"dual_back":back.class.key().0,"norm_scalar":n,"independent_n_times_input":expected.key().0,"inverse_n":inverse(n),"whole_recovered_input":recovered.key().0,"actual_public_inverse":public_inverse,"chain":chain})
}
fn cofactor_panel(rt: &Runtime, side: usize) -> Vec<PicClass> {
    let g = &rt.geometry[side];
    let pic = &g.prime.a.pic;
    let mut points = pic.rational_points_bruteforce();
    points.sort();
    assert_eq!(points.len(), 224);
    let mut found = BTreeMap::new();
    let mut attempts = Vec::new();
    for point in points {
        let class = pic.exceptional(point);
        let projection = pic.mul_scalar(&class, ELL as u128);
        attempts.push(json!({"kind":"exceptional","point":point,"class":class.key().0,"actual_ell_projection":projection.key().0}));
        found.insert(projection.key().0, projection);
    }
    for p in two_points(g) {
        let class = g.prime.a.transfer_point(&kp(p)).unwrap();
        attempts
            .push(json!({"kind":"source_two_torsion","point":point_json(p),"class":class.key().0}));
        found.insert(class.key().0, class);
    }
    assert_eq!(attempts.len(), 228);
    assert_eq!(
        found.len(),
        4,
        "full declared cofactor census is mandatory; no reselection"
    );
    let mut admission = Vec::new();
    for x in found.values() {
        assert!(pic.is_zero(&pic.mul_scalar(x, 4)));
        let admitted = rt.admit(side, &rt.encode(side, x));
        if pic.is_zero(x) {
            assert!(admitted.is_ok())
        } else {
            assert!(admitted.is_err())
        }
        admission.push(
            json!({"class":x.key().0,"is_zero":pic.is_zero(x),"prime_admitted":admitted.is_ok()}),
        );
    }
    for a in found.values() {
        for b in found.values() {
            assert!(found.contains_key(&pic.add(a, b).key().0));
        }
    }
    emit(
        "N4_ORIGINAL_PRIME_COFACTOR_ATTEMPTS",
        json!({"domain":side,"all228":attempts,"all_four_actual_classes":found.keys().collect::<Vec<_>>(),"all_prime_admission_results":admission}),
    );
    found.into_values().collect()
}
#[test]
fn complete_original_prime_reprojection() {
    let c = CheckedInstance::construct().unwrap();
    let old = ThirdHop::construct(&c);
    let pair = TwistedPair::construct(&c);
    let fourth = PairedFourth::construct(&c, &pair);
    let rt = Runtime::from_preflights(&c, &old, &fourth).unwrap();
    emit("N4_ORIGINAL_PRIME_SETUP", rt.setup.clone());
    let fixture_dir = std::path::PathBuf::from(
        std::env::var("N4_ORIGINAL_PRIME_FIXTURES").expect("entire original row fixtures required"),
    );
    let scalars = [0u64, 1, 2, 17, 12345, ELL - 1];
    let mut public_points: Vec<Vec<Pt<ER>>> = Vec::new();
    let mut public_classes: Vec<Vec<PicClass>> = Vec::new();
    let mut cofactors = Vec::new();
    for domain in 0..3 {
        let g = &rt.geometry[domain];
        let name = ["originalE2", "originalE3", "originalE4"][domain];
        let original: Value = serde_json::from_slice(
            &std::fs::read(fixture_dir.join(format!("{name}-whole-six-rows.json"))).unwrap(),
        )
        .unwrap();
        assert_eq!(
            json!(g.all_six),
            original["all_six_whole_rows"],
            "ALL whole original six-model rows must remain exact"
        );
        let offsets = g.prime.line_offsets().unwrap();
        assert_eq!(offsets.len(), 224);
        let mut norm_controls = Vec::new();
        let mut points = two_points(g);
        points.extend(scalars.iter().map(|&k| {
            curve::pmul(
                g.source.field(),
                g.source.curve(),
                &g.source.generator(),
                k as u128,
            )
        }));
        points.push(g.source.generator());
        for p in points {
            let image = g.prime.a.transfer_point(&kp(p)).unwrap();
            let actual = ep(g.prime.norm(&image).unwrap());
            let expected = curve::pmul(g.source.field(), g.source.curve(), &p, 2);
            assert_eq!(actual, expected);
            norm_controls.push(json!({"source":point_json(p),"whole_phi":image.key().0,"actual_norm":point_json(actual),"independent_double":point_json(expected)}));
        }
        emit(
            "N4_ORIGINAL_PRIME_SOURCE_MODEL",
            json!({"domain":domain,"case":CASES[domain],"mask":MASKS[domain],"actual_source_identity":g.source.identity(),"all_six_whole_original_rows":g.all_six,"whole_original_summary":g.summary,"all224_line_offsets":offsets.into_iter().map(offset_json).collect::<Vec<_>>(),"all_actual_norm_phi_controls":norm_controls}),
        );
        cofactors.push(cofactor_panel(&rt, domain));
        let mut descriptors = g.prime.a.pic.rational_points_bruteforce();
        descriptors.sort();
        assert_eq!(descriptors.len(), 224);
        for (index, point) in descriptors.into_iter().enumerate() {
            let raw = g.prime.a.pic.exceptional(point);
            let projected = g.prime.a.pic.mul_scalar(&raw, 4);
            let outgoing = (0..3)
                .filter(|&to| to != domain)
                .map(|to| check_case(&rt, &old, &fourth, domain, to, &projected))
                .collect::<Vec<_>>();
            emit(
                "N4_ORIGINAL_PRIME_EXCEPTIONAL_CASE",
                json!({"domain":domain,"index":index,"original_descriptor":point,"raw_whole_class":raw.key().0,"explicit_four_projection":projected.key().0,"both_outgoing_maps":outgoing}),
            );
        }
        let mut rng = Rng::new(0x4f5249475052494d);
        let mut ps = Vec::new();
        let mut xs = Vec::new();
        for index in 0..128 {
            let scalar = if index < 6 {
                scalars[index]
            } else {
                rng.below(ELL)
            };
            let p = curve::pmul(
                g.source.field(),
                g.source.curve(),
                &g.source.generator(),
                scalar as u128,
            );
            let class = g.prime.a.transfer_point(&kp(p)).unwrap();
            let outgoing = (0..3)
                .filter(|&to| to != domain)
                .map(|to| check_case(&rt, &old, &fourth, domain, to, &class))
                .collect::<Vec<_>>();
            emit(
                "N4_ORIGINAL_PRIME_PUBLIC_CASE",
                json!({"domain":domain,"index":index,"known_scalar_OUTSIDE_runtime":scalar,"public_source_point":point_json(p),"whole_input_class":class.key().0,"both_outgoing_maps":outgoing}),
            );
            ps.push(p);
            xs.push(class);
        }
        public_points.push(ps);
        public_classes.push(xs);
    }
    for (from, to) in [(0, 1), (0, 2), (1, 2)] {
        let s = &rt.geometry[from];
        let t = &rt.geometry[to];
        let mut rows = Vec::new();
        for i in 0..64 {
            let a = &public_classes[from][i];
            let b = &public_classes[from][(17 * i + 3) % 128];
            let sum = s.prime.a.pic.add(a, b);
            let left = rt.evaluate(from, to, &rt.encode(from, &sum)).unwrap();
            let fa = rt.evaluate(from, to, &rt.encode(from, a)).unwrap();
            let fb = rt.evaluate(from, to, &rt.encode(from, b)).unwrap();
            let actual_sum = t
                .prime
                .a
                .pic
                .add(&t.prime.decode(&fa).unwrap(), &t.prime.decode(&fb).unwrap());
            assert_eq!(left.key, actual_sum.key().0);
            rows.push(json!({"index":i,"source_a":a.key().0,"source_b":b.key().0,"source_sum":sum.key().0,"mapped_sum":left,"mapped_a":fa,"mapped_b":fb,"target_sum":actual_sum.key().0}));
        }
        emit(
            "N4_ORIGINAL_PRIME_ADDITIONS",
            json!({"from":from,"to":to,"all64":rows}),
        );
    }
    let initial = SourceE::original(&c);
    let first = chained_n4_odd_source::OddSourceIsogeny::construct(&c);
    let edge = fourth.branch(false);
    let f = initial.field();
    let mut original_controls = Vec::new();
    let mut transfers = Vec::new();
    for k in [1u64, 2, 17, 12345, ELL - 1] {
        let p0 = curve::pmul(f, initial.curve(), &initial.generator(), k as u128);
        let p1 = first.forward(p0).unwrap();
        let p2 = old.previous().forward(p1).unwrap();
        assert_eq!(p2, old.original_to_source(p0).unwrap());
        let p3 = old.forward(p2).unwrap();
        let p4 = edge.forward(p3).unwrap();
        let d3 = edge.dual(p4).unwrap();
        let d2 = old.dual(d3).unwrap();
        let d1 = old.previous().dual(d2).unwrap();
        let d0 = first.dual(d1).unwrap();
        assert_eq!(d1, curve::pmul(f, first.target(), &p1, 2197));
        assert_eq!(d0, curve::pmul(f, initial.curve(), &p0, 28561));
        let original_point = match p0 {
            Pt::Inf => chained_n4_public_target::ghs::EP::Inf,
            Pt::Aff(x, y) => {
                chained_n4_public_target::ghs::EP::A(three(f.sub(x, er(c.short_shift))), three(y))
            }
        };
        assert!(c.verify_recovered(original_point, k));
        original_controls.push(json!({"known_scalar":k,"actual_E0":point_json(p0),"actual_E1":point_json(p1),"actual_E2":point_json(p2),"actual_E3":point_json(p3),"actual_E4":point_json(p4),"actual_reverse3_to_E1":point_json(d1),"actual_reverse4_to_E0":point_json(d0),"independent_original_source_check":true,"sequential_norms":[2197,28561],"whole_composite_rational_expansion":false}));
        for (domain, p) in [p2, p3, p4].into_iter().enumerate() {
            let g = &rt.geometry[domain];
            let image = g.prime.a.transfer_point(&kp(p)).unwrap();
            let actual_norm = ep(g.prime.norm(&image).unwrap());
            assert_eq!(
                actual_norm,
                curve::pmul(g.source.field(), g.source.curve(), &p, 2)
            );
            let mut reverse = actual_norm;
            if domain == 2 {
                reverse = edge.dual(reverse).unwrap()
            }
            if domain >= 1 {
                reverse = old.dual(reverse).unwrap()
            }
            reverse = first.dual(old.previous().dual(reverse).unwrap()).unwrap();
            let n = 13u128.pow(domain as u32 + 2);
            assert_eq!(reverse, curve::pmul(f, initial.curve(), &p0, 2 * n));
            let recovered = curve::pmul(f, initial.curve(), &reverse, inverse(2 * n));
            assert_eq!(recovered, p0);
            assert!(g
                .prime
                .a
                .pic
                .is_zero(&g.prime.a.pic.mul_scalar(&image, ELL as u128)));
            transfers.push(json!({"known_scalar_OUTSIDE_runtime":k,"domain":domain,"original_E0_public_point":point_json(p0),"factored_prefix_point":point_json(p),"whole_target_class":rt.encode(domain,&image),"actual_target_norm":point_json(actual_norm),"actual_signed_dual_prefix":point_json(reverse),"elliptic_prefix_norm":n,"inverse_twice_prefix_norm":inverse(2*n),"actual_original_point_recovered":point_json(recovered)}));
        }
    }
    assert_eq!(original_controls.len(), 5);
    assert_eq!(transfers.len(), 15);
    emit(
        "N4_ORIGINAL_PRIME_ORIGINAL_PUBLIC",
        json!({"whole_original_five_controls":original_controls,"all15":transfers}),
    );
    let mut vectors = Vec::new();
    for (from, to) in [(0, 2), (2, 0)] {
        for i in 0..6 {
            let class = &public_classes[from][i];
            let packet = rt.encode(from, class);
            let point = rt.encode_point(from, public_points[from][i]);
            rt.reset_calls();
            let input = rt.admit(from, &packet).unwrap();
            let out = rt.transfer_entry(&input, to).unwrap();
            let direct = rt.check_final(&out).unwrap();
            let direct_calls = rt.calls();
            rt.reset_calls();
            let input = rt.admit(from, &packet).unwrap();
            let out = rt.sequential_entry(&input, to).unwrap();
            let sequential = rt.check_final(&out).unwrap();
            let sequential_calls = rt.calls();
            rt.reset_calls();
            let input = rt.admit(from, &packet).unwrap();
            let out = rt.retained_entry(&input, to).unwrap();
            let retained = rt.check_final(&out).unwrap();
            let retained_calls = rt.calls();
            rt.reset_calls();
            let known = rt.known_point(from, to, &point).unwrap();
            let known_calls = rt.calls();
            rt.reset_calls();
            let known_factored = rt.known_point_factored(from, to, &point).unwrap();
            let known_factored_calls = rt.calls();
            for output in [&sequential, &retained, &known, &known_factored] {
                assert_eq!(
                    serde_json::to_value(output).unwrap(),
                    serde_json::to_value(&direct).unwrap()
                );
            }
            vectors.push(json!({"from":from,"to":to,"scalar_OUTSIDE_runtime":scalars[i],"whole_jacobian_input":packet,"whole_known_elliptic_point_input":point,"direct":direct_calls,"literal_jacobian_chain":sequential_calls,"retained_normalized_prime_lift":retained_calls,"known_point_direct":known_calls,"known_point_factored":known_factored_calls,"all_five_whole_outputs_equal":direct}));
        }
    }
    assert_eq!(vectors.len(), 12);
    emit(
        "N4_ORIGINAL_PRIME_SELECTED_VECTORS",
        json!({"all12":vectors,"scope":"unpriced selected source entries, different public input presentations explicit; all setup/primitive work and minimal production constructor remain open"}),
    );
    let mut rejections = Vec::new();
    for side in 0..3 {
        let g = &rt.geometry[side];
        let packet = rt.encode(side, &public_classes[side][1]);
        let mut bad = packet.clone();
        bad.field.push_str("-foreign");
        let foreign_field = rt.admit(side, &bad).is_err();
        bad = packet.clone();
        bad.model.push_str("-foreign");
        let foreign_model = rt.admit(side, &bad).is_err();
        bad = packet.clone();
        bad.key[1] = 223;
        let noncanonical = rt.admit(side, &bad).is_err();
        let mut mixed = Vec::new();
        for t in &cofactors[side] {
            let x = g.prime.a.pic.add(&public_classes[side][1], t);
            let admitted = rt.admit(side, &rt.encode(side, &x)).is_ok();
            assert_eq!(admitted, g.prime.a.pic.is_zero(t));
            mixed.push(json!({"cofactor":t.key().0,"actual_mixed_class":x.key().0,"prime_admitted":admitted}));
        }
        let two = two_points(g);
        let point = rt.encode_point(side, two[1]);
        let target = (side + 1) % 3;
        let nonprime_point = rt.known_point(side, target, &point).is_err();
        let mut wrong_point = rt.encode_point(side, g.source.generator());
        wrong_point.field.push_str("-foreign");
        let foreign_point = rt.known_point(side, target, &wrong_point).is_err();
        let check = |ec: Curve<ER>, ell: u64, order: u128, generator: Pt<ER>| {
            std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                SourceE::paired_source(&c, ec, ell, order, generator, "actual-rejection-control")
            }))
            .is_err()
        };
        let foreign_prime = check(*g.source.curve(), 2771711, ORDER, g.source.generator());
        let wrong_order = check(*g.source.curve(), ELL, ORDER + 4, g.source.generator());
        let zero_generator = check(*g.source.curve(), ELL, ORDER, Pt::Inf);
        let altered = Curve::new(
            g.source.curve().a,
            g.source
                .field()
                .add(g.source.curve().b, g.source.field().one()),
        );
        let foreign_curve = check(altered, ELL, ORDER, g.source.generator());
        for rejected in [
            foreign_field,
            foreign_model,
            noncanonical,
            nonprime_point,
            foreign_point,
            foreign_prime,
            wrong_order,
            zero_generator,
            foreign_curve,
        ] {
            assert!(rejected)
        }
        rejections.push(json!({"domain":side,"foreign_field":foreign_field,"foreign_model":foreign_model,"noncanonical_packet":noncanonical,"nonprime_source_point":nonprime_point,"foreign_point_field":foreign_point,"actual_foreign_prime_constructor":foreign_prime,"actual_wrong_order_constructor":wrong_order,"actual_zero_generator_constructor":zero_generator,"actual_foreign_curve_constructor":foreign_curve,"all_actual_mixed_cofactor_admissions":mixed}));
    }
    emit(
        "N4_ORIGINAL_PRIME_REJECTIONS",
        json!({"all_three_domains":rejections}),
    );
    emit(
        "N4_ORIGINAL_PRIME_FULL_POPULATION",
        json!({"domains":3,"whole_old_model_rows":18,"line_offsets_per_domain":224,"projected_exceptional_descriptors":672,"exceptional_outgoing_evaluations":1344,"all_cofactor_attempts_per_domain":228,"cofactor_classes_per_domain":4,"public_points":384,"public_outgoing_evaluations":768,"addition_pairs_per_undirected_pair":64,"undirected_pairs":3,"original_public_controls":5,"original_public_endpoint_transfers":15,"selected_vectors":12,"selected_routes":5,"prime":ELL,"full_source_order":ORDER,"scope":"separate prime-subgroup reprojection; explicit four projection and strict cofactor rejection; old full-group chain and negatives unchanged; no calibrated advantage or signed standing"}),
    );
}
