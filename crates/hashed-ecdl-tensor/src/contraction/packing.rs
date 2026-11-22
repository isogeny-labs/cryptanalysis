//! D.4.2: exact conditional expectation, collision packing, and slot orientation.

use super::recursive::Parameters;
use super::Bipartite;
use crate::{integrity, invalid, overflow, BigUint, Meter, Result};
use num_traits::Zero;

#[derive(Clone)]
pub(super) struct Packet {
    pub slots: Vec<Option<usize>>,
    pub pairs: Vec<(usize, usize)>,
}
pub(super) struct Packing {
    pub packets: Vec<Packet>,
    pub row_labels: Vec<usize>,
    pub column_labels: Vec<usize>,
}

pub(super) fn digit(label: usize, coordinate: usize, radix: usize) -> usize {
    (label / radix.pow(coordinate as u32)) % radix
}

// R^2 times E[sum_gamma X_gamma^2], a nonnegative integer. The omitted
// constant -M^2/R^2 does not affect conditional-expectation minimization.
fn objective(
    graph: &Bipartite,
    rows: &[Option<usize>],
    columns: &[Option<usize>],
    labels: usize,
    meter: &mut Meter,
) -> Result<BigUint> {
    let label = BigUint::from(labels);
    let square = &label * &label;
    let mut total = BigUint::zero();
    for a in &graph.edges {
        for b in &graph.edges {
            meter.charge(1, "conditional expectation edge pair")?;
            let mut unknown = 0;
            let mut impossible = false;
            for (u, v, assignment) in [(a.left.0, b.left.0, rows), (a.right.0, b.right.0, columns)]
            {
                if u == v {
                    continue;
                }
                match (assignment[u], assignment[v]) {
                    (Some(x), Some(y)) => {
                        if x != y {
                            impossible = true;
                            break;
                        }
                    }
                    _ => unknown += 1,
                }
            }
            if !impossible {
                total += match unknown {
                    0 => square.clone(),
                    1 => label.clone(),
                    _ => BigUint::from(1u8),
                };
            }
        }
    }
    Ok(total)
}

fn conditional_labels(
    graph: &Bipartite,
    labels: usize,
    meter: &mut Meter,
) -> Result<(Vec<usize>, Vec<usize>)> {
    meter.vector(labels, "vertex label alphabet")?;
    let mut rows = vec![None; graph.left.len()];
    let mut columns = vec![None; graph.right.len()];
    for side in [false, true] {
        let count = if side { columns.len() } else { rows.len() };
        for vertex in 0..count {
            if (if side {
                &graph.right[vertex]
            } else {
                &graph.left[vertex]
            })
            .edges
            .is_empty()
            {
                if side {
                    columns[vertex] = Some(0);
                } else {
                    rows[vertex] = Some(0);
                }
                continue;
            }
            let mut best: Option<(BigUint, usize)> = None;
            for label in 0..labels {
                meter.charge(1, "conditional expectation candidate")?;
                if side {
                    columns[vertex] = Some(label);
                } else {
                    rows[vertex] = Some(label);
                }
                let value = objective(graph, &rows, &columns, labels, meter)?;
                if best.as_ref().map_or(true, |(score, _)| value < *score) {
                    best = Some((value, label));
                }
            }
            let selected = best.ok_or_else(|| invalid("empty label alphabet"))?.1;
            if side {
                columns[vertex] = Some(selected);
            } else {
                rows[vertex] = Some(selected);
            }
        }
    }
    Ok((
        rows.into_iter().map(Option::unwrap).collect(),
        columns.into_iter().map(Option::unwrap).collect(),
    ))
}

pub(super) fn pack(
    graph: &Bipartite,
    parameters: &Parameters,
    delta: usize,
    meter: &mut Meter,
) -> Result<Packing> {
    let labels = parameters
        .radix
        .checked_pow(parameters.a as u32)
        .ok_or_else(|| overflow("vertex labels"))?;
    let (rows, columns) = conditional_labels(graph, labels, meter)?;
    let mut counts = vec![0usize; parameters.array];
    for edge in &graph.edges {
        counts[rows[edge.left.0] * labels + columns[edge.right.0]] += 1;
    }
    let sum_squares: BigUint = counts
        .iter()
        .map(|&n| BigUint::from(n) * BigUint::from(n))
        .sum();
    let m = BigUint::from(graph.edges.len());
    let lhs = BigUint::from(parameters.array) * sum_squares;
    let base = &m * &m;
    let rhs = BigUint::from(2usize) * &m * BigUint::from(delta) * BigUint::from(parameters.array);
    if lhs < base || lhs - base > rhs {
        return Err(integrity("conditional-expectation variance bound"));
    }
    pack_labels(graph, parameters, rows, columns, true, meter)
}

pub(super) fn pack_labels(
    graph: &Bipartite,
    parameters: &Parameters,
    rows: Vec<usize>,
    columns: Vec<usize>,
    enforce_bounds: bool,
    meter: &mut Meter,
) -> Result<Packing> {
    let p = parameters;
    let labels = p
        .radix
        .checked_pow(p.a as u32)
        .ok_or_else(|| overflow("packet labels"))?;
    if rows.len() != graph.left.len()
        || columns.len() != graph.right.len()
        || rows.iter().chain(&columns).any(|&v| v >= labels)
    {
        return Err(invalid("packet vertex labels"));
    }
    meter.vector(p.array, "pair-label classes")?;
    let mut classes: Vec<Vec<usize>> = vec![Vec::new(); p.array];
    for (index, edge) in graph.edges.iter().enumerate() {
        classes[rows[edge.left.0] * labels + columns[edge.right.0]].push(index);
    }
    let maximum = classes.iter().map(Vec::len).max().unwrap_or(0);
    let height = maximum
        .div_ceil(p.length)
        .checked_mul(p.length)
        .ok_or_else(|| overflow("packet padding"))?;
    if enforce_bounds
        && BigUint::from(height) * BigUint::from(p.array)
            > BigUint::from(3usize) * BigUint::from(graph.edges.len())
    {
        return Err(integrity("packet padding bound"));
    }
    let pairs: Vec<_> = (0..p.radix)
        .flat_map(|a| (a..p.radix).map(move |b| (a, b)))
        .collect();
    let patterns = pairs
        .len()
        .checked_pow(p.a as u32)
        .ok_or_else(|| overflow("unordered packet patterns"))?;
    let mut packets = Vec::new();
    for mut pattern in 0..patterns {
        meter.charge(1, "packet orientation pattern")?;
        let mut chosen = Vec::with_capacity(p.a);
        for _ in 0..p.a {
            chosen.push(pairs[pattern % pairs.len()]);
            pattern /= pairs.len();
        }
        let unequal = chosen.iter().filter(|&&(a, b)| a != b).count();
        let copies = 1usize
            .checked_shl((p.a - unequal) as u32)
            .ok_or_else(|| overflow("packet copies"))?;
        for start in (0..height).step_by(copies) {
            let mut slots = Vec::with_capacity(p.length);
            for slot in 0..p.length {
                meter.charge(1, "packet slot assignment")?;
                let (mut row, mut column, mut place, mut copy, mut copy_bit) = (0, 0, 1, 0, 0);
                for (i, &(lo, hi)) in chosen.iter().enumerate() {
                    let bit = (slot >> i) & 1;
                    let (a, b) = if lo == hi {
                        copy |= bit << copy_bit;
                        copy_bit += 1;
                        (lo, hi)
                    } else if bit == 0 {
                        (lo, hi)
                    } else {
                        (hi, lo)
                    };
                    row += a * place;
                    column += b * place;
                    place *= p.radix;
                }
                slots.push(classes[row * labels + column].get(start + copy).copied());
            }
            if slots.iter().any(Option::is_some) {
                meter.vector(packets.len() + 1, "packet count")?;
                packets.push(Packet {
                    slots,
                    pairs: chosen.clone(),
                });
            }
        }
    }
    let mut seen = vec![false; graph.edges.len()];
    for packet in &packets {
        for &edge in packet.slots.iter().flatten() {
            if seen[edge] {
                return Err(integrity("edge repeated in packets"));
            }
            seen[edge] = true;
        }
    }
    if seen.iter().any(|&present| !present) {
        return Err(integrity("edge omitted from packets"));
    }
    if enforce_bounds {
        if BigUint::from(packets.len()) * BigUint::from(p.length)
            > BigUint::from(3usize) * BigUint::from(graph.edges.len())
        {
            return Err(integrity("packet count bound"));
        }
        for coordinate in 0..p.a {
            let mut row_load = vec![0usize; p.radix];
            let mut column_load = row_load.clone();
            for (v, vertex) in graph.left.iter().enumerate() {
                row_load[digit(rows[v], coordinate, p.radix)] += vertex.edges.len();
            }
            for (v, vertex) in graph.right.iter().enumerate() {
                column_load[digit(columns[v], coordinate, p.radix)] += vertex.edges.len();
            }
            if row_load.iter().chain(&column_load).any(|&n| {
                BigUint::from(n) * BigUint::from(p.radix)
                    > BigUint::from(3usize) * BigUint::from(graph.edges.len())
            }) {
                return Err(integrity("group port-balance bound"));
            }
        }
    }
    Ok(Packing {
        packets,
        row_labels: rows,
        column_labels: columns,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::contraction::{Edge, Tensor, TensorKind, TensorVertex};
    use crate::network::FnPredicate;
    use crate::Limits;
    use std::sync::Arc;
    #[test]
    fn conditional_expectations_do_not_assume_disjoint_ports() {
        let tensor = Arc::new(Tensor {
            kind: TensorKind::Boolean(Arc::new(FnPredicate::new(2, |_, _| Ok(true)))),
            creation_precision: 3,
        });
        let graph = Bipartite {
            left: vec![TensorVertex {
                tensor: tensor.clone(),
                edges: vec![0, 1],
            }],
            right: vec![TensorVertex {
                tensor,
                edges: vec![0, 1],
            }],
            edges: vec![
                Edge {
                    left: (0, 0),
                    right: (0, 0),
                },
                Edge {
                    left: (0, 1),
                    right: (0, 1),
                },
            ],
        };
        let mut meter = Meter::new(Limits::default());
        let (rows, columns) = conditional_labels(&graph, 4, &mut meter).unwrap();
        assert_eq!(rows, vec![0]);
        assert_eq!(columns, vec![0]);
        let parameters = Parameters {
            radix: 2,
            u: 1,
            a: 2,
            length: 4,
            array: 16,
        };
        let packed = pack_labels(&graph, &parameters, vec![3], vec![0], false, &mut meter).unwrap();
        assert_eq!(packed.packets.len(), 2);
        assert!(packed.packets.iter().all(|p| p.slots[3].is_some()));
    }
}
