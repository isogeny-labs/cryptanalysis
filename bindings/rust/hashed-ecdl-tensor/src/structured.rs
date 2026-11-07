//! Bounded rational two-isogeny fibre predicates and exact prefix recovery.
//!
//! This is an opt-in development reference. Ordered signed tuples permit
//! repetitions and inverse pairs. No cofactor projection, scalar labels,
//! generic subgroup log table, or source asymptotic guarantee is used.
use crate::arithmetic::{RandomSource, SquareRootContext};
use crate::contraction::Counter;
use crate::curve::{Curve, Point};
use crate::encoding::{Encoder, PointWords};
use crate::network::Network;
use crate::{integrity, invalid, overflow, BigUint, Meter, Result};
use num_traits::{One, Zero};
use std::collections::BTreeMap;
use std::sync::Arc;

/// Abscissa fibres of the rational two-torsion quotient, in translated
/// coordinates u=x-t: image abscissa u+3t+(3t²+a)/u. The kernel is excluded.
#[derive(Clone, Debug)]
pub struct IsogenyFibres {
    identity: (BigUint, BigUint, BigUint, BigUint),
    kernel_x: BigUint,
    images: Vec<BigUint>,
}
impl IsogenyFibres {
    /// Validate a rational two-torsion root and a nonempty distinct image set.
    /// This special family requires rational two-torsion on the source curve;
    /// it does not parameterize every auxiliary PKM isogeny construction.
    pub fn new(
        curve: &Curve,
        kernel_x: BigUint,
        images: Vec<BigUint>,
        meter: &mut Meter,
    ) -> Result<Self> {
        meter.vector(images.len(), "isogeny image set")?;
        meter.charge(images.len() as u64 + 1, "isogeny fibre validation")?;
        let p = curve.modulus();
        if &kernel_x >= p
            || !curve.contains(&Point::Affine {
                x: kernel_x.clone(),
                y: BigUint::zero(),
            })
            || images.is_empty()
            || images.iter().any(|x| x >= p)
        {
            return Err(invalid("two-isogeny fibre parameters"));
        }
        let mut sorted = images.clone();
        sorted.sort();
        sorted.dedup();
        if sorted.len() != images.len() {
            return Err(invalid("duplicate isogeny images"));
        }
        Ok(Self {
            identity: (
                curve.modulus().clone(),
                curve.a().clone(),
                curve.b().clone(),
                curve.order().clone(),
            ),
            kernel_x,
            images: sorted,
        })
    }
    fn check_curve(&self, curve: &Curve) -> Result<()> {
        if self.identity
            != (
                curve.modulus().clone(),
                curve.a().clone(),
                curve.b().clone(),
                curve.order().clone(),
            )
        {
            return Err(invalid("isogeny fibre curve/subgroup identity"));
        }
        Ok(())
    }
    fn coefficients(&self, curve: &Curve) -> (BigUint, BigUint) {
        let p = curve.modulus();
        (
            (BigUint::from(3u8) * &self.kernel_x) % p,
            (BigUint::from(3u8) * &self.kernel_x * &self.kernel_x + curve.a()) % p,
        )
    }
    /// Independently evaluate rational, nonkernel membership and actual [r]P=O.
    /// Denominators are tested without inversion; neither sign is projected.
    pub fn contains(&self, curve: &Curve, point: &Point, meter: &mut Meter) -> Result<bool> {
        self.check_curve(curve)?;
        meter.charge(1, "structured membership")?;
        let Point::Affine { x, .. } = point else {
            return Ok(false);
        };
        if !curve.in_subgroup(point, meter)? || x == &self.kernel_x {
            return Ok(false);
        }
        let p = curve.modulus();
        let u = (x + p - &self.kernel_x) % p;
        let (a, b) = self.coefficients(curve);
        for image in &self.images {
            meter.charge(1, "isogeny fibre test")?;
            if (&u * &u + (&a + p - image) * &u + &b) % p == BigUint::zero() {
                return Ok(true);
            }
        }
        Ok(false)
    }
    fn encode(
        &self,
        curve: &Curve,
        point: &PointWords,
        encoder: &mut Encoder,
        meter: &Meter,
    ) -> Result<()> {
        let p = curve.modulus();
        let width = p.bits() as usize;
        let c = |v: &BigUint| Encoder::constant(width, v);
        let u = encoder.modular_subtract(&point.x, &c(&self.kernel_x)?, p, meter)?;
        let is_kernel = encoder.zero_test(&u, meter)?;
        encoder.assert_equal(&is_kernel, &Encoder::constant(1, &BigUint::zero())?, meter)?;
        let uu = encoder.modular_multiply(&u, &u, p, meter)?;
        let (a, b) = self.coefficients(curve);
        let mut product = c(&BigUint::one())?;
        for image in &self.images {
            let linear = encoder.modular_multiply(&u, &c(&((&a + p - image) % p))?, p, meter)?;
            let factor = encoder.modular_add(&uu, &linear, p, meter)?;
            let factor = encoder.modular_add(&factor, &c(&b)?, p, meter)?;
            product = encoder.modular_multiply(&product, &factor, p, meter)?;
        }
        encoder.assert_equal(&product, &c(&BigUint::zero())?, meter)?;
        let mut sum = Encoder::constant_point(curve, &Point::Infinity)?;
        let mut base = point.clone();
        let mut scalar = curve.order().clone();
        while !scalar.is_zero() {
            if scalar.bit(0) {
                sum = encoder.point_add(curve, &sum, &base, meter)?;
            }
            scalar >>= 1;
            if !scalar.is_zero() {
                base = encoder.point_add(curve, &base, &base, meter)?;
            }
        }
        encoder.assert_point_equal(
            &sum,
            &Encoder::constant_point(curve, &Point::Infinity)?,
            meter,
        )
    }
}

#[derive(Clone)]
struct Node {
    bit: usize,
    low: usize,
    high: usize,
}
/// A target-independent reduced decision diagram of exact *local membership*.
/// Exhaustive and quadratic-root constructors have explicit work/storage bounds.
/// This is not a compressed message for the whole summation predicate.
pub struct MembershipMessage {
    curve: Curve,
    fibres: IsogenyFibres,
    nodes: Vec<Node>,
    root: usize,
    width: usize,
    examined: u64,
    candidates: u64,
}
impl MembershipMessage {
    /// Exhaustive small-field reference compilation. Node/work/precision limits
    /// fail closed. No table of relation targets, tuples or known logs is built.
    pub fn compile(curve: &Curve, fibres: &IsogenyFibres, meter: &mut Meter) -> Result<Self> {
        fibres.check_curve(curve)?;
        let width = curve.modulus().bits() as usize;
        meter.bits(width, "membership coordinate width")?;
        let bits = width
            .checked_mul(2)
            .ok_or_else(|| overflow("membership coordinate bits"))?;
        meter.vector(bits, "membership coordinate bits")?;
        let encodings = 1u64
            .checked_shl(u32::try_from(bits).map_err(|_| overflow("membership enumeration"))?)
            .ok_or_else(|| overflow("membership enumeration"))?;
        if encodings > meter.limits.steps.saturating_sub(meter.used) {
            return Err(crate::Error::Limit(
                "membership enumeration lower bound".into(),
            ));
        }
        let mut out = Self {
            curve: curve.clone(),
            fibres: fibres.clone(),
            nodes: Vec::new(),
            root: 0,
            width,
            examined: 0,
            candidates: 0,
        };
        out.root = out.build(0, bits, &mut vec![false; bits], &mut BTreeMap::new(), meter)?;
        Ok(out)
    }
    /// Compile the same local message by solving each quadratic fibre, lifting
    /// both rational y signs and filtering [r]P=O. This enumerates membership
    /// points, not all field encodings, target counts, or relation tuples.
    /// Setup root extraction, filtering, trie construction and storage are
    /// charged/bounded. No compression or asymptotic solver benefit is promised.
    pub fn from_fibres(
        curve: &Curve,
        fibres: &IsogenyFibres,
        rng: &mut impl RandomSource,
        meter: &mut Meter,
    ) -> Result<Self> {
        fibres.check_curve(curve)?;
        let width = curve.modulus().bits() as usize;
        meter.bits(width, "membership coordinate width")?;
        let bits = width
            .checked_mul(2)
            .ok_or_else(|| overflow("membership coordinate bits"))?;
        meter.vector(bits, "membership coordinate bits")?;
        let mut out = Self {
            curve: curve.clone(),
            fibres: fibres.clone(),
            nodes: Vec::new(),
            root: 0,
            width,
            examined: 0,
            candidates: 0,
        };
        let p = curve.modulus();
        let (a, b) = fibres.coefficients(curve);
        let inv_two = (p + BigUint::one()) >> 1usize;
        let mut roots = SquareRootContext::new(p)?;
        let mut points = std::collections::BTreeSet::new();
        for image in &fibres.images {
            meter.charge(1, "quadratic fibre construction")?;
            let linear = (&a + p - image) % p;
            let disc = (&linear * &linear + p - (BigUint::from(4u8) * &b) % p) % p;
            let Some(root) = roots.root(&disc, rng, meter)? else {
                continue;
            };
            for root in [root.clone(), (p - &root) % p] {
                let u = ((p - &linear + root) * &inv_two) % p;
                if u.is_zero() {
                    continue;
                }
                let x = (&u + &fibres.kernel_x) % p;
                let rhs = (&x * &x * &x + curve.a() * &x + curve.b()) % p;
                let Some(y) = roots.root(&rhs, rng, meter)? else {
                    continue;
                };
                for y in [y.clone(), (p - &y) % p] {
                    meter.charge(1, "fibre lift candidate")?;
                    out.candidates = out
                        .candidates
                        .checked_add(1)
                        .ok_or_else(|| overflow("fibre candidates"))?;
                    let point = Point::Affine { x: x.clone(), y };
                    if fibres.contains(curve, &point, meter)? {
                        meter.vector(points.len() + 1, "membership points")?;
                        points.insert(point);
                    }
                }
            }
        }
        let words_len = points
            .len()
            .checked_mul(bits)
            .ok_or_else(|| overflow("membership words"))?;
        meter.vector(words_len, "membership words")?;
        let mut words = Vec::with_capacity(points.len());
        for point in points {
            let Point::Affine { x, y } = point else {
                return Err(integrity("finite fibre point"));
            };
            meter.charge(bits as u64, "membership word construction")?;
            words.push(
                (0..width)
                    .map(|i| x.bit(i as u64))
                    .chain((0..width).map(|i| y.bit(i as u64)))
                    .collect::<Vec<_>>(),
            );
        }
        let word_refs = words.iter().map(Vec::as_slice).collect::<Vec<_>>();
        out.root = out.sparse_build(0, bits, &word_refs, &mut BTreeMap::new(), meter)?;
        Ok(out)
    }
    fn sparse_build(
        &mut self,
        bit: usize,
        bits: usize,
        words: &[&[bool]],
        unique: &mut BTreeMap<(usize, usize, usize), usize>,
        meter: &mut Meter,
    ) -> Result<usize> {
        meter.charge(1, "sparse membership diagram construction")?;
        if words.is_empty() {
            return Ok(0);
        }
        if bit == bits {
            return Ok(1);
        }
        // Keep each recursive allocation inside the explicit vector bound.
        meter.vector(
            words
                .len()
                .checked_mul(bits)
                .ok_or_else(|| overflow("membership split"))?,
            "membership split",
        )?;
        meter.charge(words.len() as u64, "membership split")?;
        let (low_words, high_words): (Vec<_>, Vec<_>) =
            words.iter().copied().partition(|word| !word[bit]);
        let low = self.sparse_build(bit + 1, bits, &low_words, unique, meter)?;
        let high = self.sparse_build(bit + 1, bits, &high_words, unique, meter)?;
        self.intern(bit, low, high, unique, meter)
    }
    fn build(
        &mut self,
        bit: usize,
        bits: usize,
        word: &mut [bool],
        unique: &mut BTreeMap<(usize, usize, usize), usize>,
        meter: &mut Meter,
    ) -> Result<usize> {
        meter.charge(1, "membership diagram construction")?;
        if bit == bits {
            self.examined = self
                .examined
                .checked_add(1)
                .ok_or_else(|| overflow("membership assignments"))?;
            let point = decode_coordinates(word, self.width);
            return Ok(usize::from(self.fibres.contains(
                &self.curve,
                &point,
                meter,
            )?));
        }
        word[bit] = false;
        let low = self.build(bit + 1, bits, word, unique, meter)?;
        word[bit] = true;
        let high = self.build(bit + 1, bits, word, unique, meter)?;
        self.intern(bit, low, high, unique, meter)
    }
    fn intern(
        &mut self,
        bit: usize,
        low: usize,
        high: usize,
        unique: &mut BTreeMap<(usize, usize, usize), usize>,
        meter: &Meter,
    ) -> Result<usize> {
        if low == high {
            return Ok(low);
        }
        if let Some(&id) = unique.get(&(bit, low, high)) {
            return Ok(id);
        }
        meter.vector(self.nodes.len() + 1, "membership diagram nodes")?;
        let id = self.nodes.len() + 2;
        self.nodes.push(Node { bit, low, high });
        unique.insert((bit, low, high), id);
        Ok(id)
    }
    /// Number of retained nonterminal nodes; allocator overhead is not bytes.
    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }
    /// Exhaustive coordinate encodings visited (zero for `from_fibres`).
    pub fn assignments_examined(&self) -> u64 {
        self.examined
    }
    /// Rational signed lifts tested by `from_fibres`, before deduplication.
    pub fn candidate_points_checked(&self) -> u64 {
        self.candidates
    }
    /// Evaluate this local membership message on a canonical finite point.
    pub fn contains(&self, point: &Point, meter: &mut Meter) -> Result<bool> {
        meter.charge(1, "membership message point")?;
        let Point::Affine { x, y } = point else {
            return Ok(false);
        };
        if x >= self.curve.modulus() || y >= self.curve.modulus() {
            return Ok(false);
        }
        meter.bits(self.width, "membership coordinate width")?;
        meter.vector(2 * self.width, "membership query word")?;
        let word = (0..self.width)
            .map(|i| x.bit(i as u64))
            .chain((0..self.width).map(|i| y.bit(i as u64)))
            .collect::<Vec<_>>();
        self.accepts(&word, meter)
    }
    fn accepts(&self, word: &[bool], meter: &mut Meter) -> Result<bool> {
        let mut at = self.root;
        while at >= 2 {
            meter.charge(1, "membership diagram query")?;
            let node = &self.nodes[at - 2];
            at = if word[node.bit] { node.high } else { node.low };
        }
        Ok(at == 1)
    }
}
fn decode_coordinates(word: &[bool], width: usize) -> Point {
    let value = |bits: &[bool]| {
        bits.iter()
            .enumerate()
            .fold(BigUint::zero(), |mut v, (i, &bit)| {
                if bit {
                    v.set_bit(i as u64, true);
                }
                v
            })
    };
    Point::Affine {
        x: value(&word[..width]),
        y: value(&word[width..]),
    }
}

/// One immutable arithmetic network with a public target input boundary.
/// A network can be queried repeatedly; it contains no target-scalar labels.
pub struct Prepared {
    curve: Curve,
    fibres: IsogenyFibres,
    network: Network,
    arity: usize,
    point_bits: usize,
}
impl Prepared {
    /// Build the membership-and-complete-summation predicate. An optional shared
    /// local message replaces membership circuits, not the complete curve charts.
    pub fn new(
        curve: &Curve,
        fibres: &IsogenyFibres,
        arity: usize,
        message: Option<Arc<MembershipMessage>>,
        meter: &mut Meter,
    ) -> Result<Self> {
        if !(2..=8).contains(&arity) {
            return Err(invalid("structured arity must be 2..=8"));
        }
        fibres.check_curve(curve)?;
        if let Some(ref m) = message {
            if m.curve.modulus() != curve.modulus()
                || m.curve.a() != curve.a()
                || m.curve.b() != curve.b()
                || m.curve.order() != curve.order()
                || m.fibres.kernel_x != fibres.kernel_x
                || m.fibres.images != fibres.images
            {
                return Err(invalid("membership message identity"));
            }
        }
        let mut encoder = Encoder::new();
        let mut sum = Encoder::constant_point(curve, &Point::Infinity)?;
        for _ in 0..arity {
            let point = encoder.input_point(curve, false, meter)?;
            if let Some(ref m) = message {
                let m = Arc::clone(m);
                encoder.constraint(
                    &[point.x.clone(), point.y.clone()],
                    move |v, work| {
                        let bits = (0..m.width)
                            .map(|i| v[0].bit(i as u64))
                            .chain((0..m.width).map(|i| v[1].bit(i as u64)))
                            .collect::<Vec<_>>();
                        m.accepts(&bits, work)
                    },
                    meter,
                )?;
            } else {
                fibres.encode(curve, &point, &mut encoder, meter)?;
            }
            // Constant finite flags are retained as fixed interface bits.
            encoder.mark_point_interface(&point, meter)?;
            sum = encoder.point_add(curve, &sum, &point, meter)?;
        }
        let target = encoder.input_point(curve, true, meter)?;
        encoder.mark_point_interface(&target, meter)?;
        encoder.assert_point_equal(&sum, &target, meter)?;
        Ok(Self {
            curve: curve.clone(),
            fibres: fibres.clone(),
            network: encoder.finish(meter)?,
            arity,
            point_bits: 1 + 2 * curve.modulus().bits() as usize,
        })
    }
    /// The actual graph for bounded structural inspection and independent checks.
    pub fn network(&self) -> &Network {
        &self.network
    }
    fn pins(&self, target: &Point, meter: &mut Meter) -> Result<Vec<Option<bool>>> {
        if !self.curve.in_subgroup(target, meter)? {
            return Err(invalid("structured target outside subgroup"));
        }
        meter.vector(self.network.edge_count(), "structured pins")?;
        let mut pins = vec![None; self.network.edge_count()];
        let width = (self.point_bits - 1) / 2;
        let (flag, x, y) = match target {
            Point::Infinity => (true, BigUint::zero(), BigUint::zero()),
            Point::Affine { x, y } => (false, x.clone(), y.clone()),
        };
        let word = std::iter::once(flag)
            .chain((0..width).map(|i| x.bit(i as u64)))
            .chain((0..width).map(|i| y.bit(i as u64)));
        for (&edge, bit) in self.network.interface()[self.arity * self.point_bits..]
            .iter()
            .zip(word)
        {
            pins[edge] = Some(bit);
        }
        Ok(pins)
    }
    /// Exact ordered signed-tuple count. Resource errors never become zero.
    pub fn count(
        &self,
        target: &Point,
        counter: &mut Counter,
        meter: &mut Meter,
    ) -> Result<BigUint> {
        counter.count(&self.network, &self.pins(target, meter)?, meter)
    }
    /// Count-guided interface-bit self-reduction, followed by arithmetic replay.
    /// None is returned only after an exact zero count.
    pub fn witness(
        &self,
        target: &Point,
        counter: &mut Counter,
        meter: &mut Meter,
    ) -> Result<Option<Vec<Point>>> {
        let pins = self.pins(target, meter)?;
        let Some(word) = counter.witness_by_counts(&self.network, &pins, meter)? else {
            return Ok(None);
        };
        let points = word[..self.arity * self.point_bits]
            .chunks_exact(self.point_bits)
            .map(|w| decode_coordinates(&w[1..], (self.point_bits - 1) / 2))
            .collect::<Vec<_>>();
        let mut sum = Point::Infinity;
        for point in &points {
            if !self.fibres.contains(&self.curve, point, meter)? {
                return Err(integrity("structured witness membership"));
            }
            sum = self.curve.add(&sum, point, meter)?;
        }
        if sum != *target {
            return Err(integrity("structured witness sum"));
        }
        Ok(Some(points))
    }
}
