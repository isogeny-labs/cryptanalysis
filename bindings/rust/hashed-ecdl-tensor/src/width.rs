//! Bounded exact variable elimination, cutset conditioning and witness propagation.
//! Plans are rechecked on the actual graph and pins. No floating-point tensors,
//! opaque-predicate factorization, or change to Appendix D's parameter guards.

use crate::network::{increment, Network};
use crate::{integrity, invalid, overflow, BigUint, Error, Meter, Result};
use num_traits::{One, Zero};
use std::collections::BTreeSet;

/// Explicit finite-size memory/search envelope.
#[derive(Clone, Debug)]
pub struct Policy {
    /// Maximum initial or intermediate factor rank, before allocating tables.
    pub maximum_rank: usize,
    /// Maximum conditioned edge bits; each creates two exact child cases.
    pub maximum_slices: usize,
}
impl Default for Policy {
    fn default() -> Self {
        Self {
            maximum_rank: 16,
            maximum_slices: 16,
        }
    }
}

/// A proposed elimination/cutset plan. Public fields are never trusted unchecked.
#[derive(Clone, Debug)]
pub struct Plan {
    /// Bits conditioned before elimination; every assignment is included.
    pub slices: Vec<usize>,
    /// Remaining free edges, each eliminated exactly once.
    pub order: Vec<usize>,
    /// Admitted maximum factor rank; validation recomputes it.
    pub maximum_rank: usize,
}

fn scopes(
    network: &Network,
    pins: &[Option<bool>],
    slices: &BTreeSet<usize>,
) -> Vec<BTreeSet<usize>> {
    network
        .vertices
        .iter()
        .map(|v| {
            v.edges
                .iter()
                .copied()
                .filter(|&e| pins[e].is_none() && !slices.contains(&e))
                .collect()
        })
        .collect()
}
fn bag(factors: &[BTreeSet<usize>], edge: usize, meter: &mut Meter) -> Result<BTreeSet<usize>> {
    let mut out = BTreeSet::new();
    for scope in factors {
        meter.charge(1, "width planning scope")?;
        if scope.contains(&edge) {
            for &e in scope {
                meter.charge(1, "width planning incidence")?;
                out.insert(e);
            }
        }
    }
    Ok(out)
}
fn eliminate(scopes: &mut Vec<BTreeSet<usize>>, edge: usize, mut joined: BTreeSet<usize>) {
    scopes.retain(|s| !s.contains(&edge));
    joined.remove(&edge);
    scopes.push(joined);
}
fn greedy(
    mut factors: Vec<BTreeSet<usize>>,
    mut free: BTreeSet<usize>,
    meter: &mut Meter,
) -> Result<(Vec<usize>, usize, BTreeSet<usize>)> {
    let mut widest = factors
        .iter()
        .max_by_key(|s| s.len())
        .cloned()
        .unwrap_or_default();
    let mut rank = widest.len();
    let mut order = Vec::new();
    while !free.is_empty() {
        let mut best: Option<(usize, BTreeSet<usize>)> = None;
        for &edge in &free {
            let joined = bag(&factors, edge, meter)?;
            if best
                .as_ref()
                .map_or(true, |(e, b)| (joined.len(), edge) < (b.len(), *e))
            {
                best = Some((edge, joined));
            }
        }
        let (edge, joined) = best.ok_or_else(|| integrity("empty elimination choice"))?;
        if joined.len() > rank {
            rank = joined.len();
            widest = joined.clone();
        }
        eliminate(&mut factors, edge, joined);
        free.remove(&edge);
        order.push(edge);
    }
    Ok((order, rank, widest))
}

/// Build a greedy minimum-rank order, adding cutset bits until the rank fits.
/// Failure to fit the explicit slice/memory/work policy is a resource error.
pub fn plan(
    network: &Network,
    pins: &[Option<bool>],
    policy: &Policy,
    meter: &mut Meter,
) -> Result<Plan> {
    network.check_pins(pins)?;
    meter.vector(network.edge_count(), "width planning edges")?;
    meter.vector(network.vertex_count(), "width planning vertices")?;
    let mut cuts = BTreeSet::new();
    loop {
        let factors = scopes(network, pins, &cuts);
        let free = pins
            .iter()
            .enumerate()
            .filter_map(|(e, p)| (p.is_none() && !cuts.contains(&e)).then_some(e))
            .collect();
        let (order, rank, widest) = greedy(factors.clone(), free, meter)?;
        if rank <= policy.maximum_rank {
            cells(rank, meter)?;
            return Ok(Plan {
                slices: cuts.into_iter().collect(),
                order,
                maximum_rank: rank,
            });
        }
        if cuts.len() >= policy.maximum_slices {
            return Err(Error::Limit("width slice policy".into()));
        }
        let edge = widest
            .into_iter()
            .max_by_key(|e| {
                (
                    factors.iter().filter(|s| s.contains(e)).count(),
                    std::cmp::Reverse(*e),
                )
            })
            .ok_or_else(|| integrity("oversized empty factor"))?;
        cuts.insert(edge);
    }
}

impl Plan {
    /// Recheck partition, pins and all intermediate ranks against this graph.
    pub fn validate(
        &self,
        network: &Network,
        pins: &[Option<bool>],
        meter: &mut Meter,
    ) -> Result<()> {
        network.check_pins(pins)?;
        meter.vector(network.edge_count(), "plan graph edges")?;
        meter.vector(network.vertex_count(), "plan graph vertices")?;
        let mut all = BTreeSet::new();
        for &edge in self.slices.iter().chain(&self.order) {
            meter.charge(1, "validate contraction plan")?;
            if edge >= network.edge_count() || pins[edge].is_some() || !all.insert(edge) {
                return Err(invalid("contraction plan edge partition"));
            }
        }
        if all.len() != pins.iter().filter(|p| p.is_none()).count() {
            return Err(invalid("contraction plan omitted a free edge"));
        }
        let cuts = self.slices.iter().copied().collect();
        let mut factors = scopes(network, pins, &cuts);
        let mut rank = factors.iter().map(BTreeSet::len).max().unwrap_or(0);
        for &edge in &self.order {
            let joined = bag(&factors, edge, meter)?;
            rank = rank.max(joined.len());
            eliminate(&mut factors, edge, joined);
        }
        if rank > self.maximum_rank {
            return Err(invalid("understated contraction rank"));
        }
        cells(self.maximum_rank, meter)?;
        Ok(())
    }
}
fn cells(rank: usize, meter: &Meter) -> Result<usize> {
    let n = 1usize
        .checked_shl(u32::try_from(rank).map_err(|_| overflow("factor rank"))?)
        .ok_or_else(|| overflow("factor table"))?;
    meter.vector(n, "factor table")?;
    Ok(n)
}
struct Factor {
    scope: Vec<usize>,
    values: Vec<BigUint>,
}
fn index(scope: &[usize], values: &[bool]) -> usize {
    scope
        .iter()
        .enumerate()
        .fold(0, |n, (i, &e)| n | (usize::from(values[e]) << i))
}
fn set(scope: &[usize], number: usize, values: &mut [bool]) {
    for (i, &e) in scope.iter().enumerate() {
        values[e] = number & (1usize << i) != 0;
    }
}
fn storage(factors: &[Factor]) -> Result<usize> {
    factors.iter().try_fold(0usize, |n, f| {
        n.checked_add(f.values.len())
            .ok_or_else(|| overflow("factor storage"))
    })
}

/// Execute all exact conditioned children and sum them. An exhausted plan is
/// never reported as zero. The manuscript's packet recursion is not invoked.
pub fn count(
    network: &Network,
    pins: &[Option<bool>],
    plan: &Plan,
    meter: &mut Meter,
) -> Result<BigUint> {
    plan.validate(network, pins, meter)?;
    let free = plan
        .order
        .len()
        .checked_add(plan.slices.len())
        .ok_or_else(|| overflow("count width"))?;
    meter.bits(
        free.checked_add(1).ok_or_else(|| overflow("count width"))?,
        "exact finite count",
    )?;
    let mut digits = vec![false; plan.slices.len()];
    let cuts: BTreeSet<_> = plan.slices.iter().copied().collect();
    let mut total = BigUint::zero();
    loop {
        meter.charge(1, "conditioned contraction child")?;
        let mut assignment: Vec<_> = pins.iter().map(|p| p.unwrap_or(false)).collect();
        for (&e, &b) in plan.slices.iter().zip(&digits) {
            assignment[e] = b;
        }
        let mut factors = Vec::new();
        for vertex in &network.vertices {
            let scope: Vec<_> = vertex
                .edges
                .iter()
                .copied()
                .filter(|&e| pins[e].is_none() && !cuts.contains(&e))
                .collect();
            let length = cells(scope.len(), meter)?;
            meter.vector(
                storage(&factors)?
                    .checked_add(length)
                    .ok_or_else(|| overflow("factor storage"))?,
                "live factor tables",
            )?;
            let mut values = Vec::with_capacity(length);
            for n in 0..length {
                meter.charge(1, "predicate table entry")?;
                set(&scope, n, &mut assignment);
                let ports: Vec<_> = vertex.edges.iter().map(|&e| assignment[e]).collect();
                values.push(BigUint::from(u8::from(
                    vertex.predicate.evaluate(&ports, meter)?,
                )));
            }
            factors.push(Factor { scope, values });
        }
        for &edge in &plan.order {
            let mut selected = Vec::new();
            let mut remaining = Vec::new();
            for factor in factors {
                if factor.scope.contains(&edge) {
                    selected.push(factor);
                } else {
                    remaining.push(factor);
                }
            }
            let scope: Vec<_> = selected
                .iter()
                .flat_map(|f| f.scope.iter().copied())
                .filter(|&e| e != edge)
                .collect::<BTreeSet<_>>()
                .into_iter()
                .collect();
            let length = cells(scope.len(), meter)?;
            let live = storage(&selected)?
                .checked_add(storage(&remaining)?)
                .and_then(|n| n.checked_add(length))
                .ok_or_else(|| overflow("elimination storage"))?;
            meter.vector(live, "live elimination tables")?;
            let mut values = Vec::with_capacity(length);
            for n in 0..length {
                set(&scope, n, &mut assignment);
                let mut sum = BigUint::zero();
                for bit in [false, true] {
                    assignment[edge] = bit;
                    let mut product = BigUint::one();
                    for factor in &selected {
                        meter.charge(1, "exact factor product")?;
                        product *= &factor.values[index(&factor.scope, &assignment)];
                    }
                    sum += product;
                }
                values.push(sum);
            }
            remaining.push(Factor { scope, values });
            factors = remaining;
        }
        let mut child = BigUint::one();
        for factor in factors {
            meter.charge(1, "isolated factor product")?;
            if !factor.scope.is_empty() || factor.values.len() != 1 {
                return Err(integrity("uneliminated factor"));
            }
            child *= &factor.values[0];
        }
        total += child;
        if !increment(&mut digits) {
            break;
        }
    }
    Ok(total)
}

fn propagate(
    network: &Network,
    state: &mut [Option<bool>],
    rank: usize,
    meter: &mut Meter,
) -> Result<bool> {
    loop {
        let mut changed = false;
        for vertex in &network.vertices {
            let free: Vec<_> = vertex
                .edges
                .iter()
                .copied()
                .filter(|&e| state[e].is_none())
                .collect();
            if free.len() > rank {
                continue;
            }
            let length = cells(free.len(), meter)?;
            let mut support: Option<Vec<bool>> = None;
            let mut agreed = vec![true; free.len()];
            for number in 0..length {
                meter.charge(1, "witness support assignment")?;
                let bits: Vec<_> = (0..free.len()).map(|i| number & (1 << i) != 0).collect();
                let ports: Vec<_> = vertex
                    .edges
                    .iter()
                    .map(|&e| {
                        state[e].unwrap_or_else(|| bits[free.iter().position(|&f| f == e).unwrap()])
                    })
                    .collect();
                if vertex.predicate.evaluate(&ports, meter)? {
                    if let Some(first) = &support {
                        for (i, &bit) in bits.iter().enumerate() {
                            agreed[i] &= first[i] == bit;
                        }
                    } else {
                        support = Some(bits);
                    }
                }
            }
            let Some(first) = support else {
                return Ok(false);
            };
            for (i, &edge) in free.iter().enumerate() {
                if agreed[i] {
                    state[edge] = Some(first[i]);
                    changed = true;
                }
            }
        }
        if !changed {
            return Ok(true);
        }
    }
}

/// Witness-only exact search with bounded local support propagation. It does
/// not request count precision. High-arity predicates wait for more assignments.
/// Returned interface bits always pass a full independent graph evaluation.
pub fn witness(
    network: &Network,
    pins: &[Option<bool>],
    plan: &Plan,
    meter: &mut Meter,
) -> Result<Option<Vec<bool>>> {
    plan.validate(network, pins, meter)?;
    let mut stack = vec![pins.to_vec()];
    while let Some(mut state) = stack.pop() {
        meter.charge(1, "finite witness branch")?;
        if !propagate(network, &mut state, plan.maximum_rank, meter)? {
            continue;
        }
        if let Some(edge) = plan
            .slices
            .iter()
            .chain(&plan.order)
            .copied()
            .find(|&e| state[e].is_none())
        {
            meter.vector(
                stack
                    .len()
                    .checked_add(2)
                    .and_then(|n| n.checked_mul(network.edge_count()))
                    .ok_or_else(|| overflow("witness frontier"))?,
                "witness frontier",
            )?;
            let mut yes = state.clone();
            yes[edge] = Some(true);
            state[edge] = Some(false);
            stack.push(yes);
            stack.push(state);
        } else {
            let assignment: Vec<_> = state.into_iter().map(Option::unwrap).collect();
            if !network.evaluate(&assignment, meter)? {
                return Err(integrity("propagated witness replay"));
            }
            return Ok(Some(
                network.interface.iter().map(|&e| assignment[e]).collect(),
            ));
        }
    }
    Ok(None)
}
