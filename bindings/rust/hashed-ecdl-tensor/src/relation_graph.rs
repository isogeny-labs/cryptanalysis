//! Slot-preserving cycle collection for exactly two factor-base slots.
//!
//! Rows have one unit entry in each slot. Negating the second slot gives an
//! oriented bipartite incidence matrix; signed forest cycles supply row
//! dependencies. This is ordinary modular arithmetic, not XOR cancellation.
//! The caller supplies its certified subgroup order and retains the existing
//! certificate verifier and N+1-row policy. This module does not certify a
//! modulus, change that policy, or establish a runtime improvement.
//!
//! Prior art: Godsil and Guo, *Cycle Spaces of Digraphs*, arXiv:1609.09118,
//! sections 2 and 3. The implementation also handles parallel edges and
//! computes coefficients modulo the caller's order rather than over R/C.

use crate::{integrity, invalid, overflow, BigUint, Error, Meter, Result};
use num_traits::{One, Zero};

#[derive(Clone, Debug, PartialEq, Eq)]
struct Labels {
    u: BigUint,
    v: BigUint,
}

impl Labels {
    fn zero() -> Self {
        Self {
            u: BigUint::zero(),
            v: BigUint::zero(),
        }
    }

    fn add(&self, right: &Self, modulus: &BigUint, meter: &mut Meter) -> Result<Self> {
        meter.charge(2, "graph modular label addition")?;
        Ok(Self {
            u: (&self.u + &right.u) % modulus,
            v: (&self.v + &right.v) % modulus,
        })
    }

    fn sub(&self, right: &Self, modulus: &BigUint, meter: &mut Meter) -> Result<Self> {
        meter.charge(2, "graph modular label subtraction")?;
        Ok(Self {
            u: (&self.u + modulus - &right.u) % modulus,
            v: (&self.v + modulus - &right.v) % modulus,
        })
    }
}

#[derive(Debug)]
struct ForestEdge {
    left: usize,
    right: usize,
    row: usize,
    labels: Labels,
}

/// A sparse exact row dependency, normalized at its newly closing row.
#[derive(Debug, PartialEq, Eq)]
pub(crate) struct CycleDependency {
    /// Nonzero modular row coefficients in strictly increasing row order.
    pub(crate) coefficients: Vec<(usize, BigUint)>,
    /// The modular coefficient of the public generator.
    pub(crate) combined_u: BigUint,
    /// The modular coefficient of the public target; nonzero for this result.
    pub(crate) combined_v: BigUint,
}

/// The effect of accepting one two-slot relation.
#[derive(Debug, PartialEq, Eq)]
pub(crate) enum Insertion {
    /// An edge joined two components and entered the spanning forest.
    Tree,
    /// A closing cycle has zero target coefficient, without path extraction.
    ZeroV {
        /// Generator residual, retained even for inconsistent input labels.
        combined_u: BigUint,
    },
    /// A useful closing cycle with its checked signed provenance.
    Dependency(CycleDependency),
}

/// A weighted disjoint-set forest with separately retained tree-edge provenance.
///
/// Slot-zero vertices are 0..slot_sizes[0], and slot-one vertices occupy the
/// remaining contiguous indices. Equal physical points in separate slots must
/// therefore have different IDs. Only forest edges are retained; a failed or
/// zero-V cycle cannot grow provenance storage. Resource counts are development
/// events and allocation bounds, not calibrated runtime units.
pub(crate) struct RelationGraph {
    left_vertices: usize,
    modulus: BigUint,
    parent: Vec<usize>,
    rank: Vec<usize>,
    // potential(vertex) - potential(parent), separately for u and v.
    offsets: Vec<Labels>,
    adjacency: Vec<Vec<usize>>,
    forest: Vec<ForestEdge>,
    last_row: Option<usize>,
}

fn reserve<T>(values: &mut Vec<T>, extra: usize, meter: &Meter, phase: &str) -> Result<()> {
    let len = values
        .len()
        .checked_add(extra)
        .ok_or_else(|| overflow(phase))?;
    meter.vector(len, phase)?;
    values
        .try_reserve_exact(extra)
        .map_err(|_| Error::Limit(format!("{phase}: allocation")))
}

fn filled<T: Clone>(len: usize, value: T, meter: &Meter, phase: &str) -> Result<Vec<T>> {
    let mut values = Vec::new();
    reserve(&mut values, len, meter, phase)?;
    values.resize(len, value);
    Ok(values)
}

impl RelationGraph {
    /// Bind two nonempty slot partitions and the caller's certified order.
    ///
    /// Only the numeric modulus range/width is checked here. The graph does
    /// not run a second prime certification or trust user-supplied curve data.
    pub(crate) fn new(
        slot_sizes: [usize; 2],
        modulus: &BigUint,
        meter: &mut Meter,
    ) -> Result<Self> {
        if slot_sizes.contains(&0) || modulus < &BigUint::from(2u8) {
            return Err(invalid("two-slot relation graph configuration"));
        }
        meter.bits(
            usize::try_from(modulus.bits()).map_err(|_| overflow("graph modulus width"))?,
            "graph modulus width",
        )?;
        let vertices = slot_sizes[0]
            .checked_add(slot_sizes[1])
            .ok_or_else(|| overflow("graph vertices"))?;
        meter.charge(
            u64::try_from(vertices)
                .map_err(|_| overflow("graph vertex initialization"))?
                .checked_mul(4)
                .ok_or_else(|| overflow("graph vertex initialization"))?,
            "graph vertex initialization",
        )?;
        let mut parent = Vec::new();
        reserve(&mut parent, vertices, meter, "graph parents")?;
        parent.extend(0..vertices);
        let rank = filled(vertices, 0, meter, "graph ranks")?;
        let offsets = filled(vertices, Labels::zero(), meter, "graph potentials")?;
        let adjacency = filled(vertices, Vec::new(), meter, "graph adjacency")?;
        let mut forest = Vec::new();
        reserve(&mut forest, vertices - 1, meter, "graph forest capacity")?;
        Ok(Self {
            left_vertices: slot_sizes[0],
            modulus: modulus.clone(),
            parent,
            rank,
            offsets,
            adjacency,
            forest,
            last_row: None,
        })
    }

    fn endpoints(&self, left: usize, right: usize) -> Result<()> {
        if left >= self.left_vertices || right < self.left_vertices || right >= self.parent.len() {
            return Err(invalid("relation graph endpoint slot"));
        }
        Ok(())
    }

    // Path compression is performed only after the complete root offset is
    // available. Each individual rewrite preserves its offset invariant, so
    // an interrupted compression still leaves a valid forest.
    fn find(&mut self, vertex: usize, meter: &mut Meter) -> Result<(usize, Labels)> {
        let mut root = vertex;
        let mut total = Labels::zero();
        while self.parent[root] != root {
            meter.charge(1, "graph find traversal")?;
            total = total.add(&self.offsets[root], &self.modulus, meter)?;
            root = self.parent[root];
        }
        let mut node = vertex;
        let mut remainder = total.clone();
        while self.parent[node] != root {
            meter.charge(1, "graph path compression")?;
            let next = self.parent[node];
            let next_remainder = remainder.sub(&self.offsets[node], &self.modulus, meter)?;
            self.parent[node] = root;
            self.offsets[node] = remainder;
            node = next;
            remainder = next_remainder;
        }
        Ok((root, total))
    }

    /// Inspect connectivity without exposing any target coefficients.
    pub(crate) fn would_close(&self, left: usize, right: usize, meter: &mut Meter) -> Result<bool> {
        self.endpoints(left, right)?;
        meter.charge(1, "graph connectivity query")?;
        // Witness-policy feedback reads only the unweighted component shape,
        // never label values. Weighted compression remains an insertion task.
        let root = |mut vertex: usize, work: &mut Meter| -> Result<usize> {
            while self.parent[vertex] != vertex {
                work.charge(1, "graph connectivity traversal")?;
                vertex = self.parent[vertex];
            }
            Ok(vertex)
        };
        Ok(root(left, meter)? == root(right, meter)?)
    }

    /// Accept an ordered row and screen its fundamental cycle.
    ///
    /// Row indices must strictly increase and coefficients must be canonical
    /// residues. A zero-V closing edge returns its residual without allocating
    /// or walking a provenance path. Other cycles return a sparse dependency;
    /// collecting enough rows and replaying the certificate remain the caller's
    /// responsibilities.
    pub(crate) fn insert(
        &mut self,
        left: usize,
        right: usize,
        row: usize,
        u: &BigUint,
        v: &BigUint,
        meter: &mut Meter,
    ) -> Result<Insertion> {
        self.endpoints(left, right)?;
        if self.last_row.is_some_and(|previous| row <= previous)
            || u >= &self.modulus
            || v >= &self.modulus
        {
            return Err(invalid("relation graph row or coefficient"));
        }
        meter.vector(
            row.checked_add(1)
                .ok_or_else(|| overflow("graph row index"))?,
            "graph row index",
        )?;
        meter.charge(1, "graph insertion")?;
        let labels = Labels {
            u: u.clone(),
            v: v.clone(),
        };
        let (left_root, left_offset) = self.find(left, meter)?;
        let (right_root, right_offset) = self.find(right, meter)?;
        if left_root != right_root {
            reserve(&mut self.forest, 1, meter, "graph forest edges")?;
            reserve(&mut self.adjacency[left], 1, meter, "graph left adjacency")?;
            reserve(
                &mut self.adjacency[right],
                1,
                meter,
                "graph right adjacency",
            )?;
            // potential(left_root) - potential(right_root).
            let relative = labels.sub(&left_offset, &self.modulus, meter)?.add(
                &right_offset,
                &self.modulus,
                meter,
            )?;
            let attach_left = self.rank[left_root] < self.rank[right_root];
            let offset = if attach_left {
                relative
            } else {
                Labels::zero().sub(&relative, &self.modulus, meter)?
            };
            let new_rank = if self.rank[left_root] == self.rank[right_root] {
                self.rank[left_root]
                    .checked_add(1)
                    .ok_or_else(|| overflow("graph union rank"))?
            } else {
                self.rank[left_root]
            };
            // All allocation checks, arithmetic and fallible charges precede
            // semantic mutation; a rejected edge never half-enters the forest.
            if attach_left {
                self.parent[left_root] = right_root;
                self.offsets[left_root] = offset;
            } else {
                self.parent[right_root] = left_root;
                self.offsets[right_root] = offset;
                self.rank[left_root] = new_rank;
            }
            let edge = self.forest.len();
            self.forest.push(ForestEdge {
                left,
                right,
                row,
                labels,
            });
            self.adjacency[left].push(edge);
            self.adjacency[right].push(edge);
            self.last_row = Some(row);
            return Ok(Insertion::Tree);
        }

        let predicted = left_offset.sub(&right_offset, &self.modulus, meter)?;
        let residual = labels.sub(&predicted, &self.modulus, meter)?;
        if residual.v.is_zero() {
            self.last_row = Some(row);
            return Ok(Insertion::ZeroV {
                combined_u: residual.u,
            });
        }
        let dependency = self.extract_cycle(left, right, row, labels, residual, meter)?;
        self.last_row = Some(row);
        Ok(Insertion::Dependency(dependency))
    }

    fn extract_cycle(
        &self,
        left: usize,
        right: usize,
        row: usize,
        labels: Labels,
        residual: Labels,
        meter: &mut Meter,
    ) -> Result<CycleDependency> {
        let vertices = self.parent.len();
        let mut previous = filled(vertices, None, meter, "graph path predecessors")?;
        let mut stack = Vec::new();
        reserve(&mut stack, vertices, meter, "graph path stack")?;
        previous[left] = Some((left, usize::MAX));
        stack.push(left);
        while let Some(vertex) = stack.pop() {
            meter.charge(1, "graph provenance vertex")?;
            if vertex == right {
                break;
            }
            for &edge_index in &self.adjacency[vertex] {
                meter.charge(1, "graph provenance edge")?;
                let edge = &self.forest[edge_index];
                let next = if edge.left == vertex {
                    edge.right
                } else {
                    edge.left
                };
                if previous[next].is_none() {
                    previous[next] = Some((vertex, edge_index));
                    stack.push(next);
                }
            }
        }
        if previous[right].is_none() {
            return Err(integrity("connected graph lacked forest provenance"));
        }
        let mut coefficients = Vec::new();
        reserve(
            &mut coefficients,
            vertices,
            meter,
            "graph cycle coefficients",
        )?;
        coefficients.push((row, BigUint::one()));
        let mut combined = labels;
        let mut vertex = right;
        while vertex != left {
            meter.charge(1, "graph signed cycle term")?;
            let (before, edge_index) =
                previous[vertex].ok_or_else(|| integrity("graph provenance predecessor"))?;
            let edge = &self.forest[edge_index];
            let coefficient = if edge.left == before {
                combined = combined.sub(&edge.labels, &self.modulus, meter)?;
                &self.modulus - BigUint::one()
            } else {
                combined = combined.add(&edge.labels, &self.modulus, meter)?;
                BigUint::one()
            };
            coefficients.push((edge.row, coefficient));
            vertex = before;
        }
        if combined != residual {
            return Err(integrity("graph potential/provenance residual mismatch"));
        }
        meter.charge(
            u64::try_from(coefficients.len()).map_err(|_| overflow("graph coefficient sort"))?,
            "graph coefficient ordering",
        )?;
        coefficients.sort_unstable_by_key(|term| term.0);
        Ok(CycleDependency {
            coefficients,
            combined_u: combined.u,
            combined_v: combined.v,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::arithmetic::inverse;
    use crate::Limits;
    use std::collections::BTreeMap;

    fn meter() -> Meter {
        Meter::new(Limits::default())
    }

    fn n(value: u32) -> BigUint {
        value.into()
    }

    fn accept(
        graph: &mut RelationGraph,
        edge: (usize, usize, u32, u32),
        row: usize,
        meter: &mut Meter,
    ) -> Insertion {
        graph
            .insert(edge.0, edge.1, row, &n(edge.2), &n(edge.3), meter)
            .unwrap()
    }

    fn replay(
        dependency: &CycleDependency,
        edges: &[(usize, usize, u32, u32)],
        vertices: usize,
        modulus: &BigUint,
    ) {
        let mut cancellation = vec![BigUint::zero(); vertices];
        let mut u = BigUint::zero();
        let mut v = BigUint::zero();
        for (row, coefficient) in &dependency.coefficients {
            let edge = edges[*row];
            cancellation[edge.0] = (&cancellation[edge.0] + coefficient) % modulus;
            cancellation[edge.1] = (&cancellation[edge.1] + coefficient) % modulus;
            u = (u + coefficient * n(edge.2)) % modulus;
            v = (v + coefficient * n(edge.3)) % modulus;
        }
        assert!(cancellation.iter().all(Zero::is_zero));
        assert_eq!(u, dependency.combined_u);
        assert_eq!(v, dependency.combined_v);
        assert!(!v.is_zero());
        assert!(dependency.coefficients.windows(2).all(|p| p[0].0 < p[1].0));
    }

    // Independent dense streaming-elimination control, using original +/+
    // slot rows rather than graph potentials or forest paths.
    fn dense_first(edges: &[(usize, usize, u32, u32)], vertices: usize) -> Option<Vec<BigUint>> {
        let modulus = n(17);
        let mut pivots: BTreeMap<usize, (Vec<BigUint>, Vec<BigUint>)> = BTreeMap::new();
        for (index, edge) in edges.iter().enumerate() {
            let mut row = vec![BigUint::zero(); vertices];
            row[edge.0] = BigUint::one();
            row[edge.1] = BigUint::one();
            let mut expression = vec![BigUint::zero(); edges.len()];
            expression[index] = BigUint::one();
            for (column, (pivot, provenance)) in &pivots {
                let coefficient = row[*column].clone();
                for (a, b) in row.iter_mut().zip(pivot) {
                    *a = (&*a + &modulus - &coefficient * b % &modulus) % &modulus;
                }
                for (a, b) in expression.iter_mut().zip(provenance) {
                    *a = (&*a + &modulus - &coefficient * b % &modulus) % &modulus;
                }
            }
            if let Some(column) = row.iter().position(|x| !x.is_zero()) {
                let scale = inverse(&row[column], &modulus).unwrap();
                for value in row.iter_mut().chain(expression.iter_mut()) {
                    *value = &*value * &scale % &modulus;
                }
                pivots.insert(column, (row, expression));
            } else {
                return Some(expression);
            }
        }
        None
    }

    #[test]
    fn square_cycle_has_modular_signs_and_matches_dense_first_dependency() {
        let mut work = meter();
        let mut graph = RelationGraph::new([2, 2], &n(17), &mut work).unwrap();
        let edges = [(0, 2, 1, 2), (1, 2, 3, 4), (1, 3, 5, 6), (0, 3, 7, 9)];
        for (row, edge) in edges.iter().copied().take(3).enumerate() {
            assert!(!graph.would_close(edge.0, edge.1, &mut work).unwrap());
            assert_eq!(accept(&mut graph, edge, row, &mut work), Insertion::Tree);
        }
        assert!(graph.would_close(0, 3, &mut work).unwrap());
        let Insertion::Dependency(dependency) = accept(&mut graph, edges[3], 3, &mut work) else {
            panic!("useful square cycle");
        };
        assert_eq!(
            dependency.coefficients,
            vec![(0, n(16)), (1, n(1)), (2, n(16)), (3, n(1))]
        );
        assert_eq!(
            (dependency.combined_u.clone(), dependency.combined_v.clone()),
            (n(4), n(5))
        );
        let dense = dense_first(&edges, 4).unwrap();
        assert_eq!(
            dense,
            dependency
                .coefficients
                .iter()
                .map(|(_, c)| c.clone())
                .collect::<Vec<_>>()
        );
        replay(&dependency, &edges, 4, &n(17));
    }

    #[test]
    fn first_zero_v_cycle_does_not_hide_later_useful_parallel_edge() {
        let mut work = meter();
        let mut graph = RelationGraph::new([1, 1], &n(17), &mut work).unwrap();
        let edges = [(0, 1, 2, 3), (0, 1, 5, 3), (0, 1, 2, 4)];
        assert_eq!(accept(&mut graph, edges[0], 0, &mut work), Insertion::Tree);
        assert_eq!(
            accept(&mut graph, edges[1], 1, &mut work),
            Insertion::ZeroV { combined_u: n(3) }
        );
        let Insertion::Dependency(dependency) = accept(&mut graph, edges[2], 2, &mut work) else {
            panic!("later useful parallel edge");
        };
        assert_eq!(dependency.coefficients, vec![(0, n(16)), (2, n(1))]);
        assert_eq!(graph.forest.len(), 1);
        replay(&dependency, &edges, 2, &n(17));
    }

    #[test]
    fn fixed_streams_match_dense_first_cycle_and_all_returned_dependencies_replay() {
        let orders = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8],
            [8, 0, 4, 2, 6, 1, 7, 3, 5],
            [0, 8, 4, 1, 5, 6, 2, 3, 7],
            [3, 4, 5, 8, 7, 6, 0, 1, 2],
        ];
        for order in orders {
            for seed in 0..3 {
                let edges: Vec<_> = order
                    .iter()
                    .enumerate()
                    .map(|(row, &id)| {
                        (
                            id / 3,
                            3 + id % 3,
                            (5 * row as u32 + seed) % 17,
                            (row as u32 * row as u32 + seed + 1) % 17,
                        )
                    })
                    .collect();
                let mut work = meter();
                let mut graph = RelationGraph::new([3, 3], &n(17), &mut work).unwrap();
                let mut first_cycle = true;
                for (row, edge) in edges.iter().copied().enumerate() {
                    let event = accept(&mut graph, edge, row, &mut work);
                    if let Insertion::Dependency(dependency) = &event {
                        replay(dependency, &edges, 6, &n(17));
                    }
                    if event != Insertion::Tree && first_cycle {
                        first_cycle = false;
                        let dense = dense_first(&edges[..=row], 6).unwrap();
                        if let Insertion::Dependency(dependency) = event {
                            let mut sparse = vec![BigUint::zero(); row + 1];
                            for (index, coefficient) in dependency.coefficients {
                                sparse[index] = coefficient;
                            }
                            assert_eq!(dense, sparse);
                        } else {
                            let combined_v = dense
                                .iter()
                                .zip(&edges)
                                .fold(BigUint::zero(), |sum, (c, edge)| {
                                    (sum + c * n(edge.3)) % n(17)
                                });
                            assert!(combined_v.is_zero());
                        }
                    }
                }
                assert!(graph.forest.len() <= 5);
            }
        }
    }

    #[test]
    fn slot_identity_disconnected_vertices_and_compression_are_preserved() {
        let mut work = meter();
        let mut graph = RelationGraph::new([4, 4], &n(17), &mut work).unwrap();
        // IDs 0 and 4 may encode the same physical point, but are distinct slots.
        assert!(!graph.would_close(0, 4, &mut work).unwrap());
        assert_eq!(
            accept(&mut graph, (0, 4, 1, 2), 0, &mut work),
            Insertion::Tree
        );
        assert!(!graph.would_close(1, 5, &mut work).unwrap());
        assert_eq!(
            accept(&mut graph, (1, 5, 3, 4), 1, &mut work),
            Insertion::Tree
        );
        assert_eq!(
            accept(&mut graph, (2, 6, 5, 6), 2, &mut work),
            Insertion::Tree
        );
        assert_eq!(
            accept(&mut graph, (2, 5, 7, 8), 3, &mut work),
            Insertion::Tree
        );
        assert_eq!(
            accept(&mut graph, (0, 6, 9, 10), 4, &mut work),
            Insertion::Tree
        );
        assert!(graph.would_close(1, 4, &mut work).unwrap());
        assert!(!graph.would_close(3, 7, &mut work).unwrap());
        assert!(graph.would_close(2, 4, &mut work).unwrap());
        assert!(graph.would_close(2, 4, &mut work).unwrap());
    }

    #[test]
    fn invalid_configuration_endpoints_rows_and_noncanonical_labels_are_rejected() {
        assert!(RelationGraph::new([0, 1], &n(17), &mut meter()).is_err());
        assert!(RelationGraph::new([1, 0], &n(17), &mut meter()).is_err());
        assert!(RelationGraph::new([1, 1], &n(0), &mut meter()).is_err());
        assert!(RelationGraph::new([1, 1], &n(1), &mut meter()).is_err());
        assert!(RelationGraph::new([usize::MAX, 1], &n(17), &mut meter()).is_err());
        let mut graph = RelationGraph::new([2, 2], &n(17), &mut meter()).unwrap();
        for (left, right) in [(2, 3), (0, 1), (0, 4), (usize::MAX, 3)] {
            assert!(graph.would_close(left, right, &mut meter()).is_err());
            assert!(graph
                .insert(left, right, 0, &n(1), &n(2), &mut meter())
                .is_err());
        }
        assert!(graph.insert(0, 2, 0, &n(17), &n(0), &mut meter()).is_err());
        assert!(graph.insert(0, 2, 0, &n(0), &n(17), &mut meter()).is_err());
        assert!(graph
            .insert(0, 2, usize::MAX, &n(0), &n(0), &mut meter())
            .is_err());
        assert_eq!(
            accept(&mut graph, (0, 2, 1, 2), 2, &mut meter()),
            Insertion::Tree
        );
        assert!(graph.insert(0, 3, 2, &n(1), &n(2), &mut meter()).is_err());
        assert!(graph.insert(0, 3, 1, &n(1), &n(2), &mut meter()).is_err());
    }

    #[test]
    fn limits_return_errors_and_failed_edges_can_be_retried() {
        let mut limited = Meter::new(Limits {
            vector: 1,
            ..Limits::default()
        });
        assert!(matches!(
            RelationGraph::new([1, 1], &n(17), &mut limited),
            Err(Error::Limit(_))
        ));
        let mut narrow = Meter::new(Limits {
            bits: 4,
            ..Limits::default()
        });
        assert!(matches!(
            RelationGraph::new([1, 1], &n(17), &mut narrow),
            Err(Error::Limit(_))
        ));
        let mut graph = RelationGraph::new([1, 1], &n(17), &mut meter()).unwrap();
        let mut stopped = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            graph.insert(0, 1, 0, &n(2), &n(3), &mut stopped),
            Err(Error::Limit(_))
        ));
        assert!(!graph.would_close(0, 1, &mut meter()).unwrap());
        assert_eq!(
            accept(&mut graph, (0, 1, 2, 3), 0, &mut meter()),
            Insertion::Tree
        );
        let before = graph.forest.len();
        let mut stopped = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            graph.insert(0, 1, 1, &n(2), &n(4), &mut stopped),
            Err(Error::Limit(_))
        ));
        assert_eq!(graph.forest.len(), before);
        assert!(matches!(
            accept(&mut graph, (0, 1, 2, 4), 1, &mut meter()),
            Insertion::Dependency(_)
        ));
    }

    #[test]
    fn zero_v_screening_needs_no_provenance_vector_and_path_failure_is_retryable() {
        let mut graph = RelationGraph::new([3, 3], &n(17), &mut meter()).unwrap();
        for (row, edge) in [(0, 3, 0, 0), (1, 3, 0, 0), (1, 4, 0, 0), (2, 5, 0, 0)]
            .into_iter()
            .enumerate()
        {
            assert_eq!(accept(&mut graph, edge, row, &mut meter()), Insertion::Tree);
        }
        // The row index fits length five, but a six-vertex provenance vector
        // does not. A useful cycle must fail honestly at that allocation.
        let mut limited = Meter::new(Limits {
            vector: 5,
            ..Limits::default()
        });
        assert_eq!(
            graph.insert(0, 4, 4, &n(0), &n(1), &mut limited),
            Err(Error::Limit("graph path predecessors".into()))
        );
        // The same row can then be retried as a zero-V cycle without allocating
        // the forbidden path vector or growing the existing spanning forest.
        assert_eq!(
            graph.insert(0, 4, 4, &n(0), &n(0), &mut limited).unwrap(),
            Insertion::ZeroV { combined_u: n(0) }
        );
        assert_eq!(graph.forest.len(), 4);
    }
}
