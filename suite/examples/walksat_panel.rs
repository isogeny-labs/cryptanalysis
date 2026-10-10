//! WalkSAT vs CDCL on Koblitz decomposition systems: success rate and
//! wall time per cell, on planted targets (sums of `m` base points) and on
//! random multiples of the generator.
//!
//! ```bash
//! cargo run --release --example walksat_panel -- 1:11:2:0 0:13:2:0 0:9:3:0
//! ```
//!
//! Each argument is `a:n:m:fi` (Koblitz `a`, extension degree `n`,
//! summands `m`, factor-base index `fi`).  Optional env: `WALK_TARGETS`
//! (per kind, default 20), `WALK_FLIPS`, `WALK_TRIES`, `WALK_NOISE`
//! (per mille).  Engineering stage measurement: one machine, one thread
//! per target, default options unless overridden.

use std::time::Instant;

use cryptanalysis_suite::binary_ecc::BinaryPoint;
use cryptanalysis_suite::cryptanalysis::koblitz_groebner::FieldStructure;
use cryptanalysis_suite::cryptanalysis::koblitz_index_calculus::{
    build_frobenius_factor_base, sat_decompose_with, KoblitzCurve, SatDecompositionOptions,
};
use cryptanalysis_suite::cryptanalysis::walksat::{
    walksat_decompose, WalkEncoding, WalkSatDecompositionOptions,
};
use num_bigint::BigUint;

fn env_or<T: std::str::FromStr>(k: &str, d: T) -> T {
    std::env::var(k)
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(d)
}

fn main() {
    let count: u64 = env_or("WALK_TARGETS", 20);
    let mut walk = WalkSatDecompositionOptions::default();
    walk.walk.max_flips = env_or("WALK_FLIPS", walk.walk.max_flips);
    walk.walk.max_tries = env_or("WALK_TRIES", walk.walk.max_tries);
    walk.walk.noise_permille = env_or("WALK_NOISE", walk.walk.noise_permille);
    println!(
        "walk options: tries={} flips={} noise={}/1000 max_models={}",
        walk.walk.max_tries, walk.walk.max_flips, walk.walk.noise_permille, walk.max_models
    );
    println!("cell,kind,targets,cdcl_found,cdcl_ms,cdcl_conflicts,engine,walk_found,walk_ms,walk_flips,walk_models");
    for arg in std::env::args().skip(1) {
        let p: Vec<u64> = arg.split(':').map(|s| s.parse().unwrap()).collect();
        let (a, n, m, fi) = (p[0] as u8, p[1] as u32, p[2] as usize, p[3] as usize);
        let kc = KoblitzCurve::new(a, n).expect("curve");
        let fb = build_frobenius_factor_base(&kc, fi).expect("base");
        let index_of = fb.index_map();
        let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
        let mut s = 0x1234_5678u64 ^ (n as u64) << 8 ^ m as u64;
        let mut next = move || {
            s = s.wrapping_add(0x9e37_79b9_7f4a_7c15);
            let mut z = s;
            z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
            z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
            z ^ (z >> 31)
        };
        let planted: Vec<BinaryPoint> = (0..count)
            .map(|_| {
                (0..m).fold(BinaryPoint::Infinity, |acc, _| {
                    kc.add(&acc, &fb.points[(next() % fb.points.len() as u64) as usize])
                })
            })
            .filter(|t| *t != BinaryPoint::Infinity)
            .collect();
        let random: Vec<BinaryPoint> = (0..count)
            .map(|_| kc.mul(kc.generator(), &BigUint::from(1 + next() % 1_000_003)))
            .filter(|t| *t != BinaryPoint::Infinity)
            .collect();
        for (kind, ts) in [("planted", &planted), ("random", &random)] {
            let t0 = Instant::now();
            let mut cdcl_found = 0;
            let mut conflicts = 0;
            for t in ts.iter() {
                let (r, st_) = sat_decompose_with(
                    &kc,
                    &fb,
                    &index_of,
                    &st,
                    t,
                    m,
                    4096,
                    None,
                    SatDecompositionOptions::default(),
                );
                cdcl_found += usize::from(r.is_some());
                conflicts += st_.conflicts;
            }
            let cdcl_ms = t0.elapsed().as_secs_f64() * 1e3;
            for encoding in [WalkEncoding::Anf, WalkEncoding::CnfXor] {
                let o = WalkSatDecompositionOptions { encoding, ..walk };
                let t0 = Instant::now();
                let (mut found, mut flips, mut models) = (0, 0, 0);
                for t in ts.iter() {
                    let (r, ws) = walksat_decompose(&kc, &fb, &index_of, &st, t, m, &o);
                    assert_eq!(ws.spurious, 0);
                    found += usize::from(r.is_some());
                    flips += ws.walk.flips;
                    models += ws.models;
                }
                let ms = t0.elapsed().as_secs_f64() * 1e3;
                println!(
                    "K{a}/2^{n}/m{m}/fi{fi}/l{}/F{},{kind},{},{cdcl_found},{cdcl_ms:.1},{conflicts},{encoding:?},{found},{ms:.1},{flips},{models}",
                    fb.subspace_basis.len(),
                    fb.points.len(),
                    ts.len()
                );
            }
        }
    }
}
