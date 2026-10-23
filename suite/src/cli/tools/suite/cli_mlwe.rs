//! `ca-suite mlwe …` — the command-line surface for
//! [`crate::cryptanalysis::mlwe`] and the ML-KEM / ML-DSA
//! implementation attacks.
//!
//! Every estimator, sieve and attack in those modules is reachable from here.
//! Nothing prints a cost without also printing the model it was computed in.

use crate::cryptanalysis::ml_dsa_fault;
use crate::cryptanalysis::ml_dsa_leakage;
use crate::cryptanalysis::ml_kem_pco;
use crate::cryptanalysis::mlwe::cost::{BkzModel, Reps, SvpModel};
use crate::cryptanalysis::mlwe::dual::{dual_distinguish, dual_matzov, dual_matzov_consistent};
use crate::cryptanalysis::mlwe::hybrid::{best_hybrid, hybrid_dual};
use crate::cryptanalysis::mlwe::params::{all_lwe, all_sis, lwe_by_name, ml_dsa_by_name};
use crate::cryptanalysis::mlwe::primal::{
    primal_usvp_2016, primal_usvp_simulated, sis_estimate, sis_required_beta,
};
use crate::cryptanalysis::mlwe::report::{
    best_believable, full_report, margin_table, render_table, report_search,
};
use crate::cryptanalysis::mlwe::sieve::{
    bucketed_sieve, bucketed_sieve_resume, gauss_sieve, gauss_sieve_resume, measure_gauss_scaling,
    norm2, nv_sieve, nv_sieve_resume, progressive_bkz, progressive_bkz_resume, random_qary_lattice,
    BkzCheckpoint, BucketedCheckpoint, GaussCheckpoint, NvCheckpoint, SieveConfig,
};
use clap::Subcommand;

#[derive(Subcommand)]
pub enum MlweOp {
    /// Estimate every attack against one parameter set.
    ///
    /// `--scheme` accepts `ml-kem-512/768/1024` and `ml-dsa-44/65/87`.
    Estimate {
        #[arg(long, default_value = "ml-kem-768")]
        scheme: String,
        /// SVP cost model: `core-svp-classical`, `core-svp-quantum`,
        /// `gate-count`, `sieve-memory`, `enumeration`.
        #[arg(long, default_value = "core-svp-classical")]
        model: String,
        /// Charge for BKZ tours rather than a single SVP call.
        #[arg(long, default_value_t = false)]
        tours: bool,
        /// Subtract Ducas' dimensions for free.
        #[arg(long, default_value_t = false)]
        d4f: bool,
        /// Also run the BKZ simulator alongside the closed-form condition.
        #[arg(long, default_value_t = false)]
        simulate: bool,
    },
    /// The whole table: every parameter set, every attack, every model.
    Table {
        /// Restrict to one model; omit for all of them.
        #[arg(long)]
        model: Option<String>,
    },
    /// Cheapest believable attack against each NIST category floor.
    Margins,
    /// The ML-DSA forgery (MSIS) side, on its own.
    Sis,
    /// Run a sieve on a random q-ary lattice and report what it found.
    Sieve {
        /// `gauss`, `nv`, or `bucketed`.
        #[arg(long, default_value = "gauss")]
        algo: String,
        #[arg(long, default_value_t = 20)]
        dim: usize,
        #[arg(long, default_value_t = 4099)]
        q: i64,
        #[arg(long, default_value_t = 0)]
        seed: u64,
        /// Starting list size, for `nv` and `bucketed`.
        #[arg(long, default_value_t = 600)]
        list: usize,
        /// Bucket count, for `bucketed`.
        #[arg(long, default_value_t = 32)]
        buckets: usize,
        /// Print completed checkpoints and elapsed-work heartbeats.
        #[arg(long)]
        verbose: bool,
        /// Seconds between heartbeats (implies --verbose).
        #[arg(long, value_parser = clap::value_parser!(u64).range(1..))]
        progress_every: Option<u64>,
        /// Persist live sieve state and final report here.
        #[arg(long)]
        state_dir: Option<std::path::PathBuf>,
        /// Continue local state or restore S3 state into a fresh directory.
        #[arg(long)]
        resume: bool,
        /// Mirror checkpoints and final report to S3.
        #[arg(long)]
        s3_uri: Option<String>,
    },
    /// Measure how the Gauss sieve's list grows with dimension.
    Scaling {
        /// Comma-separated dimensions.
        #[arg(long, default_value = "10,12,14,16,18")]
        dims: String,
        #[arg(long, default_value_t = 4099)]
        q: i64,
        /// Print completed dimensions and elapsed-work heartbeats.
        #[arg(long)]
        verbose: bool,
        /// Seconds between heartbeats (implies --verbose).
        #[arg(long, value_parser = clap::value_parser!(u64).range(1..))]
        progress_every: Option<u64>,
        /// Persist each completed dimension and final report here.
        #[arg(long)]
        state_dir: Option<std::path::PathBuf>,
        /// Continue local state or restore S3 state into a fresh directory.
        #[arg(long)]
        resume: bool,
        /// Mirror dimension results and final report to S3.
        #[arg(long)]
        s3_uri: Option<String>,
    },
    /// Run progressive BKZ on a random q-ary lattice and print the profile.
    Bkz {
        #[arg(long, default_value_t = 24)]
        dim: usize,
        #[arg(long, default_value_t = 12)]
        beta: usize,
        #[arg(long, default_value_t = 4099)]
        q: i64,
        #[arg(long, default_value_t = 5)]
        seed: u64,
        /// Print completed block sizes and elapsed-work heartbeats.
        #[arg(long)]
        verbose: bool,
        /// Seconds between heartbeats (implies --verbose).
        #[arg(long, value_parser = clap::value_parser!(u64).range(1..))]
        progress_every: Option<u64>,
        /// Persist the exact integer basis after each complete stage.
        #[arg(long)]
        state_dir: Option<std::path::PathBuf>,
        /// Continue local state or restore S3 state into a fresh directory.
        #[arg(long)]
        resume: bool,
        /// Mirror stage bases and the final report to S3.
        #[arg(long)]
        s3_uri: Option<String>,
    },
    /// Chosen-ciphertext key recovery against ML-KEM from decapsulation
    /// leakage.
    KemPco {
        /// `512`, `768` or `1024`.
        #[arg(long, default_value = "512")]
        param: String,
        /// `full` (message-decoding leakage) or `pc` (one-bit
        /// plaintext-checking oracle).
        #[arg(long, default_value = "full")]
        oracle: String,
        #[arg(long, default_value_t = 1)]
        seed: u8,
    },
    /// ML-DSA key recovery from whole-coefficient leakage of the mask, then
    /// forgery.
    DsaLeak {
        /// Coefficients of each polynomial of `y` that leak per signature.
        #[arg(long, default_value_t = 64)]
        per_poly: usize,
        #[arg(long, default_value_t = 1)]
        seed: u64,
    },
    /// ML-DSA key recovery from partial-bit leakage, by lattice, at reduced
    /// dimension.
    DsaPartial {
        #[arg(long, default_value_t = 8)]
        n: usize,
        #[arg(long, default_value_t = 22)]
        m: usize,
        #[arg(long, default_value_t = 12)]
        bits: usize,
        #[arg(long, default_value_t = 3)]
        seed: u64,
    },
    /// Fault attacks on ML-DSA's rejection loop.
    DsaFault {
        /// `all`, `zero`, `reuse` or `partial`.
        #[arg(long, default_value = "all")]
        fault: String,
        #[arg(long, default_value_t = 1)]
        seed: u64,
    },
    /// How much mask leakage each ML-DSA parameter set can survive.
    Budget,
}

fn build_model(name: &str, tours: bool, d4f: bool) -> BkzModel {
    let svp = SvpModel::parse(name).unwrap_or_else(|| {
        eprintln!(
            "unknown model `{name}`; try one of: {}",
            SvpModel::all()
                .iter()
                .map(|m| m.label())
                .collect::<Vec<_>>()
                .join(", ")
        );
        std::process::exit(2);
    });
    BkzModel {
        svp,
        reps: if tours {
            Reps::Tours(8)
        } else {
            Reps::CoreSvpOnly
        },
        d4f,
    }
}

pub fn run(op: MlweOp) {
    match op {
        MlweOp::Estimate {
            scheme,
            model,
            tours,
            d4f,
            simulate,
        } => {
            let Some(inst) = lwe_by_name(&scheme) else {
                eprintln!(
                    "unknown scheme `{scheme}`; try one of: {}",
                    all_lwe()
                        .iter()
                        .map(|i| i.name.clone())
                        .collect::<Vec<_>>()
                        .join(", ")
                );
                std::process::exit(2);
            };
            let m = build_model(&model, tours, d4f);
            println!("{}", inst.name);
            println!(
                "  n = {}, m = {}, q = {}, sigma = {:.4}, secret entropy = {:.0} bits",
                inst.n,
                inst.m,
                inst.q,
                inst.sigma_s,
                inst.secret_entropy()
            );
            println!("  cost model: {}\n", m.label());

            if let Some(e) = primal_usvp_2016(&inst, &m) {
                println!(
                    "  primal-usvp        beta = {:>4.0}  d = {:>4}  log2 cost = {:>7.1}  log2 mem = {:>6.1}",
                    e.beta, e.d, e.log2_cost, e.log2_memory
                );
            }
            if simulate {
                if let Some(e) = primal_usvp_simulated(&inst, &m, 8) {
                    println!(
                        "  primal (simulated) beta = {:>4.0}  d = {:>4}  log2 cost = {:>7.1}  log2 mem = {:>6.1}",
                        e.beta, e.d, e.log2_cost, e.log2_memory
                    );
                }
            }
            if let Some(e) = best_hybrid(&inst, &m, 512) {
                println!(
                    "  {:<18} beta = {:>4.0}  guessed = {:>3}  log2 cost = {:>7.1}",
                    e.method, e.beta, e.guessed, e.log2_cost
                );
            }
            let search = report_search();
            if let Some(e) = dual_distinguish(&inst, &m, &search) {
                println!(
                    "  dual-distinguish   beta = {:>4.0}  d = {:>4}  log2 cost = {:>7.1}  eps = 2^{:.1}",
                    e.beta, e.d, e.log2_cost, e.log2_advantage
                );
                println!("      {}", e.diagnostics.verdict());
            }
            if let Some(e) = dual_matzov(&inst, &m, &search) {
                println!(
                    "  dual-matzov        beta = {:>4.0}  split {}/{}/{}  p = {:>6}  log2 cost = {:>7.1}",
                    e.beta, e.k_lat, e.k_fft, e.k_enum, e.p, e.log2_cost
                );
                println!("      {}", e.diagnostics.verdict());
            }
            if let Some(e) = dual_matzov_consistent(&inst, &m, &search) {
                println!(
                    "  dual-matzov (ok)   beta = {:>4.0}  split {}/{}/{}  p = {:>6}  log2 cost = {:>7.1}",
                    e.beta, e.k_lat, e.k_fft, e.k_enum, e.p, e.log2_cost
                );
            }
            if let Some((free, consistent)) = hybrid_dual(&inst, &m, &search) {
                println!(
                    "  hybrid-dual        free = {:>7.1}   consistent = {:>7.1}",
                    free.log2_cost, consistent.log2_cost
                );
            }
            if let Some(b) = best_believable(&inst, &m) {
                println!(
                    "\n  cheapest believable: {} at 2^{:.1}",
                    b.attack, b.log2_cost
                );
            }
            if let Some(cat) = inst.category {
                println!(
                    "  NIST category {} floor: 2^{:.0} classical gates{}",
                    cat.number(),
                    cat.gate_floor_bits(),
                    if matches!(m.svp, SvpModel::GateCount) {
                        ""
                    } else {
                        "  (not comparable to this model — use --model gate-count)"
                    }
                );
            }
        }

        MlweOp::Table { model } => {
            let models: Vec<BkzModel> = match model {
                Some(name) => vec![build_model(&name, false, false)],
                None => vec![
                    BkzModel::core_svp_classical(),
                    BkzModel::core_svp_quantum(),
                    BkzModel::gate_count_realistic(),
                ],
            };
            print!("{}", render_table(&full_report(&models)));
        }

        MlweOp::Margins => print!("{}", margin_table()),

        MlweOp::Sis => {
            let m = BkzModel::core_svp_classical();
            println!(
                "{:<28}  {:>6}  {:>9}  {:>12}",
                "instance", "beta", "log2 cost", "l2 bound"
            );
            for s in all_sis() {
                let beta = sis_required_beta(&s).unwrap_or(f64::NAN);
                match sis_estimate(&s, &m) {
                    Some(e) => println!(
                        "{:<28}  {:>6.0}  {:>9.1}  {:>12.3e}",
                        s.name,
                        e.beta,
                        e.log2_cost,
                        s.l2_bound()
                    ),
                    None => println!(
                        "{:<28}  {:>6.0}  {:>9}  {:>12.3e}",
                        s.name,
                        beta,
                        "n/a",
                        s.l2_bound()
                    ),
                }
            }
            println!(
                "\nML-DSA's forgery bound is deliberately loose; a short SIS solution is not yet a\n\
                 signature, so this is not the parameter sets' security level. See primal.rs."
            );
        }

        MlweOp::Sieve {
            algo,
            dim,
            q,
            seed,
            list,
            buckets,
            verbose,
            progress_every,
            state_dir,
            resume,
            s3_uri,
        } => {
            if (resume || s3_uri.is_some()) && state_dir.is_none() {
                eprintln!("error: --resume and --s3-uri require --state-dir");
                std::process::exit(2);
            }
            if dim == 0
                || q < 2
                || list == 0
                || buckets == 0
                || !matches!(algo.as_str(), "gauss" | "nv" | "bucketed")
            {
                eprintln!("error: invalid sieve algorithm or parameters");
                std::process::exit(2);
            }
            let basis = random_qary_lattice(dim, q, seed);
            let cfg = SieveConfig {
                seed,
                ..Default::default()
            };
            let before = basis.iter().map(|v| norm2(v)).min().unwrap_or(0);
            let live = verbose || progress_every.is_some();
            let mut identity = blake3::Hasher::new();
            identity.update(b"crax-mlwe-sieve-v1\0");
            identity.update(
                &serde_json::to_vec(&(
                    &algo,
                    dim,
                    q,
                    seed,
                    list,
                    buckets,
                    cfg.max_collisions,
                    cfg.max_list,
                    cfg.max_samples,
                    cfg.sample_range,
                    cfg.max_iterations,
                    cfg.max_sample_retries,
                ))
                .unwrap(),
            );
            identity.update(include_str!("../../../cryptanalysis/mlwe/sieve.rs").as_bytes());
            identity.update(env!("CARGO_PKG_VERSION").as_bytes());
            let identity = identity.finalize().to_hex().to_string();
            let mut state = state_dir
                .as_ref()
                .map(|dir| {
                    super::unit_state::UnitState::prepare(
                        dir,
                        s3_uri.as_deref(),
                        "mlwe-sieve",
                        &identity,
                        resume,
                    )
                })
                .transpose()
                .unwrap_or_else(|e| {
                    eprintln!("error: {e}");
                    std::process::exit(1)
                });
            let units = state
                .as_ref()
                .map(|s| s.completed())
                .transpose()
                .unwrap_or_else(|e| {
                    eprintln!("error: {e}");
                    std::process::exit(1)
                })
                .unwrap_or_default();
            let started = std::time::Instant::now();
            let work = std::sync::Arc::new(std::sync::atomic::AtomicU64::new(0));
            let heartbeat = if live {
                let (tx, rx) = std::sync::mpsc::channel::<()>();
                let work = work.clone();
                let every = progress_every.unwrap_or(5);
                let worker = std::thread::spawn(move || {
                    while rx
                        .recv_timeout(std::time::Duration::from_secs(every))
                        .is_err()
                    {
                        eprintln!(
                            "[mlwe sieve] completed={} elapsed={}s",
                            work.load(std::sync::atomic::Ordering::Relaxed),
                            started.elapsed().as_secs()
                        );
                    }
                });
                Some((tx, worker))
            } else {
                None
            };
            let mut unit_idx = units.len();
            match algo.as_str() {
                "gauss" => {
                    let saved: Option<GaussCheckpoint> = units
                        .last()
                        .map(|b| serde_json::from_slice(b))
                        .transpose()
                        .unwrap_or_else(|e| {
                            eprintln!("error: invalid saved sieve state: {e}");
                            std::process::exit(1)
                        });
                    if let Some(saved) = &saved {
                        work.store(saved.stats.iterations, std::sync::atomic::Ordering::Relaxed);
                    }
                    let r = if state.is_none() && !live {
                        Ok(gauss_sieve(&basis, &cfg))
                    } else {
                        gauss_sieve_resume(&basis, &cfg, saved, 1000, |stage| {
                            if let Some(s) = &mut state {
                                s.commit(
                                    unit_idx,
                                    &serde_json::to_vec(stage).map_err(|e| e.to_string())?,
                                )?;
                                unit_idx += 1;
                            }
                            work.store(
                                stage.stats.iterations,
                                std::sync::atomic::Ordering::Relaxed,
                            );
                            if live {
                                eprintln!(
                                    "[mlwe sieve] gauss iterations={} samples={} list={} pairs={}",
                                    stage.stats.iterations,
                                    stage.stats.samples,
                                    stage.list.len(),
                                    stage.stats.pair_ops
                                );
                            }
                            Ok(())
                        })
                    }
                    .unwrap_or_else(|e| {
                        eprintln!("error: {e}");
                        std::process::exit(1)
                    });
                    if let Some(s) = &mut state {
                        s.finish(&serde_json::to_vec_pretty(&serde_json::json!({
                        "schema_version":1,"operation":"mlwe-sieve","algo":"gauss","dim":dim,"q":q,
                        "seed":seed,"shortest":&r.shortest,"norm2":r.norm2.to_string(),"stats":&r.stats
                    })).unwrap()).unwrap_or_else(|e| { eprintln!("error: {e}"); std::process::exit(1) });
                    }
                    report_sieve(
                        "gauss",
                        before,
                        r.norm2,
                        r.stats.peak_list,
                        r.stats.pair_ops,
                        r.stats.samples,
                    );
                }
                "nv" => {
                    let saved: Option<NvCheckpoint> = units
                        .last()
                        .map(|b| serde_json::from_slice(b))
                        .transpose()
                        .unwrap_or_else(|e| {
                            eprintln!("error: invalid saved sieve state: {e}");
                            std::process::exit(1)
                        });
                    if let Some(saved) = &saved {
                        work.store(
                            saved.stats.rounds as u64,
                            std::sync::atomic::Ordering::Relaxed,
                        );
                    }
                    let r = if state.is_none() && !live {
                        Ok(nv_sieve(&basis, list, 0.95, &cfg))
                    } else {
                        nv_sieve_resume(&basis, list, 0.95, &cfg, saved, |stage| {
                            if let Some(s) = &mut state {
                                s.commit(
                                    unit_idx,
                                    &serde_json::to_vec(stage).map_err(|e| e.to_string())?,
                                )?;
                                unit_idx += 1;
                            }
                            work.store(
                                stage.stats.rounds as u64,
                                std::sync::atomic::Ordering::Relaxed,
                            );
                            if live {
                                eprintln!(
                                    "[mlwe sieve] nv rounds={} list={} pairs={}",
                                    stage.stats.rounds,
                                    stage.list.len(),
                                    stage.stats.pair_ops
                                );
                            }
                            Ok(())
                        })
                    }
                    .unwrap_or_else(|e| {
                        eprintln!("error: {e}");
                        std::process::exit(1)
                    });
                    if let Some(s) = &mut state {
                        s.finish(&serde_json::to_vec_pretty(&serde_json::json!({
                        "schema_version":1,"operation":"mlwe-sieve","algo":"nv","dim":dim,"q":q,
                        "seed":seed,"shortest":&r.shortest,"norm2":r.norm2.to_string(),"stats":&r.stats
                    })).unwrap()).unwrap_or_else(|e| { eprintln!("error: {e}"); std::process::exit(1) });
                    }
                    report_sieve(
                        "nguyen-vidick",
                        before,
                        r.norm2,
                        r.stats.peak_list,
                        r.stats.pair_ops,
                        r.stats.samples,
                    );
                }
                "bucketed" => {
                    let saved: Option<BucketedCheckpoint> = units
                        .last()
                        .map(|b| serde_json::from_slice(b))
                        .transpose()
                        .unwrap_or_else(|e| {
                            eprintln!("error: invalid saved sieve state: {e}");
                            std::process::exit(1)
                        });
                    if let Some(saved) = &saved {
                        work.store(
                            saved.stats.rounds as u64,
                            std::sync::atomic::Ordering::Relaxed,
                        );
                    }
                    let r = if state.is_none() && !live {
                        Ok(bucketed_sieve(&basis, list, buckets, 4, &cfg))
                    } else {
                        bucketed_sieve_resume(&basis, list, buckets, 4, &cfg, saved, |stage| {
                            if let Some(s) = &mut state {
                                s.commit(
                                    unit_idx,
                                    &serde_json::to_vec(stage).map_err(|e| e.to_string())?,
                                )?;
                                unit_idx += 1;
                            }
                            work.store(
                                stage.stats.rounds as u64,
                                std::sync::atomic::Ordering::Relaxed,
                            );
                            if live {
                                eprintln!(
                                    "[mlwe sieve] bucketed rounds={} list={} pairs={}",
                                    stage.stats.rounds,
                                    stage.list.len(),
                                    stage.bucketed_pairs
                                );
                            }
                            Ok(())
                        })
                    }
                    .unwrap_or_else(|e| {
                        eprintln!("error: {e}");
                        std::process::exit(1)
                    });
                    if let Some(s) = &mut state {
                        s.finish(&serde_json::to_vec_pretty(&serde_json::json!({
                        "schema_version":1,"operation":"mlwe-sieve","algo":"bucketed","dim":dim,"q":q,
                        "seed":seed,"shortest":&r.result.shortest,"norm2":r.result.norm2.to_string(),
                        "stats":&r.result.stats,"bucketed_pairs":r.bucketed_pairs,"all_pairs":r.all_pairs
                    })).unwrap()).unwrap_or_else(|e| { eprintln!("error: {e}"); std::process::exit(1) });
                    }
                    report_sieve(
                        "bucketed",
                        before,
                        r.result.norm2,
                        r.result.stats.peak_list,
                        r.bucketed_pairs,
                        r.result.stats.samples,
                    );
                    println!(
                        "  buckets: {}   pairs: {} bucketed vs {} all-pairs   speedup: {:.1}x",
                        r.buckets,
                        r.bucketed_pairs,
                        r.all_pairs,
                        r.speedup()
                    );
                }
                other => {
                    eprintln!("unknown sieve `{other}`; try gauss, nv or bucketed");
                    std::process::exit(2);
                }
            }
            if let Some((tx, worker)) = heartbeat {
                let _ = tx.send(());
                let _ = worker.join();
            }
        }

        MlweOp::Scaling {
            dims,
            q,
            verbose,
            progress_every,
            state_dir,
            resume,
            s3_uri,
        } => {
            if (resume || s3_uri.is_some()) && state_dir.is_none() {
                eprintln!("error: --resume and --s3-uri require --state-dir");
                std::process::exit(2);
            }
            let dims: Vec<usize> =
                match dims.split(',').map(|s| s.trim().parse::<usize>()).collect() {
                    Ok(dims) => dims,
                    Err(e) => {
                        eprintln!("error: invalid --dims: {e}");
                        std::process::exit(2);
                    }
                };
            if dims.is_empty() || dims.iter().any(|&d| d == 0) {
                eprintln!("error: --dims requires positive comma-separated dimensions");
                std::process::exit(2);
            }
            let cfg = SieveConfig {
                max_collisions: 40,
                ..Default::default()
            };
            let live = verbose || progress_every.is_some();
            let mut identity = blake3::Hasher::new();
            identity.update(b"crax-mlwe-scaling-v1\0");
            identity.update(
                &serde_json::to_vec(&(dims.as_slice(), q, cfg.max_collisions, cfg.seed)).unwrap(),
            );
            identity.update(include_str!("../../../cryptanalysis/mlwe/sieve.rs").as_bytes());
            identity.update(include_str!("../../../cryptanalysis/lattice.rs").as_bytes());
            identity.update(env!("CARGO_PKG_VERSION").as_bytes());
            let identity = identity.finalize().to_hex().to_string();
            let mut state = match state_dir
                .as_ref()
                .map(|dir| {
                    super::unit_state::UnitState::prepare(
                        dir,
                        s3_uri.as_deref(),
                        "mlwe-scaling",
                        &identity,
                        resume,
                    )
                })
                .transpose()
            {
                Ok(state) => state,
                Err(e) => {
                    eprintln!("error: {e}");
                    std::process::exit(1);
                }
            };
            let mut rows: Vec<crate::cryptanalysis::mlwe::sieve::ScalingRow> =
                match state.as_ref().map(|s| s.completed()).transpose() {
                    Ok(Some(units)) => units
                        .into_iter()
                        .map(|bytes| {
                            serde_json::from_slice(&bytes)
                                .map_err(|e| format!("invalid saved scaling row: {e}"))
                        })
                        .collect::<Result<_, _>>()
                        .unwrap_or_else(|e| {
                            eprintln!("error: {e}");
                            std::process::exit(1);
                        }),
                    Ok(None) => Vec::new(),
                    Err(e) => {
                        eprintln!("error: {e}");
                        std::process::exit(1);
                    }
                };
            if rows.len() > dims.len() || rows.iter().enumerate().any(|(i, row)| row.dim != dims[i])
            {
                eprintln!("error: saved scaling dimensions do not match --dims");
                std::process::exit(1);
            }
            let started = std::time::Instant::now();
            let done = std::sync::Arc::new(std::sync::atomic::AtomicUsize::new(rows.len()));
            if live {
                eprintln!(
                    "[mlwe scaling] {} of {} dimensions already complete",
                    rows.len(),
                    dims.len()
                );
            }
            let heartbeat = if live {
                let (tx, rx) = std::sync::mpsc::channel::<()>();
                let done = done.clone();
                let total = dims.len();
                let every = progress_every.unwrap_or(5);
                let worker = std::thread::spawn(move || {
                    while rx
                        .recv_timeout(std::time::Duration::from_secs(every))
                        .is_err()
                    {
                        eprintln!(
                            "[mlwe scaling] {}/{} dimensions complete elapsed={}s",
                            done.load(std::sync::atomic::Ordering::Relaxed),
                            total,
                            started.elapsed().as_secs()
                        );
                    }
                });
                Some((tx, worker))
            } else {
                None
            };
            for (idx, &dim) in dims.iter().enumerate().skip(rows.len()) {
                if live {
                    eprintln!("[mlwe scaling] dimension {dim} started");
                }
                let row = measure_gauss_scaling(&[dim], q, &cfg).remove(0);
                if let Some(state) = &mut state {
                    let bytes = serde_json::to_vec_pretty(&row).unwrap();
                    if let Err(e) = state.commit(idx, &bytes) {
                        eprintln!("error: {e}");
                        std::process::exit(1);
                    }
                }
                rows.push(row);
                done.store(rows.len(), std::sync::atomic::Ordering::Relaxed);
                if live {
                    eprintln!("[mlwe scaling] dimension {dim} complete: peak_list={} pair_ops={} samples={}",
                    row.peak_list, row.pair_ops, row.samples);
                }
            }
            if let Some((tx, worker)) = heartbeat {
                let _ = tx.send(());
                let _ = worker.join();
            }
            if let Some(state) = &mut state {
                let report = serde_json::json!({"schema_version":1,"operation":"mlwe-scaling",
                    "dims":dims,"q":q,"rows":rows});
                if let Err(e) = state.finish(&serde_json::to_vec_pretty(&report).unwrap()) {
                    eprintln!("error: {e}");
                    std::process::exit(1);
                }
            }
            println!(
                "{:>5}  {:>10}  {:>12}  {:>9}  {:>12}",
                "dim", "peak list", "pair ops", "samples", "2^0.2075d"
            );
            for r in rows {
                println!(
                    "{:>5}  {:>10}  {:>12}  {:>9}  {:>12.0}",
                    r.dim,
                    r.peak_list,
                    r.pair_ops,
                    r.samples,
                    2f64.powf(0.2075 * r.dim as f64)
                );
            }
            println!(
                "\nThe last column is the asymptotic sieve list size. At these dimensions the o(d)\n\
                 term dominates and the two will not agree; what is visible is the growth, not\n\
                 the constant."
            );
        }

        MlweOp::Bkz {
            dim,
            beta,
            q,
            seed,
            verbose,
            progress_every,
            state_dir,
            resume,
            s3_uri,
        } => {
            if (resume || s3_uri.is_some()) && state_dir.is_none() {
                eprintln!("error: --resume and --s3-uri require --state-dir");
                std::process::exit(2);
            }
            if dim == 0 || q < 2 {
                eprintln!("error: --dim must be positive and --q must be at least 2");
                std::process::exit(2);
            }
            let basis = random_qary_lattice(dim, q, seed);
            let live = verbose || progress_every.is_some();
            let mut identity = blake3::Hasher::new();
            identity.update(b"crax-mlwe-bkz-v1\0");
            identity.update(&serde_json::to_vec(&(dim, beta, q, seed, 0.99f64)).unwrap());
            identity.update(include_str!("../../../cryptanalysis/mlwe/sieve.rs").as_bytes());
            identity.update(include_str!("../../../cryptanalysis/lattice.rs").as_bytes());
            identity.update(env!("CARGO_PKG_VERSION").as_bytes());
            let identity = identity.finalize().to_hex().to_string();
            let mut state = match state_dir
                .as_ref()
                .map(|dir| {
                    super::unit_state::UnitState::prepare(
                        dir,
                        s3_uri.as_deref(),
                        "mlwe-bkz",
                        &identity,
                        resume,
                    )
                })
                .transpose()
            {
                Ok(state) => state,
                Err(e) => {
                    eprintln!("error: {e}");
                    std::process::exit(1);
                }
            };
            let saved: Vec<BkzCheckpoint> = match state.as_ref().map(|s| s.completed()).transpose()
            {
                Ok(Some(units)) => units
                    .into_iter()
                    .map(|bytes| {
                        serde_json::from_slice(&bytes)
                            .map_err(|e| format!("invalid saved BKZ stage: {e}"))
                    })
                    .collect::<Result<_, _>>()
                    .unwrap_or_else(|e| {
                        eprintln!("error: {e}");
                        std::process::exit(1);
                    }),
                Ok(None) => Vec::new(),
                Err(e) => {
                    eprintln!("error: {e}");
                    std::process::exit(1);
                }
            };
            let done = std::sync::Arc::new(std::sync::atomic::AtomicUsize::new(saved.len()));
            let total = 1 + beta.saturating_sub(2) / 2;
            let started = std::time::Instant::now();
            if live {
                eprintln!(
                    "[mlwe bkz] {} of {} stages already complete",
                    saved.len(),
                    total
                );
            }
            let heartbeat = if live {
                let (tx, rx) = std::sync::mpsc::channel::<()>();
                let done = done.clone();
                let every = progress_every.unwrap_or(5);
                let worker = std::thread::spawn(move || {
                    while rx
                        .recv_timeout(std::time::Duration::from_secs(every))
                        .is_err()
                    {
                        eprintln!(
                            "[mlwe bkz] {}/{} stages complete elapsed={}s",
                            done.load(std::sync::atomic::Ordering::Relaxed),
                            total,
                            started.elapsed().as_secs()
                        );
                    }
                });
                Some((tx, worker))
            } else {
                None
            };
            let result = if state.is_none() && !live {
                progressive_bkz(&basis, beta, 0.99).map_err(str::to_string)
            } else {
                progressive_bkz_resume(&basis, beta, 0.99, saved, |idx, checkpoint| {
                    if let Some(state) = &mut state {
                        state.commit(
                            idx,
                            &serde_json::to_vec_pretty(checkpoint).map_err(|e| e.to_string())?,
                        )?;
                    }
                    done.store(idx + 1, std::sync::atomic::Ordering::Relaxed);
                    if live {
                        eprintln!(
                            "[mlwe bkz] beta={} complete: head_log2={:.4} volume_log2={:.4}",
                            checkpoint.stage.0, checkpoint.stage.1, checkpoint.stage.2
                        );
                    }
                    Ok(())
                })
            };
            if let Some((tx, worker)) = heartbeat {
                let _ = tx.send(());
                let _ = worker.join();
            }
            match result {
                Ok((reduced, stages)) => {
                    if let Some(state) = &mut state {
                        let report = serde_json::json!({"schema_version":1,"operation":"mlwe-bkz",
                            "dim":dim,"beta":beta,"q":q,"seed":seed,"stages":stages,"basis":reduced});
                        if let Err(e) = state.finish(&serde_json::to_vec_pretty(&report).unwrap()) {
                            eprintln!("error: {e}");
                            std::process::exit(1);
                        }
                    }
                    println!(
                        "{:>6}  {:>16}  {:>16}",
                        "beta", "log2 ||b*_0||", "log2 volume"
                    );
                    for (b, head, vol) in stages {
                        println!("{b:>6}  {head:>16.4}  {vol:>16.4}");
                    }
                }
                Err(e) => {
                    eprintln!("reduction failed: {e}");
                    std::process::exit(1);
                }
            }
        }

        MlweOp::KemPco {
            param,
            oracle,
            seed,
        } => {
            let Some(p) = ml_kem_pco::parameter_set(&param) else {
                eprintln!("unknown parameter set `{param}`; try 512, 768 or 1024");
                std::process::exit(2);
            };
            let full = match oracle.as_str() {
                "full" => true,
                "pc" | "plaintext-checking" => false,
                other => {
                    eprintln!("unknown oracle `{other}`; try full or pc");
                    std::process::exit(2);
                }
            };
            match ml_kem_pco::run_attack(p, full, seed) {
                Some(r) => {
                    println!("{} against the {} oracle", r.parameter_set, r.oracle);
                    println!("  queries:              {}", r.queries);
                    println!("  coefficients:         {}", r.coefficients);
                    println!("  recovered correctly:  {}", r.correct);
                    println!("  decapsulates:         {}", r.decapsulates);
                    println!(
                        "  result:               {}",
                        if r.succeeded() {
                            "KEY RECOVERED"
                        } else {
                            "failed"
                        }
                    );
                }
                None => {
                    eprintln!("attack could not run for this parameter set");
                    std::process::exit(1);
                }
            }
        }

        MlweOp::DsaLeak { per_poly, seed } => {
            match ml_dsa_leakage::run_coefficient_attack(per_poly, seed) {
                Some(r) => {
                    println!("ML-DSA-65: {}", r.method);
                    println!("  signatures observed:  {}", r.signatures);
                    println!("  mask bits leaked:     {}", r.leaked_bits);
                    println!("  s1 coefficients:      {}", r.coefficients);
                    println!("  recovered correctly:  {}", r.correct);
                    println!("  forgery verified:     {}", r.forged);
                    println!(
                        "  result:               {}",
                        if r.succeeded() {
                            "KEY RECOVERED, FORGERY ACCEPTED"
                        } else {
                            "failed"
                        }
                    );
                }
                None => {
                    eprintln!("attack did not gather enough equations");
                    std::process::exit(1);
                }
            }
        }

        MlweOp::DsaPartial { n, m, bits, seed } => {
            match ml_dsa_leakage::recover_from_partial_bits(n, m, bits, seed) {
                Some((truth, found)) => {
                    let ok = truth == found;
                    println!("hidden-number problem: n = {n}, m = {m}, {bits} leaked bits per mask coefficient");
                    println!("  truth:     {truth:?}");
                    println!("  recovered: {found:?}");
                    println!("  result:    {}", if ok { "SOLVED" } else { "wrong answer" });
                }
                None => println!("lattice reduction did not find the target — try more equations or more leaked bits"),
            }
            println!(
                "\nThis runs at a dimension LLL can finish. The real instance has n = 256 per\n\
                 component and needs BKZ at a serious block size; see ml_dsa_leakage::solve_hnp."
            );
        }

        MlweOp::DsaFault { fault, seed } => {
            let reports = match fault.as_str() {
                "all" => ml_dsa_fault::run_all(seed),
                "zero" => ml_dsa_fault::zeroed_nonce_attack(seed)
                    .into_iter()
                    .collect(),
                "reuse" => ml_dsa_fault::nonce_reuse_attack(seed).into_iter().collect(),
                "partial" => ml_dsa_fault::partial_zero_attack(seed)
                    .into_iter()
                    .collect(),
                other => {
                    eprintln!("unknown fault `{other}`; try all, zero, reuse or partial");
                    std::process::exit(2);
                }
            };
            if reports.is_empty() {
                eprintln!("no faulted signature was produced");
                std::process::exit(1);
            }
            for r in reports {
                println!("{}", r.fault);
                println!("  faulted signatures:   {}", r.signatures);
                println!("  signing attempts:     {}", r.attempts);
                println!("  recovered correctly:  {} / {}", r.correct, r.coefficients);
                println!("  forgery verified:     {}", r.forged);
                println!(
                    "  result:               {}\n",
                    if r.succeeded() {
                        "KEY RECOVERED, FORGERY ACCEPTED"
                    } else {
                        "failed"
                    }
                );
            }
        }

        MlweOp::Budget => {
            println!(
                "{:<12}  {:>14}  {:>16}  {:>16}  {:>14}",
                "set", "s1 entropy", "coeffs needed", "counting bound", "published bits"
            );
            for b in ml_dsa_leakage::leakage_budget() {
                println!(
                    "{:<12}  {:>14.0}  {:>16}  {:>16.0}  {:>14}",
                    b.parameter_set,
                    b.secret_entropy_bits,
                    b.coefficients_for_exact_attack,
                    b.counting_bound_bits,
                    b.published_bits
                );
            }
            println!(
                "\n`published bits` is the Journal of Cryptology 2026 figure for 256 leaking\n\
                 coordinates. It comes from a lattice analysis, not from the counting bound beside\n\
                 it: the counting bound says what is impossible, the published figure says what was\n\
                 achieved."
            );
            println!(
                "\nML-DSA parameter sets known to this build: {}",
                ["ml-dsa-44", "ml-dsa-65", "ml-dsa-87"]
                    .iter()
                    .filter(|n| ml_dsa_by_name(n).is_some())
                    .copied()
                    .collect::<Vec<_>>()
                    .join(", ")
            );
        }
    }
}

fn report_sieve(name: &str, before: i128, after: i128, list: usize, pairs: u64, samples: usize) {
    println!("{name} sieve");
    println!("  shortest before:  |v|^2 = {before}");
    println!("  shortest after:   |v|^2 = {after}");
    println!(
        "  improvement:      {:.3}x shorter",
        (before as f64).sqrt() / (after.max(1) as f64).sqrt()
    );
    println!("  peak list:        {list}");
    println!("  pair operations:  {pairs}");
    println!("  samples drawn:    {samples}");
}
