use super::*;
use chained_n4_public_target::{frozen_params, public_solver};
use serde_json::{json, Value};

macro_rules! report {
    ($r:expr) => {{
        let r=$r;
        json!({"ok":r.ok,"fail":r.fail,"k_found":r.k_found,"stats":r.stats,
            "phases":r.phases.iter().map(|(phase,c,wall)|json!({"phase":phase,"mul":c.mul,"inv":c.inv,"add":c.add,"lmul":c.lmul,"ladd":c.ladd,"hash":c.hash,"cmp":c.cmp,"wall":wall})).collect::<Vec<_>>(),
            "counter_scope":"originalN4 counters omit arithmetic in separate completed-map engine;correctness only"})
    }};
}

fn raw(c: &CheckedInstance, a: &AdapterV2, p: EP) -> pic::PicClass {
    a.pic.reduce_deg6(&completed_legacy_space(c, a, p).unwrap())
}

#[test]
fn completed_spaces_and_all_five_paired_public_target_solves() {
    let c = CheckedInstance::construct().unwrap();
    let targets = c
        .parse(include_bytes!("../../fixtures/public-five.json"))
        .unwrap();
    let outside: Vec<Value> =
        serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
            .unwrap();
    assert_eq!(targets.len(), 5);
    let plane = ic::Curve::new(223, &c.inst.f);
    let mut rng = common::Rng::new(102 ^ 0xC0FFEE);
    let fb = public_solver::sample_points(&plane, 36, &mut rng);
    let p0 = fb
        .iter()
        .find_map(|p| {
            let p = p.map(|v| v as u32);
            pic::PlaneQuartic::new(223, c.inst.f, p).ok().map(|_| p)
        })
        .unwrap();
    let n = NormV2::new(AdapterV2::with_base_point(&c, Some(p0)).unwrap()).unwrap();
    let a = &n.a;
    let origin = raw(&c, a, EP::Inf);
    assert!(!a.pic.is_zero(&origin));
    let mut sylow = vec![EP::Inf];
    let mut rng = common::Rng::new(0x58b2);
    for _ in 0..128 {
        let p = c.inst.ec.rand_point(&mut rng);
        let t = c.inst.ec.mul(&p, c.inst.ell as u128);
        for p in sylow.clone() {
            let v = c.inst.ec.add(&p, &t);
            if !sylow.contains(&v) {
                sylow.push(v);
            }
        }
        if sylow.len() == 4 {
            break;
        }
    }
    assert_eq!(sylow.len(), 4);
    let mut split_matches = 0;
    let mut complete_points = 0;
    for k in [0, 1, 2, 3, 17, 101, c.inst.ell / 2, c.inst.ell - 1] {
        for torsion in &sylow {
            let p = c.inst.ec.add(&c.inst.ec.mul(&c.inst.g, k as u128), torsion);
            let full = raw(&c, a, p);
            if let Some(rows) = c.inst.transfer_cubics(&p) {
                assert_eq!(full, a.pic.reduce_deg6(&pic::Gen { k: 3, rows }));
                split_matches += 1;
            }
            complete_points += 1;
        }
    }
    assert_eq!(complete_points, 32);
    assert_eq!(split_matches, 16);
    let r0 = c.inst.ec.mul(&c.inst.g, 101);
    let x0 = raw(&c, a, r0);
    let difference = a.pic.sub(&raw(&c, a, c.inst.ec.add(&r0, &c.inst.g)), &x0);
    assert!(!a.pic.is_zero(&difference));
    for (i, &q) in targets.iter().enumerate() {
        let image = a.pic.sub(&raw(&c, a, q), &origin);
        let doubled_old = match n.norm(&image).unwrap() {
            None => EP::Inf,
            Some((x, y)) => EP::A(c.inst.kf.sub(&x, &c.short_shift), c.inst.kf.neg(&y)),
        };
        assert_eq!(
            c.inst.ec.mul(&doubled_old, c.inst.ell.div_ceil(2) as u128),
            q
        );
        let diffq = a.pic.sub(&raw(&c, a, c.inst.ec.add(&r0, &q)), &x0);
        let known = outside[i]["original_native_recovered_scalar"]
            .as_u64()
            .unwrap();
        assert_eq!(a.pic.mul_scalar(&difference, known as u128), diffq);
    }
    println!(
        "N4_COMPLETED_CONTROL {}",
        json!({"actual_P0":p0,"geometric_origin":origin.key().0.to_vec(),"origin_nonzero":true,"complete_points":complete_points,"all_original_split_matches":split_matches,"all_five_point_half_inverse_controls":5,"all_five_affine_difference_controls":5,"ratio_base_nonzero":true,"scope":"actual originalPicard/completeGen bridge;not performance"})
    );
    let mut succeeded = 0;
    for (index, target) in targets.into_iter().enumerate() {
        let witness = outside[index]["original_native_recovered_scalar"]
            .as_u64()
            .unwrap();
        let mut candidate_success = false;
        let mut baseline_success = false;
        let mut cparam = 2.0;
        for attempt in 1..=6 {
            let old_params = frozen_params(cparam);
            let new_params = params(&old_params);
            let seed = 100 + attempt;
            let baseline = public_solver::ic_solve_target(&c.inst, &old_params, target, seed, true);
            let candidate = completed_solver::ic_solve_target(&c, &new_params, target, seed, true);
            let old_check = baseline
                .k_found
                .is_some_and(|k| c.verify_recovered(target, k));
            let new_check = candidate
                .k_found
                .is_some_and(|k| c.verify_recovered(target, k));
            println!(
                "N4_COMPLETED_ATTEMPT {}",
                json!({"target_index":index,"attempt":attempt,"c":cparam,"nfb":old_params.nfb,"seed":seed,"public_target":c.encode(target),"baseline":report!(&baseline),"candidate":report!(&candidate),"independent_baseline_check":old_check,"independent_candidate_check":new_check,"scope":"paired correctness/all retries retained;no speed orcountercoverage claim"})
            );
            if baseline.ok {
                assert!(old_check);
                assert_eq!(baseline.k_found, Some(witness));
                baseline_success = true;
            }
            if candidate.ok {
                assert!(new_check);
                assert_eq!(candidate.k_found, Some(witness));
                assert!(candidate
                    .stats
                    .iter()
                    .any(|(name, v)| name == "completed_map_calls" && *v == 3.0));
                candidate_success = true;
                break;
            }
            cparam += 0.4;
        }
        assert!(
            baseline_success,
            "frozen original publicIC baseline incomplete"
        );
        if candidate_success {
            succeeded += 1;
        }
        println!(
            "N4_COMPLETED_TARGET {}",
            json!({"target_index":index,"baseline_success":baseline_success,"candidate_success":candidate_success})
        );
    }
    println!(
        "N4_COMPLETED_FIVE {}",
        json!({"required":5,"candidate_successes":succeeded,"all_retries_retained":true,"original_relation_LA_descent_walks_unchanged":true,"no_DLP_fallback":true,"no_measured_advantage":true})
    );
    assert_eq!(
        succeeded, 5,
        "completed-descent candidate failed frozen five-target correctness criterion"
    );
}
