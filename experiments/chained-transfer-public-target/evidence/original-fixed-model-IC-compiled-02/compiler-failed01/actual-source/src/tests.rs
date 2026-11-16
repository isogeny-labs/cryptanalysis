use super::*;
use chained_n4_original_full_evaluator::{kp, Runtime};
use chained_n4_original_full_geometry::norm::EncodedClass;
use chained_n4_paired_fourth_preflight::{models::er, PairedFourth, ThirdHop};
use chained_n4_public_target::{ghs::EP, CheckedInstance};
use isogeny_algos::{curve::Pt, fpr::ER};
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
            packet, independent,
            "actual opaque chain differs from independent source-point Phi"
        );
        packet
    })
}
fn parameters(nfb: usize) -> class_solver::Params {
    class_solver::Params {
        nfb,
        rows_mult: 1.2,
        max_desc: 100000,
        sge: false,
        maxw: 12,
        lp2: true,
    }
}
fn report(r: &class_solver::Report) -> Value {
    json!({"ok":r.ok,"fail":r.fail,"k_found":r.k_found,"stats":r.stats,
        "phases":r.phases.iter().map(|(phase,c,wall)|json!({"phase":phase,"mul":c.mul,"inv":c.inv,"add":c.add,"lmul":c.lmul,"ladd":c.ladd,"hash":c.hash,"cmp":c.cmp,"wall":wall})).collect::<Vec<_>>(),
        "counter_scope":"original IC and wrapped Picard diagnostics only; FpR/setup/admission/source verification unknown, no calibrated price"})
}

#[test]
fn all_three_fixed_original_models_all_five_public_cases_all_sixty_attempts() {
    let c = CheckedInstance::construct().unwrap();
    let runtime = Runtime::construct(&c).unwrap();
    let pair = ThirdHop::construct(&c);
    let fourth = PairedFourth::construct(&c, &pair);
    let requests = c
        .parse(include_bytes!("../../fixtures/public-five.json"))
        .unwrap();
    let outside: Vec<Value> =
        serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
            .unwrap();
    assert_eq!(requests.len(), 5);
    let generators = packets(&runtime, source_points(&c, &pair, &fourth, c.inst.g));
    let targets: Vec<_> = requests
        .iter()
        .map(|&q| packets(&runtime, source_points(&c, &pair, &fourth, q)))
        .collect();
    println!(
        "N4_ORIGINAL_MODEL_IC_SETUP {}",
        json!({"protocol":"3da7fe/7550409 before Rust","whole_original_runtime_setup":runtime.setup,"actual_input_transfer_calls":runtime.calls(),"scope":"full original setup retained; extra setup not claimed minimal or priced"})
    );
    assert!(TargetContext::new(&runtime.geometry, 3).is_err());
    let mut attempts = 0;
    let mut solved_cases = 0;
    let mut all_targets = Vec::new();
    for side in 0..3 {
        let model = &runtime.geometry.models[side];
        let norm = &model.prime;
        let pic = &norm.a.pic;
        let context = TargetContext::new(&runtime.geometry, side).unwrap();
        let g = &generators[side];
        let gc = norm.decode(g).unwrap();
        assert!(!pic.is_zero(&gc));
        assert!(pic.is_zero(&pic.mul_scalar(&gc, ELL as u128)));
        println!(
            "N4_ORIGINAL_MODEL_IC_INPUT {}",
            json!({"side":side,"case":CASES[side],"mask":MASKS[side],"quartic":norm.a.core.quartic,"P0":pic.base_point(),"field":norm.field_tag,"model":norm.model_tag,"source":model.source.identity(),"ell":ELL,"order":ORDER,"generator":g,"actual_opaque_chain_equals_independent_Phi":true})
        );
        let mut cases = Vec::new();
        let mut solved = 0;
        for (public_index, &raw) in requests.iter().enumerate() {
            let q = &targets[public_index][side];
            let qc = norm.decode(q).unwrap();
            let mut successes = 0;
            for (attempt, &nfb) in [30, 36, 48, 64].iter().enumerate() {
                let seed = 102 + attempt as u64;
                let result = context.solve(g, q, &parameters(nfb), seed).unwrap();
                let target_ok = result
                    .k_found
                    .is_some_and(|k| pic.mul_scalar(&gc, k as u128) == qc);
                let source_ok = result.k_found.is_some_and(|k| c.verify_recovered(raw, k));
                println!(
                    "N4_ORIGINAL_MODEL_IC_ATTEMPT {}",
                    json!({"side":side,"public_index":public_index,"attempt":attempt,"nfb":nfb,"seed":seed,"original_public_target":c.encode(raw),"generator":g,"target":q,"report":report(&result),"actual_target_group_check":target_ok,"independent_original_source_check":source_ok,"actual_opaque_chain_equals_independent_Phi":true})
                );
                attempts += 1;
                if result.ok {
                    assert!(
                        target_ok && source_ok,
                        "reported IC success rejected by target or original-source verification"
                    );
                    assert_eq!(
                        result.k_found,
                        Some(
                            outside[public_index]["original_native_recovered_scalar"]
                                .as_u64()
                                .unwrap()
                        )
                    );
                    successes += 1;
                }
            }
            if successes > 0 {
                solved += 1;
                solved_cases += 1;
            }
            let row = json!({"side":side,"public_index":public_index,"successful_attempts":successes,"all_four_attempts_retained":true});
            println!("N4_ORIGINAL_MODEL_IC_CASE {}", row);
            cases.push(row);
        }
        let params = parameters(36);
        let mut controls = Vec::new();
        assert!(context
            .solve(&norm.encode(&pic.zero()), g, &params, 102)
            .is_err());
        controls.push("zero-generator");
        for name in [
            "field",
            "model",
            "source-model",
            "noncanonical",
            "malformed",
        ] {
            let mut bad = g.clone();
            match name {
                "field" => bad.field.push('x'),
                "model" => bad.model.push('x'),
                "source-model" => bad.model = model.source.source_tag().to_owned(),
                "noncanonical" => bad.key[1] = 223,
                "malformed" => bad.key[0] = 3,
                _ => unreachable!(),
            }
            assert!(context.solve(&bad, g, &params, 102).is_err());
            assert!(context.solve(g, &bad, &params, 102).is_err());
            controls.push(name);
        }
        let nonell = pic
            .rational_points_bruteforce()
            .into_iter()
            .map(|p| pic.mul_scalar(&pic.point_class(p), ELL as u128))
            .find(|p| !pic.is_zero(p))
            .unwrap();
        let nonell = norm.encode(&nonell);
        assert!(context.solve(&nonell, g, &params, 102).is_err());
        assert!(context.solve(g, &nonell, &params, 102).is_err());
        controls.push("non-ell-generator-and-target");
        let foreign = &generators[(side + 1) % 3];
        assert!(context.solve(foreign, g, &params, 102).is_err());
        assert!(context.solve(g, foreign, &params, 102).is_err());
        controls.push("actual-cross-target-packets");
        for kind in 0..5 {
            let mut bad = parameters(36);
            match kind {
                0 => bad.nfb = 3,
                1 => bad.nfb = 225,
                2 => bad.max_desc = 0,
                3 => bad.rows_mult = f64::NAN,
                4 => bad.rows_mult = 0.0,
                _ => unreachable!(),
            }
            assert!(context.solve(g, g, &bad, 102).is_err());
        }
        controls.push("all-five-invalid-parameter-kinds");
        controls.push("invalid-geometry-side");
        println!(
            "N4_ORIGINAL_MODEL_IC_REJECTIONS {}",
            json!({"side":side,"all_controls":controls,"all_rejected":true})
        );
        let row = json!({"side":side,"public_cases_solved":solved,"required":5,"all_cases":cases,"all_twenty_attempts_retained":true,"costs":"IC/Picard diagnostics only; primitive/setup/knownpoint/opaque-input/admission/reference costs unknown; no calibrated advantage"});
        println!("N4_ORIGINAL_MODEL_IC_TARGET {}", row);
        all_targets.push(row);
    }
    println!(
        "N4_ORIGINAL_MODEL_IC_SCOPE {}",
        json!({"all_targets":all_targets,"attempts":attempts,"public_cases_solved":solved_cases,"required_attempts":60,"required_public_cases":15,"solver_source":"literal existing new-target class_solver.rs, no edits","unpriced_costs":"source-validation;both-geometry-origins;model-map-setup;knownpoint;opaque-retained-transfer;FpR-extension;admission;final-independent-verification;matched-reference","scope":"finite original fixed model correctness only, unsigned, no calibrated ECDLP advantage"})
    );
    assert_eq!(attempts, 60);
    assert_eq!(
        solved_cases, 15,
        "whole frozen acceptance requires all15 public cases"
    );
}
