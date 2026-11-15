//! CT126: diagnostic actual-field C169/C13a/C13b/D and warm-transfer timings.
//! NOT a complete ECDLP, PCC verification, or admitted benchmark.
use chained_n4_fixed_jacobian_chain_evaluator as chain;
use chained_n4_beta_rational_lift::Rational6;
use chained_n4_public_target::CheckedInstance;
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
    let scalars = [1u128, 2, 17, 12_345, chain::ELL as u128 - 1];
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
        let odd = source.prime.a.transfer_point(&chain::kp(q))
            .expect("independent public source lift");
        let packet = runtime.encode(0, &odd);
        let input = runtime.admit(0, &packet).expect("public admission");
        let d = runtime.transfer_entry(&input, 2).expect("direct route");
        let r = runtime.retained_lift_entry(&input, 2).expect("retained route");
        assert_eq!(d.class, r.class);
        assert_eq!(d.norm, r.norm);
        let a = runtime.check_final(&d).expect("full norm/order verification");
        let b = runtime.check_final(&r).expect("full norm/order verification");
        assert_eq!(a.key, b.key);
        outputs.push(json!({"scalar_fixture_only":k,"source_public":packet.key,
                            "output_public":a.key,"direct_equals_retained":true}));
        input_pts.push(p);
        intermediate.push(z13);
        final_pts.push(z169);
        packets.push(packet);
    }

    let labels = ["C169","C13_first","C13_second","D","direct_warm","retained_warm"];
    let mut readings: [Vec<u64>; 6] = std::array::from_fn(|_| Vec::new());
    // Four warmup blocks followed by twelve recorded blocks. Alternate evaluation order.
    for block in 0..16usize {
        let order = if block % 2 == 0 { [0,1,2,3,4,5] }
                    else { [5,4,3,2,1,0] };
        for op in order {
            let reps = if op < 4 { 64 } else { 5 };
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
                    4 | 5 => {
                        let input = runtime.admit(0, &packets[i])
                            .expect("paired admission");
                        let out = if op == 4 {
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
            json!({"repetitions_per_block": if i < 4 {64} else {5},
                   "raw_block_ns": readings[i]}));
    }
    let rss_kb = std::fs::read_to_string("/proc/self/status").ok()
        .and_then(|s| s.lines().find(|s| s.starts_with("VmHWM:"))
          .and_then(|s| s.split_whitespace().nth(1).and_then(|s| s.parse::<u64>().ok())));
    println!("{}", json!({
        "schema":"ct126-primitive-price/v1",
        "standing":"[pcc:unverified]",
        "scope":"actual elliptic arithmetic in prebuilt geometry; NOT cold single-target ECDLP",
        "source_prime":223,
        "subgroup_prime":chain::ELL,
        "complete_group_order":chain::ORDER,
        "scalar_fixture_count":scalars.len(),
        "setup_construct_ns":setup_ns,
        "linux_vm_hwm_kb":rss_kb,
        "identity_checks":outputs,
        "timed":timed,
        "rounds_recorded":12,
        "warmup_rounds":4,
        "timing_order":"ABBA by block; original/optimized process ABBA must be external"
    }));
}
