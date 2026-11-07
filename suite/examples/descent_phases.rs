//! Native per-phase wall-time profile of the k0n53 walked descent.
//!
//! Callgrind cannot see the AVX-512 kernels the descent runs natively, and
//! the session VM has no PMU, so this driver mirrors
//! `IndividualLogSolver::solve_by_walking` round for round through the same
//! public calls (`keys_of`, `prefetch_key`, `contains_key`,
//! `decompose_fast`, `add_many_lazy`, `finish_lazy`), stopping each target
//! at its first decomposition, and times each phase with `Instant`.  The
//! logarithm step after a decomposition (one modular inverse) is left out.
//!
//! ```text
//! cargo run --release --example descent_phases -- --walks 512 --targets 64
//! ```

use cryptanalysis_suite::cryptanalysis::koblitz_fast::{BatchScratch, FastCurve, FastPoint};
use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::{
    build_subgroup_orbit_factor_base, KoblitzCurve, PairSumTable,
};
use num_bigint::BigUint;
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use std::time::{Duration, Instant};

fn arg<T: std::str::FromStr>(args: &[String], name: &str, default: T) -> T {
    args.iter()
        .position(|a| a == name)
        .and_then(|i| args.get(i + 1))
        .and_then(|v| v.parse().ok())
        .unwrap_or(default)
}

#[derive(Default)]
struct Phases {
    setup: Duration,
    keys: Duration,
    prefetch: Duration,
    probe: Duration,
    decompose: Duration,
    advance: Duration,
    finish: Duration,
    trials: u64,
    rounds: u64,
    probes_admitted: u64,
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let walks: usize = arg(&args, "--walks", 512);
    let n_targets: u64 = arg(&args, "--targets", 64);
    let target_seed: u64 = arg(&args, "--target-seed", 9000);
    // 0 = prefetch the whole round first (the solver's loop); D > 0 =
    // prefetch key i + D while probing key i.
    let distance: usize = arg(&args, "--prefetch-distance", 0);

    let curve = KoblitzCurve::subfield(1, 53, 0, 1).expect("Koblitz curve a = 0");
    let fb = build_subgroup_orbit_factor_base(&curve, 1, 15_000).expect("k0n53 base");
    let pair = PairSumTable::build_folded_within(&curve, &fb, PairSumTable::DEFAULT_BYTE_BUDGET)
        .expect("folded pair table fits");
    let rss = std::fs::read_to_string("/proc/self/status")
        .ok()
        .and_then(|s| {
            s.lines()
                .find(|l| l.starts_with("VmRSS:"))
                .map(|l| l.split_whitespace().nth(1).unwrap_or("0").to_string())
        })
        .unwrap_or_default();
    eprintln!(
        "pair table: tier {}, {} sums, process RSS {} kB after build",
        pair.tier(),
        pair.len(),
        rss
    );
    if args.iter().any(|a| a == "--probe-bench") {
        if let Some(st) = pair.folded_storage() {
            eprintln!(
                "filter: {} words ({} KiB), mask bits {}, rests {} ({} KiB), buckets {}",
                st.present.len(),
                st.present.len() * 8 / 1024,
                64 - st.present_mask.leading_zeros(),
                st.words.len(),
                st.words.len() * 4 / 1024,
                st.bucket_start.len()
            );
        }
        if let Some(st) = pair.folded_storage() {
            // The filter test alone, with the table's hash.
            let hash = |key: u64| {
                let mut h = key.wrapping_mul(0xff51_afd7_ed55_8ccd);
                h ^= h >> 33;
                h.wrapping_mul(0xc4ce_b9fe_1a85_ec53)
            };
            let mut rng = StdRng::seed_from_u64(2);
            let keys: Vec<u64> = (0..8_000_000).map(|_| rng.gen::<u64>() >> 10).collect();
            let t = Instant::now();
            let mut admitted = 0u64;
            for &k in &keys {
                let h = (hash(k) & st.present_mask) as usize;
                admitted += st.present[h >> 6] >> (h & 63) & 1;
            }
            let passed: Vec<u64> = keys
                .iter()
                .copied()
                .filter(|&k| {
                    let h = (hash(k) & st.present_mask) as usize;
                    st.present[h >> 6] >> (h & 63) & 1 == 1
                })
                .collect();
            let t2 = Instant::now();
            let mut hits2 = 0u64;
            for &k in &passed {
                hits2 += u64::from(pair.contains_key(k));
            }
            eprintln!(
                "contains_key on {} filter-admitted keys: {:.2} ns each ({hits2} hits)",
                passed.len(),
                t2.elapsed().as_nanos() as f64 / passed.len() as f64
            );
            eprintln!(
                "filter alone: {:.2} ns per probe, admit rate {:.4}",
                t.elapsed().as_nanos() as f64 / 8e6,
                admitted as f64 / 8e6
            );
        }
        // contains_key alone: one hot key, then 8M random keys.
        let mut rng = StdRng::seed_from_u64(1);
        let keys: Vec<u64> = (0..8_000_000).map(|_| rng.gen::<u64>() >> 10).collect();
        let t = Instant::now();
        let mut hits = 0u64;
        for _ in 0..8_000_000 {
            hits += u64::from(pair.contains_key(std::hint::black_box(keys[0])));
        }
        let hot = t.elapsed().as_nanos() as f64 / 8e6;
        let t = Instant::now();
        for &k in &keys {
            hits += u64::from(pair.contains_key(k));
        }
        let random = t.elapsed().as_nanos() as f64 / 8e6;
        let t = Instant::now();
        for (i, &k) in keys.iter().enumerate() {
            if let Some(&next) = keys.get(i + 16) {
                pair.prefetch_key(next);
            }
            hits += u64::from(pair.contains_key(k));
        }
        let pf = t.elapsed().as_nanos() as f64 / 8e6;
        eprintln!("contains_key with prefetch distance 16: {pf:.2} ns per probe");
        eprintln!("contains_key: hot {hot:.2} ns, random {random:.2} ns per probe ({hits} hits)");
        return;
    }
    let fc = FastCurve::new(&curve.curve).expect("single-word field");
    let g = fc.lift(curve.generator());
    let r = curve.subgroup_order.to_u64_digits()[0];

    let mut ph = Phases::default();
    let wall = Instant::now();
    for seed in target_seed..target_seed + n_targets {
        let k = StdRng::seed_from_u64(seed ^ 0x534f_4c56_4552_5447).gen_range(1..r);
        let q = fc.lift(&curve.mul(curve.generator(), &BigUint::from(k)));

        let t = Instant::now();
        let stride = (r / walks as u64).max(1 << 20);
        let mut rng = StdRng::seed_from_u64(seed);
        let a0 = rng.gen_range(1..r);
        let b = rng.gen_range(1..r);
        let stride_point = fc.mul_u64(g, stride);
        let mut states: Vec<FastPoint> = Vec::with_capacity(walks);
        let mut state = fc.add(fc.mul_u64(g, a0), fc.mul_u64(q, b));
        for _ in 0..walks {
            states.push(state);
            state = fc.add(state, stride_point);
        }
        let mut advanced = Vec::with_capacity(walks);
        let mut lambdas: Vec<u64> = Vec::with_capacity(walks);
        let mut scratch = BatchScratch::default();
        let mut keys: Vec<u64> = Vec::with_capacity(walks);
        ph.setup += t.elapsed();

        'walk: loop {
            ph.rounds += 1;
            let t = Instant::now();
            pair.keys_of(&states, &mut keys);
            ph.keys += t.elapsed();
            let t = Instant::now();
            let ahead = if distance == 0 {
                keys.len()
            } else {
                distance.min(keys.len())
            };
            for &key in &keys[..ahead] {
                pair.prefetch_key(key);
            }
            ph.prefetch += t.elapsed();
            // The loop is timed whole (a timer per trial would cost as much
            // as the probe); the decompositions, rare, are timed inside it
            // and taken out of the probe figure.
            let t = Instant::now();
            let mut dec = Duration::ZERO;
            let mut hit = false;
            for (i, (s, &key)) in states.iter().zip(&keys).enumerate() {
                if distance != 0 {
                    if let Some(&next) = keys.get(i + distance) {
                        pair.prefetch_key(next);
                    }
                }
                ph.trials += 1;
                if s.infinity || !pair.contains_key(key) {
                    continue;
                }
                ph.probes_admitted += 1;
                let td = Instant::now();
                let found = pair.decompose_fast(*s, 2);
                dec += td.elapsed();
                if found.is_some() {
                    hit = true;
                    break;
                }
            }
            ph.probe += t.elapsed() - dec;
            ph.decompose += dec;
            if hit {
                break 'walk;
            }
            let t = Instant::now();
            advanced.clear();
            lambdas.clear();
            fc.add_many_lazy(g, &states, &mut advanced, &mut lambdas, &mut scratch);
            ph.advance += t.elapsed();
            let t = Instant::now();
            for ((s, sum), &lambda) in states.iter_mut().zip(&advanced).zip(&lambdas) {
                *s = fc.finish_lazy(g, *sum, lambda);
            }
            ph.finish += t.elapsed();
        }
    }
    let total = wall.elapsed();
    let ns = |d: Duration| d.as_nanos() as f64;
    let rows = [
        ("setup", ph.setup),
        ("keys_of", ph.keys),
        ("prefetch", ph.prefetch),
        ("contains_key_loop", ph.probe),
        ("decompose_fast", ph.decompose),
        ("add_many_lazy", ph.advance),
        ("finish_lazy", ph.finish),
    ];
    let timed: f64 = rows.iter().map(|(_, d)| ns(*d)).sum();
    println!(
        "{{\"walks\":{walks},\"distance\":{distance},\"targets\":{n_targets},\"trials\":{},\"rounds\":{},\"admitted\":{},\"total_ns\":{},\"untimed_ns\":{},\"phases\":{{{}}}}}",
        ph.trials,
        ph.rounds,
        ph.probes_admitted,
        ns(total),
        ns(total) - timed,
        rows.iter()
            .map(|(n, d)| format!("\"{n}\":{{\"ns\":{},\"ns_per_trial\":{:.3},\"share\":{:.4}}}", ns(*d), ns(*d) / ph.trials as f64, ns(*d) / ns(total)))
            .collect::<Vec<_>>()
            .join(",")
    );
}
