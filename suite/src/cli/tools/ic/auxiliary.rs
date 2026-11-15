//! Bounded native auxiliary-map IC, with an explicit public-relation replay mode.
use super::{binary_hash, experiment, git_commit};
use crate::cryptanalysis::prime_auxiliary_index_calculus as aux;
use clap::{Args, ValueEnum};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{
    fs::File,
    io::Read,
    path::{Path, PathBuf},
    time::{Duration, Instant},
};

#[derive(Clone, Copy, Debug, ValueEnum)]
pub enum BackendArg {
    Auto,
    Scalar,
    Avx2,
    Avx512,
}
impl From<BackendArg> for aux::Backend {
    fn from(value: BackendArg) -> Self {
        match value {
            BackendArg::Auto => Self::Auto,
            BackendArg::Scalar => Self::Scalar,
            BackendArg::Avx2 => Self::Avx2,
            BackendArg::Avx512 => Self::Avx512,
        }
    }
}

#[derive(Clone, Debug, Args)]
pub struct AuxiliaryArgs {
    /// Public curve, target, complete auxiliary-map fiber and raw roots (JSON).
    #[arg(long)]
    pub input: PathBuf,
    /// Exact circuit backend; auto detects available SIMD, with a scalar fallback.
    #[arg(long, value_enum, default_value_t = BackendArg::Auto)]
    pub backend: BackendArg,
    /// Use batched direct subtraction without auxiliary maps. Reuse this input
    /// for a same-base control, or supply arbitrary roots without an auxiliary block.
    #[arg(long)]
    pub without_auxiliary: bool,
    /// Generate a power-map fiber of this degree (divides p-1; factors 2,3,7).
    #[arg(long, conflicts_with = "torus_depth", value_parser = clap::value_parser!(u32).range(2..=1_048_576))]
    pub multiplicative_degree: Option<u32>,
    /// Nonzero coset representative for --multiplicative-degree (default 1).
    #[arg(long, requires = "multiplicative_degree")]
    pub coset: Option<u64>,
    /// Generate a norm-one trace fiber of iterated x^2-2, with 2^depth roots.
    #[arg(long, conflicts_with = "multiplicative_degree", value_parser = clap::value_parser!(u8).range(1..=20))]
    pub torus_depth: Option<u8>,
    /// Explicit primitive norm-one trace; otherwise use bounded deterministic search.
    #[arg(long, requires = "torus_depth")]
    pub torus_trace: Option<u64>,
    /// Public coefficient sampler seed; never a target logarithm.
    #[arg(long, default_value_t = 0)]
    pub seed: u64,
    /// Processed-query cap, including failed queries and infinity targets.
    #[arg(long, default_value_t = 1_000_000)]
    pub max_queries: u64,
    /// Independent target walks sharing an inversion, 1..=1024.
    #[arg(long, default_value_t = 64, value_parser = clap::value_parser!(u16).range(1..=1024))]
    pub walk_lanes: u16,
    /// Distinct-row cap; zero chooses 4*columns+64.
    #[arg(long, default_value_t = 0)]
    pub max_relations: usize,
    /// Certificate DAG node cap.
    #[arg(long, default_value_t = 4_194_304)]
    pub max_proof_nodes: usize,
    /// Soft online deadline, checked between complete lane batches.
    #[arg(long)]
    pub max_millis: Option<u64>,
    /// Recover from existing public aG+bQ=±Fi±Fj rows (JSONL), with no search.
    /// This is certificate replay, not an attack-time or relation-yield measurement.
    #[arg(long, conflicts_with_all = ["decompose_only", "rho"])]
    pub replay_relations: Option<PathBuf>,
    /// Find a signed decomposition of Q without starting relation collection.
    #[arg(long, conflicts_with = "rho")]
    pub decompose_only: bool,
    /// Also run the repository's bounded batched, negation-map rho on this Q.
    #[arg(long)]
    pub rho: bool,
    /// Group-operation cap for the optional rho reference.
    #[arg(long, default_value_t = 10_000_000, value_parser = clap::value_parser!(u64).range(1..))]
    pub rho_max_ops: u64,
}

#[derive(Deserialize)]
struct Public {
    p: u64,
    a: u64,
    b: u64,
    n: u64,
    #[serde(rename = "P")]
    generator: [u64; 2],
    #[serde(rename = "Q")]
    target: [u64; 2],
}
#[derive(Deserialize)]
struct Map {
    r: u64,
    #[serde(rename = "A", alias = "offset")]
    offset: u64,
    #[serde(rename = "B", alias = "residue")]
    residue: u64,
}
#[derive(Deserialize)]
struct Encoding {
    p: u64,
    maps: Vec<Map>,
    terminal_c: u64,
    root_count: Option<usize>,
}
#[derive(Deserialize)]
struct Input {
    public: Public,
    auxiliary: Option<Encoding>,
    #[serde(default, alias = "roots")]
    structured_roots: Vec<u64>,
}
#[derive(Deserialize)]
struct ImportedRow {
    a: u64,
    b: u64,
    i: usize,
    j: usize,
    si: i8,
    sj: i8,
}

fn read_bounded(path: &Path) -> Result<Vec<u8>, String> {
    const LIMIT: u64 = 64 << 20;
    let mut bytes = Vec::new();
    File::open(path)
        .map_err(|e| format!("{}: {e}", path.display()))?
        .take(LIMIT + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() as u64 > LIMIT {
        return Err("input exceeds the 64 MiB envelope".into());
    }
    Ok(bytes)
}
fn row_json(row: &aux::Relation) -> Value {
    let d = row.decomposition;
    json!({"a":row.a,"b":row.b,"i":d.i,"j":d.j,"si":if d.negative_i {-1} else {1},"sj":if d.negative_j {-1} else {1}})
}
fn certificate_json(certificate: &aux::Certificate) -> Value {
    json!({"order":certificate.order,"P":certificate.generator.coordinates(),"Q":certificate.target.coordinates(),
        "scalar":certificate.scalar,"relations":certificate.relations.iter().map(row_json).collect::<Vec<_>>(),"weights":certificate.weights})
}
fn stats_json(stats: &aux::SearchStats) -> Value {
    json!({"queries":stats.queries,"generated_targets":stats.generated_targets,"circuit_queries":stats.circuit_queries,
        "lane_rounds":stats.lane_rounds,"relations":stats.relations,"duplicate_rows":stats.duplicate_rows,
        "matrix_rank":stats.matrix_rank,"proof_nodes":stats.proof_nodes,"backend":stats.backend.name()})
}

pub fn run(args: AuxiliaryArgs) -> Result<Value, String> {
    let started = Instant::now();
    let bytes = read_bounded(&args.input)?;
    let input: Input = serde_json::from_slice(&bytes).map_err(|e| format!("public input: {e}"))?;
    if let Some(encoding) = &input.auxiliary {
        if input.public.p != encoding.p {
            return Err("target and auxiliary fields differ".into());
        }
        if encoding
            .root_count
            .is_some_and(|n| n != input.structured_roots.len())
        {
            return Err("declared root count differs from supplied roots".into());
        }
    }
    let digest = blake3::hash(&bytes).to_hex().to_string();
    match input.public.p {
        7 => execute::<3>(&args, &input, digest, started),
        31 => execute::<5>(&args, &input, digest, started),
        127 => execute::<7>(&args, &input, digest, started),
        8191 => execute::<13>(&args, &input, digest, started),
        131071 => execute::<17>(&args, &input, digest, started),
        524287 => execute::<19>(&args, &input, digest, started),
        2147483647 => execute::<31>(&args, &input, digest, started),
        2305843009213693951 => execute::<61>(&args, &input, digest, started),
        _ => Err("this solver requires a supported Mersenne prime field".into()),
    }
}

fn encoding_json(encoding: aux::FactorBaseEncoding) -> Value {
    match encoding {
        aux::FactorBaseEncoding::Direct => json!({"kind":"direct"}),
        aux::FactorBaseEncoding::Auxiliary => json!({"kind":"auxiliary"}),
        aux::FactorBaseEncoding::Multiplicative { degree, coset } => {
            json!({"kind":"multiplicative","degree":degree,"coset":coset})
        }
        aux::FactorBaseEncoding::Torus { depth, trace } => {
            json!({"kind":"torus","depth":depth,"trace":trace})
        }
    }
}

fn execute<const B: u32>(
    args: &AuxiliaryArgs,
    input: &Input,
    input_hash: String,
    begin: Instant,
) -> Result<Value, String> {
    let public = &input.public;
    let curve = aux::Curve::<B>::new(public.a, public.b).map_err(|e| e.to_string())?;
    let generator = curve
        .point(public.generator[0], public.generator[1])
        .map_err(|e| e.to_string())?;
    let target = curve
        .point(public.target[0], public.target[1])
        .map_err(|e| e.to_string())?;
    if args.without_auxiliary && !matches!(args.backend, BackendArg::Auto | BackendArg::Scalar) {
        return Err("direct control uses scalar group arithmetic".into());
    }
    let base = if let Some(degree) = args.multiplicative_degree {
        aux::FactorBase::multiplicative(curve, degree, args.coset.unwrap_or(1), args.backend.into())
    } else if let Some(depth) = args.torus_depth {
        aux::FactorBase::torus(curve, depth, args.torus_trace, args.backend.into())
    } else if args.without_auxiliary {
        aux::FactorBase::without_maps(curve, &input.structured_roots)
    } else {
        let encoding = input
            .auxiliary
            .as_ref()
            .ok_or("auxiliary block required; use --without-auxiliary for a direct control")?;
        let maps = encoding
            .maps
            .iter()
            .map(|m| aux::AuxiliaryMap {
                r: m.r,
                offset: m.offset,
                residue: m.residue,
            })
            .collect();
        aux::FactorBase::new(
            curve,
            maps,
            encoding.terminal_c,
            &input.structured_roots,
            args.backend.into(),
        )
    }
    .map_err(|e| e.to_string())?;
    let selection_encoding = encoding_json(base.encoding());
    let terminal_coordinate = base.terminal_coordinate();
    let base = if args.without_auxiliary && base.uses_circuit() {
        base.direct_control().map_err(|e| e.to_string())?
    } else {
        base
    };
    let mut report = json!({
        "schema_version":1,"operation":"auxiliary-prime-field-ic","field_bits":B,"execution_class":"cpu-only",
        "input_blake3":input_hash,"binary_blake3":binary_hash(),"source_commit":git_commit(),
        "public":{"p":public.p,"a":public.a,"b":public.b,"n":public.n,"P":public.generator,"Q":public.target},
        "factor_base":{"raw_roots":base.raw_root_count(),"affine_points":base.affine_point_count(),"uses_auxiliary_maps":base.uses_auxiliary_maps(),
            "uses_circuit":base.uses_circuit(),"encoding":encoding_json(base.encoding()),
            "selection_encoding":selection_encoding,"terminal_coordinate":terminal_coordinate,
            "folded_columns":base.representatives().len(),"backend":base.backend().name()},
        "qualification":"unverified producer diagnostic; no signed independent replay or admitted performance tier",
        "online_exclusive_phases":null,"qualified_speedup":null,"gpu":{"devices":[]}
    });
    if args.decompose_only {
        let mut workspace = base.workspace();
        let row = base
            .decompose(target, &mut workspace)
            .map_err(|e| e.to_string())?;
        report["mode"] = json!("single-decomposition-control");
        report["status"] = json!(if row.is_some() {
            "relation_found"
        } else {
            "no_relation"
        });
        report["decomposition"] = row.map_or(
            Value::Null,
            |d| json!({"i":d.i,"j":d.j,"negative_i":d.negative_i,"negative_j":d.negative_j}),
        );
        return Ok(report);
    }
    let prepared =
        aux::PreparedSolver::new(&base, public.n, generator).map_err(|e| e.to_string())?;
    report["target_independent_preparation_seconds"] = json!(begin.elapsed().as_secs_f64());
    if let Some(path) = &args.replay_relations {
        let raw = read_bounded(path)?;
        let mut rows = Vec::new();
        for (index, line) in raw
            .split(|&b| b == b'\n')
            .filter(|line| !line.is_empty())
            .enumerate()
        {
            if index >= 1_000_000 {
                return Err("replay relation cap reached".into());
            }
            let row: ImportedRow =
                serde_json::from_slice(line).map_err(|e| format!("relation {}: {e}", index + 1))?;
            if ![-1, 1].contains(&row.si) || ![-1, 1].contains(&row.sj) {
                return Err("relation signs must be -1 or 1".into());
            }
            rows.push(aux::Relation {
                a: row.a,
                b: row.b,
                decomposition: aux::SignedRelation {
                    i: row.i,
                    j: row.j,
                    negative_i: row.si < 0,
                    negative_j: row.sj < 0,
                },
            });
        }
        let certificate = prepared
            .recover_from_relations(target, &rows, args.max_proof_nodes)
            .map_err(|e| e.to_string())?;
        report["mode"] = json!("public-relation-certificate-replay");
        report["queries"] = Value::Null;
        report["status"] = json!(if certificate.is_some() {
            "replayed"
        } else {
            "insufficient_relations"
        });
        report["producer_check_passed"] = json!(certificate.is_some());
        report["certificate"] = certificate.as_ref().map_or(Value::Null, certificate_json);
        report["online_wall_seconds"] = Value::Null;
        return Ok(report);
    }
    let config = aux::Config {
        seed: args.seed,
        max_queries: args.max_queries,
        walk_lanes: usize::from(args.walk_lanes),
        max_relations: args.max_relations,
        max_proof_nodes: args.max_proof_nodes,
        max_duration: args.max_millis.map(Duration::from_millis),
    };
    let online = Instant::now();
    let outcome = prepared.solve(target, &config).map_err(|e| e.to_string())?;
    let online_seconds = online.elapsed().as_secs_f64();
    report["mode"] = json!("bounded-single-target-search");
    report["sampler"] = json!("splitmix64-rejection-public-coefficient-walks");
    report["online_wall_seconds"] = json!(online_seconds);
    report["work"] = stats_json(outcome.stats());
    match &outcome {
        aux::SolveOutcome::Solved { certificate, .. } => {
            report["status"] = json!("solved");
            report["producer_check_passed"] = json!(true);
            report["certificate"] = certificate_json(certificate);
        }
        aux::SolveOutcome::Exhausted { reason, .. } => {
            report["status"] = json!("incomplete");
            report["stop_reason"] = json!(format!("{reason:?}"));
            report["certificate"] = Value::Null;
            report["producer_check_passed"] = json!(false);
        }
    }
    if args.rho {
        let group =
            libca::Group::ec(public.p, public.a, public.b, public.n).map_err(|e| e.to_string())?;
        let options = libca::Options {
            solver: libca::Solver::Rho,
            seed: args.seed.max(1),
            threads: 1,
            max_ops: args.rho_max_ops,
            rho_max_table_entries: 1 << 20,
            ..libca::Options::default()
        };
        let start = Instant::now();
        let result = group.dlog(
            &libca::Elem::ec(public.generator[0], public.generator[1]),
            &libca::Elem::ec(public.target[0], public.target[1]),
            &options,
        );
        let seconds = start.elapsed().as_secs_f64();
        report["rho"] = match result {
            Ok((scalar, stats)) => {
                let replayed = curve
                    .mul(Some(generator), scalar)
                    .map_err(|e| e.to_string())?
                    == Some(target);
                if !replayed {
                    return Err("rho public-key replay failed".into());
                }
                json!({"status":"solved","scalar":scalar,"producer_check_passed":true,"online_wall_seconds":seconds,
                    "group_ops":stats.group_ops,"seed":options.seed,"threads":1,
                    "reference":"repository C batched negation-map rho; Montgomery arithmetic"})
            }
            Err(error) => {
                json!({"status":"incomplete","error":error.to_string(),"online_wall_seconds":seconds,"seed":options.seed})
            }
        };
        // Raw unqualified durations only. Qualification/phase accounting and
        // an independent replay belong to the frozen measurement harness.
    }
    report["resources"] = experiment::resources();
    Ok(report)
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;

    #[derive(Parser)]
    struct TestCli {
        #[command(flatten)]
        args: AuxiliaryArgs,
    }

    #[test]
    fn replay_cannot_be_compared_as_a_rho_attack() {
        assert!(TestCli::try_parse_from([
            "test",
            "--input",
            "x",
            "--replay-relations",
            "rows",
            "--rho"
        ])
        .is_err());
        assert!(TestCli::try_parse_from(["test", "--input", "x", "--walk-lanes", "0"]).is_err());
    }

    #[test]
    fn native_and_direct_cli_modes_recover_the_same_public_target() {
        let curve = aux::Curve::<7>::new(2, 51).unwrap();
        let generator = curve.point(3, 46).unwrap();
        let target = curve.mul(Some(generator), 37).unwrap().unwrap();
        let input: Input = serde_json::from_value(json!({
            "public":{"p":127,"a":2,"b":51,"n":109,"P":[3,46],"Q":[target.x(),target.y()]},
            "auxiliary":{"p":127,"maps":[{"r":0,"A":0,"B":1},{"r":2,"A":6,"B":8},{"r":70,"A":71,"B":70}],"terminal_c":38},
            "roots":[3,111,78,67,85,119,57,91]
        })).unwrap();
        let mut args = TestCli::parse_from([
            "test",
            "--input",
            "unused",
            "--seed",
            "43",
            "--max-queries",
            "10000",
        ])
        .args;
        let auxiliary = execute::<7>(&args, &input, "fixture".into(), Instant::now()).unwrap();
        args.without_auxiliary = true;
        args.rho = true;
        let direct = execute::<7>(&args, &input, "fixture".into(), Instant::now()).unwrap();
        assert_eq!(auxiliary["status"], "solved");
        assert_eq!(direct["status"], "solved");
        assert_eq!(auxiliary["certificate"], direct["certificate"]);
        assert_eq!(direct["certificate"]["scalar"], 37);
        assert_eq!(direct["rho"]["status"], "solved");
        assert_eq!(direct["rho"]["scalar"], 37);
        assert_eq!(auxiliary["work"]["queries"], direct["work"]["queries"]);
        assert_eq!(direct["factor_base"]["uses_auxiliary_maps"], false);
        assert_eq!(direct["qualified_speedup"], Value::Null);
        args.max_queries = 0;
        args.rho = false;
        let incomplete = execute::<7>(&args, &input, "fixture".into(), Instant::now()).unwrap();
        assert_eq!(incomplete["status"], "incomplete");
        assert_eq!(incomplete["certificate"], Value::Null);
    }

    #[test]
    fn generated_field_fibers_have_matched_direct_cli_controls() {
        let curve = aux::Curve::<7>::new(2, 51).unwrap();
        let generator = curve.point(3, 46).unwrap();
        let target = curve.mul(Some(generator), 37).unwrap().unwrap();
        let input: Input = serde_json::from_value(json!({
            "public":{"p":127,"a":2,"b":51,"n":109,"P":[3,46],"Q":[target.x(),target.y()]}
        }))
        .unwrap();
        for flags in [["--multiplicative-degree", "18"], ["--torus-depth", "3"]] {
            let mut args = TestCli::parse_from([
                "test",
                "--input",
                "unused",
                "--max-queries",
                "10000",
                flags[0],
                flags[1],
            ])
            .args;
            let circuit = execute::<7>(&args, &input, "fixture".into(), Instant::now()).unwrap();
            args.without_auxiliary = true;
            let direct = execute::<7>(&args, &input, "fixture".into(), Instant::now()).unwrap();
            assert_eq!(circuit["status"], "solved");
            assert_eq!(circuit["certificate"], direct["certificate"]);
            assert_eq!(circuit["work"]["queries"], direct["work"]["queries"]);
            assert_eq!(
                circuit["factor_base"]["raw_roots"],
                direct["factor_base"]["raw_roots"]
            );
            assert_eq!(
                circuit["factor_base"]["selection_encoding"],
                direct["factor_base"]["selection_encoding"]
            );
            assert_eq!(circuit["factor_base"]["uses_circuit"], true);
            assert_eq!(circuit["factor_base"]["uses_auxiliary_maps"], false);
            assert_eq!(direct["factor_base"]["uses_circuit"], false);
            assert_eq!(direct["factor_base"]["encoding"]["kind"], "direct");
        }
        assert!(TestCli::try_parse_from([
            "test",
            "--input",
            "x",
            "--multiplicative-degree",
            "18",
            "--torus-depth",
            "3"
        ])
        .is_err());
        assert!(TestCli::try_parse_from(["test", "--input", "x", "--coset", "1"]).is_err());
        assert!(TestCli::try_parse_from(["test", "--input", "x", "--torus-trace", "4"]).is_err());
    }

    #[test]
    fn archived_public_rows_are_labeled_replay_and_never_timed_as_search() {
        let folder = Path::new(env!("CARGO_MANIFEST_DIR")).join("../experiments/prime-field-auxiliary-ic/snapshot/algebraic/end_to_end/field31_s5_base0");
        let mut args = TestCli::parse_from(["test", "--input", "unused"]).args;
        args.input = folder.join("public.json");
        args.replay_relations = Some(folder.join("chain_seed0.relations.jsonl"));
        let report = run(args).unwrap();
        assert_eq!(report["mode"], "public-relation-certificate-replay");
        assert_eq!(report["certificate"]["scalar"], 123456789);
        assert_eq!(report["status"], "replayed");
        assert_eq!(report["queries"], Value::Null);
        assert_eq!(report["online_wall_seconds"], Value::Null);
    }
}
