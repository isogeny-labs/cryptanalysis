//! Inverse-hash bases, tensor decompositions and Figure 2's ECDL reduction.
//!
//! Matrix columns are slot/point pairs. The tensor predicate receives only a
//! target and hash parameters, never the relation scalars or enumerated bases.
//! A certificate is replayed using curve arithmetic and a matrix dependency,
//! independently of the contraction implementation and its execution counters.

use crate::arithmetic::{floor_root, hash_prime_by, inverse, random_below, RandomSource};
use crate::contraction::Counter;
use crate::curve::{Curve, Point};
use crate::encoding::Encoder;
use crate::network::Network;
use crate::{integrity, invalid, overflow, BigUint, Error, Meter, Result};
use num_integer::Integer;
use num_traits::{One, ToPrimitive, Zero};
use std::collections::BTreeMap;

/// One independent affine-hash seed over the common public prime.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct HashSeed {
    /// Nonzero multiplier, less than s.
    pub alpha: BigUint,
    /// Translation, less than s.
    pub beta: BigUint,
}
json_record!(HashSeed, required { alpha, beta }, optional {});

/// Validated factor-base predicate. The enumerated base is deliberately absent.
#[derive(Clone, Debug)]
pub struct FactorBase {
    prime: BigUint,
    threshold: BigUint,
    seed: HashSeed,
}
impl FactorBase {
    /// Certify the hash modulus, range and affine seed.
    pub fn new(
        curve: &Curve,
        prime: BigUint,
        threshold: BigUint,
        seed: HashSeed,
        meter: &mut Meter,
    ) -> Result<Self> {
        if prime < (curve.modulus() << 1)
            || prime > (curve.modulus() << 2)
            || threshold.is_zero()
            || threshold > prime
            || seed.alpha.is_zero()
            || seed.alpha >= prime
            || seed.beta >= prime
            || !curve.certifies_prime(&prime, meter)?
        {
            return Err(invalid("factor-base parameters"));
        }
        Ok(Self {
            prime,
            threshold,
            seed,
        })
    }
    /// Certified prime s.
    pub fn prime(&self) -> &BigUint {
        &self.prime
    }
    /// Threshold tau.
    pub fn threshold(&self) -> &BigUint {
        &self.threshold
    }
    /// Affine hash parameters.
    pub fn seed(&self) -> &HashSeed {
        &self.seed
    }
    /// Exact membership, including exclusion of the identity and subgroup check.
    pub fn contains(&self, curve: &Curve, point: &Point, meter: &mut Meter) -> Result<bool> {
        if point == &Point::Infinity || !curve.in_subgroup(point, meter)? {
            return Ok(false);
        }
        Ok(
            (&self.seed.alpha * curve.encode(point)? + &self.seed.beta) % &self.prime
                < self.threshold,
        )
    }
    /// Enumerate t in [0,tau), invert the affine hash and extract one root.
    /// Work is O(tau) expected polynomial-time point operations, with no O(p)
    /// group scan or square-root table. Order is deterministic after extraction.
    pub fn enumerate(
        &self,
        curve: &Curve,
        rng: &mut impl RandomSource,
        meter: &mut Meter,
    ) -> Result<Vec<Point>> {
        let count = self
            .threshold
            .to_usize()
            .ok_or_else(|| overflow("factor-base size"))?;
        meter.vector(count, "factor-base enumeration")?;
        let inv = inverse(&self.seed.alpha, &self.prime)?;
        let mut points = Vec::new();
        let mut decoder = curve.decoder()?;
        for t in 0..count {
            meter.charge(1, "inverse-hash enumeration")?;
            let z = &inv * ((BigUint::from(t) + &self.prime - &self.seed.beta) % &self.prime)
                % &self.prime;
            if let Some(point) = decoder.decode(&z, rng, meter)? {
                if curve.in_subgroup(&point, meter)? {
                    points.push(point);
                }
            }
        }
        points.sort();
        if points.windows(2).any(|p| p[0] == p[1]) {
            return Err(integrity("inverse hash produced duplicate points"));
        }
        Ok(points)
    }
}

/// Build Lemma 11's Boolean language without consulting a factor-base list.
/// The interface is each Ai's infinity flag, x bits and y bits, all little-endian.
/// For nontrivial cofactor, free Si are projected to `Ai=[c]Si`. Multiple preimages
/// are counted as assignments, while the projected language is unchanged.
pub fn decomposition_network(
    curve: &Curve,
    bases: &[FactorBase],
    target: &Point,
    meter: &mut Meter,
) -> Result<Network> {
    if bases.len() < 2 || !curve.in_subgroup(target, meter)? {
        return Err(invalid("decomposition target or arity"));
    }
    let mut encoder = Encoder::new();
    let mut sum = Encoder::constant_point(curve, &Point::Infinity)?;
    for base in bases {
        let point = if curve.cofactor().is_one() {
            encoder.input_point(curve, false, meter)?
        } else {
            let source = encoder.input_point(curve, true, meter)?;
            encoder.clear_cofactor(curve, &source, meter)?
        };
        encoder.hash_member(
            curve,
            &point,
            &base.prime,
            &base.seed.alpha,
            &base.seed.beta,
            &base.threshold,
            meter,
        )?;
        encoder.mark_point_interface(&point, meter)?;
        sum = encoder.point_add(curve, &sum, &point, meter)?;
    }
    encoder.assert_point_equal(&sum, &Encoder::constant_point(curve, target)?, meter)?;
    encoder.finish(meter)
}

/// Deterministic prefix-count decomposition. `None` certifies zero assignments;
/// exhaustion is an error and cannot be mistaken for nonexistence.
pub fn decompose(
    curve: &Curve,
    bases: &[FactorBase],
    target: &Point,
    counter: &mut Counter,
    meter: &mut Meter,
) -> Result<Option<Vec<Point>>> {
    decompose_with(
        curve,
        bases,
        target,
        |network, work| counter.witness(network, &vec![None; network.edge_count()], work),
        meter,
    )
}

/// Opt-in exact witness backend for the existing point-coordinate language.
/// Returned interface words receive the same independent point/hash/sum replay.
pub fn decompose_with(
    curve: &Curve,
    bases: &[FactorBase],
    target: &Point,
    mut witness: impl FnMut(&Network, &mut Meter) -> Result<Option<Vec<bool>>>,
    meter: &mut Meter,
) -> Result<Option<Vec<Point>>> {
    crate::metrics::phase("network_build")?;
    let network = decomposition_network(curve, bases, target, meter)?;
    crate::metrics::phase("contraction")?;
    let Some(word) = witness(&network, meter)? else {
        return Ok(None);
    };
    crate::metrics::phase("witness_check")?;
    let width = curve.modulus().bits() as usize;
    let stride = 1usize
        .checked_add(
            width
                .checked_mul(2)
                .ok_or_else(|| overflow("point interface"))?,
        )
        .ok_or_else(|| overflow("point interface"))?;
    if word.len()
        != stride
            .checked_mul(bases.len())
            .ok_or_else(|| overflow("point interface"))?
    {
        return Err(integrity("point interface length"));
    }
    let mut out = Vec::with_capacity(bases.len());
    let mut sum = Point::Infinity;
    for (bits, base) in word.chunks(stride).zip(bases) {
        if bits[0] {
            return Err(integrity("identity in factor-base witness"));
        }
        let integer = |bits: &[bool]| {
            bits.iter().enumerate().fold(BigUint::zero(), |n, (i, b)| {
                if *b {
                    n | (BigUint::one() << i)
                } else {
                    n
                }
            })
        };
        let point = Point::Affine {
            x: integer(&bits[1..1 + width]),
            y: integer(&bits[1 + width..]),
        };
        if !base.contains(curve, &point, meter)? {
            return Err(integrity("factor-base witness replay"));
        }
        sum = curve.add(&sum, &point, meter)?;
        out.push(point);
    }
    if &sum != target {
        return Err(integrity("decomposition sum replay"));
    }
    Ok(Some(out))
}

/// Caller-selected finite work policy. It does not assert the paper's coverage
/// hypotheses for tiny curves or arbitrary override parameters.
#[derive(Clone, Debug)]
pub struct Config {
    /// Number of independent, slot-specific factor bases, at least two.
    pub slots: usize,
    /// Override tau; `None` uses a conservative integer version of Lemma 13,
    /// clamped to s in the finite range where its large-size hypotheses fail.
    pub threshold: Option<BigUint>,
    /// Optional fixed prime s in [2p,4p], as permitted by the source. Supplied
    /// proofs are checked by the curve constructor; an uncovered s retains the
    /// exact primality fallback. None preserves the original random selection.
    pub hash_prime: Option<BigUint>,
    /// Maximum fresh-seed trials; reaching it returns a resource error.
    pub trials: usize,
    /// Maximum total number of slot/point columns admitted in one trial.
    pub columns: usize,
}
impl Default for Config {
    fn default() -> Self {
        Self {
            slots: 2,
            threshold: None,
            hash_prime: None,
            trials: 16,
            columns: 4096,
        }
    }
}

impl Config {
    /// Certify an explicitly selected hash modulus without enumerating a base
    /// or building a tensor graph. Does no work when no modulus is specified.
    pub fn validate_hash_prime(&self, curve: &Curve, meter: &mut Meter) -> Result<()> {
        if let Some(prime) = &self.hash_prime {
            FactorBase::new(
                curve,
                prime.clone(),
                BigUint::one(),
                HashSeed {
                    alpha: BigUint::one(),
                    beta: BigUint::zero(),
                },
                meter,
            )?;
        }
        Ok(())
    }

    /// Use Theorem 4's integer slot choice `ceil((log2(b))^(1/4))`, with
    /// a minimum of two in the finite range. Other fields keep explicit defaults.
    /// This is a parameter choice, not a proved runtime guarantee for this code.
    pub fn for_curve(curve: &Curve) -> Self {
        let b = curve.modulus().bits().max(2);
        let logarithm = u64::BITS - (b - 1).leading_zeros();
        let mut slots = 2usize;
        while slots.pow(4) < logarithm as usize {
            slots += 1;
        }
        Self {
            slots,
            ..Self::default()
        }
    }
}

/// A successful group equation in one fixed-seed trial.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Relation {
    /// Uniform public scalar multiplying P.
    pub u: BigUint,
    /// Uniform public scalar multiplying Q.
    pub v: BigUint,
    /// Exactly one nonidentity point per slot.
    pub points: Vec<Point>,
}
json_record!(Relation, required { u, v, points }, optional {});

/// Independently replayable algebraic certificate, version 1.
/// Execution statistics are deliberately excluded: they do not attest history.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Certificate {
    /// Schema version, currently one.
    pub version: u32,
    /// Common certified hash prime.
    pub prime: BigUint,
    /// Common threshold.
    pub threshold: BigUint,
    /// Independent slot seeds for the successful trial.
    pub seeds: Vec<HashSeed>,
    /// N+1 successful relations.
    pub relations: Vec<Relation>,
    /// A nonzero row dependency modulo r, in relation order.
    pub dependency: Vec<BigUint>,
    /// Canonical recovered discrete logarithm.
    pub scalar: BigUint,
}
json_record!(
    Certificate,
    required {
        version,
        prime,
        threshold,
        seeds,
        relations,
        dependency,
        scalar
    },
    optional {}
);

fn threshold(
    curve: &Curve,
    prime: &BigUint,
    config: &Config,
    meter: &mut Meter,
) -> Result<BigUint> {
    if let Some(value) = &config.threshold {
        return Ok(value.clone());
    }
    let root = floor_root(curve.order(), config.slots, meter)?;
    let root = if root.pow(u32::try_from(config.slots).map_err(|_| overflow("root exponent"))?)
        < *curve.order()
    {
        root + BigUint::one()
    } else {
        root
    };
    let expected = root.max(BigUint::from(config.slots) * BigUint::from(10u8));
    Ok((prime * expected)
        .div_ceil(&(curve.order() - BigUint::one()))
        .min(prime.clone()))
}

// Streaming elimination stores at most N pivot rows and their expression in
// the input rows. It selects the first dependency deterministically from M only.
fn row_dependency(
    matrix: &[Vec<BigUint>],
    modulus: &BigUint,
    meter: &mut Meter,
) -> Result<Vec<BigUint>> {
    let rows = matrix.len();
    let columns = matrix.first().map_or(0, Vec::len);
    meter.vector(
        rows.checked_mul(rows + columns)
            .ok_or_else(|| overflow("dependency matrix"))?,
        "dependency matrix",
    )?;
    let mut pivots: BTreeMap<usize, (Vec<BigUint>, Vec<BigUint>)> = BTreeMap::new();
    for (i, original) in matrix.iter().enumerate() {
        if original.len() != columns {
            return Err(invalid("ragged matrix"));
        }
        let mut row = original.clone();
        let mut combination = vec![BigUint::zero(); rows];
        combination[i] = BigUint::one();
        for (&column, (pivot, expression)) in &pivots {
            let coefficient = row[column].clone();
            if coefficient.is_zero() {
                continue;
            }
            for (x, y) in row.iter_mut().zip(pivot) {
                meter.charge(1, "modular row elimination")?;
                *x = (&*x + modulus - &coefficient * y % modulus) % modulus;
            }
            for (x, y) in combination.iter_mut().zip(expression) {
                meter.charge(1, "dependency row elimination")?;
                *x = (&*x + modulus - &coefficient * y % modulus) % modulus;
            }
        }
        if let Some(column) = row.iter().position(|x| !x.is_zero()) {
            let scale = inverse(&row[column], modulus)?;
            for x in row.iter_mut().chain(combination.iter_mut()) {
                *x = &*x * &scale % modulus;
            }
            pivots.insert(column, (row, combination));
        } else {
            return Ok(combination);
        }
    }
    Err(integrity("N+1 rows lacked a dependency"))
}

fn indexed_bases(
    curve: &Curve,
    bases: &[FactorBase],
    rng: &mut impl RandomSource,
    meter: &mut Meter,
) -> Result<Vec<BTreeMap<Point, usize>>> {
    let mut next = 0usize;
    let mut indexes = Vec::with_capacity(bases.len());
    for base in bases {
        let mut index = BTreeMap::new();
        for point in base.enumerate(curve, rng, meter)? {
            index.insert(point, next);
            next = next
                .checked_add(1)
                .ok_or_else(|| overflow("slot columns"))?;
        }
        indexes.push(index);
    }
    Ok(indexes)
}

fn matrix_row(
    relation: &Relation,
    indexes: &[BTreeMap<Point, usize>],
    columns: usize,
) -> Result<Vec<BigUint>> {
    if relation.points.len() != indexes.len() {
        return Err(integrity("relation slot count"));
    }
    let mut row = vec![BigUint::zero(); columns];
    for (point, index) in relation.points.iter().zip(indexes) {
        let column = *index
            .get(point)
            .ok_or_else(|| integrity("relation point missing from slot base"))?;
        row[column] = BigUint::one();
    }
    Ok(row)
}

fn combined_scalars(
    relations: &[Relation],
    dependency: &[BigUint],
    modulus: &BigUint,
) -> (BigUint, BigUint) {
    relations
        .iter()
        .zip(dependency)
        .fold((BigUint::zero(), BigUint::zero()), |(u, v), (row, c)| {
            ((u + c * &row.u) % modulus, (v + c * &row.v) % modulus)
        })
}

/// Run Figure 2 with exact tensor decompositions and native modular elimination.
/// The caller supplies randomness; use `OsRandom` outside repeatable tests.
/// All bounds and exhaustion propagate as `Error::Limit`, never a wrong answer.
pub fn solve(
    curve: &Curve,
    target: &Point,
    config: &Config,
    rng: &mut impl RandomSource,
    counter: &mut Counter,
    meter: &mut Meter,
) -> Result<Certificate> {
    solve_using(
        curve,
        target,
        config,
        rng,
        &mut |curve, bases, point, work| decompose(curve, bases, point, counter, work),
        meter,
    )
}

/// Opt-in relation oracle. It receives only curve, bases and query point, never
/// the hidden random relation labels or their RNG. Every supplied witness is
/// independently checked before it enters the original certificate reduction.
pub fn solve_with_oracle(
    curve: &Curve,
    target: &Point,
    config: &Config,
    rng: &mut impl RandomSource,
    mut oracle: impl FnMut(&Curve, &[FactorBase], &Point, &mut Meter) -> Result<Option<Vec<Point>>>,
    meter: &mut Meter,
) -> Result<Certificate> {
    solve_using(
        curve,
        target,
        config,
        rng,
        &mut |curve, bases, point, work| {
            let answer = oracle(curve, bases, point, work)?;
            if let Some(points) = &answer {
                crate::metrics::phase("relation_check")?;
                if points.len() != bases.len() {
                    return Err(integrity("oracle slot count"));
                }
                let mut sum = Point::Infinity;
                for (base, point) in bases.iter().zip(points) {
                    if !base.contains(curve, point, work)? {
                        return Err(integrity("oracle membership replay"));
                    }
                    sum = curve.add(&sum, point, work)?;
                }
                if &sum != point {
                    return Err(integrity("oracle sum replay"));
                }
            }
            Ok(answer)
        },
        meter,
    )
}

fn solve_using(
    curve: &Curve,
    target: &Point,
    config: &Config,
    rng: &mut impl RandomSource,
    oracle: &mut impl FnMut(&Curve, &[FactorBase], &Point, &mut Meter) -> Result<Option<Vec<Point>>>,
    meter: &mut Meter,
) -> Result<Certificate> {
    if config.slots < 2 || config.trials == 0 || !curve.in_subgroup(target, meter)? {
        return Err(invalid("reduction input"));
    }
    meter.vector(config.slots, "factor-base slots")?;
    config.validate_hash_prime(curve, meter)?;
    // Identity has an immediate, independently checkable certificate.
    if target == &Point::Infinity {
        return Ok(Certificate {
            version: 1,
            prime: BigUint::zero(),
            threshold: BigUint::zero(),
            seeds: vec![],
            relations: vec![],
            dependency: vec![],
            scalar: BigUint::zero(),
        });
    }
    for _ in 0..config.trials {
        crate::metrics::phase("factor_base")?;
        meter.charge(1, "fresh-seed trial")?;
        let prime = if let Some(prime) = &config.hash_prime {
            prime.clone()
        } else {
            hash_prime_by(curve.modulus(), rng, meter, |value, work| {
                curve.certifies_prime(value, work)
            })?
        };
        let tau = threshold(curve, &prime, config, meter)?;
        let mut bases = Vec::with_capacity(config.slots);
        for _ in 0..config.slots {
            let seed = HashSeed {
                alpha: random_below(&(&prime - BigUint::one()), rng, meter)? + BigUint::one(),
                beta: random_below(&prime, rng, meter)?,
            };
            bases.push(FactorBase::new(
                curve,
                prime.clone(),
                tau.clone(),
                seed,
                meter,
            )?);
        }
        let indexes = indexed_bases(curve, &bases, rng, meter)?;
        let columns: usize = indexes.iter().map(BTreeMap::len).sum();
        if columns > config.columns {
            return Err(Error::Limit("factor-base column policy".into()));
        }
        if indexes.iter().any(BTreeMap::is_empty) {
            continue;
        }
        let required = columns
            .checked_add(1)
            .ok_or_else(|| overflow("relation count"))?;
        meter.vector(
            required
                .checked_mul(columns)
                .ok_or_else(|| overflow("relation matrix"))?,
            "relation matrix",
        )?;
        let attempts = required
            .checked_mul(20)
            .ok_or_else(|| overflow("relation attempts"))?;
        let mut relations = Vec::with_capacity(required);
        let mut matrix = Vec::with_capacity(required);
        for _ in 0..attempts {
            crate::metrics::phase("relation_target")?;
            let u = random_below(curve.order(), rng, meter)?;
            let v = random_below(curve.order(), rng, meter)?;
            let left = curve.mul(curve.generator(), &u, meter)?;
            let right = curve.mul(target, &v, meter)?;
            let point = curve.add(&left, &right, meter)?;
            crate::metrics::phase("relation_search")?;
            if let Some(points) = oracle(curve, &bases, &point, meter)? {
                crate::metrics::phase("matrix_build")?;
                let relation = Relation { u, v, points };
                matrix.push(matrix_row(&relation, &indexes, columns)?);
                relations.push(relation);
                if relations.len() == required {
                    break;
                }
            }
        }
        if relations.len() != required {
            continue;
        }
        crate::metrics::phase("linear_algebra")?;
        let dependency = row_dependency(&matrix, curve.order(), meter)?;
        let (u, v) = combined_scalars(&relations, &dependency, curve.order());
        if v.is_zero() {
            continue;
        }
        crate::metrics::phase("recovery_check")?;
        let scalar = (curve.order() - u) * inverse(&v, curve.order())? % curve.order();
        if curve.mul(curve.generator(), &scalar, meter)? != *target {
            return Err(integrity("recovered scalar replay"));
        }
        let certificate = Certificate {
            version: 1,
            prime,
            threshold: tau,
            seeds: bases.into_iter().map(|b| b.seed).collect(),
            relations,
            dependency,
            scalar,
        };
        verify_with_rng(curve, target, &certificate, rng, meter)?;
        return Ok(certificate);
    }
    Err(Error::Limit("fresh-seed trials exhausted".into()))
}

/// Replay all hash memberships, group equations, slot-column cancellations and
/// scalar extraction without using tensor hints, counters, or the solver.
/// OS randomness supplies Tonelli–Shanks nonresidues. Successful extraction
/// gives the same canonical points; work limits still propagate as errors.
pub fn verify(
    curve: &Curve,
    target: &Point,
    certificate: &Certificate,
    meter: &mut Meter,
) -> Result<()> {
    verify_with_rng(
        curve,
        target,
        certificate,
        &mut crate::arithmetic::OsRandom,
        meter,
    )
}

/// Replay using caller-supplied randomness for root extraction. Uniform bytes
/// retain expected-polynomial root extraction; a seeded source is useful for
/// reproducible public fixtures without asserting that runtime hypothesis.
pub fn verify_with_rng(
    curve: &Curve,
    target: &Point,
    certificate: &Certificate,
    rng: &mut impl RandomSource,
    meter: &mut Meter,
) -> Result<()> {
    if certificate.version != 1
        || certificate.scalar >= *curve.order()
        || !curve.in_subgroup(target, meter)?
    {
        return Err(integrity("certificate header"));
    }
    if target == &Point::Infinity {
        if certificate.scalar.is_zero()
            && certificate.prime.is_zero()
            && certificate.threshold.is_zero()
            && certificate.seeds.is_empty()
            && certificate.relations.is_empty()
            && certificate.dependency.is_empty()
        {
            return Ok(());
        }
        return Err(integrity("identity certificate"));
    }
    if certificate.seeds.len() < 2
        || certificate.relations.len() != certificate.dependency.len()
        || certificate.dependency.iter().all(Zero::is_zero)
        || certificate.dependency.iter().any(|c| c >= curve.order())
    {
        return Err(integrity("certificate dimensions or dependency"));
    }
    meter.vector(certificate.relations.len(), "certificate relations")?;
    meter.vector(certificate.seeds.len(), "certificate slots")?;
    let bases = certificate
        .seeds
        .iter()
        .map(|seed| {
            FactorBase::new(
                curve,
                certificate.prime.clone(),
                certificate.threshold.clone(),
                seed.clone(),
                meter,
            )
        })
        .collect::<Result<Vec<_>>>()?;
    // Enumeration is independently reproduced, not trusted from the certificate.
    // Root extraction is deterministic as a point encoding regardless of the
    // nonresidue selected from the caller's randomness.
    let indexes = indexed_bases(curve, &bases, rng, meter)?;
    let columns: usize = indexes.iter().map(BTreeMap::len).sum();
    if certificate.relations.len()
        != columns
            .checked_add(1)
            .ok_or_else(|| overflow("certificate relation count"))?
    {
        return Err(integrity("certificate must contain N+1 rows"));
    }
    let mut cancellation = vec![BigUint::zero(); columns];
    for (relation, coefficient) in certificate.relations.iter().zip(&certificate.dependency) {
        if relation.u >= *curve.order() || relation.v >= *curve.order() {
            return Err(integrity("noncanonical relation scalar"));
        }
        let row = matrix_row(relation, &indexes, columns)?;
        let mut sum = Point::Infinity;
        for (point, base) in relation.points.iter().zip(&bases) {
            if !base.contains(curve, point, meter)? {
                return Err(integrity("relation factor-base membership"));
            }
            sum = curve.add(&sum, point, meter)?;
        }
        let u = curve.mul(curve.generator(), &relation.u, meter)?;
        let v = curve.mul(target, &relation.v, meter)?;
        if sum != curve.add(&u, &v, meter)? {
            return Err(integrity("relation group equation"));
        }
        for (x, y) in cancellation.iter_mut().zip(row) {
            *x = (&*x + coefficient * y) % curve.order();
        }
    }
    if cancellation.iter().any(|x| !x.is_zero()) {
        return Err(integrity("slot-specific column cancellation"));
    }
    let (u, v) = combined_scalars(
        &certificate.relations,
        &certificate.dependency,
        curve.order(),
    );
    if v.is_zero()
        || (&certificate.scalar * &v + u) % curve.order() != BigUint::zero()
        || curve.mul(curve.generator(), &certificate.scalar, meter)? != *target
    {
        return Err(integrity("certificate extraction"));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::arithmetic::Seeded;
    use crate::contraction::Backend;
    use crate::Limits;

    #[test]
    fn inverse_hash_enumeration_matches_independent_subgroup_scan() {
        let mut meter = Meter::new(Limits::default());
        let curve = crate::curve::tiny(&mut meter);
        let mut rng = Seeded(17);
        for alpha in 1..11u8 {
            for tau in [1u8, 3, 11] {
                let base = FactorBase::new(
                    &curve,
                    11u8.into(),
                    tau.into(),
                    HashSeed {
                        alpha: alpha.into(),
                        beta: 7u8.into(),
                    },
                    &mut meter,
                )
                .unwrap();
                let mut expected = Vec::new();
                for k in 1..7u8 {
                    let point = curve.mul(curve.generator(), &k.into(), &mut meter).unwrap();
                    if base.contains(&curve, &point, &mut meter).unwrap() {
                        expected.push(point);
                    }
                }
                expected.sort();
                assert_eq!(
                    base.enumerate(&curve, &mut rng, &mut meter).unwrap(),
                    expected
                );
            }
        }
    }

    #[test]
    fn tensor_relation_pipeline_recovers_and_replays_without_scalar_leakage() {
        let mut meter = Meter::new(Limits {
            steps: 2_000_000_000,
            ..Limits::default()
        });
        let curve = crate::curve::tiny(&mut meter);
        let target = curve
            .mul(curve.generator(), &4u8.into(), &mut meter)
            .unwrap();
        let mut counter = Counter::default();
        let certificate = solve(
            &curve,
            &target,
            &Config::default(),
            &mut Seeded(1),
            &mut counter,
            &mut meter,
        )
        .unwrap();
        assert_eq!(certificate.scalar, 4u8.into());
        assert_eq!(certificate.relations.len(), 13);
        assert_eq!(counter.statistics.last_backend, Some(Backend::Functional));
        assert_eq!(counter.statistics.contractions, 0);
        assert!(counter.statistics.witness_searches >= 13);
        // The original count-based implementation remains selectable. Require
        // the entire seeded certificate, not only the scalar, to stay identical.
        let mut reference = Counter {
            functional_witnesses: false,
            functional_pruning: false,
            ..Counter::default()
        };
        let reference_certificate = solve(
            &curve,
            &target,
            &Config::default(),
            &mut Seeded(1),
            &mut reference,
            &mut meter,
        )
        .unwrap();
        assert_eq!(reference_certificate, certificate);
        assert!(reference.statistics.contractions > 13);
        verify(&curve, &target, &certificate, &mut meter).unwrap();
        struct CountedRandom {
            source: Seeded,
            calls: usize,
        }
        impl RandomSource for CountedRandom {
            fn fill(&mut self, bytes: &mut [u8]) -> Result<()> {
                self.calls += 1;
                self.source.fill(bytes)
            }
        }
        let mut replay_rng = CountedRandom {
            source: Seeded(17),
            calls: 0,
        };
        verify_with_rng(&curve, &target, &certificate, &mut replay_rng, &mut meter).unwrap();
        assert!(
            replay_rng.calls > 0,
            "replay must use the supplied entropy source"
        );
        let bytes = serde_json::to_vec(&certificate).unwrap();
        let restored: Certificate = serde_json::from_slice(&bytes).unwrap();
        assert_eq!(restored, certificate);
        let mut broken = certificate.clone();
        broken.relations[0].u = (&broken.relations[0].u + BigUint::one()) % curve.order();
        assert!(verify(&curve, &target, &broken, &mut meter).is_err());
        let mut broken = certificate.clone();
        broken.scalar = 5u8.into();
        assert!(verify(&curve, &target, &broken, &mut meter).is_err());
        let mut broken = certificate;
        broken.dependency.fill(BigUint::zero());
        assert!(verify(&curve, &target, &broken, &mut meter).is_err());
    }

    #[test]
    fn cofactor_tensor_projection_finds_only_subgroup_points() {
        let mut meter = Meter::new(Limits {
            steps: 2_000_000_000,
            ..Limits::default()
        });
        let curve = Curve::with_cofactor(
            5u8.into(),
            0u8.into(),
            1u8.into(),
            3u8.into(),
            2u8.into(),
            Point::Affine {
                x: 0u8.into(),
                y: 1u8.into(),
            },
            &mut meter,
        )
        .unwrap();
        let base = FactorBase::new(
            &curve,
            11u8.into(),
            11u8.into(),
            HashSeed {
                alpha: 3u8.into(),
                beta: 2u8.into(),
            },
            &mut meter,
        )
        .unwrap();
        assert_eq!(
            base.enumerate(&curve, &mut Seeded(2), &mut meter)
                .unwrap()
                .len(),
            2
        );
        let bases = vec![base.clone(), base];
        let points = decompose(
            &curve,
            &bases,
            curve.generator(),
            &mut Counter::default(),
            &mut meter,
        )
        .unwrap()
        .unwrap();
        assert!(points
            .iter()
            .all(|p| curve.in_subgroup(p, &mut meter).unwrap()));
        assert_eq!(
            curve.add(&points[0], &points[1], &mut meter).unwrap(),
            *curve.generator()
        );
    }

    #[test]
    fn exhausted_tensor_work_is_unknown_and_identity_has_an_exact_certificate() {
        let mut meter = Meter::new(Limits::default());
        let curve = crate::curve::tiny(&mut meter);
        let certificate = solve(
            &curve,
            &Point::Infinity,
            &Config::default(),
            &mut Seeded(2),
            &mut Counter::default(),
            &mut meter,
        )
        .unwrap();
        verify(&curve, &Point::Infinity, &certificate, &mut meter).unwrap();
        let mut exhausted = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            solve(
                &curve,
                curve.generator(),
                &Config::default(),
                &mut Seeded(2),
                &mut Counter::default(),
                &mut exhausted
            ),
            Err(Error::Limit(_))
        ));
    }

    #[test]
    fn factor_base_enumeration_reuses_square_root_setup() {
        struct Nonresidue {
            calls: usize,
        }
        impl RandomSource for Nonresidue {
            fn fill(&mut self, bytes: &mut [u8]) -> Result<()> {
                self.calls += 1;
                bytes.fill(3); // 3 is a quadratic nonresidue modulo 17.
                Ok(())
            }
        }
        let mut meter = Meter::new(Limits::default());
        let curve = Curve::new(
            17u8.into(),
            2u8.into(),
            2u8.into(),
            19u8.into(),
            Point::Affine {
                x: 5u8.into(),
                y: 1u8.into(),
            },
            &mut meter,
        )
        .unwrap();
        let base = FactorBase::new(
            &curve,
            37u8.into(),
            37u8.into(),
            HashSeed {
                alpha: 1u8.into(),
                beta: 0u8.into(),
            },
            &mut meter,
        )
        .unwrap();
        let mut expected: Vec<_> = (1u8..19)
            .map(|scalar| {
                curve
                    .mul(curve.generator(), &scalar.into(), &mut meter)
                    .unwrap()
            })
            .collect();
        expected.sort();
        let mut one_shot = Nonresidue { calls: 0 };
        let mut decoded = Vec::new();
        for encoding in 0u8..34 {
            if let Some(point) = curve
                .decode(&encoding.into(), &mut one_shot, &mut meter)
                .unwrap()
            {
                decoded.push(point);
            }
        }
        decoded.sort();
        assert_eq!(decoded, expected);
        assert_eq!(one_shot.calls, 18);
        let mut batched = Nonresidue { calls: 0 };
        assert_eq!(
            base.enumerate(&curve, &mut batched, &mut meter).unwrap(),
            expected
        );
        assert_eq!(batched.calls, 1, "one setup must serve the entire base");
    }
}
