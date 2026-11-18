//! CT126: diagnostic actual-field C169/C13a/C13b/D and warm-transfer timings.
//! NOT a complete ECDLP, PCC verification, or admitted benchmark.
use chained_n4_fixed_jacobian_chain_evaluator as chain;
use chained_n4_fixed_jacobian_chain::{ELL, ORDER};
use chained_n4_beta_rational_lift::Rational6;
use chained_n4_public_target::CheckedInstance;
use chained_n4_paired_fourth_preflight::models::even::back6;
use isogeny_algos::curve::{self, Pt};
use serde_json::{json, Value};
use std::{hint::black_box, time::Instant};

fn ns(t: Instant) -> u64 {
    u64::try_from(t.elapsed().as_nanos()).expect("elapsed ns overflow")
}
fn main() {
    let before = Instant::now();
    let c = CheckedInstance::construct().expect("pinned CheckedInstance");
    let runtime = chain::Runtime::construct(&c).expect("pinned complete geometry");
    let setup_ns = ns(before);

    let certificates = &runtime.geometry.map_certificates;
    let first = Rational6::new(&certificates["pair"]["whole_rational_checks"][0]["map"]);
    let second = Rational6::new(&certificates["fourth"]["twist_fourth_forward"]);
    let composite_cert = runtime.setup["actual_composite_certificates"]
        .as_array().expect("composite records").iter()
        .find(|r| r["source"] == 0 && r["target"] == 2)
        .expect("exact original 0->2 composite");
    let composite = Rational6::new(&composite_cert["whole_composite"]);
    let source = &runtime.geometry.models[0];
    let target = &runtime.geometry.models[2];
    let f = &source.quadratic.f;
    let e = &target.quadratic.curve;
    let scalars = [1u128, 2, 17, 12_345, ELL as u128 - 1];
    let mut input_pts: Vec<Pt<_>> = Vec::new();
    let mut intermediate: Vec<Pt<_>> = Vec::new();
    let mut final_pts: Vec<Pt<_>> = Vec::new();
    let mut packets = Vec::new();
    let mut outputs: Vec<Value> = Vec::new();

    for k in scalars {
        let q = curve::pmul(source.source.field(), source.source.curve(),
                           &source.source.generator(), k);
        let p = chain::lift(q);
        source.quadratic.admit(&p).expect("actual source curve");
        let z13 = first.eval(f, p);
        let z1313 = second.eval(f, z13);
        let z169 = composite.eval(f, p);
        assert_eq!(z169, z1313, "two-hop isogenies must equal composite");
        target.quadratic.admit(&z169).expect("actual target curve");
        let doubled = curve::padd(&target.quadratic.f, e, &z169, &z169);
        target.quadratic.admit(&doubled).expect("actual target double");
        // Exact CT125 norm-point path: pmul(P,2) THEN descent, not D_padd.
        let optimized_norm = match curve::pmul(&target.quadratic.f, e, &z169, 2) {
            Pt::Inf => Pt::Inf,
            Pt::Aff(x, y) => Pt::Aff(back6(x), back6(y)),
        };
        let padd_then_descend = match doubled {
            Pt::Inf => Pt::Inf,
            Pt::Aff(x, y) => Pt::Aff(back6(x), back6(y)),
        };
        assert_eq!(optimized_norm, padd_then_descend,
                   "N2_actual and descended D_padd disagree mathematically");
        target.quadratic.admit(&optimized_norm)
            .expect("actual optimized norm point on target quadratic curve");
        let odd = source.prime.a.transfer_point(&chain::kp(q))
            .expect("independent public source lift");
        let packet = runtime.encode(0, &odd);
        let input = runtime.admit(0, &packet).expect("public admission");
        let d = runtime.transfer_entry(&input, 2).expect("direct route");
        let r = runtime.retained_lift_entry(&input, 2).expect("retained route");
        // Entry's raw class and norm are intentionally private. check_final()
        // independently verifies each actual Jacobian norm and full-group order;
        // compare the complete canonical public class representations instead.
        let a = runtime.check_final(&d).expect("full norm/order verification");
        let b = runtime.check_final(&r).expect("full norm/order verification");
        assert_eq!(a.field, b.field, "destination field mismatch");
        assert_eq!(a.model, b.model, "destination model mismatch");
        assert_eq!(a.key, b.key, "canonical target class mismatch");
        outputs.push(json!({"scalar_fixture_only":k,"source_public":packet.key,
                            "output_public":a.key,"direct_equals_retained":true}));
        input_pts.push(p);
        intermediate.push(z13);
        final_pts.push(z169);
        packets.push(packet);
    }

    let labels = ["C169","C13_first","C13_second","D_padd","N2_actual","direct_warm","retained_warm"];
    let mut readings: [Vec<u64>; 7] = std::array::from_fn(|_| Vec::new());
    // Four warmup blocks followed by twelve recorded blocks. Alternate evaluation order.
    for block in 0..16usize {
        let order = if block % 2 == 0 { [0,1,2,3,4,5,6] }
                    else { [6,5,4,3,2,1,0] };
        for op in order {
            let reps = if op < 5 { 64 } else { 5 };
            let start = Instant::now();
            for rep in 0..reps {
                let i = (rep + block) % scalars.len();
                match op {
                    0 => { black_box(composite.eval(f, input_pts[i])); }
                    1 => { black_box(first.eval(f, input_pts[i])); }
                    2 => { black_box(second.eval(f, intermediate[i])); }
                    3 => {
                        black_box(curve::padd(&target.quadratic.f, e,
                                             &final_pts[i], &final_pts[i]));
                    }
                    4 => {
                        // Source-identical arithmetic to CT125 Runtime::norm_point
                        // (its Cell counter bump is intentionally NOT timed).
                        // The selected operand cohort remains CT126's FIVE
                        // points, NOT the full 48/695 population.
                        let doubled = curve::pmul(&target.quadratic.f, e, &final_pts[i], 2);
                        let actual_norm = match doubled {
                            Pt::Inf => Pt::Inf,
                            Pt::Aff(x, y) => Pt::Aff(back6(x), back6(y)),
                        };
                        black_box(actual_norm);
                    }
                    5 | 6 => {
                        let input = runtime.admit(0, &packets[i])
                            .expect("paired admission");
                        let out = if op == 5 {
                            runtime.transfer_entry(&input, 2)
                        } else {
                            runtime.retained_lift_entry(&input, 2)
                        }.expect("paired transfer");
                        black_box(runtime.check_final(&out).expect("paired verification").key);
                    }
                    _ => unreachable!(),
                }
            }
            let elapsed = ns(start);
            if block >= 4 {
                readings[op].push(elapsed);
            }
        }
    }
    let mut timed = serde_json::Map::new();
    for (i, label) in labels.iter().enumerate() {
        timed.insert((*label).to_owned(),
            json!({"repetitions_per_block": if i < 5 {64} else {5},
                   "raw_block_ns": readings[i]}));
    }
    let rss_kb = std::fs::read_to_string("/proc/self/status").ok()
        .and_then(|s| s.lines().find(|s| s.starts_with("VmHWM:"))
          .and_then(|s| s.split_whitespace().nth(1).and_then(|s| s.parse::<u64>().ok())));
    println!("{}", json!({
        "schema":"ct191-exact-norm-warm-price/v1",
        "standing":"[pcc:unverified]",
        "scope":"five original CT126 toy input points, same warm geometry; N2_actual executes pmul(2)+back6; NOT full 48/695 custody, cold ECDLP or signed PCC",
        "source_prime":223,
        "subgroup_prime":ELL,
        "complete_group_order":ORDER,
        "scalar_fixture_count":scalars.len(),
        "setup_construct_ns":setup_ns,
        "linux_vm_hwm_kb":rss_kb,
        "identity_checks":outputs,
        "timed":timed,
        "rounds_recorded":12,
        "warmup_rounds":4,
        "timing_order":"alternating forward/reverse seven-arm order; external cold-process randomization separately required"
    }));
}
