use super::*;
use chained_n4_completed_v2::{AdapterV2, NormV2};
use chained_n4_new_target_ic::{class_solver as baseline, TargetContext};
use chained_n4_odd_product_maps::Adapter;
use chained_n4_odd_product_models::{construct_all, SourceE};
use chained_n4_odd_product_refinements::FastSourceChain;
use chained_n4_odd_source::OddSourceIsogeny;
use chained_n4_public_target::{ghs::EP, CheckedInstance};
use serde_json::{json, Value};

fn short(c: &CheckedInstance, p: EP) -> Point {
    match p {
        EP::Inf => None,
        EP::A(x, y) => Some((c.inst.kf.add(&x, &c.short_shift), y)),
    }
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
fn exact_scalar_samples_and_all_sixty_original_candidate_ic_pairs() {
    println!("N4_ARITHMETIC_BUILD {}", serde_json::json!({"manifest_dir":env!("CARGO_MANIFEST_DIR"),"controls_sha256":ghs_original_engines::digest::sha256(include_bytes!("../../../../../arithmetic-controls.rs")).iter().map(|b|format!("{b:02x}")).collect::<String>(),"literal_scalar_taps_checked_below":true}));
    crate::arithmetic_controls::run();
    let _audit_scope = n4_arithmetic_taps::scope("setup");
    let original = include_str!("../original/class_solver.rs");
    assert_eq!(
        original,
        include_str!("../../new-target-ic/derived/class_solver.rs")
    );
    assert_eq!(crate::arithmetic_controls::strip_scalar_taps(include_str!("../../new-target-ic/arithmetic-derived/class_solver.rs")), original);
    assert_eq!(crate::arithmetic_controls::strip_scalar_taps(include_str!("../arithmetic-derived/class_solver.rs")), include_str!("../derived/class_solver.rs"));
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
        "N4_NORM_SAMPLER_PROVENANCE {}",
        json!({"literal_substitutions":replacements,"all_other_bytes_unchanged":true,"original_final_Picard_check_unchanged":true,"protocol":"4a6745/b57 published beforecode"})
    );

    let c = CheckedInstance::construct().unwrap();
    let old = NormV2::new(AdapterV2::new(&c).unwrap()).unwrap();
    let isogeny = OddSourceIsogeny::construct(&c);
    let source = SourceE::degree13_target(&c, &isogeny);
    let (models, _) = construct_all(&source, &old.a);
    let public = c
        .parse(include_bytes!("../../fixtures/public-five.json"))
        .unwrap();
    let answers: Vec<Value> =
        serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
            .unwrap();
    let (mut pairs, mut scalar_pairs, mut triples, mut solved_cases, mut models_seen) =
        (0, 0, 0, 0, 0);
    let mut outcomes = vec![];
    let mut foreign: Option<EncodedClass> = None;
    for model in models {
        if model.square_root.is_none() {
            continue;
        }
        let id = [model.root_index, model.sign_index];
        let _model_scope = n4_arithmetic_taps::scope(format!("model-{id:?}"));
        let norm = NormNew::new(Adapter::new(&source, &old.a, model).unwrap()).unwrap();
        let chain = FastSourceChain::new(&c, &norm, &isogeny).unwrap();
        let g = chain
            .from_source(&chain.encode_source(short(&c, c.inst.g)))
            .unwrap();
        let gc = norm.decode(&g).unwrap();
        let prepared = n4_arithmetic_taps::within(format!("prepare-{id:?}"), || SamplerContext::new(&norm, &g).unwrap());
        let baseline_context = TargetContext::new(&norm).unwrap();
        let pic = &norm.a.pic;
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
        for &raw in &public {
            let q = chain
                .from_source(&chain.encode_source(short(&c, raw)))
                .unwrap();
            let qc = norm.decode(&q).unwrap();
            targets.push((q, qc));
        }
        println!(
            "N4_NORM_SAMPLER_INPUT {}",
            json!({"target":id,"quartic":norm.a.core.quartic,"P0":pic.base_point(),"field":norm.field_tag,"model":norm.model_tag,"ell":c.inst.ell,"generator":g,"prepared_public_source":prepared.prepared_source(),"preparation_explicit_calls":preparation,"nested_decode_norm_and_other_work":"not flattened or priced","source":source.identity()})
        );

        let ell = c.inst.ell;
        let mut scalars = vec![0, 1, 2, 3, 12, 13, 26, 52, ell / 2, ell - 2, ell - 1];
        let mut rng = common::Rng::new(0x71A55157);
        scalars.extend((0..64).map(|_| rng.below(ell)));
        assert_eq!(scalars.len(), 75);
        let mut all_samples = vec![];
        for &r in &scalars {
            let before = prepared.calls();
            let sampled = n4_arithmetic_taps::within(format!("sample-candidate-{id:?}"), || prepared.sample(r).unwrap());
            let original = n4_arithmetic_taps::within(format!("sample-original-{id:?}"), || pic.mul_scalar(&gc, r as u128));
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
            "N4_NORM_SAMPLER_SCALARS {}",
            json!({"target":id,"seed":0x71A55157u64,"scalars":scalars,"all75":all_samples})
        );

        let mut cases = vec![];
        for (i, &(ref q, ref qc)) in targets.iter().enumerate() {
            let mut common_correct = 0;
            let mut case_outcomes = vec![];
            for (attempt, &nfb) in [30, 36, 48, 64].iter().enumerate() {
                let seed = 102 + attempt as u64;
                let a = n4_arithmetic_taps::within(format!("solver-original-{id:?}-public{i}-FB{nfb}"), || baseline_context
                    .solve(&g, q, &baseline_params(nfb), seed)
                    .unwrap());
                let before = prepared.calls();
                let b = n4_arithmetic_taps::within(format!("solver-candidate-{id:?}-public{i}-FB{nfb}"), || prepared.solve(&g, q, &candidate_params(nfb), seed).unwrap());
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
                let _verify_scope = n4_arithmetic_taps::scope(format!("verification-{id:?}-public{i}-FB{nfb}"));
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
                    "N4_NORM_SAMPLER_ATTEMPT {}",
                    json!({"target":id,"public_index":i,"attempt":attempt,"nfb":nfb,"seed":seed,"public_Q":q,"original":ar,"candidate":br,"explicit_candidate_calls":calls,"original_target_group_check":a_target,"candidate_target_group_check":b_target,"original_source_check":a_source,"candidate_source_check":b_source,"all_frozen_nontiming_fields_equal":true,"cost_scope":"unpriced FpR/map/admission/preparation/verification;raw old counter differences are not a stage win"})
                );
                case_outcomes.push(json!({"attempt":attempt,"nfb":nfb,"both_ok":a.ok&&b.ok,"failure":a.fail,"k_found":a.k_found}));
                pairs += 1;
            }
            assert!(
                common_correct > 0,
                "no common correct IC setting at {id:?},public{i}"
            );
            let row = json!({"target":id,"public_index":i,"common_correct_settings":common_correct,"all_four_outcomes":case_outcomes});
            println!("N4_NORM_SAMPLER_CASE {}", row);
            cases.push(row);
            solved_cases += 1;
        }

        let mut controls = vec![];
        assert!(prepared.sample(ell).is_err());
        assert!(prepared.sample(u64::MAX).is_err());
        controls.push("noncanonical-scalar");
        let zero = norm.encode(&pic.zero());
        assert!(SamplerContext::new(&norm, &zero).is_err());
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
            assert!(SamplerContext::new(&norm, &bad).is_err());
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
        assert!(SamplerContext::new(&norm, &nonodd).is_err());
        assert!(prepared
            .solve(&nonodd, &g, &candidate_params(36), 103)
            .is_err());
        assert!(prepared
            .solve(&g, &nonodd, &candidate_params(36), 103)
            .is_err());
        controls.push("actual-nonodd-generator-and-target");
        if let Some(ref bad) = foreign {
            assert!(SamplerContext::new(&norm, bad).is_err());
            assert!(prepared.solve(bad, &g, &candidate_params(36), 103).is_err());
            assert!(prepared.solve(&g, bad, &candidate_params(36), 103).is_err());
            controls.push("actual-foreign-Jacobian-and-P0");
        }
        // Same quartic with a genuinely different base point,not just a label edit.
        let alternate = pic
            .rational_points_bruteforce()
            .into_iter()
            .find(|p| *p != pic.base_point())
            .unwrap();
        let (alternate_models, _) = construct_all(&source, &old.a);
        let alternate_model = alternate_models
            .into_iter()
            .find(|m| [m.root_index, m.sign_index] == id)
            .unwrap();
        let alternate_norm = NormNew::new(
            Adapter::with_base_point(&source, &old.a, alternate_model, Some(alternate)).unwrap(),
        )
        .unwrap();
        assert_ne!(alternate_norm.a.pic.base_point(), pic.base_point());
        let wrong_p0 = alternate_norm.encode(
            &alternate_norm
                .a
                .transfer_point(&prepared.prepared_source())
                .unwrap(),
        );
        assert!(SamplerContext::new(&norm, &wrong_p0).is_err());
        assert!(prepared
            .solve(&g, &wrong_p0, &candidate_params(36), 103)
            .is_err());
        controls.push("actual-foreign-P0-packet");
        foreign = Some(g.clone());
        let row = json!({"target":id,"all_five_cases":cases,"negative_controls":controls,"preparation_calls":preparation,"all_calls_including_controls":prepared.calls(),"complete_primitive_costs":"unknown;not zero"});
        println!("N4_NORM_SAMPLER_TARGET {}", row);
        outcomes.push(row);
        models_seen += 1;
    }
    assert_eq!(
        (models_seen, scalar_pairs, triples, pairs, solved_cases),
        (3, 225, 1125, 60, 15)
    );
    println!(
        "N4_NORM_SAMPLER_SCOPE {}",
        json!({"models":models_seen,"scalar_pairs":scalar_pairs,"triples":triples,"paired_attempts":pairs,"solver_reports":2*pairs,"common_solved_cases":solved_cases,"all_target_outcomes":outcomes,"no_fallback_or_scalar_witness":true,"pricing":"complete arithmetic coverage/admission/matchedreferences pending"})
    );
    println!("N4_ARITHMETIC_CENSUS {}", n4_arithmetic_taps::snapshot());
    n4_arithmetic_taps::assert_no_unsupported();
}
