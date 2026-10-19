//! Persistent CUDA/Metal workers, explicit host emulation, and bounded I/O.
//! CPU binaries need no GPU SDK or driver at build time.
use std::io::{BufRead, BufReader, Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::{Arc, Condvar, Mutex};
use std::thread::JoinHandle;
use std::time::{Duration, Instant};

use clap::ValueEnum;
use num_bigint::BigUint;
use serde::Serialize;

use super::{ChallengeGroup, ChallengePoint, SolveReport};

pub(super) fn check_deadline(deadline: Option<Instant>) -> Result<(), String> {
    if deadline.is_some_and(|deadline| Instant::now() >= deadline) {
        return Err("device worker session deadline exceeded".into());
    }
    Ok(())
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, ValueEnum)]
pub enum Backend {
    Cpu,
    Auto,
    Cuda,
    Metal,
    /// Run the shared device source on the host; this is not GPU execution.
    GpuEmulator,
}
impl Backend {
    pub fn name(self) -> &'static str {
        match self {
            Self::Cpu => "cpu",
            Self::Auto => "auto",
            Self::Cuda => "cuda",
            Self::Metal => "metal",
            Self::GpuEmulator => "gpu-emulator",
        }
    }
}

#[derive(Clone, Debug)]
pub struct DeviceOptions {
    pub backend: Backend,
    pub worker: Option<PathBuf>,
    pub device: u32,
    pub batch_size: usize,
    pub rho_walks: usize,
    /// Deadline for the entire worker session, including setup and host work.
    pub timeout_seconds: u64,
}
impl Default for DeviceOptions {
    fn default() -> Self {
        Self {
            backend: Backend::Cpu,
            worker: None,
            device: 0,
            batch_size: 128,
            rho_walks: 32,
            timeout_seconds: 120,
        }
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct ExecutionReport {
    pub backend: String,
    pub device: Option<String>,
    pub kernel_launches: u64,
    pub device_point_multiplications: u64,
    pub device_point_additions: u64,
    /// Floyd iterations summed over walks; each iteration has three steps.
    pub device_rho_iterations: u64,
    pub host_verification: bool,
    pub note: Option<String>,
}
impl Default for ExecutionReport {
    fn default() -> Self {
        Self {
            backend: "cpu".into(),
            device: None,
            kernel_launches: 0,
            device_point_multiplications: 0,
            device_point_additions: 0,
            device_rho_iterations: 0,
            host_verification: true,
            note: None,
        }
    }
}

pub(super) fn integer(k: &BigUint) -> Result<[u32; 5], String> {
    if k.bits() > 131 {
        return Err("device integer exceeds the exact 131-bit representation".into());
    }
    let mut words = [0; 5];
    let digits = k.to_u32_digits();
    words[..digits.len()].copy_from_slice(&digits);
    Ok(words)
}
pub(super) fn big(words: &[u32]) -> BigUint {
    BigUint::new(words.to_vec())
}
pub(super) fn point(group: &ChallengeGroup, p: &ChallengePoint) -> [u32; 11] {
    let mut words = [0; 11];
    if let Some((x, y)) = group.coordinates(p) {
        words[..5].copy_from_slice(&integer(&x).expect("validated exact-curve coordinate"));
        words[5..10].copy_from_slice(&integer(&y).expect("validated exact-curve coordinate"));
    } else {
        words[10] = 1;
    }
    words
}

pub(super) fn decode_point(
    group: &ChallengeGroup,
    words: &[u32],
) -> Result<ChallengePoint, String> {
    if words.len() != 11 || words[10] > 1 {
        return Err("invalid device point encoding".into());
    }
    if words[10] == 1 {
        if words[..10].iter().any(|v| *v != 0) {
            return Err("noncanonical device infinity".into());
        }
        return Ok(group.identity());
    }
    group.point_on_curve(&big(&words[..5]), &big(&words[5..10]))
}

fn curve_words(group: &ChallengeGroup, target: &ChallengePoint) -> Result<Vec<u32>, String> {
    use super::Curve;
    let mut words = Vec::with_capacity(43);
    let (binary, modulus, a, b) = match &group.curve {
        Curve::Prime(c) => (0, c.p.clone(), c.a.clone(), c.b.clone()),
        Curve::Binary(c) => {
            let mut modulus = BigUint::from(1u32) << c.m;
            for term in &c.irreducible.low_terms {
                modulus |= BigUint::from(1u32) << *term;
            }
            (1, modulus, c.a.to_biguint(), c.b.to_biguint())
        }
    };
    words.push(binary);
    // The binary reduction polynomial includes its degree-131 bit.
    let mut polynomial = [0; 5];
    let digits = modulus.to_u32_digits();
    polynomial[..digits.len()].copy_from_slice(&digits);
    words.extend(polynomial);
    for value in [&a, &b, group.order()] {
        words.extend(integer(value)?);
    }
    words.extend(point(group, &group.generator()));
    words.extend(point(group, target));
    Ok(words)
}

/// An explicitly identified process running actual kernels or host emulation.
/// Dropping it closes the session, stops the watchdog, and reaps the process.
pub struct DeviceWorker {
    child: Arc<Mutex<Child>>,
    input: ChildStdin,
    output: BufReader<ChildStdout>,
    stop: Arc<(Mutex<bool>, Condvar)>,
    watchdog: Option<JoinHandle<()>>,
    deadline: Instant,
    curve: Vec<u32>,
    batch_size: usize,
    pub(super) rho_walks: usize,
    pub(super) execution: ExecutionReport,
}

impl DeviceWorker {
    pub fn open(
        group: &ChallengeGroup,
        target: &ChallengePoint,
        opts: &DeviceOptions,
        path: &Path,
        expected: Backend,
    ) -> Result<Self, String> {
        let deadline = Instant::now()
            .checked_add(Duration::from_secs(opts.timeout_seconds))
            .ok_or("worker session timeout exceeds this host's monotonic clock range")?;
        group.validate(target)?;
        if !matches!(
            expected,
            Backend::Cuda | Backend::Metal | Backend::GpuEmulator
        ) {
            return Err("worker must explicitly identify CUDA, Metal, or GPU emulation".into());
        }
        let curve = curve_words(group, target)?;
        if !(1..=4096).contains(&opts.batch_size)
            || !(1..=4096).contains(&opts.rho_walks)
            || opts.timeout_seconds == 0
        {
            return Err(
                "GPU batch size and rho walks must be 1..4096; timeout must be positive".into(),
            );
        }
        check_deadline(Some(deadline))?;
        let mut command = Command::new(path);
        command
            .args(["--device", &opts.device.to_string()])
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit());
        #[cfg(unix)]
        {
            use std::os::unix::process::CommandExt;
            // SAFETY: setpgid is async-signal-safe; no allocation in pre_exec.
            unsafe {
                command.pre_exec(|| {
                    if libc::setpgid(0, 0) == 0 {
                        Ok(())
                    } else {
                        Err(std::io::Error::last_os_error())
                    }
                });
            }
        }
        let mut child = command
            .spawn()
            .map_err(|e| format!("start {}: {e}", path.display()))?;
        let input = child.stdin.take().ok_or("missing worker stdin")?;
        let output = BufReader::new(child.stdout.take().ok_or("missing worker stdout")?);
        let child = Arc::new(Mutex::new(child));
        let stop = Arc::new((Mutex::new(false), Condvar::new()));
        let watchdog = {
            let child = Arc::clone(&child);
            let stop = Arc::clone(&stop);
            std::thread::spawn(move || {
                let (lock, cv) = &*stop;
                let guard = lock.lock().unwrap_or_else(|e| e.into_inner());
                let (guard, _) = cv
                    .wait_timeout_while(
                        guard,
                        deadline.saturating_duration_since(Instant::now()),
                        |done| !*done,
                    )
                    .unwrap_or_else(|e| e.into_inner());
                if !*guard {
                    let mut child = child.lock().unwrap_or_else(|e| e.into_inner());
                    #[cfg(unix)]
                    // SAFETY: this child owns a separate, unreaped process group.
                    unsafe {
                        libc::kill(-(child.id() as i32), libc::SIGKILL);
                    }
                    let _ = child.kill();
                }
            })
        };
        let mut worker = Self {
            child,
            input,
            output,
            stop,
            watchdog: Some(watchdog),
            deadline,
            curve,
            batch_size: opts.batch_size,
            rho_walks: opts.rho_walks,
            execution: ExecutionReport::default(),
        };
        worker.ensure_active()?;
        let mut greeting = Vec::new();
        (&mut worker.output)
            .take(4097)
            .read_until(b'\n', &mut greeting)
            .map_err(|e| format!("worker handshake: {e}"))?;
        if greeting.len() > 4096 || greeting.last() != Some(&b'\n') {
            return Err("worker unavailable, timed out, or returned an invalid handshake".into());
        }
        let greeting = String::from_utf8(greeting).map_err(|e| e.to_string())?;
        let fields: Vec<_> = greeting.trim_end().splitn(4, ' ').collect();
        if fields.len() != 4
            || fields[0] != "CERTICOM_WORKER"
            || fields[1] != "1"
            || fields[2] != expected.name()
        {
            return Err(format!(
                "worker does not identify as the requested {} backend",
                expected.name()
            ));
        }
        worker.execution.backend = expected.name().into();
        worker.execution.device = Some(fields[3].into());
        if expected == Backend::GpuEmulator {
            worker.execution.note =
                Some("Device source executed on the CPU; no GPU hardware was used".into());
        }
        worker.ensure_active()?;
        Ok(worker)
    }

    /// Reject work and results once the whole session's monotonic deadline passes.
    /// The watchdog also kills blocked native I/O; this check covers host work
    /// and solver paths that do not make another device request.
    pub fn ensure_active(&self) -> Result<(), String> {
        check_deadline(Some(self.deadline))
    }

    pub(super) fn deadline(&self) -> Instant {
        self.deadline
    }

    pub(super) fn finish(&self, mut report: SolveReport) -> Result<SolveReport, String> {
        self.ensure_active()?;
        report.execution = self.execution();
        self.ensure_active()?;
        Ok(report)
    }

    pub fn execution(&self) -> ExecutionReport {
        self.execution.clone()
    }

    pub(super) fn check_binding(
        &self,
        group: &ChallengeGroup,
        target: &ChallengePoint,
    ) -> Result<(), String> {
        self.ensure_active()?;
        if self.curve != curve_words(group, target)? {
            return Err("device worker belongs to a different exact curve or target".into());
        }
        self.ensure_active()
    }

    pub(super) fn batch_size(&self) -> usize {
        self.batch_size
    }

    fn request(
        &mut self,
        op: u32,
        count: usize,
        steps: u32,
        payload: &[u32],
        output_words: usize,
    ) -> Result<Vec<u32>, String> {
        self.ensure_active()?;
        if count == 0 || count > 4096 {
            return Err("invalid device request count".into());
        }
        let mut bytes = Vec::with_capacity(4 * (4 + self.curve.len() + payload.len()));
        for value in [0x43435131, op, count as u32, steps]
            .iter()
            .chain(&self.curve)
            .chain(payload)
        {
            bytes.extend(value.to_le_bytes());
        }
        self.ensure_active()?;
        self.input
            .write_all(&bytes)
            .map_err(|e| format!("worker write: {e}"))?;
        self.input.flush().map_err(|e| e.to_string())?;
        let mut header = [0u8; 12];
        self.output
            .read_exact(&mut header)
            .map_err(|e| format!("worker stopped, timed out, or truncated its reply: {e}"))?;
        self.ensure_active()?;
        let word = |i| u32::from_le_bytes(header[i..i + 4].try_into().unwrap());
        if word(0) != 0x43435231 {
            return Err("worker reply protocol mismatch".into());
        }
        if word(4) != 0 {
            let n = word(8) as usize;
            if n > 4096 {
                return Err("invalid worker error length".into());
            }
            let mut message = vec![0; n];
            self.output
                .read_exact(&mut message)
                .map_err(|e| e.to_string())?;
            return Err(format!(
                "device kernel failed: {}",
                String::from_utf8_lossy(&message)
            ));
        }
        if word(8) as usize != count {
            return Err("worker reply count mismatch".into());
        }
        let mut bytes = vec![0; output_words * 4];
        self.output
            .read_exact(&mut bytes)
            .map_err(|e| format!("truncated worker payload: {e}"))?;
        self.ensure_active()?;
        self.execution.kernel_launches += 1;
        Ok(bytes
            .chunks(4)
            .map(|w| u32::from_le_bytes(w.try_into().unwrap()))
            .collect())
    }

    pub(super) fn add(
        &mut self,
        group: &ChallengeGroup,
        pairs: &[(ChallengePoint, ChallengePoint)],
    ) -> Result<Vec<ChallengePoint>, String> {
        self.ensure_active()?;
        let mut result = Vec::with_capacity(pairs.len());
        for batch in pairs.chunks(self.batch_size) {
            let payload: Vec<_> = batch
                .iter()
                .flat_map(|(p, _)| point(group, p))
                .chain(batch.iter().flat_map(|(_, q)| point(group, q)))
                .collect();
            let words = self.request(1, batch.len(), 0, &payload, batch.len() * 11)?;
            result.extend(
                words
                    .chunks(11)
                    .map(|w| {
                        self.ensure_active()?;
                        decode_point(group, w)
                    })
                    .collect::<Result<Vec<_>, _>>()?,
            );
            self.execution.device_point_additions += batch.len() as u64;
        }
        self.ensure_active()?;
        Ok(result)
    }

    pub(super) fn mul(
        &mut self,
        group: &ChallengeGroup,
        requests: &[(ChallengePoint, BigUint)],
    ) -> Result<Vec<ChallengePoint>, String> {
        self.ensure_active()?;
        let mut result = Vec::with_capacity(requests.len());
        for batch in requests.chunks(self.batch_size) {
            let mut payload: Vec<_> = batch.iter().flat_map(|(p, _)| point(group, p)).collect();
            for (_, k) in batch {
                payload.extend(integer(k)?);
            }
            let words = self.request(2, batch.len(), 0, &payload, batch.len() * 11)?;
            result.extend(
                words
                    .chunks(11)
                    .map(|w| {
                        self.ensure_active()?;
                        decode_point(group, w)
                    })
                    .collect::<Result<Vec<_>, _>>()?,
            );
            self.execution.device_point_multiplications += batch.len() as u64;
        }
        self.ensure_active()?;
        Ok(result)
    }

    pub(super) fn rho(
        &mut self,
        states: &[[u32; 45]],
        steps: u32,
    ) -> Result<Vec<[u32; 45]>, String> {
        self.ensure_active()?;
        let mut result = Vec::with_capacity(states.len());
        for batch in states.chunks(self.batch_size) {
            let payload: Vec<_> = batch.iter().flat_map(|s| s.iter().copied()).collect();
            let words = self.request(3, batch.len(), steps, &payload, batch.len() * 45)?;
            result.extend(words.chunks(45).map(|w| <[u32; 45]>::try_from(w).unwrap()));
        }
        self.ensure_active()?;
        Ok(result)
    }
}

impl Drop for DeviceWorker {
    fn drop(&mut self) {
        let (lock, cv) = &*self.stop;
        *lock.lock().unwrap_or_else(|e| e.into_inner()) = true;
        cv.notify_one();
        if let Some(watchdog) = self.watchdog.take() {
            let _ = watchdog.join();
        }
        let mut child = self.child.lock().unwrap_or_else(|e| e.into_inner());
        #[cfg(unix)]
        // SAFETY: the unreaped child owns this process group.
        unsafe {
            libc::kill(-(child.id() as i32), libc::SIGKILL);
        }
        let _ = child.kill();
        let _ = child.wait();
    }
}

fn discover(kind: Backend) -> Option<PathBuf> {
    let name = match kind {
        Backend::Cuda => "certicom_cuda",
        Backend::Metal => "certicom_metal",
        Backend::GpuEmulator => "certicom_emulator",
        _ => return None,
    };
    let exe = std::env::current_exe().ok()?;
    let path = exe.parent()?.join(name);
    path.is_file().then_some(path)
}

/// Explicit GPU selection fails on missing hardware. Only `auto` may choose CPU.
pub fn select(
    group: &ChallengeGroup,
    target: &ChallengePoint,
    opts: &DeviceOptions,
) -> Result<(Option<DeviceWorker>, ExecutionReport), String> {
    if opts.backend == Backend::Cpu {
        if opts.worker.is_some() {
            return Err("--gpu-worker requires a GPU backend or gpu-emulator".into());
        }
        return Ok((None, ExecutionReport::default()));
    }
    if opts.backend != Backend::Auto {
        let path = opts
            .worker
            .clone()
            .or_else(|| discover(opts.backend))
            .ok_or_else(|| {
                format!(
                    "{} worker not found; build gpu/certicom and pass --gpu-worker PATH",
                    opts.backend.name()
                )
            })?;
        let worker = DeviceWorker::open(group, target, opts, &path, opts.backend)?;
        let execution = worker.execution();
        return Ok((Some(worker), execution));
    }
    if opts.worker.is_some() {
        return Err(
            "an explicit --gpu-worker requires --backend cuda, metal, or gpu-emulator".into(),
        );
    }
    let order = if cfg!(target_os = "macos") {
        [Backend::Metal, Backend::Cuda]
    } else {
        [Backend::Cuda, Backend::Metal]
    };
    let mut reasons = Vec::new();
    for kind in order {
        if let Some(path) = discover(kind) {
            match DeviceWorker::open(group, target, opts, &path, kind) {
                Ok(worker) => {
                    let execution = worker.execution();
                    return Ok((Some(worker), execution));
                }
                Err(e) => reasons.push(e),
            }
        }
    }
    let note = if reasons.is_empty() {
        "auto selected CPU; no CUDA or Metal worker installed beside the executable".into()
    } else {
        format!(
            "auto selected CPU; GPU workers unavailable: {}",
            reasons.join("; ")
        )
    };
    Ok((
        None,
        ExecutionReport {
            note: Some(note),
            ..ExecutionReport::default()
        },
    ))
}
