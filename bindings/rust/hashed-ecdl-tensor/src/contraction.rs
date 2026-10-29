//! Exact counts, witness self-reduction, and Appendix D.4 recursive contraction.
//!
//! The source constants force direct fallback below an astronomical threshold.
//! The backend used is reported explicitly; a fallback is never labelled a
//! measured subexponential speedup. Small forced-recursion tests exercise the
//! same kernel, modes, children and reconstruction used by the general branch.

mod deformation;
mod packing;
mod recursive;

use crate::arithmetic::{random_below, RandomSource};
use crate::network::{increment, Network, Predicate};
use crate::ring::{Element, Ring};
use crate::{integrity, invalid, overflow, BigUint, Meter, Result};
use num_traits::{One, Zero};
use std::sync::Arc;

/// Actual backend used for a contraction.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Backend {
    /// Direct summation over graph edges, the manuscript's finite-size fallback.
    Direct,
    /// Exact finite-size fallback using built-in parsimonious program metadata.
    Functional,
    /// Packet/mode recursion with tapered Hermite reconstruction.
    Recursive,
}

/// Cumulative execution diagnostics, not calibrated operation-cost evidence.
#[derive(Clone, Debug, Default)]
pub struct Statistics {
    /// Public contraction calls, including self-reduction queries.
    pub contractions: u64,
    /// Recursive tensor calls entered.
    pub recursive_calls: u64,
    /// Direct ring/Boolean edge assignments actually visited.
    pub edge_assignments: u64,
    /// Free program input assignments actually visited.
    pub functional_assignments: u64,
    /// Backend used by the most recent public call.
    pub last_backend: Option<Backend>,
}

/// Exact tensor counter with optional, sound built-in finite-size acceleration.
pub struct Counter {
    /// Permit unique-witness arithmetic-program evaluation in the leaf range.
    /// Arbitrary user predicates cannot attach such metadata.
    pub functional_leaves: bool,
    /// Actual work diagnostics.
    pub statistics: Statistics,
}
impl Default for Counter {
    fn default() -> Self {
        Self {
            functional_leaves: true,
            statistics: Statistics::default(),
        }
    }
}

fn event(value: &mut u64, phase: &str) -> Result<()> {
    *value = value.checked_add(1).ok_or_else(|| overflow(phase))?;
    Ok(())
}

impl Counter {
    /// Count all satisfying edge assignments, after fixing optional edge bits.
    /// The result is an exact nonnegative integer, not a decision approximation.
    pub fn count(
        &mut self,
        network: &Network,
        pins: &[Option<bool>],
        meter: &mut Meter,
    ) -> Result<BigUint> {
        network.check_pins(pins)?;
        meter.vector(network.edge_count(), "contraction graph")?;
        meter.bits(
            network
                .edge_count()
                .checked_add(1)
                .ok_or_else(|| overflow("count precision"))?,
            "exact count precision",
        )?;
        event(&mut self.statistics.contractions, "contraction calls")?;
        let edges = network
            .edge_count()
            .checked_mul(2)
            .ok_or_else(|| overflow("bipartite subdivision"))?;
        let setup = recursive::Setup::new(edges.max(2), network.maximum_degree().max(2), meter)?;
        if setup.parameters(edges, 0)?.is_none() || edges <= setup.leaf_size {
            if self.functional_leaves && network.model.is_some() {
                self.statistics.last_backend = Some(Backend::Functional);
                return self.functional_count(network, pins, meter);
            }
            self.statistics.last_backend = Some(Backend::Direct);
            return self.direct_count(network, pins, meter);
        }
        self.statistics.last_backend = Some(Backend::Recursive);
        let precision = network.edge_count() + 1;
        let degree = setup
            .lambda
            .checked_mul(4)
            .ok_or_else(|| overflow("residue field degree"))?;
        let ring = Ring::new(degree, precision, meter)?;
        let graph = Bipartite::from_boolean(network, pins, precision, meter)?;
        let answer = recursive::contract(&graph, &ring, &setup, 0, &mut self.statistics, meter)?;
        if answer.coordinates().iter().skip(1).any(|c| !c.is_zero()) {
            return Err(integrity(
                "Boolean contraction did not return to the base coefficient ring",
            ));
        }
        let value = answer.coordinates()[0].clone();
        if value > (BigUint::one() << network.edge_count()) {
            return Err(integrity("Boolean count exceeds assignment space"));
        }
        Ok(value)
    }

    fn direct_count(
        &mut self,
        network: &Network,
        pins: &[Option<bool>],
        meter: &mut Meter,
    ) -> Result<BigUint> {
        let free: Vec<_> = pins
            .iter()
            .enumerate()
            .filter_map(|(e, p)| p.is_none().then_some(e))
            .collect();
        let mut digits = vec![false; free.len()];
        let mut answer = BigUint::zero();
        loop {
            meter.charge(1, "direct Boolean contraction")?;
            event(
                &mut self.statistics.edge_assignments,
                "edge assignment count",
            )?;
            let mut assignment: Vec<_> = pins.iter().map(|p| p.unwrap_or(false)).collect();
            for (&edge, &bit) in free.iter().zip(&digits) {
                assignment[edge] = bit;
            }
            if network.evaluate(&assignment, meter)? {
                answer += BigUint::one();
            }
            if !increment(&mut digits) {
                break;
            }
        }
        Ok(answer)
    }

    fn functional_count(
        &mut self,
        network: &Network,
        pins: &[Option<bool>],
        meter: &mut Meter,
    ) -> Result<BigUint> {
        let program = network
            .model
            .as_ref()
            .ok_or_else(|| invalid("missing built-in witness program"))?;
        let Some(signal_pins) = program.signal_pins(pins)? else {
            return Ok(BigUint::zero());
        };
        let unpinned: Vec<_> = program
            .free
            .iter()
            .enumerate()
            .filter_map(|(i, &signal)| signal_pins[signal].is_none().then_some(i))
            .collect();
        let mut digits = vec![false; unpinned.len()];
        let mut values: Vec<_> = program
            .free
            .iter()
            .map(|&signal| signal_pins[signal].unwrap_or(false))
            .collect();
        let mut count = BigUint::zero();
        loop {
            meter.charge(1, "functional leaf contraction")?;
            event(
                &mut self.statistics.functional_assignments,
                "functional assignment count",
            )?;
            for (&i, &bit) in unpinned.iter().zip(&digits) {
                values[i] = bit;
            }
            if program
                .materialize(&values, &signal_pins, network, meter)?
                .is_some()
            {
                count += BigUint::one();
            }
            if !increment(&mut digits) {
                break;
            }
        }
        Ok(count)
    }

    /// Lemma 1: deterministically select a language word by prefix counts.
    /// At most one initial count and one count per unfixed interface bit are used.
    /// Resource errors propagate; `None` means an exact zero contraction.
    pub fn witness(
        &mut self,
        network: &Network,
        pins: &[Option<bool>],
        meter: &mut Meter,
    ) -> Result<Option<Vec<bool>>> {
        let mut pins = pins.to_vec();
        let mut total = self.count(network, &pins, meter)?;
        if total.is_zero() {
            return Ok(None);
        }
        let mut word = Vec::with_capacity(network.interface().len());
        for &edge in network.interface() {
            if let Some(bit) = pins[edge] {
                word.push(bit);
                continue;
            }
            pins[edge] = Some(false);
            let zero = self.count(network, &pins, meter)?;
            if zero > total {
                return Err(integrity("prefix contraction increased after pinning"));
            }
            if zero.is_zero() {
                pins[edge] = Some(true);
                word.push(true);
            } else {
                total = zero;
                word.push(false);
            }
        }
        Ok(Some(word))
    }

    /// Sample an interface word by the exact prefix-count probabilities of
    /// Lemma 1, using uniform caller bytes. For a parsimonious encoding this
    /// is uniform over accepted words. For an arbitrary encoding, each word
    /// is weighted by its number of satisfying auxiliary assignments.
    ///
    /// Uses at most one initial contraction and one per unfixed interface bit.
    /// `None` certifies an empty language; counting and entropy errors propagate.
    pub fn sample(
        &mut self,
        network: &Network,
        pins: &[Option<bool>],
        rng: &mut impl RandomSource,
        meter: &mut Meter,
    ) -> Result<Option<Vec<bool>>> {
        let mut pins = pins.to_vec();
        let mut total = self.count(network, &pins, meter)?;
        if total.is_zero() {
            return Ok(None);
        }
        let mut word = Vec::with_capacity(network.interface().len());
        for &edge in network.interface() {
            if let Some(bit) = pins[edge] {
                word.push(bit);
                continue;
            }
            pins[edge] = Some(false);
            let zero = self.count(network, &pins, meter)?;
            if zero > total {
                return Err(integrity("prefix contraction increased after pinning"));
            }
            let one = &total - &zero;
            let bit = if zero.is_zero() {
                true
            } else if one.is_zero() {
                false
            } else {
                random_below(&total, rng, meter)? >= zero
            };
            pins[edge] = Some(bit);
            total = if bit { one } else { zero };
            word.push(bit);
        }
        Ok(Some(word))
    }
}

#[derive(Clone)]
pub(crate) enum TensorKind {
    Boolean(Arc<dyn Predicate>),
    Equality(Option<bool>),
    Packet(Arc<deformation::PacketTensor>),
}

#[derive(Clone)]
pub(crate) struct Tensor {
    pub kind: TensorKind,
    pub creation_precision: usize,
}
impl Tensor {
    pub fn entry(&self, bits: &[bool], ring: &Ring, meter: &mut Meter) -> Result<Element> {
        meter.charge(1, "implicit tensor entry")?;
        if ring.precision() < self.creation_precision {
            return Err(integrity("tensor precision decreased"));
        }
        match &self.kind {
            TensorKind::Boolean(p) => {
                Ok(ring.integer(&BigUint::from(u8::from(p.evaluate(bits, meter)?))))
            }
            TensorKind::Equality(pin) => {
                if bits.len() != 2 {
                    return Err(integrity("subdivision equality arity"));
                }
                Ok(ring.integer(&BigUint::from(u8::from(
                    bits[0] == bits[1] && pin.map_or(true, |p| p == bits[0]),
                ))))
            }
            TensorKind::Packet(packet) => {
                if packet.ring.precision() != self.creation_precision {
                    return Err(integrity("packet creation precision"));
                }
                // Evaluate at the immutable creation precision FIRST, then lift
                // coordinates. Re-evaluating at the new precision is unsound.
                ring.lift(&packet.entry(bits, meter)?)
            }
        }
    }
}

#[derive(Clone)]
pub(crate) struct TensorVertex {
    pub tensor: Arc<Tensor>,
    pub edges: Vec<usize>,
}
#[derive(Clone, Copy)]
pub(crate) struct Edge {
    pub left: (usize, usize),
    pub right: (usize, usize),
}
#[derive(Clone)]
pub(crate) struct Bipartite {
    pub left: Vec<TensorVertex>,
    pub right: Vec<TensorVertex>,
    pub edges: Vec<Edge>,
}
impl Bipartite {
    fn from_boolean(
        network: &Network,
        pins: &[Option<bool>],
        precision: usize,
        meter: &Meter,
    ) -> Result<Self> {
        let size = network
            .edge_count()
            .checked_mul(2)
            .ok_or_else(|| overflow("edge subdivision"))?;
        meter.vector(size, "bipartite edge subdivision")?;
        let mut edges = vec![
            Edge {
                left: (usize::MAX, usize::MAX),
                right: (usize::MAX, usize::MAX)
            };
            size
        ];
        let mut left = Vec::with_capacity(network.vertex_count());
        for (vertex_id, vertex) in network.vertices.iter().enumerate() {
            let mut incident = Vec::with_capacity(vertex.edges.len());
            for (port, &old_edge) in vertex.edges.iter().enumerate() {
                let (a, b) = network.edges[old_edge];
                let half = if a == vertex_id {
                    0
                } else if b == vertex_id {
                    1
                } else {
                    return Err(integrity("Boolean edge incidence"));
                };
                let edge = 2 * old_edge + half;
                edges[edge] = Edge {
                    left: (vertex_id, port),
                    right: (old_edge, half),
                };
                incident.push(edge);
            }
            left.push(TensorVertex {
                tensor: Arc::new(Tensor {
                    kind: TensorKind::Boolean(vertex.predicate.clone()),
                    creation_precision: precision,
                }),
                edges: incident,
            });
        }
        let right = (0..network.edge_count())
            .map(|e| TensorVertex {
                tensor: Arc::new(Tensor {
                    kind: TensorKind::Equality(pins[e]),
                    creation_precision: precision,
                }),
                edges: vec![2 * e, 2 * e + 1],
            })
            .collect();
        let out = Self { left, right, edges };
        out.validate()?;
        Ok(out)
    }
    pub fn validate(&self) -> Result<()> {
        for (e, edge) in self.edges.iter().enumerate() {
            if self
                .left
                .get(edge.left.0)
                .and_then(|v| v.edges.get(edge.left.1))
                != Some(&e)
                || self
                    .right
                    .get(edge.right.0)
                    .and_then(|v| v.edges.get(edge.right.1))
                    != Some(&e)
            {
                return Err(integrity("bipartite port ordering"));
            }
        }
        for (side, vertices) in [(false, &self.left), (true, &self.right)] {
            for (vertex, value) in vertices.iter().enumerate() {
                for (port, &edge) in value.edges.iter().enumerate() {
                    let Some(edge) = self.edges.get(edge) else {
                        return Err(integrity("unattached bipartite port"));
                    };
                    let endpoint = if side { edge.right } else { edge.left };
                    if endpoint != (vertex, port) {
                        return Err(integrity("duplicate bipartite incidence"));
                    }
                }
            }
        }
        Ok(())
    }
}

pub(crate) fn brute_tensor(
    graph: &Bipartite,
    ring: &Ring,
    statistics: &mut Statistics,
    meter: &mut Meter,
) -> Result<Element> {
    let mut assignment = vec![false; graph.edges.len()];
    let mut total = ring.zero();
    loop {
        meter.charge(1, "direct ring edge assignment")?;
        event(&mut statistics.edge_assignments, "ring edge assignments")?;
        let mut product = ring.one();
        for vertex in graph.left.iter().chain(&graph.right) {
            let ports: Vec<_> = vertex.edges.iter().map(|&e| assignment[e]).collect();
            let value = vertex.tensor.entry(&ports, ring, meter)?;
            product = ring.mul(&product, &value, meter)?;
            if product.is_zero() {
                break;
            }
        }
        total = ring.add(&total, &product, meter)?;
        if !increment(&mut assignment) {
            break;
        }
    }
    Ok(total)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::network::{direct_count, FnPredicate, GraphBuilder};
    use crate::{Error, Limits};
    #[test]
    fn counts_and_prefix_witnesses_match_truth_tables() {
        let mut meter = Meter::new(Limits::default());
        for table in 0..16u8 {
            let mut builder = GraphBuilder::new();
            let a = builder.vertex(FnPredicate::new(2, move |x, _| {
                Ok(table & (1 << (u8::from(x[0]) + 2 * u8::from(x[1]))) != 0)
            }));
            let b = builder.vertex(FnPredicate::new(2, |_, _| Ok(true)));
            let e0 = builder.edge(a, b, &mut meter).unwrap();
            let e1 = builder.edge(a, b, &mut meter).unwrap();
            let graph = builder.finish(vec![e0, e1]).unwrap();
            let mut counter = Counter::default();
            let pins = vec![None; 2];
            let exact = direct_count(&graph, &pins, &mut meter).unwrap();
            assert_eq!(counter.count(&graph, &pins, &mut meter).unwrap(), exact);
            let witness = counter.witness(&graph, &pins, &mut meter).unwrap();
            assert_eq!(witness.is_some(), !exact.is_zero());
            if let Some(word) = witness {
                assert!(graph.evaluate(&word, &mut meter).unwrap());
            }
        }
        let mut builder = GraphBuilder::new();
        let a = builder.vertex(FnPredicate::new(1, |_, _| Ok(true)));
        let b = builder.vertex(FnPredicate::new(1, |_, _| Ok(true)));
        builder.edge(a, b, &mut meter).unwrap();
        let graph = builder.finish(vec![]).unwrap();
        let mut meter = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            Counter::default().count(&graph, &[None], &mut meter),
            Err(Error::Limit(_))
        ));
    }
    #[test]
    fn functional_leaf_count_equals_complete_edge_enumeration() {
        let mut meter = Meter::new(Limits::default());
        let mut encoder = crate::encoding::Encoder::new();
        let a = encoder.input_word(2, &meter).unwrap();
        let b = encoder.input_word(2, &meter).unwrap();
        let sum = encoder.integer_add(&a, &b, &meter).unwrap();
        encoder.mark_interface(&sum, &meter).unwrap();
        let network = encoder.finish(&meter).unwrap();
        let mut counter = Counter::default();
        let mut pins = vec![None; network.edge_count()];
        for pin in [None, Some(false), Some(true)] {
            pins[network.interface()[0]] = pin;
            let expected = direct_count(&network, &pins, &mut meter).unwrap();
            assert_eq!(
                counter.count(&network, &pins, &mut meter).unwrap(),
                expected
            );
            assert_eq!(counter.statistics.last_backend, Some(Backend::Functional));
        }
    }

    struct Draws {
        bytes: std::collections::VecDeque<u8>,
        calls: usize,
    }
    impl RandomSource for Draws {
        fn fill(&mut self, bytes: &mut [u8]) -> Result<()> {
            self.calls += 1;
            for byte in bytes {
                *byte = self
                    .bytes
                    .pop_front()
                    .ok_or_else(|| invalid("fixture entropy exhausted"))?;
            }
            Ok(())
        }
    }

    fn or_network(interface: Vec<usize>, meter: &mut Meter) -> Network {
        let mut builder = GraphBuilder::new();
        let a = builder.vertex(FnPredicate::new(2, |x, _| Ok(x[0] || x[1])));
        let b = builder.vertex(FnPredicate::new(2, |_, _| Ok(true)));
        builder.edge(a, b, meter).unwrap();
        builder.edge(a, b, meter).unwrap();
        builder.finish(interface).unwrap()
    }

    #[test]
    fn exact_sampling_uses_counts_and_preserves_auxiliary_multiplicity() {
        let mut meter = Meter::new(Limits::default());
        let graph = or_network(vec![0, 1], &mut meter);
        let mut frequencies = std::collections::BTreeMap::new();
        // All six equiprobable root/child draws. No statistical tolerance:
        // the three accepted words must each have exactly two preimages.
        for root in 0..3 {
            for child in 0..2 {
                let mut draws = Draws {
                    bytes: [root, child].into(),
                    calls: 0,
                };
                let mut counter = Counter::default();
                let word = counter
                    .sample(&graph, &[None, None], &mut draws, &mut meter)
                    .unwrap()
                    .unwrap();
                assert!(graph.evaluate(&word, &mut meter).unwrap());
                assert_eq!(counter.statistics.contractions, 3);
                *frequencies.entry(word).or_insert(0) += 1;
            }
        }
        assert_eq!(frequencies.len(), 3);
        assert!(frequencies.values().all(|&count| count == 2));

        // Hiding the second edge gives one extension of 0 and two of 1.
        // Interface words must have weights 1:2, not be reported as uniform.
        let graph = or_network(vec![0], &mut meter);
        for root in 0..3 {
            let mut draws = Draws {
                bytes: [root].into(),
                calls: 0,
            };
            let word = Counter::default()
                .sample(&graph, &[None, None], &mut draws, &mut meter)
                .unwrap()
                .unwrap();
            assert_eq!(word, vec![root != 0]);
            assert_eq!(draws.calls, 1);
        }
    }

    #[test]
    fn sampling_respects_pins_empty_languages_and_failure_boundaries() {
        let mut meter = Meter::new(Limits::default());
        let graph = or_network(vec![0, 1], &mut meter);
        let mut no_entropy = Draws {
            bytes: [].into(),
            calls: 0,
        };
        let mut counter = Counter::default();
        assert_eq!(
            counter
                .sample(&graph, &[Some(false), None], &mut no_entropy, &mut meter)
                .unwrap(),
            Some(vec![false, true])
        );
        assert_eq!(counter.statistics.contractions, 2);
        assert_eq!(no_entropy.calls, 0);
        assert_eq!(
            counter
                .sample(
                    &graph,
                    &[Some(false), Some(false)],
                    &mut no_entropy,
                    &mut meter
                )
                .unwrap(),
            None
        );
        assert!(matches!(
            counter.sample(&graph, &[], &mut no_entropy, &mut meter),
            Err(Error::Invalid(_))
        ));
        assert!(matches!(
            counter.sample(&graph, &[None, None], &mut no_entropy, &mut meter),
            Err(Error::Invalid(_))
        ));
        let mut exhausted = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            counter.sample(&graph, &[None, None], &mut no_entropy, &mut exhausted),
            Err(Error::Limit(_))
        ));

        // An empty interface still distinguishes satisfiable from empty.
        let graph = or_network(vec![], &mut meter);
        assert_eq!(
            counter
                .sample(&graph, &[None, None], &mut no_entropy, &mut meter)
                .unwrap(),
            Some(vec![])
        );
    }
}
