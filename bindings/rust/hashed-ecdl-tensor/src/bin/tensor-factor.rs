//! Exact, explicitly bounded divisor-counting factorization runner.

use hashed_ecdl_tensor::contraction::Counter;
use hashed_ecdl_tensor::factoring::factor_integer;
use hashed_ecdl_tensor::{BigUint, Limits, Meter};
use serde_json::json;

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args.len() == 1 && args[0] == "--help" {
        println!("tensor-factor N [MAX_STEPS]\nExact divisor-prefix counting; finite-size fallback can be exponential.");
        return Ok(());
    }
    if !(1..=2).contains(&args.len()) {
        return Err("usage: tensor-factor N [MAX_STEPS]".into());
    }
    let mut limits = Limits::default();
    if let Some(steps) = args.get(1) {
        limits.steps = steps.parse()?;
    }
    if args[0].is_empty()
        || args[0].len() > limits.bits / 3 + 1
        || !args[0].bytes().all(|b| b.is_ascii_digit())
    {
        return Err("N must be a bounded unsigned decimal integer".into());
    }
    let n = BigUint::parse_bytes(args[0].as_bytes(), 10).ok_or("invalid integer")?;
    let mut meter = Meter::new(limits);
    let mut counter = Counter::default();
    let factors = factor_integer(&n, &mut counter, &mut meter)?;
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "schema": "tensor-factor/v1", "n": n.to_string(),
            "factors": factors.iter().map(ToString::to_string).collect::<Vec<_>>(),
            "algorithm": "divisor-prefix-counting", "source": "https://hexagonmath.org/2610.00600v1",
            "diagnostics": { "charged_steps": meter.used, "contractions": counter.statistics.contractions,
                "last_backend": format!("{:?}", counter.statistics.last_backend),
                "functional_assignments": counter.statistics.functional_assignments },
            "verification_scope": "exact arithmetic; no asymptotic or measured speedup claim"
        }))?
    );
    Ok(())
}

fn main() {
    if let Err(e) = run() {
        eprintln!("tensor-factor: {e}");
        std::process::exit(1);
    }
}
