//! `crax`: the unified command line of the toolkit.
//!
//! One binary, one subcommand per attack. The generic discrete-logarithm
//! solvers run on the C library in the repository root (64-bit groups,
//! measured constants); everything else runs on this crate's
//! arbitrary-precision attacks. Every command accepts `--json` and emits one
//! JSON object. Older research commands expose their native report text inside
//! a JSON envelope. Native solver commands independently verify answers they
//! mark solved; each research command retains its own evidence contract.
//!
//! `crax ic`, `crax icx` and the suite's cipher, hash, lattice, isogeny and
//! collaborative-rho commands are the research command lines in
//! [`tools`], handed their arguments unchanged: they keep their own flags
//! and report formats. The older binaries (`ca-ic`, `ca-icx`, `ca-suite`,
//! `ca-curves`) remain as compatible entry points to the same code.

pub mod aes_attack;
pub mod aes_sbox_table;
pub mod challenge;
pub mod curve;
pub mod digest;
pub mod dlog;
pub mod ecdlp;
pub mod ecdsa;
pub mod factor;
pub mod ic;
pub mod output;
pub mod tools;

use std::ffi::OsString;
use std::process::ExitCode;

use clap::{CommandFactory, FromArgMatches, Parser, Subcommand};

use output::{CmdResult, Out};

const OVERVIEW: &str = "\
Attacks by family:
  discrete logs (generic)   bsgs, rho, kangaroo, grumpy, precomp, glv, pohlig-hellman, cheon, gpu-rho
  weak curves (any size)    ecdlp (singular, Smart anomalous, Pohlig-Hellman, MOV/Frey-Rueck)
  factoring                 factor, gnfs, snfs, qs, ecm, pm1 (--pp1), rho-factor
  RSA                       rsa fermat|wiener|from-d|hastad|common-modulus|small-e|batch-gcd
  index calculus            ic (zp, prime, run, compare, fixed, workflow, boundary, bench, rho, ...), icx
  sibling crypto tools      ecdlp-nist, ic/icx solve-prime|solve-prime-file|solve-cubic|prime-route-generate|cubic-graph|cubic-route-generate, isogeny-walk, store, crypto
  symmetric & hash          aes-attack, aes-sbox-table, list-ciphers, auto, boomerang, rectangle, sbox, aes-related-key, hash, hash-auto, length-extension
  lattice & post-quantum    mlwe
  isogenies                 isogeny
  distributed rho           rho-collab
  demos & research bench    visual-all, aes-visual-demo, bench, ec-challenges
  curves & challenges       curve names, curve info, challenge list|show|solve|rho-job

Every command accepts --json. Native Markdown reports are wrapped as report_text in JSON mode.
`crax <command> --help` shows its options.";

/// The top-level parser.
#[derive(Parser, Debug)]
#[command(
    name = "crax",
    version,
    about = "Cryptanalysis toolkit: discrete logarithms, index calculus, factoring, weak curves, \
             symmetric, hash, lattice and post-quantum attacks",
    after_help = OVERVIEW
)]
pub struct Cli {
    /// Print one JSON object instead of text.
    #[arg(long, global = true)]
    pub json: bool,
    #[command(subcommand)]
    pub command: Command,
}

/// Every `crax` subcommand.
#[derive(Subcommand, Debug)]
pub enum Command {
    /// Recover key material on bounded AES-128 differential, linear, or integral instances.
    AesAttack(aes_attack::AesAttackArgs),
    /// Export exact AES S-box DDT, LAT, BCT, or DLCT rows or complete tables.
    AesSboxTable(aes_sbox_table::AesSboxTableArgs),
    /// Compute MD, SHA-1/2/3, SHAKE, or BLAKE3 digests from text, hex bytes, or a file.
    Hash(digest::DigestArgs),
    /// Baby-step giant-step over an interval or the whole group.
    Bsgs(dlog::IntervalArgs),
    /// Pollard rho: r-adding walk, distinguished points, negation map, threads.
    Rho(dlog::RhoArgs),
    /// Pollard kangaroo (van Oorschot-Wiener) over an interval.
    Kangaroo(dlog::IntervalArgs),
    /// Two grumpy giants and a baby (Bernstein-Lange).
    Grumpy(dlog::IntervalArgs),
    /// Discrete logs with a Bernstein-Lange precomputed table.
    Precomp(dlog::PrecompArgs),
    /// Rho folded by the GLV endomorphism of a j = 0 / 1728 curve.
    Glv(dlog::GlvArgs),
    /// Pohlig-Hellman over the factorised group order.
    #[command(visible_aliases = ["ph", "dlog"])]
    PohligHellman(dlog::PohligArgs),
    /// Cheon's attack on the strong Diffie-Hellman problem.
    Cheon(dlog::CheonArgs),
    /// ECDLP on prime-field curves of any size: analyse, then the cheapest
    /// structural attack (singular, Smart, Pohlig-Hellman, MOV).
    Ecdlp(ecdlp::EcdlpArgs),
    /// Pollard rho on the GPU kernel (CUDA, or its host emulator).
    GpuRho(dlog::GpuRhoArgs),
    /// Factor an integer completely: trial division, rho, p-1, ECM, SIQS,
    /// SNFS/GNFS, each factor verified.
    Factor(factor::FactorArgs),
    /// General number field sieve (base-m polynomial selection).
    Gnfs(factor::GnfsArgs),
    /// Special number field sieve for n dividing c*r^e + s.
    Snfs(factor::SnfsArgs),
    /// Self-initialising multiple-polynomial quadratic sieve.
    Qs(factor::QsArgs),
    /// Lenstra's elliptic-curve method.
    Ecm(factor::EcmArgs),
    /// Pollard p-1 (or Williams p+1 with --pp1).
    Pm1(factor::Pm1Args),
    /// Pollard-Brent rho for integer factoring.
    RhoFactor(factor::RhoFactorArgs),
    /// Classic RSA attacks: Fermat, Wiener, d -> p,q, Hastad, common
    /// modulus, small e, batch GCD.
    #[command(subcommand)]
    Rsa(factor::RsaCmd),
    /// Curve registry and structure.
    #[command(subcommand)]
    Curve(curve::CurveCmd),
    /// ECDSA signature attacks: nonce reuse, biased-nonce HNP, transcript
    /// audit, and the oracle invalid-curve attack.
    #[command(subcommand)]
    Ecdsa(ecdsa::EcdsaCmd),
    /// The elliptic-curve challenge corpus: list, show, solve.
    Challenge(challenge::ChallengeArgs),
}

/// `crax ic zp`, parsed by `crax` itself so that it prints like the other
/// generic solvers.
#[derive(Parser, Debug)]
#[command(
    name = "crax ic zp",
    about = "Discrete logs in (Z/pZ)^* by the linear sieve (p < 2^63)"
)]
struct IcZpCli {
    /// Print one JSON object instead of text.
    #[arg(long)]
    json: bool,
    #[command(flatten)]
    args: ic::ZpArgs,
}

/// Which research command line a subcommand belongs to.
enum Tool {
    Ic,
    Icx,
    Suite,
}

/// The suite subcommands `crax` hands to [`tools::suite`].
fn suite_commands() -> Vec<String> {
    tools::suite::Cli::command()
        .get_subcommands()
        .map(|c| c.get_name().to_string())
        .collect()
}

fn tool_for(sub: &str) -> Option<Tool> {
    match sub {
        "ic" => Some(Tool::Ic),
        "icx" => Some(Tool::Icx),
        s if suite_commands().iter().any(|c| c == s) => Some(Tool::Suite),
        _ => None,
    }
}

/// Resolve an optional sibling executable in a release bundle. An explicit
/// override wins; otherwise a binary beside `crax` wins over `PATH`.
pub(crate) fn sibling_binary(env_name: &str, default_binary: &str) -> OsString {
    if let Some(binary) = std::env::var_os(env_name) {
        return binary;
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            let adjacent = dir.join(default_binary);
            if adjacent.is_file() {
                return adjacent.into_os_string();
            }
        }
    }
    default_binary.into()
}

/// Bridge the sibling crypto executables without a shell. This keeps the
/// public-target EC IC, isogeny-walk, and artifact-store surfaces reachable
/// from `crax` while preserving the producing executable's exit status.
fn run_external(
    env_name: &str,
    default_binary: &str,
    sub: &str,
    args: &[OsString],
    json_requested: bool,
    pass_json: bool,
) -> ExitCode {
    let binary = sibling_binary(env_name, default_binary);
    let mut native_args: Vec<OsString> = args
        .iter()
        .filter(|arg| arg.as_os_str() != std::ffi::OsStr::new("--json"))
        .cloned()
        .collect();
    if json_requested && pass_json {
        native_args.push("--json".into());
    }
    let mut command = std::process::Command::new(&binary);
    command.args(&native_args);
    if json_requested {
        match command.output() {
            Ok(output) => {
                let ok = output.status.success();
                let report: serde_json::Value = serde_json::from_slice(&output.stdout)
                    .unwrap_or_else(|_| serde_json::Value::Null);
                let report_text = report
                    .is_null()
                    .then(|| String::from_utf8_lossy(&output.stdout).to_string());
                println!(
                    "{}",
                    serde_json::json!({
                        "status": if ok { "ok" } else { "error" },
                        "command": sub,
                        "exit_code": output.status.code(),
                        "report": report,
                        "report_text": report_text,
                        "diagnostics_text": String::from_utf8_lossy(&output.stderr),
                    })
                );
                ExitCode::from(output.status.code().unwrap_or(1) as u8)
            }
            Err(e) => {
                println!(
                    "{}",
                    serde_json::json!({"status":"error","command":sub,"error":format!("starting {}: {e}", binary.to_string_lossy())})
                );
                ExitCode::FAILURE
            }
        }
    } else {
        match command.status() {
            Ok(status) => ExitCode::from(status.code().unwrap_or(1) as u8),
            Err(e) => {
                eprintln!("error: starting {}: {e}", binary.to_string_lossy());
                ExitCode::FAILURE
            }
        }
    }
}

/// Run a legacy suite command as a child so its native stdout and diagnostics
/// can be reported as exactly one JSON object without changing its parser or
/// allowing an inner `process::exit` to terminate the unified dispatcher.
fn run_suite_json(sub: &str, args: &[OsString]) -> ExitCode {
    let exe = match std::env::current_exe() {
        Ok(path) => path,
        Err(e) => {
            println!(
                "{}",
                serde_json::json!({"status":"error","error":format!("locating crax: {e}")})
            );
            return ExitCode::FAILURE;
        }
    };
    let output = std::process::Command::new(exe).arg(sub).args(args).output();
    match output {
        Ok(output) => {
            let ok = output.status.success();
            println!(
                "{}",
                serde_json::json!({
                    "status": if ok { "ok" } else { "error" },
                    "command": sub,
                    "exit_code": output.status.code(),
                    "report_text": String::from_utf8_lossy(&output.stdout),
                    "diagnostics_text": String::from_utf8_lossy(&output.stderr),
                })
            );
            ExitCode::from(output.status.code().unwrap_or(1) as u8)
        }
        Err(e) => {
            println!(
                "{}",
                serde_json::json!({"status":"error","error":format!("starting crax: {e}")})
            );
            ExitCode::FAILURE
        }
    }
}

/// The full command tree, for `--help`: `crax`'s own subcommands plus the
/// research command lines, grafted in under their `crax` names.
pub fn command() -> clap::Command {
    // crax's own subcommands first, in declaration order; the research
    // command lines after them.
    let mut cmd = Cli::command();
    let own: Vec<String> = cmd
        .get_subcommands()
        .map(|c| c.get_name().to_string())
        .collect();
    for (i, name) in own.iter().enumerate() {
        cmd = cmd.mut_subcommand(name, |c| c.display_order(i));
    }
    let mut cmd = cmd
        .subcommand(
            tools::ic::Cli::command()
                .name("ic")
                .about("Index calculus: prime-field curves by type, Koblitz curves, fixed K_0 runs, boundary pricing, (Z/pZ)^* (`ic zp`)"),
        )
        .subcommand(
            tools::icx::Cli::command()
                .name("icx")
                .about("Index calculus across every standardized curve: catalog, estimate, run"),
        )
        .subcommand(clap::Command::new("crypto").about("Bridge to the sibling crypto CLI"))
        .subcommand(clap::Command::new("ecdlp-nist").about("NIST and Certicom ECDLP audit and bounded solve via crypto"))
        .subcommand(clap::Command::new("store").about("Content-addressed artifact store via crypto"))
        .subcommand(clap::Command::new("isogeny-walk").about("Certified isogeny graph CLI"));
    for sub in tools::suite::Cli::command().get_subcommands() {
        cmd = cmd.subcommand(sub.clone());
    }
    let n = own.len();
    for (i, name) in ["ic", "icx"].iter().enumerate() {
        cmd = cmd.mut_subcommand(name, |c| c.display_order(n + i));
    }
    for (i, name) in suite_commands().iter().enumerate() {
        cmd = cmd.mut_subcommand(name, |c| c.display_order(n + 2 + i));
    }
    cmd
}

/// Die quietly on a closed pipe (`crax ... | head`) as command-line tools
/// do, instead of panicking in `println!`.
pub fn default_sigpipe() {
    #[cfg(unix)]
    // SAFETY: restoring the default disposition of one signal before any
    // thread is started; no handler runs Rust code.
    unsafe {
        libc::signal(libc::SIGPIPE, libc::SIG_DFL);
    }
}

/// Run one parsed command.
pub fn run(out: Out, cmd: Command) -> CmdResult {
    use dlog::IntervalSolver;
    match cmd {
        Command::AesAttack(a) => aes_attack::run(out, &a),
        Command::AesSboxTable(a) => aes_sbox_table::run(out, &a),
        Command::Hash(a) => digest::run(out, &a),
        Command::Bsgs(a) => dlog::run_interval(out, IntervalSolver::Bsgs, &a),
        Command::Rho(a) => dlog::run_rho(out, &a),
        Command::Kangaroo(a) => dlog::run_interval(out, IntervalSolver::Kangaroo, &a),
        Command::Grumpy(a) => dlog::run_interval(out, IntervalSolver::Grumpy, &a),
        Command::Precomp(a) => dlog::run_precomp(out, &a),
        Command::Glv(a) => dlog::run_glv(out, &a),
        Command::PohligHellman(a) => dlog::run_pohlig(out, &a),
        Command::Cheon(a) => dlog::run_cheon(out, &a),
        Command::Ecdlp(a) => ecdlp::run(out, &a),
        Command::GpuRho(a) => dlog::run_gpu_rho(out, &a),
        Command::Factor(a) => factor::run_factor(out, &a),
        Command::Gnfs(a) => factor::run_gnfs(out, &a),
        Command::Snfs(a) => factor::run_snfs(out, &a),
        Command::Qs(a) => factor::run_qs(out, &a),
        Command::Ecm(a) => factor::run_ecm(out, &a),
        Command::Pm1(a) => factor::run_pm1(out, &a),
        Command::RhoFactor(a) => factor::run_rho_factor(out, &a),
        Command::Rsa(c) => factor::run_rsa(out, &c),
        Command::Curve(c) => curve::run(out, &c),
        Command::Ecdsa(c) => ecdsa::run(out, &c),
        Command::Challenge(a) => challenge::run(out, &a),
    }
}

/// Entry point of the `crax` binary.
pub fn main() -> ExitCode {
    default_sigpipe();
    main_from(std::env::args_os())
}

/// Run `crax` on `args` (the first item is the program name).
pub fn main_from<I, T>(args: I) -> ExitCode
where
    I: IntoIterator<Item = T>,
    T: Into<OsString> + Clone,
{
    let args: Vec<OsString> = args.into_iter().map(Into::into).collect();
    // A leading --json belongs to crax; the research tools take theirs after
    // the subcommand, so move it there.
    let lead_json = args.get(1).is_some_and(|a| a == "--json");
    let rest: Vec<OsString> = args
        .iter()
        .skip(if lead_json { 2 } else { 1 })
        .cloned()
        .collect();
    let sub = rest.first().and_then(|a| a.to_str()).unwrap_or("");
    let requested_json = lead_json || rest.iter().skip(1).any(|a| a == "--json");
    match sub {
        "ecdlp-nist" => {
            return run_external(
                "CRAX_ECDLP_NIST_BIN",
                "ecdlp-nist",
                sub,
                &rest[1..],
                requested_json,
                true,
            )
        }
        "crypto" => {
            return run_external(
                "CRAX_CRYPTO_BIN",
                "crypto",
                sub,
                &rest[1..],
                requested_json,
                false,
            )
        }
        "store" => {
            return run_external(
                "CRAX_CRYPTO_BIN",
                "crypto",
                sub,
                &rest,
                requested_json,
                true,
            )
        }
        "isogeny-walk" => {
            return run_external(
                "CRAX_ISOGENY_WALK_BIN",
                "isogeny_walk",
                sub,
                &rest[1..],
                requested_json,
                false,
            )
        }
        "icx"
            if matches!(
                rest.get(1).and_then(|a| a.to_str()),
                Some(
                    "solve-prime"
                        | "solve-prime-file"
                        | "solve-cubic"
                        | "prime-route-generate"
                        | "cubic-graph"
                        | "cubic-route-generate"
                )
            ) =>
        {
            return run_external("CRAX_ICX_BIN", "icx", sub, &rest[1..], requested_json, true);
        }
        "ic" if matches!(
            rest.get(1).and_then(|a| a.to_str()),
            Some(
                "solve-prime"
                    | "solve-prime-file"
                    | "solve-cubic"
                    | "prime-route-generate"
                    | "cubic-graph"
                    | "cubic-route-generate"
            )
        ) =>
        {
            return run_external("CRAX_IC_BIN", "ic", sub, &rest[1..], requested_json, true);
        }
        _ => {}
    }
    if let Some(tool) = tool_for(sub) {
        if matches!(tool, Tool::Suite) && (lead_json || rest.iter().skip(1).any(|a| a == "--json"))
        {
            let native_args: Vec<OsString> = rest
                .iter()
                .skip(1)
                .filter(|a| *a != "--json")
                .cloned()
                .collect();
            return run_suite_json(sub, &native_args);
        }
        let is_zp = matches!(tool, Tool::Ic) && rest.get(1).is_some_and(|a| a == "zp");
        if !is_zp {
            let mut argv: Vec<OsString> = vec![format!("crax {sub}").into()];
            argv.extend(rest[1..].iter().cloned());
            if lead_json && !matches!(tool, Tool::Suite) {
                argv.push("--json".into());
            }
            return match tool {
                Tool::Ic => tools::ic::run_from(argv),
                Tool::Icx => tools::icx::run_from(argv),
                Tool::Suite => {
                    let mut argv = argv;
                    argv[0] = "crax".into();
                    argv.insert(1, sub.into());
                    tools::suite::run_from(argv)
                }
            };
        }
        let mut argv: Vec<OsString> = vec!["crax ic zp".into()];
        argv.extend(rest[2..].iter().cloned());
        if lead_json {
            argv.push("--json".into());
        }
        let z = IcZpCli::parse_from(argv);
        return finish(
            Out { json: z.json },
            ic::run_zp(Out { json: z.json }, &z.args),
        );
    }
    let matches = command().get_matches_from(&args);
    let cli = match Cli::from_arg_matches(&matches) {
        Ok(c) => c,
        Err(e) => e.exit(),
    };
    let out = Out { json: cli.json };
    finish(out, run(out, cli.command))
}

fn finish(out: Out, r: CmdResult) -> ExitCode {
    match r {
        Ok(()) => ExitCode::SUCCESS,
        Err(f) => {
            if f.reported {
                eprintln!("error: {}", f.message);
            } else if out.json {
                println!(
                    "{}",
                    serde_json::json!({ "status": "error", "error": f.message })
                );
            } else {
                eprintln!("error: {}", f.message);
            }
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::CommandFactory;

    #[test]
    fn the_command_tree_is_well_formed() {
        Cli::command().debug_assert();
        command().debug_assert();
        IcZpCli::command().debug_assert();
    }

    #[test]
    fn research_tools_are_routed_by_name() {
        assert!(matches!(tool_for("ic"), Some(Tool::Ic)));
        assert!(matches!(tool_for("icx"), Some(Tool::Icx)));
        for s in ["auto", "mlwe", "rho-collab", "isogeny", "list-ciphers"] {
            assert!(matches!(tool_for(s), Some(Tool::Suite)), "{s}");
        }
        assert!(tool_for("rho").is_none());
        // No crax subcommand shadows a research tool's.
        let own: Vec<String> = Cli::command()
            .get_subcommands()
            .map(|c| c.get_name().to_string())
            .collect();
        for s in suite_commands() {
            assert!(!own.contains(&s), "{s} is both a crax and a suite command");
        }
    }
}
