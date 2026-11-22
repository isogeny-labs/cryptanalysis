//! Published Hess-baseline parameter certificates, not new weak-curve claims.
//!
//! This example is deliberately separate from the frozen search engine. It
//! constructs one split-pole witness and checks it with two field algorithms.
use anyhow::{ensure, Context, Result};
use clap::Parser;
use ghs_sweeper::{field::Field, verify::RawField};
use serde::Serialize;
use std::collections::BTreeMap;

#[derive(Parser)]
#[command(
    about = "Check one published split-pole existence witness; no cover or DLP is instantiated"
)]
struct Args {
    #[arg(long)]
    base_degree: u32,
    #[arg(long)]
    relative_degree: u32,
    #[arg(long, default_value_t = 0)]
    a: u32,
    #[arg(long)]
    b: u32,
}

#[derive(Debug, Serialize)]
struct Witness {
    kind: &'static str,
    characteristic: u32,
    base_degree: u32,
    relative_degree: u32,
    absolute_degree: u32,
    modulus: u32,
    a: u32,
    b: u32,
    absolute_trace_a: u32,
    gamma: u32,
    beta: u32,
    relative_trace_gamma: u32,
    relative_trace_beta: u32,
    gamma_annihilator_binary: u64,
    beta_annihilator_binary: u64,
    joint_annihilator_binary: u64,
    joint_frobenius_period: u32,
    m: u32,
    published_witness_genus: u64,
    uniform_existence_genus_bound: u64,
    kernel_annihilated_by: u64,
    independent_parameter_checks_passed: bool,
    exact_constant_condition_checked: bool,
    frobenius_lift_condition_checked: bool,
    curve_id: Option<String>,
    candidate_id: Option<String>,
    subgroup_order: Option<u64>,
    cover_instantiated: bool,
    planted_log_verified: bool,
    publication_novelty_established: bool,
    interpretation: &'static str,
}

fn orbit(f: &Field, mut x: u32, d: u32, n: u32) -> Vec<u32> {
    (0..n)
        .map(|_| {
            let value = x;
            x = f.power(x, 1 << d);
            value
        })
        .collect()
}

fn raw_orbit(f: &RawField, mut x: u32, d: u32, n: u32) -> Vec<u32> {
    (0..n)
        .map(|_| {
            let value = x;
            for _ in 0..d {
                x = f.mul(x, x);
            }
            value
        })
        .collect()
}

fn trace(values: &[u32]) -> u32 {
    values.iter().fold(0, |a, b| a ^ b)
}

fn rem(mut a: u64, b: u64) -> u64 {
    while a != 0 && a.ilog2() >= b.ilog2() {
        a ^= b << (a.ilog2() - b.ilog2());
    }
    a
}

/// Minimal relation among successive Frobenius images over F2, with the
/// relation tracked during elimination. The input wraps at its known period.
fn annihilator(values: &[u64]) -> u64 {
    let mut basis = BTreeMap::new();
    for i in 0..=values.len() {
        let mut value = values[i % values.len()];
        let mut relation = 1_u64 << i;
        while value != 0 {
            let pivot = value.ilog2();
            if let Some(&(row, combination)) = basis.get(&pivot) {
                value ^= row;
                relation ^= combination;
            } else {
                basis.insert(pivot, (value, relation));
                break;
            }
        }
        if value == 0 {
            return relation;
        }
    }
    unreachable!("a cyclic orbit has a relation by its period")
}

fn witness(d: u32, n: u32, a: u32, b: u32) -> Result<Witness> {
    ensure!(
        d > 0 && n >= 2,
        "a proper extension of relative degree at least two is required"
    );
    let degree = d.checked_mul(n).context("field degree overflow")?;
    ensure!(
        degree <= 20,
        "this parameter checker supports absolute degree at most 20"
    );
    let f = Field::new(degree)?;
    ensure!(
        a < f.size && b > 0 && b < f.size,
        "invalid or singular source parameters"
    );
    let b_orbit = orbit(&f, b, d, n);
    ensure!(
        (1..n).all(|i| b_orbit[i as usize] != b),
        "b is not of full relative degree; no conclusion for subfield or Koblitz inputs"
    );

    let root_b = f.power(b, 1 << (degree - 1));
    let (gamma, beta) = (1..f.size)
        .filter(|&g| trace(&orbit(&f, g, d, n)) == 0)
        .find_map(|g| {
            let beta = f.mul(root_b, f.inv(g));
            (trace(&orbit(&f, beta, d, n)) != 0).then_some((g, beta))
        })
        .context("no trace-balanced witness; this would contradict the stated lemma")?;

    let raw = RawField::new(degree, f.modulus)?;
    ensure!(
        raw.mul(root_b, root_b) == b,
        "independent square-root check failed"
    );
    ensure!(
        raw.mul(gamma, beta) == root_b,
        "independent product check failed"
    );
    let go = raw_orbit(&raw, gamma, d, n);
    let bo = raw_orbit(&raw, beta, d, n);
    ensure!(
        go == orbit(&f, gamma, d, n) && bo == orbit(&f, beta, d, n),
        "Frobenius algorithms disagree"
    );
    ensure!(
        trace(&go) == 0 && trace(&bo) != 0,
        "trace conditions failed"
    );

    let gamma_ann = annihilator(&go.iter().map(|&x| x as u64).collect::<Vec<_>>());
    let beta_ann = annihilator(&bo.iter().map(|&x| x as u64).collect::<Vec<_>>());
    let pairs: Vec<_> = go
        .iter()
        .zip(&bo)
        .map(|(&g, &b)| g as u64 | ((b as u64) << degree))
        .collect();
    let joint_ann = annihilator(&pairs);
    let (u, v, m) = (gamma_ann.ilog2(), beta_ann.ilog2(), joint_ann.ilog2());
    ensure!(u < n && v <= n && m <= n, "annihilator-degree bound failed");
    ensure!(
        rem((1 << n) - 1, gamma_ann) == 0,
        "gamma is not annihilated by the trace polynomial"
    );
    ensure!(
        rem((1 << n) | 1, joint_ann) == 0,
        "joint annihilator does not divide T^N+1"
    );
    ensure!(
        rem(joint_ann, gamma_ann) == 0 && rem(joint_ann, beta_ann) == 0,
        "joint relation failed"
    );
    ensure!(
        beta_ann.count_ones().is_multiple_of(2) && joint_ann.count_ones().is_multiple_of(2),
        "T+1 factor missing"
    );
    let ao = raw_orbit(&raw, a, d, n);
    let constant_relation = (0..=m)
        .filter(|&i| joint_ann & (1 << i) != 0)
        .fold(0, |value, i| value ^ ao[(i % n) as usize]);
    ensure!(
        raw.traces[constant_relation as usize] == 0,
        "exact-constant condition failed"
    );
    let period = (1..=n)
        .find(|&i| pairs[(i % n) as usize] == pairs[0])
        .unwrap();
    ensure!(
        period == n,
        "the full-period condition for Hess Theorem 14 failed"
    );
    let genus = (1_u64 << m) - (1 << (m - u)) - (1 << (m - v)) + 1;
    let bound = (1_u64 << n) - 2;
    ensure!(genus <= bound, "uniform genus bound failed");

    Ok(Witness {
        kind: "published_hess_split_pole_parameters",
        characteristic: 2, base_degree: d, relative_degree: n, absolute_degree: degree,
        modulus: f.modulus, a, b, absolute_trace_a: raw.traces[a as usize], gamma, beta,
        relative_trace_gamma: trace(&go), relative_trace_beta: trace(&bo),
        gamma_annihilator_binary: gamma_ann, beta_annihilator_binary: beta_ann,
        joint_annihilator_binary: joint_ann, joint_frobenius_period: period, m,
        published_witness_genus: genus, uniform_existence_genus_bound: bound,
        kernel_annihilated_by: 1 << (m - 1), independent_parameter_checks_passed: true,
        exact_constant_condition_checked: true, frobenius_lift_condition_checked: true,
        curve_id: None, candidate_id: None, subgroup_order: None, cover_instantiated: false,
        planted_log_verified: false, publication_novelty_established: false,
        interpretation: "Published-construction inclusion witness, not a minimum-genus or cost result. Odd-subgroup injectivity is derived from Hess Theorem 14; no explicit cover, subgroup, or log is instantiated here.",
    })
}

fn main() -> Result<()> {
    let args = Args::parse();
    println!(
        "{}",
        serde_json::to_string_pretty(&witness(
            args.base_degree,
            args.relative_degree,
            args.a,
            args.b
        )?)?
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quadratic_controls_cover_both_constant_traces() -> Result<()> {
        for d in 1..=4 {
            let f = Field::new(2 * d)?;
            let one = f.trace.iter().position(|&t| t == 1).unwrap() as u32;
            for a in [0, one] {
                let w = witness(d, 2, a, 2)?;
                assert_eq!(w.published_witness_genus, 2);
                assert_eq!(w.gamma, 1);
                assert_eq!(w.absolute_trace_a, u32::from(a != 0));
            }
        }
        Ok(())
    }

    #[test]
    fn cubic_fixed_control_has_the_expected_hess_parameters() -> Result<()> {
        let w = witness(1, 3, 1, 2)?;
        assert_eq!(
            (w.gamma, w.beta, w.m, w.published_witness_genus),
            (2, 3, 3, 6)
        );
        assert_eq!(
            (w.gamma_annihilator_binary, w.beta_annihilator_binary),
            (7, 9)
        );
        Ok(())
    }

    #[test]
    fn even_degree_and_historical_trace_one_controls() -> Result<()> {
        let f = Field::new(4)?;
        let one = f.trace.iter().position(|&t| t == 1).unwrap() as u32;
        assert!(witness(1, 4, one, 2)?.published_witness_genus <= 14);
        let old = witness(2, 5, 236, 166)?;
        assert_eq!(old.absolute_trace_a, 1);
        assert!(old.published_witness_genus <= 30);
        assert!(
            !old.cover_instantiated
                && !old.planted_log_verified
                && !old.publication_novelty_established
        );
        Ok(())
    }

    #[test]
    fn proper_subfield_koblitz_singular_and_trivial_inputs_are_outside_scope() {
        assert!(witness(1, 3, 0, 1).is_err());
        assert!(witness(1, 3, 0, 0).is_err());
        assert!(witness(1, 1, 0, 1).is_err());
        assert!(witness(1, 3, 8, 2).is_err());
    }
}
