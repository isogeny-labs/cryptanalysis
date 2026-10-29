//! Appendix D.4: parameter guards, tapered jets, and depth-first recursion.

use super::deformation::{self, Cauchy, Mode};
use super::packing::{self, Packing};
use super::{brute_tensor, event, Bipartite, Statistics};
use crate::arithmetic::{floor_root, inverse, residue};
use crate::ring::{interpolate, polynomial_mul, Element, Ring};
use crate::{integrity, invalid, overflow, BigInt, BigUint, Meter, Result};
use num_integer::Integer;
use num_traits::{One, ToPrimitive, Zero};
use std::collections::BTreeSet;

// Ratio is generic over our workspace's integer version; enabling its optional
// BigInt alias would introduce a second integer version into cryptanalysis.
type BigRational = num_rational::Ratio<BigInt>;

#[derive(Clone, Debug)]
pub(super) struct Parameters {
    pub radix: usize,
    pub u: usize,
    pub a: usize,
    pub length: usize,
    pub array: usize,
}

pub(super) struct Setup {
    pub lambda: usize,
    pub leaf_size: usize,
    pub delta: usize,
}
impl Setup {
    pub fn new(size: usize, maximum_degree: usize, meter: &mut Meter) -> Result<Self> {
        if size < 2 {
            return Err(invalid("contraction size parameter"));
        }
        let lambda = (usize::BITS - (size - 1).leading_zeros()) as usize;
        let sqrt = floor_root(&BigUint::from(lambda), 2, meter)?
            .to_usize()
            .ok_or_else(|| overflow("leaf cutoff"))?
            .max(1);
        let ninth_power = BigUint::from(size).pow(9);
        let floor = floor_root(&ninth_power, 10, meter)?;
        let delta = (&floor + BigUint::from(u8::from(floor.pow(10) != ninth_power)))
            .to_usize()
            .ok_or_else(|| overflow("degree cap"))?;
        // A violated degree hypothesis is an exact-fallback case, not a false
        // assertion that the recursive complexity theorem applies.
        let delta = if maximum_degree > delta { 0 } else { delta };
        Ok(Self {
            lambda,
            leaf_size: size / sqrt,
            delta,
        })
    }
    pub fn parameters(&self, edges: usize, depth: usize) -> Result<Option<Parameters>> {
        if edges <= self.leaf_size || self.delta == 0 {
            return Ok(None);
        }
        // epsilon = 1/(128*1024), exactly as in (D.4).
        let root_u = self.lambda / (128 * 1024);
        let u = root_u.checked_shr(depth as u32).unwrap_or(0);
        if u == 0 {
            return Ok(None);
        }
        let mut sum = 0usize;
        for level in 0..=depth {
            sum = sum
                .checked_add(root_u.checked_shr(level as u32).unwrap_or(0))
                .ok_or_else(|| overflow("recursive scale"))?;
        }
        let a = sum
            .checked_mul(2)
            .ok_or_else(|| overflow("recursive scale"))?;
        let length = 1usize
            .checked_shl(u32::try_from(a).map_err(|_| overflow("packet exponent"))?)
            .ok_or_else(|| overflow("packet length"))?;
        let array = 64usize
            .checked_pow(u32::try_from(2 * a).map_err(|_| overflow("packet array"))?)
            .ok_or_else(|| overflow("packet array"))?;
        let m = BigUint::from(edges);
        let d = BigUint::from(array);
        if u > a
            || u > edges
            || m < (BigUint::from(2u8) * &d * &d * BigUint::from(self.delta))
            || m < (BigUint::from(length) * &d)
            || BigUint::from(2 * length) > BigUint::from(self.delta)
        {
            return Ok(None);
        }
        Ok(Some(Parameters {
            radix: 64,
            u,
            a,
            length,
            array,
        }))
    }
}

fn multiplicity(edges: usize, parameters: &Parameters, t: i64) -> Result<usize> {
    if t == 0 {
        return Ok(0);
    }
    let i = deformation::valuation(t);
    if i >= parameters.u {
        return Ok(0);
    }
    let h = edges
        .checked_mul(3)
        .ok_or_else(|| overflow("Hermite multiplicity"))?
        .div_ceil(parameters.u);
    h.checked_mul(parameters.u - i)
        .ok_or_else(|| overflow("Hermite multiplicity"))
}

fn child_precision(
    edges: usize,
    parameters: &Parameters,
    t: i64,
    precision: usize,
) -> Result<usize> {
    let i = deformation::valuation(t);
    if i >= parameters.u {
        return Err(invalid("inactive Hermite node"));
    }
    let h = edges
        .checked_mul(3)
        .ok_or_else(|| overflow("taper width"))?
        .div_ceil(parameters.u);
    let d = parameters.length >> i;
    let node_loss = h
        .checked_mul(d)
        .and_then(|n| n.checked_mul(8))
        .ok_or_else(|| overflow("Hermite node precision"))?;
    let evaluation_loss = edges
        .checked_mul(parameters.a + 1)
        .and_then(|n| n.checked_mul(8))
        .ok_or_else(|| overflow("Hermite evaluation precision"))?;
    precision
        .checked_add(node_loss)
        .and_then(|n| n.checked_add(evaluation_loss))
        .ok_or_else(|| overflow("Hermite precision"))
}

struct Jet {
    t: i64,
    ring: Ring,
    coefficients: Vec<Element>,
}

fn rational_power(
    mut base: BigRational,
    mut exponent: usize,
    meter: &mut Meter,
) -> Result<BigRational> {
    let mut out = BigRational::one();
    while exponent != 0 {
        meter.charge(1, "rational Hermite power")?;
        if exponent & 1 != 0 {
            out *= &base;
        }
        exponent >>= 1;
        if exponent != 0 {
            base = &base * &base;
        }
        for value in [&out, &base] {
            meter.bits(value.numer().bits() as usize, "Hermite rational numerator")?;
            meter.bits(
                value.denom().bits() as usize,
                "Hermite rational denominator",
            )?;
        }
    }
    Ok(out)
}

// Ordinary z-series coefficients of (1 + ratio*z)^power, truncated at limit.
fn binomial_series(
    ratio: &Element,
    power: usize,
    limit: usize,
    ring: &Ring,
    meter: &mut Meter,
) -> Result<Vec<Element>> {
    let mut out = vec![ring.zero(); limit];
    let mut binomial = BigUint::one();
    let mut ratio_power = ring.one();
    for j in 0..limit.min(power + 1) {
        meter.charge(1, "Hermite binomial series")?;
        out[j] = ring.mul(&ring.integer(&binomial), &ratio_power, meter)?;
        if j < power {
            binomial = binomial * BigUint::from(power - j) / BigUint::from(j + 1);
            meter.bits(binomial.bits() as usize, "binomial integer width")?;
            ratio_power = ring.mul(&ratio_power, ratio, meter)?;
        }
    }
    Ok(out)
}

fn recover(
    jets: &[Jet],
    edges: usize,
    parameters: &Parameters,
    ring: &Ring,
    meter: &mut Meter,
) -> Result<Element> {
    let points = deformation::grid(parameters, meter)?;
    let mut expected = BTreeSet::new();
    for &t in &points {
        if multiplicity(edges, parameters, t)? > 0 {
            expected.insert(t);
        }
    }
    let supplied: BTreeSet<_> = jets.iter().map(|jet| jet.t).collect();
    if expected != supplied || supplied.len() != jets.len() {
        return Err(invalid("incomplete or duplicate tapered jets"));
    }
    let mut result = vec![BigRational::zero(); ring.degree()];
    let alpha = BigInt::one() << (parameters.a + 1);
    for jet in jets {
        let qt = multiplicity(edges, parameters, jet.t)?;
        if jet.coefficients.len() != qt
            || jet.ring.precision() != child_precision(edges, parameters, jet.t, ring.precision())?
        {
            return Err(invalid("tapered jet shape or precision"));
        }
        let mut e_zero = BigRational::one();
        let mut e_series = vec![jet.ring.zero(); qt];
        e_series[0] = jet.ring.one();
        for &q in &points {
            if q == 0 || q == jet.t {
                continue;
            }
            let qq = multiplicity(edges, parameters, q)?;
            if qq == 0 {
                continue;
            }
            let fraction = BigRational::new(BigInt::from(-q), BigInt::from(jet.t - q));
            e_zero *= rational_power(fraction, qq, meter)?;
            let v = deformation::valuation(jet.t - q);
            if v > parameters.a {
                return Err(integrity("Hermite grid valuation"));
            }
            let odd = BigInt::from(jet.t - q) >> v;
            let unit_inverse = jet.ring.inverse(&jet.ring.signed(&odd), meter)?;
            let ratio = jet.ring.shift(&unit_inverse, parameters.a + 1 - v)?;
            let factor = binomial_series(&ratio, qq, qt, &jet.ring, meter)?;
            e_series = polynomial_mul(&e_series, &factor, qt, &jet.ring, meter)?;
        }
        let mut reciprocal = vec![jet.ring.zero(); qt];
        reciprocal[0] = jet.ring.one();
        for k in 1..qt {
            let mut sum = jet.ring.zero();
            for j in 1..=k {
                let product = jet.ring.mul(&e_series[j], &reciprocal[k - j], meter)?;
                sum = jet.ring.add(&sum, &product, meter)?;
            }
            reciprocal[k] = jet.ring.sub(&jet.ring.zero(), &sum, meter)?;
        }
        let quotient = polynomial_mul(&jet.coefficients, &reciprocal, qt, &jet.ring, meter)?;
        let ratio = BigRational::new(BigInt::from(-jet.t), alpha.clone());
        let mut multiplier = e_zero;
        for coefficient in quotient {
            for (coordinate, value) in result.iter_mut().zip(coefficient.coordinates()) {
                meter.charge(1, "rational Hermite reconstruction")?;
                *coordinate += &multiplier * BigRational::from_integer(BigInt::from(value.clone()));
                meter.bits(
                    coordinate.numer().bits() as usize,
                    "Hermite common numerator",
                )?;
                meter.bits(
                    coordinate.denom().bits() as usize,
                    "Hermite common denominator",
                )?;
            }
            multiplier *= &ratio;
        }
    }
    let mut coordinates = Vec::with_capacity(ring.degree());
    for value in result {
        if value.denom().is_even() {
            return Err(integrity("Hermite recovery is not 2-adically integral"));
        }
        let numerator = residue(value.numer(), ring.modulus());
        let denominator = value
            .denom()
            .to_biguint()
            .ok_or_else(|| integrity("Hermite denominator sign"))?;
        coordinates.push(numerator * inverse(&denominator, ring.modulus())? % ring.modulus());
    }
    Ok(Element(coordinates))
}

fn next_tuple(
    beta: &mut [usize],
    modes: &[Mode],
    group_usage: &mut [usize],
    group_bounds: &[usize],
    weight: &mut usize,
    precision: usize,
    radix: usize,
    meter: &mut Meter,
) -> Result<bool> {
    for (i, mode) in modes.iter().enumerate() {
        meter.charge(1, "weighted mode enumeration")?;
        let group = mode.packet * radix + mode.target;
        if mode.weight < precision - *weight && group_usage[group] < group_bounds[group] {
            beta[i] += 1;
            *weight += mode.weight;
            group_usage[group] += 1;
            return Ok(true);
        }
        *weight -= beta[i] * mode.weight;
        group_usage[group] -= beta[i];
        beta[i] = 0;
    }
    Ok(false)
}

fn evaluate_at(
    graph: &Bipartite,
    packing: &Packing,
    parameters: &Parameters,
    t: i64,
    z: &Element,
    ring: &Ring,
    strict: bool,
    delta: usize,
    evaluate_child: &mut impl FnMut(&Bipartite, &Ring, &mut Meter) -> Result<Element>,
    meter: &mut Meter,
) -> Result<Element> {
    let coordinate = deformation::valuation(t);
    let kernel = Cauchy::new(parameters, t, z, ring, meter)?;
    let modes = deformation::modes(graph, packing, coordinate, parameters, &kernel, meter)?;
    let groups = packing
        .packets
        .len()
        .checked_mul(parameters.radix)
        .ok_or_else(|| overflow("mode degree bounds"))?;
    meter.vector(groups, "mode group degree bounds")?;
    let mut bounds = vec![0usize; groups];
    for (p, packet) in packing.packets.iter().enumerate() {
        for &edge in packet.slots.iter().flatten() {
            let group = packing::digit(
                packing.row_labels[graph.edges[edge].left.0],
                coordinate,
                parameters.radix,
            );
            bounds[p * parameters.radix + group] += 1;
        }
    }
    let mut usage = vec![0usize; groups];
    let mut beta = vec![0usize; modes.len()];
    let mut weight = 0usize;
    let mut total = ring.zero();
    loop {
        meter.charge(1, "mode monomial")?;
        let mut product = ring.one();
        for group in 0..parameters.radix {
            let child = deformation::child(
                graph, packing, coordinate, parameters, &kernel, &modes, &beta, group, meter,
            )?;
            if strict
                && (BigUint::from(child.edges.len()) * BigUint::from(8u8)
                    > BigUint::from(graph.edges.len())
                    || child
                        .left
                        .iter()
                        .chain(&child.right)
                        .any(|v| v.edges.len() > delta))
            {
                return Err(integrity("recursive child failed edge/degree shrinkage"));
            }
            let value = evaluate_child(&child, ring, meter)?;
            product = ring.mul(&product, &value, meter)?;
            if product.is_zero() {
                break;
            }
        }
        total = ring.add(&total, &product, meter)?;
        if !next_tuple(
            &mut beta,
            &modes,
            &mut usage,
            &bounds,
            &mut weight,
            ring.precision(),
            parameters.radix,
            meter,
        )? {
            break;
        }
    }
    Ok(total)
}

fn active(
    graph: &Bipartite,
    ring: &Ring,
    parameters: &Parameters,
    packing: &Packing,
    strict: bool,
    delta: usize,
    evaluate_child: &mut impl FnMut(&Bipartite, &Ring, &mut Meter) -> Result<Element>,
    meter: &mut Meter,
) -> Result<Element> {
    let edges = graph.edges.len();
    if parameters.u == 0 || parameters.u > parameters.a || parameters.u > edges {
        return Err(invalid("active recursion parameters"));
    }
    let degree = edges
        .checked_mul(2 * parameters.length - 1)
        .ok_or_else(|| overflow("deformation degree"))?;
    let points = degree
        .checked_add(1)
        .ok_or_else(|| overflow("interpolation point count"))?;
    meter.vector(points, "deformation interpolation points")?;
    if BigUint::from(points) > (BigUint::one() << ring.degree()) {
        return Err(invalid("not enough residue-distinct interpolation points"));
    }
    let mut jets = Vec::new();
    let mut jet_storage = 0usize;
    for t in deformation::grid(parameters, meter)? {
        let qt = multiplicity(edges, parameters, t)?;
        if qt == 0 {
            continue;
        }
        let precision = child_precision(edges, parameters, t, ring.precision())?;
        let local_ring = ring.at_precision(precision, meter)?;
        let mut nodes = Vec::with_capacity(points);
        let mut values = Vec::with_capacity(points);
        for j in 0..points {
            let z = local_ring.point(&BigUint::from(j))?;
            let value = evaluate_at(
                graph,
                packing,
                parameters,
                t,
                &z,
                &local_ring,
                strict,
                delta,
                evaluate_child,
                meter,
            )?;
            nodes.push(z);
            values.push(value);
        }
        let mut coefficients = interpolate(&nodes, &values, &local_ring, meter)?;
        coefficients.resize(qt, local_ring.zero());
        coefficients.truncate(qt);
        jet_storage = jet_storage
            .checked_add(qt)
            .ok_or_else(|| overflow("retained tapered jets"))?;
        meter.vector(jet_storage, "retained tapered jets")?;
        jets.push(Jet {
            t,
            ring: local_ring,
            coefficients,
        });
    }
    recover(&jets, edges, parameters, ring, meter)
}

pub(super) fn contract(
    graph: &Bipartite,
    ring: &Ring,
    setup: &Setup,
    depth: usize,
    statistics: &mut Statistics,
    meter: &mut Meter,
) -> Result<Element> {
    event(&mut statistics.recursive_calls, "recursive call count")?;
    let Some(parameters) = setup.parameters(graph.edges.len(), depth)? else {
        return brute_tensor(graph, ring, statistics, meter);
    };
    let packing = packing::pack(graph, &parameters, setup.delta, meter)?;
    active(
        graph,
        ring,
        &parameters,
        &packing,
        true,
        setup.delta,
        &mut |child, child_ring, work| {
            contract(child, child_ring, setup, depth + 1, statistics, work)
        },
        meter,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::contraction::{Edge, Tensor, TensorKind, TensorVertex};
    use crate::network::FnPredicate;
    use crate::ring::polynomial_value;
    use crate::Limits;
    use std::sync::Arc;
    fn parameters() -> Parameters {
        Parameters {
            radix: 2,
            u: 1,
            a: 2,
            length: 4,
            array: 16,
        }
    }

    #[test]
    fn tapered_hermite_recovers_the_constant_without_rounding() {
        let mut meter = Meter::new(Limits::default());
        let parameters = parameters();
        let ring = Ring::new(4, 7, &mut meter).unwrap();
        let coefficients: Vec<_> = (0..8u8)
            .map(|i| ring.integer(&BigUint::from(3 * i + 1)))
            .collect();
        let mut jets = Vec::new();
        for t in deformation::grid(&parameters, &meter).unwrap() {
            let qt = multiplicity(1, &parameters, t).unwrap();
            if qt == 0 {
                continue;
            }
            let local = ring
                .at_precision(child_precision(1, &parameters, t, 7).unwrap(), &meter)
                .unwrap();
            let points: Vec<_> = (0..8usize)
                .map(|j| local.point(&j.into()).unwrap())
                .collect();
            let actual_coefficients: Vec<_> = coefficients
                .iter()
                .map(|c| local.lift(c).unwrap())
                .collect();
            let mut values = Vec::new();
            for z in &points {
                let shifted = local.shift(z, 3).unwrap();
                let argument = local
                    .add(&local.signed(&BigInt::from(t)), &shifted, &mut meter)
                    .unwrap();
                values.push(
                    polynomial_value(&actual_coefficients, &argument, &local, &mut meter).unwrap(),
                );
            }
            let mut jet = interpolate(&points, &values, &local, &mut meter).unwrap();
            jet.truncate(qt);
            jets.push(Jet {
                t,
                ring: local,
                coefficients: jet,
            });
        }
        assert_eq!(
            recover(&jets, 1, &parameters, &ring, &mut meter).unwrap(),
            coefficients[0]
        );
        jets.pop();
        assert!(recover(&jets, 1, &parameters, &ring, &mut meter).is_err());
    }

    #[test]
    fn weighted_enumeration_has_no_missing_or_repeated_monomials() {
        let mut meter = Meter::new(Limits::default());
        let modes: Vec<_> = [1usize, 2, 3]
            .iter()
            .map(|&weight| Mode {
                packet: 0,
                source: 1,
                target: 0,
                weight,
                rows: vec![],
                columns: vec![],
            })
            .collect();
        let mut beta = vec![0; 3];
        let mut usage = vec![0; 2];
        let bounds = [2, 0];
        let mut weight = 0;
        let mut actual = BTreeSet::new();
        loop {
            assert!(actual.insert(beta.clone()));
            if !next_tuple(
                &mut beta,
                &modes,
                &mut usage,
                &bounds,
                &mut weight,
                5,
                2,
                &mut meter,
            )
            .unwrap()
            {
                break;
            }
        }
        let mut expected = BTreeSet::new();
        for a in 0..=2 {
            for b in 0..=2 {
                for c in 0..=2 {
                    if a + b + c <= 2 && a + 2 * b + 3 * c < 5 {
                        expected.insert(vec![a, b, c]);
                    }
                }
            }
        }
        assert_eq!(actual, expected);
    }

    #[test]
    fn forced_small_packet_recursion_matches_independent_direct_contraction() {
        // Diagnostic constants deliberately bypass the astronomical asymptotic
        // admission range. The exact kernel/child/recovery implementation is
        // unchanged; no performance statement follows from this control.
        let mut meter = Meter::new(Limits {
            steps: 1_000_000_000,
            ..Limits::default()
        });
        let parameters = parameters();
        for (left_table, right_table) in [(3u8, 3u8), (2, 2), (1, 2), (0, 3)] {
            for (row_label, column_label) in [(0, 3), (3, 0)] {
                let tensor = |table: u8| {
                    Arc::new(Tensor {
                        creation_precision: 3,
                        kind: TensorKind::Boolean(Arc::new(FnPredicate::new(1, move |bits, _| {
                            Ok(table & (1 << u8::from(bits[0])) != 0)
                        }))),
                    })
                };
                let graph = Bipartite {
                    left: vec![TensorVertex {
                        tensor: tensor(left_table),
                        edges: vec![0],
                    }],
                    right: vec![TensorVertex {
                        tensor: tensor(right_table),
                        edges: vec![0],
                    }],
                    edges: vec![Edge {
                        left: (0, 0),
                        right: (0, 0),
                    }],
                };
                let ring = Ring::new(4, 3, &mut meter).unwrap();
                let packing = packing::pack_labels(
                    &graph,
                    &parameters,
                    vec![row_label],
                    vec![column_label],
                    false,
                    &mut meter,
                )
                .unwrap();
                let expected =
                    brute_tensor(&graph, &ring, &mut Statistics::default(), &mut meter).unwrap();
                let mut statistics = Statistics::default();
                let answer = active(
                    &graph,
                    &ring,
                    &parameters,
                    &packing,
                    false,
                    usize::MAX,
                    &mut |child, ring, meter| brute_tensor(child, ring, &mut statistics, meter),
                    &mut meter,
                )
                .unwrap();
                assert_eq!(
                    answer, expected,
                    "tables={left_table}/{right_table}, labels={row_label}/{column_label}"
                );
            }
        }
    }
}
