//! Existing native F4 plus bounded triangular substitution. Never call
//! f4_fp::solve here: its small-prime root finder scans the entire field.
use super::poly::{mul, pow};
use super::{verify_leaves_with_work, System};
use cryptanalysis_suite::cryptanalysis::f4_fp::{self, F4Options, Ordering, Poly};
use cryptanalysis_suite::cryptanalysis::factoring::nfs::poly::fp;
use num_bigint::BigUint;
use serde::Serialize;
use serde_json::{json, Value};
use std::time::{Duration, Instant};

#[derive(Clone, Copy, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Schedule {
    Global,
    Staged,
}
impl Schedule {
    pub fn parse(s: &str) -> Result<Self, String> {
        match s {
            "global" => Ok(Self::Global),
            "staged" => Ok(Self::Staged),
            _ => Err("schedule must be global or staged".into()),
        }
    }
}
fn trim(mut f: Vec<u64>) -> Vec<u64> {
    while f.last() == Some(&0) {
        f.pop();
    }
    f
}

fn roots(coeff: &[u64], p: u64, deadline: Instant, steps: &mut u64) -> Result<Vec<u64>, String> {
    fn split(
        g: Vec<u64>,
        p: u64,
        deadline: Instant,
        steps: &mut u64,
        out: &mut Vec<u64>,
    ) -> Result<(), String> {
        let g = trim(g);
        if g.len() <= 1 {
            return Ok(());
        }
        if g.len() == 2 {
            out.push(mul((p - g[0]) % p, pow(g[1], p - 2, p), p));
            return Ok(());
        }
        for delta in 0..64 {
            if Instant::now() > deadline {
                return Err("recovery_deadline".into());
            }
            *steps += 1;
            let h = fp::powmod(&[delta, 1], &BigUint::from((p - 1) / 2), &g, p);
            let d = fp::gcd(&g, &fp::sub(&h, &[1], p), p);
            if d.len() > 1 && d.len() < g.len() {
                let (q, rem) = fp::divrem(&g, &d, p);
                if !rem.is_empty() {
                    return Err("factor_exact_division_failed".into());
                }
                split(d, p, deadline, steps, out)?;
                return split(q, p, deadline, steps, out);
            }
        }
        Err("root_split_shift_cap".into())
    }
    let f = trim(coeff.to_vec());
    if f.len() <= 1 {
        return Ok(vec![]);
    }
    if f.len() > 65 {
        return Err("root_degree_cap".into());
    }
    if Instant::now() > deadline {
        return Err("recovery_deadline".into());
    }
    let xp = fp::powmod(&[0, 1], &BigUint::from(p), &f, p);
    let g = fp::gcd(&f, &fp::sub(&xp, &[0, 1], p), p);
    let mut out = Vec::new();
    split(g, p, deadline, steps, &mut out)?;
    out.sort_unstable();
    out.dedup();
    Ok(out)
}
fn substitute(polys: &[Poly], assignment: &[Option<u64>], p: u64) -> Vec<Poly> {
    polys
        .iter()
        .map(|f| {
            let terms: Vec<_> = f
                .iter()
                .map(|(e, c)| {
                    let mut exp = e.clone();
                    let mut coeff = *c;
                    for (i, &a) in assignment.iter().enumerate() {
                        if let Some(x) = a {
                            coeff = mul(coeff, pow(x, exp[i] as u64, p), p);
                            exp[i] = 0;
                        }
                    }
                    (exp, coeff)
                })
                .collect();
            f4_fp::normalise(&terms, p, Ordering::Grevlex)
        })
        .filter(|f| !f.is_empty())
        .collect()
}
#[derive(Default)]
struct Recovery {
    nodes: u64,
    root_split_steps: u64,
    finite_domain_branches: u64,
    solutions: Vec<Vec<u64>>,
    incomplete: Option<String>,
}
impl Recovery {
    fn walk(
        &mut self,
        polys: &[Poly],
        original: &[Poly],
        assignment: &mut [Option<u64>],
        domains: &[Option<Vec<u64>>],
        p: u64,
        deadline: Instant,
    ) {
        if self.nodes >= 4096 || self.solutions.len() >= 256 {
            self.incomplete = Some("recovery_node_or_solution_cap".into());
            return;
        }
        if Instant::now() > deadline {
            self.incomplete = Some("recovery_deadline".into());
            return;
        }
        self.nodes += 1;
        let residual = substitute(polys, assignment, p);
        if residual
            .iter()
            .any(|f| f.iter().all(|(e, _)| e.iter().all(|&v| v == 0)))
        {
            return;
        }
        if assignment.iter().all(Option::is_some) {
            let x: Vec<_> = assignment.iter().map(|a| a.unwrap()).collect();
            if original.iter().all(|f| f4_fp::eval(f, &x, p) == 0) {
                self.solutions.push(x);
            }
            return;
        }
        let mut candidate: Option<(usize, Vec<u64>)> = None;
        for f in &residual {
            let variables: Vec<_> = (0..assignment.len())
                .filter(|&i| f.iter().any(|(e, _)| e[i] != 0))
                .collect();
            if variables.len() != 1 {
                continue;
            }
            let i = variables[0];
            let degree = f.iter().map(|(e, _)| e[i]).max().unwrap() as usize;
            if degree > 64 {
                continue;
            }
            let mut coeff = vec![0; degree + 1];
            for (e, c) in f {
                coeff[e[i] as usize] = *c;
            }
            let values = if let Some(domain) = &domains[i] {
                domain
                    .iter()
                    .copied()
                    .filter(|&x| {
                        let mut acc = 0;
                        for &c in coeff.iter().rev() {
                            acc = (mul(acc, x, p) + c) % p;
                        }
                        acc == 0
                    })
                    .collect()
            } else {
                match roots(&coeff, p, deadline, &mut self.root_split_steps) {
                    Ok(r) => r,
                    Err(reason) => {
                        self.incomplete = Some(reason);
                        return;
                    }
                }
            };
            if values.is_empty() {
                return;
            }
            if candidate
                .as_ref()
                .is_none_or(|(_, v)| values.len() < v.len())
            {
                candidate = Some((i, values));
            }
        }
        if candidate.is_none() {
            candidate = domains
                .iter()
                .enumerate()
                .filter(|(i, d)| assignment[*i].is_none() && d.is_some())
                .map(|(i, d)| (i, d.clone().unwrap()))
                .min_by_key(|(_, d)| d.len());
            if candidate.is_some() {
                self.finite_domain_branches += 1;
            }
        }
        let Some((i, values)) = candidate else {
            self.incomplete = Some("nontriangular_unbounded_variable".into());
            return;
        };
        for value in values {
            assignment[i] = Some(value);
            self.walk(&residual, original, assignment, domains, p, deadline);
            assignment[i] = None;
            if self.nodes >= 4096 || Instant::now() > deadline {
                break;
            }
        }
    }
}

pub fn run(system: &System, schedule: Schedule, budget: Duration, max_degree: u32) -> Value {
    let started = Instant::now();
    let deadline = started + budget;
    run_core(system, schedule, started, deadline, budget, max_degree)
}

pub(super) fn run_until(
    system: &System,
    schedule: Schedule,
    deadline: Instant,
    max_degree: u32,
) -> Value {
    let started = Instant::now();
    run_core(
        system,
        schedule,
        started,
        deadline,
        deadline.saturating_duration_since(started),
        max_degree,
    )
}

fn run_core(
    system: &System,
    schedule: Schedule,
    started: Instant,
    deadline: Instant,
    budget: Duration,
    max_degree: u32,
) -> Value {
    let p = system.input.p;
    let n = system.names.len();
    let original: Vec<Poly> = system.blocks.iter().flatten().cloned().collect();
    let batches: Vec<Vec<Poly>> = match schedule {
        Schedule::Global => vec![original.clone()],
        Schedule::Staged => system.blocks.clone(),
    };
    let mut accumulated = Vec::new();
    let mut basis = Vec::new();
    let mut reports = Vec::new();
    let mut timed_out = false;
    let mut inconsistent = false;
    let mut truncated = false;
    for block in batches {
        if Instant::now() > deadline {
            timed_out = true;
            break;
        }
        accumulated.extend(block);
        let mut input = accumulated.clone();
        input.extend(basis);
        let options = F4Options {
            order: Ordering::Grevlex,
            max_degree,
            deadline: Some(deadline),
            stop_staircase: None,
        };
        let report = f4_fp::f4(&input, n, p, &options);
        timed_out |= report.timed_out;
        inconsistent = report.inconsistent;
        truncated |= report.pairs_above_bound > 0;
        reports.push(json!({"degree_reached":report.degree_reached,"solving_degree_max":report.solving_degree_max,"last_productive_degree":report.solving_degree,"steps":report.steps,"max_rows":report.max_rows,"max_cols":report.max_cols,"basis_size":report.basis.len(),"pairs_above_bound":report.pairs_above_bound,"timed_out":report.timed_out,"inconsistent":report.inconsistent,"engine_ms":report.ms}));
        basis = report.basis;
        if timed_out || inconsistent {
            break;
        }
    }
    let f4_ns = started.elapsed().as_nanos();
    let recovery_started = Instant::now();
    let mut recovery = Recovery::default();
    if !timed_out && !inconsistent {
        let mut polynomials = original.clone();
        polynomials.extend(basis);
        recovery.walk(
            &polynomials,
            &original,
            &mut vec![None; n],
            &system.domains,
            p,
            deadline,
        );
    }
    let root_recovery_ns = recovery_started.elapsed().as_nanos();
    let validation_started = Instant::now();
    let mut validation_group_additions = 0u64;
    let mut verified = Vec::new();
    let mut rejected = 0;
    for assignment in &recovery.solutions {
        let xs = &assignment[..system.m];
        let (signs, adds) = verify_leaves_with_work(&system.input, xs);
        validation_group_additions += adds;
        if let Some(signs) = signs {
            verified.push(json!({"x":xs,"signs":signs,"assignment":assignment}));
        } else {
            rejected += 1;
        }
    }
    let independent_group_validation_ns = validation_started.elapsed().as_nanos();
    let status = if !verified.is_empty() {
        "verified_witnesses_via_f4_and_bounded_substitution"
    } else if timed_out {
        "engine_timeout"
    } else if inconsistent {
        "refuted_encoded_system_only"
    } else if recovery.incomplete.is_some() {
        "recovery_undetermined"
    } else if truncated {
        "degree_truncated_no_verified_witness"
    } else {
        "encoded_system_no_rational_group_witness"
    };
    json!({"schema":"m31-relation-encodings/v1","producer_only":true,"input":system.input,"m":system.m,"encoding":system.encoding,"schedule":schedule,"scope":system.scope,
        "solver":"native f4_fp::f4 + bounded triangular substitution; no p-sized scan","ordering":"grevlex","max_degree":max_degree,"engine_budget_ms":budget.as_millis(),"root_split_schedule":"deterministic shifts0..63; no random seed", "recovery_node_cap":4096,"recovery_solution_cap":256,"construction_term_cap":50000,"leaf_quotient_reduction":true,
        "n_variables":n,"n_equations":original.len(),"input_terms":original.iter().map(Vec::len).sum::<usize>(),"input_max_degree":system.degrees.iter().max(),"variables":system.names,"construction_ns":system.construction_ns,"f4_ns":f4_ns,"root_recovery_ns":root_recovery_ns,"independent_group_validation_ns":independent_group_validation_ns,"validation_group_additions":validation_group_additions,"solve_and_recovery_ns":started.elapsed().as_nanos(),"stages":reports,"status":status,"degree_truncated":truncated,
        "recovery":{"nodes":recovery.nodes,"finite_domain_fallback_branches":recovery.finite_domain_branches,"root_split_steps":recovery.root_split_steps,"incomplete":recovery.incomplete,"polynomial_assignments":recovery.solutions.len(),"group_rejected":rejected},"verified":verified})
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn bounded_native_factor_splitter_checks_m31_roots() {
        let p = 2147483647;
        let mut f = vec![1];
        for root in [1, 2, 19] {
            f = fp::mul(&f, &[(p - root) % p, 1], p);
        }
        let mut steps = 0;
        assert_eq!(
            roots(&f, p, Instant::now() + Duration::from_secs(2), &mut steps).unwrap(),
            vec![1, 2, 19]
        );
        assert!(steps <= 3 * 64);
    }
}
