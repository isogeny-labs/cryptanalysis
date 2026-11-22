//! **Go benchmark format (`benchfmt`) reader/writer and a `testing.B`-style
//! harness.**
//!
//! The wire format is the one `go test -bench` prints and
//! [`golang.org/x/perf/benchfmt`](https://pkg.go.dev/golang.org/x/perf/benchfmt)
//! reads, so results from this crate can be compared with any Go benchmark
//! (or another Rust crate) using `benchstat`:
//!
//! ```text
//! goos: linux
//! goarch: amd64
//! pkg: crypto_lib
//! BenchmarkSHA256/1KiB-8   3131   383221 ns/op   1024 B/op   0 allocs/op
//! ```
//!
//! A benchmark line is
//!
//! ```text
//! Benchmark<name>-<procs>\t<iterations>\t<value> <unit>[\t<value> <unit> ...]
//! ```
//!
//! The conventional units are `ns/op`, `B/op` and `allocs/op`; arbitrary
//! units such as `MB/s` are preserved.  `BenchResult` is both the parsed
//! form and the writer, and [`parse_line`] / [`parse_benchmarks`] are the
//! reader.
//!
//! # Harness
//!
//! [`Harness`] is the Rust answer to Go's `testing.B`: it auto-scales the
//! iteration count like `go test -bench` does (start at `b.N = 1`, grow
//! until one run lasts at least `-benchtime`, default 1 s), honours
//! `-bench`, `-benchtime` and `-count`, and writes Go-format lines.  It is
//! deliberately dependency-free so it can live in both the `crypto` and
//! `cryptanalysis` crates.
//!
//! ```ignore
//! use your_crate::benchfmt::Harness;
//! use your_crate::hash::sha256::sha256;
//!
//! let mut h = Harness::from_env().unwrap()
//!     .with_package("your_crate");
//! h.bench_bytes("SHA256/1KiB", 1024, || {
//!     std::hint::black_box(sha256(std::hint::black_box(&[0u8; 1024])));
//! }).unwrap();
//! ```
//!
//! Run a bench target with, for example,
//!
//! ```sh
//! cargo bench --bench go_bench -- -benchtime 100ms -count 5 | tee new.txt
//! benchstat old.txt new.txt
//! ```
//!
//! `-benchtime` accepts a duration (`500ms`, `2s`) or a fixed iteration
//! count (`100x`).  `-bench` takes a substring or a glob (`SHA256/*`,
//! `AES?28/*`); `.` and `*` match everything.  Unknown flags are rejected,
//! but the flags cargo/libtest add (`--bench`, `--test`, `--nocapture`,
//! ...) are ignored.
//!
//! # Measurement rules
//!
//! * Each sample is timed end to end; setup belongs outside the closure
//!   or is charged to the operation.  There is no `ResetTimer`.
//! * The median is *not* substituted for the mean: Go and `benchstat`
//!   expect the per-run rate, and `benchstat` does the aggregation.
//! * `black_box` the inputs and outputs so the optimiser cannot delete
//!   the work.
//! * `procs` comes from `GOMAXPROCS` when set, otherwise from
//!   [`std::thread::available_parallelism`].
//! * `allocs/op` is not instrumented (that would need a global allocator
//!   wrapper); add it explicitly with [`BenchResult::metric`] when it is
//!   known.

use std::fmt;
use std::io::{self, Write};
use std::time::{Duration, Instant};

/// Default `-benchtime` (one second), matching `go test`.
pub const DEFAULT_BENCHTIME: Duration = Duration::from_secs(1);

/// Upper bound on auto-scaled iterations, matching Go's practical cap.
pub const DEFAULT_MAX_ITERATIONS: u64 = 1_000_000_000;

// ── Result model ─────────────────────────────────────────────────────────────

/// One `value unit` pair on a benchmark line, e.g. `812.3 ns/op`.
#[derive(Clone, Debug, PartialEq)]
pub struct Value {
    /// The numeric part.
    pub value: f64,
    /// The unit, e.g. `ns/op`, `B/op`, `allocs/op`, `MB/s`.
    pub unit: String,
}

impl Value {
    /// Construct a metric pair.
    pub fn new(value: f64, unit: impl Into<String>) -> Self {
        Self {
            value,
            unit: unit.into(),
        }
    }
}

/// One benchmark sample in the Go benchmark format.
///
/// `name` is the part after `Benchmark`; the writer adds the prefix and
/// the `-<procs>` suffix.  The reader strips both.
#[derive(Clone, Debug, PartialEq)]
pub struct BenchResult {
    /// Benchmark name without the `Benchmark` prefix or `-<procs>` suffix.
    pub name: String,
    /// `GOMAXPROCS` value the sample was taken with.
    pub procs: u32,
    /// Number of iterations (`b.N`).
    pub iterations: u64,
    /// Metrics in output order.  `ns/op` is normally first.
    pub values: Vec<Value>,
}

impl BenchResult {
    /// A result with no metrics yet.
    pub fn new(name: impl Into<String>, procs: u32, iterations: u64) -> Self {
        Self {
            name: name.into(),
            procs,
            iterations,
            values: Vec::new(),
        }
    }

    /// Append a metric and return `self` for chaining.
    pub fn with_metric(mut self, value: f64, unit: impl Into<String>) -> Self {
        self.values.push(Value::new(value, unit));
        self
    }

    /// Append a metric in place.
    pub fn metric(&mut self, value: f64, unit: impl Into<String>) -> &mut Self {
        self.values.push(Value::new(value, unit));
        self
    }

    /// The `ns/op` value, if present.
    pub fn ns_per_op(&self) -> Option<f64> {
        self.value("ns/op")
    }

    /// The `B/op` value, if present.
    pub fn bytes_per_op(&self) -> Option<f64> {
        self.value("B/op")
    }

    /// The `allocs/op` value, if present.
    pub fn allocs_per_op(&self) -> Option<f64> {
        self.value("allocs/op")
    }

    /// The first metric with `unit`, if present.
    pub fn value(&self, unit: &str) -> Option<f64> {
        self.values.iter().find(|v| v.unit == unit).map(|v| v.value)
    }

    /// The `Benchmark<name>-<procs>` field.
    pub fn benchmark_name(&self) -> String {
        let name = self.name.strip_prefix("Benchmark").unwrap_or(&self.name);
        format!("Benchmark{name}-{}", self.procs)
    }

    /// Format exactly one line (with a trailing newline).
    pub fn line(&self) -> String {
        let mut out = self.benchmark_name();
        out.push('\t');
        out.push_str(&self.iterations.to_string());
        for v in &self.values {
            out.push('\t');
            out.push_str(&format_number(v.value));
            out.push(' ');
            out.push_str(&v.unit);
        }
        out.push('\n');
        out
    }

    /// Write one line to `w`.
    pub fn write_to<W: Write>(&self, w: &mut W) -> io::Result<()> {
        w.write_all(self.line().as_bytes())
    }
}

impl fmt::Display for BenchResult {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.line().trim_end_matches('\n'))
    }
}

/// Format a number the way `benchfmt` does: integral values without a
/// decimal point, everything else with Rust's shortest round-trip form.
fn format_number(v: f64) -> String {
    if v.is_finite() && v == v.trunc() && v.abs() < 1e15 {
        format!("{}", v as i64)
    } else {
        format!("{v}")
    }
}

// ── Reader ───────────────────────────────────────────────────────────────────

/// A malformed benchmark line.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ParseError {
    /// 1-based line number when the error came from [`parse_benchmarks`].
    pub line: Option<usize>,
    /// Human-readable reason.
    pub message: String,
}

impl ParseError {
    fn new(message: impl Into<String>) -> Self {
        Self {
            line: None,
            message: message.into(),
        }
    }

    fn at(mut self, line: usize) -> Self {
        self.line = Some(line);
        self
    }
}

impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self.line {
            Some(n) => write!(f, "line {n}: {}", self.message),
            None => f.write_str(&self.message),
        }
    }
}

impl std::error::Error for ParseError {}

/// Parse one line.
///
/// Returns `Ok(None)` for metadata, `PASS`/`ok`/`FAIL`, blank lines and
/// anything else that is not a benchmark result.  Returns an error only
/// when a line starts with `Benchmark` but is malformed.
pub fn parse_line(line: &str) -> Result<Option<BenchResult>, ParseError> {
    let line = line.trim_end_matches(['\r', '\n']);
    if !line.starts_with("Benchmark") {
        return Ok(None);
    }
    let mut fields = line.split_whitespace();
    let head = fields
        .next()
        .ok_or_else(|| ParseError::new("empty benchmark line"))?;
    let (name, procs) = split_name_procs(head)?;
    let iters_tok = fields
        .next()
        .ok_or_else(|| ParseError::new("missing iteration count"))?;
    let iterations: u64 = iters_tok
        .parse()
        .map_err(|_| ParseError::new(format!("bad iteration count {iters_tok:?}")))?;

    let rest: Vec<&str> = fields.collect();
    let mut values = Vec::with_capacity(rest.len() / 2);
    let mut i = 0;
    while i < rest.len() {
        let number = rest[i];
        let value: f64 = number
            .parse()
            .map_err(|_| ParseError::new(format!("bad metric value {number:?}")))?;
        let unit = rest
            .get(i + 1)
            .ok_or_else(|| ParseError::new(format!("missing unit after {number:?}")))?;
        values.push(Value::new(value, *unit));
        i += 2;
    }

    Ok(Some(BenchResult {
        name,
        procs,
        iterations,
        values,
    }))
}

/// Parse every benchmark result in `text`, skipping metadata and test
/// status lines.  A malformed benchmark line is an error with its
/// 1-based line number.
pub fn parse_benchmarks(text: &str) -> Result<Vec<BenchResult>, ParseError> {
    let mut out = Vec::new();
    for (idx, line) in text.lines().enumerate() {
        match parse_line(line) {
            Ok(Some(r)) => out.push(r),
            Ok(None) => {}
            Err(e) => return Err(e.at(idx + 1)),
        }
    }
    Ok(out)
}

/// Split `BenchmarkFoo/bar-8` into `("Foo/bar", 8)`.  A missing `-<n>`
/// suffix is treated as `procs = 1`, which is what pre-1.5 Go output did.
fn split_name_procs(head: &str) -> Result<(String, u32), ParseError> {
    let name = head
        .strip_prefix("Benchmark")
        .ok_or_else(|| ParseError::new("benchmark line must start with Benchmark"))?;
    if name.is_empty() {
        return Err(ParseError::new("benchmark name is empty"));
    }
    if let Some((base, suffix)) = name.rsplit_once('-') {
        if !suffix.is_empty() && suffix.bytes().all(|b| b.is_ascii_digit()) {
            let procs = suffix
                .parse()
                .map_err(|_| ParseError::new(format!("bad procs suffix {suffix:?}")))?;
            if procs == 0 {
                return Err(ParseError::new("procs suffix must be positive"));
            }
            if base.is_empty() {
                return Err(ParseError::new("benchmark name is empty"));
            }
            return Ok((base.to_string(), procs));
        }
    }
    Ok((name.to_string(), 1))
}

// ── Writer helpers ───────────────────────────────────────────────────────────

/// Write the standard `goos`/`goarch`/`pkg` header understood by
/// `benchstat`.  `goos`/`goarch` are translated to the Go spellings.
pub fn write_metadata<W: Write>(w: &mut W, pkg: &str) -> io::Result<()> {
    writeln!(w, "goos: {}", goos())?;
    writeln!(w, "goarch: {}", goarch())?;
    writeln!(w, "pkg: {pkg}")?;
    Ok(())
}

fn goos() -> &'static str {
    match std::env::consts::OS {
        "macos" => "darwin",
        other => other,
    }
}

fn goarch() -> &'static str {
    match std::env::consts::ARCH {
        "x86_64" => "amd64",
        "x86" => "386",
        "aarch64" => "arm64",
        "arm" => "arm",
        "powerpc64" => "ppc64",
        "powerpc64le" => "ppc64le",
        "s390x" => "s390x",
        "riscv64" => "riscv64",
        other => other,
    }
}

// ── Harness ──────────────────────────────────────────────────────────────────

/// Configuration for [`Harness`], matching the subset of `go test -bench`
/// flags that makes sense here.
#[derive(Clone, Debug)]
pub struct BenchConfig {
    /// Minimum wall time for one auto-scaled run.
    pub benchtime: Duration,
    /// Number of independent samples (`-count`).
    pub count: usize,
    /// `-bench` pattern: substring, glob, or `.`/`*` for everything.
    pub filter: Option<String>,
    /// Hard cap on `b.N`.
    pub max_iterations: u64,
    /// Value used in the `-<procs>` suffix.
    pub procs: u32,
    /// `-benchtime 100x`: fixed iteration count instead of auto-scaling.
    pub fixed_iterations: Option<u64>,
}

impl Default for BenchConfig {
    fn default() -> Self {
        Self {
            benchtime: DEFAULT_BENCHTIME,
            count: 1,
            filter: None,
            max_iterations: DEFAULT_MAX_ITERATIONS,
            procs: process_count(),
            fixed_iterations: None,
        }
    }
}

impl BenchConfig {
    /// Parse benchmark flags.  `args` should not include the program name.
    ///
    /// Supported: `-bench`, `-benchtime`, `-count`, `-procs`, `-h`/`-help`.
    /// The cargo/libtest markers (`--bench`, `--test`, `--nocapture`, ...)
    /// are accepted and ignored.
    pub fn from_args<I, S>(args: I) -> Result<Self, String>
    where
        I: IntoIterator<Item = S>,
        S: AsRef<str>,
    {
        let args: Vec<String> = args.into_iter().map(|s| s.as_ref().to_string()).collect();
        let mut cfg = Self::default();
        let mut i = 0;
        while i < args.len() {
            let arg = &args[i];
            if arg == "--" {
                break;
            }
            let (flag, inline) = match arg.split_once('=') {
                Some((f, v)) => (f, Some(v.to_string())),
                None => (arg.as_str(), None),
            };
            match flag {
                "-bench" => {
                    cfg.filter = Some(take_value(&args, &mut i, inline, flag)?);
                }
                // `cargo bench` passes a bare `--bench` marker; Go users may
                // also write `--bench pattern`.  Disambiguate on the next arg.
                "--bench" => {
                    if let Some(v) = inline {
                        if v.is_empty() {
                            return Err("--bench needs a non-empty value".to_string());
                        }
                        cfg.filter = Some(v);
                    } else if let Some(next) = args.get(i + 1) {
                        if !next.starts_with('-') {
                            cfg.filter = Some(next.clone());
                            i += 1;
                        }
                    }
                }
                "-benchtime" | "--benchtime" => {
                    match parse_benchtime(&take_value(&args, &mut i, inline, flag)?)? {
                        BenchTime::Duration(d) => {
                            cfg.benchtime = d;
                            cfg.fixed_iterations = None;
                        }
                        BenchTime::Iterations(n) => {
                            cfg.fixed_iterations = Some(n);
                        }
                    }
                }
                "-count" | "--count" => {
                    let v = take_value(&args, &mut i, inline, flag)?;
                    let n: usize = v
                        .parse()
                        .map_err(|_| format!("-count needs a positive integer, got {v:?}"))?;
                    if n == 0 {
                        return Err("-count must be at least 1".to_string());
                    }
                    cfg.count = n;
                }
                "-procs" | "--procs" => {
                    let v = take_value(&args, &mut i, inline, flag)?;
                    let n: u32 = v
                        .parse()
                        .map_err(|_| format!("-procs needs a positive integer, got {v:?}"))?;
                    if n == 0 {
                        return Err("-procs must be at least 1".to_string());
                    }
                    cfg.procs = n;
                }
                "-h" | "--help" | "-help" => {
                    return Err("usage: <bench> [-bench pattern] [-benchtime 1s|100ms|Nx] \
                         [-count n] [-procs n]"
                        .to_string());
                }
                // Flags cargo and libtest pass through to bench targets.
                "--test" | "--nocapture" | "--quiet" | "--exact" | "--ignored"
                | "--include-ignored" | "--show-output" | "--no-fail-fast" => {}
                _ if flag.starts_with("--color") || flag.starts_with("-Z") => {}
                _ => return Err(format!("unknown benchmark flag {arg:?}")),
            }
            i += 1;
        }
        Ok(cfg)
    }

    /// True when `name` matches the `-bench` filter.
    pub fn should_run(&self, name: &str) -> bool {
        match self.filter.as_deref() {
            None => true,
            Some(pattern) => matches(pattern, name),
        }
    }
}

enum BenchTime {
    Duration(Duration),
    Iterations(u64),
}

fn take_value(
    args: &[String],
    i: &mut usize,
    inline: Option<String>,
    flag: &str,
) -> Result<String, String> {
    if let Some(v) = inline {
        return if v.is_empty() {
            Err(format!("{flag} needs a non-empty value"))
        } else {
            Ok(v)
        };
    }
    *i += 1;
    args.get(*i)
        .cloned()
        .ok_or_else(|| format!("{flag} needs a value"))
}

fn parse_benchtime(s: &str) -> Result<BenchTime, String> {
    let s = s.trim();
    if let Some(n) = s.strip_suffix('x') {
        let n: u64 = n
            .parse()
            .map_err(|_| format!("bad iteration count in -benchtime {s:?}"))?;
        if n == 0 {
            return Err("-benchtime iteration count must be positive".to_string());
        }
        return Ok(BenchTime::Iterations(n));
    }
    Ok(BenchTime::Duration(parse_duration(s)?))
}

fn parse_duration(s: &str) -> Result<Duration, String> {
    let split = s
        .find(|c: char| !(c.is_ascii_digit() || c == '.' || c == '+' || c == '-'))
        .ok_or_else(|| format!("-benchtime {s:?} needs a unit (ns, us, ms, s, m, h) or Nx"))?;
    let (number, unit) = s.split_at(split);
    let n: f64 = number
        .parse()
        .map_err(|_| format!("bad number in -benchtime {s:?}"))?;
    if !n.is_finite() || n <= 0.0 {
        return Err("-benchtime must be positive".to_string());
    }
    let seconds = match unit {
        "ns" => 1e-9,
        "us" | "µs" => 1e-6,
        "ms" => 1e-3,
        "s" => 1.0,
        "m" => 60.0,
        "h" => 3600.0,
        _ => {
            return Err(format!(
                "unknown -benchtime unit {unit:?} (use ns, us, ms, s, m, h or Nx)"
            ))
        }
    };
    let d = Duration::from_secs_f64(n * seconds);
    if d.is_zero() {
        return Err("-benchtime is below the timer resolution".to_string());
    }
    Ok(d)
}

/// Go-style `-bench` matching: a plain pattern is a substring, `*` and
/// `?` are globs, and `.`/`.*`/`*` match everything.
pub fn matches(pattern: &str, name: &str) -> bool {
    let pattern = pattern.trim();
    if pattern.is_empty() || pattern == "." || pattern == ".*" || pattern == "*" {
        return true;
    }
    if pattern.contains(['*', '?']) {
        glob_match(pattern, name)
    } else {
        name.contains(pattern)
    }
}

fn glob_match(pattern: &str, text: &str) -> bool {
    let p = pattern.as_bytes();
    let t = text.as_bytes();
    let (mut pi, mut ti) = (0usize, 0usize);
    let mut star: Option<usize> = None;
    let mut star_t = 0usize;
    while ti < t.len() {
        if pi < p.len() && (p[pi] == b'?' || p[pi] == t[ti]) {
            pi += 1;
            ti += 1;
        } else if pi < p.len() && p[pi] == b'*' {
            star = Some(pi);
            pi += 1;
            star_t = ti;
        } else if let Some(s) = star {
            pi = s + 1;
            star_t += 1;
            ti = star_t;
        } else {
            return false;
        }
    }
    while pi < p.len() && p[pi] == b'*' {
        pi += 1;
    }
    pi == p.len()
}

fn process_count() -> u32 {
    std::env::var("GOMAXPROCS")
        .ok()
        .and_then(|s| s.trim().parse::<u32>().ok())
        .filter(|&n| n > 0)
        .or_else(|| {
            std::thread::available_parallelism()
                .ok()
                .map(|n| n.get() as u32)
        })
        .unwrap_or(1)
}

/// A Go `testing.B`-style benchmark driver that writes `benchfmt` lines.
pub struct Harness<W: Write> {
    config: BenchConfig,
    out: W,
    package: Option<String>,
    header_written: bool,
}

impl Harness<io::Stdout> {
    /// Read flags from [`std::env::args`] and write to stdout.
    pub fn from_env() -> Result<Self, String> {
        Self::from_args(std::env::args().skip(1))
    }

    /// Read flags from an explicit argument list and write to stdout.
    pub fn from_args<I, S>(args: I) -> Result<Self, String>
    where
        I: IntoIterator<Item = S>,
        S: AsRef<str>,
    {
        Self::from_args_with_output(args, io::stdout())
    }
}

impl<W: Write> Harness<W> {
    /// Build a harness from a configuration and any writer.
    pub fn new(config: BenchConfig, out: W) -> Self {
        Self {
            config,
            out,
            package: None,
            header_written: false,
        }
    }

    /// Build a harness from flags and an arbitrary writer (useful in tests).
    pub fn from_args_with_output<I, S>(args: I, out: W) -> Result<Self, String>
    where
        I: IntoIterator<Item = S>,
        S: AsRef<str>,
    {
        Ok(Self::new(BenchConfig::from_args(args)?, out))
    }

    /// Emit `goos`/`goarch`/`pkg` before the first benchmark line.
    pub fn with_package(mut self, pkg: impl Into<String>) -> Self {
        self.package = Some(pkg.into());
        self
    }

    /// The active configuration.
    pub fn config(&self) -> &BenchConfig {
        &self.config
    }

    /// True when `name` matches `-bench`.
    pub fn should_run(&self, name: &str) -> bool {
        self.config.should_run(name)
    }

    /// Benchmark `f`, auto-scaling `b.N`, and write `ns/op`.
    ///
    /// Returns the emitted samples (one per `-count`).  Returns an empty
    /// vector when the name does not match `-bench`.
    pub fn bench<F, T>(&mut self, name: &str, mut f: F) -> io::Result<Vec<BenchResult>>
    where
        F: FnMut() -> T,
    {
        let mut metrics = || Vec::<Value>::new();
        self.run(name, &mut f, &mut metrics)
    }

    /// Benchmark `f` and additionally report `B/op` (the `-benchmem`
    /// column Go fills from its allocator counters).
    pub fn bench_bytes<F, T>(
        &mut self,
        name: &str,
        bytes_per_op: u64,
        mut f: F,
    ) -> io::Result<Vec<BenchResult>>
    where
        F: FnMut() -> T,
    {
        let mut metrics = move || vec![Value::new(bytes_per_op as f64, "B/op")];
        self.run(name, &mut f, &mut metrics)
    }

    /// Benchmark `f` and append caller-supplied metrics (computed once per
    /// sample, after the timed run).
    pub fn bench_with_metrics<F, M, T>(
        &mut self,
        name: &str,
        mut f: F,
        mut metrics: M,
    ) -> io::Result<Vec<BenchResult>>
    where
        F: FnMut() -> T,
        M: FnMut() -> Vec<Value>,
    {
        self.run(name, &mut f, &mut metrics)
    }

    /// Flush the writer.
    pub fn flush(&mut self) -> io::Result<()> {
        self.out.flush()
    }

    /// Consume the harness and return the writer.
    pub fn into_inner(self) -> W {
        self.out
    }

    fn write_header(&mut self) -> io::Result<()> {
        if self.header_written {
            return Ok(());
        }
        if let Some(pkg) = &self.package {
            write_metadata(&mut self.out, pkg)?;
        }
        self.header_written = true;
        Ok(())
    }

    fn run<F, M, T>(
        &mut self,
        name: &str,
        f: &mut F,
        metrics: &mut M,
    ) -> io::Result<Vec<BenchResult>>
    where
        F: FnMut() -> T,
        M: FnMut() -> Vec<Value>,
    {
        if !self.should_run(name) {
            return Ok(Vec::new());
        }
        self.write_header()?;
        let mut results = Vec::with_capacity(self.config.count);
        for _ in 0..self.config.count {
            let (iterations, elapsed) = measure(&self.config, f);
            let ns_per_op = elapsed.as_nanos() as f64 / iterations as f64;
            let mut result = BenchResult::new(name, self.config.procs, iterations);
            result.values.push(Value::new(ns_per_op, "ns/op"));
            result.values.extend(metrics());
            result.write_to(&mut self.out)?;
            self.out.flush()?;
            results.push(result);
        }
        Ok(results)
    }
}

/// Run `f` with an auto-scaled `b.N` until `benchtime` is reached.
fn measure<F, T>(config: &BenchConfig, f: &mut F) -> (u64, Duration)
where
    F: FnMut() -> T,
{
    if let Some(n) = config.fixed_iterations {
        return (n, run_iterations(f, n));
    }
    let mut n: u64 = 1;
    loop {
        let elapsed = run_iterations(f, n);
        if elapsed >= config.benchtime || n >= config.max_iterations {
            return (n, elapsed);
        }
        n = next_iterations(n, elapsed, config.benchtime).min(config.max_iterations);
    }
}

fn run_iterations<F, T>(f: &mut F, n: u64) -> Duration
where
    F: FnMut() -> T,
{
    let start = Instant::now();
    for _ in 0..n {
        std::hint::black_box(f());
    }
    start.elapsed()
}

/// Grow `n` so the next run is expected to take `benchtime`, using the
/// same 1/2/3/5/10 rounding Go's `testing` package uses.
fn next_iterations(n: u64, elapsed: Duration, benchtime: Duration) -> u64 {
    if elapsed.is_zero() {
        return n.saturating_mul(10).max(n + 1);
    }
    let ratio = benchtime.as_secs_f64() / elapsed.as_secs_f64();
    let proposed = (n as f64 * ratio).ceil();
    let proposed = if proposed.is_finite() && proposed >= 0.0 {
        proposed as u64
    } else {
        n.saturating_mul(2)
    };
    round_up(proposed.max(n + 1))
}

fn round_up(n: u64) -> u64 {
    if n < 10 {
        return n.max(1);
    }
    let mut base = 1u64;
    while base <= n / 10 {
        base *= 10;
    }
    for mult in [1u64, 2, 3, 5, 10] {
        if n <= base.saturating_mul(mult) {
            return base.saturating_mul(mult);
        }
    }
    base.saturating_mul(10)
}

// ── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_a_full_line() {
        let line = "BenchmarkSHA256/64B-8\t1234567\t812.3 ns/op\t64 B/op\t0 allocs/op\n";
        let r = parse_line(line).unwrap().unwrap();
        assert_eq!(r.name, "SHA256/64B");
        assert_eq!(r.procs, 8);
        assert_eq!(r.iterations, 1_234_567);
        assert_eq!(r.ns_per_op(), Some(812.3));
        assert_eq!(r.bytes_per_op(), Some(64.0));
        assert_eq!(r.allocs_per_op(), Some(0.0));
        assert_eq!(
            r.line(),
            "BenchmarkSHA256/64B-8\t1234567\t812.3 ns/op\t64 B/op\t0 allocs/op\n"
        );
    }

    #[test]
    fn parses_line_without_procs_suffix() {
        let r = parse_line("BenchmarkFoo\t10\t5 ns/op").unwrap().unwrap();
        assert_eq!(r.name, "Foo");
        assert_eq!(r.procs, 1);
        assert_eq!(r.ns_per_op(), Some(5.0));
    }

    #[test]
    fn ignores_non_benchmark_lines() {
        for line in [
            "",
            "PASS",
            "ok  \tcrypto\t1.234s",
            "goos: linux",
            "pkg: crypto_lib",
            "Benchmark", // becomes a malformed error, handled below
        ] {
            if line == "Benchmark" {
                assert!(parse_line(line).is_err());
            } else {
                assert!(parse_line(line).unwrap().is_none(), "{line:?}");
            }
        }
    }

    #[test]
    fn rejects_malformed_benchmark_lines() {
        assert!(parse_line("BenchmarkFoo-8\tnotanumber\t1 ns/op").is_err());
        assert!(parse_line("BenchmarkFoo-8\t10\t1").is_err());
        assert!(parse_line("BenchmarkFoo-8\t10\t1 ns/op\t2").is_err());
        assert!(parse_line("BenchmarkFoo-0\t10\t1 ns/op").is_err());
    }

    #[test]
    fn parses_a_stream_and_numbers_lines() {
        let text = "\
goos: linux
pkg: demo
BenchmarkA-4\t10\t1.5 ns/op
BenchmarkB/sub-4\t20\t2 ns/op
PASS
";
        let rs = parse_benchmarks(text).unwrap();
        assert_eq!(rs.len(), 2);
        assert_eq!(rs[0].name, "A");
        assert_eq!(rs[1].name, "B/sub");
        assert_eq!(rs[1].ns_per_op(), Some(2.0));

        let bad = "goos: linux\nBenchmarkA-4\tnope\t1 ns/op\n";
        let err = parse_benchmarks(bad).unwrap_err();
        assert_eq!(err.line, Some(2));
    }

    #[test]
    fn writer_uses_go_spellings_for_platform() {
        let mut buf = Vec::new();
        write_metadata(&mut buf, "demo").unwrap();
        let text = String::from_utf8(buf).unwrap();
        assert!(text.contains("goos: "));
        assert!(text.contains("goarch: "));
        assert!(text.contains("pkg: demo\n"));
        if std::env::consts::ARCH == "x86_64" {
            assert!(text.contains("goarch: amd64"));
        }
        if std::env::consts::OS == "macos" {
            assert!(text.contains("goos: darwin"));
        }
    }

    #[test]
    fn parsing_flags() {
        let cfg = BenchConfig::from_args([
            "-bench",
            "SHA*",
            "-benchtime",
            "10ms",
            "-count",
            "3",
            "-procs",
            "2",
        ])
        .unwrap();
        assert_eq!(cfg.filter.as_deref(), Some("SHA*"));
        assert_eq!(cfg.benchtime, Duration::from_millis(10));
        assert_eq!(cfg.count, 3);
        assert_eq!(cfg.procs, 2);

        let cfg = BenchConfig::from_args(["-benchtime=100x"]).unwrap();
        assert_eq!(cfg.fixed_iterations, Some(100));

        assert!(BenchConfig::from_args(["-count", "0"]).is_err());
        assert!(BenchConfig::from_args(["-benchtime", "10"]).is_err());
        assert!(BenchConfig::from_args(["-wat"]).is_err());
        // cargo/libtest markers are accepted.
        let cfg = BenchConfig::from_args(["--bench", "--nocapture"]).unwrap();
        assert!(cfg.filter.is_none());
        let cfg = BenchConfig::from_args(["--bench", "SHA*"]).unwrap();
        assert_eq!(cfg.filter.as_deref(), Some("SHA*"));
    }

    #[test]
    fn filter_matching() {
        assert!(matches(".", "anything"));
        assert!(matches("*", "anything"));
        assert!(matches("SHA", "BenchSHA256"));
        assert!(matches("SHA*", "SHA256/64B"));
        assert!(matches("SHA?56", "SHA256"));
        assert!(!matches("AES*", "SHA256"));
        assert!(matches("AES/*", "AES/128"));
    }

    #[test]
    fn harness_writes_a_line_and_honours_count() {
        let cfg = BenchConfig {
            benchtime: Duration::from_millis(1),
            count: 2,
            procs: 3,
            ..BenchConfig::default()
        };
        let mut h = Harness::new(cfg, Vec::new()).with_package("demo");
        let results = h
            .bench("Smoke", || {
                std::hint::black_box(1u64.wrapping_add(1));
            })
            .unwrap();
        assert_eq!(results.len(), 2);
        assert!(results[0].iterations >= 1);
        assert!(results[0].ns_per_op().is_some());

        let text = String::from_utf8(h.into_inner()).unwrap();
        assert!(text.contains("goos: "));
        assert!(text.contains("pkg: demo"));
        assert_eq!(text.matches("BenchmarkSmoke-3\t").count(), 2);
        assert!(text.contains(" ns/op"));
    }

    #[test]
    fn harness_reports_bytes_and_filters() {
        let cfg = BenchConfig {
            benchtime: Duration::from_millis(1),
            count: 1,
            filter: Some("keep*".to_string()),
            procs: 1,
            ..BenchConfig::default()
        };
        let mut h = Harness::new(cfg, Vec::new());
        assert!(h.bench("drop", || {}).unwrap().is_empty());
        let r = h
            .bench_bytes("keep/1KiB", 1024, || {
                std::hint::black_box(0u8);
            })
            .unwrap();
        assert_eq!(r.len(), 1);
        assert_eq!(r[0].bytes_per_op(), Some(1024.0));
    }

    #[test]
    fn fixed_iterations_are_exact() {
        let cfg = BenchConfig {
            fixed_iterations: Some(7),
            procs: 1,
            ..BenchConfig::default()
        };
        let mut h = Harness::new(cfg, Vec::new());
        let r = h.bench("fixed", || {}).unwrap();
        assert_eq!(r[0].iterations, 7);
    }

    #[test]
    fn round_up_uses_go_series() {
        assert_eq!(round_up(1), 1);
        assert_eq!(round_up(7), 7);
        assert_eq!(round_up(11), 20);
        assert_eq!(round_up(21), 30);
        assert_eq!(round_up(31), 50);
        assert_eq!(round_up(51), 100);
        assert_eq!(round_up(101), 200);
    }
}
