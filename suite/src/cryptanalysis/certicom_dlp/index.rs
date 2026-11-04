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
    /// Summands per decomposition (`m`), 2 to 4.
    pub summands: u32,
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

struct PairEntry {
    sum: ChallengePoint,
    left: usize,
    left_negative: bool,
    right: usize,
    right_negative: bool,
}

struct Decomposer<'a> {
    group: &'a ChallengeGroup,
    base: &'a [ChallengePoint],
    lookup: HashMap<Option<(BigUint, BigUint)>, (usize, bool)>,
    /// Summands per decomposition (`m`): 2, 3 or 4.
    summands: u32,
    /// Pair sums used by the `m = 3` and `m = 4` meet-in-the-middle paths.
    pairs: Vec<PairEntry>,
    pair_index: HashMap<Option<(BigUint, BigUint)>, usize>,
}

impl<'a> Decomposer<'a> {
    fn new(
        group: &'a ChallengeGroup,
        base: &'a [ChallengePoint],
        summands: u32,
        max_table_entries: usize,
        deadline: Option<Instant>,
    ) -> Result<Self, String> {
        if !(2..=4).contains(&summands) {
            return Err(format!(
                "index-calculus decomposition supports m = 2, 3 or 4 summands, got {summands}"
            ));
        }
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

        let signed_count = 2 * base.len();
        let pair_budget = signed_count
            .checked_mul(signed_count + 1)
            .map(|v| v / 2)
            .ok_or("factor base is too large for a signed pair table")?;
        if summands >= 3 && pair_budget > max_table_entries {
            return Err(format!(
                "m = {summands} needs up to {pair_budget} signed pair sums, above max-table-entries {max_table_entries}"
            ));
        }

        let mut pairs = Vec::new();
        let mut pair_index = HashMap::new();
        if summands >= 3 {
            for left in 0..signed_count {
                check_deadline(deadline)?;
                let (left_index, left_negative, left_point) = signed_point(group, base, left);
                for right in left..signed_count {
                    check_deadline(deadline)?;
                    let (right_index, right_negative, right_point) =
                        signed_point(group, base, right);
                    let sum = group.add(&left_point, &right_point);
                    if sum == group.identity() {
                        continue;
                    }
                    let key = group.key(&sum);
                    if pair_index.contains_key(&key) {
                        continue;
                    }
                    pair_index.insert(key, pairs.len());
                    pairs.push(PairEntry {
                        sum,
                        left: left_index,
                        left_negative,
                        right: right_index,
                        right_negative,
                    });
                }
            }
            check_deadline(deadline)?;
        }

        Ok(Self {
            group,
            base,
            lookup,
            summands,
            pairs,
            pair_index,
        })
    }

    fn add_signed(&self, row: &mut [BigUint], index: usize, negative: bool, n: &BigUint) {
        let value = if negative {
            n - BigUint::one()
        } else {
            BigUint::one()
        };
        row[index] = (&row[index] + value) % n;
    }

    fn row(&self, target: &ChallengePoint) -> Option<Vec<BigUint>> {
        let n = self.group.order();
        if let Some(&(j, negative)) = self.lookup.get(&self.group.key(target)) {
            let mut row = vec![BigUint::zero(); self.base.len()];
            self.add_signed(&mut row, j, negative, n);
            return Some(row);
        }
        match self.summands {
            2 => {
                for left in 0..2 * self.base.len() {
                    let (i, neg_i, left_point) = signed_point(self.group, self.base, left);
                    let right = self.group.add(target, &self.group.neg(&left_point));
                    let Some(&(j, neg_j)) = self.lookup.get(&self.group.key(&right)) else {
                        continue;
                    };
                    let mut row = vec![BigUint::zero(); self.base.len()];
                    self.add_signed(&mut row, i, neg_i, n);
                    self.add_signed(&mut row, j, neg_j, n);
                    return Some(row);
                }
                None
            }
            3 => {
                for left in 0..2 * self.base.len() {
                    let (i, neg_i, left_point) = signed_point(self.group, self.base, left);
                    let rest = self.group.add(target, &self.group.neg(&left_point));
                    if rest == self.group.identity() {
                        continue;
                    }
                    let Some(&pair) = self.pair_index.get(&self.group.key(&rest)) else {
                        continue;
                    };
                    let pair = &self.pairs[pair];
                    let mut row = vec![BigUint::zero(); self.base.len()];
                    self.add_signed(&mut row, i, neg_i, n);
                    self.add_signed(&mut row, pair.left, pair.left_negative, n);
                    self.add_signed(&mut row, pair.right, pair.right_negative, n);
                    return Some(row);
                }
                None
            }
            4 => {
                for first in &self.pairs {
                    let rest = self
                        .group
                        .add(target, &self.group.neg(&first.sum));
                    if rest == self.group.identity() {
                        continue;
                    }
                    let Some(&second) = self.pair_index.get(&self.group.key(&rest)) else {
                        continue;
                    };
                    let second = &self.pairs[second];
                    let mut row = vec![BigUint::zero(); self.base.len()];
                    self.add_signed(&mut row, first.left, first.left_negative, n);
                    self.add_signed(&mut row, first.right, first.right_negative, n);
                    self.add_signed(&mut row, second.left, second.left_negative, n);
                    self.add_signed(&mut row, second.right, second.right_negative, n);
                    return Some(row);
                }
                None
            }
            _ => None,
        }
    }

    fn row_on_device(
        &self,
        target: &ChallengePoint,
        worker: &mut DeviceWorker,
    ) -> Result<Option<Vec<BigUint>>, String> {
        worker.ensure_active()?;
        if self.summands != 2 {
            return Ok(self.row(target));
        }
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

fn decomposition_name(summands: u32) -> &'static str {
    match summands {
        3 => "signed-three-summand-mitm",
        4 => "signed-four-summand-pair-mitm",
        _ => "signed-two-summand-mitm",
    }
}

fn signed_point(
    group: &ChallengeGroup,
    base: &[ChallengePoint],
    position: usize,
) -> (usize, bool, ChallengePoint) {
    let index = position / 2;
    let negative = position % 2 == 1;
    let point = if negative {
        group.neg(&base[index])
    } else {
        base[index].clone()
    };
    (index, negative, point)
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
    if !(2..=4).contains(&opts.summands) {
        return Err(format!(
            "index-calculus decomposition supports m = 2, 3 or 4 summands, got {}",
            opts.summands
        ));
    }
    let mut report = SolveReport::pending(group, "index-calculus");
    let mut stages = IndexReport {
        decomposition: decomposition_name(opts.summands),
        summands: opts.summands,
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
    let decomposer = Decomposer::new(
        group,
        &base,
        opts.summands,
        opts.max_table_entries,
        deadline,
    )?;
    report.table_entries = decomposer.lookup.len() + decomposer.pairs.len();
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
