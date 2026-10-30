//! Exact counts, witness self-reduction, and Appendix D.4 recursive contraction.
//!
//! The source constants force direct fallback below an astronomical threshold.
//! The backend used is reported explicitly; a fallback is never labelled a
//! measured subexponential speedup. Small forced-recursion tests exercise the
//! same kernel, modes, children and reconstruction used by the general branch.

mod deformation;
mod packing;
mod recursive;

use crate::network::{increment, Network, Predicate};
use crate::ring::{Element, Ring};
use crate::{integrity, invalid, overflow, BigUint, Meter, Result};
use num_traits::{One, Zero};
use std::collections::{BTreeMap, BTreeSet};
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
    /// Built-in functional witness searches, separate from exact count queries.
    pub witness_searches: u64,
    /// Backend used by the most recent public call.
    pub last_backend: Option<Backend>,
}

/// Exact tensor counter with optional, sound built-in finite-size acceleration.
pub struct Counter {
    /// Permit unique-witness arithmetic-program evaluation in the leaf range.
    /// Arbitrary user predicates cannot attach such metadata.
    pub functional_leaves: bool,
    /// Use the single-pass built-in witness search in the functional leaf range.
    /// Disable to retain the original prefix-count path for exact comparisons.
    pub functional_witnesses: bool,
    /// Actual work diagnostics.
    pub statistics: Statistics,
}
impl Default for Counter {
    fn default() -> Self {
        Self {
            functional_leaves: true,
            functional_witnesses: true,
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

    /// Select the same lexicographically least interface word as prefix counts.
    /// Built-in functional leaves search inputs once and stop at the first valid
    /// word only when their order proves it is least. Derived interface bits
    /// require a full pass. Other networks retain the prefix-count algorithm.
    /// Resource errors propagate; `None` is returned only after exact exhaustion.
    pub fn witness(
        &mut self,
        network: &Network,
        pins: &[Option<bool>],
        meter: &mut Meter,
    ) -> Result<Option<Vec<bool>>> {
        network.check_pins(pins)?;
        if self.functional_leaves && self.functional_witnesses && network.model.is_some() {
            meter.vector(network.edge_count(), "contraction graph")?;
            meter.bits(
                network
                    .edge_count()
                    .checked_add(1)
                    .ok_or_else(|| overflow("count precision"))?,
                "exact count precision",
            )?;
            let edges = network
                .edge_count()
                .checked_mul(2)
                .ok_or_else(|| overflow("bipartite subdivision"))?;
            let setup =
                recursive::Setup::new(edges.max(2), network.maximum_degree().max(2), meter)?;
            if setup.parameters(edges, 0)?.is_none() || edges <= setup.leaf_size {
                self.statistics.last_backend = Some(Backend::Functional);
                event(
                    &mut self.statistics.witness_searches,
                    "functional witness searches",
                )?;
                return self.functional_witness(network, pins, meter);
            }
        }
        self.witness_by_counts(network, pins, meter)
    }

    fn functional_witness(
        &mut self,
        network: &Network,
        pins: &[Option<bool>],
        meter: &mut Meter,
    ) -> Result<Option<Vec<bool>>> {
        let program = network
            .model
            .as_ref()
            .ok_or_else(|| invalid("missing built-in witness program"))?;
        let Some(signal_pins) = program.signal_pins(pins)? else {
            return Ok(None);
        };
        let positions: BTreeMap<_, _> = program
            .free
            .iter()
            .enumerate()
            .map(|(i, &s)| (s, i))
            .collect();
        let mut order = Vec::new();
        let mut seen = BTreeSet::new();
        let mut interface_is_input = true;
        // Prioritize interface signals, respecting aliases and fixed values.
        for &edge in network.interface() {
            let signal = program.edge_signals[edge];
            if signal_pins[signal].is_some() {
                continue;
            }
            if let Some(&position) = positions.get(&signal) {
                if seen.insert(position) {
                    order.push(position);
                }
            } else {
                interface_is_input = false;
            }
        }
        for (position, &signal) in program.free.iter().enumerate() {
            if signal_pins[signal].is_none() && seen.insert(position) {
                order.push(position);
            }
        }
        // increment() changes its first digit fastest. Reverse the priorities so
        // interface[0] changes slowest, matching prefix false-before-true order.
        order.reverse();
        let mut digits = vec![false; order.len()];
        let mut values: Vec<_> = program
            .free
            .iter()
            .map(|&s| signal_pins[s].unwrap_or(false))
            .collect();
        let mut best: Option<Vec<bool>> = None;
        loop {
            meter.charge(1, "functional witness assignment")?;
            event(
                &mut self.statistics.functional_assignments,
                "functional assignment count",
            )?;
            for (&position, &bit) in order.iter().zip(&digits) {
                values[position] = bit;
            }
            if let Some(assignment) = program.materialize(&values, &signal_pins, network, meter)? {
                let word: Vec<_> = network
                    .interface()
                    .iter()
                    .map(|&edge| assignment[edge])
                    .collect();
                if interface_is_input {
                    return Ok(Some(word));
                }
                if best.as_ref().map_or(true, |old| word < *old) {
                    best = Some(word);
                }
            }
            if !increment(&mut digits) {
                return Ok(best);
            }
        }
    }

    /// Lemma 1's original deterministic self-reduction, retained for exact
    /// comparisons and callers that explicitly require prefix count queries.
    /// Uses at most one initial count and one per unfixed interface bit.
    pub fn witness_by_counts(
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

    #[test]
    fn functional_input_witness_preserves_prefix_order_without_recounts() {
        let mut meter = Meter::new(Limits::default());
        let mut encoder = crate::encoding::Encoder::new();
        let input = encoder.input_word(4, &meter).unwrap();
        // Reversing the input interface is intentional: enumeration must follow
        // the requested interface order, rather than the program's input order.
        let reversed = crate::network::Word(input.0.iter().rev().copied().collect());
        encoder.mark_interface(&reversed, &meter).unwrap();
        let network = encoder.finish(&meter).unwrap();
        for prefix in [None, Some(false), Some(true)] {
            let mut pins = vec![None; network.edge_count()];
            pins[network.interface()[1]] = prefix;
            let mut baseline = Counter::default();
            let expected = baseline
                .witness_by_counts(&network, &pins, &mut meter)
                .unwrap();
            let mut candidate = Counter::default();
            assert_eq!(
                candidate.witness(&network, &pins, &mut meter).unwrap(),
                expected
            );
            assert_eq!(candidate.statistics.functional_assignments, 1);
            assert_eq!(candidate.statistics.contractions, 0);
            assert_eq!(candidate.statistics.witness_searches, 1);
            assert!(baseline.statistics.functional_assignments > 1);
            if prefix.is_none() {
                assert_eq!(baseline.statistics.functional_assignments, 31);
            }
        }
    }

    #[test]
    fn functional_derived_interfaces_match_prefixes_for_all_output_pins() {
        let mut meter = Meter::new(Limits::default());
        let mut encoder = crate::encoding::Encoder::new();
        let a = encoder.input_word(2, &meter).unwrap();
        let b = encoder.input_word(2, &meter).unwrap();
        let sum = encoder.integer_add(&a, &b, &meter).unwrap();
        encoder.mark_interface(&sum, &meter).unwrap();
        let network = encoder.finish(&meter).unwrap();
        for mut code in 0..27 {
            let mut pins = vec![None; network.edge_count()];
            for &edge in network.interface() {
                pins[edge] = [None, Some(false), Some(true)][code % 3];
                code /= 3;
            }
            let expected = Counter::default()
                .witness_by_counts(&network, &pins, &mut meter)
                .unwrap();
            let mut candidate = Counter::default();
            assert_eq!(
                candidate.witness(&network, &pins, &mut meter).unwrap(),
                expected
            );
            assert_eq!(candidate.statistics.last_backend, Some(Backend::Functional));
        }
    }

    #[test]
    fn functional_witness_aliases_empty_unsat_and_limits_are_exact() {
        let mut meter = Meter::new(Limits::default());
        let mut encoder = crate::encoding::Encoder::new();
        let input = encoder.input_word(1, &meter).unwrap();
        let negated = encoder.not(&input, &meter).unwrap();
        encoder.zero_test(&input, &meter).unwrap();
        encoder
            .assert_equal(
                &negated,
                &crate::encoding::Encoder::constant(1, &BigUint::one()).unwrap(),
                &meter,
            )
            .unwrap();
        encoder.mark_interface(&input, &meter).unwrap();
        let network = encoder.finish(&meter).unwrap();
        let program = network.model.as_ref().unwrap();
        let alias = program
            .edge_signals
            .iter()
            .enumerate()
            .filter(|(_, s)| **s == program.free[0])
            .map(|(e, _)| e)
            .collect::<Vec<_>>();
        assert!(alias.len() >= 2);
        let mut pins = vec![None; network.edge_count()];
        pins[alias[0]] = Some(false);
        pins[alias[1]] = Some(true);
        assert_eq!(
            Counter::default()
                .witness(&network, &pins, &mut meter)
                .unwrap(),
            None
        );
        let mut empty = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            Counter::default().witness(&network, &vec![None; network.edge_count()], &mut empty),
            Err(Error::Limit(_))
        ));
        let mut encoder = crate::encoding::Encoder::new();
        let input = encoder.input_word(1, &meter).unwrap();
        encoder
            .assert_equal(
                &input,
                &crate::encoding::Encoder::constant(1, &BigUint::zero()).unwrap(),
                &meter,
            )
            .unwrap();
        encoder
            .assert_equal(
                &input,
                &crate::encoding::Encoder::constant(1, &BigUint::one()).unwrap(),
                &meter,
            )
            .unwrap();
        let network = encoder.finish(&meter).unwrap();
        assert_eq!(
            Counter::default()
                .witness(&network, &vec![None; network.edge_count()], &mut meter)
                .unwrap(),
            None
        );
        let mut encoder = crate::encoding::Encoder::new();
        encoder.input_word(1, &meter).unwrap();
        let network = encoder.finish(&meter).unwrap();
        assert_eq!(
            Counter::default()
                .witness(&network, &vec![None; network.edge_count()], &mut meter)
                .unwrap(),
            Some(vec![])
        );
    }
}
