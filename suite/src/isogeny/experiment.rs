//! # Experimental harness.
//!
//! Drives the full pipeline:
//!
//! 1. Generate random ordinary curves at a target bit-size.
//! 2. For each curve, compute CM data ([`crate::isogeny::cm`]).
//! 3. Build the local `S`-isogeny graph ([`crate::isogeny::graph`]).
//! 4. Run the attack suite ([`crate::isogeny::attack`]) on every
//!    vertex of the graph.
//! 5. Compute summary statistics: mean/median/stddev of rho cost
//!    across the class, count of curves where MOV / Smart apply.
//!
//! Output is JSON for analysis in a notebook downstream.

use super::attack::{run_attack_suite, AttackReport};
use super::cm::cm_discriminant;
use super::graph::build_graph;
use super::SmallCurve;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::Path;

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ExperimentConfig {
    /// Approximate bit-size of `p`.
    pub bits: u32,
    /// How many random curves to sweep.
    pub num_curves: u32,
    /// Primes `ℓ` used for graph construction.
    pub primes: Vec<u64>,
    /// Max nodes per isogeny graph (cap for very dense graphs).
    pub max_graph_nodes: usize,
    /// Cap on rho iterations per discrete-log attempt.
    pub rho_max_iters: u64,
    /// Deterministic seed for reproducibility.
    pub seed: u64,
}

impl ExperimentConfig {
    pub fn default_for_bits(bits: u32) -> Self {
        Self {
            bits,
            num_curves: 4,
            primes: vec![2, 3, 5],
            max_graph_nodes: 32,
            rho_max_iters: 1 << 18,
            seed: 0xC0FFEE,
        }
    }
}

/// Summary of one experimental sweep.
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ExperimentReport {
    pub config: ExperimentConfig,
    pub per_curve: Vec<PerCurveResult>,
    pub aggregate: AggregateStats,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct PerCurveResult {
    pub start: (u64, u64, u64),
    pub class_size: usize,
    /// Attack reports for every vertex in the class.
    pub class: Vec<AttackReport>,
    pub mean_rho_iters: f64,
    pub median_rho_iters: f64,
    pub stddev_rho_iters: f64,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct AggregateStats {
    pub total_curves: usize,
    pub total_isogenous_vertices: usize,
    pub curves_with_smart_applicable: usize,
    pub curves_with_mov_feasible: usize,
    pub curves_with_glv: usize,
    pub overall_mean_rho_iters: f64,
}

#[derive(Clone, Debug, Serialize)]
pub struct CheckpointProgress {
    pub status: &'static str,
    pub completed_curves: usize,
    pub planned_curves: usize,
    pub identity_blake3: String,
    pub report: Option<ExperimentReport>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct CheckpointIdentity {
    config: ExperimentConfig,
    binary_blake3: String,
    curves: Vec<(u64, u64, u64)>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct CheckpointPayload {
    schema_version: u32,
    identity: CheckpointIdentity,
    completed: Vec<PerCurveResult>,
}

#[derive(Deserialize, Serialize)]
struct CheckpointEnvelope {
    payload: CheckpointPayload,
    blake3: String,
}

fn payload_hash(payload: &CheckpointPayload) -> Result<String, String> {
    let bytes = serde_json::to_vec(payload).map_err(|e| e.to_string())?;
    Ok(blake3::hash(&bytes).to_hex().to_string())
}

fn save_checkpoint(path: &Path, payload: &CheckpointPayload) -> Result<(), String> {
    let envelope = CheckpointEnvelope {
        blake3: payload_hash(payload)?,
        payload: payload.clone(),
    };
    let bytes = serde_json::to_vec_pretty(&envelope).map_err(|e| e.to_string())?;
    let nonce = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map_err(|e| e.to_string())?
        .as_nanos();
    let temp = path.with_extension(format!("json.tmp.{}.{}", std::process::id(), nonce));
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&temp)
        .map_err(|e| format!("{}: {e}", temp.display()))?;
    file.write_all(&bytes).map_err(|e| e.to_string())?;
    file.sync_all().map_err(|e| e.to_string())?;
    fs::rename(&temp, path).map_err(|e| format!("{}: {e}", path.display()))?;
    #[cfg(unix)]
    {
        let directory = path.parent().ok_or("checkpoint has no parent directory")?;
        fs::File::open(directory)
            .and_then(|file| file.sync_all())
            .map_err(|e| format!("{}: {e}", directory.display()))?;
    }
    Ok(())
}

/// Resume a deterministic sweep at the next unfinished starting curve. A
/// completed unit is published by atomic checkpoint replacement before the
/// next unit starts. The lock keeps one local writer per state directory.
pub fn run_experiment_checkpointed(
    cfg: &ExperimentConfig,
    state_dir: &Path,
    resume: bool,
    max_new_curves: Option<usize>,
    binary_blake3: &str,
) -> Result<CheckpointProgress, String> {
    if cfg.num_curves == 0 || cfg.num_curves > 1_000 {
        return Err("checkpointed experiment requires 1..=1000 starting curves".into());
    }
    if max_new_curves == Some(0) || binary_blake3.is_empty() {
        return Err("max-new-curves and binary identity must be nonzero".into());
    }
    fs::create_dir_all(state_dir).map_err(|e| format!("{}: {e}", state_dir.display()))?;
    let lock_path = state_dir.join(".experiment.lock");
    let lock = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .open(&lock_path)
        .map_err(|e| format!("{}: {e}", lock_path.display()))?;
    lock.try_lock()
        .map_err(|e| format!("experiment state directory is already in use: {e}"))?;

    let curves = generate_random_curves(cfg.bits, cfg.num_curves, cfg.seed);
    if curves.len() != cfg.num_curves as usize {
        return Err("could not generate the requested number of ordinary curves".into());
    }
    let identity = CheckpointIdentity {
        config: cfg.clone(),
        binary_blake3: binary_blake3.to_string(),
        curves: curves.iter().map(|c| (c.p, c.a, c.b)).collect(),
    };
    let identity_blake3 = blake3::hash(&serde_json::to_vec(&identity).map_err(|e| e.to_string())?)
        .to_hex()
        .to_string();
    let checkpoint_path = state_dir.join("checkpoint.json");
    let mut payload = if resume {
        let bytes = fs::read(&checkpoint_path)
            .map_err(|e| format!("cannot resume {}: {e}", checkpoint_path.display()))?;
        if bytes.len() > 32 * 1024 * 1024 {
            return Err("isogeny experiment checkpoint exceeds 32 MiB".into());
        }
        let envelope: CheckpointEnvelope =
            serde_json::from_slice(&bytes).map_err(|e| format!("invalid checkpoint: {e}"))?;
        if payload_hash(&envelope.payload)? != envelope.blake3 {
            return Err("isogeny experiment checkpoint checksum differs".into());
        }
        if envelope.payload.schema_version != 1
            || serde_json::to_vec(&envelope.payload.identity).map_err(|e| e.to_string())?
                != serde_json::to_vec(&identity).map_err(|e| e.to_string())?
        {
            return Err("isogeny experiment checkpoint identity differs".into());
        }
        if envelope.payload.completed.len() > curves.len()
            || envelope
                .payload
                .completed
                .iter()
                .enumerate()
                .any(|(i, result)| result.start != identity.curves[i])
        {
            return Err("isogeny experiment checkpoint curve sequence differs".into());
        }
        envelope.payload
    } else {
        if checkpoint_path.exists() {
            return Err("isogeny experiment checkpoint exists; pass --resume".into());
        }
        let payload = CheckpointPayload {
            schema_version: 1,
            identity,
            completed: Vec::new(),
        };
        save_checkpoint(&checkpoint_path, &payload)?;
        payload
    };

    let remaining = curves.len() - payload.completed.len();
    let budget = max_new_curves.unwrap_or(remaining).min(remaining);
    for index in payload.completed.len()..payload.completed.len() + budget {
        let result = run_one_curve(cfg, &curves[index], index);
        payload.completed.push(result);
        save_checkpoint(&checkpoint_path, &payload)?;
        eprintln!(
            "[isogeny experiment] checkpointed curve {}/{}",
            payload.completed.len(),
            curves.len()
        );
    }
    let done = payload.completed.len() == curves.len();
    Ok(CheckpointProgress {
        status: if done { "complete" } else { "partial" },
        completed_curves: payload.completed.len(),
        planned_curves: curves.len(),
        identity_blake3,
        report: done.then(|| report_from_results(cfg, payload.completed)),
    })
}

/// Run one full experimental sweep.
pub fn run_experiment(cfg: &ExperimentConfig) -> ExperimentReport {
    let starting_curves = generate_random_curves(cfg.bits, cfg.num_curves, cfg.seed);
    let per_curve: Vec<PerCurveResult> = starting_curves
        .par_iter()
        .enumerate()
        .map(|(idx, curve)| run_one_curve(cfg, curve, idx))
        .collect();
    report_from_results(cfg, per_curve)
}

fn run_one_curve(cfg: &ExperimentConfig, curve: &SmallCurve, idx: usize) -> PerCurveResult {
    let local_seed = cfg.seed.wrapping_add(idx as u64);
    let graph = build_graph(curve, &cfg.primes, cfg.max_graph_nodes);
    let class: Vec<AttackReport> = graph
        .nodes
        .iter()
        .map(|node| {
            let candidate = SmallCurve {
                name: curve.name,
                p: node.curve.0,
                a: node.curve.1,
                b: node.curve.2,
            };
            run_attack_suite(&candidate, cfg.rho_max_iters, local_seed)
        })
        .collect();
    let iters: Vec<f64> = class
        .iter()
        .filter_map(|report| report.rho_iters.map(|value| value as f64))
        .collect();
    let mean = if iters.is_empty() {
        0.0
    } else {
        iters.iter().sum::<f64>() / iters.len() as f64
    };
    let mut sorted = iters.clone();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let median = if sorted.is_empty() {
        0.0
    } else {
        sorted[sorted.len() / 2]
    };
    let var = if iters.len() < 2 {
        0.0
    } else {
        iters
            .iter()
            .map(|value| (value - mean).powi(2))
            .sum::<f64>()
            / (iters.len() as f64 - 1.0)
    };
    PerCurveResult {
        start: (curve.p, curve.a, curve.b),
        class_size: class.len(),
        class,
        mean_rho_iters: mean,
        median_rho_iters: median,
        stddev_rho_iters: var.sqrt(),
    }
}

fn report_from_results(cfg: &ExperimentConfig, per_curve: Vec<PerCurveResult>) -> ExperimentReport {
    let total_curves = per_curve.len();
    let total_vertices: usize = per_curve.iter().map(|r| r.class_size).sum();
    let smart_count: usize = per_curve
        .iter()
        .flat_map(|r| r.class.iter())
        .filter(|a| a.smart_applies)
        .count();
    let mov_count: usize = per_curve
        .iter()
        .flat_map(|r| r.class.iter())
        .filter(|a| a.mov_feasible)
        .count();
    let glv_count: usize = per_curve
        .iter()
        .flat_map(|r| r.class.iter())
        .filter(|a| a.glv_speedup_available)
        .count();
    let all_iters: Vec<f64> = per_curve
        .iter()
        .flat_map(|r| r.class.iter())
        .filter_map(|a| a.rho_iters.map(|v| v as f64))
        .collect();
    let overall_mean = if all_iters.is_empty() {
        0.0
    } else {
        all_iters.iter().sum::<f64>() / all_iters.len() as f64
    };

    ExperimentReport {
        config: cfg.clone(),
        per_curve,
        aggregate: AggregateStats {
            total_curves,
            total_isogenous_vertices: total_vertices,
            curves_with_smart_applicable: smart_count,
            curves_with_mov_feasible: mov_count,
            curves_with_glv: glv_count,
            overall_mean_rho_iters: overall_mean,
        },
    }
}

/// Render an experiment report as JSON (pretty-printed).
pub fn to_json(report: &ExperimentReport) -> String {
    serde_json::to_string_pretty(report).unwrap_or_else(|_| "{}".into())
}

// ── Random curve generation ──────────────────────────────────────────────────

/// Generate a deterministic batch of random ordinary curves with
/// `p ≈ 2^bits`.  Tries a small prime near `2^bits` and varies
/// `(a, b)` until the curve is non-singular and ordinary.
fn generate_random_curves(bits: u32, count: u32, seed: u64) -> Vec<SmallCurve> {
    // With BSGS point counting wired in, we can scale to ~62-bit
    // primes (we keep p < 2^62 so intermediate u128 products in the
    // SmallCurve helpers don't overflow).  We still clamp the lower
    // end at 8 — anything smaller has < 256 field elements and the
    // toy curves are a better fit.
    let p = next_prime_near_2pow(bits.clamp(8, 62));
    let mut result = Vec::with_capacity(count as usize);
    let mut rng_state = seed;
    let mut attempts = 0;
    while result.len() < count as usize && attempts < count as u64 * 64 {
        attempts += 1;
        rng_state = rng_state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        let a = (rng_state >> 7) % p;
        rng_state = rng_state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        let b = (rng_state >> 7) % p;
        // Discriminant condition: 4 a³ + 27 b² ≠ 0 (mod p).
        let disc = (4 * ((a as u128 * a as u128 % p as u128) * a as u128 % p as u128)
            + 27 * (b as u128 * b as u128 % p as u128))
            % p as u128;
        if disc == 0 {
            continue;
        }
        let curve = SmallCurve {
            name: "exp",
            p,
            a,
            b,
        };
        let cm = cm_discriminant(&curve);
        if cm.supersingular {
            continue;
        }
        result.push(curve);
    }
    result
}

/// Smallest prime ≥ 2^bits found by trial division.  Caller passes
/// `bits` in `[8, 30]` to keep the search bounded.
fn next_prime_near_2pow(bits: u32) -> u64 {
    let start: u64 = 1u64 << bits;
    let mut n = start | 1; // make odd
    while !is_probable_prime(n) {
        n += 2;
    }
    n
}

fn is_probable_prime(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    for p in [2u64, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37] {
        if n == p {
            return true;
        }
        if n.is_multiple_of(p) {
            return false;
        }
    }
    // Deterministic Miller-Rabin for n < 3 317 044 064 679 887 385 961 981
    // (covers all of u64) using the witness set from Sorenson-Webster.
    miller_rabin_u64(n, &[2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37])
}

fn miller_rabin_u64(n: u64, witnesses: &[u64]) -> bool {
    let mut d = n - 1;
    let mut s = 0u32;
    while d & 1 == 0 {
        d >>= 1;
        s += 1;
    }
    'next: for &a in witnesses {
        if a % n == 0 {
            continue;
        }
        let mut x = mod_pow_u64(a, d, n);
        if x == 1 || x == n - 1 {
            continue;
        }
        for _ in 0..(s - 1) {
            x = ((x as u128 * x as u128) % n as u128) as u64;
            if x == n - 1 {
                continue 'next;
            }
        }
        return false;
    }
    true
}

fn mod_pow_u64(base: u64, mut exp: u64, m: u64) -> u64 {
    let mm = m as u128;
    let mut acc: u128 = 1;
    let mut b = base as u128 % mm;
    while exp > 0 {
        if exp & 1 == 1 {
            acc = (acc * b) % mm;
        }
        b = (b * b) % mm;
        exp >>= 1;
    }
    acc as u64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn next_prime_basic() {
        let p = next_prime_near_2pow(10);
        assert!(p >= 1024);
        assert!(is_probable_prime(p));
    }

    #[test]
    fn experiment_tiny_smoke() {
        // 9-bit primes are large enough to be interesting and small
        // enough to keep the test fast.
        let mut cfg = ExperimentConfig::default_for_bits(9);
        cfg.num_curves = 1;
        cfg.primes = vec![2];
        cfg.max_graph_nodes = 6;
        cfg.rho_max_iters = 1 << 10;
        let report = run_experiment(&cfg);
        assert!(!report.per_curve.is_empty());
    }

    #[test]
    fn checkpoint_resume_replays_the_exact_curve_schedule() {
        let mut cfg = ExperimentConfig::default_for_bits(8);
        cfg.num_curves = 2;
        cfg.primes = vec![2];
        cfg.max_graph_nodes = 4;
        cfg.rho_max_iters = 128;
        let nonce = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let dir = std::env::temp_dir().join(format!(
            "crax-isogeny-checkpoint-{}-{nonce}",
            std::process::id()
        ));
        let first = run_experiment_checkpointed(&cfg, &dir, false, Some(1), "binary-a").unwrap();
        assert_eq!(first.status, "partial");
        assert_eq!(first.completed_curves, 1);
        assert!(first.report.is_none());
        assert!(run_experiment_checkpointed(&cfg, &dir, false, None, "binary-a").is_err());
        assert!(run_experiment_checkpointed(&cfg, &dir, true, None, "binary-b").is_err());
        let mut changed = cfg.clone();
        changed.seed += 1;
        assert!(run_experiment_checkpointed(&changed, &dir, true, None, "binary-a").is_err());
        let finished = run_experiment_checkpointed(&cfg, &dir, true, None, "binary-a").unwrap();
        assert_eq!(finished.status, "complete");
        assert_eq!(finished.completed_curves, 2);
        assert_eq!(
            serde_json::to_value(finished.report.unwrap()).unwrap(),
            serde_json::to_value(run_experiment(&cfg)).unwrap()
        );
        let path = dir.join("checkpoint.json");
        let mut saved: serde_json::Value =
            serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
        saved["blake3"] = serde_json::json!("0".repeat(64));
        fs::write(&path, serde_json::to_vec(&saved).unwrap()).unwrap();
        assert!(
            run_experiment_checkpointed(&cfg, &dir, true, None, "binary-a")
                .unwrap_err()
                .contains("checksum differs")
        );
        fs::remove_dir_all(dir).unwrap();
    }
}
