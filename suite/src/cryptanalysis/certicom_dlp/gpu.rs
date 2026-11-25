//! GPU point batches and parallel Floyd walks; collision solving and final
//! verification remain on the CPU. CUDA, Metal and emulation use the same wire.
use std::collections::HashMap;

use num_bigint::{BigUint, RandBigInt};
use num_traits::{One, ToPrimitive, Zero};
use rand::{rngs::StdRng, SeedableRng};

use super::worker::{big, decode_point, integer, point, DeviceWorker};
use super::{ChallengeGroup, ChallengePoint, SolveReport, SolverOptions};

pub fn bsgs_on_device(
    group: &ChallengeGroup,
    target: &ChallengePoint,
    lo: &BigUint,
    width: &BigUint,
    opts: &SolverOptions,
    worker: &mut DeviceWorker,
) -> Result<SolveReport, String> {
    worker.ensure_active()?;
    group.validate(target)?;
    worker.check_binding(group, target)?;
    if width.is_zero() || lo >= group.order() || lo + width > *group.order() {
        return Err("BSGS requires a nonempty interval contained in [0,n)".into());
    }
    if opts.max_table_entries == 0 {
        return Err("BSGS needs at least one baby-table entry".into());
    }
    let mut report = SolveReport::pending(group, "bsgs");
    if opts.max_iterations == 0 {
        report.reason = Some("BSGS giant-step budget is zero".into());
        return worker.finish(report);
    }
    let root = width.sqrt();
    let m = (if &root * &root < *width {
        root + BigUint::one()
    } else {
        root
    })
    .min(BigUint::from(opts.max_table_entries))
    .to_usize()
    .ok_or("baby-table size does not fit this host")?;
    let mut table = HashMap::new();
    table
        .try_reserve(m)
        .map_err(|e| format!("cannot allocate baby table: {e}"))?;
    let generator = group.generator();
    for start in (0..m).step_by(worker.batch_size()) {
        let end = m.min(start + worker.batch_size());
        let requests: Vec<_> = (start..end)
            .map(|j| (generator.clone(), BigUint::from(j)))
            .collect();
        for (j, baby) in (start..end).zip(worker.mul(group, &requests)?) {
            worker.ensure_active()?;
            table.insert(group.key(&baby), j);
        }
    }
    report.table_entries = table.len();
    let stride = BigUint::from(m);
    let mut offset = BigUint::zero();
    let mut giants = 0u64;
    while giants < opts.max_iterations && offset < *width {
        let cap = worker
            .batch_size()
            .min((opts.max_iterations - giants).min(4096) as usize);
        let needed = ((width - &offset + &stride - BigUint::one()) / &stride)
            .to_usize()
            .unwrap_or(cap);
        let count = cap.min(needed);
        let requests: Vec<_> = (0..count)
            .map(|i| {
                (
                    generator.clone(),
                    (lo + &offset + &stride * BigUint::from(i)) % group.order(),
                )
            })
            .collect();
        let pairs: Vec<_> = worker
            .mul(group, &requests)?
            .iter()
            .map(|p| (target.clone(), group.neg(p)))
            .collect();
        for (i, current) in worker.add(group, &pairs)?.iter().enumerate() {
            worker.ensure_active()?;
            if let Some(j) = table.get(&group.key(current)) {
                let candidate = &offset + &stride * BigUint::from(i) + BigUint::from(*j);
                if candidate < *width {
                    report.iterations = Some(giants + i as u64 + 1);
                    report.recover(group, target, lo + candidate)?;
                    return worker.finish(report);
                }
            }
        }
        giants += count as u64;
        offset += &stride * BigUint::from(count);
    }
    report.iterations = Some(giants);
    if offset >= *width {
        report.status = "interval_exhausted";
        report.reason = Some("target logarithm is outside the supplied interval".into());
    } else {
        report.reason = Some("BSGS giant-step budget exhausted".into());
    }
    worker.finish(report)
}

fn seed_states(
    group: &ChallengeGroup,
    target: &ChallengePoint,
    worker: &mut DeviceWorker,
    rng: &mut StdRng,
    count: usize,
    classical_start: bool,
) -> Result<Vec<[u32; 45]>, String> {
    let mut tags = Vec::with_capacity(count);
    let mut requests = Vec::with_capacity(2 * count);
    for i in 0..count {
        worker.ensure_active()?;
        let (a, b) = if classical_start && i == 0 {
            (BigUint::one(), BigUint::zero())
        } else {
            (
                rng.gen_biguint_below(group.order()),
                rng.gen_biguint_below(group.order()),
            )
        };
        requests.push((group.generator(), a.clone()));
        requests.push((target.clone(), b.clone()));
        tags.push((a, b));
    }
    let terms = worker.mul(group, &requests)?;
    let pairs: Vec<_> = terms
        .chunks(2)
        .map(|p| (p[0].clone(), p[1].clone()))
        .collect();
    worker
        .add(group, &pairs)?
        .iter()
        .zip(tags)
        .map(|(p, (a, b))| {
            let mut state = [0u32; 45];
            state[..11].copy_from_slice(&point(group, p));
            state[11..16].copy_from_slice(&integer(&a)?);
            state[16..21].copy_from_slice(&integer(&b)?);
            let initial: [u32; 21] = state[..21].try_into().unwrap();
            state[21..42].copy_from_slice(&initial);
            Ok(state)
        })
        .collect()
}

fn iterations(state: &[u32; 45]) -> u64 {
    u64::from(state[42]) | (u64::from(state[43]) << 32)
}

pub fn rho_on_device(
    group: &ChallengeGroup,
    target: &ChallengePoint,
    opts: &SolverOptions,
    worker: &mut DeviceWorker,
) -> Result<SolveReport, String> {
    worker.ensure_active()?;
    group.validate(target)?;
    worker.check_binding(group, target)?;
    let mut report = SolveReport::pending(group, "rho");
    if *target == group.identity() {
        report.recover(group, target, BigUint::zero())?;
        return worker.finish(report);
    }
    if opts.max_iterations == 0 {
        report.reason = Some("rho iteration budget is zero".into());
        return worker.finish(report);
    }
    let mut rng = StdRng::seed_from_u64(opts.seed);
    let walks = worker.rho_walks;
    let mut states = seed_states(group, target, worker, &mut rng, walks, true)?;
    let mut restarts = vec![0u32; states.len()];
    let mut active = vec![true; states.len()];
    let mut total = 0u64;
    loop {
        let ids: Vec<_> = (0..states.len()).filter(|i| active[*i]).collect();
        if ids.is_empty() {
            break;
        }
        let steps = ids
            .iter()
            .map(|i| opts.max_iterations - iterations(&states[*i]))
            .min()
            .unwrap()
            .min(64) as u32;
        if steps == 0 {
            return Err("invalid active rho budget".into());
        }
        let input: Vec<_> = ids.iter().map(|i| states[*i]).collect();
        let output = worker.rho(&input, steps)?;
        // Account for every lane already executed, including speculative work
        // after another lane's eventual successful collision.
        for ((id, old), new) in ids.iter().zip(&input).zip(&output) {
            worker.ensure_active()?;
            let delta = iterations(new)
                .checked_sub(iterations(old))
                .ok_or("GPU rho counter regressed")?;
            if new[44] > 1
                || delta == 0
                || delta > u64::from(steps)
                || (new[44] == 0 && delta != u64::from(steps))
            {
                return Err("invalid GPU rho work or collision counters".into());
            }
            for range in [11..16, 16..21, 32..37, 37..42] {
                if big(&new[range]) >= *group.order() {
                    return Err("GPU rho scalar tag out of range".into());
                }
            }
            let t = decode_point(group, &new[..11])?;
            let h = decode_point(group, &new[21..32])?;
            if new[44] == 1 && t != h {
                return Err("GPU rho reported unequal collision points".into());
            }
            total = total
                .checked_add(delta)
                .ok_or("aggregate rho work counter overflow")?;
            states[*id] = *new;
        }
        worker.execution.device_rho_iterations = total;
        let mut reseed = Vec::new();
        for id in ids {
            worker.ensure_active()?;
            let state = &states[id];
            if state[44] == 1 {
                let n = group.order();
                let numerator = (big(&state[11..16]) + n - big(&state[32..37])) % n;
                let denominator = (big(&state[37..42]) + n - big(&state[16..21])) % n;
                if !denominator.is_zero() {
                    let inverse = crate::utils::mod_inverse(&denominator, n)
                        .ok_or("noninvertible GPU rho collision")?;
                    report.recover(group, target, numerator * inverse % n)?;
                    report.iterations = Some(total);
                    return worker.finish(report);
                }
                if !numerator.is_zero() {
                    return Err("inconsistent sterile GPU rho collision".into());
                }
                if restarts[id] < opts.max_restarts {
                    restarts[id] += 1;
                    reseed.push(id);
                } else {
                    active[id] = false;
                }
            } else if iterations(state) == opts.max_iterations {
                active[id] = false;
            }
        }
        if !reseed.is_empty() {
            let fresh = seed_states(group, target, worker, &mut rng, reseed.len(), false)?;
            for (id, state) in reseed.into_iter().zip(fresh) {
                states[id] = state;
            }
        }
    }
    report.iterations = Some(total);
    report.reason =
        Some("parallel rho exhausted per-walk iteration or sterile-restart budgets".into());
    worker.finish(report)
}
