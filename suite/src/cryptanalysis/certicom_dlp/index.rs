//! Factor-base construction, two-summand point decomposition, verified relation
//! collection, modular linear algebra and target descent on the exact group.
//! This native reference path uses the existing MITM oracle contract. It makes
//! no claim that a bounded run will solve a public 131-bit challenge.

use std::collections::HashMap;
use std::time::Instant;

use num_bigint::{BigUint, RandBigInt};
use num_traits::{One, Zero};
use rand::{rngs::StdRng, SeedableRng};
use serde::Serialize;

use super::worker::{check_deadline, DeviceWorker};
use super::{ChallengeGroup, ChallengePoint, Curve, SolveReport, SolverOptions};
use crate::binary_ecc::curve::BinaryPoint;
use crate::binary_ecc::F2mElement;
use crate::cryptanalysis::binary_semaev::solve_artin_schreier;
use crate::cryptanalysis::ec_index_calculus::{gaussian_eliminate_mod_n, sqrt_mod_p};
use crate::ecc::Point;

/// Public factor-base points and query scalars for externally prepared work.
/// No factor-base logarithms or target logarithm are accepted. Queries are
/// `[a]G`; their two-point decompositions supply the linear system modulo n.
/// Explicit schedules are also useful for constructed correctness fixtures.
#[derive(Clone, Debug)]
pub struct IndexInput {
    pub factor_base: Vec<ChallengePoint>,
    pub relation_queries: Vec<BigUint>,
    pub descent_shifts: Vec<BigUint>,
}

#[derive(Clone, Debug, Default, Serialize)]
pub struct IndexReport {
    pub factor_base_size: usize,
    pub factor_base_candidates: u64,
    pub factor_base_source: &'static str,
    pub decomposition: &'static str,
    pub relation_queries: u64,
    pub verified_relations: u64,
    pub trivial_relations: u64,
    pub dependent_relations: u64,
    pub rank: usize,
    pub factor_base_logs_verified: bool,
    pub descent_queries: u64,
    pub linear_algebra_backend: &'static str,
}

fn build_factor_base(
    group: &ChallengeGroup,
    opts: &SolverOptions,
    deadline: Option<Instant>,
) -> Result<(Vec<ChallengePoint>, u64), String> {
    let mut base = Vec::new();
    let mut seen = HashMap::new();
    let mut tried = 0;
    for xi in 1..=opts.max_base_candidates {
        check_deadline(deadline)?;
        tried += 1;
        let x = BigUint::from(xi);
        let point = match &group.curve {
            Curve::Prime(c) => {
                if x >= c.p {
                    break;
                }
                let rhs = ((&x * &x % &c.p) * &x + &c.a * &x + &c.b) % &c.p;
                sqrt_mod_p(&rhs, &c.p).map(|y| {
                    group.mul(
                        &ChallengePoint::Prime(Point::Affine {
                            x: c.fe(x),
                            y: c.fe(y),
                        }),
                        &BigUint::from(c.h),
                    )
                })
            }
            Curve::Binary(c) => {
                if x.bits() > c.m as u64 {
                    break;
                }
                let x = F2mElement::from_biguint(&x, c.m);
                let inv_x2 = x
                    .square(&c.irreducible)
                    .flt_inverse(&c.irreducible)
                    .ok_or("noninvertible binary abscissa")?;
                let rhs = x.add(&c.a).add(&c.b.mul(&inv_x2, &c.irreducible));
                solve_artin_schreier(&rhs, c.m, &c.irreducible).map(|z| {
                    group.mul(
                        &ChallengePoint::Binary(BinaryPoint::Affine {
                            y: x.mul(&z, &c.irreducible),
                            x,
                        }),
                        &c.cofactor,
                    )
                })
            }
        };
        let Some(point) = point else { continue };
        if point == group.identity() {
            continue;
        }
        group.validate(&point)?;
        if seen.contains_key(&group.key(&point))
            || seen.contains_key(&group.key(&group.neg(&point)))
        {
            continue;
        }
        seen.insert(group.key(&point), ());
        base.push(point);
        if base.len() == opts.factor_base_size {
            break;
        }
    }
    check_deadline(deadline)?;
    Ok((base, tried))
}

struct Decomposer<'a> {
    group: &'a ChallengeGroup,
    base: &'a [ChallengePoint],
    lookup: HashMap<Option<(BigUint, BigUint)>, (usize, bool)>,
}

impl<'a> Decomposer<'a> {
    fn new(
        group: &'a ChallengeGroup,
        base: &'a [ChallengePoint],
        deadline: Option<Instant>,
    ) -> Result<Self, String> {
        let mut lookup = HashMap::new();
        for (i, point) in base.iter().enumerate() {
            check_deadline(deadline)?;
            group.validate(point)?;
            if *point == group.identity() {
                return Err("factor base contains infinity".into());
            }
            for negative in [false, true] {
                let p = if negative {
                    group.neg(point)
                } else {
                    point.clone()
                };
                if lookup.insert(group.key(&p), (i, negative)).is_some() {
                    return Err("factor base has duplicate points or negation orbits".into());
                }
            }
        }
        check_deadline(deadline)?;
        Ok(Self {
            group,
            base,
            lookup,
        })
    }

    fn row(&self, target: &ChallengePoint) -> Option<Vec<BigUint>> {
        let n = self.group.order();
        let signed = |negative| {
            if negative {
                n - BigUint::one()
            } else {
                BigUint::one()
            }
        };
        if let Some(&(j, negative)) = self.lookup.get(&self.group.key(target)) {
            let mut row = vec![BigUint::zero(); self.base.len()];
            row[j] = signed(negative);
            return Some(row);
        }
        for (i, point) in self.base.iter().enumerate() {
            for neg_i in [false, true] {
                let left = if neg_i {
                    self.group.neg(point)
                } else {
                    point.clone()
                };
                let right = self.group.add(target, &self.group.neg(&left));
                if let Some(&(j, neg_j)) = self.lookup.get(&self.group.key(&right)) {
                    let right = if neg_j {
                        self.group.neg(&self.base[j])
                    } else {
                        self.base[j].clone()
                    };
                    if self.group.add(&left, &right) != *target {
                        continue;
                    }
                    let mut row = vec![BigUint::zero(); self.base.len()];
                    row[i] = signed(neg_i);
                    row[j] = (&row[j] + signed(neg_j)) % n;
                    return Some(row);
                }
            }
        }
        None
    }

    fn row_on_device(
        &self,
        target: &ChallengePoint,
        worker: &mut DeviceWorker,
    ) -> Result<Option<Vec<BigUint>>, String> {
        worker.ensure_active()?;
        if self.lookup.contains_key(&self.group.key(target)) {
            let row = self.row(target);
            worker.ensure_active()?;
            return Ok(row);
        }
        let mut lefts = Vec::with_capacity(2 * self.base.len());
        for p in self.base {
            worker.ensure_active()?;
            lefts.push(p.clone());
            lefts.push(self.group.neg(p));
        }
        let pairs: Vec<_> = lefts
            .iter()
            .map(|p| (target.clone(), self.group.neg(p)))
            .collect();
        let right_candidates = worker.add(self.group, &pairs)?;
        for (position, candidate) in right_candidates.iter().enumerate() {
            worker.ensure_active()?;
            let Some(&(j, negative)) = self.lookup.get(&self.group.key(candidate)) else {
                continue;
            };
            let right = if negative {
                self.group.neg(&self.base[j])
            } else {
                self.base[j].clone()
            };
            if self.group.add(&lefts[position], &right) != *target {
                return Err("device decomposition fails independent CPU point replay".into());
            }
            let n = self.group.order();
            let mut row = vec![BigUint::zero(); self.base.len()];
            row[position / 2] = if position % 2 == 0 {
                BigUint::one()
            } else {
                n - BigUint::one()
            };
            row[j] = (&row[j]
                + if negative {
                    n - BigUint::one()
                } else {
                    BigUint::one()
                })
                % n;
            worker.ensure_active()?;
            return Ok(Some(row));
        }
        worker.ensure_active()?;
        Ok(None)
    }
}

/// Run an actual IC pipeline on the named curve, using either cofactor-cleared
/// low-x points and uniform query scalars or explicit public preparation work.
/// The target is never passed to factor-base construction or log preparation.
pub fn index_calculus(
    group: &ChallengeGroup,
    target: &ChallengePoint,
    opts: &SolverOptions,
    input: Option<&IndexInput>,
) -> Result<SolveReport, String> {
    index_impl(group, target, opts, input, None)
}

/// GPU-assisted IC: point generation and signed-pair decomposition execute on
/// the selected device. Factor-base lifting, BigUint LA and replay stay on CPU.
pub fn index_calculus_on_device(
    group: &ChallengeGroup,
    target: &ChallengePoint,
    opts: &SolverOptions,
    input: Option<&IndexInput>,
    worker: &mut DeviceWorker,
) -> Result<SolveReport, String> {
    worker.check_binding(group, target)?;
    let report = index_impl(group, target, opts, input, Some(worker))?;
    let mut report = worker.finish(report)?;
    let note="Factor-base lifting, modular linear algebra and verification run on CPU; point generation and decomposition run on the selected backend";
    report.execution.note = Some(match report.execution.note {
        Some(previous) => format!("{previous}; {note}"),
        None => note.into(),
    });
    worker.ensure_active()?;
    Ok(report)
}

fn index_impl(
    group: &ChallengeGroup,
    target: &ChallengePoint,
    opts: &SolverOptions,
    input: Option<&IndexInput>,
    mut device: Option<&mut DeviceWorker>,
) -> Result<SolveReport, String> {
    let deadline = device.as_deref().map(DeviceWorker::deadline);
    check_deadline(deadline)?;
    group.validate(target)?;
    check_deadline(deadline)?;
    let mut report = SolveReport::pending(group, "index-calculus");
    let mut stages = IndexReport {
        decomposition: "signed-two-summand-mitm",
        linear_algebra_backend: "cpu-biguint",
        ..IndexReport::default()
    };
    if *target == group.identity() {
        report.recover(group, target, BigUint::zero())?;
        report.index_calculus = Some(stages);
        check_deadline(deadline)?;
        return Ok(report);
    }
    if opts.factor_base_size == 0 || opts.max_table_entries == 0 {
        return Err("index calculus requires a nonempty factor base and table budget".into());
    }
    if input.is_none()
        && (opts.factor_base_size > opts.max_table_entries / 2
            || opts
                .factor_base_size
                .checked_mul(opts.factor_base_size)
                .is_none_or(|cells| cells > opts.max_matrix_entries))
    {
        return Err("requested factor base exceeds its table or matrix budget".into());
    }
    let (base, candidates) = match input {
        Some(work) => {
            stages.factor_base_source = "external-public-points-and-queries";
            (work.factor_base.clone(), 0)
        }
        None => {
            stages.factor_base_source = "cofactor-cleared-low-x";
            build_factor_base(group, opts, deadline)?
        }
    };
    stages.factor_base_size = base.len();
    stages.factor_base_candidates = candidates;
    if base.is_empty() || base.len() > opts.max_table_entries / 2 {
        return Err("factor base is empty or exceeds the signed-point table budget".into());
    }
    if base
        .len()
        .checked_mul(base.len())
        .is_none_or(|cells| cells > opts.max_matrix_entries)
    {
        return Err("factor-base relation matrix exceeds the configured entry budget".into());
    }
    if input.is_none() && base.len() != opts.factor_base_size {
        report.reason = Some("factor-base candidate budget exhausted".into());
        report.index_calculus = Some(stages);
        check_deadline(deadline)?;
        return Ok(report);
    }
    let decomposer = Decomposer::new(group, &base, deadline)?;
    report.table_entries = decomposer.lookup.len();
    let n = group.order();
    let generator = group.generator();
    let mut rng = StdRng::seed_from_u64(opts.seed);
    let mut matrix: Vec<Vec<BigUint>> = Vec::new();
    let mut rhs: Vec<BigUint> = Vec::new();
    let mut logs = None;
    for trial in 0..opts.max_iterations {
        check_deadline(deadline)?;
        let a = match input {
            Some(work) => match work.relation_queries.get(trial as usize) {
                Some(a) => a % n,
                None => break,
            },
            None => rng.gen_biguint_below(n),
        };
        stages.relation_queries += 1;
        let query = if let Some(worker) = device.as_deref_mut() {
            worker
                .mul(group, &[(generator.clone(), a.clone())])?
                .remove(0)
        } else {
            group.mul(&generator, &a)
        };
        let row = if let Some(worker) = device.as_deref_mut() {
            decomposer.row_on_device(&query, worker)?
        } else {
            decomposer.row(&query)
        };
        let Some(row) = row else {
            continue;
        };
        if device.is_some() && group.mul(&generator, &a) != query {
            return Err("device relation query fails independent CPU scalar replay".into());
        }
        check_deadline(deadline)?;
        if row.iter().all(|v| v.is_zero()) {
            stages.trivial_relations += 1;
            continue;
        }
        stages.verified_relations += 1;
        let mut candidate_matrix = matrix.clone();
        let mut candidate_rhs = rhs.clone();
        candidate_matrix.push(row.clone());
        candidate_rhs.push(a.clone());
        let solution = gaussian_eliminate_mod_n(&mut candidate_matrix, &mut candidate_rhs, n);
        check_deadline(deadline)?;
        // Both existing native LA implementations reduce the entire matrix.
        // The older suite returns arbitrary free-variable values; require full
        // rank before accepting any of them as factor-base logarithms.
        let rank = candidate_matrix
            .iter()
            .filter(|row| row.iter().any(|v| !v.is_zero()))
            .count();
        if rank > stages.rank {
            matrix.push(row);
            rhs.push(a);
            stages.rank = rank;
        } else {
            stages.dependent_relations += 1;
        }
        if rank == base.len() {
            let values =
                solution.ok_or("full-rank verified relation system could not be solved")?;
            for (p, k) in base.iter().zip(&values) {
                check_deadline(deadline)?;
                if group.mul(&generator, k) != *p {
                    return Err("factor-base logs fail independent scalar replay".into());
                }
            }
            check_deadline(deadline)?;
            stages.factor_base_logs_verified = true;
            logs = Some(values);
            break;
        }
    }
    if let Some(logs) = logs {
        for trial in 0..opts.max_iterations {
            check_deadline(deadline)?;
            let a = match input {
                Some(work) => match work.descent_shifts.get(trial as usize) {
                    Some(a) => a % n,
                    None => break,
                },
                None => rng.gen_biguint_below(n),
            };
            stages.descent_queries += 1;
            let query = if let Some(worker) = device.as_deref_mut() {
                let shift = worker
                    .mul(group, &[(generator.clone(), a.clone())])?
                    .remove(0);
                worker.add(group, &[(target.clone(), shift)])?.remove(0)
            } else {
                group.add(target, &group.mul(&generator, &a))
            };
            let row = if let Some(worker) = device.as_deref_mut() {
                decomposer.row_on_device(&query, worker)?
            } else {
                decomposer.row(&query)
            };
            let Some(row) = row else {
                continue;
            };
            let sum = row
                .iter()
                .zip(&logs)
                .fold(BigUint::zero(), |s, (c, k)| (s + c * k) % n);
            report.recover(group, target, (sum + n - a) % n)?;
            check_deadline(deadline)?;
            break;
        }
        if !report.verified {
            report.reason = Some("target-descent query budget exhausted".into());
        }
    } else {
        report.reason = Some("relation query budget exhausted before full factor-base rank".into());
    }
    report.index_calculus = Some(stages);
    check_deadline(deadline)?;
    Ok(report)
}
