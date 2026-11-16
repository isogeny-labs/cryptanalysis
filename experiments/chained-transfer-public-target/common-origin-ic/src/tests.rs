use super::*;
use chained_n4_completed_v2::{AdapterV2, Point, QuarticPoint};
use chained_n4_public_target::{ghs::EP, public_solver, CheckedInstance};
use serde_json::{json, Value};

fn signed(c: &CheckedInstance, p: EP) -> Point {
    match p {
        EP::Inf => None,
        EP::A(x, y) => Some((c.inst.kf.add(&x, &c.short_shift), c.inst.kf.neg(&y))),
    }
}
fn original_params(nfb: usize) -> public_solver::Params {
    public_solver::Params {
        nfb,
        rows_mult: 1.2,
        max_desc: 100000,
        sge: false,
        maxw: 12,
        lp2: true,
    }
}
fn class_params(nfb: usize) -> class_solver::Params {
    class_solver::Params {
        nfb,
        rows_mult: 1.2,
        max_desc: 100000,
        sge: false,
        maxw: 12,
        lp2: true,
    }
}
macro_rules! report {
    ($r:expr) => {{
        let r = &$r;
        json!({"ok":r.ok,"fail":r.fail,"k_found":r.k_found,"stats":r.stats,
            "phases":r.phases.iter().map(|(name,c,wall)|json!({"phase":name,
                "mul":c.mul,"inv":c.inv,"add":c.add,"lmul":c.lmul,
                "ladd":c.ladd,"hash":c.hash,"cmp":c.cmp,"wall":wall})).collect::<Vec<_>>()})
    }};
}
fn through(s: &str, start: &str, end: &str) -> String {
    let a = s.find(start).unwrap();
    let b = s[a..].find(end).unwrap() + a + end.len();
    s[a..b].to_owned()
}
fn literal_contract() {
    let baseline = include_str!("../original/public_solver.rs");
    assert_eq!(
        baseline,
        include_str!("../../native/derived/public_solver.rs")
    );
    let snapshot = include_str!("../original/class_solver.rs");
    assert_eq!(
        snapshot,
        include_str!("../../new-target-ic/derived/class_solver.rs")
    );
    let derived = include_str!("../derived/class_solver.rs");
    assert_eq!(
        derived,
        snapshot
            .replace("crate::TargetContext<'_>", "crate::BridgeContext<'_>")
            .replace("let cv = &inst.norm.a.pic;", "let cv = inst.pic;")
    );
    let stop = "    phase!(\"log_recovery\");";
    assert_eq!(
        through(baseline, "    // 2. relations", stop),
        through(derived, "    // 2. relations", stop)
    );
    let start = "            let mut added: Vec<u32> = Vec::new();";
    let stop = "    rep.stat(\"descent_trials\", total_trials as f64);";
    assert_eq!(
        through(baseline, start, stop),
        through(derived, start, stop)
    );
    println!(
        "N4_ORIGIN_PROVENANCE {}",
        json!({"protocol":"2dd807/0a3412cd published beforecode",
            "original_baseline_snapshot_exact":true,"class_snapshot_exact":true,
            "derivative_delta":"ONLY context type and borrowed actual Picard access",
            "relation_LA_log_recovery_and_inner_descent_literal":true,
            "counters":"diagnostic/incomplete,no S or operational equivalence claim"})
    );
}

#[test]
fn exact_origins_all_twenty_pairs_and_actual_affine_class_bridges() {
    literal_contract();
    let c = CheckedInstance::construct().unwrap();
    let requests = c
        .parse(include_bytes!("../../fixtures/public-five.json"))
        .unwrap();
    let answers: Vec<Value> =
        serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
            .unwrap();
    let plane = ic::Curve::new(c.inst.q, &c.inst.f);
    let mut paired_attempts = 0;
    let mut common_solutions = [0; 5];
    let mut omitted_origin_controls = 0;
    let mut whole_cases = vec![];
    for (setting, nfb) in [30, 36, 48, 64].into_iter().enumerate() {
        let seed = 102 + setting as u64;
        let mut rng_old = common::Rng::new(seed ^ 0xC0FFEE);
        let mut rng_class = common::Rng::new(seed ^ 0xC0FFEE);
        let mut old_fb = public_solver::sample_points(&plane, nfb, &mut rng_old);
        let mut class_fb = class_solver::sample_points(&plane, nfb, &mut rng_class);
        assert_eq!(old_fb, class_fb);
        assert_eq!(rng_old.0, rng_class.0);
        let first = old_fb
            .iter()
            .position(|p| PlaneQuartic::new(223, c.inst.f, p.map(|v| v as u32)).is_ok())
            .unwrap();
        old_fb.swap(0, first);
        let p0 = old_fb[0].map(|v| v as u32);
        let norm = NormV2::new(AdapterV2::with_base_point(&c, Some(p0)).unwrap()).unwrap();
        let pic = &norm.a.pic;
        assert_eq!(pic.base_point(), p0);
        assert_eq!(norm.a.core.quartic.map(|v| v as u32), c.inst.f);
        let index = class_fb
            .iter()
            .position(|p| *p == pic.base_point().map(u64::from))
            .unwrap();
        class_fb.swap(0, index);
        assert_eq!(old_fb, class_fb);
        let context = BridgeContext::new(&norm).unwrap();
        let hg = norm.a.transfer_point(&signed(&c, c.inst.g)).unwrap();
        assert!(!pic.is_zero(&hg));
        assert!(pic.is_zero(&pic.mul_scalar(&hg, c.inst.ell as u128)));
        assert_eq!(
            norm.norm(&hg).unwrap(),
            signed(&c, c.inst.ec.mul(&c.inst.g, 2))
        );
        let generator = norm.encode(&hg);
        let infinity = norm.a.short_point(QuarticPoint::InfinityMinus).unwrap();
        let origin = pic.reduce_deg6(&norm.a.trace_space(&infinity).unwrap());
        let other_p0 = pic
            .rational_points_bruteforce()
            .into_iter()
            .find(|&p| p != p0)
            .unwrap();
        let foreign = NormV2::new(AdapterV2::with_base_point(&c, Some(other_p0)).unwrap()).unwrap();
        let foreign_g = foreign.a.transfer_point(&signed(&c, c.inst.g)).unwrap();
        assert_ne!(norm.model_tag, foreign.model_tag);
        assert!(context
            .solve(
                &foreign.encode(&foreign_g),
                &generator,
                &class_params(nfb),
                seed
            )
            .is_err());
        assert!(context
            .solve(
                &norm.encode(&pic.zero()),
                &generator,
                &class_params(nfb),
                seed
            )
            .is_err());
        println!(
            "N4_ORIGIN_SETTING {}",
            json!({"setting_zero_index":setting,"nfb":nfb,"seed":seed,"P0":p0,
                "factor_base":old_fb,"RNG_after_sampling":rng_old.0,
                "quartic":c.inst.f,"field":norm.field_tag,"model":norm.model_tag,
                "generator":generator,"actual_raw_origin":origin.key().0.to_vec(),
                "origin_nonzero":!pic.is_zero(&origin),"foreign_P0":other_p0,
                "foreign_actual_model_and_zero_generator_rejected":true})
        );
        for (public_index, &q) in requests.iter().enumerate() {
            let hq = norm.a.transfer_point(&signed(&c, q)).unwrap();
            assert!(pic.is_zero(&pic.mul_scalar(&hq, c.inst.ell as u128)));
            let mut triples = vec![];
            let mut available_points = 0;
            let mut available_triples = 0;
            let mut wrong_origin_rejections = 0;
            for r in 0..=32 {
                let r0 = c.inst.ec.mul(&c.inst.g, r);
                let r1 = c.inst.ec.add(&r0, &c.inst.g);
                let r2 = c.inst.ec.add(&r0, &q);
                let points = [r0, r1, r2];
                let images: Vec<_> = points
                    .iter()
                    .map(|&p| norm.a.transfer_point(&signed(&c, p)).unwrap())
                    .collect();
                assert_eq!(pic.sub(&images[1], &images[0]), hg);
                assert_eq!(pic.sub(&images[2], &images[0]), hq);
                let raw: Vec<_> = points
                    .iter()
                    .map(|p| {
                        c.inst
                            .transfer_cubics(p)
                            .map(|rows| pic.reduce_deg6(&pic::Gen { k: 3, rows }))
                    })
                    .collect();
                for i in 0..3 {
                    if let Some(ref original) = raw[i] {
                        available_points += 1;
                        assert_eq!(*original, pic.add(&images[i], &origin));
                        assert_eq!(pic.sub(original, &origin), images[i]);
                        if !pic.is_zero(&origin) {
                            assert_ne!(*original, images[i]);
                            wrong_origin_rejections += 1;
                        }
                    }
                }
                if raw.iter().all(Option::is_some) {
                    available_triples += 1;
                    assert_eq!(
                        pic.sub(raw[1].as_ref().unwrap(), raw[0].as_ref().unwrap()),
                        hg
                    );
                    assert_eq!(
                        pic.sub(raw[2].as_ref().unwrap(), raw[0].as_ref().unwrap()),
                        hq
                    );
                }
                triples.push(json!({"r":r,"original_source_points":points.map(chained_n4_public_target::encode_point),
                    "completed_images":images.iter().map(|x|x.key().0.to_vec()).collect::<Vec<_>>(),
                    "original_legacy_raw":raw.iter().map(|x|x.as_ref().map(|a|a.key().0.to_vec())).collect::<Vec<_>>(),
                    "completed_differences_equal_public_G_Q":true}));
            }
            omitted_origin_controls += wrong_origin_rejections;
            println!(
                "N4_ORIGIN_GEOMETRY {}",
                json!({"setting":setting,"public_index":public_index,"P0":p0,
                    "r_inclusive":[0,32],"available_legacy_points":available_points,
                    "available_legacy_triples":available_triples,
                    "omitted_actual_nonzero_origin_rejections":wrong_origin_rejections,
                    "all_original_raw_equal_completed_plus_actual_origin":true,
                    "whole_triplets":triples})
            );
            let original =
                public_solver::ic_solve_target(&c.inst, &original_params(nfb), q, seed, true);
            let candidate = context
                .solve(&generator, &norm.encode(&hq), &class_params(nfb), seed)
                .unwrap();
            let original_target_ok = original
                .k_found
                .is_some_and(|k| pic.mul_scalar(&hg, k as u128) == hq);
            let original_source_ok = original.k_found.is_some_and(|k| c.verify_recovered(q, k));
            let candidate_target_ok = candidate
                .k_found
                .is_some_and(|k| pic.mul_scalar(&hg, k as u128) == hq);
            let candidate_source_ok = candidate.k_found.is_some_and(|k| c.verify_recovered(q, k));
            let expected = answers[public_index]["original_native_recovered_scalar"]
                .as_u64()
                .unwrap();
            if original.ok {
                assert!(original_target_ok && original_source_ok);
                assert_eq!(original.k_found, Some(expected));
            }
            if candidate.ok {
                assert!(candidate_target_ok && candidate_source_ok);
                assert_eq!(candidate.k_found, Some(expected));
            }
            if original.ok && candidate.ok {
                assert_eq!(original.k_found, candidate.k_found);
                common_solutions[public_index] += 1;
            }
            let row = json!({"setting":setting,"public_index":public_index,"nfb":nfb,"seed":seed,
                "same_actual_P0":p0,"original_public_Q":c.encode(q),"target_G":generator,"target_Q":norm.encode(&hq),
                "original":report!(original),"candidate":report!(candidate),
                "original_target_check":original_target_ok,"original_independent_source_check":original_source_ok,
                "candidate_target_check":candidate_target_ok,"candidate_independent_source_check":candidate_source_ok,
                "same_outcome":original.ok==candidate.ok,"common_correct_solve":original.ok&&candidate.ok,
                "scope":"same actual origin/factor base/DLP data;paths/counters need not agree;all costs incomplete"});
            println!("N4_ORIGIN_ATTEMPT {}", row);
            whole_cases.push(row);
            paired_attempts += 1;
        }
    }
    for (i, common) in common_solutions.into_iter().enumerate() {
        println!(
            "N4_ORIGIN_CASE {}",
            json!({"public_index":i,"common_correct_settings":common,"all4_pairs_retained":true})
        );
    }
    println!(
        "N4_ORIGIN_SCOPE {}",
        json!({"paired_attempts":paired_attempts,"solver_reports":2*paired_attempts,
            "common_correct_settings":common_solutions,"omitted_origin_controls":omitted_origin_controls,
            "all_attempts":whole_cases,"old729_scientific_inputs":"held by outer guards",
            "performance":"unpriced FpR/model/maps/admission/independentverify;no S/ratio/operational equivalence"})
    );
    assert_eq!(paired_attempts, 20);
    assert!(omitted_origin_controls > 0);
    assert!(
        common_solutions.iter().all(|&n| n > 0),
        "at least one COMMON correct IC setting per public target is required"
    );
}
