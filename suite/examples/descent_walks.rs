//! Walk-count experiment for the k0n53 walked descent
//! (`experiments/descent-walks-k0n53-20261104/PROTOCOL.md`).
//!
//! Builds the perfbench k0n53 rung once (degree 53, a = 0 Koblitz curve,
//! 15,000-point subgroup-orbit base, folded pair table, collection seed 1,
//! m = 3 collection, m = 2 descent), solves its factor-base logarithms,
//! then descends every held-out target under every walk count in an
//! interleaved, seeded order, one target at a time on one thread.  Every
//! recovered logarithm is checked against the scalar the target was made
//! from.  One JSON line per (round, arm, target) on stdout.
//!
//! ```text
//! cargo run --release --example descent_walks -- \
//!     --walks 64,64,128,256,512 --targets 48 --target-seed 1000 \
//!     --rounds 3 --order-seed 20261104
//! ```

use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::{
    build_subgroup_orbit_factor_base, CollectedRelation, ColumnCoverage, DecompositionStrategy,
    FactorBaseLogSolver, IndividualLogSolver, KoblitzCurve, KoblitzIcOptions, LinearAlgebra,
    PairSumTable, RelationCollector, RelationWorkUnit,
};
use cryptanalysis_suite::cryptanalysis::koblitz_sparse_la::SparseSolveOptions;
use num_bigint::BigUint;
use rand::rngs::StdRng;
use rand::seq::SliceRandom;
use rand::{Rng, SeedableRng};
use std::time::Instant;

fn arg<T: std::str::FromStr>(args: &[String], name: &str, default: T) -> T {
    args.iter()
        .position(|a| a == name)
        .and_then(|i| args.get(i + 1))
        .and_then(|v| v.parse().ok())
        .unwrap_or(default)
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let walks: Vec<usize> = args
        .iter()
        .position(|a| a == "--walks")
        .and_then(|i| args.get(i + 1))
        .map(|v| {
            v.split(',')
                .map(|w| w.parse().expect("walk count"))
                .collect()
        })
        .unwrap_or_else(|| vec![64, 64, 128, 256, 512]);
    let n_targets: u64 = arg(&args, "--targets", 48);
    let target_seed: u64 = arg(&args, "--target-seed", 1000);
    let rounds: usize = arg(&args, "--rounds", 3);
    let order_seed: u64 = arg(&args, "--order-seed", 20_261_104);

    // The perfbench k0n53 rung (examples/perfbench/relation.rs, `k0n53`).
    let curve = KoblitzCurve::subfield(1, 53, 0, 1).expect("Koblitz curve a = 0");
    let fb = build_subgroup_orbit_factor_base(&curve, 1, 15_000).expect("k0n53 base");
    let ic = KoblitzIcOptions {
        m: 3,
        descent_m: Some(2),
        collection_window: Some(477),
        strategy: DecompositionStrategy::PairTable,
        collapse_negation: true,
        collapse_projected_orbits: true,
        crossbred: None,
        allow_direct_relation: false,
        max_trials: 20_000_000,
        seed: 1,
        linear_algebra: LinearAlgebra::Sparse(SparseSolveOptions::default()),
        ..KoblitzIcOptions::default()
    };
    let t0 = Instant::now();
    let pair = PairSumTable::build_folded_within(&curve, &fb, PairSumTable::DEFAULT_BYTE_BUDGET)
        .expect("folded pair table fits");
    let collector =
        RelationCollector::with_pair_table(&curve, &fb, &ic, Some(&pair)).expect("collector");
    let mut solver = FactorBaseLogSolver::new(&curve, &fb, &ic).expect("projected columns");
    let mut coverage = ColumnCoverage::new(&curve, &fb).expect("projected columns");
    let mut table = None;
    for u in 0..2048u64 {
        let missing = coverage.missing_points();
        let aim = (!missing.is_empty()).then_some(missing);
        let unit = RelationWorkUnit {
            seed: 1,
            start: u * 2048,
            count: 2048,
        };
        let (rels, _) = collector.collect_aimed(unit, aim.as_deref());
        coverage.add(&rels);
        let rels: Vec<CollectedRelation> = rels;
        solver.push(&rels);
        if let Some((t, _)) = solver.try_solve() {
            table = Some(t);
            break;
        }
    }
    let table = table.expect("k0n53 log table solved");
    eprintln!("fixture built in {:.1} s", t0.elapsed().as_secs_f64());

    let r = curve.subgroup_order.to_u64_digits()[0];
    let targets: Vec<(u64, _)> = (target_seed..target_seed + n_targets)
        .map(|seed| {
            let k = StdRng::seed_from_u64(seed ^ 0x534f_4c56_4552_5447).gen_range(1..r);
            (k, curve.mul(curve.generator(), &BigUint::from(k)))
        })
        .collect();

    let mut rng = StdRng::seed_from_u64(order_seed);
    for round in 0..rounds {
        let mut order: Vec<usize> = (0..walks.len()).collect();
        order.shuffle(&mut rng);
        for &arm in &order {
            let w = walks[arm];
            let s = IndividualLogSolver::new(&curve, &fb, &table, &ic, Some(&pair))
                .expect("descent solver")
                .with_walks(w);
            for (ti, (k, q)) in targets.iter().enumerate() {
                let t = Instant::now();
                let out = s.solve(q);
                let ns = t.elapsed().as_nanos();
                let (verified, trials) = match &out {
                    Some((d, rep)) => (*d == BigUint::from(*k), rep.trials),
                    None => (false, 0),
                };
                println!(
                    "{{\"round\":{round},\"arm\":{arm},\"walks\":{w},\"target\":{ti},\"seed\":{},\"solved\":{},\"verified\":{verified},\"trials\":{trials},\"ns\":{ns}}}",
                    target_seed + ti as u64,
                    out.is_some()
                );
            }
        }
    }
}
