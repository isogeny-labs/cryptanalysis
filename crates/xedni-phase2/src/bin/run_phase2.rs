//! Deterministic benchmark runner for Xedni Phase 2 (`experiments/xedni-phase2-20261119/RESULTS.json`).

use std::env;
use std::fs;
use std::path::PathBuf;
use std::time::Instant;

use serde::Serialize;

use xedni_phase2::cayley_bacharach::{run_escape_7a_suite, Escape7aSummary};
use xedni_phase2::l4_selector::{run_escape_7c_suite, Escape7cSummary};
use xedni_phase2::nodal_bezout::{run_escape_7b_suite, Escape7bSummary};

#[derive(Serialize)]
struct Phase2ResultsBundle {
    schema: &'static str,
    date: &'static str,
    standing: &'static str,
    seed: u64,
    elapsed_seconds: f64,
    escape_7a_cayley_bacharach: Escape7aSummary,
    escape_7b_nodal_bezout: Escape7bSummary,
    escape_7c_l4_selector: Escape7cSummary,
}

fn main() -> Result<(), String> {
    let out_path = env::args()
        .nth(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("experiments/xedni-phase2-20261119/RESULTS.json"));
    let seed = 2026_1119u64;
    let t0 = Instant::now();

    eprintln!("[1/3] Running Escape 7A (Cayley-Bacharach 9-point cubic pencils + CoordinateFb, 8..14 bits)...");
    let e7a = run_escape_7a_suite(seed)?;

    eprintln!("[2/3] Running Escape 7B (Nodal degree-d>=4 Bezout curves & genus-2 1-nodal quartic Jacobian LLL)...");
    let e7b = run_escape_7b_suite(seed)?;

    eprintln!("[3/3] Running Escape 7C (CH-L4 / L4-check F1 scalar-blind public small-height lift selector, 8..12 & 24..28 bits)...");
    let e7c = run_escape_7c_suite(seed)?;

    let elapsed = t0.elapsed().as_secs_f64();
    let bundle = Phase2ResultsBundle {
        schema: "xedni.phase2.results/v1",
        date: "2026-11-19",
        standing: "pcc:unverified",
        seed,
        elapsed_seconds: elapsed,
        escape_7a_cayley_bacharach: e7a,
        escape_7b_nodal_bezout: e7b,
        escape_7c_l4_selector: e7c,
    };

    if let Some(parent) = out_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let json = serde_json::to_string_pretty(&bundle).map_err(|e| e.to_string())?;
    fs::write(&out_path, json).map_err(|e| e.to_string())?;
    eprintln!("Wrote {} ({:.2}s)", out_path.display(), elapsed);
    Ok(())
}
