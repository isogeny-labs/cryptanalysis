use super::*;
use chained_n4_completed_v2::AdapterV2;
use chained_n4_original_fixed_model_ic::{class_solver as baseline, TargetContext};
use chained_n4_original_full_evaluator::Runtime;
use chained_n4_original_full_geometry::{take_fixed_model, Adapter, CASES};
use chained_n4_paired_fourth_preflight::{
    models::{construct_all, SourceE},
    PairedFourth, ThirdHop, TwistedPair,
};
use chained_n4_public_target::{ghs::EP, CheckedInstance};
use isogeny_algos::fpr::ER;
use serde_json::{json, Value};

fn short(c: &CheckedInstance, p: EP) -> Pt<ER> {
    match p {
        EP::Inf => Pt::Inf,
        EP::A(x, y) => Pt::Aff(er(c.inst.kf.add(&x, &c.short_shift)), er(y)),
    }
}
fn source_points(
    c: &CheckedInstance,
    pair: &ThirdHop,
    fourth: &PairedFourth<'_>,
    p: EP,
) -> [Pt<ER>; 3] {
    let p2 = pair.original_to_source(short(c, p)).unwrap();
    let p3 = pair.forward(p2).unwrap();
    let p4 = fourth.branch(false).forward(p3).unwrap();
    [p2, p3, p4]
}
fn packets(runtime: &Runtime, points: [Pt<ER>; 3]) -> [EncodedClass; 3] {
    let first = runtime.encode(
        0,
        &runtime.geometry.models[0]
            .prime
            .a
            .transfer_point(&kp(points[0]))
            .unwrap(),
    );
    std::array::from_fn(|side| {
        let packet = if side == 0 {
            first.clone()
        } else {
            runtime.evaluate(0, side, &first).unwrap()
        };
        let model = &runtime.geometry.models[side];
        let independent = model
            .prime
            .encode(&model.prime.a.transfer_point(&kp(points[side])).unwrap());
        assert_eq!(
            (&packet.field, &packet.model, &packet.key),
            (&independent.field, &independent.model, &independent.key),
            "actual opaque chain differs from independent source-point Phi"
        );
        packet
    })
}
macro_rules! report {
    ($r:expr) => {{
        let r = &$r;
        json!({"ok":r.ok,"fail":r.fail,"k_found":r.k_found,"stats":r.stats,
        "phases":r.phases.iter().map(|(phase,c,wall)|json!({"phase":phase,"mul":c.mul,"inv":c.inv,"add":c.add,"lmul":c.lmul,"ladd":c.ladd,"hash":c.hash,"cmp":c.cmp,"wall":wall})).collect::<Vec<_>>(),
        "counter_scope":"original IC and wrapped Picard only;FpR/maps/setup/admission/independentverify unknown;not a price"})
    }};
}
fn comparable(mut value: Value) -> Value {
    value["stats"]
        .as_array_mut()
        .unwrap()
        .retain(|x| x[0] != "wall_total");
    for phase in value["phases"].as_array_mut().unwrap() {
        let descent = phase["phase"] == "descent";
        let object = phase.as_object_mut().unwrap();
        object.remove("wall");
        if descent {
            for key in ["mul", "inv", "add", "lmul", "ladd", "hash", "cmp"] {
                object.remove(key);
            }
        }
    }
    value
}
fn baseline_params(nfb: usize) -> baseline::Params {
    baseline::Params {
        nfb,
        rows_mult: 1.2,
        max_desc: 100000,
        sge: false,
        maxw: 12,
        lp2: true,
    }
}
fn candidate_params(nfb: usize) -> class_solver::Params {
    class_solver::Params {
        nfb,
        rows_mult: 1.2,
        max_desc: 100000,
        sge: false,
        maxw: 12,
        lp2: true,
    }
}

#[test]
fn all_original_fixed_models_all_scalar_triples_and_sixty_paired_attempts() {
    let original = include_str!("../original/class_solver.rs");
    assert_eq!(
        original,
        include_str!("../../new-target-ic/derived/class_solver.rs")
    );
    let replacements = [
        ("crate::TargetContext<'_>", "crate::SamplerContext<'_>"),
        (
            "let r0 = pc(&cv, || cv.mul_scalar(generator, r as u128));",
            "let r0 = inst.sample(r).expect(\"prepared exact-generator sampler\");",
        ),
    ];
    let mut derived = original.to_owned();
    for (from, to) in replacements {
        assert_eq!(derived.matches(from).count(), 1);
        derived = derived.replace(from, to);
    }
    assert_eq!(derived, include_str!("../derived/class_solver.rs"));
    println!(
        "N4_ORIGINAL_FIXED_SAMPLER_PROVENANCE {}",
        json!({"literal_substitutions":replacements,"all_other_bytes_unchanged":true,"original_final_Picard_check_unchanged":true,"protocol":"abf432/80631ad before new Rust"})
    );

    let c = CheckedInstance::construct().unwrap();
    let old = AdapterV2::new(&c).unwrap();
    let runtime = Runtime::construct(&c).unwrap();
    let pair = ThirdHop::construct(&c);
    let twisted_pair = TwistedPair::construct(&c);
    let fourth = PairedFourth::construct(&c, &twisted_pair);
    let known_generator_points = source_points(&c, &pair, &fourth, c.inst.g);
    let generators = packets(&runtime, known_generator_points);
    let public = c
        .parse(include_bytes!("../../fixtures/public-five.json"))
        .unwrap();
    let answers: Vec<Value> =
        serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
            .unwrap();
    let public_packets: Vec<_> = public
        .iter()
        .map(|&q| packets(&runtime, source_points(&c, &pair, &fourth, q)))
        .collect();
    println!(
        "N4_ORIGINAL_FIXED_SAMPLER_SETUP {}",
        json!({"whole_original_runtime_setup":runtime.setup,"actual_input_transfer_calls":runtime.calls(),"scope":"complete original setup retained, not minimal or priced"})
    );
    let (mut pairs, mut scalar_pairs, mut triples, mut solved_cases, mut models_seen) =
        (0, 0, 0, 0, 0);
    let mut outcomes = vec![];
    for side in 0..3 {
        let model = &runtime.geometry.models[side];
        let source = &model.source;
        let id = [CASES[side].0, CASES[side].1];
        let norm = &model.prime;
        let g = generators[side].clone();
        let gc = norm.decode(&g).unwrap();
        let prepared = SamplerContext::new(&runtime.geometry, side, &g).unwrap();
        let baseline_context = TargetContext::new(&runtime.geometry, side).unwrap();
        let pic = &norm.a.pic;
        assert_eq!(
            prepared.prepared_source(),
            kp(known_generator_points[side]),
            "public norm preparation differs from independently transported known generator point"
        );
        let preparation = prepared.calls();
        assert_eq!(
            preparation,
            Calls {
                decode: 1,
                explicit_norm: 1,
                source_scalar: 1,
                source_order_check: 1,
                completed_transfer: 1,
                target_admission_scalar: 1,
                sampled: 0
            }
        );
        let mut targets = vec![];
        for (public_index, _) in public.iter().enumerate() {
            let q = public_packets[public_index][side].clone();
            let qc = norm.decode(&q).unwrap();
            targets.push((q, qc));
        }
        println!(
            "N4_ORIGINAL_FIXED_SAMPLER_INPUT {}",
            json!({"side":side,"target":id,"quartic":norm.a.core.quartic,"P0":pic.base_point(),"field":norm.field_tag,"model":norm.model_tag,"ell":c.inst.ell,"generator":g,"prepared_public_source":prepared.prepared_source(),"independent_already_known_source_point":kp(known_generator_points[side]),"strong_known_point_reference_exact":true,"preparation_explicit_calls":preparation,"nested_decode_norm_and_other_work":"not flattened or priced","source":source.identity()})
        );

        let ell = c.inst.ell;
        let mut scalars = vec![0, 1, 2, 3, 12, 13, 26, 52, ell / 2, ell - 2, ell - 1];
        let mut rng = common::Rng::new(0x71A55157);
        scalars.extend((0..64).map(|_| rng.below(ell)));
        assert_eq!(scalars.len(), 75);
        let mut all_samples = vec![];
        for &r in &scalars {
            let before = prepared.calls();
            let sampled = prepared.sample(r).unwrap();
            let original = pic.mul_scalar(&gc, r as u128);
            assert_eq!(
                sampled, original,
                "exact sampler class mismatch at {id:?},r={r}"
            );
            let next = pic.add(&sampled, &gc);
            let original_next = pic.add(&original, &gc);
            assert_eq!(next, original_next);
            let mut all_triples = vec![];
            for (i, (_, qc)) in targets.iter().enumerate() {
                let with_q = pic.add(&sampled, qc);
                let original_with_q = pic.add(&original, qc);
                assert_eq!(with_q, original_with_q);
                all_triples.push(json!({"public_index":i,"R":sampled.key().0,"R_plus_G":next.key().0,"R_plus_Q":with_q.key().0,"all_three_exact":true}));
                triples += 1;
            }
            let calls = prepared.calls().since(before);
            assert_eq!(
                calls,
                Calls {
                    source_scalar: 1,
                    completed_transfer: 1,
                    sampled: 1,
                    ..Calls::default()
                }
            );
            let source_point = curve::pmul(
                &norm.a.f3,
                &norm.a.source_ec,
                &ep(prepared.prepared_source()),
                r as u128,
            );
            all_samples.push(json!({"r":r,"source_point":kp(source_point),"sampler_class":sampled.key().0,"original_Picard_class":original.key().0,"explicit_calls":calls,"all_five_triples":all_triples}));
            scalar_pairs += 1;
        }
        println!(
            "N4_ORIGINAL_FIXED_SAMPLER_SCALARS {}",
            json!({"side":side,"target":id,"seed":0x71A55157u64,"scalars":scalars,"all75":all_samples})
        );

        let mut cases = vec![];
        for (i, &(ref q, ref qc)) in targets.iter().enumerate() {
            let mut common_correct = 0;
            let mut case_outcomes = vec![];
            for (attempt, &nfb) in [30, 36, 48, 64].iter().enumerate() {
                let seed = 102 + attempt as u64;
                let a = baseline_context
                    .solve(&g, q, &baseline_params(nfb), seed)
                    .unwrap();
                let before = prepared.calls();
                let b = prepared.solve(&g, q, &candidate_params(nfb), seed).unwrap();
                let calls = prepared.calls().since(before);
                let ar = report!(a);
                let br = report!(b);
                assert_eq!(
                    comparable(ar.clone()),
                    comparable(br.clone()),
                    "paired IC output mismatch at {id:?},public{i},FB{nfb}"
                );
                assert_eq!(calls.decode, 2);
                assert_eq!(calls.target_admission_scalar, 2);
                assert_eq!(calls.explicit_norm, 0);
                assert_eq!(calls.source_order_check, 0);
                assert_eq!(calls.source_scalar, calls.sampled);
                assert_eq!(calls.completed_transfer, calls.sampled);
                assert!(calls.sampled <= 1);
                let a_target = a
                    .k_found
                    .is_some_and(|k| pic.mul_scalar(&gc, k as u128) == *qc);
                let b_target = b
                    .k_found
                    .is_some_and(|k| pic.mul_scalar(&gc, k as u128) == *qc);
                let a_source = a.k_found.is_some_and(|k| c.verify_recovered(public[i], k));
                let b_source = b.k_found.is_some_and(|k| c.verify_recovered(public[i], k));
                if a.ok || b.ok {
                    assert!(a.ok && b.ok && a_target && b_target && a_source && b_source);
                    let expected = answers[i]["original_native_recovered_scalar"]
                        .as_u64()
                        .unwrap();
                    assert_eq!(a.k_found, Some(expected));
                    assert_eq!(b.k_found, Some(expected));
                    common_correct += 1;
                }
                println!(
                    "N4_ORIGINAL_FIXED_SAMPLER_ATTEMPT {}",
                    json!({"side":side,"target":id,"public_index":i,"attempt":attempt,"nfb":nfb,"seed":seed,"public_Q":q,"original":ar,"candidate":br,"explicit_candidate_calls":calls,"original_target_group_check":a_target,"candidate_target_group_check":b_target,"original_source_check":a_source,"candidate_source_check":b_source,"all_frozen_nontiming_fields_equal":true,"cost_scope":"unpriced FpR/map/admission/preparation/verification;raw old counter differences are not a stage win"})
                );
                case_outcomes.push(json!({"attempt":attempt,"nfb":nfb,"both_ok":a.ok&&b.ok,"failure":a.fail,"k_found":a.k_found}));
                pairs += 1;
            }
            assert!(
                common_correct > 0,
                "no common correct IC setting at {id:?},public{i}"
            );
            let row = json!({"side":side,"target":id,"public_index":i,"common_correct_settings":common_correct,"all_four_outcomes":case_outcomes});
            println!("N4_ORIGINAL_FIXED_SAMPLER_CASE {}", row);
            cases.push(row);
            solved_cases += 1;
        }

        let mut controls = vec![];
        assert!(prepared.sample(ell).is_err());
        assert!(prepared.sample(u64::MAX).is_err());
        controls.push("noncanonical-scalar");
        let zero = norm.encode(&pic.zero());
        assert!(SamplerContext::new(&runtime.geometry, side, &zero).is_err());
        assert!(prepared
            .solve(&zero, &g, &candidate_params(36), 103)
            .is_err());
        controls.push("zero-generator");
        let wrong_half = norm.a.transfer_point(&norm.norm(&gc).unwrap()).unwrap();
        assert_eq!(wrong_half, pic.mul_scalar(&gc, 2));
        assert_ne!(wrong_half, gc);
        controls.push("actual-omitted-inverse2");
        let other = norm.encode(&pic.mul_scalar(&gc, 2));
        assert!(prepared
            .solve(&other, &g, &candidate_params(36), 103)
            .is_err());
        controls.push("changed-prepared-generator");
        for label in [
            "field",
            "model",
            "source-model",
            "noncanonical",
            "malformed",
        ] {
            let mut bad = g.clone();
            match label {
                "field" => bad.field.push('x'),
                "model" => bad.model.push('x'),
                "source-model" => bad.model = SourceE::original(&c).source_tag().to_owned(),
                "noncanonical" => bad.key[1] = 223,
                "malformed" => bad.key[0] = 3,
                _ => unreachable!(),
            }
            assert!(SamplerContext::new(&runtime.geometry, side, &bad).is_err());
            assert!(prepared
                .solve(&bad, &g, &candidate_params(36), 103)
                .is_err());
            assert!(prepared
                .solve(&g, &bad, &candidate_params(36), 103)
                .is_err());
            controls.push(label);
        }
        let nonodd = pic
            .rational_points_bruteforce()
            .into_iter()
            .map(|p| pic.mul_scalar(&pic.point_class(p), ell as u128))
            .find(|x| !pic.is_zero(x))
            .unwrap();
        let nonodd = norm.encode(&nonodd);
        assert!(SamplerContext::new(&runtime.geometry, side, &nonodd).is_err());
        assert!(prepared
            .solve(&nonodd, &g, &candidate_params(36), 103)
            .is_err());
        assert!(prepared
            .solve(&g, &nonodd, &candidate_params(36), 103)
            .is_err());
        controls.push("actual-nonodd-generator-and-target");
        let bad = &generators[(side + 1) % 3];
        assert!(SamplerContext::new(&runtime.geometry, side, bad).is_err());
        assert!(prepared.solve(bad, &g, &candidate_params(36), 103).is_err());
        assert!(prepared.solve(&g, bad, &candidate_params(36), 103).is_err());
        controls.push("actual-foreign-Jacobian-and-P0");
        assert!(SamplerContext::new(&runtime.geometry, 3, &g).is_err());
        controls.push("invalid-fixed-side");
        for kind in 0..5 {
            let mut bad = candidate_params(36);
            match kind {
                0 => bad.nfb = 3,
                1 => bad.nfb = 225,
                2 => bad.max_desc = 0,
                3 => bad.rows_mult = f64::NAN,
                4 => bad.rows_mult = 0.0,
                _ => unreachable!(),
            }
            assert!(prepared.solve(&g, &g, &bad, 103).is_err());
        }
        controls.push("five-invalid-bounded-parameters");
        // Same quartic with a genuinely different base point,not just a label edit.
        let alternate = pic
            .rational_points_bruteforce()
            .into_iter()
            .find(|p| *p != pic.base_point())
            .unwrap();
        let (mut alternate_models, _) = construct_all(source, &old);
        let alternate_model = take_fixed_model(
            &mut alternate_models,
            side,
            chained_n4_original_full_geometry::MASKS[side],
        )
        .unwrap();
        let alternate_norm = NormNew::new(
            Adapter::with_base_point(source, &old, alternate_model, Some(alternate)).unwrap(),
        )
        .unwrap();
        assert_ne!(alternate_norm.a.pic.base_point(), pic.base_point());
        let wrong_p0 = alternate_norm.encode(
            &alternate_norm
                .a
                .transfer_point(&prepared.prepared_source())
                .unwrap(),
        );
        assert!(SamplerContext::new(&runtime.geometry, side, &wrong_p0).is_err());
        assert!(prepared
            .solve(&g, &wrong_p0, &candidate_params(36), 103)
            .is_err());
        controls.push("actual-foreign-P0-packet");
        let row = json!({"side":side,"target":id,"all_five_cases":cases,"negative_controls":controls,"preparation_calls":preparation,"all_calls_including_controls":prepared.calls(),"complete_primitive_costs":"unknown;not zero"});
        println!("N4_ORIGINAL_FIXED_SAMPLER_TARGET {}", row);
        outcomes.push(row);
        models_seen += 1;
    }
    assert_eq!(
        (models_seen, scalar_pairs, triples, pairs, solved_cases),
        (3, 225, 1125, 60, 15)
    );
    println!(
        "N4_ORIGINAL_FIXED_SAMPLER_SCOPE {}",
        json!({"models":models_seen,"scalar_pairs":scalar_pairs,"triples":triples,"paired_attempts":pairs,"solver_reports":2*pairs,"common_solved_cases":solved_cases,"all_target_outcomes":outcomes,"no_fallback_or_scalar_witness":true,"pricing":"complete arithmetic coverage/admission/matchedreferences pending"})
    );
}
