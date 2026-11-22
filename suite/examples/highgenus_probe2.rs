//! Stage timings for non-hyperelliptic planted instances (diagnostic).
use cryptanalysis_suite::highgenus::instances::{
    superelliptic_power_instance, three_point_instance,
};
use cryptanalysis_suite::highgenus::rho::{pollard_rho, RhoParams};
use cryptanalysis_suite::highgenus::JacobianGroup;
use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let which = args.get(1).map(|s| s.as_str()).unwrap_or("three");
    let g: u32 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(5);
    let lo: u32 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(12);
    let hi: u32 = args.get(4).and_then(|s| s.parse().ok()).unwrap_or(20);
    let t = Instant::now();
    if which == "three" {
        let inst = three_point_instance(g, 3, (lo, hi), 1).unwrap();
        eprintln!(
            "instance {} N bits {} in {:?}",
            inst.description,
            inst.n.bits(),
            t.elapsed()
        );
        let t = Instant::now();
        let x = inst.group.add(&inst.d1, &inst.d2);
        eprintln!("one group op {:?} (deg {})", t.elapsed(), x.degree());
        let t = Instant::now();
        let res = pollard_rho(
            &inst.group,
            &inst.d1,
            &inst.d2,
            &inst.n,
            &RhoParams::default(),
        )
        .unwrap();
        eprintln!(
            "rho ok={} walk_ops={} s={:.2} in {:?}",
            res.k == inst.k,
            res.walk_ops,
            res.s_walk,
            t.elapsed()
        );
    } else {
        let m: u32 = args.get(5).and_then(|s| s.parse().ok()).unwrap_or(3);
        let n: u32 = args.get(6).and_then(|s| s.parse().ok()).unwrap_or(8);
        let inst = superelliptic_power_instance(m, n, 3, (lo, hi), 1).unwrap();
        eprintln!(
            "instance {} g={} N bits {} in {:?}",
            inst.description,
            inst.genus,
            inst.n.bits(),
            t.elapsed()
        );
        let t = Instant::now();
        let x = inst.group.add(&inst.d1, &inst.d2);
        eprintln!("one group op {:?} (deg {})", t.elapsed(), x.degree());
        let t = Instant::now();
        let res = pollard_rho(
            &inst.group,
            &inst.d1,
            &inst.d2,
            &inst.n,
            &RhoParams::default(),
        )
        .unwrap();
        eprintln!(
            "rho ok={} walk_ops={} s={:.2} in {:?}",
            res.k == inst.k,
            res.walk_ops,
            res.s_walk,
            t.elapsed()
        );
    }
}
