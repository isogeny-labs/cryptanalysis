//! Stage timings for one planted instance (diagnostic).
use cryptanalysis_suite::highgenus::fp::Fp;
use cryptanalysis_suite::highgenus::instances::{hyperelliptic_instance, prime_one_mod};
use cryptanalysis_suite::highgenus::jacobi::{
    find_prime_subgroup_order, jacobian_order_with_orbit_norms, JacobiSumCurve,
};
use cryptanalysis_suite::highgenus::rho::{pollard_rho, RhoParams};
use num_bigint::BigUint;
use num_traits::One;
use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let g: u32 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(5);
    let lo: u32 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(16);
    let hi: u32 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(22);
    let n_exp = 2 * g + 1;
    let mut p = prime_one_mod(2 * n_exp as u64, 3).unwrap();
    for _ in 0..6 {
        let t = Instant::now();
        let curve = JacobiSumCurve::PowerSum {
            m: 2,
            n: n_exp,
            a: 1,
        };
        let (order, norms) = jacobian_order_with_orbit_norms(&curve, p).unwrap();
        eprintln!("p={p} order bits {} in {:?}", order.bits(), t.elapsed());
        let t = Instant::now();
        let r = find_prime_subgroup_order(
            &order,
            &norms,
            &(BigUint::one() << lo),
            &(BigUint::one() << hi),
            2_000_000,
        );
        eprintln!(
            "  subgroup search {:?} -> {:?}",
            t.elapsed(),
            r.as_ref().map(|(n, _)| n.bits())
        );
        if r.is_some() {
            break;
        }
        p = prime_one_mod(2 * n_exp as u64, p + 1).unwrap();
    }
    let t = Instant::now();
    let inst = hyperelliptic_instance(g, 3, (lo, hi), 1).unwrap();
    eprintln!(
        "instance {} N bits {} in {:?}",
        inst.description,
        inst.n.bits(),
        t.elapsed()
    );
    let _ = Fp::new(inst.p);
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
