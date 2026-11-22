//! Exact bounded cost profiles motivated by Hexagon 2610.00594v1 and
//! 2610.00613v1: coefficients count assignments of each total local cost.
//!
//! This is an exhaustive correctness/reference backend, not the papers'
//! subexponential weighted contraction algorithm. It does not replace the
//! coefficient ring of the existing recursive counter by a tropical semiring.

use crate::network::increment;
use crate::{invalid, overflow, BigUint, Meter, Result};
use num_traits::{One, Zero};
use std::collections::BTreeSet;

/// A truth table of nonnegative local costs. `None` rejects an assignment.
#[derive(Clone, Debug)]
pub struct LocalCost {
    /// Distinct zero-based variable indices, in truth-table bit order (LSB first).
    pub variables: Vec<usize>,
    /// Exactly `2^variables.len()` entries; zero-variable constants are allowed.
    pub costs: Vec<Option<usize>>,
}

/// Coefficient representation of the generating polynomial, with no truncation.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CostProfile {
    /// Coefficient `j` counts accepted assignments whose total cost is `j`.
    pub coefficients: Vec<BigUint>,
}
impl CostProfile {
    /// Smallest attained total cost, or `None` for an inconsistent instance.
    pub fn minimum(&self) -> Option<usize> {
        self.coefficients.iter().position(|c| !c.is_zero())
    }
    /// Largest attained total cost, or `None` for an inconsistent instance.
    pub fn maximum(&self) -> Option<usize> {
        self.coefficients.iter().rposition(|c| !c.is_zero())
    }
}

/// Enumerate the exact local-cost generating polynomial under explicit limits.
/// Exceeding `maximum_cost` is an error, never silent polynomial truncation.
pub fn cost_profile(
    variables: usize,
    factors: &[LocalCost],
    maximum_cost: usize,
    meter: &mut Meter,
) -> Result<CostProfile> {
    meter.vector(variables, "cost-profile variables")?;
    meter.vector(factors.len(), "cost-profile factors")?;
    meter.bits(
        variables
            .checked_add(1)
            .ok_or_else(|| overflow("profile count width"))?,
        "cost-profile count width",
    )?;
    let length = maximum_cost
        .checked_add(1)
        .ok_or_else(|| overflow("profile coefficients"))?;
    meter.vector(length, "cost-profile coefficients")?;
    for factor in factors {
        let table_size = 1usize
            .checked_shl(
                u32::try_from(factor.variables.len()).map_err(|_| overflow("local cost arity"))?,
            )
            .ok_or_else(|| overflow("local cost table"))?;
        meter.vector(table_size, "local cost table")?;
        if factor.costs.len() != table_size
            || factor.variables.iter().any(|&v| v >= variables)
            || factor
                .variables
                .iter()
                .copied()
                .collect::<BTreeSet<_>>()
                .len()
                != factor.variables.len()
        {
            return Err(invalid("local cost table width or variable indices"));
        }
    }
    let mut coefficients = vec![BigUint::zero(); length];
    let mut assignment = vec![false; variables];
    loop {
        meter.charge(1, "cost-profile assignment")?;
        let mut score = 0usize;
        let mut accepted = true;
        for factor in factors {
            meter.charge(1, "local cost lookup")?;
            let mut index = 0usize;
            for (bit, &variable) in factor.variables.iter().enumerate() {
                meter.charge(1, "local cost input")?;
                if assignment[variable] {
                    index |= 1usize << bit;
                }
            }
            match factor.costs[index] {
                Some(cost) => {
                    score = score
                        .checked_add(cost)
                        .ok_or_else(|| overflow("total local cost"))?;
                }
                None => {
                    accepted = false;
                    break;
                }
            }
        }
        if accepted {
            if score > maximum_cost {
                return Err(crate::Error::Limit(
                    "cost profile exceeds declared coefficient bound".into(),
                ));
            }
            coefficients[score] += BigUint::one();
        }
        if !increment(&mut assignment) {
            break;
        }
    }
    Ok(CostProfile { coefficients })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Error, Limits};
    fn meter() -> Meter {
        Meter::new(Limits::default())
    }

    #[test]
    fn triangle_maxcut_profile_has_two_constant_and_six_optimal_assignments() {
        let factors: Vec<_> = [(0, 1), (1, 2), (0, 2)]
            .iter()
            .map(|&(a, b)| LocalCost {
                variables: vec![a, b],
                costs: vec![Some(0), Some(1), Some(1), Some(0)],
            })
            .collect();
        let p = cost_profile(3, &factors, 3, &mut meter()).unwrap();
        assert_eq!(
            p.coefficients,
            [2u32, 0, 6, 0]
                .into_iter()
                .map(BigUint::from)
                .collect::<Vec<_>>()
        );
        assert_eq!(p.minimum(), Some(0));
        assert_eq!(p.maximum(), Some(2));
    }

    #[test]
    fn parity_check_profile_retains_zero_word_and_positive_distance() {
        let mut factors: Vec<_> = (0..3)
            .map(|i| LocalCost {
                variables: vec![i],
                costs: vec![Some(0), Some(1)],
            })
            .collect();
        factors.push(LocalCost {
            variables: vec![0, 1, 2],
            costs: (0u32..8)
                .map(|v| (v.count_ones() % 2 == 0).then_some(0))
                .collect(),
        });
        let p = cost_profile(3, &factors, 3, &mut meter()).unwrap();
        assert_eq!(
            p.coefficients,
            [1u32, 0, 3, 0]
                .into_iter()
                .map(BigUint::from)
                .collect::<Vec<_>>()
        );
        assert_eq!(
            p.coefficients
                .iter()
                .enumerate()
                .skip(1)
                .find(|(_, v)| !v.is_zero())
                .map(|(i, _)| i),
            Some(2)
        );
    }

    #[test]
    fn constants_unsat_and_limits_have_distinct_outcomes() {
        assert_eq!(
            cost_profile(0, &[], 0, &mut meter()).unwrap().coefficients,
            vec![BigUint::one()]
        );
        let reject = LocalCost {
            variables: vec![],
            costs: vec![None],
        };
        assert_eq!(
            cost_profile(0, &[reject], 0, &mut meter())
                .unwrap()
                .maximum(),
            None
        );
        let invalid = LocalCost {
            variables: vec![0, 0],
            costs: vec![Some(0); 4],
        };
        assert!(cost_profile(1, &[invalid], 0, &mut meter()).is_err());
        let large = LocalCost {
            variables: vec![],
            costs: vec![Some(1)],
        };
        assert!(matches!(
            cost_profile(0, &[large], 0, &mut meter()),
            Err(Error::Limit(_))
        ));
        let mut work = meter();
        work.limits.steps = 0;
        assert!(matches!(
            cost_profile(2, &[], 0, &mut work),
            Err(Error::Limit(_))
        ));
    }
}
