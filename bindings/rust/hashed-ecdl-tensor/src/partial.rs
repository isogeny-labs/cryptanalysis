//! Nested-threshold partial relations with exact odd-order sparse elimination.
//! Columns retain slot identities. This is not binary graph-cycle cancellation.

use crate::arithmetic::{inverse, random_below, RandomSource};
use crate::curve::{Curve, Point};
use crate::reduction::{FactorBase, Relation};
use crate::{integrity, invalid, overflow, BigUint, Error, Meter, Result};
use num_traits::{One, Zero};
use std::collections::{BTreeMap, BTreeSet};

/// Same affine hash with an inner and an outer threshold.
#[derive(Clone, Debug)]
pub struct NestedBase {
    inner: FactorBase,
    outer: FactorBase,
}
impl NestedBase {
    /// Validate nesting without changing hash seeds or certifying a new modulus.
    pub fn new(inner: FactorBase, outer: FactorBase) -> Result<Self> {
        if inner.prime() != outer.prime()
            || inner.seed() != outer.seed()
            || inner.threshold() > outer.threshold()
        {
            return Err(invalid("non-nested hash bases"));
        }
        Ok(Self { inner, outer })
    }
    /// Small base.
    pub fn inner(&self) -> &FactorBase {
        &self.inner
    }
    /// Larger base.
    pub fn outer(&self) -> &FactorBase {
        &self.outer
    }
}

/// Algebraic certificate containing all admitted original partial relations.
#[derive(Clone, Debug)]
pub struct Certificate {
    /// Labelled original rows, never only their post-elimination replacements.
    pub relations: Vec<Relation>,
    /// Canonical row coefficients modulo the subgroup prime.
    pub dependency: Vec<BigUint>,
    /// Independently verified discrete logarithm.
    pub scalar: BigUint,
}

/// The disposition of an attempted partial relation.
#[derive(Clone, Debug)]
pub enum Outcome {
    /// Valid outer relation rejected by the two-outer-point admission policy.
    Rejected,
    /// A new pivot; the Boolean records whether its first column is outer.
    Pivot(bool),
    /// A row dependency whose target coefficient is zero; no scalar extraction.
    Degenerate,
    /// Complete independently replayed solution.
    Solved(Certificate),
}

// Outer columns sort before inner columns, so every outer coefficient is
// eliminated before a retained row can pivot on its inner part.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
struct Column {
    inner: bool,
    slot: usize,
    point: Point,
}
#[derive(Clone)]
struct Row {
    columns: BTreeMap<Column, BigUint>,
    weights: BTreeMap<usize, BigUint>,
    u: BigUint,
    v: BigUint,
}
fn subtract<K: Ord + Clone>(
    left: &mut BTreeMap<K, BigUint>,
    right: &BTreeMap<K, BigUint>,
    scale: &BigUint,
    modulus: &BigUint,
    meter: &mut Meter,
) -> Result<()> {
    for (key, value) in right {
        meter.charge(1, "partial sparse elimination")?;
        let old = left.get(key).cloned().unwrap_or_default();
        let next = (old + modulus - scale * value % modulus) % modulus;
        if next.is_zero() {
            left.remove(key);
        } else {
            left.insert(key.clone(), next);
        }
        meter.vector(left.len(), "partial sparse row")?;
    }
    Ok(())
}
fn check_relation(
    curve: &Curve,
    target: &Point,
    bases: &[NestedBase],
    relation: &Relation,
    meter: &mut Meter,
) -> Result<(BTreeMap<Column, BigUint>, usize)> {
    if relation.points.len() != bases.len()
        || relation.u >= *curve.order()
        || relation.v >= *curve.order()
    {
        return Err(invalid("partial relation shape or scalar"));
    }
    let mut columns = BTreeMap::new();
    let mut outer = 0;
    let mut sum = Point::Infinity;
    for (slot, (base, point)) in bases.iter().zip(&relation.points).enumerate() {
        if !base.outer.contains(curve, point, meter)? {
            return Err(integrity("partial outer membership"));
        }
        let inner = base.inner.contains(curve, point, meter)?;
        outer += usize::from(!inner);
        columns.insert(
            Column {
                inner,
                slot,
                point: point.clone(),
            },
            BigUint::one(),
        );
        sum = curve.add(&sum, point, meter)?;
    }
    let left = curve.mul(curve.generator(), &relation.u, meter)?;
    let right = curve.mul(target, &relation.v, meter)?;
    if curve.add(&left, &right, meter)? != sum {
        return Err(integrity("partial labelled group equation"));
    }
    Ok((columns, outer))
}

/// Bounded streaming collector. Each row admits at most two outer-base points.
/// Raw provenance and scalar labels survive all elimination operations.
pub struct Collector {
    curve: Curve,
    target: Point,
    bases: Vec<NestedBase>,
    max_relations: usize,
    max_columns: usize,
    relations: Vec<Relation>,
    columns: BTreeSet<Column>,
    pivots: BTreeMap<Column, Row>,
    finished: bool,
}
impl Collector {
    /// Bind the actual curve, target, nested slot bases and resource policies.
    pub fn new(
        curve: &Curve,
        target: &Point,
        bases: Vec<NestedBase>,
        max_relations: usize,
        max_columns: usize,
        meter: &mut Meter,
    ) -> Result<Self> {
        if bases.len() < 2
            || max_relations == 0
            || max_columns == 0
            || !curve.in_subgroup(target, meter)?
        {
            return Err(invalid("partial collector policy"));
        }
        meter.vector(bases.len(), "partial base slots")?;
        for base in &bases {
            if base.outer.prime() < &(curve.modulus() << 1)
                || base.outer.prime() > &(curve.modulus() << 2)
            {
                return Err(invalid("partial hash field range"));
            }
        }
        Ok(Self {
            curve: curve.clone(),
            target: target.clone(),
            bases,
            max_relations,
            max_columns,
            relations: Vec::new(),
            columns: BTreeSet::new(),
            pivots: BTreeMap::new(),
            finished: false,
        })
    }
    /// Admit, eliminate and, when possible, recover a scalar. An error invalidates
    /// continuation of this collector; callers must not treat it as rejection.
    pub fn push(&mut self, relation: Relation, meter: &mut Meter) -> Result<Outcome> {
        if self.finished {
            return Err(invalid("partial collector already solved"));
        }
        let (columns, outer) =
            check_relation(&self.curve, &self.target, &self.bases, &relation, meter)?;
        if outer > 2 {
            return Ok(Outcome::Rejected);
        }
        if self.relations.len() >= self.max_relations {
            return Err(Error::Limit("partial relation policy".into()));
        }
        let count = self
            .columns
            .union(&columns.keys().cloned().collect())
            .count();
        if count > self.max_columns {
            return Err(Error::Limit("partial column policy".into()));
        }
        meter.vector(count, "partial columns")?;
        meter.vector(self.relations.len() + 1, "partial provenance rows")?;
        let mut row = Row {
            columns,
            weights: BTreeMap::from([(self.relations.len(), BigUint::one())]),
            u: relation.u.clone(),
            v: relation.v.clone(),
        };
        self.columns.extend(row.columns.keys().cloned());
        self.relations.push(relation);
        let modulus = self.curve.order();
        for (column, pivot) in &self.pivots {
            let Some(scale) = row.columns.get(column).cloned() else {
                continue;
            };
            subtract(&mut row.columns, &pivot.columns, &scale, modulus, meter)?;
            subtract(&mut row.weights, &pivot.weights, &scale, modulus, meter)?;
            row.u = (&row.u + modulus - &scale * &pivot.u % modulus) % modulus;
            row.v = (&row.v + modulus - &scale * &pivot.v % modulus) % modulus;
        }
        if let Some((column, value)) = row.columns.first_key_value() {
            let column = column.clone();
            let scale = inverse(value, modulus)?;
            for value in row
                .columns
                .values_mut()
                .chain(row.weights.values_mut())
                .chain([&mut row.u, &mut row.v])
            {
                meter.charge(1, "partial pivot normalization")?;
                *value = &*value * &scale % modulus;
            }
            let cells =
                self.pivots
                    .values()
                    .try_fold(row.columns.len() + row.weights.len(), |n, p| {
                        n.checked_add(p.columns.len())
                            .and_then(|n| n.checked_add(p.weights.len()))
                            .ok_or_else(|| overflow("partial pivot storage"))
                    })?;
            meter.vector(cells, "partial pivot storage")?;
            let outer = !column.inner;
            self.pivots.insert(column, row);
            return Ok(Outcome::Pivot(outer));
        }
        if row.v.is_zero() {
            return Ok(Outcome::Degenerate);
        }
        let scalar = (modulus - row.u) * inverse(&row.v, modulus)? % modulus;
        let mut dependency = vec![BigUint::zero(); self.relations.len()];
        for (i, value) in row.weights {
            dependency[i] = value;
        }
        let certificate = Certificate {
            relations: self.relations.clone(),
            dependency,
            scalar,
        };
        verify(&self.curve, &self.target, &self.bases, &certificate, meter)?;
        self.finished = true;
        Ok(Outcome::Solved(certificate))
    }
}

/// Independent replay of original rows, outer/inner cancellations and scalar.
pub fn verify(
    curve: &Curve,
    target: &Point,
    bases: &[NestedBase],
    certificate: &Certificate,
    meter: &mut Meter,
) -> Result<()> {
    if bases.len() < 2
        || !curve.in_subgroup(target, meter)?
        || certificate.relations.is_empty()
        || certificate.dependency.len() != certificate.relations.len()
        || certificate.scalar >= *curve.order()
        || !certificate.dependency.iter().any(|c| !c.is_zero())
    {
        return Err(invalid("partial certificate shape"));
    }
    let mut columns = BTreeMap::<Column, BigUint>::new();
    let (mut u, mut v) = (BigUint::zero(), BigUint::zero());
    for (relation, coefficient) in certificate.relations.iter().zip(&certificate.dependency) {
        if coefficient >= curve.order() {
            return Err(invalid("partial dependency coefficient"));
        }
        let (row, outer) = check_relation(curve, target, bases, relation, meter)?;
        if outer > 2 {
            return Err(invalid("partial outer admission"));
        }
        for (column, value) in row {
            meter.charge(1, "partial independent column replay")?;
            let x = columns.entry(column).or_default();
            *x = (&*x + coefficient * value) % curve.order();
            meter.vector(columns.len(), "partial replay columns")?;
        }
        u = (u + coefficient * &relation.u) % curve.order();
        v = (v + coefficient * &relation.v) % curve.order();
    }
    if columns.values().any(|x| !x.is_zero())
        || v.is_zero()
        || (u + &certificate.scalar * v) % curve.order() != BigUint::zero()
        || curve.mul(curve.generator(), &certificate.scalar, meter)? != *target
    {
        return Err(integrity("partial dependency/scalar replay"));
    }
    Ok(())
}

/// Collect bounded natural labelled queries using the outer selector domains.
/// The witness engine sees neither the relation scalars nor their RNG. Returns
/// the complete partial certificate, or a limit error after the explicit budget.
pub fn solve(
    curve: &Curve,
    target: &Point,
    bases: Vec<NestedBase>,
    max_relations: usize,
    max_columns: usize,
    attempts: usize,
    rng: &mut impl RandomSource,
    meter: &mut Meter,
) -> Result<Certificate> {
    if attempts == 0 {
        return Err(invalid("partial attempt policy"));
    }
    let outer: Vec<_> = bases.iter().map(|b| b.outer.clone()).collect();
    let mut collector = Collector::new(curve, target, bases, max_relations, max_columns, meter)?;
    let mut statistics = crate::finite::Statistics::default();
    for _ in 0..attempts {
        meter.charge(1, "partial relation query")?;
        let u = random_below(curve.order(), rng, meter)?;
        let v = random_below(curve.order(), rng, meter)?;
        let left = curve.mul(curve.generator(), &u, meter)?;
        let right = curve.mul(target, &v, meter)?;
        let query = curve.add(&left, &right, meter)?;
        if let Some(points) = crate::finite::prime_decompose(
            curve,
            &outer,
            &query,
            &crate::finite::Options::default(),
            &mut statistics,
            meter,
        )? {
            if let Outcome::Solved(certificate) =
                collector.push(Relation { u, v, points }, meter)?
            {
                return Ok(certificate);
            }
        }
    }
    Err(Error::Limit("partial relation attempts exhausted".into()))
}
