//! D.4.3–D.4.6: integral Cauchy kernels and implicit coefficient tensors.

use super::packing::{digit, Packing};
use super::recursive::Parameters;
use super::{Bipartite, Edge, Tensor, TensorKind, TensorVertex};
use crate::ring::{Element, Ring};
use crate::{integrity, invalid, overflow, BigInt, BigUint, Meter, Result};
use num_traits::Zero;
use std::collections::BTreeMap;
use std::sync::Arc;

pub(super) fn valuation(value: i64) -> usize {
    if value == 0 {
        usize::MAX
    } else {
        value.unsigned_abs().trailing_zeros() as usize
    }
}

pub(super) fn grid(parameters: &Parameters, meter: &Meter) -> Result<Vec<i64>> {
    let count = parameters
        .length
        .checked_mul(2)
        .ok_or_else(|| overflow("Hermite grid"))?;
    meter.vector(count, "Hermite grid")?;
    let length = i64::try_from(parameters.length).map_err(|_| overflow("signed Hermite grid"))?;
    i64::try_from(count).map_err(|_| overflow("Hermite grid differences"))?;
    Ok((-length..length).collect())
}

/// A fixed t, z and working precision. Every stored inverse is a unit inverse;
/// no division by a nonunit silently discards significant bits.
pub(super) struct Cauchy {
    pub ring: Ring,
    pub a: usize,
    pub t: i64,
    base: Element,
    numerator_unit: Element,
    factors: BTreeMap<i64, (usize, Element)>,
}
impl Cauchy {
    pub fn new(
        parameters: &Parameters,
        t: i64,
        z: &Element,
        ring: &Ring,
        meter: &mut Meter,
    ) -> Result<Self> {
        let points = grid(parameters, meter)?;
        if !points.contains(&t) {
            return Err(invalid("Cauchy center outside grid"));
        }
        let mut denominator = ring.one();
        let mut denominator_valuation = 0usize;
        for &q in &points {
            if q == 0 {
                continue;
            }
            let v = valuation(q);
            denominator_valuation = denominator_valuation
                .checked_add(v)
                .ok_or_else(|| overflow("Cauchy content"))?;
            let odd = BigInt::from(-q) >> v;
            denominator = ring.mul(&denominator, &ring.signed(&odd), meter)?;
        }
        let inverse_denominator = ring.inverse(&denominator, meter)?;
        let mut product = ring.one();
        let mut numerator_valuation = 0usize;
        let mut factors = BTreeMap::new();
        for &q in &points {
            if q == t {
                continue;
            }
            let v = valuation(t - q);
            if v > parameters.a {
                return Err(integrity("grid difference valuation"));
            }
            numerator_valuation = numerator_valuation
                .checked_add(v)
                .ok_or_else(|| overflow("Cauchy numerator content"))?;
            let odd = BigInt::from(t - q) >> v;
            let scaled_z = ring.shift(z, parameters.a + 1 - v)?;
            let factor = ring.add(&ring.signed(&odd), &scaled_z, meter)?;
            product = ring.mul(&product, &factor, meter)?;
            factors.insert(q, (v, ring.inverse(&factor, meter)?));
        }
        if numerator_valuation != denominator_valuation {
            return Err(integrity(
                "grid derivative content is not translation invariant",
            ));
        }
        let base = ring.mul(&product, &inverse_denominator, meter)?;
        let numerator_unit = ring.mul(&base, z, meter)?;
        Ok(Self {
            ring: ring.clone(),
            a: parameters.a,
            t,
            base,
            numerator_unit,
            factors,
        })
    }

    /// W_xy(t+alpha*z), evaluated by cancelling known contents before inversion.
    pub fn weight(&self, x: usize, y: usize, meter: &mut Meter) -> Result<Element> {
        let x = i64::try_from(x).map_err(|_| overflow("Cauchy row position"))?;
        let y = i64::try_from(y).map_err(|_| overflow("Cauchy column position"))?;
        let q = y - x;
        if q == self.t {
            return Ok(self.base.clone());
        }
        let (v, inverse) = self
            .factors
            .get(&q)
            .ok_or_else(|| integrity("Cauchy difference missing from grid"))?;
        let product = self.ring.mul(&self.numerator_unit, inverse, meter)?;
        self.ring.shift(&product, self.a + 1 - v)
    }

    /// Coefficient of a tile's weight-(b+1) mode in (D.12).
    pub fn mode_coefficient(
        &self,
        x: usize,
        y0: usize,
        i: usize,
        b: usize,
        meter: &mut Meter,
    ) -> Result<Element> {
        let x = i64::try_from(x).map_err(|_| overflow("mode row position"))?;
        let y0 = i64::try_from(y0).map_err(|_| overflow("mode tile position"))?;
        let q = y0 - x;
        let (v, inverse) = self
            .factors
            .get(&q)
            .ok_or_else(|| integrity("crossing denominator equals its center"))?;
        if *v > i || i > self.a {
            return Err(integrity("crossing tile valuation bound"));
        }
        let shift = (i + 1 - v)
            .checked_mul(b)
            .and_then(|n| n.checked_add(self.a + 1 - v))
            .ok_or_else(|| overflow("mode coefficient valuation"))?;
        if shift >= self.ring.precision() {
            return Ok(self.ring.zero());
        }
        let power = self.ring.pow(inverse, b + 1, meter)?;
        let coefficient = self.ring.mul(&self.numerator_unit, &power, meter)?;
        self.ring.shift(&coefficient, shift)
    }
}

pub(super) struct Mode {
    pub packet: usize,
    pub source: usize,
    pub target: usize,
    pub weight: usize,
    pub rows: Vec<(usize, Element)>,
    pub columns: Vec<(usize, BigUint)>,
}

pub(super) fn modes(
    graph: &Bipartite,
    packing: &Packing,
    coordinate: usize,
    parameters: &Parameters,
    kernel: &Cauchy,
    meter: &mut Meter,
) -> Result<Vec<Mode>> {
    let mut out = Vec::new();
    let tiles = 1usize
        .checked_shl((coordinate + 1) as u32)
        .ok_or_else(|| overflow("mode tiles"))?;
    for (packet_id, packet) in packing.packets.iter().enumerate() {
        let (lo, hi) = packet.pairs[coordinate];
        if lo == hi {
            continue;
        }
        for y0 in 0..tiles {
            let (source, target) = if (y0 >> coordinate) & 1 == 0 {
                (hi, lo)
            } else {
                (lo, hi)
            };
            let columns: Vec<_> = (y0..parameters.length)
                .step_by(tiles)
                .filter_map(|y| packet.slots[y].map(|e| (y, e)))
                .collect();
            if columns.is_empty() {
                continue;
            }
            let rows: Vec<_> = packet
                .slots
                .iter()
                .enumerate()
                .filter_map(|(x, &e)| {
                    e.filter(|&e| {
                        digit(
                            packing.row_labels[graph.edges[e].left.0],
                            coordinate,
                            parameters.radix,
                        ) == target
                    })
                    .map(|_| x)
                })
                .collect();
            if rows.is_empty() {
                continue;
            }
            for b in 0..kernel.ring.precision().saturating_sub(1) {
                meter.charge(1, "weighted mode construction")?;
                let mut coefficients = Vec::new();
                for &(y, e) in &columns {
                    if digit(
                        packing.column_labels[graph.edges[e].right.0],
                        coordinate,
                        parameters.radix,
                    ) != source
                    {
                        return Err(integrity("tile column changes its group"));
                    }
                    let j = (y - y0) / tiles;
                    let value = BigUint::from(j).modpow(&BigUint::from(b), kernel.ring.modulus());
                    if !value.is_zero() {
                        coefficients.push((y, value));
                    }
                }
                // An identically zero source form cannot contribute any positive exponent.
                if coefficients.is_empty() {
                    continue;
                }
                let mut row_coefficients = Vec::new();
                for &x in &rows {
                    let coefficient = kernel.mode_coefficient(x, y0, coordinate, b, meter)?;
                    if !coefficient.is_zero() {
                        row_coefficients.push((x, coefficient));
                    }
                }
                if row_coefficients.is_empty() {
                    continue;
                }
                meter.vector(out.len() + 1, "weighted mode variables")?;
                out.push(Mode {
                    packet: packet_id,
                    source,
                    target,
                    weight: b + 1,
                    rows: row_coefficients,
                    columns: coefficients,
                });
            }
        }
    }
    Ok(out)
}

pub(super) struct Incoming {
    exponent: usize,
    coefficients: Vec<Element>,
}
pub(super) struct Outgoing {
    exponent: usize,
    terms: Vec<(usize, BigUint)>,
}

/// Immutable creation-time packet description. It contains no callback to a
/// parent tensor evaluator, so description-evaluation costs do not compose
/// exponentially down the recursion stack.
pub(crate) struct PacketTensor {
    pub ring: Ring,
    local: Vec<Vec<Element>>,
    column_count: usize,
    incoming: Vec<Incoming>,
    outgoing: Vec<Outgoing>,
}
impl PacketTensor {
    pub fn entry(&self, bits: &[bool], meter: &mut Meter) -> Result<Element> {
        let rows = self.local.len();
        if bits.len() != rows + self.column_count {
            return Err(integrity("packet tensor port arity"));
        }
        let mut constants = Vec::with_capacity(rows);
        let mut coefficients: Vec<Vec<Element>> = self
            .incoming
            .iter()
            .map(|_| Vec::with_capacity(rows))
            .collect();
        for row in 0..rows {
            let mut local = self.ring.zero();
            for column in 0..self.column_count {
                if bits[rows + column] {
                    local = self.ring.add(&local, &self.local[row][column], meter)?;
                }
            }
            constants.push(if bits[row] {
                local
            } else {
                self.ring.sub(&self.ring.one(), &local, meter)?
            });
            for (mode, incoming) in self.incoming.iter().enumerate() {
                coefficients[mode].push(if bits[row] {
                    incoming.coefficients[row].clone()
                } else {
                    self.ring
                        .sub(&self.ring.zero(), &incoming.coefficients[row], meter)?
                });
            }
        }
        let mut left: Vec<_> = self.incoming.iter().map(|m| m.exponent).collect();
        let mut remaining: usize = left.iter().sum();
        if remaining > rows {
            return Ok(self.ring.zero());
        }
        let mut sum = self.ring.zero();
        // Depth-first coefficient extraction with explicit polynomial-space state.
        let mut choices = vec![0usize; rows];
        let mut chosen = vec![0usize; rows];
        let mut prefix = vec![self.ring.one(); rows + 1];
        let mut row = 0;
        loop {
            if row == rows {
                if remaining == 0 {
                    sum = self.ring.add(&sum, &prefix[row], meter)?;
                }
                if row == 0 {
                    break;
                }
                row -= 1;
                if chosen[row] != 0 {
                    left[chosen[row] - 1] += 1;
                    remaining += 1;
                }
                continue;
            }
            let mut advanced = false;
            while choices[row] <= self.incoming.len() {
                meter.charge(1, "packet coefficient extraction")?;
                let choice = choices[row];
                choices[row] += 1;
                let factor = if choice == 0 {
                    &constants[row]
                } else {
                    if left[choice - 1] == 0 {
                        continue;
                    }
                    &coefficients[choice - 1][row]
                };
                if factor.is_zero() {
                    continue;
                }
                if choice != 0 {
                    left[choice - 1] -= 1;
                    remaining -= 1;
                }
                if remaining > rows - row - 1 {
                    if choice != 0 {
                        left[choice - 1] += 1;
                        remaining += 1;
                    }
                    continue;
                }
                prefix[row + 1] = self.ring.mul(&prefix[row], factor, meter)?;
                chosen[row] = choice;
                row += 1;
                if row < rows {
                    choices[row] = 0;
                }
                advanced = true;
                break;
            }
            if advanced {
                continue;
            }
            if row == 0 {
                break;
            }
            row -= 1;
            if chosen[row] != 0 {
                left[chosen[row] - 1] += 1;
                remaining += 1;
            }
        }
        if sum.is_zero() {
            return Ok(sum);
        }
        for mode in &self.outgoing {
            let mut value = BigUint::zero();
            for &(column, ref coefficient) in &mode.terms {
                if bits[rows + column] {
                    value = (value + coefficient) % self.ring.modulus();
                }
            }
            let power = self
                .ring
                .pow(&self.ring.integer(&value), mode.exponent, meter)?;
            sum = self.ring.mul(&sum, &power, meter)?;
            if sum.is_zero() {
                break;
            }
        }
        Ok(sum)
    }
}

/// Build the group child with all old vertices on its left and packet vertices
/// on its right. Old port order and old tensor creation precision are retained.
pub(super) fn child(
    graph: &Bipartite,
    packing: &Packing,
    coordinate: usize,
    parameters: &Parameters,
    kernel: &Cauchy,
    modes: &[Mode],
    beta: &[usize],
    group: usize,
    meter: &mut Meter,
) -> Result<Bipartite> {
    if modes.len() != beta.len() {
        return Err(invalid("mode exponent tuple"));
    }
    let mut left = Vec::new();
    let mut row_map = vec![None; graph.left.len()];
    let mut column_map = vec![None; graph.right.len()];
    for (side, vertices, labels, map) in [
        (false, &graph.left, &packing.row_labels, &mut row_map),
        (true, &graph.right, &packing.column_labels, &mut column_map),
    ] {
        let _ = side;
        for (v, vertex) in vertices.iter().enumerate() {
            if digit(labels[v], coordinate, parameters.radix) == group {
                map[v] = Some(left.len());
                left.push(TensorVertex {
                    tensor: vertex.tensor.clone(),
                    edges: vec![usize::MAX; vertex.edges.len()],
                });
            }
        }
    }
    let mut right = Vec::with_capacity(packing.packets.len());
    let mut edges = Vec::new();
    for (packet_id, packet) in packing.packets.iter().enumerate() {
        let rows: Vec<_> = packet
            .slots
            .iter()
            .enumerate()
            .filter_map(|(slot, &edge)| {
                edge.filter(|&e| row_map[graph.edges[e].left.0].is_some())
                    .map(|e| (slot, e))
            })
            .collect();
        let columns: Vec<_> = packet
            .slots
            .iter()
            .enumerate()
            .filter_map(|(slot, &edge)| {
                edge.filter(|&e| column_map[graph.edges[e].right.0].is_some())
                    .map(|e| (slot, e))
            })
            .collect();
        let mut local = Vec::with_capacity(rows.len());
        for &(x, _) in &rows {
            let mut weights = Vec::with_capacity(columns.len());
            for &(y, _) in &columns {
                weights.push(kernel.weight(x, y, meter)?);
            }
            local.push(weights);
        }
        let mut incoming = Vec::new();
        let mut outgoing = Vec::new();
        for (mode, &exponent) in modes.iter().zip(beta) {
            if exponent == 0 || mode.packet != packet_id {
                continue;
            }
            if mode.target == group {
                let coefficients = rows
                    .iter()
                    .map(|&(x, _)| {
                        mode.rows
                            .iter()
                            .find(|&&(slot, _)| slot == x)
                            .map(|(_, value)| value.clone())
                            .unwrap_or_else(|| kernel.ring.zero())
                    })
                    .collect();
                incoming.push(Incoming {
                    exponent,
                    coefficients,
                });
            }
            if mode.source == group {
                let mut terms = Vec::new();
                for (column, &(y, _)) in columns.iter().enumerate() {
                    if let Some((_, value)) = mode.columns.iter().find(|&&(slot, _)| slot == y) {
                        terms.push((column, value.clone()));
                    }
                }
                outgoing.push(Outgoing { exponent, terms });
            }
        }
        let packet_tensor = PacketTensor {
            ring: kernel.ring.clone(),
            local,
            column_count: columns.len(),
            incoming,
            outgoing,
        };
        let right_id = right.len();
        right.push(TensorVertex {
            tensor: Arc::new(Tensor {
                kind: TensorKind::Packet(Arc::new(packet_tensor)),
                creation_precision: kernel.ring.precision(),
            }),
            edges: Vec::new(),
        });
        for (is_column, &(_, old_edge)) in rows
            .iter()
            .map(|e| (false, e))
            .chain(columns.iter().map(|e| (true, e)))
        {
            let endpoint = if is_column {
                graph.edges[old_edge].right
            } else {
                graph.edges[old_edge].left
            };
            let left_id = if is_column {
                column_map[endpoint.0]
            } else {
                row_map[endpoint.0]
            }
            .ok_or_else(|| integrity("child vertex group"))?;
            meter.vector(edges.len() + 1, "child tensor edges")?;
            let edge_id = edges.len();
            let right_port = right[right_id].edges.len();
            edges.push(Edge {
                left: (left_id, endpoint.1),
                right: (right_id, right_port),
            });
            left[left_id].edges[endpoint.1] = edge_id;
            right[right_id].edges.push(edge_id);
        }
    }
    let child = Bipartite { left, right, edges };
    child.validate()?;
    Ok(child)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Limits;
    use num_traits::One;
    #[test]
    fn packet_entries_keep_creation_time_representatives() {
        let mut meter = Meter::new(Limits::default());
        let low = Ring::new(1, 2, &mut meter).unwrap();
        let high = low.at_precision(8, &meter).unwrap();
        let tensor = Tensor {
            creation_precision: 2,
            kind: TensorKind::Packet(Arc::new(PacketTensor {
                ring: low.clone(),
                local: vec![
                    vec![low.integer(&3u8.into())],
                    vec![low.integer(&3u8.into())],
                ],
                column_count: 1,
                incoming: vec![],
                outgoing: vec![],
            })),
        };
        let value = tensor
            .entry(&[true, true, true], &high, &mut meter)
            .unwrap();
        assert_eq!(value, high.one());
        assert_ne!(value, high.integer(&9u8.into()));
    }
    #[test]
    fn integral_kernel_and_geometric_mode_series_match() {
        let mut meter = Meter::new(Limits {
            steps: 500_000_000,
            ..Limits::default()
        });
        let p = Parameters {
            radix: 2,
            u: 1,
            a: 2,
            length: 4,
            array: 16,
        };
        let ring = Ring::new(4, 19, &mut meter).unwrap();
        let zero = Cauchy::new(&p, 0, &ring.zero(), &ring, &mut meter).unwrap();
        for x in 0..4 {
            for y in 0..4 {
                assert_eq!(
                    zero.weight(x, y, &mut meter).unwrap(),
                    if x == y { ring.one() } else { ring.zero() }
                );
            }
        }
        for t in [-3i64, -2, -1, 1, 2, 3] {
            let i = valuation(t);
            for z in [ring.one(), ring.point(&BigUint::from(2u8)).unwrap()] {
                let kernel = Cauchy::new(&p, t, &z, &ring, &mut meter).unwrap();
                let tiles = 1usize << (i + 1);
                for x in 0..4 {
                    for y0 in 0..tiles {
                        if ((x >> i) & 1) != ((y0 >> i) & 1) {
                            continue;
                        }
                        for y in (y0..4).step_by(tiles) {
                            let j = (y - y0) / tiles;
                            let mut sum = ring.zero();
                            for b in 0..ring.precision() - 1 {
                                let coefficient =
                                    kernel.mode_coefficient(x, y0, i, b, &mut meter).unwrap();
                                assert!(coefficient
                                    .coordinates()
                                    .iter()
                                    .all(|c| (c & ((BigUint::one() << (b + 1)) - BigUint::one()))
                                        .is_zero()));
                                let scalar = ring.integer(
                                    &BigUint::from(j).modpow(&BigUint::from(b), ring.modulus()),
                                );
                                let term = ring.mul(&coefficient, &scalar, &mut meter).unwrap();
                                sum = ring.add(&sum, &term, &mut meter).unwrap();
                            }
                            assert_eq!(
                                sum,
                                kernel.weight(x, y, &mut meter).unwrap(),
                                "t={t},x={x},y={y}"
                            );
                        }
                    }
                }
            }
        }
    }
}
