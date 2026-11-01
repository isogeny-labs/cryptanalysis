//! Boolean tensor multigraphs, exact pins, and parsimonious-program metadata.

use crate::{integrity, invalid, BigUint, Meter, Result};
use num_traits::{One, Zero};
use std::collections::BTreeSet;
use std::sync::Arc;

/// One tensor predicate, with a fixed and explicitly ordered port list.
pub trait Predicate: Send + Sync {
    /// Number of incident bit ports, counting parallel edges separately.
    fn arity(&self) -> usize;
    /// Evaluate the Boolean predicate exactly.
    fn evaluate(&self, ports: &[bool], meter: &mut Meter) -> Result<bool>;
}

/// A native predicate closure with explicit arity.
pub struct FnPredicate {
    arity: usize,
    function: Arc<dyn Fn(&[bool], &mut Meter) -> Result<bool> + Send + Sync>,
}
impl FnPredicate {
    /// Construct a predicate. Contraction complexity assumptions on user-supplied
    /// predicate evaluation remain the caller's responsibility.
    pub fn new(
        arity: usize,
        function: impl Fn(&[bool], &mut Meter) -> Result<bool> + Send + Sync + 'static,
    ) -> Self {
        Self {
            arity,
            function: Arc::new(function),
        }
    }
}
impl Predicate for FnPredicate {
    fn arity(&self) -> usize {
        self.arity
    }
    fn evaluate(&self, ports: &[bool], meter: &mut Meter) -> Result<bool> {
        if ports.len() != self.arity {
            return Err(invalid("predicate port arity"));
        }
        (self.function)(ports, meter)
    }
}

#[derive(Clone)]
pub(crate) struct Vertex {
    pub predicate: Arc<dyn Predicate>,
    pub edges: Vec<usize>,
}

/// Validated finite undirected multigraph without self-loops. Each edge occurs
/// once at each endpoint; parallel edges retain distinct ordered ports.
#[derive(Clone)]
pub struct Network {
    pub(crate) vertices: Vec<Vertex>,
    pub(crate) edges: Vec<(usize, usize)>,
    pub(crate) interface: Vec<usize>,
    pub(crate) model: Option<Arc<Program>>,
}
impl Network {
    /// Number of bit edges.
    pub fn edge_count(&self) -> usize {
        self.edges.len()
    }
    /// Number of vertices, including isolated scalar predicates.
    pub fn vertex_count(&self) -> usize {
        self.vertices.len()
    }
    /// Maximum degree, counting multiplicities.
    pub fn maximum_degree(&self) -> usize {
        self.vertices
            .iter()
            .map(|v| v.edges.len())
            .max()
            .unwrap_or(0)
    }
    /// Explicit interface edges in language-word order.
    pub fn interface(&self) -> &[usize] {
        &self.interface
    }
    /// Evaluate a full edge assignment, independently of program hints.
    pub fn evaluate(&self, assignment: &[bool], meter: &mut Meter) -> Result<bool> {
        if assignment.len() != self.edges.len() {
            return Err(invalid("edge assignment width"));
        }
        for vertex in &self.vertices {
            meter.charge(1, "Boolean vertex evaluation")?;
            let ports: Vec<_> = vertex.edges.iter().map(|&e| assignment[e]).collect();
            if !vertex.predicate.evaluate(&ports, meter)? {
                return Ok(false);
            }
        }
        Ok(true)
    }
    /// Validate a pin vector; each edge is fixed once or remains free.
    pub fn check_pins(&self, pins: &[Option<bool>]) -> Result<()> {
        if pins.len() != self.edge_count() {
            return Err(invalid("pin vector width"));
        }
        Ok(())
    }
    /// Number of free input bits in a built-in parsimonious encoding.
    pub fn input_bit_count(&self) -> Option<usize> {
        self.model.as_ref().map(|p| p.free.len())
    }
    /// Construct and independently check the full witness determined by free
    /// inputs. Arbitrary predicate graphs do not have this optional metadata.
    pub fn witness_from_input_bits(
        &self,
        bits: &[bool],
        meter: &mut Meter,
    ) -> Result<Option<Vec<bool>>> {
        let Some(program) = &self.model else {
            return Err(invalid("network has no built-in program witness"));
        };
        program.materialize(bits, &vec![None; program.signals], self, meter)
    }
}

/// A graph builder for arbitrary native predicates. It adds no program hints.
#[derive(Default)]
pub struct GraphBuilder {
    vertices: Vec<Vertex>,
    edges: Vec<(usize, usize)>,
}
impl GraphBuilder {
    /// Start an empty graph.
    pub fn new() -> Self {
        Self::default()
    }
    /// Add a predicate; all its ports must subsequently be attached.
    pub fn vertex(&mut self, predicate: impl Predicate + 'static) -> usize {
        self.vertex_arc(Arc::new(predicate))
    }
    pub(crate) fn vertex_arc(&mut self, predicate: Arc<dyn Predicate>) -> usize {
        let index = self.vertices.len();
        self.vertices.push(Vertex {
            predicate,
            edges: Vec::new(),
        });
        index
    }
    /// Attach a distinct edge to the next port of each endpoint.
    pub fn edge(&mut self, left: usize, right: usize, meter: &mut Meter) -> Result<usize> {
        if left == right || left >= self.vertices.len() || right >= self.vertices.len() {
            return Err(invalid("edge endpoints or self-loop"));
        }
        meter.vector(self.edges.len() + 1, "Boolean graph edges")?;
        let edge = self.edges.len();
        self.edges.push((left, right));
        self.vertices[left].edges.push(edge);
        self.vertices[right].edges.push(edge);
        Ok(edge)
    }
    /// Freeze the graph after checking all arities and distinct interface edges.
    pub fn finish(self, interface: Vec<usize>) -> Result<Network> {
        if self
            .vertices
            .iter()
            .any(|v| v.edges.len() != v.predicate.arity())
        {
            return Err(invalid("unattached predicate ports"));
        }
        let mut seen = BTreeSet::new();
        if interface
            .iter()
            .any(|&e| e >= self.edges.len() || !seen.insert(e))
        {
            return Err(invalid("interface must contain distinct graph edges"));
        }
        Ok(Network {
            vertices: self.vertices,
            edges: self.edges,
            interface,
            model: None,
        })
    }
}

#[derive(Clone, Copy, Debug)]
pub(crate) enum Bit {
    Constant(bool),
    Signal(usize),
}
impl Bit {
    pub(crate) fn read(self, values: &[bool]) -> bool {
        match self {
            Self::Constant(b) => b,
            Self::Signal(i) => values[i],
        }
    }
}

/// A little-endian word in an encoding builder. Constants need no graph edges.
#[derive(Clone, Debug)]
pub struct Word(pub(crate) Vec<Bit>);
impl Word {
    /// Number of bits, including hardcoded constants.
    pub fn width(&self) -> usize {
        self.0.len()
    }
    pub(crate) fn value(&self, values: &[bool]) -> BigUint {
        let mut out = BigUint::zero();
        for (i, &bit) in self.0.iter().enumerate() {
            if bit.read(values) {
                out.set_bit(i as u64, true);
            }
        }
        out
    }
}

pub(crate) type ValueFunction =
    Arc<dyn Fn(&[BigUint], &mut Meter) -> Result<Vec<BigUint>> + Send + Sync>;

#[derive(Clone)]
pub(crate) enum Step {
    Define {
        inputs: Vec<Word>,
        outputs: Vec<Word>,
        function: ValueFunction,
    },
    Check {
        vertex: usize,
        ports: Vec<Bit>,
    },
}

// Only the built-in, parsimonious arithmetic encoders construct this metadata.
// Arbitrary caller predicates cannot attach hints or assert their uniqueness.
#[derive(Clone)]
pub(crate) struct Program {
    pub free: Vec<usize>,
    pub signals: usize,
    pub steps: Vec<Step>,
    pub edge_signals: Vec<usize>,
}

impl Program {
    pub(crate) fn signal_pins(&self, pins: &[Option<bool>]) -> Result<Option<Vec<Option<bool>>>> {
        if pins.len() != self.edge_signals.len() {
            return Err(invalid("program pin shape"));
        }
        let mut out = vec![None; self.signals];
        for (edge, &pin) in pins.iter().enumerate() {
            if let Some(bit) = pin {
                let signal = self.edge_signals[edge];
                if let Some(old) = out[signal] {
                    if old != bit {
                        return Ok(None);
                    }
                }
                out[signal] = Some(bit);
            }
        }
        Ok(Some(out))
    }

    pub(crate) fn materialize(
        &self,
        free_values: &[bool],
        signal_pins: &[Option<bool>],
        network: &Network,
        meter: &mut Meter,
    ) -> Result<Option<Vec<bool>>> {
        if free_values.len() != self.free.len() || signal_pins.len() != self.signals {
            return Err(invalid("program input shape"));
        }
        meter.vector(self.signals, "program signal assignment")?;
        let mut values = vec![false; self.signals];
        for (&signal, &value) in self.free.iter().zip(free_values) {
            if signal_pins[signal].is_some_and(|p| p != value) {
                return Ok(None);
            }
            values[signal] = value;
        }
        for step in &self.steps {
            meter.charge(1, "parsimonious program evaluation")?;
            match step {
                Step::Define {
                    inputs,
                    outputs,
                    function,
                } => {
                    let input: Vec<_> = inputs.iter().map(|word| word.value(&values)).collect();
                    let output = function(&input, meter)?;
                    if output.len() != outputs.len() {
                        return Err(integrity("program result arity"));
                    }
                    for (word, value) in outputs.iter().zip(output) {
                        if value.bits() > word.width() as u64 {
                            return Ok(None);
                        }
                        for (i, &bit) in word.0.iter().enumerate() {
                            let Bit::Signal(signal) = bit else {
                                return Err(integrity("program output is not a fresh signal"));
                            };
                            let value = value.bit(i as u64);
                            if signal_pins[signal].is_some_and(|p| p != value) {
                                return Ok(None);
                            }
                            values[signal] = value;
                        }
                    }
                }
                Step::Check { vertex, ports } => {
                    let bits: Vec<_> = ports.iter().map(|&bit| bit.read(&values)).collect();
                    if !network.vertices[*vertex].predicate.evaluate(&bits, meter)? {
                        return Ok(None);
                    }
                }
            }
        }
        let assignment: Vec<_> = self
            .edge_signals
            .iter()
            .map(|&signal| values[signal])
            .collect();
        if !network.evaluate(&assignment, meter)? {
            return Err(integrity("program witness disagrees with graph"));
        }
        Ok(Some(assignment))
    }
}

/// Increment little-endian Boolean digits; return false after the last word.
pub(crate) fn increment(bits: &mut [bool]) -> bool {
    for bit in bits {
        if !*bit {
            *bit = true;
            return true;
        }
        *bit = false;
    }
    false
}

/// Independent exact reference contraction over all unpinned edge bits.
pub fn direct_count(
    network: &Network,
    pins: &[Option<bool>],
    meter: &mut Meter,
) -> Result<BigUint> {
    network.check_pins(pins)?;
    let free: Vec<_> = pins
        .iter()
        .enumerate()
        .filter_map(|(e, p)| p.is_none().then_some(e))
        .collect();
    let mut digits = vec![false; free.len()];
    let mut answer = BigUint::zero();
    loop {
        meter.charge(1, "direct Boolean edge assignment")?;
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Limits;
    #[test]
    fn parallel_edges_pins_and_isolated_scalars() {
        let mut meter = Meter::new(Limits::default());
        let mut b = GraphBuilder::new();
        let left = b.vertex(FnPredicate::new(2, |bits, _| Ok(bits[0] == bits[1])));
        let right = b.vertex(FnPredicate::new(2, |_, _| Ok(true)));
        b.vertex(FnPredicate::new(0, |_, _| Ok(true)));
        let e0 = b.edge(left, right, &mut meter).unwrap();
        let e1 = b.edge(left, right, &mut meter).unwrap();
        let graph = b.finish(vec![e0, e1]).unwrap();
        assert_eq!(
            direct_count(&graph, &[None, None], &mut meter).unwrap(),
            BigUint::from(2u8)
        );
        assert_eq!(
            direct_count(&graph, &[Some(false), None], &mut meter).unwrap(),
            BigUint::one()
        );
        assert_eq!(
            direct_count(&graph, &[Some(false), Some(true)], &mut meter).unwrap(),
            BigUint::zero()
        );
        let mut b = GraphBuilder::new();
        b.vertex(FnPredicate::new(0, |_, _| Ok(false)));
        assert_eq!(
            direct_count(&b.finish(vec![]).unwrap(), &[], &mut meter).unwrap(),
            BigUint::zero()
        );
    }
    #[test]
    fn incomplete_graphs_and_duplicate_interfaces_are_rejected() {
        let mut b = GraphBuilder::new();
        b.vertex(FnPredicate::new(1, |_, _| Ok(true)));
        assert!(b.finish(vec![]).is_err());
    }
}
