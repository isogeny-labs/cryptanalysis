//! Bounded producer comparison; no end-to-end or speedup qualification.
mod m31_relation_encodings;
use clap::Parser;
use m31_relation_encodings::{build, run, run_up_to, Encoding, Input, Schedule};
use serde_json::{json, Value};
use std::{
    fs,
    io::{self, Write},
    path::PathBuf,
    time::{Duration, Instant},
};
#[derive(Parser)]
struct Args {
    #[arg(long)]
    input: PathBuf,
    #[arg(long)]
    m: usize,
    #[arg(long)]
    encoding: String,
    #[arg(long)]
    schedule: String,
    #[arg(long, default_value_t = 2000)]
    budget_ms: u64,
    #[arg(long, default_value_t = 8)]
    degree: u32,
    #[arg(long, default_value_t = 10000)]
    construction_ms: u64,
    /// Supplemental bounded search of lengths0..m; default remains exact m.
    #[arg(long)]
    up_to_m: bool,
}
fn main() {
    let args = Args::parse();
    let start = Instant::now();
    eprintln!(
        "{}",
        json!({"schema":"m31-relation-encodings-preflight/v1","stage":"start","input_path":args.input,"m":args.m,"encoding":args.encoding,"schedule":args.schedule,"engine_budget_ms":args.budget_ms,"degree":args.degree,"construction_budget_ms":args.construction_ms,"up_to_m":args.up_to_m,"producer_only":true})
    );
    let _ = io::stderr().flush();
    let result = (|| -> Result<Value, String> {
        if args.budget_ms == 0 || args.degree == 0 || args.construction_ms == 0 {
            return Err("positive budgets/degree required".into());
        }
        let value: Value =
            serde_json::from_str(&fs::read_to_string(&args.input).map_err(|e| e.to_string())?)
                .map_err(|e| e.to_string())?;
        let input = if value.get("public").is_some() {
            let p = &value["public"];
            serde_json::from_value::<Input>(
                json!({"p":p["p"],"a":p["a"],"b":p["b"],"base":value["base"],"target":p["Q"]}),
            )
        } else {
            serde_json::from_value::<Input>(value)
        }
        .map_err(|e| e.to_string())?;
        if args.up_to_m {
            let mut report = run_up_to(
                &input,
                args.m,
                Encoding::parse(&args.encoding)?,
                Schedule::parse(&args.schedule)?,
                Duration::from_millis(args.budget_ms),
                args.degree,
                Duration::from_millis(args.construction_ms),
            )?;
            report["input_path"] = json!(args.input);
            return Ok(report);
        }
        let system = build(
            &input,
            args.m,
            Encoding::parse(&args.encoding)?,
            Duration::from_millis(args.construction_ms),
        )?;
        let mut report = run(
            &system,
            Schedule::parse(&args.schedule)?,
            Duration::from_millis(args.budget_ms),
            args.degree,
        );
        report["construction_budget_ms"] = json!(args.construction_ms);
        report["input_path"] = json!(args.input);
        Ok(report)
    })();
    match result {
        Ok(mut report) => {
            report["enclosing_ns"] = json!(start.elapsed().as_nanos());
            println!("{report}");
        }
        Err(error) => {
            println!(
                "{}",
                json!({"schema":"m31-relation-encodings/v1","status":"construction_or_input_error","error":error,"encoding":args.encoding,"schedule":args.schedule,"m":args.m,"elapsed_ns":start.elapsed().as_nanos()})
            );
            std::process::exit(2);
        }
    }
}
