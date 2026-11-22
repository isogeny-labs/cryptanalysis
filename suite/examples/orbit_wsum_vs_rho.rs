//! Cold single-target Aut-folded `wsum` vs matched `rho_baseline` on
//! Generic / J1728 / J0 prime curves at fp20 / fp24 / fp28.
//!
//! Emits JSON rows for the workspace rho-parity panel (PR #42). Group-op
//! ratio is `whole_process_ops / (rho_ops_total + rho_precompute_ops)`;
//! wall ratio is IC seconds / rho seconds. Exact `[d]G=Q` via
//! `DescentReport::verified` / `RhoReport::verified`.

use cryptanalysis_suite::cryptanalysis::ec_index_calculus_curves::CurveKind;
use cryptanalysis_suite::cryptanalysis::prime_orbit_index_calculus::{
    generate_instance, OrbitIcOptions, OrbitIcReport, ScaledShape,
};
use serde_json::json;
use std::time::Instant;

fn main() {
    let seeds: &[u64] = &[59297, 10007, 31415, 27182, 16180, 42069, 77777, 99991];
    let bits_list: &[u32] = &[20, 24, 28];
    let kinds = [CurveKind::Generic, CurveKind::J1728, CurveKind::J0];
    let mut rows = Vec::new();

    for &bits in bits_list {
        for &kind in &kinds {
            let mut ic_ops = Vec::new();
            let mut rho_ops = Vec::new();
            let mut ic_wall = Vec::new();
            let mut rho_wall = Vec::new();
            let mut verified = 0usize;
            let mut failed = 0usize;
            for &seed in seeds {
                let Ok(inst) = generate_instance(ScaledShape::of_kind(kind), bits, None, seed)
                else {
                    failed += 1;
                    continue;
                };
                let opts = OrbitIcOptions {
                    wsum_targets: 1,
                    learn: false,
                    ..OrbitIcOptions::wsum()
                };
                let t0 = Instant::now();
                let rep = run_cold(&inst.curve, inst.target, &opts, seed);
                let wall_ic = t0.elapsed().as_secs_f64();
                // Prefer internal phase timers when present.
                let ic_sec = rep.logs.seconds
                    + rep.descents.iter().map(|d| d.seconds).sum::<f64>();
                let rho_sec = rep.rhos.iter().map(|r| r.seconds).sum::<f64>();
                let ic_ok = rep.descents_verified() == 1
                    && rep.descents[0].recovered == Some(inst.known_log);
                let rho_ok = rep.rhos_verified() == 1
                    && rep.rhos[0].recovered == Some(inst.known_log);
                if !(ic_ok && rho_ok) {
                    failed += 1;
                    eprintln!(
                        "FAIL {kind:?} fp{bits} seed={seed} ic_ok={ic_ok} rho_ok={rho_ok} recovered={:?}",
                        rep.descents.first().and_then(|d| d.recovered)
                    );
                    continue;
                }
                verified += 1;
                let ic = rep.whole_process_ops() as f64;
                let rho = (rep.rho_ops_total() + rep.rho_precompute_ops) as f64;
                ic_ops.push(ic);
                rho_ops.push(rho);
                ic_wall.push(if ic_sec > 0.0 { ic_sec } else { wall_ic });
                rho_wall.push(rho_sec.max(1e-12));
                eprintln!(
                    "ok {kind:?} fp{bits} seed={seed} S={:.3} wall={:.3} B={} entries={} w={}",
                    ic / rho,
                    ic_wall.last().unwrap() / rho_wall.last().unwrap(),
                    rep.logs.wsum_bound,
                    rep.logs.wsum_entries,
                    rep.automorphism_order
                );
            }
            let s_ratios: Vec<f64> = ic_ops
                .iter()
                .zip(rho_ops.iter())
                .map(|(a, b)| a / b)
                .collect();
            let w_ratios: Vec<f64> = ic_wall
                .iter()
                .zip(rho_wall.iter())
                .map(|(a, b)| a / b)
                .collect();
            let row = json!({
                "method": "orbit-wsum",
                "curve_kind": format!("{kind:?}"),
                "bits": bits,
                "seeds": seeds.len(),
                "verified": verified,
                "failed": failed,
                "S_mean": mean(&s_ratios),
                "S_geo": geo_mean(&s_ratios),
                "S_min": s_ratios.iter().cloned().fold(f64::INFINITY, f64::min),
                "S_max": s_ratios.iter().cloned().fold(0.0_f64, f64::max),
                "wall_mean": mean(&w_ratios),
                "wall_geo": geo_mean(&w_ratios),
                "wall_min": w_ratios.iter().cloned().fold(f64::INFINITY, f64::min),
                "wall_max": w_ratios.iter().cloned().fold(0.0_f64, f64::max),
                "S_ok_all_le_1": s_ratios.iter().all(|r| *r <= 1.0),
                "wall_ok_all_le_1": w_ratios.iter().all(|r| *r <= 1.0),
            });
            println!("{}", serde_json::to_string(&row).unwrap());
            rows.push(row);
        }
    }
    println!("{}", serde_json::to_string_pretty(&json!({"panel": rows})).unwrap());
}

fn run_cold(
    c: &cryptanalysis_suite::cryptanalysis::prime_orbit_index_calculus::OrbitCurve,
    q: cryptanalysis_suite::cryptanalysis::bsgs_fast::FastPoint,
    opts: &OrbitIcOptions,
    seed: u64,
) -> OrbitIcReport {
    let opts = OrbitIcOptions { seed, ..*opts };
    cryptanalysis_suite::cryptanalysis::prime_orbit_index_calculus::run_known_answer(
        c,
        &[q],
        &opts,
    )
}

fn mean(xs: &[f64]) -> f64 {
    if xs.is_empty() {
        return f64::NAN;
    }
    xs.iter().sum::<f64>() / xs.len() as f64
}

fn geo_mean(xs: &[f64]) -> f64 {
    if xs.is_empty() {
        return f64::NAN;
    }
    let s: f64 = xs.iter().map(|x| x.ln()).sum();
    (s / xs.len() as f64).exp()
}
