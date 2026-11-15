use super::*;
use chained_n4_completed_v2::{AdapterV2, NormV2};
use chained_n4_odd_product_maps::{Adapter, NormNew, Point};
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
fn report(r: &class_solver::Report) -> Value {
    json!({"ok":r.ok,"fail":r.fail,"k_found":r.k_found,"stats":r.stats,
        "phases":r.phases.iter().map(|(phase,c,wall)|json!({"phase":phase,"mul":c.mul,"inv":c.inv,"add":c.add,"lmul":c.lmul,"ladd":c.ladd,"hash":c.hash,"cmp":c.cmp,"wall":wall})).collect::<Vec<_>>(),
        "counter_scope":"original IC and wrapped canonical Picard only;FpR/map/setup/admission/independentverify costs incomplete;not S or benchmark"})
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

#[test]
fn all_three_actual_jacobians_all_five_public_targets_all_sixty_ic_attempts() {
    let c = CheckedInstance::construct().unwrap();
    let old = NormV2::new(AdapterV2::new(&c).unwrap()).unwrap();
    let t = OddSourceIsogeny::construct(&c);
    let source = SourceE::degree13_target(&c, &t);
    let (models, _) = construct_all(&source, &old.a);
    let requests = c
        .parse(include_bytes!("../../fixtures/public-five.json"))
        .unwrap();
    let answers: Vec<Value> =
        serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
            .unwrap();
    let mut whole_attempts = 0;
    let mut total_solved = 0;
    let mut targets = vec![];
    let mut foreign: Option<EncodedClass> = None;
    for model in models {
        if model.square_root.is_none() {
            continue;
        }
        let id = [model.root_index, model.sign_index];
        let norm = NormNew::new(Adapter::new(&source, &old.a, model).unwrap()).unwrap();
        let map = FastSourceChain::new(&c, &norm, &t).unwrap();
        let context = TargetContext::new(&norm).unwrap();
        let pic = &norm.a.pic;
        let g = map
            .from_source(&map.encode_source(short(&c, c.inst.g)))
            .unwrap();
        let gc = norm.decode(&g).unwrap();
        assert!(!pic.is_zero(&gc));
        assert!(pic.is_zero(&pic.mul_scalar(&gc, c.inst.ell as u128)));
        println!(
            "N4_NEW_JACOBIAN_IC_INPUT {}",
            json!({"protocol":"98c6f0/2aee published beforecode","target":id,"quartic":norm.a.core.quartic,"P0":pic.base_point(),"model":norm.model_tag,"field":norm.field_tag,"ell":c.inst.ell,"order":c.inst.order,"public_generator":g,"source":source.identity(),"runtime":"only actual target classes/curve/ell/algorithm parameters;no source solver or scalar witness"})
        );
        let mut solved = 0;
        let mut case_rows = vec![];
        for (i, &raw) in requests.iter().enumerate() {
            let q = map.from_source(&map.encode_source(short(&c, raw))).unwrap();
            let qc = norm.decode(&q).unwrap();
            let mut successes = 0;
            for (attempt, &nfb) in [30, 36, 48, 64].iter().enumerate() {
                let seed = 102 + attempt as u64;
                let params = parameters(nfb);
                let r = context.solve(&g, &q, &params, seed).unwrap();
                let target_ok = r
                    .k_found
                    .is_some_and(|k| pic.mul_scalar(&gc, k as u128) == qc);
                let source_ok = r.k_found.is_some_and(|k| c.verify_recovered(raw, k));
                let expected = answers[i]["original_native_recovered_scalar"]
                    .as_u64()
                    .unwrap();
                println!(
                    "N4_NEW_JACOBIAN_IC_ATTEMPT {}",
                    json!({"target":id,"public_index":i,"attempt":attempt,"nfb":nfb,"seed":seed,"original_public_target":c.encode(raw),"actual_Jacobian_G":g,"actual_Jacobian_Q":q,"report":report(&r),"actual_target_group_check":target_ok,"independent_original_source_check":source_ok,"scope":"all60 attempts including failures retained;original counters incomplete/no performance comparison"})
                );
                whole_attempts += 1;
                if r.ok {
                    assert!(
                        target_ok && source_ok,
                        "reported IC success rejected by actualtarget or independent source"
                    );
                    assert_eq!(r.k_found, Some(expected));
                    successes += 1;
                }
            }
            if successes > 0 {
                solved += 1;
                total_solved += 1;
            }
            let row = json!({"target":id,"public_index":i,"successful_attempts":successes,"all4_attempts_retained":true});
            println!("N4_NEW_JACOBIAN_IC_CASE {}", row);
            case_rows.push(row);
        }
        let params = parameters(36);
        let mut controls = vec![];
        assert!(context
            .solve(&norm.encode(&pic.zero()), &g, &params, 102)
            .is_err());
        controls.push("zero-generator");
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
            assert!(context.solve(&bad, &g, &params, 102).is_err());
            assert!(context.solve(&g, &bad, &params, 102).is_err());
            controls.push(label);
        }
        let nonodd = pic
            .rational_points_bruteforce()
            .into_iter()
            .map(|p| pic.mul_scalar(&pic.point_class(p), c.inst.ell as u128))
            .find(|x| !pic.is_zero(x))
            .unwrap();
        let nonodd = norm.encode(&nonodd);
        assert!(context.solve(&nonodd, &g, &params, 102).is_err());
        assert!(context.solve(&g, &nonodd, &params, 102).is_err());
        controls.push("nonodd-generator-and-target");
        if let Some(ref bad) = foreign {
            assert!(context.solve(bad, &g, &params, 102).is_err());
            assert!(context.solve(&g, bad, &params, 102).is_err());
            controls.push("actual-foreign-target-model");
        }
        foreign = Some(g.clone());
        let row = json!({"target":id,"public_cases_solved":solved,"required":5,"all_cases":case_rows,"negative_controls":controls,"compatibility_control":"original source-bound solver chooses random fb0 and affine legacy-origin triples;exact same-origin same-input bridge not supplied;control remains open,not replaced by an ECDLP fallback","cost_coverage":{"original_IC_and_wrapped_Picard":"diagnostic counters retained","FpR":"no exposed counter;unpriced unknown","source_model_map_setup_and_evaluations":"outside solver counters;unpriced unknown","source_target_admission":"outside phases;unpriced unknown","independent_source_verification":"outside phases;unpriced unknown","S_ratio_or_advantage":"not admitted or established"}});
        println!("N4_NEW_JACOBIAN_IC_TARGET {}", row);
        targets.push(row);
    }
    println!(
        "N4_NEW_JACOBIAN_IC_SCOPE {}",
        json!({"all_targets":targets,"attempts":whole_attempts,"all15_public_cases_solved":total_solved,"required_public_cases":15,"protocol":"98c6f0","complete_costs":"unknown;not zero","performance":"no S/ratio or IC/rho advantage claim","original703_refinement_inputs":"immutable;guarded outside native"})
    );
    assert_eq!(whole_attempts, 60);
    assert_eq!(
        total_solved, 15,
        "native IC acceptance requires all15 public cases;whole failures remain"
    );
}
