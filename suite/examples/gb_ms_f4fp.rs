//! Run the degree-bounded F4 over `F_p` (`f4_fp`) on a system in msolve's
//! input format, so `f4_fp` and an external solver run on the same bytes.
//!
//! The `.ms` format: variable names on line 1, the characteristic on line 2,
//! then polynomials separated by commas, with terms `c*x0^2*x3` and signed
//! integer coefficients. The pilot's `--export` and
//! `research/gb_reference_20261121/direct_semaev.py` write it.
//!
//! The degree bound is the pilot's default for its non-naive controls,
//! `n + d_max + 6`, unless `--cap` is given. A `<id>.sol.json` beside the
//! file supplies the planted solution, checked on the output basis.
//!
//! ```text
//! cargo run --release --example gb_ms_f4fp -- SYSTEM.ms [--budget S] [--cap D]
//! ```
//!
//! Prints one JSON row with the same field names as the pilot's rows.

use std::time::{Duration, Instant};

use cryptanalysis_suite::cryptanalysis::f4_fp::{self, F4Options, Ordering, Poly};
use serde_json::{json, Value};

fn parse_poly(s: &str, names: &[String], p: u64) -> Vec<(Vec<u32>, u64)> {
    let n = names.len();
    let s: String = s.chars().filter(|c| !c.is_whitespace()).collect();
    let mut terms = Vec::new();
    let mut i = 0;
    let b = s.as_bytes();
    while i < b.len() {
        let mut neg = false;
        if b[i] == b'+' || b[i] == b'-' {
            neg = b[i] == b'-';
            i += 1;
        }
        let start = i;
        while i < b.len() && b[i] != b'+' && b[i] != b'-' {
            i += 1;
        }
        let body = &s[start..i];
        let mut c: u64 = 1;
        let mut e = vec![0u32; n];
        for f in body.split('*') {
            if f.is_empty() {
                continue;
            }
            if f.bytes().all(|x| x.is_ascii_digit()) {
                let v = (f.parse::<u128>().expect("coefficient") % p as u128) as u64;
                c = ((c as u128 * v as u128) % p as u128) as u64;
            } else {
                let (v, d) = match f.split_once('^') {
                    Some((v, d)) => (v, d.parse::<u32>().expect("exponent")),
                    None => (f, 1),
                };
                let k = names
                    .iter()
                    .position(|x| x == v)
                    .unwrap_or_else(|| panic!("unknown variable {v}"));
                e[k] += d;
            }
        }
        if neg {
            c = (p - c) % p;
        }
        if c != 0 {
            terms.push((e, c));
        }
    }
    terms
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let path = args
        .first()
        .expect("usage: gb_ms_f4fp SYSTEM.ms [--budget S] [--cap D]");
    let mut budget = 60u64;
    let mut cap: Option<u32> = None;
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--budget" => budget = args[i + 1].parse().expect("--budget"),
            "--cap" => cap = Some(args[i + 1].parse().expect("--cap")),
            o => panic!("unknown flag {o}"),
        }
        i += 2;
    }
    let text = std::fs::read_to_string(path).expect("read system");
    let mut lines = text.lines();
    let names: Vec<String> = lines
        .next()
        .expect("variables")
        .split(',')
        .map(|s| s.trim().to_string())
        .collect();
    let p: u64 = lines
        .next()
        .expect("characteristic")
        .trim()
        .parse()
        .expect("p");
    let rest: String = lines.collect::<Vec<_>>().join("");
    let n = names.len();
    let input: Vec<Poly> = rest
        .split(',')
        .filter(|s| !s.trim().is_empty())
        .map(|s| f4_fp::normalise(&parse_poly(s, &names, p), p, Ordering::Grevlex))
        .filter(|f| !f.is_empty())
        .collect();
    let d_max = input
        .iter()
        .map(|f| {
            f.iter()
                .map(|(e, _)| e.iter().sum::<u32>())
                .max()
                .unwrap_or(0)
        })
        .max()
        .unwrap_or(1);
    let max_degree = cap.unwrap_or(n as u32 + d_max + 6);
    let sol_path = path.strip_suffix(".ms").map(|s| format!("{s}.sol.json"));
    let sol: Option<Vec<u64>> = sol_path
        .and_then(|sp| std::fs::read_to_string(sp).ok())
        .and_then(|t| serde_json::from_str::<Value>(&t).ok())
        .and_then(|v| serde_json::from_value(v["solution"].clone()).ok());
    if let Some(s) = &sol {
        for (k, f) in input.iter().enumerate() {
            assert_eq!(
                f4_fp::eval(f, s, p),
                0,
                "input {k} does not vanish at the planted solution"
            );
        }
    }
    let opts =
        F4Options::new(Ordering::Grevlex, max_degree).with_budget(Duration::from_secs(budget));
    let started = Instant::now();
    let r = f4_fp::f4(&input, n, p, &opts);
    let wall = started.elapsed().as_secs_f64();
    let planted_ok = sol
        .as_ref()
        .map(|s| !r.inconsistent && r.basis.iter().all(|f| f4_fp::eval(f, s, p) == 0));
    let id = std::path::Path::new(path)
        .file_name()
        .and_then(|f| f.to_str())
        .and_then(|f| f.strip_suffix(".ms"))
        .unwrap_or(path);
    let row = json!({
        "id": id, "engine": "f4_fp", "p": p, "n_vars": n, "n_equations": input.len(),
        "max_degree_bound": max_degree, "solving_degree_max": r.solving_degree_max,
        "degree_reached": r.degree_reached, "max_cols_to_solution": r.max_cols_to_solution,
        "max_rows": r.max_rows, "max_cols": r.max_cols, "steps": r.steps,
        "basis_len": r.basis.len(), "inconsistent": r.inconsistent, "ms": r.ms, "wall_s": wall,
        "timed_out": r.timed_out, "pairs_above_bound": r.pairs_above_bound, "planted_ok": planted_ok,
    });
    println!("{row}");
}
