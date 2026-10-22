//! Integer factoring and RSA attacks: `crax factor | gnfs | snfs | qs |
//! ecm | pm1 | rho-factor | rsa ...`.
//!
//! These run [`crate::cryptanalysis::factoring`]: a general and a special
//! number field sieve, the self-initialising quadratic sieve, Pollard
//! p-1 / Williams p+1, Pollard-Brent rho, Lenstra ECM, the classic RSA
//! attacks, and a full-factorisation ladder that picks among them. Every
//! reported factor has been checked by multiplication. Integers may be
//! written as expressions: `2^227-1`, `(2^239+1)/3`, `3*10^40+7`.

use clap::{Args, Subcommand};
use num_bigint::{BigInt, BigUint};
use num_integer::Integer;
use num_traits::{One, Zero};
use serde::{Deserialize, Serialize};
use std::cell::{Cell, RefCell};
use std::fs::{self, File, OpenOptions};
use std::io::Write;
#[cfg(unix)]
use std::os::fd::AsRawFd;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::{mpsc, Arc, Mutex};
use std::thread::JoinHandle;
use std::time::{Duration, Instant};

use super::output::{CmdResult, Failure, Out};
use crate::cryptanalysis::factoring::nfs::snfs::SnfsInput;
use crate::cryptanalysis::factoring::{
    self,
    nfs::{gnfs::GnfsParams, snfs::SnfsParams, NfsParams, NfsReport},
    pm1::{Pm1Params, Pp1Params},
    qs::{QsParams, QsReport},
    rho_factor::RhoParams,
    rsa_attacks, FactorOptions, FactorReport, Progress,
};

// ---- integer expressions --------------------------------------------------

/// Parse an integer expression: decimal or 0x literals, `+ - * / ^` and
/// parentheses. Division must be exact; the result must be non-negative.
pub fn parse_expr(s: &str) -> Result<BigUint, String> {
    let toks: Vec<char> = s
        .chars()
        .filter(|c| !c.is_whitespace() && *c != '_')
        .collect();
    let mut p = Parser { t: &toks, i: 0 };
    let v = p.sum()?;
    if p.i != toks.len() {
        return Err(format!("unexpected {:?} in {s:?}", toks[p.i]));
    }
    v.to_biguint().ok_or_else(|| format!("{s:?} is negative"))
}

struct Parser<'a> {
    t: &'a [char],
    i: usize,
}

impl Parser<'_> {
    fn peek(&self) -> Option<char> {
        self.t.get(self.i).copied()
    }
    fn sum(&mut self) -> Result<BigInt, String> {
        let mut v = self.product()?;
        while let Some(c @ ('+' | '-')) = self.peek() {
            self.i += 1;
            let r = self.product()?;
            v = if c == '+' { v + r } else { v - r };
        }
        Ok(v)
    }
    fn product(&mut self) -> Result<BigInt, String> {
        let mut v = self.power()?;
        while let Some(c @ ('*' | '/')) = self.peek() {
            self.i += 1;
            let r = self.power()?;
            if c == '*' {
                v *= r;
            } else {
                if r.is_zero() {
                    return Err("division by zero".into());
                }
                let (q, rem) = v.div_rem(&r);
                if !rem.is_zero() {
                    return Err(format!("{v} is not divisible by {r}"));
                }
                v = q;
            }
        }
        Ok(v)
    }
    fn power(&mut self) -> Result<BigInt, String> {
        let base = self.atom()?;
        if self.peek() == Some('^') {
            self.i += 1;
            let e = self.power()?;
            let e = u32::try_from(&e).map_err(|_| format!("exponent {e} out of range"))?;
            if e > 100_000 {
                return Err(format!("exponent {e} is too large"));
            }
            return Ok(base.pow(e));
        }
        Ok(base)
    }
    fn atom(&mut self) -> Result<BigInt, String> {
        match self.peek() {
            Some('(') => {
                self.i += 1;
                let v = self.sum()?;
                if self.peek() != Some(')') {
                    return Err("missing ')'".into());
                }
                self.i += 1;
                Ok(v)
            }
            Some('-') => {
                self.i += 1;
                Ok(-self.atom()?)
            }
            Some(c) if c.is_ascii_digit() => {
                let start = self.i;
                let hex = c == '0' && matches!(self.t.get(self.i + 1), Some('x' | 'X'));
                if hex {
                    self.i += 2;
                }
                while self.peek().is_some_and(|c| {
                    if hex {
                        c.is_ascii_hexdigit()
                    } else {
                        c.is_ascii_digit()
                    }
                }) {
                    self.i += 1;
                }
                let lit: String = self.t[start..self.i].iter().collect();
                let v = if hex {
                    BigInt::parse_bytes(&lit.as_bytes()[2..], 16)
                } else {
                    BigInt::parse_bytes(lit.as_bytes(), 10)
                };
                v.ok_or_else(|| format!("bad number {lit:?}"))
            }
            other => Err(format!("expected a number, found {other:?}")),
        }
    }
}

/// Parse an SNFS form `(c*)r^e(+|-)s`, e.g. `2^227-1`, `3*10^80+7`.
pub fn parse_form(s: &str) -> Result<SnfsInput, String> {
    let t: String = s.chars().filter(|c| !c.is_whitespace()).collect();
    let bad = || format!("expected an SNFS form [c*]r^e+s or [c*]r^e-s, got {s:?}");
    let (head, sign, tail) = match t.rfind(['+', '-']) {
        Some(i) if i > 0 => (&t[..i], &t[i..i + 1], &t[i + 1..]),
        _ => return Err(bad()),
    };
    let (c, re) = match head.split_once('*') {
        Some((c, re)) => (c.parse::<u64>().map_err(|_| bad())?, re),
        None => (1, head),
    };
    let (r, e) = re.split_once('^').ok_or_else(bad)?;
    let s_abs: i64 = tail.parse().map_err(|_| bad())?;
    Ok(SnfsInput::Form {
        r: r.parse().map_err(|_| bad())?,
        e: e.parse().map_err(|_| bad())?,
        s: if sign == "-" { -s_abs } else { s_abs },
        c,
    })
}

fn progress_printer(verbose: bool) -> Option<impl Fn(&Progress)> {
    verbose.then_some(|p: &Progress| {
        eprintln!(
            "[{:>8.2}s] {:<10} {}/{}",
            p.seconds, p.stage, p.done, p.target
        )
    })
}

fn digits(n: &BigUint) -> usize {
    n.to_str_radix(10).len()
}

/// Refuse a size the implementation cannot finish in reasonable time
/// unless `--force` is given: these are educational sieves (see the
/// module docs), not CADO-NFS or msieve.
fn size_guard(n: &BigUint, method: &str, max: usize, force: bool) -> Result<(), String> {
    let d = digits(n);
    if d > max && !force {
        return Err(format!(
            "{method}: n has {d} digits; this implementation is practical up to about {max} \
             (measured: GNFS 55 digits ~18 s, 59 digits ~2 min; SIQS 60 digits ~16 s). \
             Pass --force to run it anyway."
        ));
    }
    Ok(())
}

fn split_line(n: &BigUint, f: &Option<BigUint>, c: &Option<BigUint>, verified: bool) -> String {
    match (f, c) {
        (Some(f), Some(c)) => format!(
            "{n} ({} digits) = {f} * {c}  ({})",
            digits(n),
            if verified { "verified" } else { "NOT VERIFIED" }
        ),
        _ => format!("{n} ({} digits): no factor found", digits(n)),
    }
}

fn verdict(verified: bool, found: bool, what: &str) -> CmdResult {
    match (found, verified) {
        (true, true) => Ok(()),
        (true, false) => Err(Failure::reported(format!("{what}: factor not verified"))),
        (false, _) => Err(Failure::reported(format!("{what}: no factor found"))),
    }
}

// ---- crax factor -----------------------------------------------------------

#[derive(Args, Clone, Debug)]
pub struct FactorArgs {
    /// The integer (an expression such as 2^227-1 is accepted).
    pub n: String,
    /// n divides this SNFS form ((c*)r^e+s), enabling the special sieve.
    #[arg(long)]
    pub snfs_form: Option<String>,
    /// Use the number field sieve instead of the quadratic sieve from
    /// --nfs-min-digits on (the QS is faster at every size here).
    #[arg(long)]
    pub prefer_nfs: bool,
    /// Also run Williams p+1.
    #[arg(long)]
    pub pp1: bool,
    /// Largest cofactor size the quadratic sieve takes, in digits.
    #[arg(long)]
    pub qs_max_digits: Option<usize>,
    #[arg(long, default_value_t = 1)]
    pub threads: usize,
    #[arg(long, default_value_t = 1)]
    pub seed: u64,
    /// Print factoring stage changes and periodic work counts on stderr.
    #[arg(long)]
    pub verbose: bool,
    /// Seconds between heartbeat lines (implies --verbose).
    #[arg(long, value_parser = clap::value_parser!(u64).range(1..))]
    pub progress_every: Option<u64>,
    /// Dedicated directory for the full ladder and inner sieve checkpoints.
    #[arg(long)]
    pub state_dir: Option<PathBuf>,
    /// Continue saved cofactors and methods, restoring from S3 if needed.
    #[arg(long)]
    pub resume: bool,
    /// Seconds between inner sieve checkpoint writes (0 saves every batch).
    #[arg(long)]
    pub checkpoint_every: Option<u64>,
    /// Mirror checkpoints and final artifacts to this S3 prefix.
    #[arg(long)]
    pub s3_uri: Option<String>,
    /// Seconds between S3 copies; final sync is always attempted.
    #[arg(long, value_parser = clap::value_parser!(u64).range(1..))]
    pub sync_every: Option<u64>,
}

fn factor_text(r: &FactorReport) -> String {
    let mut s = format!("{} ({} digits) =", r.n, digits(&r.n));
    let parts: Vec<String> = r
        .factors
        .iter()
        .map(|f| {
            let e = if f.exponent > 1 {
                format!("^{}", f.exponent)
            } else {
                String::new()
            };
            format!(" {}{e}", f.prime)
        })
        .chain(r.unfactored.iter().map(|(c, e)| {
            format!(
                " [{c}]{}",
                if *e > 1 {
                    format!("^{e}")
                } else {
                    String::new()
                }
            )
        }))
        .collect();
    s += &parts.join(" *");
    s += &format!(
        "\n  {} ({:.3} s)\n",
        match (r.complete, r.verified) {
            (true, true) => "complete, product verified",
            (false, true) => "INCOMPLETE: bracketed composites were not split",
            _ => "NOT VERIFIED",
        },
        r.total_seconds
    );
    for f in &r.factors {
        s += &format!(
            "  {:<40} {:?}{}\n",
            f.prime.to_string(),
            f.method,
            if f.proven {
                ", proven prime"
            } else {
                ", probable prime"
            }
        );
    }
    s
}

fn factor_stage(method: factoring::Method) -> &'static str {
    match method {
        factoring::Method::Primality => "primality",
        factoring::Method::TrialDivision => "trial",
        factoring::Method::PerfectPower => "power",
        factoring::Method::Rho => "rho",
        factoring::Method::PMinus1 => "p-1",
        factoring::Method::PPlus1 => "p+1",
        factoring::Method::Ecm => "ecm",
        factoring::Method::Qs => "qs",
        factoring::Method::Gnfs => "gnfs",
        factoring::Method::Snfs => "snfs",
    }
}

#[derive(Serialize, Deserialize)]
struct FactorCheckpointFile {
    checksum: String,
    fingerprint: String,
    payload: String,
}

fn save_factor_checkpoint(
    path: &Path,
    fingerprint: &str,
    state: &factoring::auto::FactorState,
) -> Result<(), String> {
    let payload =
        serde_json::to_string(state).map_err(|e| format!("serializing factor state: {e}"))?;
    write_json_atomic(
        path,
        &FactorCheckpointFile {
            checksum: blake3::hash(payload.as_bytes()).to_hex().to_string(),
            fingerprint: fingerprint.into(),
            payload,
        },
    )
}

fn load_factor_checkpoint(
    path: &Path,
    fingerprint: &str,
    n: &BigUint,
) -> Result<factoring::auto::FactorState, String> {
    let bytes = fs::read(path).map_err(|e| format!("reading factor checkpoint: {e}"))?;
    decode_factor_checkpoint(&bytes, fingerprint, n)
}

fn decode_factor_checkpoint(
    bytes: &[u8],
    fingerprint: &str,
    n: &BigUint,
) -> Result<factoring::auto::FactorState, String> {
    let saved: FactorCheckpointFile =
        serde_json::from_slice(bytes).map_err(|e| format!("invalid factor checkpoint: {e}"))?;
    if saved.checksum != blake3::hash(saved.payload.as_bytes()).to_hex().as_str() {
        return Err("factor checkpoint checksum mismatch".into());
    }
    if saved.fingerprint != fingerprint {
        return Err("factor checkpoint parameters differ".into());
    }
    let state: factoring::auto::FactorState = serde_json::from_str(&saved.payload)
        .map_err(|e| format!("invalid factor checkpoint payload: {e}"))?;
    if state.schema_version != 1
        || state.generation == 0
        || &state.report.n != n
        || !state.elapsed_seconds.is_finite()
        || state.elapsed_seconds < 0.0
        || !state.report.total_seconds.is_finite()
        || state.report.total_seconds < 0.0
        || state
            .active
            .as_ref()
            .is_some_and(|active| active.attempt_seed.is_some() != active.attempt_method.is_some())
    {
        return Err("invalid factor checkpoint identity or time".into());
    }
    let mut product = BigUint::one();
    let mut include = |piece: &BigUint, exponent: u32| -> Result<(), String> {
        if piece.is_zero() || exponent == 0 || u64::from(exponent) > n.bits() {
            return Err("invalid factor checkpoint piece".into());
        }
        product *= piece.pow(exponent);
        if &product > n {
            return Err("factor checkpoint pieces exceed input".into());
        }
        Ok(())
    };
    for factor in &state.report.factors {
        include(&factor.prime, factor.exponent)?;
    }
    for (piece, exponent) in &state.report.unfactored {
        include(
            &piece
                .parse()
                .map_err(|_| "invalid unfactored checkpoint piece")?,
            *exponent,
        )?;
    }
    for piece in &state.pending {
        include(&piece.n, piece.multiplicity)?;
    }
    if let Some(active) = &state.active {
        include(&active.piece.n, active.piece.multiplicity)?;
    }
    if product != *n {
        return Err("factor checkpoint pieces do not multiply to input".into());
    }
    Ok(state)
}

pub fn run_factor(out: Out, a: &FactorArgs) -> CmdResult {
    let n = parse_expr(&a.n)?;
    if n.is_zero() {
        return Err("cannot factor 0".into());
    }
    let mut o = FactorOptions {
        prefer_nfs: a.prefer_nfs,
        seed: a.seed,
        ..FactorOptions::default()
    };
    if let Some(f) = &a.snfs_form {
        o.snfs_form = Some(parse_form(f)?);
    }
    if a.pp1 {
        o.pp1 = Some(Pp1Params::default());
    }
    if let Some(d) = a.qs_max_digits {
        o.qs_max_digits = d;
    }
    o.qs.threads = a.threads.max(1);
    o.gnfs.nfs.threads = a.threads.max(1);
    o.snfs.nfs.threads = a.threads.max(1);
    let cadence = a
        .checkpoint_every
        .unwrap_or(60)
        .min(a.sync_every.unwrap_or(u64::MAX));
    o.qs.checkpoint_every_secs = cadence;
    o.gnfs.nfs.checkpoint_every_secs = cadence;
    o.snfs.nfs.checkpoint_every_secs = cadence;
    let manifest = serde_json::json!({
        "schema_version": 1, "method": "factor", "n": n.to_string(),
        "snfs_form": o.snfs_form, "prefer_nfs": a.prefer_nfs,
        "pp1": a.pp1, "qs_max_digits": o.qs_max_digits,
        "threads": a.threads.max(1), "seed": a.seed,
    });
    let fingerprint = blake3::hash(&serde_json::to_vec(&manifest).map_err(|e| e.to_string())?)
        .to_hex()
        .to_string();
    let state = FactoringRun::prepare(
        &RunOptions {
            state_dir: a.state_dir.clone(),
            resume: a.resume,
            s3_uri: a.s3_uri.clone(),
            sync_every: a.sync_every,
            checkpoint_every: a.checkpoint_every,
            verbose: a.verbose,
            progress_every: a.progress_every,
            checkpoint_name: "factor.ckpt",
        },
        "factor",
        manifest,
    )?;
    let initial = if a.resume {
        let dir = state.dir.as_ref().ok_or("--resume requires --state-dir")?;
        Some(load_factor_checkpoint(
            &dir.join("factor.ckpt"),
            &fingerprint,
            &n,
        )?)
    } else {
        None
    };
    if let (Some(local), Some(uri)) = (&initial, &state.s3_uri) {
        if s3_has_object(uri, "factor.ckpt")? {
            let remote_bytes = aws(&[
                "s3",
                "cp",
                &format!("{uri}/factor.ckpt"),
                "-",
                "--only-show-errors",
            ])?
            .stdout;
            let remote = decode_factor_checkpoint(&remote_bytes, &fingerprint, &n)?;
            if remote.generation > local.generation {
                return Err(
                    "S3 factor checkpoint is ahead of local state; restore into a fresh directory"
                        .into(),
                );
            }
            if remote.generation == local.generation {
                let local_bytes = fs::read(state.dir.as_ref().unwrap().join("factor.ckpt"))
                    .map_err(|e| format!("reading local factor checkpoint: {e}"))?;
                if remote_bytes != local_bytes {
                    return Err(
                        "S3 and local factor checkpoints diverge at the same generation".into(),
                    );
                }
            }
        }
    }
    let verbose = a.verbose || a.progress_every.is_some();
    let heartbeat = verbose.then(|| StageHeartbeat::start("factor", a.progress_every.unwrap_or(5)));
    let progress = |p: &Progress| {
        if let Some(print) = progress_printer(verbose) {
            print(p);
        }
        if let Some(heartbeat) = &heartbeat {
            heartbeat.update(p);
        }
        state.progress("factor", p);
    };
    let save = |checkpoint: &factoring::auto::FactorState| -> Result<(), String> {
        let active = checkpoint.active.as_ref();
        let stage = active
            .and_then(|piece| piece.attempt_method)
            .map(factor_stage)
            .unwrap_or("cofactor");
        let stage_progress = Progress {
            stage,
            done: checkpoint.report.steps.len() as u64,
            target: 0,
            seconds: checkpoint.elapsed_seconds,
        };
        if let Some(heartbeat) = &heartbeat {
            heartbeat.update(&stage_progress);
        }
        if verbose {
            eprintln!(
                "[factor] {:.1}s stage={stage} prime-powers={} pending={} active={} method-index={}",
                checkpoint.elapsed_seconds,
                checkpoint.report.factors.len(),
                checkpoint.pending.len(),
                active.map_or_else(|| "none".into(), |p| p.piece.n.to_string()),
                active.map_or(0, |p| p.next_method)
            );
        }
        if let Some(dir) = &state.dir {
            save_factor_checkpoint(&dir.join("factor.ckpt"), &fingerprint, checkpoint)?;
            state.progress("factor", &stage_progress);
            write_json_atomic(
                &dir.join("progress.json"),
                &serde_json::json!({
                    "stage": stage, "active": active.map(|p| p.piece.n.to_string()),
                    "method_index": active.map(|p| p.next_method),
                    "prime_powers": checkpoint.report.factors.len(),
                    "pending": checkpoint.pending.len(),
                    "steps": checkpoint.report.steps.len(),
                    "seconds": checkpoint.elapsed_seconds,
                }),
            )?;
        }
        Ok(())
    };
    let r = factoring::auto::factor_with_state(
        &n,
        &o,
        (verbose || state.dir.is_some()).then_some(&progress as &dyn Fn(&Progress)),
        initial,
        state.dir.as_deref(),
        Some(&save),
    )?;
    state.finish(&r, r.verified)?;
    out.emit(&r, || factor_text(&r))?;
    match (r.complete, r.verified) {
        (true, true) => Ok(()),
        (_, false) => Err(Failure::reported("the factors do not multiply back to n")),
        (false, true) => Err(Failure::reported(
            "incomplete: some composite parts were not split",
        )),
    }
}

// ---- number field sieves ---------------------------------------------------

#[derive(Args, Clone, Debug)]
pub struct NfsArgs {
    /// Rational factor-base bound (default: from the size of n).
    #[arg(long)]
    pub rational_bound: Option<u64>,
    /// Algebraic factor-base bound (default: from the size of n).
    #[arg(long)]
    pub algebraic_bound: Option<u64>,
    /// Sieve half-width in a (default: from the size of n).
    #[arg(long)]
    pub sieve_half_width: Option<u64>,
    /// Sieving threads.
    #[arg(long, default_value_t = 1)]
    pub threads: usize,
    /// Stop after this many sieve lines; raise on resume to continue.
    #[arg(long)]
    pub max_b: Option<u64>,
    /// Stage progress on stderr.
    #[arg(long)]
    pub verbose: bool,
    /// Seconds between heartbeats during a stage with no new work reports.
    #[arg(long, value_parser = clap::value_parser!(u64).range(1..))]
    pub progress_every: Option<u64>,
    /// Dedicated directory for atomic NFS relation checkpoints and reports.
    #[arg(long)]
    pub state_dir: Option<PathBuf>,
    /// Continue from the relation checkpoint in --state-dir (or restore it from S3).
    #[arg(long)]
    pub resume: bool,
    /// Seconds between local checkpoint writes (0 saves every sieve batch).
    #[arg(long)]
    pub checkpoint_every: Option<u64>,
    /// Mirror the run directory to this S3 prefix with the AWS CLI.
    #[arg(long)]
    pub s3_uri: Option<String>,
    /// Seconds between S3 syncs; the final sync is always attempted.
    #[arg(long)]
    pub sync_every: Option<u64>,
    /// Run even above the size this implementation is practical for.
    #[arg(long)]
    pub force: bool,
}

impl NfsArgs {
    fn params(&self) -> NfsParams {
        NfsParams {
            rational_bound: self.rational_bound,
            algebraic_bound: self.algebraic_bound,
            sieve_half_width: self.sieve_half_width,
            threads: self.threads.max(1),
            max_b: self.max_b,
            checkpoint_path: self.state_dir.as_ref().map(|dir| dir.join("nfs.ckpt")),
            resume: self.resume,
            checkpoint_every_secs: self
                .checkpoint_every
                .unwrap_or(60)
                .min(self.sync_every.unwrap_or(u64::MAX)),
            ..NfsParams::default()
        }
    }
}

struct FactoringRun {
    dir: Option<PathBuf>,
    s3_uri: Option<String>,
    checkpoint_name: &'static str,
    method: &'static str,
    _lock: Option<File>,
    verbose: bool,
    resume: bool,
    did_progress: Cell<bool>,
    sync_every: u64,
    last_sync: Cell<Instant>,
    local_error: RefCell<Option<String>>,
}

struct RunOptions {
    state_dir: Option<PathBuf>,
    resume: bool,
    s3_uri: Option<String>,
    sync_every: Option<u64>,
    checkpoint_every: Option<u64>,
    verbose: bool,
    progress_every: Option<u64>,
    checkpoint_name: &'static str,
}

impl From<&NfsArgs> for RunOptions {
    fn from(args: &NfsArgs) -> Self {
        Self {
            state_dir: args.state_dir.clone(),
            resume: args.resume,
            s3_uri: args.s3_uri.clone(),
            sync_every: args.sync_every,
            checkpoint_every: args.checkpoint_every,
            verbose: args.verbose,
            progress_every: args.progress_every,
            checkpoint_name: "nfs.ckpt",
        }
    }
}

struct StageHeartbeat {
    stage: Arc<Mutex<(&'static str, u64, u64)>>,
    stop: mpsc::Sender<()>,
    worker: Option<JoinHandle<()>>,
}

impl StageHeartbeat {
    fn start(method: &'static str, every_seconds: u64) -> Self {
        let initial = if method == "ecm" {
            "curve"
        } else if method == "factor" {
            "startup"
        } else {
            "polyselect"
        };
        let stage = Arc::new(Mutex::new((initial, 0, 0)));
        let shared = Arc::clone(&stage);
        let (stop, receiver) = mpsc::channel();
        let worker = std::thread::spawn(move || {
            let started = Instant::now();
            while receiver
                .recv_timeout(Duration::from_secs(every_seconds))
                .is_err_and(|e| e == mpsc::RecvTimeoutError::Timeout)
            {
                let (name, done, target) = *shared.lock().expect("stage heartbeat lock");
                if target == 0 {
                    eprintln!(
                        "[{method}] {:.1}s {name} work={done}",
                        started.elapsed().as_secs_f64()
                    );
                } else {
                    eprintln!(
                        "[{method}] {:.1}s {name} {done}/{target}",
                        started.elapsed().as_secs_f64()
                    );
                }
            }
        });
        Self {
            stage,
            stop,
            worker: Some(worker),
        }
    }

    fn update(&self, p: &Progress) {
        *self.stage.lock().expect("stage heartbeat lock") = (p.stage, p.done, p.target);
    }
}

impl Drop for StageHeartbeat {
    fn drop(&mut self) {
        let _ = self.stop.send(());
        if let Some(worker) = self.worker.take() {
            let _ = worker.join();
        }
    }
}

fn state_dir_has_payload(dir: &Path) -> Result<bool, String> {
    for entry in fs::read_dir(dir).map_err(|e| format!("reading {}: {e}", dir.display()))? {
        let entry = entry.map_err(|e| format!("reading {}: {e}", dir.display()))?;
        if entry.file_name() != ".lock" {
            return Ok(true);
        }
    }
    Ok(false)
}

fn write_json_atomic(path: &Path, value: &impl Serialize) -> Result<(), String> {
    let data =
        serde_json::to_vec(value).map_err(|e| format!("serializing {}: {e}", path.display()))?;
    let temporary = path.with_extension("json.tmp");
    if temporary.exists() || temporary.is_symlink() {
        fs::remove_file(&temporary)
            .map_err(|e| format!("removing stale {}: {e}", temporary.display()))?;
    }
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&temporary)
        .map_err(|e| format!("creating {}: {e}", temporary.display()))?;
    file.write_all(&data)
        .and_then(|_| file.sync_all())
        .map_err(|e| format!("syncing {}: {e}", temporary.display()))?;
    fs::rename(&temporary, path).map_err(|e| format!("publishing {}: {e}", path.display()))
}

fn aws(args: &[&str]) -> Result<std::process::Output, String> {
    let output = Command::new("aws")
        .args(args)
        .output()
        .map_err(|e| format!("starting AWS CLI: {e}"))?;
    if !output.status.success() {
        return Err(format!(
            "AWS CLI failed ({}): {}",
            output.status,
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    Ok(output)
}

fn s3_has_objects(uri: &str) -> Result<bool, String> {
    let (bucket, prefix) = uri
        .strip_prefix("s3://")
        .and_then(|s| s.split_once('/'))
        .ok_or("invalid S3 prefix")?;
    let prefix = format!("{prefix}/");
    let listing = aws(&[
        "s3api",
        "list-objects-v2",
        "--bucket",
        bucket,
        "--prefix",
        &prefix,
        "--max-keys",
        "1",
        "--output",
        "json",
    ])?;
    let document: serde_json::Value =
        serde_json::from_slice(&listing.stdout).map_err(|e| format!("invalid S3 listing: {e}"))?;
    Ok(document["KeyCount"].as_u64().unwrap_or(0) > 0)
}

fn s3_has_object(uri: &str, name: &str) -> Result<bool, String> {
    let (bucket, prefix) = uri
        .strip_prefix("s3://")
        .and_then(|value| value.split_once('/'))
        .ok_or("invalid S3 prefix")?;
    let key = format!("{prefix}/{name}");
    let listing = aws(&[
        "s3api",
        "list-objects-v2",
        "--bucket",
        bucket,
        "--prefix",
        &key,
        "--max-keys",
        "10",
        "--output",
        "json",
    ])?;
    let document: serde_json::Value =
        serde_json::from_slice(&listing.stdout).map_err(|e| format!("invalid S3 listing: {e}"))?;
    Ok(document["Contents"].as_array().is_some_and(|contents| {
        contents
            .iter()
            .any(|entry| entry["Key"].as_str() == Some(key.as_str()))
    }))
}

impl FactoringRun {
    fn prepare_nfs(
        args: &NfsArgs,
        method: &'static str,
        n: &BigUint,
        method_params: serde_json::Value,
    ) -> Result<Self, String> {
        let manifest = serde_json::json!({
            "schema_version": 1,
            "method": method,
            "n": n.to_string(),
            "method_params": method_params,
            "rational_bound": args.rational_bound,
            "algebraic_bound": args.algebraic_bound,
            "sieve_half_width": args.sieve_half_width,
        });
        Self::prepare(&RunOptions::from(args), method, manifest)
    }

    fn prepare(
        options: &RunOptions,
        method: &'static str,
        manifest: serde_json::Value,
    ) -> Result<Self, String> {
        if options.state_dir.is_none() {
            if options.resume
                || options.checkpoint_every.is_some()
                || options.s3_uri.is_some()
                || options.sync_every.is_some()
            {
                return Err(
                    "--resume, --checkpoint-every, --s3-uri and --sync-every require --state-dir"
                        .into(),
                );
            }
        }
        if options.sync_every.is_some() && options.s3_uri.is_none() {
            return Err("--sync-every requires --s3-uri".into());
        }
        if let Some(uri) = &options.s3_uri {
            let Some((bucket, prefix)) = uri.strip_prefix("s3://").and_then(|s| s.split_once('/'))
            else {
                return Err("--s3-uri must be s3://BUCKET/PREFIX".into());
            };
            if bucket.is_empty() || prefix.trim_matches('/').is_empty() || uri.ends_with('/') {
                return Err(
                    "--s3-uri must name a nonempty bucket and prefix without a trailing slash"
                        .into(),
                );
            }
        }
        let mut run = Self {
            dir: options.state_dir.clone(),
            s3_uri: options.s3_uri.clone(),
            checkpoint_name: options.checkpoint_name,
            method,
            _lock: None,
            verbose: options.verbose || options.progress_every.is_some(),
            resume: options.resume,
            did_progress: Cell::new(false),
            sync_every: options.sync_every.unwrap_or(60),
            last_sync: Cell::new(Instant::now()),
            local_error: RefCell::new(None),
        };
        let Some(dir) = &run.dir else {
            return Ok(run);
        };
        fs::create_dir_all(dir).map_err(|e| format!("creating {}: {e}", dir.display()))?;
        let lock = OpenOptions::new()
            .create(true)
            .read(true)
            .write(true)
            .open(dir.join(".lock"))
            .map_err(|e| format!("opening {method} state lock: {e}"))?;
        #[cfg(unix)]
        if unsafe { libc::flock(lock.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } != 0 {
            return Err(format!("{} is already in use", dir.display()));
        }
        #[cfg(not(unix))]
        return Err(format!(
            "{method} state directory locking is unavailable on this platform"
        ));
        run._lock = Some(lock);

        let manifest_path = dir.join("manifest.json");
        if options.resume {
            if !manifest_path.exists() {
                if state_dir_has_payload(dir)? {
                    return Err(format!(
                        "{method} state directory has no manifest but is not empty"
                    ));
                }
                let uri = run
                    .s3_uri
                    .as_ref()
                    .ok_or_else(|| format!("no local {method} manifest to resume"))?;
                if run.verbose {
                    eprintln!("[{method}] restoring S3 state");
                }
                let remote = format!("{uri}/");
                let local = dir.to_string_lossy();
                aws(&[
                    "s3",
                    "sync",
                    &remote,
                    &local,
                    "--exclude",
                    ".lock",
                    "--only-show-errors",
                ])?;
            } else if let Some(uri) = &run.s3_uri {
                if s3_has_objects(uri)? {
                    let remote_manifest = format!("{uri}/manifest.json");
                    let remote = aws(&["s3", "cp", &remote_manifest, "-", "--only-show-errors"])?;
                    let found: serde_json::Value = serde_json::from_slice(&remote.stdout)
                        .map_err(|e| format!("invalid S3 {method} manifest: {e}"))?;
                    if found != manifest {
                        return Err(format!("S3 {method} manifest differs from the local run"));
                    }
                }
            }
            let found: serde_json::Value = serde_json::from_slice(
                &fs::read(&manifest_path).map_err(|e| format!("reading {method} manifest: {e}"))?,
            )
            .map_err(|e| format!("invalid {method} manifest: {e}"))?;
            if found != manifest {
                return Err(format!("{method} manifest differs from the requested run"));
            }
            if !dir.join(options.checkpoint_name).is_file() {
                let completed: serde_json::Value =
                    serde_json::from_slice(&fs::read(dir.join("result.json")).map_err(|_| {
                        format!(
                            "{method} resume needs {} or a verified result",
                            options.checkpoint_name
                        )
                    })?)
                    .map_err(|e| format!("invalid NFS result: {e}"))?;
                if completed["verified"] != true {
                    return Err(format!(
                        "{method} resume needs {} or a verified result",
                        options.checkpoint_name
                    ));
                }
            }
        } else {
            if state_dir_has_payload(dir)? {
                return Err(format!("{} is not empty; use --resume", dir.display()));
            }
            if let Some(uri) = &run.s3_uri {
                if s3_has_objects(uri)? {
                    return Err("S3 prefix is not empty; use a unique prefix or --resume".into());
                }
            }
            write_json_atomic(&manifest_path, &manifest)?;
        }
        Ok(run)
    }

    fn sync(&self, label: &str) -> Result<(), String> {
        let (Some(dir), Some(uri)) = (&self.dir, &self.s3_uri) else {
            return Ok(());
        };
        if self.verbose {
            eprintln!("[{}] {label} S3 sync started", self.method);
        }
        let started = Instant::now();
        // Force each object upload: `aws s3 sync` may skip a rewritten
        // checkpoint with the same size and timestamp. The result goes last.
        let push = |name: &str| -> Result<(), String> {
            let path = dir.join(name);
            if path.is_file() {
                let local = path.to_string_lossy();
                let remote = format!("{uri}/{name}");
                aws(&["s3", "cp", &local, &remote, "--only-show-errors"])?;
            }
            Ok(())
        };
        push("manifest.json")?;
        if self.method == "factor" {
            let mut inner = fs::read_dir(dir)
                .map_err(|e| format!("reading factor state for S3 sync: {e}"))?
                .map(|entry| entry.map_err(|e| e.to_string()))
                .collect::<Result<Vec<_>, _>>()?;
            inner.sort_by_key(|entry| entry.file_name());
            for entry in inner {
                let name = entry.file_name();
                let name = name.to_string_lossy();
                if name.starts_with("factor-") && name.ends_with(".ckpt") {
                    push(&name)?;
                }
            }
        }
        for name in [self.checkpoint_name, "progress.json"] {
            push(name)?;
        }
        if label == "final" {
            push("result.json")?;
        }
        self.last_sync.set(Instant::now());
        if self.verbose {
            eprintln!(
                "[{}] {label} S3 sync complete in {:.1}s",
                self.method,
                started.elapsed().as_secs_f64()
            );
        }
        Ok(())
    }

    fn progress(&self, method: &str, p: &Progress) {
        self.did_progress.set(true);
        let Some(dir) = &self.dir else {
            return;
        };
        let progress = serde_json::json!({
            "method": method, "stage": p.stage, "done": p.done,
            "target": p.target, "seconds": p.seconds,
        });
        if let Err(error) = write_json_atomic(&dir.join("progress.json"), &progress) {
            *self.local_error.borrow_mut() = Some(error);
        }
        if self.s3_uri.is_some() && self.last_sync.get().elapsed().as_secs() >= self.sync_every {
            if let Err(error) = self.sync("periodic") {
                eprintln!("[{}] {error}", self.method);
            }
            self.last_sync.set(Instant::now());
        }
    }

    fn finish(&self, report: &impl Serialize, verified: bool) -> Result<(), String> {
        // A failed checkpoint validation emits no progress. Keep the previous
        // local and remote result intact so an operator can repair the state.
        if self.resume && !self.did_progress.get() && !verified {
            return Ok(());
        }
        if let Some(error) = self.local_error.borrow_mut().take() {
            return Err(error);
        }
        if let Some(dir) = &self.dir {
            write_json_atomic(&dir.join("result.json"), report)?;
        }
        self.sync("final")?;
        Ok(())
    }
}

fn nfs_text(r: &NfsReport) -> String {
    let mut s = format!(
        "{}: {}\n",
        r.method,
        split_line(&r.n, &r.factor, &r.cofactor, r.verified)
    );
    s += &format!(
        "  polynomial  {} (degree {}, m = {}, skewness {:.2}, alpha {:.2})\n",
        r.polynomial, r.degree, r.m, r.skewness, r.alpha
    );
    s += &format!(
        "  factor base rational {} primes (B = {}), algebraic {} ideals (B = {}), {} quadratic characters\n",
        r.rational_fb_size, r.rational_bound, r.algebraic_fb_size, r.algebraic_bound, r.quadratic_characters
    );
    s += &format!(
        "  sieve       {} lines, {} relations ({} full, {} from partials)\n",
        r.lines_sieved,
        r.full_relations + r.partial_relations,
        r.full_relations,
        r.partial_relations
    );
    s += &format!(
        "  matrix      {} x {} -> {} x {} after filtering, {} dependencies; {} square roots tried\n",
        r.linalg.rows_in,
        r.linalg.cols_in,
        r.linalg.rows_filtered,
        r.linalg.cols_filtered,
        r.linalg.dependencies,
        r.dependencies_tried
    );
    s += &format!(
        "  time        polyselect {:.2} s, sieve {:.2} s, linear algebra {:.2} s, sqrt {:.2} s, total {:.2} s\n",
        r.polyselect_seconds, r.sieve_seconds, r.linalg_seconds, r.sqrt_seconds, r.total_seconds
    );
    if let Some(f) = &r.failure {
        s += &format!("  failure     {f}\n");
    }
    s
}

#[derive(Args, Clone, Debug)]
pub struct GnfsArgs {
    /// The integer to split (an expression is accepted).
    pub n: String,
    /// Polynomial degree (default: 3 below 66 digits, then 4, 5).
    #[arg(long)]
    pub degree: Option<usize>,
    #[command(flatten)]
    pub nfs: NfsArgs,
}

pub fn run_gnfs(out: Out, a: &GnfsArgs) -> CmdResult {
    let n = parse_expr(&a.n)?;
    size_guard(&n, "gnfs", 65, a.nfs.force)?;
    let state =
        FactoringRun::prepare_nfs(&a.nfs, "gnfs", &n, serde_json::json!({"degree": a.degree}))?;
    let params = GnfsParams {
        degree: a.degree,
        nfs: a.nfs.params(),
        ..GnfsParams::default()
    };
    let verbose = a.nfs.verbose || a.nfs.progress_every.is_some();
    let pr = progress_printer(verbose);
    if verbose {
        eprintln!("[gnfs] polynomial selection started");
    }
    let r = {
        let heartbeat =
            verbose.then(|| StageHeartbeat::start("gnfs", a.nfs.progress_every.unwrap_or(5)));
        let progress = |p: &Progress| {
            if let Some(print) = &pr {
                print(p);
            }
            if let Some(heartbeat) = &heartbeat {
                heartbeat.update(p);
            }
            state.progress("gnfs", p);
        };
        let callback = (verbose || state.dir.is_some()).then_some(&progress as &dyn Fn(&Progress));
        factoring::gnfs(&n, &params, callback)
    };
    state.finish(&r, r.verified)?;
    out.emit(&r, || nfs_text(&r))?;
    verdict(r.verified, r.factor.is_some(), "gnfs")
}

#[derive(Args, Clone, Debug)]
pub struct SnfsArgs {
    /// The integer to split: n divides the special form.
    pub n: String,
    /// The special form (c*)r^e+s or (c*)r^e-s (default: n itself, if it
    /// is written in that form).
    #[arg(long, conflicts_with = "poly")]
    pub form: Option<String>,
    /// An explicit polynomial, coefficients from the constant term up:
    /// "c0,c1,...,cd"; needs --m.
    #[arg(long, requires = "m", allow_hyphen_values = true)]
    pub poly: Option<String>,
    /// The common root: f(m) = 0 (mod n).
    #[arg(long)]
    pub m: Option<String>,
    /// Polynomial degree for --form (default: chosen from the size).
    #[arg(long)]
    pub degree: Option<usize>,
    #[command(flatten)]
    pub nfs: NfsArgs,
}

pub fn run_snfs(out: Out, a: &SnfsArgs) -> CmdResult {
    let n = parse_expr(&a.n)?;
    let input = match (&a.form, &a.poly) {
        (Some(f), _) => parse_form(f)?,
        (None, Some(p)) => SnfsInput::Poly {
            coeffs: p
                .split(',')
                .map(|c| {
                    BigInt::parse_bytes(c.trim().as_bytes(), 10)
                        .ok_or_else(|| format!("bad coefficient {c:?}"))
                })
                .collect::<Result<_, _>>()?,
            m: parse_expr(a.m.as_deref().unwrap_or_default())?,
        },
        (None, None) => parse_form(&a.n).map_err(|_| {
            "give --form [c*]r^e+s (or --poly with --m), or write n itself as r^e+s".to_string()
        })?,
    };
    size_guard(&n, "snfs", 90, a.nfs.force)?;
    let method_params = serde_json::json!({"degree":a.degree,"input":input});
    let state = FactoringRun::prepare_nfs(&a.nfs, "snfs", &n, method_params)?;
    let params = SnfsParams {
        degree: a.degree,
        nfs: a.nfs.params(),
    };
    let verbose = a.nfs.verbose || a.nfs.progress_every.is_some();
    let pr = progress_printer(verbose);
    if verbose {
        eprintln!("[snfs] polynomial selection started");
    }
    let r = {
        let heartbeat =
            verbose.then(|| StageHeartbeat::start("snfs", a.nfs.progress_every.unwrap_or(5)));
        let progress = |p: &Progress| {
            if let Some(print) = &pr {
                print(p);
            }
            if let Some(heartbeat) = &heartbeat {
                heartbeat.update(p);
            }
            state.progress("snfs", p);
        };
        let callback = (verbose || state.dir.is_some()).then_some(&progress as &dyn Fn(&Progress));
        factoring::snfs(&n, &input, &params, callback)
    };
    state.finish(&r, r.verified)?;
    out.emit(&r, || nfs_text(&r))?;
    verdict(r.verified, r.factor.is_some(), "snfs")
}

// ---- quadratic sieve --------------------------------------------------------

#[derive(Args, Clone, Debug)]
pub struct QsArgs {
    /// The integer to split (an expression is accepted).
    pub n: String,
    /// Factor-base size (default: from the size of n).
    #[arg(long)]
    pub factor_base_size: Option<usize>,
    /// Knuth-Schroeppel multiplier (default: chosen automatically).
    #[arg(long)]
    pub multiplier: Option<u64>,
    /// Sieve interval half-width.
    #[arg(long)]
    pub sieve_half_width: Option<u32>,
    #[arg(long, default_value_t = 1)]
    pub threads: usize,
    #[arg(long, default_value_t = 1)]
    pub seed: u64,
    /// Stage progress on stderr.
    #[arg(long)]
    pub verbose: bool,
    /// Seconds between heartbeats during a stage with no new work reports.
    #[arg(long, value_parser = clap::value_parser!(u64).range(1..))]
    pub progress_every: Option<u64>,
    /// Stop after this many polynomial a-values; raise on resume to continue.
    #[arg(long)]
    pub max_a_values: Option<u64>,
    /// Dedicated directory for SIQS relation checkpoints and reports.
    #[arg(long)]
    pub state_dir: Option<PathBuf>,
    /// Continue from the checkpoint in --state-dir (or restore from S3).
    #[arg(long)]
    pub resume: bool,
    /// Seconds between local checkpoint writes (0 saves every batch).
    #[arg(long)]
    pub checkpoint_every: Option<u64>,
    /// Mirror the run directory to this S3 prefix with the AWS CLI.
    #[arg(long)]
    pub s3_uri: Option<String>,
    /// Seconds between S3 uploads; the final upload is always attempted.
    #[arg(long)]
    pub sync_every: Option<u64>,
    /// Run even above the size this implementation is practical for.
    #[arg(long)]
    pub force: bool,
}

impl From<&QsArgs> for RunOptions {
    fn from(args: &QsArgs) -> Self {
        Self {
            state_dir: args.state_dir.clone(),
            resume: args.resume,
            s3_uri: args.s3_uri.clone(),
            sync_every: args.sync_every,
            checkpoint_every: args.checkpoint_every,
            verbose: args.verbose,
            progress_every: args.progress_every,
            checkpoint_name: "qs.ckpt",
        }
    }
}

fn qs_text(r: &QsReport) -> String {
    let mut s = format!(
        "siqs: {}\n",
        split_line(&r.n, &r.factor, &r.cofactor, r.verified)
    );
    s += &format!(
        "  factor base {} primes up to {} (multiplier {}), {} polynomials from {} a-values\n",
        r.factor_base_size, r.largest_prime, r.multiplier, r.polynomials, r.a_values
    );
    s += &format!(
        "  relations   {} full, {} from partials; matrix {} x {}, {} dependencies\n",
        r.full_relations,
        r.partial_relations,
        r.linalg.rows_filtered,
        r.linalg.cols_filtered,
        r.linalg.dependencies
    );
    s += &format!(
        "  time        sieve {:.2} s, linear algebra {:.2} s, sqrt {:.2} s, total {:.2} s\n",
        r.sieve_seconds, r.linalg_seconds, r.sqrt_seconds, r.total_seconds
    );
    if let Some(f) = &r.failure {
        s += &format!("  failure     {f}\n");
    }
    s
}

pub fn run_qs(out: Out, a: &QsArgs) -> CmdResult {
    let n = parse_expr(&a.n)?;
    size_guard(&n, "qs", 75, a.force)?;
    let manifest = serde_json::json!({
        "schema_version": 1,
        "method": "qs",
        "n": n.to_string(),
        "factor_base_size": a.factor_base_size,
        "multiplier": a.multiplier,
        "sieve_half_width": a.sieve_half_width,
        "seed": a.seed,
    });
    let state = FactoringRun::prepare(&RunOptions::from(a), "qs", manifest)?;
    let params = QsParams {
        factor_base_size: a.factor_base_size,
        multiplier: a.multiplier,
        sieve_half_width: a.sieve_half_width,
        threads: a.threads.max(1),
        seed: a.seed,
        max_a_values: a.max_a_values.unwrap_or(0),
        checkpoint_path: a.state_dir.as_ref().map(|dir| dir.join("qs.ckpt")),
        resume: a.resume,
        checkpoint_every_secs: a
            .checkpoint_every
            .unwrap_or(60)
            .min(a.sync_every.unwrap_or(u64::MAX)),
        ..QsParams::default()
    };
    let verbose = a.verbose || a.progress_every.is_some();
    let pr = progress_printer(verbose);
    if verbose {
        eprintln!("[qs] factor-base setup started");
    }
    let r = {
        let heartbeat = verbose.then(|| StageHeartbeat::start("qs", a.progress_every.unwrap_or(5)));
        let progress = |p: &Progress| {
            if let Some(print) = &pr {
                print(p);
            }
            if let Some(heartbeat) = &heartbeat {
                heartbeat.update(p);
            }
            state.progress("qs", p);
        };
        let callback = (verbose || state.dir.is_some()).then_some(&progress as &dyn Fn(&Progress));
        factoring::qs(&n, &params, callback)
    };
    state.finish(&r, r.verified)?;
    out.emit(&r, || qs_text(&r))?;
    verdict(r.verified, r.factor.is_some(), "qs")
}

// ---- ECM, p-1, p+1, rho ----------------------------------------------------

#[derive(Args, Clone, Debug)]
pub struct EcmArgs {
    pub n: String,
    /// Stage-1 bound.
    #[arg(long, default_value_t = 11_000)]
    pub b1: u64,
    /// Curves to try.
    #[arg(long, default_value_t = 64)]
    pub curves: u64,
    #[arg(long, default_value_t = 1)]
    pub seed: u64,
    /// Print each completed curve and a heartbeat while one curve runs.
    #[arg(long)]
    pub verbose: bool,
    /// Seconds between heartbeats (implies --verbose).
    #[arg(long, value_parser = clap::value_parser!(u64).range(1..))]
    pub progress_every: Option<u64>,
    /// Dedicated directory for completed-curve checkpoints and reports.
    #[arg(long)]
    pub state_dir: Option<PathBuf>,
    /// Continue completed curves locally or restore their state from S3.
    #[arg(long)]
    pub resume: bool,
    /// Mirror checkpoints and final artifacts to this S3 prefix.
    #[arg(long)]
    pub s3_uri: Option<String>,
    /// Seconds between S3 copies; the final copy is always attempted.
    #[arg(long, value_parser = clap::value_parser!(u64).range(1..))]
    pub sync_every: Option<u64>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct EcmCheckpoint {
    schema_version: u32,
    fingerprint: String,
    next_curve: u64,
    factor: Option<String>,
    compute_seconds: f64,
}

#[derive(Serialize, Deserialize)]
struct EcmCheckpointFile {
    checksum: String,
    payload: String,
}

fn save_ecm_checkpoint(path: &Path, state: &EcmCheckpoint) -> Result<(), String> {
    let payload =
        serde_json::to_string(state).map_err(|e| format!("serializing ECM state: {e}"))?;
    write_json_atomic(
        path,
        &EcmCheckpointFile {
            checksum: blake3::hash(payload.as_bytes()).to_hex().to_string(),
            payload,
        },
    )
}

fn load_ecm_checkpoint(
    path: &Path,
    fingerprint: &str,
    n: &BigUint,
) -> Result<EcmCheckpoint, String> {
    let saved: EcmCheckpointFile = serde_json::from_slice(
        &fs::read(path).map_err(|e| format!("reading ECM checkpoint: {e}"))?,
    )
    .map_err(|e| format!("invalid ECM checkpoint: {e}"))?;
    if saved.checksum != blake3::hash(saved.payload.as_bytes()).to_hex().as_str() {
        return Err("ECM checkpoint checksum mismatch".into());
    }
    let state: EcmCheckpoint = serde_json::from_str(&saved.payload)
        .map_err(|e| format!("invalid ECM checkpoint payload: {e}"))?;
    if state.schema_version != 1 || state.fingerprint != fingerprint {
        return Err("ECM checkpoint parameters or version differ".into());
    }
    if !state.compute_seconds.is_finite() || state.compute_seconds < 0.0 {
        return Err("invalid ECM checkpoint compute time".into());
    }
    if let Some(factor) = &state.factor {
        let f = factor
            .parse::<BigUint>()
            .map_err(|e| format!("invalid ECM factor: {e}"))?;
        if f.is_one() || &f == n || (n % &f) != BigUint::zero() {
            return Err("ECM checkpoint factor does not divide n".into());
        }
    }
    Ok(state)
}

#[derive(Serialize)]
struct SplitReport {
    method: &'static str,
    n: String,
    factor: Option<String>,
    cofactor: Option<String>,
    verified: bool,
    seconds: f64,
    detail: String,
}

impl SplitReport {
    fn text(&self) -> String {
        let (n, f, c) = (
            self.n.parse::<BigUint>().unwrap_or_default(),
            self.factor.as_ref().and_then(|s| s.parse().ok()),
            self.cofactor.as_ref().and_then(|s| s.parse().ok()),
        );
        format!(
            "{}: {}\n  {} ({:.3} s)\n",
            self.method,
            split_line(&n, &f, &c, self.verified),
            self.detail,
            self.seconds
        )
    }
}

fn split(
    method: &'static str,
    n: &BigUint,
    f: Option<BigUint>,
    seconds: f64,
    detail: String,
) -> SplitReport {
    let f = f.filter(|f| !f.is_one() && f != n && (n % f).is_zero());
    let c = f.as_ref().map(|f| n / f);
    SplitReport {
        method,
        n: n.to_string(),
        verified: matches!((&f, &c), (Some(f), Some(c)) if &(f * c) == n),
        factor: f.map(|f| f.to_string()),
        cofactor: c.map(|c| c.to_string()),
        seconds,
        detail,
    }
}

pub fn run_ecm(out: Out, a: &EcmArgs) -> CmdResult {
    let n = parse_expr(&a.n)?;
    if n < BigUint::from(2u32) || a.curves == 0 {
        return Err("ECM requires n >= 2 and at least one curve".into());
    }
    let manifest = serde_json::json!({
        "schema_version": 1, "method": "ecm", "n": n.to_string(),
        "b1": a.b1, "seed": a.seed,
    });
    let fingerprint = blake3::hash(&serde_json::to_vec(&manifest).map_err(|e| e.to_string())?)
        .to_hex()
        .to_string();
    let options = RunOptions {
        state_dir: a.state_dir.clone(),
        resume: a.resume,
        s3_uri: a.s3_uri.clone(),
        sync_every: a.sync_every,
        checkpoint_every: None,
        verbose: a.verbose,
        progress_every: a.progress_every,
        checkpoint_name: "ecm.ckpt",
    };
    let state = FactoringRun::prepare(&options, "ecm", manifest)?;
    let checkpoint_path = a.state_dir.as_ref().map(|dir| dir.join("ecm.ckpt"));
    let mut checkpoint = if a.resume {
        load_ecm_checkpoint(
            checkpoint_path
                .as_deref()
                .ok_or("ECM resume needs --state-dir")?,
            &fingerprint,
            &n,
        )?
    } else {
        EcmCheckpoint {
            schema_version: 1,
            fingerprint,
            next_curve: 0,
            factor: None,
            compute_seconds: 0.0,
        }
    };
    if checkpoint.next_curve > a.curves {
        return Err("ECM checkpoint contains more curves than the requested budget".into());
    }
    if !a.resume {
        if let Some(path) = &checkpoint_path {
            save_ecm_checkpoint(path, &checkpoint)?;
            state.sync("initial")?;
        }
    }
    let verbose = a.verbose || a.progress_every.is_some();
    let printer = progress_printer(verbose);
    let heartbeat = verbose.then(|| StageHeartbeat::start("ecm", a.progress_every.unwrap_or(5)));
    let progress = |done: u64, seconds: f64| {
        let update = Progress {
            stage: "curve",
            done,
            target: a.curves,
            seconds,
        };
        if let Some(print) = &printer {
            print(&update);
        }
        if let Some(heartbeat) = &heartbeat {
            heartbeat.update(&update);
        }
        state.progress("ecm", &update);
    };
    progress(checkpoint.next_curve, checkpoint.compute_seconds);
    while checkpoint.next_curve < a.curves && checkpoint.factor.is_none() {
        let curve = checkpoint.next_curve;
        let started = Instant::now();
        let outcome =
            crate::cryptanalysis::ecm::ecm_one_curve(&n, a.b1, a.seed.wrapping_add(curve));
        checkpoint.compute_seconds += started.elapsed().as_secs_f64();
        checkpoint.next_curve += 1;
        if let crate::cryptanalysis::ecm::EcmResult::Found(factor) = outcome {
            if factor.is_one() || factor == n || (&n % &factor) != BigUint::zero() {
                return Err("ECM engine returned an invalid factor".into());
            }
            checkpoint.factor = Some(factor.to_string());
        }
        if let Some(path) = &checkpoint_path {
            save_ecm_checkpoint(path, &checkpoint)?;
        }
        progress(checkpoint.next_curve, checkpoint.compute_seconds);
    }
    drop(heartbeat);
    let f = checkpoint
        .factor
        .as_deref()
        .map(str::parse::<BigUint>)
        .transpose()
        .map_err(|e| format!("invalid saved ECM factor: {e}"))?;
    let r = split(
        "ecm",
        &n,
        f,
        checkpoint.compute_seconds,
        format!(
            "B1 = {}, completed {} of {} curves; seconds count curve work only",
            a.b1, checkpoint.next_curve, a.curves
        ),
    );
    state.finish(&r, r.verified)?;
    out.emit(&r, || r.text())?;
    verdict(r.verified, r.factor.is_some(), "ecm")
}

#[derive(Args, Clone, Debug)]
pub struct Pm1Args {
    pub n: String,
    /// Stage-1 bound.
    #[arg(long, default_value_t = 100_000)]
    pub b1: u64,
    /// Stage-2 bound.
    #[arg(long, default_value_t = 10_000_000)]
    pub b2: u64,
    /// Williams p+1 instead of Pollard p-1 (finds p when p+1 is smooth).
    #[arg(long)]
    pub pp1: bool,
}

pub fn run_pm1(out: Out, a: &Pm1Args) -> CmdResult {
    let n = parse_expr(&a.n)?;
    let r = if a.pp1 {
        factoring::pp1(
            &n,
            &Pp1Params {
                b1: a.b1,
                ..Pp1Params::default()
            },
        )
    } else {
        factoring::pm1(
            &n,
            &Pm1Params {
                b1: a.b1,
                b2: a.b2,
                ..Pm1Params::default()
            },
        )
    };
    let s = split(
        r.method,
        &n,
        r.factor.clone(),
        r.seconds,
        format!("B1 = {}, B2 = {}, found in stage {}", a.b1, a.b2, r.stage),
    );
    out.emit(&r, || s.text())?;
    verdict(r.verified, r.factor.is_some(), r.method)
}

#[derive(Args, Clone, Debug)]
pub struct RhoFactorArgs {
    pub n: String,
    /// Iterations per attempt.
    #[arg(long, default_value_t = 1 << 26)]
    pub iterations: u64,
}

pub fn run_rho_factor(out: Out, a: &RhoFactorArgs) -> CmdResult {
    let n = parse_expr(&a.n)?;
    let r = factoring::rho(
        &n,
        &RhoParams {
            max_iterations: a.iterations,
            ..RhoParams::default()
        },
    );
    let s = split(
        "pollard-brent-rho",
        &n,
        r.factor.clone(),
        r.seconds,
        format!("{} iterations", r.iterations),
    );
    out.emit(&r, || s.text())?;
    verdict(r.verified, r.factor.is_some(), "rho-factor")
}

// ---- RSA -------------------------------------------------------------------

#[derive(Subcommand, Clone, Debug)]
pub enum RsaCmd {
    /// Fermat's method: p and q close together.
    Fermat {
        n: String,
        #[arg(long, default_value_t = 1 << 24)]
        iterations: u64,
    },
    /// Wiener's continued-fraction attack: small private exponent d.
    Wiener {
        n: String,
        #[arg(long)]
        e: String,
    },
    /// Factor n from a known private exponent d.
    FromD {
        n: String,
        #[arg(long)]
        e: String,
        #[arg(long)]
        d: String,
    },
    /// Håstad's broadcast attack: one message, e moduli, public exponent e.
    Hastad {
        /// Public exponent.
        #[arg(long)]
        e: u32,
        /// Ciphertext:modulus pairs c:n (e of them).
        #[arg(required = true)]
        pairs: Vec<String>,
    },
    /// Common-modulus attack: one message under two exponents of one n.
    CommonModulus {
        #[arg(long)]
        n: String,
        #[arg(long)]
        e1: String,
        #[arg(long)]
        c1: String,
        #[arg(long)]
        e2: String,
        #[arg(long)]
        c2: String,
    },
    /// Small public exponent: m^e barely (or not) wrapped mod n.
    SmallE {
        #[arg(long)]
        n: String,
        #[arg(long)]
        e: u32,
        #[arg(long)]
        c: String,
        /// Try c + k n for k below this.
        #[arg(long, default_value_t = 1 << 16)]
        max_k: u64,
    },
    /// Shared primes across many moduli (product and remainder trees).
    BatchGcd {
        /// Moduli, or @file with one per line.
        #[arg(required = true)]
        moduli: Vec<String>,
    },
}

fn big(s: &str) -> Result<BigUint, String> {
    parse_expr(s)
}

pub fn run_rsa(out: Out, cmd: &RsaCmd) -> CmdResult {
    match cmd {
        RsaCmd::Fermat { n, iterations } => {
            let r = rsa_attacks::fermat(&big(n)?, *iterations);
            factor_attack(out, &r)
        }
        RsaCmd::Wiener { n, e } => factor_attack(out, &rsa_attacks::wiener(&big(n)?, &big(e)?)),
        RsaCmd::FromD { n, e, d } => factor_attack(
            out,
            &rsa_attacks::factor_from_private_exponent(&big(n)?, &big(e)?, &big(d)?, 1),
        ),
        RsaCmd::Hastad { e, pairs } => {
            let pairs = pairs
                .iter()
                .map(|p| {
                    let (c, n) = p
                        .split_once(':')
                        .ok_or_else(|| format!("expected c:n, got {p:?}"))?;
                    Ok((big(c)?, big(n)?))
                })
                .collect::<Result<Vec<_>, String>>()?;
            message_attack(out, &rsa_attacks::hastad_broadcast(*e, &pairs))
        }
        RsaCmd::CommonModulus { n, e1, c1, e2, c2 } => message_attack(
            out,
            &rsa_attacks::common_modulus(&big(n)?, &big(e1)?, &big(c1)?, &big(e2)?, &big(c2)?),
        ),
        RsaCmd::SmallE { n, e, c, max_k } => message_attack(
            out,
            &rsa_attacks::small_e_root(&big(c)?, *e, &big(n)?, *max_k),
        ),
        RsaCmd::BatchGcd { moduli } => {
            let mut ns = Vec::new();
            for m in moduli {
                if let Some(path) = m.strip_prefix('@') {
                    let text = std::fs::read_to_string(path)
                        .map_err(|e| format!("reading {path}: {e}"))?;
                    for line in text.lines().map(str::trim).filter(|l| !l.is_empty()) {
                        ns.push(big(line)?);
                    }
                } else {
                    ns.push(big(m)?);
                }
            }
            let r = rsa_attacks::batch_gcd(&ns);
            out.emit(&r, || {
                let mut s = format!(
                    "batch-gcd: {} of {} moduli share a prime ({:.3} s)\n",
                    r.factored.len(),
                    r.moduli,
                    r.seconds
                );
                for f in &r.factored {
                    s += &format!("  #{}: p = {}, q = {}\n", f.index, f.p, f.q);
                }
                if !r.duplicates.is_empty() {
                    s += &format!(
                        "  duplicate moduli (no gcd information): {:?}\n",
                        r.duplicates
                    );
                }
                s
            })
        }
    }
}

fn factor_attack(out: Out, r: &rsa_attacks::FactorAttackResult) -> CmdResult {
    out.emit(r, || {
        let mut s = format!(
            "{}: {} ({} iterations, {:.3} s)\n",
            r.attack,
            match (&r.p, &r.q) {
                (Some(p), Some(q)) => format!(
                    "n = {p} * {q} ({})",
                    if r.verified {
                        "verified"
                    } else {
                        "NOT VERIFIED"
                    }
                ),
                _ => "not factored".to_string(),
            },
            r.iterations,
            r.seconds
        );
        if let Some(d) = &r.d {
            s += &format!("  d = {d}\n");
        }
        s
    })?;
    verdict(r.verified, r.p.is_some(), r.attack)
}

fn message_attack(out: Out, r: &rsa_attacks::MessageAttackResult) -> CmdResult {
    out.emit(r, || {
        let mut s = format!(
            "{}: {} ({:.3} s)\n{}",
            r.attack,
            match &r.message {
                Some(m) => format!(
                    "m = {m} ({})",
                    if r.verified {
                        "verified: re-encrypts to the ciphertext"
                    } else {
                        "NOT VERIFIED"
                    }
                ),
                None => "message not recovered".to_string(),
            },
            r.seconds,
            if r.detail.is_empty() {
                String::new()
            } else {
                format!("  {}\n", r.detail)
            }
        );
        if let Some(m) = &r.message {
            let bytes = m.to_bytes_be();
            if bytes.iter().all(|b| b.is_ascii_graphic() || *b == b' ') {
                s += &format!("  as text: {}\n", String::from_utf8_lossy(&bytes));
            }
        }
        if let Some(f) = &r.factor_found {
            s += &format!("  a modulus factor turned up along the way: {f}\n");
        }
        s
    })?;
    verdict(r.verified, r.message.is_some(), r.attack)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn factor_checkpoint_rejects_tampered_and_missing_pieces() {
        let unique = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path =
            std::env::temp_dir().join(format!("crax-factor-{}-{unique}.ckpt", std::process::id()));
        let n = BigUint::from(101u32);
        let saved = std::cell::RefCell::new(None);
        let save = |state: &factoring::auto::FactorState| -> Result<(), String> {
            *saved.borrow_mut() = Some(state.clone());
            Ok(())
        };
        factoring::auto::factor_with_state(
            &n,
            &FactorOptions::default(),
            None,
            None,
            None,
            Some(&save),
        )
        .unwrap();
        let state = saved.into_inner().unwrap();
        save_factor_checkpoint(&path, "fingerprint", &state).unwrap();
        load_factor_checkpoint(&path, "fingerprint", &n).unwrap();
        let mut file: FactorCheckpointFile =
            serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
        file.payload.push(' ');
        fs::write(&path, serde_json::to_vec(&file).unwrap()).unwrap();
        assert!(load_factor_checkpoint(&path, "fingerprint", &n)
            .unwrap_err()
            .contains("checksum"));
        let mut invalid = state;
        invalid.report.factors.clear();
        save_factor_checkpoint(&path, "fingerprint", &invalid).unwrap();
        assert!(load_factor_checkpoint(&path, "fingerprint", &n)
            .unwrap_err()
            .contains("multiply"));
        fs::remove_file(path).unwrap();
    }

    #[test]
    fn ecm_resumes_only_unfinished_curves_and_rejects_corruption() {
        let unique = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let dir = std::env::temp_dir().join(format!("crax-ecm-{}-{unique}", std::process::id()));
        let args = EcmArgs {
            n: "101".into(),
            b1: 20,
            curves: 2,
            seed: 7,
            verbose: false,
            progress_every: None,
            state_dir: Some(dir.clone()),
            resume: false,
            s3_uri: None,
            sync_every: None,
        };
        assert!(run_ecm(Out { json: true }, &args).is_err());
        let path = dir.join("ecm.ckpt");
        let manifest = serde_json::json!({
            "schema_version": 1, "method": "ecm", "n": "101", "b1": 20, "seed": 7,
        });
        let fingerprint = blake3::hash(&serde_json::to_vec(&manifest).unwrap())
            .to_hex()
            .to_string();
        let first = load_ecm_checkpoint(&path, &fingerprint, &BigUint::from(101u32)).unwrap();
        assert_eq!(first.next_curve, 2);
        let continued = EcmArgs {
            curves: 4,
            resume: true,
            ..args
        };
        assert!(run_ecm(Out { json: true }, &continued).is_err());
        let second = load_ecm_checkpoint(&path, &fingerprint, &BigUint::from(101u32)).unwrap();
        assert_eq!(second.next_curve, 4);
        assert!(second.compute_seconds >= first.compute_seconds);
        let mut altered: EcmCheckpointFile =
            serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
        let mut payload: serde_json::Value = serde_json::from_str(&altered.payload).unwrap();
        payload["next_curve"] = serde_json::json!(3);
        altered.payload = payload.to_string();
        fs::write(&path, serde_json::to_vec(&altered).unwrap()).unwrap();
        assert!(
            load_ecm_checkpoint(&path, &fingerprint, &BigUint::from(101u32))
                .unwrap_err()
                .contains("checksum mismatch")
        );
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn expressions_and_forms() {
        assert_eq!(parse_expr("2^10-1").unwrap(), BigUint::from(1023u32));
        assert_eq!(parse_expr("(2^5+1)/3").unwrap(), BigUint::from(11u32));
        assert_eq!(parse_expr("3*10^2 + 0x10").unwrap(), BigUint::from(316u32));
        assert_eq!(parse_expr("2^3^2").unwrap(), BigUint::from(512u32));
        assert!(parse_expr("7/2").is_err());
        assert!(parse_expr("1-2").is_err());
        assert!(parse_expr("2^").is_err());
        match parse_form("3*10^80+7").unwrap() {
            SnfsInput::Form { r, e, s, c } => assert_eq!((r, e, s, c), (10, 80, 7, 3)),
            _ => panic!(),
        }
        match parse_form("2^227-1").unwrap() {
            SnfsInput::Form { r, e, s, c } => assert_eq!((r, e, s, c), (2, 227, -1, 1)),
            _ => panic!(),
        }
        assert!(parse_form("12345").is_err());
    }

    #[test]
    fn every_command_factors_a_small_semiprime() {
        let out = Out { json: true };
        // 1000003 * 1000033: small enough for everything to be quick.
        let n = "1000036000099".to_string();
        run_factor(
            out,
            &FactorArgs {
                n: n.clone(),
                snfs_form: None,
                prefer_nfs: false,
                pp1: false,
                qs_max_digits: None,
                threads: 1,
                seed: 1,
                verbose: false,
                progress_every: None,
                state_dir: None,
                resume: false,
                checkpoint_every: None,
                s3_uri: None,
                sync_every: None,
            },
        )
        .unwrap();
        run_rho_factor(
            out,
            &RhoFactorArgs {
                n: n.clone(),
                iterations: 1 << 20,
            },
        )
        .unwrap();
        run_rsa(
            out,
            &RsaCmd::Fermat {
                n,
                iterations: 1 << 16,
            },
        )
        .unwrap();
    }

    #[test]
    fn qs_splits_a_30_digit_semiprime() {
        // 1000000000000037 * 100000000000031 (16 and 15 digits).
        let out = Out { json: true };
        run_qs(
            out,
            &QsArgs {
                n: "1000000000000037*100000000000031".into(),
                factor_base_size: None,
                multiplier: None,
                sieve_half_width: None,
                threads: 1,
                seed: 1,
                verbose: false,
                progress_every: None,
                max_a_values: None,
                state_dir: None,
                resume: false,
                checkpoint_every: None,
                s3_uri: None,
                sync_every: None,
                force: false,
            },
        )
        .unwrap();
    }
}
