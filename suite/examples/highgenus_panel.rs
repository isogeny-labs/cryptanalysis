//! Functional panel for the higher-genus engines: Pollard rho and index
//! calculus on planted instances at requested genera, hyperelliptic and
//! non-hyperelliptic, with every logarithm verified.
//!
//! ```sh
//! cargo run --release --example highgenus_panel -- rho --genera 5,7,11 --nbits 16,24
//! cargo run --release --example highgenus_panel -- ic-known --genera 5,11 --bound 1
//! cargo run --release --example highgenus_panel -- ic-order --genera 23 --p 3 --bound 5
//! ```
//!
//! Output: one JSON line per row on stdout (`highgenus.panel/v1`), a
//! markdown table on stderr. Counts are group operations from the engines'
//! own counters; wall times are for orientation only. No speed claim.

use std::time::Instant;

use clap::{Parser, Subcommand};
use num_traits::ToPrimitive;
use rand::rngs::StdRng;
use rand::{RngCore, SeedableRng};

use cryptanalysis_suite::highgenus::cantor::HyperellipticCurve;
use cryptanalysis_suite::highgenus::fp::Fp;
use cryptanalysis_suite::highgenus::ic::{
    build_factor_base, index_calculus_dlp, index_calculus_group_order, largest_prime_factor,
    IcParams, IndexCalculusCurve,
};
use cryptanalysis_suite::highgenus::instances::{
    hyperelliptic_instance, superelliptic_power_instance, three_point_instance, Instance,
};
use cryptanalysis_suite::highgenus::kummer::SuperellipticCurve;
use cryptanalysis_suite::highgenus::rho::{pollard_rho, RhoParams};
use cryptanalysis_suite::highgenus::JacobianGroup;

#[derive(Parser)]
#[command(name = "highgenus_panel")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Pollard rho on Jacobi-sum instances with a known prime subgroup.
    Rho {
        #[arg(long, value_delimiter = ',')]
        genera: Vec<u32>,
        /// Subgroup order bit range lo,hi.
        #[arg(long, value_delimiter = ',', default_value = "16,24")]
        nbits: Vec<u32>,
        /// hyper | power | three | all
        #[arg(long, default_value = "all")]
        family: String,
        #[arg(long, default_value_t = 3)]
        min_p: u64,
        #[arg(long, default_value_t = 1)]
        seed: u64,
    },
    /// Index calculus in a known prime-order subgroup of a Jacobi-sum curve.
    IcKnown {
        #[arg(long, value_delimiter = ',')]
        genera: Vec<u32>,
        #[arg(long, value_delimiter = ',', default_value = "16,40")]
        nbits: Vec<u32>,
        #[arg(long, default_value_t = 1)]
        bound: usize,
        #[arg(long, default_value = "all")]
        family: String,
        #[arg(long, default_value_t = 3)]
        min_p: u64,
        #[arg(long, default_value_t = 1)]
        seed: u64,
    },
    /// Relation-rate probe: build the factor base and run the relation
    /// walk for a bounded number of trials, reporting the smoothness rate
    /// and cost per trial (no solve).
    Probe {
        #[arg(long, value_delimiter = ',')]
        genera: Vec<u32>,
        #[arg(long)]
        p: u64,
        #[arg(long)]
        bound: usize,
        /// hyper | trigonal | all
        #[arg(long, default_value = "all")]
        family: String,
        #[arg(long, default_value_t = 1)]
        seed: u64,
        #[arg(long, default_value_t = 200_000)]
        max_trials: u64,
    },
    /// Index calculus on a random curve over a small field: group order
    /// from the relation lattice, then a DLP in the largest prime subgroup.
    IcOrder {
        #[arg(long, value_delimiter = ',')]
        genera: Vec<u32>,
        #[arg(long)]
        p: u64,
        #[arg(long)]
        bound: usize,
        /// hyper | trigonal | all
        #[arg(long, default_value = "all")]
        family: String,
        #[arg(long, default_value_t = 1)]
        seed: u64,
        #[arg(long, default_value_t = 50_000_000)]
        max_trials: u64,
    },
}

fn md_row(cols: &[String]) {
    eprintln!("| {} |", cols.join(" | "));
}

fn emit(json: serde_json::Value, cols: &[String]) {
    println!("{json}");
    md_row(cols);
}

fn run_rho<G: JacobianGroup>(label: &str, model: &str, inst: &Instance<G>, seed: u64) {
    let t0 = Instant::now();
    // The ideal engine pays a full reduction for a negation, so the
    // negation map buys nothing there; fewer branches keep the setup cheap.
    let params = if model == "kummer" {
        RhoParams {
            seed,
            branches: 8,
            negation_map: false,
            ..Default::default()
        }
    } else {
        RhoParams {
            seed,
            ..Default::default()
        }
    };
    let res = pollard_rho(&inst.group, &inst.d1, &inst.d2, &inst.n, &params);
    let wall = t0.elapsed().as_secs_f64();
    match res {
        Ok(r) => {
            let verified = r.k == inst.k;
            let json = serde_json::json!({
                "schema": "highgenus.panel/v1", "task": "rho", "model": model, "label": label,
                "genus": inst.genus, "p": inst.p, "curve": inst.description,
                "jacobian_order_bits": inst.jacobian_order.bits(), "n_bits": inst.n.bits(), "n": inst.n.to_string(),
                "k": r.k.to_string(), "planted_k": inst.k.to_string(), "verified": verified,
                "walk_ops": r.walk_ops, "setup_ops": r.setup_ops, "s_walk": r.s_walk, "dps": r.distinguished_points,
                "walks": r.walks, "wall_s": wall, "pcc": "unverified"
            });
            emit(
                json,
                &[
                    label.into(),
                    model.into(),
                    inst.genus.to_string(),
                    inst.p.to_string(),
                    inst.jacobian_order.bits().to_string(),
                    inst.n.bits().to_string(),
                    r.walk_ops.to_string(),
                    format!("{:.2}", r.s_walk),
                    format!("{wall:.1}"),
                    verified.to_string(),
                ],
            );
        }
        Err(e) => {
            let json = serde_json::json!({"schema": "highgenus.panel/v1", "task": "rho", "model": model, "label": label, "genus": inst.genus, "p": inst.p, "curve": inst.description, "error": e.to_string(), "wall_s": wall});
            emit(
                json,
                &[
                    label.into(),
                    model.into(),
                    inst.genus.to_string(),
                    inst.p.to_string(),
                    "-".into(),
                    inst.n.bits().to_string(),
                    "-".into(),
                    "-".into(),
                    format!("{wall:.1}"),
                    format!("error: {e}"),
                ],
            );
        }
    }
}

fn power_params_for_genus(g: u32) -> Option<(u32, u32)> {
    // Smallest m ≥ 3 with (m−1)(n−1) = 2g, gcd(m,n) = 1, n ≥ 2.
    for m in 3..=(2 * g + 1) {
        if !(2 * g).is_multiple_of(m - 1) {
            continue;
        }
        let n = 2 * g / (m - 1) + 1;
        if n >= 2 && gcd(m, n) == 1 {
            return Some((m, n));
        }
    }
    None
}

fn gcd(mut a: u32, mut b: u32) -> u32 {
    while b != 0 {
        let t = a % b;
        a = b;
        b = t;
    }
    a
}

fn run_ic_known<C: IndexCalculusCurve>(
    label: &str,
    model: &str,
    inst: &Instance<C>,
    bound: usize,
    seed: u64,
) {
    let mut rng = StdRng::seed_from_u64(seed);
    let t0 = Instant::now();
    let fb = match build_factor_base(&inst.group, bound, &mut rng) {
        Ok(fb) => fb,
        Err(e) => {
            emit(
                serde_json::json!({"schema": "highgenus.panel/v1", "task": "ic-known", "model": model, "label": label, "genus": inst.genus, "p": inst.p, "error": e.to_string()}),
                &[
                    label.into(),
                    model.into(),
                    inst.genus.to_string(),
                    inst.p.to_string(),
                    bound.to_string(),
                    "-".into(),
                    "-".into(),
                    "-".into(),
                    "-".into(),
                    "-".into(),
                    format!("error: {e}"),
                ],
            );
            return;
        }
    };
    let fb_wall = t0.elapsed().as_secs_f64();
    let params = IcParams {
        seed,
        ..Default::default()
    };
    let t1 = Instant::now();
    let res = index_calculus_dlp(&inst.group, &fb, &inst.d1, &inst.d2, &inst.n, &params);
    let wall = t1.elapsed().as_secs_f64();
    match res {
        Ok(r) => {
            let verified = r.k == inst.k;
            emit(
                serde_json::json!({
                    "schema": "highgenus.panel/v1", "task": "ic-known", "model": model, "label": label, "genus": inst.genus, "p": inst.p,
                    "curve": inst.description, "n_bits": inst.n.bits(), "n": inst.n.to_string(), "bound": bound, "fb_size": fb.len(), "fb_wall_s": fb_wall,
                    "relations": r.relations, "trials": r.stats.trials, "smooth_rate": r.stats.smooth_rate(), "walk_ops": r.stats.walk_ops, "setup_ops": r.stats.setup_ops,
                    "la_ms": r.la_ms, "la_dim": r.la_dim, "k": r.k.to_string(), "verified": verified, "wall_s": wall, "pcc": "unverified"
                }),
                &[
                    label.into(),
                    model.into(),
                    inst.genus.to_string(),
                    inst.p.to_string(),
                    bound.to_string(),
                    fb.len().to_string(),
                    r.stats.trials.to_string(),
                    format!("{:.2e}", r.stats.smooth_rate()),
                    r.stats.walk_ops.to_string(),
                    format!("{wall:.1}"),
                    verified.to_string(),
                ],
            );
        }
        Err(e) => emit(
            serde_json::json!({"schema": "highgenus.panel/v1", "task": "ic-known", "model": model, "label": label, "genus": inst.genus, "p": inst.p, "bound": bound, "fb_size": fb.len(), "error": e.to_string(), "wall_s": wall}),
            &[
                label.into(),
                model.into(),
                inst.genus.to_string(),
                inst.p.to_string(),
                bound.to_string(),
                fb.len().to_string(),
                "-".into(),
                "-".into(),
                "-".into(),
                format!("{wall:.1}"),
                format!("error: {e}"),
            ],
        ),
    }
}

fn run_ic_order<C: IndexCalculusCurve>(
    label: &str,
    model: &str,
    curve: &C,
    desc: &str,
    bound: usize,
    seed: u64,
    max_trials: u64,
) {
    let mut rng = StdRng::seed_from_u64(seed);
    let p = curve.field().p();
    let g = curve.genus();
    let t0 = Instant::now();
    let fb = match build_factor_base(curve, bound, &mut rng) {
        Ok(fb) => fb,
        Err(e) => {
            emit(
                serde_json::json!({"schema": "highgenus.panel/v1", "task": "ic-order", "model": model, "label": label, "genus": g, "p": p, "error": e.to_string()}),
                &[
                    label.into(),
                    model.into(),
                    g.to_string(),
                    p.to_string(),
                    bound.to_string(),
                    "-".into(),
                    "-".into(),
                    "-".into(),
                    "-".into(),
                    "-".into(),
                    "-".into(),
                    format!("error: {e}"),
                ],
            );
            return;
        }
    };
    let fb_wall = t0.elapsed().as_secs_f64();
    let params = IcParams {
        seed,
        max_trials,
        ..Default::default()
    };
    let t1 = Instant::now();
    let order = index_calculus_group_order(curve, &fb, &params);
    let order_wall = t1.elapsed().as_secs_f64();
    let rep = match order {
        Ok(r) => r,
        Err(e) => {
            emit(
                serde_json::json!({"schema": "highgenus.panel/v1", "task": "ic-order", "model": model, "label": label, "genus": g, "p": p, "bound": bound, "fb_size": fb.len(), "error": e.to_string(), "wall_s": order_wall}),
                &[
                    label.into(),
                    model.into(),
                    g.to_string(),
                    p.to_string(),
                    bound.to_string(),
                    fb.len().to_string(),
                    "-".into(),
                    "-".into(),
                    "-".into(),
                    "-".into(),
                    format!("{order_wall:.1}"),
                    format!("error: {e}"),
                ],
            );
            return;
        }
    };
    // DLP in the largest prime subgroup (N < 2^63 required by the solver).
    let mut dlp_json = serde_json::json!({});
    let mut dlp_col = "-".to_string();
    if let Some((n, cof)) = largest_prime_factor(&rep.order, 4_000_000) {
        if n.bits() <= 62 && n.to_u64().map(|v| v > 3).unwrap_or(false) {
            let mut d1 = curve.identity();
            let mut tries = 0;
            while curve.is_identity(&d1) && tries < 32 {
                tries += 1;
                let r = &fb.places[(rng.next_u64() as usize) % fb.len()].elem;
                d1 = curve.scalar_mul(&cof, r);
            }
            if !curve.is_identity(&d1) {
                let k = cryptanalysis_suite::highgenus::rho::random_below(&mut rng, &n);
                let d2 = curve.scalar_mul(&k, &d1);
                let t2 = Instant::now();
                match index_calculus_dlp(curve, &fb, &d1, &d2, &n, &params) {
                    Ok(r) => {
                        let verified = r.k == k;
                        dlp_json = serde_json::json!({"n_bits": n.bits(), "n": n.to_string(), "dlp_trials": r.stats.trials, "dlp_walk_ops": r.stats.walk_ops, "dlp_la_ms": r.la_ms, "dlp_verified": verified, "dlp_wall_s": t2.elapsed().as_secs_f64()});
                        dlp_col = format!(
                            "N {} bits: {}",
                            n.bits(),
                            if verified { "verified" } else { "WRONG" }
                        );
                    }
                    Err(e) => {
                        dlp_json =
                            serde_json::json!({"n_bits": n.bits(), "dlp_error": e.to_string()});
                        dlp_col = format!("N {} bits: error {e}", n.bits());
                    }
                }
            }
        } else {
            dlp_col = format!("N {} bits (solver needs < 2^62)", n.bits());
        }
    } else {
        dlp_col = "order not fully factored".into();
    }
    let mut json = serde_json::json!({
        "schema": "highgenus.panel/v1", "task": "ic-order", "model": model, "label": label, "genus": g, "p": p, "curve": desc,
        "bound": bound, "fb_size": fb.len(), "fb_wall_s": fb_wall, "relations": rep.relations, "trials": rep.stats.trials,
        "smooth_rate": rep.stats.smooth_rate(), "walk_ops": rep.stats.walk_ops, "la_ms": rep.la_ms,
        "order": rep.order.to_string(), "order_bits": rep.order.bits(), "annihilates_random": rep.annihilates_random,
        "within_hasse_weil": rep.within_hasse_weil, "order_wall_s": order_wall, "pcc": "unverified"
    });
    if let (Some(a), Some(b)) = (json.as_object_mut(), dlp_json.as_object()) {
        for (k, v) in b {
            a.insert(k.clone(), v.clone());
        }
    }
    emit(
        json,
        &[
            label.into(),
            model.into(),
            g.to_string(),
            p.to_string(),
            bound.to_string(),
            fb.len().to_string(),
            rep.stats.trials.to_string(),
            format!("{:.2e}", rep.stats.smooth_rate()),
            rep.stats.walk_ops.to_string(),
            format!(
                "{} bits, HW {}, h·R=0 {}",
                rep.order.bits(),
                rep.within_hasse_weil,
                rep.annihilates_random
            ),
            format!("{order_wall:.1}"),
            dlp_col,
        ],
    );
}

fn run_probe<C: IndexCalculusCurve>(
    label: &str,
    model: &str,
    curve: &C,
    desc: &str,
    bound: usize,
    seed: u64,
    max_trials: u64,
) {
    use cryptanalysis_suite::highgenus::ic::collect_relations;
    let mut rng = StdRng::seed_from_u64(seed);
    let p = curve.field().p();
    let g = curve.genus();
    let t0 = Instant::now();
    let fb = match build_factor_base(curve, bound, &mut rng) {
        Ok(fb) => fb,
        Err(e) => {
            emit(
                serde_json::json!({"schema": "highgenus.panel/v1", "task": "probe", "model": model, "label": label, "genus": g, "p": p, "error": e.to_string()}),
                &[
                    label.into(),
                    model.into(),
                    g.to_string(),
                    p.to_string(),
                    bound.to_string(),
                    "-".into(),
                    "-".into(),
                    "-".into(),
                    "-".into(),
                    "-".into(),
                    format!("error: {e}"),
                ],
            );
            return;
        }
    };
    let fb_wall = t0.elapsed().as_secs_f64();
    let params = IcParams {
        seed,
        max_trials,
        ..Default::default()
    };
    let t1 = Instant::now();
    let (rels, stats) = collect_relations(curve, &fb, None, fb.len() + 16, &params, &mut rng)
        .expect("factor base non-empty");
    let wall = t1.elapsed().as_secs_f64();
    let per_trial_ms = if stats.trials > 0 {
        1000.0 * wall / stats.trials as f64
    } else {
        0.0
    };
    emit(
        serde_json::json!({
            "schema": "highgenus.panel/v1", "task": "probe", "model": model, "label": label, "genus": g, "p": p, "curve": desc,
            "bound": bound, "fb_size": fb.len(), "fb_wall_s": fb_wall, "trials": stats.trials, "smooth": stats.smooth, "relations": rels.len(),
            "needed": fb.len() + 16, "smooth_rate": stats.smooth_rate(), "walk_ops": stats.walk_ops, "ms_per_trial": per_trial_ms,
            "exhausted": stats.exhausted, "wall_s": wall, "pcc": "unverified"
        }),
        &[
            label.into(),
            model.into(),
            g.to_string(),
            p.to_string(),
            bound.to_string(),
            fb.len().to_string(),
            stats.trials.to_string(),
            format!("{:.2e}", stats.smooth_rate()),
            format!("{}/{}", rels.len(), fb.len() + 16),
            format!("{per_trial_ms:.3}"),
            format!("{wall:.1}"),
        ],
    );
}

fn main() {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::Probe {
            genera,
            p,
            bound,
            family,
            seed,
            max_trials,
        } => {
            md_row(
                &[
                    "label",
                    "model",
                    "g",
                    "p",
                    "B",
                    "|FB|",
                    "trials",
                    "smooth rate",
                    "relations/needed",
                    "ms/trial",
                    "wall s",
                ]
                .map(String::from),
            );
            md_row(&["---"; 11].map(String::from));
            let field = Fp::new(p).expect("prime");
            for g in genera {
                let mut rng = StdRng::seed_from_u64(seed ^ (g as u64) << 8);
                if (family == "hyper" || family == "all") && field.is_odd() {
                    let c = HyperellipticCurve::random(field, g, &mut rng).expect("curve");
                    let desc = format!("y² = {}", c.f);
                    run_probe(
                        "hyperelliptic random",
                        "cantor",
                        &c,
                        &desc,
                        bound,
                        seed,
                        max_trials,
                    );
                }
                if (family == "trigonal" || family == "all") && p != 3 {
                    let c = SuperellipticCurve::random_trigonal(field, g, &mut rng).expect("curve");
                    let desc = format!(
                        "y³ = {} · ({})²",
                        c.factors[0].0,
                        c.factors
                            .get(1)
                            .map(|f| f.0.to_string())
                            .unwrap_or_default()
                    );
                    run_probe(
                        "non-hyperelliptic trigonal random",
                        "kummer",
                        &c,
                        &desc,
                        bound,
                        seed,
                        max_trials,
                    );
                }
            }
        }
        Cmd::Rho {
            genera,
            nbits,
            family,
            min_p,
            seed,
        } => {
            let nb = (nbits[0], nbits[1]);
            md_row(
                &[
                    "label",
                    "model",
                    "g",
                    "p",
                    "#Jac bits",
                    "N bits",
                    "walk ops",
                    "S_walk",
                    "wall s",
                    "verified",
                ]
                .map(String::from),
            );
            md_row(&["---"; 10].map(String::from));
            for g in genera {
                if family == "hyper" || family == "all" {
                    match hyperelliptic_instance(g, min_p, nb, seed) {
                        Ok(inst) => run_rho("hyperelliptic y²=x^{2g+1}+a", "cantor", &inst, seed),
                        Err(e) => {
                            eprintln!("| hyperelliptic | cantor | {g} | - | instance error: {e} |")
                        }
                    }
                }
                if family == "power" || family == "all" {
                    if let Some((m, n)) = power_params_for_genus(g) {
                        match superelliptic_power_instance(m, n, min_p, nb, seed) {
                            Ok(inst) => run_rho(&format!("non-hyperelliptic y^{m}=x^{n}+a"), "kummer", &inst, seed),
                            Err(e) => eprintln!("| non-hyperelliptic power | kummer | {g} | - | instance error: {e} |"),
                        }
                    } else if family == "power" {
                        eprintln!("| non-hyperelliptic power | kummer | {g} | - | no (m,n) with (m−1)(n−1)=2g, gcd(m,n)=1, m≥3 |");
                    }
                }
                if family == "three" || (family == "all" && power_params_for_genus(g).is_none()) {
                    match three_point_instance(g, min_p, nb, seed) {
                        Ok(inst) => run_rho("non-hyperelliptic y^{2g+1}=x(1−x)^b", "kummer", &inst, seed),
                        Err(e) => eprintln!("| non-hyperelliptic three-point | kummer | {g} | - | instance error: {e} |"),
                    }
                }
            }
        }
        Cmd::IcKnown {
            genera,
            nbits,
            bound,
            family,
            min_p,
            seed,
        } => {
            let nb = (nbits[0], nbits[1]);
            md_row(
                &[
                    "label",
                    "model",
                    "g",
                    "p",
                    "B",
                    "|FB|",
                    "trials",
                    "smooth rate",
                    "walk ops",
                    "wall s",
                    "verified",
                ]
                .map(String::from),
            );
            md_row(&["---"; 11].map(String::from));
            for g in genera {
                if family == "hyper" || family == "all" {
                    match hyperelliptic_instance(g, min_p, nb, seed) {
                        Ok(inst) => run_ic_known(
                            "hyperelliptic y²=x^{2g+1}+a",
                            "cantor",
                            &inst,
                            bound,
                            seed,
                        ),
                        Err(e) => {
                            eprintln!("| hyperelliptic | cantor | {g} | instance error: {e} |")
                        }
                    }
                }
                if family == "power" || family == "all" {
                    if let Some((m, n)) = power_params_for_genus(g) {
                        match superelliptic_power_instance(m, n, min_p, nb, seed) {
                            Ok(inst) => run_ic_known(
                                &format!("non-hyperelliptic y^{m}=x^{n}+a"),
                                "kummer",
                                &inst,
                                bound,
                                seed,
                            ),
                            Err(e) => eprintln!(
                                "| non-hyperelliptic power | kummer | {g} | instance error: {e} |"
                            ),
                        }
                    }
                }
            }
        }
        Cmd::IcOrder {
            genera,
            p,
            bound,
            family,
            seed,
            max_trials,
        } => {
            md_row(
                &[
                    "label",
                    "model",
                    "g",
                    "p",
                    "B",
                    "|FB|",
                    "trials",
                    "smooth rate",
                    "walk ops",
                    "order",
                    "wall s",
                    "dlp",
                ]
                .map(String::from),
            );
            md_row(&["---"; 12].map(String::from));
            let field = Fp::new(p).expect("prime");
            for g in genera {
                let mut rng = StdRng::seed_from_u64(seed ^ (g as u64) << 8);
                if (family == "hyper" || family == "all") && field.is_odd() {
                    let c = HyperellipticCurve::random(field, g, &mut rng).expect("curve");
                    let desc = format!("y² = {}", c.f);
                    run_ic_order(
                        "hyperelliptic random",
                        "cantor",
                        &c,
                        &desc,
                        bound,
                        seed,
                        max_trials,
                    );
                }
                if (family == "trigonal" || family == "all") && p != 3 {
                    let c = SuperellipticCurve::random_trigonal(field, g, &mut rng).expect("curve");
                    let desc = format!(
                        "y³ = {} · ({})²",
                        c.factors[0].0,
                        c.factors
                            .get(1)
                            .map(|f| f.0.to_string())
                            .unwrap_or_default()
                    );
                    run_ic_order(
                        "non-hyperelliptic trigonal random",
                        "kummer",
                        &c,
                        &desc,
                        bound,
                        seed,
                        max_trials,
                    );
                }
            }
        }
    }
}
