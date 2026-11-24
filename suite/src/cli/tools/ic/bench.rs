//! `ic bench` — run index-calculus configurations and compare them.
//!
//! ```text
//! ic bench --list                       what can be plugged in where
//! ic bench --bits 16 --factor-base prime-abscissa:size=24 \
//!          --oracle mitm:negation_folded=1 --targets walk
//! ic bench --fp2-bits 20 --factor-base fp2-subfield --oracle fp2-weil
//! ic bench --sweep sweep.json --out docs/ic/runs/sweep-YYYY-MM-DD.json
//! ```
//!
//! A configuration is a choice at each stage.  The table it prints
//! carries every stage's numbers, so the effect of a choice is visible
//! where it lands: change the factor base and the hit rate moves, which
//! moves the trials, which moves the matrix.
//!
//! See `docs/ic/FRAMEWORK.md`.

use clap::Args;
use serde_json::{json, Value};

use crate::cryptanalysis::ic_boundary::{
    calibrate_binary_instance, calibrate_group, calibrate_row_ops, calibrate_word_xor,
    find_prime_order_curve, generic_floor_ops, koblitz_instance, random_binary_instance,
    rho_reference, rho_reference_negation, roster_prime_instance, signed_frobenius_rho,
    BinaryGroup, BinaryInstance, Calibration, CountedGroup, GroupOps, PinOutcome, PrimeCurve,
    PrimeInstance, RhoResult,
};
use crate::cryptanalysis::ic_fp2::{
    calibrate_fp_units, find_fp2_curve, Fp2Curve, Fp2Instance, Fp2SubfieldBase, Fp2WeilOracle,
};
use crate::cryptanalysis::ic_framework::affine::AffineS3Oracle;
use crate::cryptanalysis::ic_framework::batch_mitm::BinaryBatchMitmOracle;
use crate::cryptanalysis::ic_framework::rep_join::RepJoinOracle;
use crate::cryptanalysis::ic_framework::hashed::{HashedAffineBase, HashedTensorOracle};
use crate::cryptanalysis::ic_framework::linalg::MATRIX_NAMES;
use crate::cryptanalysis::ic_framework::plugins::{
    BinarySubspaceBase, DescentAlgebraicOracle, FrobeniusMitmOracle, KoblitzOrbitBase, MitmOracle,
    PrimeAbscissaBase, SubtractOracle,
};
use crate::cryptanalysis::ic_framework::prime_batch_mitm::PrimeBatchMitmOracle;
use crate::cryptanalysis::ic_framework::chain_sat::ChainSatOracle;
use crate::cryptanalysis::ic_framework::solvers::{
    solver_by_name, solver_registry, validate_solver_params,
};
use crate::cryptanalysis::ic_framework::stages::{
    DecompositionOracle, FactorBaseBuilder, InstanceCtx, Params, Targets,
};
use crate::cryptanalysis::ic_framework::{format_markdown, run_pipeline, PipelineSpec, RunReport};

#[derive(Args, Clone)]
pub struct BenchArgs {
    /// Print what can be plugged in at each stage, with the parameters
    /// each plug-in reads, and exit.
    #[arg(long)]
    pub list: bool,
    /// Prime-field instance of this subgroup bit length.
    #[arg(long)]
    pub bits: Option<u32>,
    /// Binary-field instance of this field degree (random curve).
    #[arg(long)]
    pub char2_degree: Option<u32>,
    /// Koblitz instance of this field degree.
    #[arg(long)]
    pub koblitz_degree: Option<u32>,
    /// `F_{p²}` instance whose prime-order subgroup has about this many
    /// bits (`p ≈ 2^{bits/2}`, random curve not defined over `F_p`).
    #[arg(long)]
    pub fp2_bits: Option<u32>,
    /// Largest cofactor a random binary curve may have.  The boundary
    /// ladders use 8, so `S = ops / sqrt(r)` is taken over a subgroup
    /// close to the whole group, as on every ledger row; a larger bound
    /// finds a curve faster but can hand back a tiny `r` that makes `S`
    /// meaningless against rho.
    #[arg(long, default_value_t = 8)]
    pub max_cofactor: u64,
    /// `name` or `name:k=v,k=v`.
    #[arg(long)]
    pub factor_base: Option<String>,
    /// `name` or `name:k=v,k=v`.
    #[arg(long)]
    pub oracle: Option<String>,
    /// The polynomial solver, for oracles that use one.
    #[arg(long)]
    pub solver: Option<String>,
    /// `random` or `walk`.
    #[arg(long, default_value = "walk")]
    pub targets: String,
    /// The relation matrix, including opt-in `incremental-gauss-u32` reciprocal arithmetic.
    #[arg(long, default_value = "incremental-gauss")]
    pub linalg: String,
    #[arg(long, default_value_t = 2_000_000)]
    pub max_trials: u64,
    #[arg(long, default_value_t = 0x1C_B0_0B_DA_7A)]
    pub seed: u64,
    /// Repeats per configuration; each draws a fresh target.
    #[arg(long, default_value_t = 1)]
    pub repeats: usize,
    /// Per-solver-call budget in seconds; 0 for none.
    #[arg(long, default_value_t = 120)]
    pub solver_budget_seconds: u64,
    /// Counted Pollard-rho runs on the same instance and planted targets,
    /// averaged into the `vs rho` column; 0 leaves the column empty.
    #[arg(long, default_value_t = 16)]
    pub rho_runs: usize,
    /// Threads for the relation phase (and the matched rho runs); 0 is
    /// every available core.  Wall time only: every count, row, `S` and
    /// recovered logarithm are those of `--threads 1`.  An oracle that
    /// cannot fork stays serial.
    #[arg(long, default_value_t = 1)]
    pub threads: usize,
    /// A JSON file of configurations to sweep.  See the framework
    /// documentation for the schema.
    #[arg(long)]
    pub sweep: Option<std::path::PathBuf>,
}

/// `name:k=v,k=v` → `(name, params)`.
fn parse_plugin(spec: &str) -> Result<(String, Params), String> {
    let (name, rest) = match spec.split_once(':') {
        None => (spec, ""),
        Some((n, r)) => (n, r),
    };
    let mut params = Params::default();
    for kv in rest.split(',').filter(|s| !s.is_empty()) {
        let (k, v) = kv
            .split_once('=')
            .ok_or_else(|| format!("parameter `{kv}` is not key=value"))?;
        params.set(k.trim(), v.trim());
    }
    Ok((name.to_string(), params))
}

fn listing() -> Value {
    let solvers: Vec<Value> = solver_registry()
        .iter()
        .map(|s| {
            json!({
                "name": s.name(),
                "describes": s.describe(),
                "parameters": s.parameters().iter()
                    .map(|(k, d)| json!({"name": k, "means": d}))
                    .collect::<Vec<_>>(),
            })
        })
        .collect();
    json!({
        "stages": [
            {
                "stage": "factor base",
                "trait": "FactorBaseBuilder",
                "what_it_chooses": "which points relations are written over, and which unknown each point contributes to",
                "plugins": [
                    {"name": "prime-abscissa", "regimes": ["prime"],
                     "parameters": [{"name": "size", "means": "abscissae in the base; the family optimum is about #E^(1/3)"}]},
                    {"name": "hashed-affine", "regimes": ["prime"],
                     "parameters": [
                        {"name": "slots", "means": "independent affine-hashed slot bases, 2..=8; must match the oracle"},
                        {"name": "seed", "means": "SplitMix64 seed for the affine hash seeds; default 1"},
                        {"name": "tau", "means": "shared threshold; default the Lemma 13 integer ceiling"},
                        {"name": "s", "means": "shared hash prime in [2p,4p]; default the first prime there"},
                        {"name": "steps", "means": "enumeration and per-target contraction budget in charged primitive steps"}]},
                    {"name": "binary-subspace", "regimes": ["char2", "koblitz"],
                     "parameters": [{"name": "dimension", "means": "F_2-dimension of the abscissa subspace"}]},
                    {"name": "fp2-subfield", "regimes": ["fp2"],
                     "parameters": [{"name": "size", "means": "abscissae in F_p in the base, smallest x0 first; default all (about p/2)"}]},
                    {"name": "koblitz-orbit", "regimes": ["koblitz"],
                     "parameters": [
                        {"name": "divisor", "means": "comma-separated factor indices selecting the Frobenius-invariant subspace"},
                        {"name": "no_fold", "means": "1 for one column per abscissa: the control that shows what the fold buys"}]},
                ],
            },
            {
                "stage": "targets",
                "trait": "Targets",
                "what_it_chooses": "how each trial point is produced",
                "plugins": [
                    {"name": "random", "means": "a fresh [a]G + [b]Q per trial: two scalar multiplications"},
                    {"name": "walk", "means": "an r-adding walk: one addition per trial, with a repeat guard"},
                    {"name": "walk-batch16", "means": "sixteen walk lanes stepped together with one shared inversion; native pair addition where the group has it"},
                    {"name": "walk-batch16-scalar", "means": "the same sixteen lanes added one at a time: the control for walk-batch16"},
                    {"name": "walk-batch16-vector", "means": "sixteen lanes with the vector pair formulas after the shared inverse"},
                    {"name": "walk-batch16-vector-inverse", "means": "sixteen lanes with a vectorised shared inverse as well"},
                ],
            },
            {
                "stage": "point decomposition",
                "trait": "DecompositionOracle",
                "what_it_chooses": "how a target is written as a sum of factor-base points",
                "plugins": [
                    {"name": "subtract", "summands": 2, "regimes": ["prime", "char2", "koblitz", "fp2"],
                     "parameters": []},
                    {"name": "subtract-binary-batch", "summands": 2, "regimes": ["char2", "koblitz"],
                     "parameters": [{"name": "block", "means": "batch size 1..4096, default 32"},
                                    {"name": "lazy", "means": "1 (default) to finish only candidate ordinates; 0 for full batch"}]},
                    {"name": "mitm", "summands": "2 or 3", "regimes": ["prime", "char2", "koblitz", "fp2"],
                     "parameters": [{"name": "native_setup_pricing", "means": "0 or1, default0; whole native setup with observed arithmetic diagnostics"},{"name": "negation_folded", "means": "1 to halve the table's additions"},
                                    {"name": "coset_filter", "means": "1 to build only the pairs whose coset classes in E/<G> cancel (m = 2, cofactor > 1); cofactor 2 reads the class from Tr(x) = Tr(a) for free"},
                                    {"name": "m", "means": "summands, 2 or 3"}]},
                    {"name": "mitm-prime-batched", "summands": "2 or 3", "regimes": ["prime"],
                     "parameters": [{"name": "m", "means": "summands, 2 or 3"},
                                    {"name": "negation_folded", "means": "1 (default) to charge the folded build's additions, 0 the full build's; same table either way"},
                                    {"name": "native_setup_pricing", "means": "1 (default) charges the batched preparation as measured nanoseconds; 0 charges the scalar build's additions"},
                                    {"name": "native_probe_pricing", "means": "1 (default) charges m = 3 candidate arithmetic as measured nanoseconds; 0 charges one addition per candidate point"},
                                    {"name": "chunk", "means": "pairs per batched inversion while preparing, default 1024"},
                                    {"name": "probe_chunk", "means": "abscissae per batched inversion while probing at m = 3, default 16"}],
                     "needs": "the mitm pair table (same entries and witnesses) prepared with one inversion per abscissa pair and Montgomery batch inversion; lookups and hit verification stay counted as for mitm"},
                    {"name": "rep-join", "summands": "2..9", "regimes": ["prime", "char2", "koblitz", "fp2"],
                     "parameters": [{"name": "m", "means": "summands, 2..=9"},
                                    {"name": "filter_bits", "means": "d in 0..=32: pair sums kept only when their abscissa hash lies in a 2^-d subset (the representation filter); 0 = plain MITM at m"},
                                    {"name": "filter_seed", "means": "filter hash seed, default 1"}],
                     "needs": "generic: the (m-2)-tuple search is exhaustive, so the filter saves memory and lookups, never additions (Delaplace-May 2019 without the summation-polynomial enumeration)"},
                    {"name": "hashed-tensor", "summands": "2..8", "regimes": ["prime"],
                     "parameters": [
                        {"name": "slots", "means": "independent affine-hashed slot bases, 2..=8; must match hashed-affine"},
                        {"name": "seed", "means": "SplitMix64 seed for the affine hash seeds; default 1"},
                        {"name": "tau", "means": "shared threshold; must match hashed-affine"},
                        {"name": "s", "means": "shared hash prime; must match hashed-affine"},
                        {"name": "steps", "means": "per-target contraction budget in charged primitive steps"}],
                     "needs": "hashed-affine with identical slots, seed, tau and s; contraction primitive steps are uncalibrated, so do not read S as a priced end-to-end cost"},
                    {"name": "fp2-weil", "summands": 2, "regimes": ["fp2"],
                     "parameters": [],
                     "needs": "fp2-subfield: Gaudry/Diem n = 2, the Weil restriction of S3(x1, x2, x_R) over F_p in (x1 + x2, x1 x2), roots by gcd(g, X^p - X) and Cantor-Zassenhaus; F_p multiplications, inversions and square roots counted and priced at this host's measured F_p units"},
                    {"name": "mitm-frobenius", "summands": "2 or 3", "regimes": ["koblitz"],
                     "parameters": [{"name": "m", "means": "summands, 2 or 3"},
                                    {"name": "coset_filter", "means": "1 to build only the representative-point pairs whose coset classes in E/<G> cancel (m = 2, cofactor > 1)"}]},
                    {"name": "mitm-batched", "summands": "2", "regimes": ["char2", "koblitz"],
                     "parameters": [{"name":"vector_prepare","means":"0 scalar default,1 vector,2 vector with packed squaring <=32 bits; guarded AVX2/PCLMUL, exact fallback"},{"name":"scalar_prepare","means":"0 or1, default0; original preparation, fixed-m2 queries"},{"name":"adaptive_prepare","means":"0 or1, default0; scalar at <=64 abscissae, cached above"},{"name":"prefix_inverse_cache","means":"0 or1, default0; bounded inverse reuse, generic fallback"},{"name":"x_only","means":"0 or1, default0; abscissa-only preparation"},{"name":"batch_size","means":"1..=65536, default1024; ordered batch preparation"},{"name":"suppress_indexed_counter","means":"0 default or1; setup-state experiment omitting only the indexed-pair metadata entry"}]},
                    {"name": "affine-s3", "summands": "2", "regimes": ["char2", "koblitz"],
                     "parameters": [{"name":"max_residual","means":"0..20, default12; complete subtraction fallback beyond it"},
                                    {"name":"column_solver","means":"0 or1, default0; direct projected column elimination"},
                                    {"name":"inverse_cache","means":"0 or1, default0; prefix inverse-square preparation"}],
                     "needs":"a subspace factor base; native affine projection and exact signed lifts"},
                    {"name": "chain-sat", "summands": "2..31", "regimes": ["char2", "koblitz"],
                     "parameters": [{"name":"m","means":"2..31 exact-length summands, repetitions allowed"},
                                    {"name":"topology","means":"serial or balanced; default serial"},
                                    {"name":"conflicts","means":"native CDCL conflict budget per target"},
                                    {"name":"models","means":"maximum candidate models checked per target"}],
                     "needs":"native SAT with local S3 blocks; binary-subspace or koblitz-orbit; local blocks require n <= 21"},
                    {"name": "descent-algebraic", "summands": "2, 3 or 4", "regimes": ["char2", "koblitz"],
                     "parameters": [{"name": "m", "means": "summands, 2 (descends S3), 3 (descends S4) or 4 (balanced split of S5)"},{"name": "inter_dim", "means": "m = 4 only: dimension of the subspace span(1..z^(l-1)) the two intermediates are restricted to (the representation filter); default n"}],
                     "needs": "a subspace factor base (binary-subspace or koblitz-orbit) and --solver"},
                ],
            },
            {
                "stage": "polynomial system solver",
                "trait": "SystemSolver",
                "what_it_chooses": "how an algebraic oracle decides its system; the plug point for F4, F5, XL, SAT",
                "plugins": solvers,
            },
            {
                "stage": "relation matrix",
                "trait": "RelationSolver",
                "what_it_chooses": "how relations are accumulated and the logarithm read off",
                "plugins": MATRIX_NAMES.iter().map(|(n, d)| json!({"name": n, "means": d})).collect::<Vec<_>>(),
            },
        ],
        "how_to_add_one": "implement the stage's trait and register it; docs/ic/FRAMEWORK.md walks through a solver end to end",
    })
}

/// Measure this host, then pin every ratio the repository's table
/// carries, so two runs of the same counts price the same (§12 of the
/// ledger note).
/// The prime regime's calibration: the group, the matrix and the word
/// XOR measured here, the prime-only units (square roots, Legendre
/// symbols, inversions) taken from the pinned table for the roster
/// curves, and every unit the table carries pinned over the measured
/// value.
fn calibration_for<G: CountedGroup>(
    g: &G,
    points: &[G::Elt],
    regime: &str,
    instance: &str,
    modulus: u64,
) -> (Calibration, PinOutcome) {
    let mut calib = Calibration::default();
    if !points.is_empty() {
        calibrate_group(g, points, &mut calib);
    }
    calibrate_row_ops(modulus, &mut calib);
    calib.ns_per_word_xor = Some(calibrate_word_xor());
    let pins = calib.pin(regime, instance);
    (calib, pins)
}

/// The binary regimes' calibration: the ledger's own measurement of
/// the group, the Artin–Schreier solve, the Frobenius map, the matrix
/// and the word XOR, then the pinned ratios where the table has this
/// instance.  A freshly generated random curve is not in the table, so
/// its base build is priced at the measured Artin–Schreier factor
/// rather than left at zero.
fn calibration_for_binary(inst: &BinaryInstance, regime: &str) -> (Calibration, PinOutcome) {
    let mut calib = calibrate_binary_instance(inst);
    calibrate_row_ops(inst.r, &mut calib);
    let pins = calib.pin(regime, &inst.name);
    (calib, pins)
}

fn sample_prime_points(inst: &PrimeInstance) -> Vec<crate::cryptanalysis::ic_boundary::PrimePoint> {
    let g = inst.generator_point();
    let mut ops = GroupOps::default();
    (1..=8u64).map(|k| inst.curve.mul(&mut ops, g, k)).collect()
}

/// The logarithm a configuration's `rep`-th repeat plants.
fn planted_log(seed: u64, rep: usize, r: u64) -> u64 {
    1 + (seed.wrapping_add(rep as u64 * 0x9E37)) % (r - 1)
}

/// One counted rho run.
#[derive(serde::Serialize)]
struct RhoRun {
    planted: u64,
    seed: u64,
    s: f64,
    /// Walk operations over `√r`: the part the `√(πr/2A)` floor is about.
    s_walk: f64,
    steps: u64,
    steps_over_expected: f64,
    verified: bool,
}

/// **The method boundary, measured on the instance.**  A counted Pollard
/// rho run on the logarithms the configurations plant, several walks
/// averaged because one rho run's cost is a draw from a wide
/// distribution.
#[derive(serde::Serialize)]
struct RhoReference {
    method: String,
    /// Automorphisms the walk uses: `2` for the negation map, `2n` for
    /// the signed Frobenius, `1` for the plain walk.
    automorphisms: u32,
    runs: usize,
    mean_s: f64,
    min_s: f64,
    max_s: f64,
    mean_s_walk: f64,
    all_verified: bool,
    per_run: Vec<RhoRun>,
}

/// `runs` rho runs of one walk on the configurations' planted
/// logarithms.  `walk(target, planted, seed, max_steps)` runs one; the
/// seeds and targets are the same for every walk, so two references on
/// one instance are paired.
///
/// The runs are independent (each has its own seed and target), so with
/// `threads > 1` they run concurrently and are collected in run order:
/// the reference is the serial one, sooner.
#[allow(clippy::too_many_arguments)]
fn rho_reference_for<G: CountedGroup + Sync>(
    g: &G,
    generator: G::Elt,
    r: u64,
    seed: u64,
    repeats: usize,
    runs: usize,
    threads: usize,
    walk: impl Fn(G::Elt, u64, u64, u64) -> RhoResult + Sync,
) -> Option<RhoReference>
where
    G::Elt: Send + Sync,
{
    use rayon::prelude::*;
    if runs == 0 || r < 3 {
        return None;
    }
    let max_steps = (generic_floor_ops(r as f64, 1.0) * 64.0) as u64 + 4096;
    let one = |k: usize| {
        let planted = planted_log(seed, k % repeats.max(1), r);
        let mut ops = GroupOps::default();
        let target = g.mul(&mut ops, generator, planted);
        let run_seed = seed ^ (0x5248_4F00 + k as u64);
        (
            planted,
            run_seed,
            walk(target, planted, run_seed, max_steps),
        )
    };
    let results: Vec<(u64, u64, RhoResult)> = if threads > 1 {
        rayon::ThreadPoolBuilder::new()
            .num_threads(threads)
            .build()
            .map(|pool| pool.install(|| (0..runs).into_par_iter().map(one).collect()))
            .unwrap_or_else(|_| (0..runs).map(one).collect())
    } else {
        (0..runs).map(one).collect()
    };
    let mut per_run = Vec::with_capacity(runs);
    let (mut method, mut automorphisms) = (String::new(), 1);
    for (planted, run_seed, res) in results {
        method = res.method.clone();
        automorphisms = res.automorphisms;
        per_run.push(RhoRun {
            planted,
            seed: run_seed,
            s: res.s,
            s_walk: res.s_walk,
            steps: res.steps,
            steps_over_expected: res.steps_over_expected,
            verified: res.verified && res.recovered == Some(planted),
        });
    }
    let s: Vec<f64> = per_run.iter().map(|r| r.s).collect();
    Some(RhoReference {
        method,
        automorphisms,
        runs,
        mean_s: s.iter().sum::<f64>() / runs as f64,
        min_s: s.iter().copied().fold(f64::INFINITY, f64::min),
        max_s: s.iter().copied().fold(0.0, f64::max),
        mean_s_walk: per_run.iter().map(|r| r.s_walk).sum::<f64>() / runs as f64,
        all_verified: per_run.iter().all(|r| r.verified),
        per_run,
    })
}

/// The references an instance is priced against.
struct RhoReferences {
    /// The matched reference: the `vs rho` column divides by its mean.
    matched: Option<RhoReference>,
    /// The plain walk (`A = 1`) every run was priced against through
    /// ledger §17, on the same seeds: the before mark.
    plain: Option<RhoReference>,
    /// The other eligible automorphism-aware walks that were run on the
    /// same seeds (Koblitz curves), kept beside the one chosen.
    candidates: Vec<RhoReference>,
    /// How the matched reference was chosen.
    rule: &'static str,
}

/// **The matched rho** (accounting contract, `comparison_contract.rho`):
/// the negation map on the prime and random binary curves; on a Koblitz
/// curve both eligible walks — the repository's signed-Frobenius walk
/// (`A = 2n`) and the negation walk — and the one with the lower mean
/// `S`, because on toy subgroups the signed walk's set-up (thirty-two
/// parallel walks started by scalar multiplications) outweighs what
/// the Frobenius saves.  The plain walk rides along as the before mark.
fn matched_rho(
    instance: &Instance,
    seed: u64,
    repeats: usize,
    runs: usize,
    threads: usize,
) -> RhoReferences {
    match instance {
        Instance::Prime(i) => {
            let (g, gen, r) = (&i.curve, i.generator_point(), i.r);
            RhoReferences {
                matched: rho_reference_for(
                    g,
                    gen,
                    r,
                    seed,
                    repeats,
                    runs,
                    threads,
                    |t, _, s, cap| rho_reference_negation(g, gen, t, r, s, cap),
                ),
                plain: rho_reference_for(
                    g,
                    gen,
                    r,
                    seed,
                    repeats,
                    runs,
                    threads,
                    |t, _, s, cap| rho_reference(g, gen, t, r, s, cap),
                ),
                candidates: Vec::new(),
                rule: "negation map (A = 2): the only eligible automorphism of this curve",
            }
        }
        Instance::Fp2(i) => {
            let (g, gen, r) = (&i.curve, i.generator, i.r);
            RhoReferences {
                matched: rho_reference_for(g, gen, r, seed, repeats, runs, threads, |t, _, s, cap| {
                    rho_reference_negation(g, gen, t, r, s, cap)
                }),
                plain: rho_reference_for(g, gen, r, seed, repeats, runs, threads, |t, _, s, cap| {
                    rho_reference(g, gen, t, r, s, cap)
                }),
                candidates: Vec::new(),
                rule: "negation map (A = 2): a generic curve over F_{p^2} not defined over F_p, so no Frobenius endomorphism acts on it; the negation is the only eligible automorphism",
            }
        }
        Instance::Binary(i) => {
            let bg = BinaryGroup(&i.fast);
            let (gen, r) = (i.generator, i.r);
            let negation =
                rho_reference_for(&bg, gen, r, seed, repeats, runs, threads, |t, _, s, cap| {
                    rho_reference_negation(&bg, gen, t, r, s, cap)
                });
            let plain =
                rho_reference_for(&bg, gen, r, seed, repeats, runs, threads, |t, _, s, cap| {
                    rho_reference(&bg, gen, t, r, s, cap)
                });
            if i.koblitz.is_none() {
                return RhoReferences {
                    matched: negation,
                    plain,
                    candidates: Vec::new(),
                    rule: "negation map (A = 2): the only eligible automorphism of this curve",
                };
            }
            let signed = rho_reference_for(
                &bg,
                gen,
                r,
                seed,
                repeats,
                runs,
                threads,
                |t, planted, s, _| {
                    signed_frobenius_rho(i, t, planted, s)
                        .expect("a Koblitz instance carries its curve")
                },
            );
            let mut candidates: Vec<RhoReference> = signed.into_iter().chain(negation).collect();
            // The cheaper of the eligible walks, among those that verified.
            let best = candidates
                .iter()
                .enumerate()
                .filter(|(_, c)| c.all_verified)
                .min_by(|a, b| a.1.mean_s.total_cmp(&b.1.mean_s))
                .map(|(k, _)| k);
            let matched = best.map(|k| candidates.remove(k));
            RhoReferences {
                matched,
                plain,
                candidates,
                rule: "Koblitz curve: the signed-Frobenius walk (A = 2n) and the negation walk (A = 2) on the same seeds; the lower mean S prices the column, the other is kept in rho_reference_candidates",
            }
        }
    }
}

/// One prime-field configuration, over `repeats` targets.
fn run_prime(
    inst: &PrimeInstance,
    spec: &PipelineSpec,
    args: &BenchArgs,
    calib: &Calibration,
    rho_s: Option<f64>,
) -> Result<Vec<RunReport>, String> {
    let fb_name = spec.factor_base.as_str();
    let or_name = spec.oracle.as_str();
    let abscissa = PrimeAbscissaBase { instance: inst };
    let hashed = HashedAffineBase { instance: inst };
    let base: &dyn FactorBaseBuilder<PrimeCurve> = match fb_name {
        "prime-abscissa" => &abscissa,
        "hashed-affine" => &hashed,
        other => {
            return Err(format!(
                "factor base `{other}` is not available on a prime-field curve; try prime-abscissa or hashed-affine"
            ))
        }
    };
    let mut out = Vec::new();
    for rep in 0..args.repeats.max(1) {
        let mut ops = GroupOps::default();
        let g = inst.generator_point();
        let planted = planted_log(spec.seed, rep, inst.r);
        let q = inst.curve.mul(&mut ops, g, planted);
        let ctx = InstanceCtx {
            group: &inst.curve,
            generator: g,
            target: q,
            r: inst.r,
            cofactor: inst.cofactor,
            group_order: inst.group_order,
            name: inst.name.clone(),
            field_degree: None,
        };
        let mut spec = spec.clone();
        spec.seed = spec.seed.wrapping_add(rep as u64 * 0x9E37);
        let m = spec.oracle_params.u64_or("m", 2)? as u32;
        let mut subtract = SubtractOracle;
        let mut mitm = MitmOracle::new(m);
        let mut hashed = HashedTensorOracle::new();
        let mut prime_batched = PrimeBatchMitmOracle::new(m);
        let mut rep_join = RepJoinOracle::new(m);
        let oracle: &mut dyn DecompositionOracle<_> = match or_name {
            "subtract" => &mut subtract,
            "mitm" => &mut mitm,
            "mitm-prime-batched" => &mut prime_batched,
            "rep-join" => &mut rep_join,
            "hashed-tensor" => &mut hashed,
            other => {
                return Err(format!(
                    "oracle `{other}` is not available on a prime-field curve; try subtract, mitm, rep-join or hashed-tensor"
                ))
            }
        };
        out.push(run_pipeline(
            &ctx, &spec, base, oracle, planted, calib, rho_s,
        )?);
    }
    Ok(out)
}

/// One binary or Koblitz configuration, over `repeats` targets.
fn run_binary(
    inst: &BinaryInstance,
    spec: &PipelineSpec,
    args: &BenchArgs,
    calib: &Calibration,
    rho_s: Option<f64>,
) -> Result<Vec<RunReport>, String> {
    let fb_name = spec.factor_base.as_str();
    let or_name = spec.oracle.as_str();
    let g = BinaryGroup(&inst.fast);
    let subspace = BinarySubspaceBase { instance: inst };
    let orbit = KoblitzOrbitBase { instance: inst };
    let base: &dyn FactorBaseBuilder<BinaryGroup> = match fb_name {
        "binary-subspace" => &subspace,
        "koblitz-orbit" => &orbit,
        other => {
            return Err(format!(
                "factor base `{other}` is not available on a binary curve; try binary-subspace or koblitz-orbit"
            ))
        }
    };
    let mut out = Vec::new();
    for rep in 0..args.repeats.max(1) {
        let mut ops = GroupOps::default();
        let planted = planted_log(spec.seed, rep, inst.r);
        let q = g.mul(&mut ops, inst.generator, planted);
        let ctx = InstanceCtx {
            group: &g,
            generator: inst.generator,
            target: q,
            r: inst.r,
            cofactor: inst.cofactor,
            group_order: inst.group_order,
            name: inst.name.clone(),
            field_degree: Some(inst.n),
        };
        let mut spec = spec.clone();
        spec.seed = spec.seed.wrapping_add(rep as u64 * 0x9E37);
        let m = spec.oracle_params.u64_or("m", 2)? as u32;
        let mut subtract = SubtractOracle;
        let mut subtract_binary =
            crate::cryptanalysis::ic_framework::binary_subtract::BinarySubtractOracle::new();
        let mut mitm = MitmOracle::new(m);
        let mut frob = FrobeniusMitmOracle::new(m, inst);
        let mut affine = AffineS3Oracle::new(inst);
        let mut chain_sat = ChainSatOracle::new(m, inst);
        let mut batch_mitm = BinaryBatchMitmOracle::default();
        let mut rep_join = RepJoinOracle::new(m);
        let mut algebraic = match or_name {
            "descent-algebraic" => {
                let raw = spec.solver.as_deref().ok_or(
                    "descent-algebraic needs --solver (try buchberger-f2, sat-cdcl or exhaustive)",
                )?;
                let (sname, sparams) = parse_plugin(raw)?;
                let budget = (spec.solver_budget_seconds > 0)
                    .then(|| std::time::Duration::from_secs(spec.solver_budget_seconds));
                Some(DescentAlgebraicOracle::new(
                    m,
                    inst,
                    solver_by_name(&sname)?,
                    sparams,
                    budget,
                ))
            }
            _ => None,
        };
        let oracle: &mut dyn DecompositionOracle<BinaryGroup> = match or_name {
            "subtract" => &mut subtract,
            "subtract-binary-batch" => &mut subtract_binary,
            "mitm" => &mut mitm,
            "mitm-frobenius" => &mut frob,
            "affine-s3" => &mut affine,
            "chain-sat" => &mut chain_sat,
            "mitm-batched" => &mut batch_mitm,
            "rep-join" => &mut rep_join,
            "descent-algebraic" => algebraic.as_mut().expect("built above"),
            other => return Err(format!("oracle `{other}` is not available here")),
        };
        out.push(run_pipeline(
            &ctx, &spec, base, oracle, planted, calib, rho_s,
        )?);
    }
    Ok(out)
}

/// One `F_{p²}` configuration, over `repeats` targets.
fn run_fp2(
    inst: &Fp2Instance,
    spec: &PipelineSpec,
    args: &BenchArgs,
    calib: &Calibration,
    rho_s: Option<f64>,
) -> Result<Vec<RunReport>, String> {
    let fb_name = spec.factor_base.as_str();
    let or_name = spec.oracle.as_str();
    let subfield = Fp2SubfieldBase { instance: inst };
    let base: &dyn FactorBaseBuilder<Fp2Curve> = match fb_name {
        "fp2-subfield" => &subfield,
        other => {
            return Err(format!(
                "factor base `{other}` is not available on an F_{{p^2}} curve; try fp2-subfield"
            ))
        }
    };
    let mut out = Vec::new();
    for rep in 0..args.repeats.max(1) {
        let mut ops = GroupOps::default();
        let g = inst.generator;
        let planted = planted_log(spec.seed, rep, inst.r);
        let q = inst.curve.mul(&mut ops, g, planted);
        let ctx = InstanceCtx {
            group: &inst.curve,
            generator: g,
            target: q,
            r: inst.r,
            cofactor: inst.cofactor,
            group_order: inst.group_order,
            name: inst.name.clone(),
            field_degree: None,
        };
        let mut spec = spec.clone();
        spec.seed = spec.seed.wrapping_add(rep as u64 * 0x9E37);
        let m = spec.oracle_params.u64_or("m", 2)? as u32;
        let mut subtract = SubtractOracle;
        let mut mitm = MitmOracle::new(m);
        let mut rep_join = RepJoinOracle::new(m);
        let mut weil = Fp2WeilOracle::new(inst);
        let oracle: &mut dyn DecompositionOracle<_> = match or_name {
            "subtract" => &mut subtract,
            "mitm" => &mut mitm,
            "rep-join" => &mut rep_join,
            "fp2-weil" => &mut weil,
            other => {
                return Err(format!(
                    "oracle `{other}` is not available on an F_{{p^2}} curve; try subtract, mitm, rep-join or fp2-weil"
                ))
            }
        };
        out.push(run_pipeline(
            &ctx, &spec, base, oracle, planted, calib, rho_s,
        )?);
    }
    Ok(out)
}

/// The instance a sweep runs every configuration on, built once.  The
/// binary instance carries its field tables, so it is boxed.
enum Instance {
    Prime(PrimeInstance),
    Binary(Box<BinaryInstance>),
    Fp2(Fp2Instance),
}

impl Instance {
    fn name(&self) -> &str {
        match self {
            Instance::Prime(i) => &i.name,
            Instance::Binary(i) => &i.name,
            Instance::Fp2(i) => &i.name,
        }
    }
}

/// A sweep file: one instance, and either an explicit list of
/// configurations or a matrix to take the product of.
#[derive(serde::Deserialize)]
struct SweepFile {
    instance: SweepInstance,
    #[serde(default)]
    repeats: Option<usize>,
    #[serde(default)]
    seed: Option<u64>,
    #[serde(default)]
    max_trials: Option<u64>,
    /// Explicit configurations, each a map of stage to plug-in spec.
    #[serde(default)]
    configurations: Vec<std::collections::BTreeMap<String, String>>,
    /// A matrix: every combination of the listed choices is run.
    #[serde(default)]
    matrix: std::collections::BTreeMap<String, Vec<String>>,
}

#[derive(serde::Deserialize)]
struct SweepInstance {
    regime: String,
    degree: u32,
    /// `char2` only: the largest cofactor the random curve may have;
    /// the `--max-cofactor` default when absent.
    #[serde(default)]
    max_cofactor: Option<u64>,
}

/// Every combination of the matrix, in a stable order.
fn expand_matrix(
    matrix: &std::collections::BTreeMap<String, Vec<String>>,
) -> Vec<std::collections::BTreeMap<String, String>> {
    let mut out = vec![std::collections::BTreeMap::new()];
    for (key, choices) in matrix {
        if choices.is_empty() {
            continue;
        }
        let mut next = Vec::with_capacity(out.len() * choices.len());
        for base in &out {
            for choice in choices {
                let mut row = base.clone();
                row.insert(key.clone(), choice.clone());
                next.push(row);
            }
        }
        out = next;
    }
    out
}

fn spec_from(
    cfg: &std::collections::BTreeMap<String, String>,
    defaults: &BenchArgs,
) -> Result<PipelineSpec, String> {
    let fb = cfg
        .get("factor_base")
        .cloned()
        .or_else(|| defaults.factor_base.clone())
        .ok_or("a configuration needs a `factor_base`")?;
    let or = cfg
        .get("oracle")
        .cloned()
        .or_else(|| defaults.oracle.clone())
        .ok_or("a configuration needs an `oracle`")?;
    let tg = cfg
        .get("targets")
        .cloned()
        .unwrap_or_else(|| defaults.targets.clone());
    let (fb_name, fb_params) = parse_plugin(&fb)?;
    let (or_name, or_params) = parse_plugin(&or)?;
    Ok(PipelineSpec {
        factor_base: fb_name,
        factor_base_params: fb_params,
        oracle: or_name,
        oracle_params: or_params,
        solver: cfg
            .get("solver")
            .cloned()
            .or_else(|| defaults.solver.clone()),
        solver_params: Params::default(),
        targets: Targets::parse(&tg)?,
        linalg: cfg
            .get("linalg")
            .cloned()
            .unwrap_or_else(|| defaults.linalg.clone()),
        max_trials: defaults.max_trials,
        seed: defaults.seed,
        solver_budget_seconds: defaults.solver_budget_seconds,
        threads: resolve_threads(defaults.threads),
    })
}

// ── Checking a configuration before any work ───────────────────────

/// Edit distance, for "did you mean".
fn edit_distance(a: &str, b: &str) -> usize {
    let b: Vec<char> = b.chars().collect();
    let mut row: Vec<usize> = (0..=b.len()).collect();
    for (i, ca) in a.chars().enumerate() {
        let mut prev = row[0];
        row[0] = i + 1;
        for (j, &cb) in b.iter().enumerate() {
            let cur = row[j + 1];
            row[j + 1] = (prev + usize::from(ca != cb)).min(row[j] + 1).min(cur + 1);
            prev = cur;
        }
    }
    row[b.len()]
}

/// The closest of `candidates` to `word`, when it is close enough to be a typo.
fn did_you_mean<'a>(word: &str, candidates: impl IntoIterator<Item = &'a str>) -> Option<&'a str> {
    let limit = (word.chars().count() / 3).max(2);
    candidates
        .into_iter()
        .map(|c| (edit_distance(word, c), c))
        .filter(|(d, _)| *d <= limit)
        .min_by_key(|(d, _)| *d)
        .map(|(_, c)| c)
}

fn hint(word: &str, candidates: &[&str]) -> String {
    match did_you_mean(word, candidates.iter().copied()) {
        Some(c) => format!("; did you mean `{c}`?"),
        None => format!("; choose one of {}", candidates.join(", ")),
    }
}

/// What checking a configuration up front found.
#[derive(Debug, Default, PartialEq)]
struct Checked {
    /// The configuration cannot mean anything: a misspelt name or key, a
    /// summand count the oracle does not take.  Fatal before any work.
    errors: Vec<String>,
    /// Real plug-ins that do not apply to this regime.  Fatal for a
    /// single configuration; a sweep matrix reports them as skipped.
    inapplicable: Vec<String>,
    /// Keys the catalogue does not declare and nothing resembles: passed
    /// through to the plug-in, which may read them, with a note.
    warnings: Vec<String>,
}

/// Summand counts a catalogue entry admits: `2`, `"2"`, `"2 or 3"`, `"2..8"`.
fn summand_range(v: &Value) -> Option<(u64, u64)> {
    if let Some(n) = v.as_u64() {
        return Some((n, n));
    }
    let s = v.as_str()?.replace(' ', "");
    if let Some((a, b)) = s.split_once("..") {
        return Some((
            a.trim_start_matches('=').parse().ok()?,
            b.trim_start_matches('=').parse().ok()?,
        ));
    }
    if let Some((a, b)) = s.split_once("or") {
        return Some((a.parse().ok()?, b.parse().ok()?));
    }
    let n = s.parse().ok()?;
    Some((n, n))
}

/// Check one stage's plug-in against the catalogue: its name, regime and
/// parameter keys.  Returns the catalogue entry when the name is known.
fn check_plugin<'c>(
    stage_label: &str,
    flag: &str,
    name: &str,
    params: &Params,
    regime: &str,
    entries: &'c [Value],
    implicit: &[&str],
    out: &mut Checked,
) -> Option<&'c Value> {
    let names: Vec<&str> = entries.iter().filter_map(|e| e["name"].as_str()).collect();
    let Some(entry) = entries.iter().find(|e| e["name"] == name) else {
        out.errors.push(format!(
            "unknown {stage_label} `{name}` ({flag}){}",
            hint(name, &names)
        ));
        return None;
    };
    if let Some(regimes) = entry["regimes"].as_array() {
        if !regimes.iter().any(|r| r == regime) {
            let here: Vec<&str> = entries
                .iter()
                .filter(|e| {
                    e["regimes"]
                        .as_array()
                        .is_some_and(|rs| rs.iter().any(|r| r == regime))
                })
                .filter_map(|e| e["name"].as_str())
                .collect();
            let on: Vec<&str> = regimes.iter().filter_map(|r| r.as_str()).collect();
            out.inapplicable.push(format!(
                "{stage_label} `{name}` runs on {} curves, not {regime}; on {regime} use {}",
                on.join("/"),
                here.join(", ")
            ));
        }
    }
    let mut declared: Vec<&str> = entry["parameters"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|p| p["name"].as_str())
        .collect();
    for k in implicit {
        if !declared.contains(k) {
            declared.push(k);
        }
    }
    for key in params.0.keys() {
        if declared.contains(&key.as_str()) {
            continue;
        }
        match did_you_mean(key, declared.iter().copied()) {
            Some(c) => out.errors.push(format!(
                "{stage_label} `{name}` has no parameter `{key}`; did you mean `{c}`?"
            )),
            None => out.warnings.push(format!(
                "{stage_label} `{name}` does not declare `{key}` (declared: {}); passing it through",
                if declared.is_empty() { "none".to_string() } else { declared.join(", ") }
            )),
        }
    }
    Some(entry)
}

/// Check a whole configuration against `ic bench --list`, the regime and
/// the CLI defaults.  Nothing is built or run.
fn check_config(
    cfg: &std::collections::BTreeMap<String, String>,
    args: &BenchArgs,
    regime: &str,
    catalogue: &Value,
) -> Checked {
    let mut out = Checked::default();
    let stage = |name: &str| -> Vec<Value> {
        catalogue["stages"]
            .as_array()
            .into_iter()
            .flatten()
            .find(|s| s["stage"] == name)
            .and_then(|s| s["plugins"].as_array().cloned())
            .unwrap_or_default()
    };
    for key in cfg.keys() {
        const KEYS: &[&str] = &["factor_base", "oracle", "targets", "solver", "linalg"];
        if !KEYS.contains(&key.as_str()) {
            out.errors.push(format!(
                "configuration key `{key}` is not one of {}{}",
                KEYS.join(", "),
                hint(key, KEYS)
                    .split(';')
                    .next_back()
                    .map(|h| format!(";{h}"))
                    .unwrap_or_default()
            ));
        }
    }
    let fb = cfg.get("factor_base").or(args.factor_base.as_ref());
    let or = cfg.get("oracle").or(args.oracle.as_ref());
    match fb {
        None => out.errors.push(
            "no factor base: pass --factor-base NAME[:k=v,...] (ic bench --list shows them)".into(),
        ),
        Some(raw) => match parse_plugin(raw) {
            Err(e) => out.errors.push(format!("--factor-base `{raw}`: {e}")),
            Ok((name, params)) => {
                check_plugin(
                    "factor base",
                    "--factor-base",
                    &name,
                    &params,
                    regime,
                    &stage("factor base"),
                    &[],
                    &mut out,
                );
            }
        },
    }
    match or {
        None => out.errors.push(
            "no decomposition oracle: pass --oracle NAME[:k=v,...] (ic bench --list shows them)"
                .into(),
        ),
        Some(raw) => match parse_plugin(raw) {
            Err(e) => out.errors.push(format!("--oracle `{raw}`: {e}")),
            Ok((name, params)) => {
                let entries = stage("point decomposition");
                // Every oracle may be given `m`: the runner reads it for all of them.
                if let Some(entry) = check_plugin(
                    "oracle",
                    "--oracle",
                    &name,
                    &params,
                    regime,
                    &entries,
                    &["m"],
                    &mut out,
                ) {
                    if let Some(raw_m) = params.get("m") {
                        match raw_m.parse::<u64>() {
                            Err(_) => out
                                .errors
                                .push(format!("oracle `{name}`: m = `{raw_m}` is not a number")),
                            Ok(m) => {
                                if let Some((lo, hi)) = summand_range(&entry["summands"]) {
                                    if m < lo || m > hi {
                                        let takes = if lo == hi {
                                            format!("m = {lo}")
                                        } else if hi == lo + 1 {
                                            format!("m = {lo} or {hi}")
                                        } else {
                                            format!("m = {lo}..{hi}")
                                        };
                                        out.errors.push(format!(
                                            "oracle `{name}` takes {takes}, not m = {m}"
                                        ));
                                    }
                                }
                            }
                        }
                    }
                    let algebraic = entry["needs"]
                        .as_str()
                        .is_some_and(|n| n.contains("--solver"));
                    let solver = cfg.get("solver").or(args.solver.as_ref());
                    if algebraic && solver.is_none() {
                        out.errors.push(format!("oracle `{name}` needs --solver NAME (ic bench --list shows the engines)"));
                    }
                    if !algebraic
                        && solver.is_some()
                        && cfg.get("solver").is_none()
                        && args.sweep.is_none()
                    {
                        out.warnings.push(format!(
                            "oracle `{name}` solves no polynomial system; --solver is ignored"
                        ));
                    }
                }
            }
        },
    }
    let tg = cfg.get("targets").unwrap_or(&args.targets);
    if Targets::parse(tg).is_err() {
        const TARGETS: &[&str] = &[
            "random",
            "walk",
            "walk-batch16",
            "walk-batch16-scalar",
            "walk-batch16-vector",
            "walk-batch16-vector-inverse",
        ];
        out.errors.push(format!(
            "unknown target source `{tg}` (--targets){}",
            hint(tg, TARGETS)
        ));
    }
    let la = cfg.get("linalg").unwrap_or(&args.linalg);
    let matrices: Vec<&str> = MATRIX_NAMES.iter().map(|(n, _)| *n).collect();
    if !la.is_empty() && !matrices.contains(&la.as_str()) {
        out.errors.push(format!(
            "unknown relation matrix `{la}` (--linalg){}",
            hint(la, &matrices)
        ));
    }
    if let Some(raw) = cfg.get("solver").or(args.solver.as_ref()) {
        if let Ok((name, _)) = parse_plugin(raw) {
            if solver_by_name(&name).is_err() {
                let names: Vec<String> = solver_registry()
                    .iter()
                    .map(|s| s.name().to_string())
                    .collect();
                let refs: Vec<&str> = names.iter().map(|s| s.as_str()).collect();
                out.errors.push(format!(
                    "unknown solver `{name}` (--solver){}",
                    hint(&name, &refs)
                ));
            }
        }
    }
    out
}

/// `--threads 0` is every core this process may run on.
fn resolve_threads(threads: usize) -> usize {
    if threads == 0 {
        std::thread::available_parallelism().map_or(1, |n| n.get())
    } else {
        threads
    }
}

pub fn run(args: BenchArgs, json_only: bool) -> Result<Value, String> {
    if args.list {
        let l = listing();
        return Ok(json!({
            "schema_version": 1,
            "operation": "bench-list",
            "status": "complete",
            "registry": l,
        }));
    }

    // Either a sweep file or the flags describe the work.
    let (instance_spec, configs, args) = match &args.sweep {
        Some(path) => {
            let raw = std::fs::read_to_string(path)
                .map_err(|e| format!("cannot read sweep file {}: {e}", path.display()))?;
            let file: SweepFile = serde_json::from_str(&raw)
                .map_err(|e| format!("sweep file {} is not valid: {e}", path.display()))?;
            let mut a = args.clone();
            if let Some(v) = file.repeats {
                a.repeats = v;
            }
            if let Some(v) = file.seed {
                a.seed = v;
            }
            if let Some(v) = file.max_trials {
                a.max_trials = v;
            }
            if let Some(v) = file.instance.max_cofactor {
                a.max_cofactor = v;
            }
            let mut configs = file.configurations.clone();
            configs.extend(expand_matrix(&file.matrix));
            if configs.is_empty() {
                return Err("the sweep file lists no configurations and no matrix".into());
            }
            (
                (file.instance.regime.clone(), file.instance.degree),
                configs,
                a,
            )
        }
        None => {
            let (regime, degree) = match (
                args.bits,
                args.char2_degree,
                args.koblitz_degree,
                args.fp2_bits,
            ) {
                (Some(b), None, None, None) => ("prime".to_string(), b),
                (None, Some(n), None, None) => ("char2".to_string(), n),
                (None, None, Some(n), None) => ("koblitz".to_string(), n),
                (None, None, None, Some(k)) => ("fp2".to_string(), k),
                _ => return Err(
                    "choose exactly one of --bits, --char2-degree, --koblitz-degree, --fp2-bits, or --sweep"
                        .into(),
                ),
            };
            let mut one = std::collections::BTreeMap::new();
            if let Some(v) = &args.factor_base {
                one.insert("factor_base".to_string(), v.clone());
            }
            if let Some(v) = &args.oracle {
                one.insert("oracle".to_string(), v.clone());
            }
            one.insert("targets".to_string(), args.targets.clone());
            ((regime, degree), vec![one], args.clone())
        }
    };

    // Every configuration is checked against the catalogue before the
    // instance, the calibration or the rho runs: a misspelt name or key,
    // or a summand count an oracle does not take, fails in milliseconds
    // with a suggestion instead of after minutes as a skipped row.
    let catalogue = listing();
    let mut usage: Vec<String> = Vec::new();
    let mut inapplicable: Vec<Value> = Vec::new();
    let sweep = args.sweep.is_some();
    for (k, cfg) in configs.iter().enumerate() {
        let checked = check_config(cfg, &args, &instance_spec.0, &catalogue);
        let at = |m: &String| {
            if configs.len() > 1 {
                format!("configuration {}: {m}", k + 1)
            } else {
                m.clone()
            }
        };
        usage.extend(checked.errors.iter().map(at));
        if sweep {
            if !checked.inapplicable.is_empty() && checked.errors.is_empty() {
                inapplicable.push(json!({"index": k, "why": checked.inapplicable.join("; ")}));
            }
        } else {
            usage.extend(checked.inapplicable.iter().map(at));
        }
        if !json_only {
            for w in &checked.warnings {
                eprintln!("ic bench: note: {}", at(w));
            }
        }
    }
    if !usage.is_empty() {
        return Err(format!(
            "usage: ic bench was not started:\n  {}\n(ic bench --list shows every plug-in, its parameters and the regimes it runs on)",
            usage.join("\n  ")
        ));
    }
    if !json_only {
        for s in &inapplicable {
            eprintln!(
                "ic bench: configuration {} will be skipped: {}",
                s["index"].as_u64().unwrap_or(0) + 1,
                s["why"].as_str().unwrap_or("")
            );
        }
    }

    // A sweep may override the CLI default solver per configuration.
    // Reject malformed SAT encoding before calibrations, rho or a target.
    for cfg in &configs {
        if let Some(raw) = cfg.get("solver").or(args.solver.as_ref()) {
            let (name, params) = parse_plugin(raw)?;
            solver_by_name(&name)?;
            validate_solver_params(&name, &params)?;
        }
    }

    let (regime, degree) = instance_spec;
    let instance = match regime.as_str() {
        "prime" => Instance::Prime(
            roster_prime_instance(degree)
                .or_else(|| {
                    (8..=32)
                        .contains(&degree)
                        .then(|| find_prime_order_curve(degree, args.seed))
                })
                .ok_or_else(|| format!("no prime instance at {degree} bits"))?,
        ),
        "char2" => Instance::Binary(Box::new(
            random_binary_instance(degree, args.seed, args.max_cofactor).ok_or_else(|| {
                format!(
                    "no random binary instance at degree {degree} with cofactor at most {}",
                    args.max_cofactor
                )
            })?,
        )),
        "koblitz" => Instance::Binary(Box::new(
            koblitz_instance(1, degree)
                .or_else(|| koblitz_instance(0, degree))
                .ok_or_else(|| format!("no Koblitz instance at degree {degree}"))?,
        )),
        "fp2" => Instance::Fp2(find_fp2_curve(degree, args.seed, args.max_cofactor).ok_or_else(
            || {
                format!(
                    "no F_{{p^2}} instance at {degree} bits (12..=60) with cofactor at most {}",
                    args.max_cofactor
                )
            },
        )?),
        other => {
            return Err(format!(
                "unknown regime `{other}`; try prime, char2, koblitz or fp2"
            ))
        }
    };

    let (calib, pins) = match &instance {
        Instance::Prime(i) => {
            calibration_for(&i.curve, &sample_prime_points(i), "prime", &i.name, i.r)
        }
        Instance::Binary(i) => calibration_for_binary(i, &regime),
        Instance::Fp2(i) => {
            let mut ops = GroupOps::default();
            let points: Vec<_> = (1..=8u64)
                .map(|k| i.curve.mul(&mut ops, i.generator, k))
                .collect();
            let (mut calib, _) = calibration_for(&i.curve, &points, "fp2", &i.name, i.r);
            // The F_p units the fp2 base and the fp2-weil oracle count.
            // The repository's table has no fp2 entry, so every factor is
            // this host's measurement; re-pin to record that.
            calibrate_fp_units(i.p(), &mut calib);
            // One pair-table probe, measured on a real table over a small
            // subfield base.  (The prime path leaves this unit at the
            // pinned ratio, or zero on a generated curve; measuring it here
            // keeps the oracles' lookups from being free.)
            let small = crate::cryptanalysis::ic_fp2::fp2_subfield_factor_base(i, Some(64));
            calib.ns_per_lookup =
                crate::cryptanalysis::ic_boundary::PairTable::build(&i.curve, &small)
                    .calibrate_lookup(1_000_000);
            let pins = calib.pin("fp2", &i.name);
            (calib, pins)
        }
    };

    let started = std::time::Instant::now();
    // The method boundary on this instance, before any configuration:
    // every row's `vs rho` is its S over the matched reference's mean.
    let references = matched_rho(
        &instance,
        args.seed,
        args.repeats,
        args.rho_runs,
        resolve_threads(args.threads),
    );
    let rho = &references.matched;
    let rho_s = rho.as_ref().filter(|r| r.all_verified).map(|r| r.mean_s);
    if !json_only {
        if let Some(r) = rho {
            eprintln!(
                "  rho reference (A = {}): S = {:.3} (mean of {}, {:.3}–{:.3}){}",
                r.automorphisms,
                r.mean_s,
                r.runs,
                r.min_s,
                r.max_s,
                if r.all_verified {
                    ""
                } else {
                    " — a run failed to verify; the column is left empty"
                }
            );
        }
        if let Some(p) = &references.plain {
            eprintln!("  before mark, plain walk (A = 1): S = {:.3}", p.mean_s);
        }
        for c in &references.candidates {
            eprintln!("  also run (A = {}): S = {:.3}", c.automorphisms, c.mean_s);
        }
    }
    let mut rows: Vec<RunReport> = Vec::new();
    let mut failures: Vec<Value> = Vec::new();
    for cfg in &configs {
        let spec = spec_from(cfg, &args)?;
        if !json_only {
            eprintln!("  {} …", spec.label());
        }
        // A configuration that does not apply to this regime is
        // reported, not fatal: a sweep over a matrix will contain
        // combinations that do not exist, and the useful output is the
        // ones that do plus a note on the ones that do not.
        let outcome = match &instance {
            Instance::Prime(i) => run_prime(i, &spec, &args, &calib, rho_s),
            Instance::Binary(i) => run_binary(i, &spec, &args, &calib, rho_s),
            Instance::Fp2(i) => run_fp2(i, &spec, &args, &calib, rho_s),
        };
        match outcome {
            Ok(mut got) => rows.append(&mut got),
            Err(why) => failures.push(json!({"configuration": spec.label(), "why": why})),
        }
    }

    let all_verified = !rows.is_empty() && rows.iter().all(|r| r.verified);
    let markdown = format_markdown(&rows);
    if !json_only {
        eprintln!("\n{markdown}");
        for f in &failures {
            eprintln!(
                "  skipped: {} — {}",
                f["configuration"].as_str().unwrap_or("?"),
                f["why"].as_str().unwrap_or("no reason given")
            );
        }
    }
    let mut report = json!({
        "schema_version": 1,
        "operation": "bench",
        "status": if all_verified { "complete" } else { "incomplete" },
        "what_this_is": "Index-calculus configurations -- each a choice of factor base, target source, decomposition oracle, polynomial solver and relation matrix -- run end to end against a planted logarithm, with every stage's cost in group-addition equivalents and the total divided by sqrt(r).",
        "what_this_is_not": [
            "not a speed claim: a configuration on a toy instance is a measurement, and a comparison needs the matched reference rows AGENTS.md section 1 asks for",
            "not a wall-clock benchmark: operation counts are the metric, wall time rides along",
            "not a claim about any deployed curve"
        ],
        "instance": instance.name(),
        "regime": regime,
        // The conversion every non-addition unit was priced at, so a
        // frozen report re-derives its own GAE: nanoseconds per unit on
        // this host, with the units the repository's table pinned over
        // the measurement named apart from the ones left measured.
        "calibration": calib,
        "calibration_pins": pins,
        "rho_reference": rho,
        "rho_reference_rule": references.rule,
        "rho_reference_plain": references.plain,
        "rho_reference_candidates": references.candidates,
        "configurations_run": rows.len(),
        "configurations_skipped": failures,
        "all_verified": all_verified,
        "elapsed_seconds": started.elapsed().as_secs_f64(),
        "markdown": markdown,
        "rows": rows,
    });
    // An F_{p^2} curve is generated, not a roster entry: record its
    // field, coefficients and generator so the instance can be rebuilt.
    if let Instance::Fp2(i) = &instance {
        report["instance_detail"] = i.describe();
    }
    Ok(report)
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;

    #[derive(Parser)]
    struct Wrap {
        #[command(flatten)]
        args: BenchArgs,
    }

    fn args(extra: &[&str]) -> BenchArgs {
        let mut v = vec!["bench"];
        v.extend_from_slice(extra);
        Wrap::parse_from(v).args
    }

    fn one(a: &BenchArgs) -> std::collections::BTreeMap<String, String> {
        let mut c = std::collections::BTreeMap::new();
        if let Some(v) = &a.factor_base {
            c.insert("factor_base".into(), v.clone());
        }
        if let Some(v) = &a.oracle {
            c.insert("oracle".into(), v.clone());
        }
        c.insert("targets".into(), a.targets.clone());
        c
    }

    fn check(regime: &str, flags: &[&str]) -> Checked {
        let a = args(flags);
        check_config(&one(&a), &a, regime, &listing())
    }

    #[test]
    fn a_typo_is_caught_with_the_name_it_meant() {
        assert_eq!(did_you_mean("mitmm", ["mitm", "subtract"]), Some("mitm"));
        assert_eq!(
            did_you_mean("prime-abscisa", ["prime-abscissa"]),
            Some("prime-abscissa")
        );
        assert_eq!(did_you_mean("zzz", ["mitm", "subtract"]), None);
        let c = check(
            "prime",
            &[
                "--factor-base",
                "prime-abscisa:sise=40",
                "--oracle",
                "mitmm",
                "--targets",
                "walkk",
            ],
        );
        let all = c.errors.join("\n");
        assert!(all.contains("did you mean `prime-abscissa`"), "{all}");
        assert!(all.contains("did you mean `mitm`"), "{all}");
        assert!(all.contains("did you mean `walk`"), "{all}");
        let c = check(
            "prime",
            &[
                "--factor-base",
                "prime-abscissa:sise=40",
                "--oracle",
                "mitm",
            ],
        );
        assert!(
            c.errors.join("\n").contains("did you mean `size`"),
            "{:?}",
            c.errors
        );
    }

    #[test]
    fn a_summand_count_the_oracle_does_not_take_is_refused() {
        assert_eq!(summand_range(&json!(2)), Some((2, 2)));
        assert_eq!(summand_range(&json!("2 or 3")), Some((2, 3)));
        assert_eq!(summand_range(&json!("2..8")), Some((2, 8)));
        let c = check(
            "prime",
            &[
                "--factor-base",
                "prime-abscissa:size=40",
                "--oracle",
                "mitm:m=9",
            ],
        );
        assert_eq!(
            c.errors,
            vec!["oracle `mitm` takes m = 2 or 3, not m = 9".to_string()]
        );
        assert!(check(
            "prime",
            &[
                "--factor-base",
                "prime-abscissa:size=40",
                "--oracle",
                "mitm:m=3"
            ]
        )
        .errors
        .is_empty());
    }

    #[test]
    fn a_plugin_from_another_regime_is_named_with_the_ones_that_apply() {
        let c = check(
            "prime",
            &[
                "--factor-base",
                "binary-subspace:dimension=6",
                "--oracle",
                "mitm",
            ],
        );
        assert!(c.errors.is_empty(), "{:?}", c.errors);
        assert_eq!(c.inapplicable.len(), 1);
        assert!(
            c.inapplicable[0].contains("on prime use prime-abscissa"),
            "{}",
            c.inapplicable[0]
        );
    }

    #[test]
    fn an_undeclared_key_nothing_resembles_passes_through_with_a_note() {
        let c = check(
            "prime",
            &[
                "--factor-base",
                "prime-abscissa:size=40",
                "--oracle",
                "mitm:frob=1",
            ],
        );
        assert!(c.errors.is_empty(), "{:?}", c.errors);
        assert_eq!(c.warnings.len(), 1);
    }

    #[test]
    fn an_algebraic_oracle_without_a_solver_is_refused_before_any_work() {
        let c = check(
            "char2",
            &[
                "--factor-base",
                "binary-subspace:dimension=6",
                "--oracle",
                "descent-algebraic",
            ],
        );
        assert!(
            c.errors.join("\n").contains("needs --solver"),
            "{:?}",
            c.errors
        );
        let c = check(
            "char2",
            &[
                "--factor-base",
                "binary-subspace:dimension=6",
                "--oracle",
                "descent-algebraic",
                "--solver",
                "f4f2",
            ],
        );
        assert!(
            c.errors.join("\n").contains("did you mean `f4-f2`"),
            "{:?}",
            c.errors
        );
    }

    /// The check must not refuse anything the committed sweeps run.
    #[test]
    fn every_committed_sweep_passes_the_check() {
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("docs/ic/sweeps");
        let mut seen = 0;
        for entry in std::fs::read_dir(&dir).unwrap() {
            let path = entry.unwrap().path();
            if path.extension().is_none_or(|e| e != "json") {
                continue;
            }
            let file: SweepFile =
                serde_json::from_str(&std::fs::read_to_string(&path).unwrap()).unwrap();
            let mut configs = file.configurations.clone();
            configs.extend(expand_matrix(&file.matrix));
            let a = args(&[]);
            for cfg in &configs {
                let c = check_config(cfg, &a, &file.instance.regime, &listing());
                assert!(
                    c.errors.is_empty(),
                    "{}: {cfg:?}: {:?}",
                    path.display(),
                    c.errors
                );
            }
            seen += 1;
        }
        assert!(seen > 0);
    }
}
