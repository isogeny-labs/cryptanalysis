//! **Complete factorisation** by a dispatch ladder, recursing on cofactors.
//!
//! For each composite piece, cheapest method first:
//!
//! 1. **trial division** by primes up to `trial_bound` (once, on `n`);
//! 2. **perfect power** check (`m = rᵏ` → recurse on `r` with exponent
//!    `k`);
//! 3. **primality**: Baillie–PSW ([`is_probable_prime`]);
//! 4. **Pollard–Brent rho** with a small budget (factors to ~10 digits);
//! 5. **Pollard p − 1** (and optionally Williams p + 1);
//! 6. **ECM** ([`crate::cryptanalysis::ecm`]) for pieces of at least
//!    `ecm_min_digits` digits — a few curves per level, aimed at factors
//!    of 12–25 digits before the sieve is committed to;
//! 7. **SNFS** when the caller supplied a special form that the piece
//!    divides and the piece has at least `snfs_min_digits` digits;
//! 8. **SIQS** up to `qs_max_digits`, **GNFS** above.
//!
//! Every split is verified by multiplication, every final factor passes
//! BPSW (proven below `2⁶⁴`, probable above — [`PrimeFactor::proven`]),
//! and the report is `verified` only if the product of `pᵉ` over all
//! factors times any unfactored remainder equals `n`.
//!
//! On the crossover: with the sieves of this suite the QS is faster than
//! the GNFS at every size either can reach, so the default sends
//! everything up to 100 digits to the QS; `prefer_nfs` changes that.

use num_bigint::BigUint;
use num_integer::Integer;
use num_traits::{One, Zero};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::time::Instant;

use super::arith::{decimal_digits, is_probable_prime, perfect_power, primes_up_to, secs};
use super::nfs::gnfs::{gnfs, GnfsParams};
use super::nfs::snfs::{snfs, SnfsInput, SnfsParams};
use super::pm1::{pm1, pp1, Pm1Params, Pp1Params};
use super::qs::{qs, QsParams};
use super::rho_factor::{rho, RhoParams};
use super::{serde_big, ProgressFn};
use crate::cryptanalysis::ecm::{ecm_factor_progressive, ecm_one_curve, EcmResult};

/// The method that isolated a factor.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum Method {
    /// The input (or a cofactor) was prime already.
    Primality,
    /// Trial division.
    TrialDivision,
    /// `m = rᵏ`.
    PerfectPower,
    /// Pollard–Brent rho.
    Rho,
    /// Pollard p − 1.
    PMinus1,
    /// Williams p + 1.
    PPlus1,
    /// Lenstra ECM.
    Ecm,
    /// Self-initialising quadratic sieve.
    Qs,
    /// General number field sieve.
    Gnfs,
    /// Special number field sieve.
    Snfs,
}

/// Options for [`factor`].
#[derive(Clone, Debug, Serialize)]
pub struct FactorOptions {
    /// Trial-division bound.
    pub trial_bound: u64,
    /// Rho budget.
    pub rho: RhoParams,
    /// p − 1 bounds (`b1 = 0` skips p − 1).
    pub pm1: Pm1Params,
    /// Williams p + 1 (`None` skips it).
    pub pp1: Option<Pp1Params>,
    /// ECM smoothness bounds, one level each.
    pub ecm_b1_levels: Vec<u64>,
    /// ECM curves per level (0 skips ECM).
    pub ecm_curves_per_level: u64,
    /// Smallest piece (digits) on which ECM is run.
    pub ecm_min_digits: usize,
    /// Largest piece (digits) sent to the QS when `prefer_nfs` is false.
    pub qs_max_digits: usize,
    /// Use the GNFS instead of the QS from `nfs_min_digits` digits up.
    pub prefer_nfs: bool,
    /// Smallest piece (digits) for the GNFS when `prefer_nfs` is set.
    pub nfs_min_digits: usize,
    /// A special form of `n` (or of a multiple of `n`) for the SNFS.
    pub snfs_form: Option<SnfsInput>,
    /// Smallest piece (digits) for the SNFS.
    pub snfs_min_digits: usize,
    /// QS parameters.
    pub qs: QsParams,
    /// GNFS parameters.
    pub gnfs: GnfsParams,
    /// SNFS parameters.
    pub snfs: SnfsParams,
    /// Seed for the randomised methods.
    pub seed: u64,
}

impl Default for FactorOptions {
    fn default() -> Self {
        FactorOptions {
            trial_bound: 1 << 16,
            rho: RhoParams {
                max_iterations: 1 << 18,
                attempts: 2,
                batch: 128,
            },
            pm1: Pm1Params {
                b1: 20_000,
                b2: 1_000_000,
                base: 3,
            },
            pp1: None,
            ecm_b1_levels: vec![2_000, 11_000],
            ecm_curves_per_level: 8,
            ecm_min_digits: 45,
            qs_max_digits: 100,
            prefer_nfs: false,
            nfs_min_digits: 40,
            snfs_form: None,
            snfs_min_digits: 40,
            qs: QsParams::default(),
            gnfs: GnfsParams::default(),
            snfs: SnfsParams::default(),
            seed: 1,
        }
    }
}

/// One prime power of the factorisation.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PrimeFactor {
    /// The prime.
    #[serde(with = "serde_big::biguint")]
    pub prime: BigUint,
    /// Its exponent in `n`.
    pub exponent: u32,
    /// The method that isolated it.
    pub method: Method,
    /// `true` below `2⁶⁴`, where BPSW is proven to have no pseudoprimes.
    pub proven: bool,
}

/// One attempted split.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Step {
    /// Method tried.
    pub method: Method,
    /// Digits of the piece.
    pub digits: usize,
    /// The piece.
    #[serde(with = "serde_big::biguint")]
    pub input: BigUint,
    /// The factor found, if any.
    #[serde(with = "serde_big::opt_biguint")]
    pub found: Option<BigUint>,
    /// Wall-clock seconds.
    pub seconds: f64,
}

/// Outcome of [`factor`].
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FactorReport {
    /// The input.
    #[serde(with = "serde_big::biguint")]
    pub n: BigUint,
    /// Prime factorisation found (sorted by prime).
    pub factors: Vec<PrimeFactor>,
    /// Composite pieces no method split, with multiplicity.
    pub unfactored: Vec<(String, u32)>,
    /// `unfactored` is empty.
    pub complete: bool,
    /// `∏ pᵉ · ∏ unfactored = n` and every `p` passes BPSW.
    pub verified: bool,
    /// Every split attempted, in order.
    pub steps: Vec<Step>,
    /// Wall-clock seconds.
    pub total_seconds: f64,
}

/// Restart state for the automatic factoring ladder. The caller binds it to
/// its input/options manifest and stores it with a checksum.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FactorState {
    pub schema_version: u32,
    pub generation: u64,
    pub report: FactorReport,
    pub pending: Vec<PendingPiece>,
    pub active: Option<ActivePiece>,
    pub seed: u64,
    pub elapsed_seconds: f64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PendingPiece {
    #[serde(with = "serde_big::biguint")]
    pub n: BigUint,
    pub multiplicity: u32,
    pub method: Method,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ActivePiece {
    pub piece: PendingPiece,
    pub next_method: usize,
    pub attempt_seed: Option<u64>,
    pub attempt_method: Option<Method>,
    pub ecm_next_curve: u64,
}

/// Fully factor `n`.
pub fn factor(n: &BigUint, options: &FactorOptions) -> FactorReport {
    factor_with_progress(n, options, None)
}

fn record(factors: &mut Vec<PrimeFactor>, p: BigUint, e: u32, method: Method) {
    if let Some(f) = factors.iter_mut().find(|f| f.prime == p) {
        f.exponent += e;
        return;
    }
    let proven = p.bits() <= 64;
    factors.push(PrimeFactor {
        prime: p,
        exponent: e,
        method,
        proven,
    });
}

/// Try one method on `m`; returns a verified proper divisor.
fn checkpoint_failure(message: &str) -> bool {
    message.contains("checkpoint")
        || message.contains(".ckpt")
        || message.contains("polynomial choices")
}

fn try_method(
    method: Method,
    m: &BigUint,
    options: &FactorOptions,
    seed: u64,
    progress: ProgressFn,
    checkpoint_path: Option<PathBuf>,
) -> Result<Option<BigUint>, String> {
    let g = match method {
        Method::Rho => rho(m, &options.rho).factor,
        Method::PMinus1 => pm1(m, &options.pm1).factor,
        Method::PPlus1 => options.pp1.as_ref().and_then(|p| pp1(m, p).factor),
        Method::Ecm => ecm_factor_progressive(
            m,
            &options.ecm_b1_levels,
            options.ecm_curves_per_level,
            seed,
        )
        .map(|(g, _)| g),
        Method::Qs => {
            let mut params = options.qs.clone();
            params.resume = checkpoint_path.as_ref().is_some_and(|path| path.is_file());
            params.checkpoint_path = checkpoint_path;
            let result = qs(m, &params, progress);
            if let Some(error) = result.failure.as_deref().filter(|e| checkpoint_failure(e)) {
                return Err(format!("SIQS: {error}"));
            }
            result.factor
        }
        Method::Gnfs => {
            let mut params = options.gnfs.clone();
            params.nfs.resume = checkpoint_path.as_ref().is_some_and(|path| path.is_file());
            params.nfs.checkpoint_path = checkpoint_path;
            let result = gnfs(m, &params, progress);
            if let Some(error) = result.failure.as_deref().filter(|e| checkpoint_failure(e)) {
                return Err(format!("GNFS: {error}"));
            }
            result.factor
        }
        Method::Snfs => {
            let mut params = options.snfs.clone();
            params.nfs.resume = checkpoint_path.as_ref().is_some_and(|path| path.is_file());
            params.nfs.checkpoint_path = checkpoint_path;
            let result = options
                .snfs_form
                .as_ref()
                .map(|form| snfs(m, form, &params, progress));
            if let Some(result) = result {
                if let Some(error) = result.failure.as_deref().filter(|e| checkpoint_failure(e)) {
                    return Err(format!("SNFS: {error}"));
                }
                result.factor
            } else {
                None
            }
        }
        _ => None,
    };
    let Some(g) = g else { return Ok(None) };
    let (q, r) = m.div_rem(&g);
    Ok((r.is_zero() && !g.is_one() && &g != m && &g * &q == *m).then_some(g))
}

/// Does the special form (if any) apply to the piece `m`?
fn snfs_applies(form: &SnfsInput, m: &BigUint) -> bool {
    use super::arith::bigint_mod;
    use num_bigint::BigInt;
    match form {
        SnfsInput::Form { r, e, s, c } => {
            let big = BigInt::from(*c) * num_traits::pow(BigInt::from(*r), *e as usize) + *s;
            bigint_mod(&big, m).is_zero()
        }
        SnfsInput::Poly { coeffs, m: root } => {
            let f = super::nfs::poly::IntPoly::new(coeffs.clone());
            bigint_mod(&f.eval(&BigInt::from(root.clone())), m).is_zero()
        }
    }
}

/// [`factor`] with a progress callback for the sieves.
pub fn factor_with_progress(
    n: &BigUint,
    options: &FactorOptions,
    progress: ProgressFn,
) -> FactorReport {
    factor_with_state(n, options, progress, None, None, None)
        .expect("factoring without state cannot fail at a state boundary")
}

/// Continue the full ladder from a validated checkpoint. `save` runs at
/// completed cofactor/method boundaries; the sieve methods also use their own
/// batch checkpoints in `checkpoint_dir`.
pub fn factor_with_state(
    n: &BigUint,
    options: &FactorOptions,
    progress: ProgressFn,
    initial: Option<FactorState>,
    checkpoint_dir: Option<&std::path::Path>,
    save: Option<&dyn Fn(&FactorState) -> Result<(), String>>,
) -> Result<FactorReport, String> {
    let t0 = Instant::now();
    if n.is_zero() {
        let mut report = FactorReport {
            n: n.clone(),
            factors: Vec::new(),
            unfactored: Vec::new(),
            complete: false,
            verified: false,
            steps: Vec::new(),
            total_seconds: 0.0,
        };
        report.unfactored.push(("0".into(), 1));
        return Ok(report);
    }
    let mut state = if let Some(state) = initial {
        state
    } else {
        let mut report = FactorReport {
            n: n.clone(),
            factors: Vec::new(),
            unfactored: Vec::new(),
            complete: false,
            verified: false,
            steps: Vec::new(),
            total_seconds: 0.0,
        };
        let mut rest = n.clone();
        let t = Instant::now();
        for p in primes_up_to(options.trial_bound.max(2)) {
            let pb = BigUint::from(p);
            if &pb * &pb > rest {
                break;
            }
            let mut e = 0;
            loop {
                let (q, r) = rest.div_rem(&pb);
                if !r.is_zero() {
                    break;
                }
                rest = q;
                e += 1;
            }
            if e > 0 {
                record(&mut report.factors, pb.clone(), e, Method::TrialDivision);
                report.steps.push(Step {
                    method: Method::TrialDivision,
                    digits: decimal_digits(n),
                    input: n.clone(),
                    found: Some(pb),
                    seconds: secs(t),
                });
            }
        }
        let mut pending = Vec::new();
        if !rest.is_one() {
            let first = if report.factors.is_empty() {
                Method::Primality
            } else {
                Method::TrialDivision
            };
            pending.push(PendingPiece {
                n: rest,
                multiplicity: 1,
                method: first,
            });
        }
        FactorState {
            schema_version: 1,
            generation: 0,
            report,
            pending,
            active: None,
            seed: options.seed,
            elapsed_seconds: 0.0,
        }
    };
    let previous_elapsed = state.elapsed_seconds;
    let persist = |state: &mut FactorState| -> Result<(), String> {
        state.generation = state
            .generation
            .checked_add(1)
            .ok_or("factor checkpoint generation overflow")?;
        state.elapsed_seconds = previous_elapsed + secs(t0);
        state.report.total_seconds = state.elapsed_seconds;
        if let Some(callback) = save {
            callback(state)?;
        }
        Ok(())
    };
    persist(&mut state)?;
    while state.active.is_some() || !state.pending.is_empty() {
        if state.active.is_none() {
            state.active = state.pending.pop().map(|piece| ActivePiece {
                piece,
                next_method: 0,
                attempt_seed: None,
                attempt_method: None,
                ecm_next_curve: 0,
            });
            persist(&mut state)?;
        }
        let active = state.active.as_ref().expect("active piece");
        let m = active.piece.n.clone();
        let mult = active.piece.multiplicity;
        let how = active.piece.method;
        if m.is_one() {
            state.active = None;
            persist(&mut state)?;
            continue;
        }
        if is_probable_prime(&m) {
            record(&mut state.report.factors, m, mult, how);
            state.active = None;
            persist(&mut state)?;
            continue;
        }
        if let Some((r, k)) = perfect_power(&m) {
            state.report.steps.push(Step {
                method: Method::PerfectPower,
                digits: decimal_digits(&m),
                input: m.clone(),
                found: Some(r.clone()),
                seconds: 0.0,
            });
            state.pending.push(PendingPiece {
                n: r,
                multiplicity: mult * k,
                method: Method::PerfectPower,
            });
            state.active = None;
            persist(&mut state)?;
            continue;
        }
        let digits = decimal_digits(&m);
        let mut ladder = vec![Method::Rho];
        if options.pm1.b1 > 0 {
            ladder.push(Method::PMinus1);
        }
        if options.pp1.is_some() {
            ladder.push(Method::PPlus1);
        }
        if options.ecm_curves_per_level > 0 && digits >= options.ecm_min_digits {
            ladder.push(Method::Ecm);
        }
        let snfs_ok = options
            .snfs_form
            .as_ref()
            .is_some_and(|f| digits >= options.snfs_min_digits && snfs_applies(f, &m));
        if snfs_ok {
            ladder.push(Method::Snfs);
        }
        if options.prefer_nfs && digits >= options.nfs_min_digits {
            ladder.push(Method::Gnfs);
        } else if digits <= options.qs_max_digits {
            ladder.push(Method::Qs);
        } else {
            ladder.push(Method::Gnfs);
        }
        while state.active.as_ref().expect("active piece").next_method < ladder.len() {
            let index = state.active.as_ref().expect("active piece").next_method;
            let method = ladder[index];
            let t = Instant::now();
            let seed = if let Some(seed) = state.active.as_ref().expect("active piece").attempt_seed
            {
                seed
            } else {
                state.seed = state.seed.wrapping_add(1000);
                let seed = state.seed;
                let active = state.active.as_mut().expect("active piece");
                active.attempt_seed = Some(seed);
                active.attempt_method = Some(method);
                persist(&mut state)?;
                seed
            };
            let checkpoint_path = checkpoint_dir.and_then(|dir| match method {
                Method::Qs | Method::Gnfs | Method::Snfs => {
                    let key = blake3::hash(format!("{m}:{method:?}:{seed}").as_bytes());
                    Some(dir.join(format!(
                        "factor-{}-{}.ckpt",
                        format!("{method:?}").to_lowercase(),
                        &key.to_hex()[..16]
                    )))
                }
                _ => None,
            });
            let g = if method == Method::Ecm {
                let per_level = options.ecm_curves_per_level;
                let target = (options.ecm_b1_levels.len() as u64)
                    .checked_mul(per_level)
                    .ok_or("ECM curve budget overflows u64")?;
                let mut found = None;
                while state.active.as_ref().expect("active piece").ecm_next_curve < target {
                    let index = state.active.as_ref().expect("active piece").ecm_next_curve;
                    let b1 = options.ecm_b1_levels[(index / per_level) as usize];
                    let curve_seed = seed.wrapping_add(index);
                    if let EcmResult::Found(candidate) = ecm_one_curve(&m, b1, curve_seed) {
                        let (q, rem) = m.div_rem(&candidate);
                        if rem.is_zero()
                            && !candidate.is_one()
                            && candidate != m
                            && &candidate * &q == m
                        {
                            found = Some(candidate);
                            break;
                        }
                    }
                    state.active.as_mut().expect("active piece").ecm_next_curve += 1;
                    persist(&mut state)?;
                    if let Some(callback) = progress {
                        callback(&super::Progress {
                            stage: "ecm",
                            done: index + 1,
                            target,
                            seconds: previous_elapsed + secs(t0),
                        });
                    }
                }
                found
            } else {
                try_method(method, &m, options, seed, progress, checkpoint_path)?
            };
            state.report.steps.push(Step {
                method,
                digits,
                input: m.clone(),
                found: g.clone(),
                seconds: secs(t),
            });
            if let Some(g) = g {
                let q = &m / &g;
                state.pending.push(PendingPiece {
                    n: g,
                    multiplicity: mult,
                    method,
                });
                state.pending.push(PendingPiece {
                    n: q,
                    multiplicity: mult,
                    method,
                });
                state.active = None;
                persist(&mut state)?;
                break;
            }
            let active = state.active.as_mut().expect("active piece");
            active.next_method += 1;
            active.attempt_seed = None;
            active.attempt_method = None;
            active.ecm_next_curve = 0;
            persist(&mut state)?;
        }
        if state.active.is_some() {
            state.report.unfactored.push((m.to_str_radix(10), mult));
            state.active = None;
            persist(&mut state)?;
        }
    }
    state.report.factors.sort_by(|a, b| a.prime.cmp(&b.prime));
    state.report.complete = state.report.unfactored.is_empty();
    let mut prod = BigUint::one();
    for f in &state.report.factors {
        prod *= num_traits::pow(f.prime.clone(), f.exponent as usize);
    }
    for (u, e) in &state.report.unfactored {
        let u: BigUint = u.parse().unwrap_or_default();
        prod *= num_traits::pow(u, *e as usize);
    }
    state.report.verified = &prod == n
        && state
            .report
            .factors
            .iter()
            .all(|f| is_probable_prime(&f.prime));
    persist(&mut state)?;
    Ok(state.report)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::RefCell;

    fn check(n: &BigUint, want: &[(&str, u32)]) -> FactorReport {
        let r = factor(n, &FactorOptions::default());
        assert!(r.complete && r.verified, "{r:?}");
        let got: Vec<(String, u32)> = r
            .factors
            .iter()
            .map(|f| (f.prime.to_string(), f.exponent))
            .collect();
        let want: Vec<(String, u32)> = want.iter().map(|&(p, e)| (p.to_string(), e)).collect();
        assert_eq!(got, want);
        r
    }

    #[test]
    fn small_numbers() {
        check(&BigUint::from(1u32), &[]);
        check(&BigUint::from(2u32), &[("2", 1)]);
        check(&BigUint::from(360u32), &[("2", 3), ("3", 2), ("5", 1)]);
        check(&BigUint::from(1_000_003u32), &[("1000003", 1)]);
    }

    #[test]
    fn ladder_resume_keeps_completed_method_attempts() {
        let n = BigUint::from(1_000_003u64) * BigUint::from(1_000_033u64);
        let options = FactorOptions::default();
        let expected = factor(&n, &options);
        let saved = RefCell::new(None);
        let stop_after_split = |state: &FactorState| -> Result<(), String> {
            *saved.borrow_mut() = Some(state.clone());
            if !state.report.steps.is_empty() && !state.pending.is_empty() {
                return Err("interrupt after completed method".into());
            }
            Ok(())
        };
        assert_eq!(
            factor_with_state(&n, &options, None, None, None, Some(&stop_after_split)).unwrap_err(),
            "interrupt after completed method"
        );
        let resumed =
            factor_with_state(&n, &options, None, saved.into_inner(), None, None).unwrap();
        assert_eq!(
            serde_json::to_value(&resumed.factors).unwrap(),
            serde_json::to_value(&expected.factors).unwrap()
        );
        assert_eq!(resumed.steps.len(), expected.steps.len());
        assert!(resumed.complete && resumed.verified);
    }

    #[test]
    fn ladder_resume_continues_after_completed_ecm_curves() {
        let n = BigUint::from(1_000_000_007u64) * BigUint::from(1_000_000_009u64);
        let mut options = FactorOptions::default();
        options.trial_bound = 2;
        options.rho.max_iterations = 1;
        options.rho.attempts = 1;
        options.pm1.b1 = 0;
        options.ecm_min_digits = 0;
        options.ecm_b1_levels = vec![2];
        options.ecm_curves_per_level = 4;
        let expected = factor(&n, &options);
        let saved = RefCell::new(None);
        let interrupt = |state: &FactorState| -> Result<(), String> {
            if state.active.as_ref().is_some_and(|active| {
                active.attempt_method == Some(Method::Ecm) && active.ecm_next_curve == 2
            }) {
                *saved.borrow_mut() = Some(state.clone());
                return Err("interrupt after ECM curve 2".into());
            }
            Ok(())
        };
        assert_eq!(
            factor_with_state(&n, &options, None, None, None, Some(&interrupt)).unwrap_err(),
            "interrupt after ECM curve 2"
        );
        let state = saved.into_inner().unwrap();
        assert_eq!(state.active.as_ref().unwrap().ecm_next_curve, 2);
        let resumed = factor_with_state(&n, &options, None, Some(state), None, None).unwrap();
        assert_eq!(
            serde_json::to_value(&resumed.factors).unwrap(),
            serde_json::to_value(&expected.factors).unwrap()
        );
        assert_eq!(resumed.steps.len(), expected.steps.len());
        assert!(resumed.complete && resumed.verified);
    }

    #[test]
    fn ladder_rejects_damaged_inner_sieve_checkpoint() {
        let n = BigUint::from(1_000_003u64) * BigUint::from(1_000_033u64);
        let mut options = FactorOptions::default();
        options.trial_bound = 2;
        options.rho.max_iterations = 1;
        options.rho.attempts = 1;
        options.pm1.b1 = 0;
        options.ecm_curves_per_level = 0;
        let unique = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let dir =
            std::env::temp_dir().join(format!("crax-factor-sieve-{}-{unique}", std::process::id()));
        std::fs::create_dir(&dir).unwrap();
        let key = blake3::hash(format!("{n}:Qs:2001").as_bytes());
        let path = dir.join(format!("factor-qs-{}.ckpt", &key.to_hex()[..16]));
        std::fs::write(&path, b"broken checkpoint").unwrap();
        let error = factor_with_state(&n, &options, None, None, Some(&dir), None).unwrap_err();
        assert!(error.contains("checkpoint"), "{error}");
        std::fs::remove_file(path).unwrap();
        std::fs::remove_dir(dir).unwrap();
    }

    #[test]
    fn ladder_resumes_from_saved_inner_siqs_batch() {
        let n = BigUint::from(1_000_003u64) * BigUint::from(1_000_033u64);
        let mut options = FactorOptions::default();
        options.trial_bound = 2;
        options.rho.max_iterations = 1;
        options.rho.attempts = 1;
        options.pm1.b1 = 0;
        options.ecm_curves_per_level = 0;
        options.qs.checkpoint_every_secs = 0;
        let expected = factor(&n, &options);
        let unique = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let dir =
            std::env::temp_dir().join(format!("crax-factor-siqs-{}-{unique}", std::process::id()));
        std::fs::create_dir(&dir).unwrap();
        let saved = RefCell::new(None);
        let save = |state: &FactorState| -> Result<(), String> {
            *saved.borrow_mut() = Some(state.clone());
            Ok(())
        };
        let interrupt = |progress: &super::super::Progress| {
            if progress.stage == "sieve" {
                panic!("interrupt after SIQS batch");
            }
        };
        let stopped = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            factor_with_state(
                &n,
                &options,
                Some(&interrupt),
                None,
                Some(&dir),
                Some(&save),
            )
        }));
        assert!(stopped.is_err());
        let state = saved.into_inner().unwrap();
        assert_eq!(
            state.active.as_ref().unwrap().attempt_method,
            Some(Method::Qs)
        );
        let checkpoint = std::fs::read_dir(&dir)
            .unwrap()
            .map(|entry| entry.unwrap().path())
            .find(|path| path.extension().is_some_and(|ext| ext == "ckpt"))
            .unwrap();
        let resumed = factor_with_state(&n, &options, None, Some(state), Some(&dir), None).unwrap();
        assert_eq!(
            serde_json::to_value(&resumed.factors).unwrap(),
            serde_json::to_value(&expected.factors).unwrap()
        );
        assert_eq!(resumed.steps.len(), expected.steps.len());
        assert!(resumed.complete && resumed.verified);
        std::fs::remove_file(checkpoint).unwrap();
        std::fs::remove_dir(dir).unwrap();
    }

    #[test]
    fn mixed_methods() {
        // 2^3 · 1000003^2 · (a 20-digit semiprime) → trial, perfect power
        // is not needed, rho / QS for the rest.
        let n = BigUint::from(8u32)
            * BigUint::from(1_000_003u64 * 1_000_003u64)
            * BigUint::from(3_267_000_013u64)
            * BigUint::from(10_000_000_019u64);
        let r = check(
            &n,
            &[
                ("2", 3),
                ("1000003", 2),
                ("3267000013", 1),
                ("10000000019", 1),
            ],
        );
        assert!(r.factors.iter().all(|f| f.proven));
    }

    #[test]
    fn perfect_power_of_large_prime() {
        let p: BigUint = "1000000000000000000000007".parse().unwrap();
        let n = num_traits::pow(p.clone(), 3);
        let r = check(&n, &[("1000000000000000000000007", 3)]);
        assert_eq!(r.factors[0].method, Method::PerfectPower);
    }

    #[test]
    fn semiprime_goes_to_qs() {
        let p: BigUint = "100000000000000003".parse().unwrap();
        let q: BigUint = "1000000000000000000000007".parse().unwrap();
        let r = check(
            &(&p * &q),
            &[("100000000000000003", 1), ("1000000000000000000000007", 1)],
        );
        assert!(r.factors.iter().all(|f| f.method == Method::Qs));
    }

    #[test]
    fn snfs_form_is_used() {
        // F7 = 2^128 + 1: rho/p−1 fail, the SNFS form applies.
        let n = (BigUint::one() << 128) + 1u32;
        let options = FactorOptions {
            snfs_form: Some(SnfsInput::Form {
                r: 2,
                e: 128,
                s: 1,
                c: 1,
            }),
            snfs_min_digits: 30,
            ..Default::default()
        };
        let r = factor(&n, &options);
        assert!(r.complete && r.verified);
        assert_eq!(r.factors.len(), 2);
        assert!(r.factors.iter().all(|f| f.method == Method::Snfs));
    }
}
