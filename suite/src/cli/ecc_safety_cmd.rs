//! `crax ecc-safety`: Curve and Parameter Review auditor.
//!
//! Runs [`crate::ecc_safety::CurveParams::analyse`] on short-Weierstrass
//! parameters `(p, a, b, G, n, h)` and prints a [`SafetyReport`]. This is
//! the dedicated JSON surface for Evidence Lab / assessment reports; it does
//! not invent break costs and does not accept Montgomery form without an
//! explicit Weierstrass conversion (out of scope for this command).

use clap::Args;
use num_bigint::{BigInt, BigUint, Sign};
use num_traits::Num;
use serde::Serialize;

use super::output::{parse_biguint, CmdResult, Out};
use crate::ecc_safety::{AnalysisOptions, CurveParams, SafetyCheck, SafetyReport};

/// Arguments for `crax ecc-safety`.
#[derive(Args, Clone, Debug)]
pub struct EccSafetyArgs {
    /// Field prime (decimal or 0x hex).
    #[arg(long)]
    pub p: String,
    /// Curve coefficient a (signed decimal or 0x hex; use `--a=-3` for negatives).
    #[arg(long, allow_hyphen_values = true)]
    pub a: String,
    /// Curve coefficient b (signed decimal or 0x hex; use `--b=-1` for negatives).
    #[arg(long, allow_hyphen_values = true)]
    pub b: String,
    /// Generator x-coordinate (decimal or 0x hex).
    #[arg(long)]
    pub gx: String,
    /// Generator y-coordinate (decimal or 0x hex).
    #[arg(long)]
    pub gy: String,
    /// Order of G (decimal or 0x hex).
    #[arg(long)]
    pub n: String,
    /// Cofactor h = #E / n (decimal or 0x hex).
    #[arg(long)]
    pub h: String,
    /// Minimum `bits(n)` required to pass the order-size check (default 200).
    #[arg(long, default_value_t = 200)]
    pub min_order_bits: u32,
    /// Trial-division smoothness bound for factoring `n` (default 2^22).
    #[arg(long, default_value_t = 1 << 22)]
    pub smoothness_bound: u64,
    /// Minimum bit-length of the largest prime factor of `n` (default 160).
    #[arg(long, default_value_t = 160)]
    pub min_largest_prime_factor_bits: u32,
    /// Assumed private-key size in bits for the almost-smooth check (default 200).
    #[arg(long, default_value_t = 200)]
    pub min_private_key_bits: u32,
    /// Embedding-degree cutoff for the MOV / Frey–Rück flag (default 6).
    #[arg(long, default_value_t = 6)]
    pub max_unsafe_embedding_degree: u32,
    /// Expected number of keys sharing this curve (multi-target margin).
    #[arg(long)]
    pub expected_deployment_size: Option<u64>,
    /// Minimum amortised per-key security floor in bits (default 100).
    #[arg(long, default_value_t = 100)]
    pub min_amortised_security_bits: u32,
    /// Field-extension degree; 1 = prime field (default 1).
    #[arg(long, default_value_t = 1)]
    pub extension_degree: u32,
}

/// Signed integer in decimal or `0x` / `-0x` hex.
fn parse_bigint(s: &str) -> Result<BigInt, String> {
    let t = s.trim().replace('_', "");
    let (neg, rest) = match t.strip_prefix('-') {
        Some(r) => (true, r),
        None => (false, t.as_str()),
    };
    if rest.is_empty() {
        return Err(format!("not an integer: {s:?}"));
    }
    let mag = if let Some(hex) = rest
        .strip_prefix("0x")
        .or_else(|| rest.strip_prefix("0X"))
    {
        BigUint::from_str_radix(hex, 16)
    } else {
        BigUint::from_str_radix(rest, 10)
    }
    .map_err(|_| format!("not an integer: {s:?}"))?;
    let mut v = BigInt::from_biguint(Sign::Plus, mag);
    if neg {
        v = -v;
    }
    Ok(v)
}

impl EccSafetyArgs {
    fn curve(&self) -> Result<CurveParams, String> {
        Ok(CurveParams {
            p: parse_biguint(&self.p)?,
            a: parse_bigint(&self.a)?,
            b: parse_bigint(&self.b)?,
            gx: parse_biguint(&self.gx)?,
            gy: parse_biguint(&self.gy)?,
            n: parse_biguint(&self.n)?,
            h: parse_biguint(&self.h)?,
        })
    }

    fn options(&self) -> AnalysisOptions {
        AnalysisOptions {
            min_order_bits: self.min_order_bits,
            smoothness_bound: self.smoothness_bound,
            min_largest_prime_factor_bits: self.min_largest_prime_factor_bits,
            min_private_key_bits: self.min_private_key_bits,
            max_unsafe_embedding_degree: self.max_unsafe_embedding_degree,
            expected_deployment_size: self.expected_deployment_size,
            min_amortised_security_bits: self.min_amortised_security_bits,
            extension_degree: self.extension_degree,
            ..AnalysisOptions::default()
        }
    }
}

#[derive(Serialize)]
struct EccSafetyOut<'a> {
    status: &'static str,
    all_pass: bool,
    failed_checks: Vec<&'static str>,
    report: &'a SafetyReport,
}

fn check_line(name: &str, c: &SafetyCheck) -> String {
    match c {
        SafetyCheck::Pass => format!("  {name}: pass"),
        SafetyCheck::Fail(d) => format!("  {name}: FAIL — {d}"),
        SafetyCheck::Inconclusive(d) => format!("  {name}: inconclusive — {d}"),
    }
}

fn text_report(r: &SafetyReport) -> String {
    let mut lines = vec![
        format!(
            "ecc-safety: {}",
            if r.failed_checks().is_empty() {
                "no demonstrated failures"
            } else {
                "FAILED checks present"
            }
        ),
        check_line("order_size", &r.order_size),
        check_line("order_smoothness", &r.order_smoothness),
        check_line("effective_security", &r.effective_security),
        check_line("generator_on_curve", &r.generator_on_curve),
        check_line("non_singular", &r.non_singular),
        check_line("non_supersingular", &r.non_supersingular),
        check_line("non_anomalous", &r.non_anomalous),
        check_line("multi_target_margin", &r.multi_target_margin),
        check_line("no_weil_descent", &r.no_weil_descent),
        check_line("orbit_brittleness", &r.orbit_brittleness),
    ];
    let failed = r.failed_checks();
    if !failed.is_empty() {
        lines.push(format!("failed: {}", failed.join(", ")));
    }
    lines.join("\n")
}

/// Run the parameter audit and emit a [`SafetyReport`].
pub fn run(out: Out, a: &EccSafetyArgs) -> CmdResult {
    let curve = a.curve()?;
    let report = curve.analyse(&a.options());
    let failed = report.failed_checks();
    let status = if failed.is_empty() { "ok" } else { "fail" };
    let payload = EccSafetyOut {
        status,
        all_pass: report.all_pass(),
        failed_checks: failed,
        report: &report,
    };
    out.emit(&payload, || text_report(&report))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;

    #[derive(Parser, Debug)]
    struct TestCli {
        #[command(subcommand)]
        command: TestCmd,
    }

    #[derive(clap::Subcommand, Debug)]
    enum TestCmd {
        #[command(name = "ecc-safety", visible_alias = "ecc_safety")]
        EccSafety(EccSafetyArgs),
    }

    fn secp256k1_argv() -> [&'static str; 16] {
        [
            "test",
            "ecc-safety",
            "--p",
            "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F",
            "--a",
            "0",
            "--b",
            "7",
            "--gx",
            "0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798",
            "--gy",
            "0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8",
            "--n",
            "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141",
            "--h",
            "1",
        ]
    }

    #[test]
    fn clap_parses_ecc_safety_and_alias() {
        let cli = TestCli::try_parse_from(secp256k1_argv()).expect("ecc-safety parse");
        match cli.command {
            TestCmd::EccSafety(a) => {
                assert_eq!(a.b, "7");
                assert_eq!(a.h, "1");
                assert_eq!(a.min_order_bits, 200);
            }
        }
        let aliased = TestCli::try_parse_from([
            "test",
            "ecc_safety",
            "--p",
            "7",
            "--a=-3",
            "--b",
            "2",
            "--gx",
            "0",
            "--gy",
            "0",
            "--n",
            "1",
            "--h",
            "1",
        ])
        .expect("ecc_safety alias");
        assert!(matches!(aliased.command, TestCmd::EccSafety(_)));
    }

    #[test]
    fn secp256k1_has_no_failed_checks() {
        let cli = TestCli::try_parse_from(secp256k1_argv()).unwrap();
        let TestCmd::EccSafety(a) = cli.command;
        let report = a.curve().unwrap().analyse(&a.options());
        assert!(
            report.failed_checks().is_empty(),
            "unexpected failures: {:?}",
            report.failed_checks()
        );
        assert_eq!(report.non_singular, SafetyCheck::Pass);
        assert_eq!(report.generator_on_curve, SafetyCheck::Pass);
    }

    #[test]
    fn singular_curve_fails_non_singular() {
        let cli = TestCli::try_parse_from([
            "test",
            "ecc-safety",
            "--p",
            "7",
            "--a=-3",
            "--b",
            "2",
            "--gx",
            "0",
            "--gy",
            "0",
            "--n",
            "1",
            "--h",
            "1",
        ])
        .unwrap();
        let TestCmd::EccSafety(a) = cli.command;
        let report = a.curve().unwrap().analyse(&a.options());
        assert!(
            report.non_singular.is_fail(),
            "expected singular fail, got {:?}",
            report.non_singular
        );
        assert!(report.failed_checks().contains(&"non_singular"));
    }

    #[test]
    fn parse_bigint_accepts_signed_hex() {
        assert_eq!(parse_bigint("-3").unwrap(), BigInt::from(-3));
        assert_eq!(parse_bigint("-0x10").unwrap(), BigInt::from(-16));
        assert_eq!(parse_bigint("0xFF").unwrap(), BigInt::from(255));
    }
}
