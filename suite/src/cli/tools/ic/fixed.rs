//! Fixed-parameter wide-field workflow through the existing Python ONB engine.
mod s3;

use clap::Args;
use serde_json::{json, Value};
use std::{
    fs::{self, File},
    path::PathBuf,
    process::{Command, Stdio},
    time::{Duration, Instant},
};

#[derive(Args, Clone)]
pub struct FixedArgs {
    /// Fixed K_0 parameters and target coordinates, including the field basis.
    #[arg(long)]
    pub params: PathBuf,
    /// Durable campaign directory. Rerun with the same parameters to resume.
    #[arg(long)]
    pub dir: PathBuf,
    /// Stage; all also attempts target-specific relations when base logs are incomplete.
    #[arg(long, default_value = "all", value_parser = ["select", "pairs", "collect", "logs", "solve", "all", "status"])]
    pub stage: String,
    /// Exact pair table, bounded SAT, or an opt-in learned policy with pair fallback.
    #[arg(long, default_value = "pairs", value_parser = ["pairs", "sat", "learned"])]
    pub solver: String,
    /// JSON selector trained with indexcalc_selector.py; required for learned.
    #[arg(long)]
    pub selector_model: Option<PathBuf>,
    /// Additional probes per collection stream or target in this invocation.
    #[arg(long, default_value_t = 32)]
    pub attempts: u32,
    /// Maximum new pair candidates built in this invocation.
    #[arg(long, default_value_t = 10000)]
    pub pair_budget: u64,
    /// Native SAT solve budget; a separate watchdog bounds each complete SAT query.
    #[arg(long, default_value_t = 0.25)]
    pub query_seconds: f64,
    /// Python interpreter; python-sat and pycryptosat are needed only for SAT.
    #[arg(long, default_value = "python3")]
    pub python: PathBuf,
    /// Print live stage and elapsed-work messages to stderr.
    #[arg(long)]
    pub verbose: bool,
    /// Seconds between live heartbeats (implies --verbose).
    #[arg(long, value_parser = clap::value_parser!(u64).range(1..))]
    pub progress_every: Option<u64>,
    /// Restore from S3 into a fresh directory, or continue a local campaign.
    #[arg(long)]
    pub resume: bool,
    /// Mirror a transactionally consistent SQLite snapshot and report to S3.
    #[arg(long)]
    pub s3_uri: Option<String>,
}

pub fn run(args: FixedArgs) -> Result<Value, String> {
    let python_version = Command::new(&args.python)
        .args([
            "-c",
            "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)",
        ])
        .status()
        .map_err(|e| format!("could not run {}: {e}", args.python.display()))?;
    if !python_version.success() {
        return Err(format!(
            "ic fixed requires Python 3.10 or newer; select it with --python (got {})",
            args.python.display()
        ));
    }
    let script =
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("python/indexcalc/indexcalc_fixed.py");
    if !script.is_file() {
        return Err(format!(
            "fixed workflow engine is missing: {}",
            script.display()
        ));
    }
    let live = args.verbose || args.progress_every.is_some();
    let mut store = if let Some(uri) = &args.s3_uri {
        let identity = s3::input_digest(&args.params, args.selector_model.as_deref(), &script)?;
        Some(s3::Store::prepare(
            &args.dir,
            uri,
            &identity,
            args.resume,
            live,
        )?)
    } else {
        None
    };
    if live {
        eprintln!(
            "[ic fixed] {} started in {}",
            args.stage,
            args.dir.display()
        );
    }
    let started = Instant::now();
    let heartbeat = if live {
        let (stop, received) = std::sync::mpsc::channel::<()>();
        let dir = args.dir.clone();
        let stage = args.stage.clone();
        let every = args.progress_every.unwrap_or(5);
        let worker = std::thread::spawn(move || {
            while received.recv_timeout(Duration::from_secs(every)).is_err() {
                let bytes = fs::metadata(dir.join("campaign.sqlite3"))
                    .map(|m| m.len())
                    .unwrap_or(0);
                eprintln!(
                    "[ic fixed] {stage} {:.0}s sqlite_bytes={bytes}",
                    started.elapsed().as_secs_f64()
                );
            }
        });
        Some((stop, worker))
    } else {
        None
    };
    let result = run_child(&args, &script, &mut store, live);
    if let Some((stop, worker)) = heartbeat {
        let _ = stop.send(());
        let _ = worker.join();
    }
    result
}

fn run_child(
    args: &FixedArgs,
    script: &PathBuf,
    store: &mut Option<s3::Store>,
    live: bool,
) -> Result<Value, String> {
    let mut command = Command::new(&args.python);
    command.arg(script);
    if let Some(model) = &args.selector_model {
        command.arg("--selector-model").arg(model);
    }
    if live {
        command.arg("--verbose");
        command
            .arg("--progress-every")
            .arg(args.progress_every.unwrap_or(5).to_string());
    }
    let result = command
        .arg("--params")
        .arg(&args.params)
        .arg("--dir")
        .arg(&args.dir)
        .arg("--stage")
        .arg(&args.stage)
        .arg("--solver")
        .arg(&args.solver)
        .arg("--attempts")
        .arg(args.attempts.to_string())
        .arg("--pair-budget")
        .arg(args.pair_budget.to_string())
        .arg("--query-seconds")
        .arg(args.query_seconds.to_string())
        .stdin(Stdio::null())
        .stderr(Stdio::inherit())
        .output()
        .map_err(|e| {
            format!(
                "could not run fixed workflow with {}: {e}",
                args.python.display()
            )
        })?;
    let mut report: Value = serde_json::from_slice(&result.stdout).map_err(|e| {
        format!(
            "fixed workflow exited {} without a valid JSON report: {e}",
            result.status
        )
    })?;
    if report["operation"] != "fixed" {
        return Err("fixed workflow returned an unexpected report".into());
    }
    if !result.status.success() && matches!(report["status"].as_str(), Some("complete" | "stopped"))
    {
        return Err(format!(
            "fixed workflow reported success but exited {}",
            result.status
        ));
    }
    report["software"] = json!({"version":env!("CARGO_PKG_VERSION"),
        "os":std::env::consts::OS,"arch":std::env::consts::ARCH,
        "binary_blake3":super::binary_hash(),"git_commit":super::git_commit()});
    fs::create_dir_all(&args.dir).map_err(|e| e.to_string())?;
    let report_path = args.dir.join("result.json");
    let temp = args.dir.join("result.json.tmp");
    let mut bytes = serde_json::to_vec_pretty(&report).map_err(|e| e.to_string())?;
    bytes.push(b'\n');
    fs::write(&temp, bytes).map_err(|e| e.to_string())?;
    File::open(&temp)
        .map_err(|e| e.to_string())?
        .sync_all()
        .map_err(|e| e.to_string())?;
    fs::rename(&temp, report_path).map_err(|e| e.to_string())?;
    if report["status"] != "error" {
        if let Some(store) = store {
            store.sync(&args.python)?;
        }
    }
    if live {
        eprintln!(
            "[ic fixed] {} finished: {}",
            args.stage,
            report["status"].as_str().unwrap_or("unknown")
        );
    }
    Ok(report)
}
