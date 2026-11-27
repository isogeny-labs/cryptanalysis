// Coordinate-input M31 recovery with cold setup and reusable signed witnesses.
// No target scalar, planted decomposition, or rho fallback is accepted.
use prime_field_auxiliary_ic::*;
use std::{
    fmt::Write as _,
    time::{Duration, Instant},
};

fn phases(p: &SearchPhases) -> String {
    format!("{{\"initialization\":{},\"target_walk\":{},\"decomposition\":{},\"row_validation\":{},\"elimination\":{},\"certificate_replay\":{},\"bookkeeping\":{},\"total\":{},\"clock_reads\":{}}}",p.initialization.as_nanos(),p.target_walk.as_nanos(),p.decomposition.as_nanos(),p.row_validation.as_nanos(),p.graph_recovery.as_nanos(),p.certificate_replay.as_nanos(),p.bookkeeping.as_nanos(),p.total.as_nanos(),p.clock_reads)
}
fn pair_stats(s: &PairIndexStats) -> String {
    format!("{{\"constructed_pairs\":{},\"entries\":{},\"collision_witnesses\":{},\"generated_candidates\":{},\"lookups\":{},\"hits\":{},\"cache_hits\":{},\"group_replays\":{}}}",s.constructed_pairs,s.entries,s.collision_witnesses,s.generated_candidates,s.lookups,s.hits,s.cache_hits,s.group_replays)
}
fn statistics(s: &SearchStats) -> String {
    format!("{{\"queries\":{},\"generated_targets\":{},\"relations\":{},\"matrix_rank\":{},\"proof_nodes\":{},\"duplicate_rows\":{},\"lane_rounds\":{}}}",s.queries,s.generated_targets,s.relations,s.matrix_rank,s.proof_nodes,s.duplicate_rows,s.lane_rounds)
}
fn certificate(c: &MultiCertificate) -> String {
    let mut out=format!("{{\"summands\":{},\"order\":{},\"generator\":[{},{}],\"target\":[{},{}],\"scalar\":{},\"weights\":{:?},\"relations\":[",c.summands,c.order,c.generator.x(),c.generator.y(),c.target.x(),c.target.y(),c.scalar,c.weights);
    for (i, r) in c.relations.iter().enumerate() {
        if i > 0 {
            out.push(',');
        }
        write!(out, "{{\"a\":{},\"b\":{},\"terms\":[", r.a, r.b).unwrap();
        for (j, t) in r.decomposition.summands().iter().enumerate() {
            if j > 0 {
                out.push(',');
            }
            write!(
                out,
                "{{\"column\":{},\"sign\":{}}}",
                t.index,
                if t.negative { -1 } else { 1 }
            )
            .unwrap();
        }
        out.push_str("]}");
    }
    out.push_str("]}");
    out
}
fn main() -> std::process::ExitCode {
    if std::env::args().any(|a| a == "--help" || a == "-h") {
        println!("Usage: m31-fast --qx X --qy Y [--seed N] [--columns B] [--summands 2|3|4]\nFixed E/Fp: p=2147483647, a=2, b=14, N=2147505293, G=(1,814455902).\nDefaults: B256, m2, interval base, signed pair index, 4M queries, 5s online.\nOptions: --base interval|random|torus --base-seed N --method indexed|direct\n         --max-queries N --max-ms N --lanes 1..1024 --chunk 1..16384 --profile\nExit: 0 solved and replayed; 1 bounded incomplete; 2 invalid input/error.\nJSON stdout includes the full certificate; no target scalar or rho fallback.");
        return std::process::ExitCode::SUCCESS;
    }
    match run() {
        Ok(true) => std::process::ExitCode::SUCCESS,
        Ok(false) => std::process::ExitCode::FAILURE,
        Err(error) => {
            eprintln!("m31-fast: {error}");
            std::process::ExitCode::from(2)
        }
    }
}
fn parse<T: std::str::FromStr>(flag: &str, value: &str) -> std::result::Result<T, String> {
    value
        .parse()
        .map_err(|_| format!("{flag} requires a valid unsigned integer"))
}
fn run() -> std::result::Result<bool, String> {
    let start = Instant::now();
    let args: Vec<String> = std::env::args().collect();
    let mut qx = None;
    let mut qy = None;
    let mut columns = 256usize;
    let mut summands = 2u8;
    let mut seed = 0u64;
    let mut base_seed = 1u64;
    let mut max_ms = 5000u64;
    let mut max_queries = 4_000_000;
    let mut lanes = 64usize;
    let mut chunk = 64usize;
    let mut method = "indexed";
    let mut base_kind = "interval";
    let mut profile = false;
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--profile" {
            profile = true;
            i += 1;
            continue;
        }
        let value = args
            .get(i + 1)
            .ok_or_else(|| format!("{} needs a value", args[i]))?;
        match args[i].as_str() {
            "--qx" => qx = Some(parse(&args[i], value)?),
            "--qy" => qy = Some(parse(&args[i], value)?),
            "--columns" => columns = parse(&args[i], value)?,
            "--summands" => summands = parse(&args[i], value)?,
            "--seed" => seed = parse(&args[i], value)?,
            "--base-seed" => base_seed = parse(&args[i], value)?,
            "--max-ms" => max_ms = parse(&args[i], value)?,
            "--max-queries" => max_queries = parse(&args[i], value)?,
            "--lanes" => lanes = parse(&args[i], value)?,
            "--chunk" => chunk = parse(&args[i], value)?,
            "--method" => method = value,
            "--base" => base_kind = value,
            _ => return Err(format!("unknown flag {}", args[i])),
        };
        i += 2;
    }
    if !(2..=4).contains(&summands) || !(1..=2048).contains(&columns) {
        return Err("summands must be 2..=4 and columns 1..=2048".into());
    }
    if !(1..=1024).contains(&lanes) || !(1..=16384).contains(&chunk) {
        return Err("lanes must be 1..=1024 and chunk 1..=16384".into());
    }
    if method != "indexed" && method != "direct" {
        return Err("method must be indexed or direct".into());
    }
    if !["interval", "random", "torus"].contains(&base_kind) {
        return Err("base must be interval, random or torus".into());
    }
    let c = Curve::<31>::new(2, 14).unwrap();
    let n = 2147505293;
    let g = c.point(1, 814455902).unwrap();
    let q = c
        .point(
            qx.ok_or("public --qx is required")?,
            qy.ok_or("public --qy is required")?,
        )
        .map_err(|e| e.to_string())?;
    let prep = Instant::now();
    let mut torus_depth = None;
    let base = match base_kind {
        "interval" => {
            let roots: Vec<_> = (0..c.modulus())
                .filter(|x| c.lift_x(*x).unwrap().is_some())
                .take(columns)
                .collect();
            FactorBase::without_maps(c, &roots).map_err(|e| e.to_string())?
        }
        "random" => {
            FactorBase::random_control(c, n, g, columns, base_seed, 1000000)
                .map_err(|e| e.to_string())?
                .0
        }
        "torus" => {
            let mut found = None;
            for depth in 1..=15 {
                let b = FactorBase::torus(c, depth, None, Backend::Scalar)
                    .map_err(|e| e.to_string())?;
                if b.representatives().len() >= columns {
                    let roots: Vec<_> = b.representatives()[..columns]
                        .iter()
                        .map(|p| p.x())
                        .collect();
                    found = Some(FactorBase::without_maps(c, &roots).map_err(|e| e.to_string())?);
                    torus_depth = Some(depth);
                    break;
                }
            }
            found.ok_or("requested torus subset is unattainable")?
        }
        _ => unreachable!("base validated above"),
    };
    let base_ns = prep.elapsed().as_nanos();
    let prepared_at = Instant::now();
    let prepared = PreparedSolver::new(&base, n, g).map_err(|e| e.to_string())?;
    let preparation_ns = prepared_at.elapsed().as_nanos();
    let build = Instant::now();
    let index = if method == "indexed" {
        Some(PairIndex::new(&base, 4_194_304, chunk).map_err(|e| e.to_string())?)
    } else {
        None
    };
    let index_ns = build.elapsed().as_nanos();
    let setup_stats = index
        .as_ref()
        .map_or("null".into(), |x| pair_stats(x.stats()));
    let config = Config {
        seed,
        max_queries,
        walk_lanes: lanes,
        max_duration: Some(Duration::from_millis(max_ms)),
        ..Config::default()
    };
    let online = Instant::now();
    let (outcome, probe_stats, phase) = if let Some(index) = &index {
        if profile {
            let (o, s, p) = prepared
                .solve_multi_indexed_profiled(summands, q, &config, index)
                .map_err(|e| e.to_string())?;
            (o, pair_stats(&s), phases(&p))
        } else {
            let (o, s) = prepared
                .solve_multi_indexed(summands, q, &config, index)
                .map_err(|e| e.to_string())?;
            (o, pair_stats(&s), "null".into())
        }
    } else if profile {
        let (o, p) = prepared
            .solve_multi_profiled(summands, q, &config)
            .map_err(|e| e.to_string())?;
        (o, "null".into(), phases(&p))
    } else {
        (
            prepared
                .solve_multi(summands, q, &config)
                .map_err(|e| e.to_string())?,
            "null".into(),
            "null".into(),
        )
    };
    let online_ns = online.elapsed().as_nanos();
    let replay = Instant::now();
    let (status, proof, scalar, reason) = match &outcome {
        MultiSolveOutcome::Solved {
            certificate: proof, ..
        } => {
            verify_multi_certificate(&base, proof).map_err(|e| e.to_string())?;
            (
                "solved",
                Some(proof),
                Some(proof.scalar),
                "null".to_string(),
            )
        }
        MultiSolveOutcome::Exhausted { reason, .. } => {
            ("incomplete", None, None, format!("\"{reason:?}\""))
        }
    };
    let extra_replay_ns = replay.elapsed().as_nanos();
    let stats = statistics(outcome.stats());
    let proof = proof.map_or("null".into(), certificate);
    let scalar = scalar.map_or("null".into(), |x| x.to_string());
    let points: Vec<_> = base
        .representatives()
        .iter()
        .map(|p| [p.x(), p.y()])
        .collect();
    drop(outcome);
    drop(index);
    drop(base);
    let cold_ns = start.elapsed().as_nanos();
    println!("{{\"schema\":\"m31-e2e-native/v1\",\"p\":2147483647,\"a\":2,\"b\":14,\"n\":{n},\"G\":[1,814455902],\"Q\":[{},{}],\"method\":\"{method}\",\"base_kind\":\"{base_kind}\",\"torus_subset_depth\":{},\"columns\":{columns},\"summands\":{summands},\"seed\":{seed},\"base_seed\":{base_seed},\"max_ms\":{max_ms},\"max_queries\":{max_queries},\"lanes\":{lanes},\"chunk\":{chunk},\"status\":\"{status}\",\"scalar\":{scalar},\"stop_reason\":{reason},\"base_construction_ns\":{base_ns},\"group_preparation_ns\":{preparation_ns},\"pair_index_ns\":{index_ns},\"online_ns\":{online_ns},\"extra_certificate_replay_ns\":{extra_replay_ns},\"cold_to_report_ns\":{cold_ns},\"cold_scope\":\"main-entry through result serialization preparation and math teardown; final stdout emission and runtime startup excluded\",\"setup_pair_counts\":{setup_stats},\"online_pair_counts\":{probe_stats},\"phase_profile_ns\":{phase},\"work\":{stats},\"base_points\":{points:?},\"certificate\":{proof},\"producer_only\":true}}",q.x(),q.y(),torus_depth.map_or("null".into(),|d|d.to_string()));
    Ok(status == "solved")
}
