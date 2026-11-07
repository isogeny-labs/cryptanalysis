//! Opt-in selector-domain witness search. Generic enumeration/propagation,
//! not the manuscript's asymptotic contractor and not a sub-rho claim.

use crate::arithmetic::{inverse, Seeded};
use crate::curve::{Curve, Point};
use crate::encoding::Encoder;
use crate::network::Network;
use crate::reduction::FactorBase;
use crate::{integrity, invalid, overflow, BigUint, Meter, Result};
use num_traits::{One, Zero};
use std::collections::BTreeMap;

/// Exact group operations needed by the finite-size witness engine.
pub trait Group {
    /// Canonical, ordered group point representation.
    type Point: Clone + Ord;
    /// The identity.
    fn identity(&self) -> Self::Point;
    /// Check canonical membership in the intended subgroup.
    fn valid(&self, point: &Self::Point, meter: &mut Meter) -> Result<bool>;
    /// Checked addition.
    fn add(&self, a: &Self::Point, b: &Self::Point, meter: &mut Meter) -> Result<Self::Point>;
    /// Checked negation.
    fn negate(&self, a: &Self::Point, meter: &mut Meter) -> Result<Self::Point>;
}

impl Group for Curve {
    type Point = Point;
    fn identity(&self) -> Point {
        Point::Infinity
    }
    fn valid(&self, point: &Point, meter: &mut Meter) -> Result<bool> {
        self.in_subgroup(point, meter)
    }
    fn add(&self, a: &Point, b: &Point, meter: &mut Meter) -> Result<Point> {
        self.add(a, b, meter)
    }
    fn negate(&self, a: &Point, meter: &mut Meter) -> Result<Point> {
        meter.charge(1, "finite negation")?;
        self.negate(a)
    }
}

/// A bounded selector parameterization with independently replayable membership.
pub trait Domain<G: Group> {
    /// Validate this domain against the actual group.
    fn validate(&self, group: &G, meter: &mut Meter) -> Result<()>;
    /// Exclusive selector limit, required positive.
    fn limit(&self) -> &BigUint;
    /// Decode one selector; invalid encodings return None, limits return errors.
    fn decode(&self, group: &G, selector: &BigUint, meter: &mut Meter) -> Result<Option<G::Point>>;
    /// Exact independent membership, including canonical/subgroup checks.
    fn contains(&self, group: &G, point: &G::Point, meter: &mut Meter) -> Result<bool>;
}

/// The existing affine hash base, with its inverse computed once per domain.
#[derive(Clone, Debug)]
pub struct PrimeDomain {
    base: FactorBase,
    inverse: BigUint,
}
impl PrimeDomain {
    /// Prepare a previously validated hash base. No base list or root table.
    pub fn new(base: FactorBase, meter: &mut Meter) -> Result<Self> {
        meter.bits(base.prime().bits() as usize, "selector inverse width")?;
        meter.charge(1, "selector inverse preparation")?;
        let inverse = inverse(&base.seed().alpha, base.prime())?;
        Ok(Self { base, inverse })
    }
}
impl Domain<Curve> for PrimeDomain {
    fn validate(&self, group: &Curve, meter: &mut Meter) -> Result<()> {
        meter.bits(self.base.prime().bits() as usize, "selector hash width")?;
        if self.base.prime() < &(group.modulus() << 1)
            || self.base.prime() > &(group.modulus() << 2)
        {
            return Err(invalid("selector base belongs to a different field"));
        }
        Ok(())
    }
    fn limit(&self) -> &BigUint {
        self.base.threshold()
    }
    fn decode(
        &self,
        group: &Curve,
        selector: &BigUint,
        meter: &mut Meter,
    ) -> Result<Option<Point>> {
        if selector >= self.limit() {
            return Err(invalid("selector outside domain"));
        }
        let prime = self.base.prime();
        let code = &self.inverse * ((selector + prime - &self.base.seed().beta) % prime) % prime;
        // Decoder randomness never consumes the relation-label RNG. The canonical
        // parity-selected root is independent of the nonresidue search stream.
        let point = group.decode(&code, &mut Seeded(0x73656c6563746f72), meter)?;
        match point {
            Some(point) if self.base.contains(group, &point, meter)? => Ok(Some(point)),
            _ => Ok(None),
        }
    }
    fn contains(&self, group: &Curve, point: &Point, meter: &mut Meter) -> Result<bool> {
        self.base.contains(group, point, meter)
    }
}

/// Explicit finite-size policy; none of these options changes the default solver.
#[derive(Clone, Debug)]
pub struct Options {
    /// Derive the last point from the group equation instead of enumerating it.
    pub derive_last: bool,
    /// Enumerate smaller domains first, retaining each original slot identity.
    pub smallest_first: bool,
    /// Maximum cached selector decodes within one query; zero disables caching.
    pub cache_entries: usize,
}
impl Default for Options {
    fn default() -> Self {
        Self {
            derive_last: true,
            smallest_first: true,
            cache_entries: 4096,
        }
    }
}

/// Uncalibrated execution diagnostics, never a runtime result.
#[derive(Clone, Debug, Default)]
pub struct Statistics {
    /// Actual selector decoder calls.
    pub decodes: u64,
    /// Reused selector results, including rejected codes.
    pub cache_hits: u64,
    /// Group-equation-derived final candidates checked.
    pub derived_checks: u64,
    /// Complete decompositions independently replayed.
    pub replays: u64,
}
fn event(value: &mut u64) -> Result<()> {
    *value = value
        .checked_add(1)
        .ok_or_else(|| overflow("finite diagnostics"))?;
    Ok(())
}

/// Search one relation. None means the full selected domains were exhausted;
/// resource limits propagate as errors. Domain implementations must be complete.
pub fn decompose<G: Group, D: Domain<G>>(
    group: &G,
    domains: &[D],
    target: &G::Point,
    options: &Options,
    statistics: &mut Statistics,
    meter: &mut Meter,
) -> Result<Option<Vec<G::Point>>> {
    if !(2..=64).contains(&domains.len()) || !group.valid(target, meter)? {
        return Err(invalid("finite decomposition input or slot-depth policy"));
    }
    meter.vector(domains.len(), "finite slots")?;
    for domain in domains {
        domain.validate(group, meter)?;
        if domain.limit().is_zero() {
            return Err(invalid("empty selector interval"));
        }
        meter.bits(domain.limit().bits() as usize, "selector interval width")?;
    }
    let mut order: Vec<_> = (0..domains.len()).collect();
    if options.smallest_first {
        order.sort_by(|&a, &b| domains[a].limit().cmp(domains[b].limit()).then(a.cmp(&b)));
    }
    let mut search = Search {
        group,
        domains,
        target,
        options,
        statistics,
        order,
        points: vec![group.identity(); domains.len()],
        cache: BTreeMap::new(),
    };
    search.visit(0, &group.identity(), meter)
}

struct Search<'a, G: Group, D> {
    group: &'a G,
    domains: &'a [D],
    target: &'a G::Point,
    options: &'a Options,
    statistics: &'a mut Statistics,
    order: Vec<usize>,
    points: Vec<G::Point>,
    cache: BTreeMap<(usize, BigUint), Option<G::Point>>,
}
impl<G: Group, D: Domain<G>> Search<'_, G, D> {
    fn replay(&mut self, meter: &mut Meter) -> Result<Option<Vec<G::Point>>> {
        event(&mut self.statistics.replays)?;
        let mut sum = self.group.identity();
        for (point, domain) in self.points.iter().zip(self.domains) {
            if point == &self.group.identity()
                || !self.group.valid(point, meter)?
                || !domain.contains(self.group, point, meter)?
            {
                return Err(integrity("finite witness membership replay"));
            }
            sum = self.group.add(&sum, point, meter)?;
        }
        if &sum != self.target {
            return Err(integrity("finite witness sum replay"));
        }
        Ok(Some(self.points.clone()))
    }
    fn visit(
        &mut self,
        depth: usize,
        sum: &G::Point,
        meter: &mut Meter,
    ) -> Result<Option<Vec<G::Point>>> {
        meter.charge(1, "selector search prefix")?;
        if depth == self.order.len() {
            return if sum == self.target {
                self.replay(meter)
            } else {
                Ok(None)
            };
        }
        let slot = self.order[depth];
        if self.options.derive_last && depth + 1 == self.order.len() {
            event(&mut self.statistics.derived_checks)?;
            let minus = self.group.negate(sum, meter)?;
            let point = self.group.add(self.target, &minus, meter)?;
            if point != self.group.identity()
                && self.domains[slot].contains(self.group, &point, meter)?
            {
                self.points[slot] = point;
                return self.replay(meter);
            }
            return Ok(None);
        }
        let mut selector = BigUint::zero();
        while &selector < self.domains[slot].limit() {
            meter.charge(1, "selector candidate")?;
            let key = (slot, selector.clone());
            let point = if let Some(point) = self.cache.get(&key) {
                event(&mut self.statistics.cache_hits)?;
                point.clone()
            } else {
                event(&mut self.statistics.decodes)?;
                let point = self.domains[slot].decode(self.group, &selector, meter)?;
                if self.cache.len() < self.options.cache_entries {
                    meter.vector(self.cache.len() + 1, "selector cache")?;
                    self.cache.insert(key, point.clone());
                }
                point
            };
            if let Some(point) = point {
                if point == self.group.identity()
                    || !self.group.valid(&point, meter)?
                    || !self.domains[slot].contains(self.group, &point, meter)?
                {
                    return Err(integrity("selector decoder returned an invalid member"));
                }
                let next = self.group.add(sum, &point, meter)?;
                self.points[slot] = point;
                if let Some(points) = self.visit(depth + 1, &next, meter)? {
                    return Ok(Some(points));
                }
            }
            selector += BigUint::one();
        }
        Ok(None)
    }
}

/// Prime-field adapter suitable for `reduction::solve_with_oracle`.
pub fn prime_decompose(
    curve: &Curve,
    bases: &[FactorBase],
    target: &Point,
    options: &Options,
    statistics: &mut Statistics,
    meter: &mut Meter,
) -> Result<Option<Vec<Point>>> {
    let domains = bases
        .iter()
        .cloned()
        .map(|base| PrimeDomain::new(base, meter))
        .collect::<Result<Vec<_>>>()?;
    decompose(curve, &domains, target, options, statistics, meter)
}

/// Alternative relation graph whose only free point inputs are hash selectors.
/// It counts distinct decoded tuples, not cofactor-projection preimages. The
/// original coordinate graph and its counting semantics remain available.
pub fn selector_network(
    curve: &Curve,
    bases: &[FactorBase],
    target: &Point,
    meter: &mut Meter,
) -> Result<Network> {
    if !(2..=64).contains(&bases.len()) || !curve.in_subgroup(target, meter)? {
        return Err(invalid("selector network target or slots"));
    }
    meter.vector(bases.len(), "selector network slots")?;
    let mut encoder = Encoder::new();
    let mut sum = Encoder::constant_point(curve, &Point::Infinity)?;
    for base in bases {
        let point = encoder.selector_point(curve, base, meter)?;
        encoder.mark_point_interface(&point, meter)?;
        sum = encoder.point_add(curve, &sum, &point, meter)?;
    }
    encoder.assert_point_equal(&sum, &Encoder::constant_point(curve, target)?, meter)?;
    encoder.finish(meter)
}
