use crate::field::{is_prime, F};
use crate::kernel::{Circuit, Scalar, Step, Terminal};
use crate::solve::{hasse_cofactor, SplitMix64};
use crate::{BatchScratch, Curve, Error, Point, Result};
use std::collections::BTreeSet;

#[cfg(target_arch = "x86_64")]
#[path = "circuit_x86.rs"]
mod x86;

/// One rational map `f(z)=(z-r)+offset+residue/(z-r)`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct AuxiliaryMap {
    /// Pole coordinate.
    pub r: u64,
    /// Additive image offset (A in the archived formulas).
    pub offset: u64,
    /// Nonzero residue (B in the archived formulas).
    pub residue: u64,
}

/// Requested or selected arithmetic implementation.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum Backend {
    /// Choose an available SIMD backend for fields of at most 31 bits.
    #[default]
    Auto,
    /// Portable single-word/128-bit arithmetic.
    Scalar,
    /// Four coordinates per vector, with runtime CPU capability checking.
    Avx2,
    /// Eight coordinates per vector on supported compilers and CPUs.
    Avx512,
}

impl Backend {
    /// Stable name for reports.
    pub fn name(self) -> &'static str {
        match self {
            Self::Auto => "auto",
            Self::Scalar => "scalar",
            Self::Avx2 => "avx2",
            Self::Avx512 => "avx512",
        }
    }
    fn select<const B: u32>(self) -> Result<Self> {
        #[cfg(target_arch = "x86_64")]
        let avx2 = B <= 31 && std::is_x86_feature_detected!("avx2");
        #[cfg(not(target_arch = "x86_64"))]
        let avx2 = false;
        #[cfg(all(target_arch = "x86_64", auxiliary_ic_avx512))]
        let avx512 = B <= 31 && std::is_x86_feature_detected!("avx512f");
        #[cfg(not(all(target_arch = "x86_64", auxiliary_ic_avx512)))]
        let avx512 = false;
        match self {
            Self::Auto => Ok(if avx512 {
                Self::Avx512
            } else if avx2 {
                Self::Avx2
            } else {
                Self::Scalar
            }),
            Self::Scalar => Ok(Self::Scalar),
            Self::Avx2 if avx2 => Ok(Self::Avx2),
            Self::Avx512 if avx512 => Ok(Self::Avx512),
            _ => Err(Error::UnsupportedBackend),
        }
    }
    fn width(self) -> usize {
        match self {
            Self::Avx512 => 8,
            Self::Avx2 => 4,
            _ => 1,
        }
    }
}

/// Source of the factor-base membership encoding.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FactorBaseEncoding {
    /// Arbitrary coordinates and direct point subtraction.
    Direct,
    /// Complete fiber of the supplied auxiliary-curve maps.
    Auxiliary,
    /// Fiber of x^degree = coset^degree in the multiplicative group.
    Multiplicative {
        /// Cardinality of the complete raw fiber.
        degree: u32,
        /// Nonzero canonical coset representative.
        coset: u64,
    },
    /// Fiber of iterated x^2-2 on primitive norm-one traces.
    Torus {
        /// Number of doubling maps; the raw fiber has 2^depth roots.
        depth: u8,
        /// Primitive trace used to choose the terminal fiber.
        trace: u64,
    },
}

/// Target-independent random-base preparation counters, not performance evidence.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct RandomBaseStats {
    /// Public SplitMix64 seed, separate from the relation-search seed.
    pub seed: u64,
    /// Cofactor certified from the generator order and the Hasse interval.
    pub cofactor: u64,
    /// Raw 64-bit draws, including every rejected draw.
    pub draws: u64,
    /// Draws rejected to avoid reduction bias in field coordinates.
    pub field_rejections: u64,
    /// Canonical coordinates with no rational point on the target curve.
    pub non_lifts: u64,
    /// Rational lifts that become the identity after cofactor clearing.
    pub cleared_to_identity: u64,
    /// Repeated coordinates already present in the selected base.
    pub duplicate_columns: u64,
}

/// Reusable target-independent circuit and signed factor-base representatives.
///
/// Circuit constructors check complete raw fibers before discarding
/// nonliftable target coordinates. Direct controls accept arbitrary coordinates.
#[derive(Clone, Debug)]
pub struct FactorBase<const B: u32> {
    pub(crate) curve: Curve<B>,
    points: Vec<Point>,
    xs: Vec<u64>,
    squares: Vec<u64>,
    maps: Vec<AuxiliaryMap>,
    circuit: Option<Circuit>,
    encoding: FactorBaseEncoding,
    roots: usize,
    backend: Backend,
    direct_steps: Vec<Option<Point>>,
}

/// Caller-owned scratch avoids allocation and shared mutable kernel state.
#[derive(Clone, Debug)]
pub struct CandidateWorkspace {
    values: Vec<u64>,
    indices: Vec<usize>,
    active: usize,
    differences: Vec<Option<Point>>,
    batch: BatchScratch,
}

impl CandidateWorkspace {
    /// Exact scalar circuit values at the usable base coordinates, after a query.
    pub fn values(&self) -> &[u64] {
        &self.values[..self.active]
    }
    /// Indices at which the most recent exact scalar value was zero.
    pub fn indices(&self) -> &[usize] {
        &self.indices
    }
}

/// A signed two-point decomposition in the stored representative coordinates.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct SignedRelation {
    /// First representative index.
    pub i: usize,
    /// Second representative index.
    pub j: usize,
    /// Negate the first representative.
    pub negative_i: bool,
    /// Negate the second representative.
    pub negative_j: bool,
}

impl SignedRelation {
    pub(crate) fn key(self) -> Option<(usize, usize, bool)> {
        if self.i == self.j && self.negative_i != self.negative_j {
            return None;
        }
        Some((
            self.i.min(self.j),
            self.i.max(self.j),
            self.negative_i != self.negative_j,
        ))
    }
}

impl<const B: u32> FactorBase<B> {
    /// Validate a complete splitting fiber, lift it, and compile its circuit.
    /// At most 2^20 raw roots are accepted to bound preparation memory.
    pub fn new(
        curve: Curve<B>,
        maps: Vec<AuxiliaryMap>,
        terminal: u64,
        roots: &[u64],
        backend: Backend,
    ) -> Result<Self> {
        let p = F::<B>::P;
        if maps.is_empty() || maps.len() > 20 || terminal >= p {
            return Err(Error::Invalid("invalid map depth or terminal coordinate"));
        }
        if roots.len() != 1usize << maps.len() {
            return Err(Error::Invalid("complete splitting fiber required"));
        }
        if maps
            .iter()
            .any(|m| m.r >= p || m.offset >= p || m.residue == 0 || m.residue >= p)
        {
            return Err(Error::Invalid(
                "map coefficients must be canonical and residue nonzero",
            ));
        }
        let mut seen = BTreeSet::new();
        let mut points = Vec::new();
        for &root in roots {
            if root >= p || !seen.insert(root) {
                return Err(Error::Invalid(
                    "roots must be distinct canonical coordinates",
                ));
            }
            // Homogeneous evaluation avoids inversions and rejects every pole.
            let (mut n, mut d) = (root, 1);
            for map in &maps {
                let u = F::<B>::sub(n, F::<B>::mul(map.r, d));
                let ud = F::<B>::mul(u, d);
                n = F::<B>::add(
                    F::<B>::add(F::<B>::sq(u), F::<B>::mul(map.offset, ud)),
                    F::<B>::mul(map.residue, F::<B>::sq(d)),
                );
                d = ud;
            }
            if d == 0 || n != F::<B>::mul(terminal, d) {
                return Err(Error::Invalid(
                    "root does not belong to the auxiliary fiber",
                ));
            }
            if let Some(point) = curve.lift_x(root)? {
                points.push(point);
            }
        }
        let last = maps.last().expect("nonempty maps");
        let delta = F::<B>::sub(last.offset, terminal);
        let discriminant = F::<B>::sub(F::<B>::sq(delta), F::<B>::mul(4, last.residue));
        let sqrt = Self::nonzero_sqrt(discriminant)?;
        let inv2 = p.div_ceil(2);
        let left = F::<B>::mul(F::<B>::sub(sqrt, delta), inv2);
        let right = F::<B>::mul(F::<B>::sub(F::<B>::sub(0, sqrt), delta), inv2);
        let circuit = Circuit {
            first_pole: maps[0].r,
            steps: maps
                .windows(2)
                .map(|pair| Step::Rational {
                    residue: pair[0].residue,
                    delta: F::<B>::sub(pair[0].offset, pair[1].r),
                })
                .collect(),
            terminal: Terminal::split::<B>(left.min(right), left.max(right)),
            value: terminal,
        };
        Self::assemble(
            curve,
            points,
            roots.len(),
            maps,
            Some(circuit),
            FactorBaseEncoding::Auxiliary,
            backend,
        )
    }
    fn nonzero_sqrt(value: u64) -> Result<u64> {
        let root = F::<B>::pow(value, (F::<B>::P + 1) / 4);
        if root == 0 || F::<B>::sq(root) != value {
            return Err(Error::Invalid("fiber must split without repeated roots"));
        }
        Ok(root.min(F::<B>::P - root))
    }
    fn assemble(
        curve: Curve<B>,
        mut points: Vec<Point>,
        roots: usize,
        maps: Vec<AuxiliaryMap>,
        circuit: Option<Circuit>,
        encoding: FactorBaseEncoding,
        requested: Backend,
    ) -> Result<Self> {
        if points.is_empty() {
            return Err(Error::Invalid(
                "factor base contains no rational target points",
            ));
        }
        points.sort_unstable_by_key(|p| p.x());
        let backend = requested.select::<B>()?;
        let mut xs: Vec<_> = points.iter().map(|p| p.x()).collect();
        if backend != Backend::Scalar {
            let tile = 3 * backend.width();
            xs.resize(xs.len().div_ceil(tile) * tile, xs[0]);
        }
        let squares = xs.iter().map(|&x| F::<B>::sq(x)).collect();
        let direct_steps = if circuit.is_none() {
            points
                .iter()
                .flat_map(|&p| [Some(curve.neg_inner(p)), Some(p)])
                .collect()
        } else {
            Vec::new()
        };
        Ok(Self {
            curve,
            points,
            xs,
            squares,
            maps,
            circuit,
            encoding,
            roots,
            backend,
            direct_steps,
        })
    }
    /// Construct x^degree=coset^degree with degree dividing p-1 and only
    /// prime factors 2, 3 and 7. The complete fiber is generated and checked.
    pub fn multiplicative(
        curve: Curve<B>,
        degree: u32,
        coset: u64,
        backend: Backend,
    ) -> Result<Self> {
        let p = F::<B>::P;
        if !(2..=1 << 20).contains(&degree)
            || (p - 1) % u64::from(degree) != 0
            || coset == 0
            || coset >= p
        {
            return Err(Error::Invalid(
                "degree must divide p-1 and coset must be canonical nonzero",
            ));
        }
        let mut remaining = degree;
        let even = remaining % 2 == 0;
        if even {
            remaining /= 2;
        }
        let mut steps = Vec::new();
        for (prime, step) in [(3, Step::Cube), (7, Step::Septic)] {
            while remaining % prime == 0 {
                remaining /= prime;
                steps.push(step);
            }
        }
        if remaining != 1 {
            return Err(Error::Invalid(
                "degree supports at most one 2 and otherwise factors 3 and 7",
            ));
        }
        let degree64 = u64::from(degree);
        let generator = (2..p.min(4096))
            .map(|g| F::<B>::pow(g, (p - 1) / degree64))
            .find(|&g| {
                [2, 3, 7]
                    .iter()
                    .all(|&q| degree64 % q != 0 || F::<B>::pow(g, degree64 / q) != 1)
            })
            .ok_or(Error::ResourceLimit(
                "bounded multiplicative generator search exhausted",
            ))?;
        let value = F::<B>::pow(coset, degree64);
        let terminal = if even {
            let r = F::<B>::pow(coset, degree64 / 2);
            Terminal::split::<B>(r.min(p - r), r.max(p - r))
        } else {
            Terminal::Linear {
                value,
                squared: F::<B>::sq(value),
            }
        };
        let mut roots = Vec::with_capacity(degree as usize);
        let mut root = coset;
        for _ in 0..degree {
            roots.push(root);
            root = F::<B>::mul(root, generator);
        }
        let circuit = Circuit {
            first_pole: 0,
            steps,
            terminal,
            value,
        };
        Self::generated(
            curve,
            roots,
            circuit,
            FactorBaseEncoding::Multiplicative { degree, coset },
            backend,
        )
    }
    /// Construct a complete fiber of depth iterates of x^2-2. The selected
    /// trace has primitive order p+1 in the norm-one torus. No auxiliary
    /// elliptic curve or quadratic-extension arithmetic is needed.
    pub fn torus(curve: Curve<B>, depth: u8, trace: Option<u64>, backend: Backend) -> Result<Self> {
        let p = F::<B>::P;
        if depth == 0 || u32::from(depth) > 20.min(B - 2) {
            return Err(Error::Invalid(
                "torus depth must be 1..=min(20, field_bits-2)",
            ));
        }
        let primitive = |a: u64| {
            if a >= p {
                return false;
            }
            let mut v = a;
            for _ in 0..B - 1 {
                v = F::<B>::sub(F::<B>::sq(v), 2);
            }
            v == p - 2
        };
        let trace = match trace {
            Some(a) if primitive(a) => a,
            Some(_) => {
                return Err(Error::Invalid(
                    "trace must have primitive norm-one order p+1",
                ))
            }
            None => (0..p.min(4096))
                .find(|&a| primitive(a))
                .ok_or(Error::ResourceLimit(
                    "bounded primitive trace search exhausted",
                ))?,
        };
        let mut last_root = trace;
        for _ in 1..depth {
            last_root = F::<B>::sub(F::<B>::sq(last_root), 2);
        }
        let value = F::<B>::sub(F::<B>::sq(last_root), 2);
        let left = last_root.min(p - last_root);
        // Let xi have primitive order p+1 with trace a, and zeta have
        // order 2^depth with trace b. tr(xi*zeta) is a root of
        // X^2-a*b*X+(a^2+b^2-4), whose discriminant is
        // (a^2-4)*(b^2-4). Either root chooses an orbit orientation.
        // x_(i+1)=b*x_i-x_(i-1) then enumerates the entire coset fiber.
        // This replaces the inverse tree's 2^depth-2 square roots with
        // one square root (none at depth one); forward checks remain below.
        let mut step_trace = trace;
        for _ in 0..B - u32::from(depth) {
            step_trace = F::<B>::sub(F::<B>::sq(step_trace), 2);
        }
        let second = if depth == 1 {
            F::<B>::sub(0, trace)
        } else {
            let discriminant = F::<B>::mul(
                F::<B>::sub(F::<B>::sq(trace), 4),
                F::<B>::sub(F::<B>::sq(step_trace), 4),
            );
            let sqrt = Self::nonzero_sqrt(discriminant)?;
            F::<B>::mul(
                F::<B>::add(F::<B>::mul(trace, step_trace), sqrt),
                p.div_ceil(2),
            )
        };
        let count = 1usize << depth;
        let mut roots = Vec::with_capacity(count);
        roots.extend([trace, second]);
        while roots.len() < count {
            let i = roots.len();
            roots.push(F::<B>::sub(
                F::<B>::mul(step_trace, roots[i - 1]),
                roots[i - 2],
            ));
        }
        let circuit = Circuit {
            first_pole: 0,
            steps: vec![Step::TorusSquare; usize::from(depth) - 1],
            terminal: Terminal::split::<B>(left, p - left),
            value,
        };
        Self::generated(
            curve,
            roots,
            circuit,
            FactorBaseEncoding::Torus { depth, trace },
            backend,
        )
    }
    fn generated(
        curve: Curve<B>,
        roots: Vec<u64>,
        circuit: Circuit,
        encoding: FactorBaseEncoding,
        backend: Backend,
    ) -> Result<Self> {
        let mut seen = BTreeSet::new();
        let mut points = Vec::new();
        for &root in &roots {
            let value = match encoding {
                FactorBaseEncoding::Multiplicative { degree, .. } => {
                    F::<B>::pow(root, u64::from(degree))
                }
                FactorBaseEncoding::Torus { depth, .. } => {
                    let mut v = root;
                    for _ in 0..depth {
                        v = F::<B>::sub(F::<B>::sq(v), 2);
                    }
                    v
                }
                _ => unreachable!("generated field encoding"),
            };
            if root >= F::<B>::P || !seen.insert(root) || value != circuit.value {
                return Err(Error::Invalid("generated fiber is incomplete or repeated"));
            }
            if let Some(point) = curve.lift_x(root)? {
                points.push(point);
            }
        }
        Self::assemble(
            curve,
            points,
            roots.len(),
            Vec::new(),
            Some(circuit),
            encoding,
            backend,
        )
    }
    /// Build a direct-search control from arbitrary canonical x coordinates.
    /// No auxiliary curve, membership maps, or table of point pairs is used.
    /// Both signs share one batch inversion per complete subtraction scan.
    pub fn without_maps(curve: Curve<B>, roots: &[u64]) -> Result<Self> {
        if roots.is_empty() || roots.len() > 1 << 20 {
            return Err(Error::Invalid(
                "direct factor base needs 1..=2^20 coordinates",
            ));
        }
        let mut seen = BTreeSet::new();
        let mut points = Vec::new();
        for &root in roots {
            if root >= curve.modulus() || !seen.insert(root) {
                return Err(Error::Invalid(
                    "roots must be distinct canonical coordinates",
                ));
            }
            if let Some(point) = curve.lift_x(root)? {
                points.push(point);
            }
        }
        Self::assemble(
            curve,
            points,
            roots.len(),
            Vec::new(),
            None,
            FactorBaseEncoding::Direct,
            Backend::Scalar,
        )
    }
    /// Sample an ordinary direct IC base with exactly `columns` negation classes.
    /// Coordinates are sampled by rejection, lifted, and cofactor cleared; no
    /// target or known factor-base logarithms enter construction. The generator
    /// and Hasse interval must certify an exact cofactor coprime to `order`.
    /// An uncertified cofactor is refused. All rejected draws count against
    /// `max_draws`; duplicates are tested after clearing.
    pub fn random_control(
        curve: Curve<B>,
        order: u64,
        generator: Point,
        columns: usize,
        seed: u64,
        max_draws: u64,
    ) -> Result<(Self, RandomBaseStats)> {
        if !(3..1u64 << 63).contains(&order) || !is_prime(order) {
            return Err(Error::Invalid(
                "odd prime subgroup order below 2^63 required",
            ));
        }
        if columns == 0 || columns > 1 << 20 || columns as u64 > (order - 1) / 2 {
            return Err(Error::Invalid(
                "random base needs an attainable 1..=2^20 signed columns",
            ));
        }
        if !curve.contains(Some(generator)) || curve.mul_inner(Some(generator), order).is_some() {
            return Err(Error::Invalid(
                "generator does not have the claimed prime order",
            ));
        }
        let cofactor = hasse_cofactor(curve.modulus(), order)
            .filter(|h| h % order != 0)
            .ok_or(Error::Invalid(
                "random base requires a Hasse-certified cofactor coprime to the subgroup order",
            ))?;
        let mut rng = SplitMix64(seed);
        let threshold = curve.modulus().wrapping_neg() % curve.modulus();
        let mut stats = RandomBaseStats {
            seed,
            cofactor,
            ..RandomBaseStats::default()
        };
        let mut seen = BTreeSet::new();
        let mut points = Vec::with_capacity(columns);
        for _ in 0..max_draws {
            stats.draws += 1;
            let draw = rng.next();
            if draw < threshold {
                stats.field_rejections += 1;
                continue;
            }
            let x = draw % curve.modulus();
            if cofactor == 1 && seen.contains(&x) {
                stats.duplicate_columns += 1;
                continue;
            }
            let Some(point) = curve.lift_x(x)? else {
                stats.non_lifts += 1;
                continue;
            };
            let Some(point) = (if cofactor == 1 {
                Some(point)
            } else {
                curve.mul_inner(Some(point), cofactor)
            }) else {
                stats.cleared_to_identity += 1;
                continue;
            };
            if !seen.insert(point.x()) {
                stats.duplicate_columns += 1;
                continue;
            }
            let point = if point.y() > curve.modulus() - point.y() {
                curve.neg_inner(point)
            } else {
                point
            };
            points.push(point);
            if points.len() == columns {
                let base = Self::assemble(
                    curve,
                    points,
                    columns,
                    Vec::new(),
                    None,
                    FactorBaseEncoding::Direct,
                    Backend::Scalar,
                )?;
                return Ok((base, stats));
            }
        }
        Err(Error::ResourceLimit(
            "random factor-base draw budget exhausted",
        ))
    }
    /// Direct subtraction control with exactly the same signed columns and
    /// raw-root accounting. No maps or polynomial circuit are retained.
    pub fn direct_control(&self) -> Result<Self> {
        Self::assemble(
            self.curve,
            self.points.clone(),
            self.roots,
            Vec::new(),
            None,
            FactorBaseEncoding::Direct,
            Backend::Scalar,
        )
    }
    /// Whether decomposition uses the supplied auxiliary-curve maps.
    pub fn uses_auxiliary_maps(&self) -> bool {
        self.encoding == FactorBaseEncoding::Auxiliary
    }
    /// Whether decomposition evaluates a polynomial circuit (any encoding).
    pub fn uses_circuit(&self) -> bool {
        self.circuit.is_some()
    }
    /// Actual encoding and reproducible generation parameters.
    pub fn encoding(&self) -> FactorBaseEncoding {
        self.encoding
    }
    /// The target curve, distinct from the auxiliary curve supplying the maps.
    pub fn curve(&self) -> Curve<B> {
        self.curve
    }
    /// Number of membership roots before lifting and sign folding.
    pub fn raw_root_count(&self) -> usize {
        self.roots
    }
    /// One representative for each usable signed pair, ordered by x coordinate.
    pub fn representatives(&self) -> &[Point] {
        &self.points
    }
    /// Actual number of affine base points before negation folding.
    pub fn affine_point_count(&self) -> usize {
        self.points
            .iter()
            .map(|p| if p.y() == 0 { 1 } else { 2 })
            .sum()
    }
    /// Selected backend; never `Auto`.
    pub fn backend(&self) -> Backend {
        self.backend
    }
    /// Ordered rational maps supplied during preparation.
    pub fn auxiliary_maps(&self) -> &[AuxiliaryMap] {
        &self.maps
    }
    /// Terminal coordinate of the complete membership fiber.
    pub fn terminal_coordinate(&self) -> u64 {
        self.circuit.as_ref().map_or(0, |c| c.value)
    }
    /// Allocate reusable scratch for this base, including private SIMD padding.
    pub fn workspace(&self) -> CandidateWorkspace {
        CandidateWorkspace {
            values: vec![0; self.xs.len()],
            indices: Vec::with_capacity(self.points.len()),
            active: 0,
            differences: vec![None; self.direct_steps.len()],
            batch: BatchScratch::default(),
        }
    }
    /// Evaluate the exact circuit at all usable coordinates, without a GCD.
    pub fn candidates(&self, target_x: u64, workspace: &mut CandidateWorkspace) -> Result<()> {
        if !self.uses_circuit() {
            return Err(Error::Invalid(
                "direct factor base has no polynomial circuit",
            ));
        }
        if target_x >= F::<B>::P {
            return Err(Error::Invalid("noncanonical target x coordinate"));
        }
        if workspace.values.len() < self.xs.len() {
            return Err(Error::Invalid("workspace belongs to a smaller base"));
        }
        let x2 = F::<B>::sq(target_x);
        workspace.indices.clear();
        match self.backend {
            #[cfg(target_arch = "x86_64")]
            Backend::Avx2 => {
                // SAFETY: selection checked CPU support; preparation pads all
                // arrays to complete three-vector tiles, and workspace fits.
                unsafe {
                    x86::evaluate_avx2(
                        self,
                        target_x,
                        x2,
                        &mut workspace.values,
                        &mut workspace.indices,
                    )
                };
            }
            #[cfg(all(target_arch = "x86_64", auxiliary_ic_avx512))]
            Backend::Avx512 => {
                // SAFETY: same checked feature and array-length invariants.
                unsafe {
                    x86::evaluate_avx512(
                        self,
                        target_x,
                        x2,
                        &mut workspace.values,
                        &mut workspace.indices,
                    )
                };
            }
            Backend::Scalar => {
                for i in 0..self.points.len() {
                    let value = self.scalar_value(self.xs[i], self.squares[i], target_x, x2);
                    workspace.values[i] = value;
                    if value == 0 {
                        workspace.indices.push(i);
                    }
                }
            }
            _ => return Err(Error::UnsupportedBackend),
        }
        workspace.active = self.points.len();
        Ok(())
    }
    fn scalar_value(&self, x: u64, x_squared: u64, target: u64, target_squared: u64) -> u64 {
        let product = F::<B>::mul(x, target);
        let sum = F::<B>::add(x, target);
        let d = F::<B>::sub(
            F::<B>::add(x_squared, target_squared),
            F::<B>::add(product, product),
        );
        let mid = F::<B>::add(
            F::<B>::mul(sum, F::<B>::add(product, self.curve.a)),
            F::<B>::add(self.curve.b, self.curve.b),
        );
        let mut c = F::<B>::add(mid, mid);
        let mut h = F::<B>::sub(
            F::<B>::sq(F::<B>::sub(product, self.curve.a)),
            F::<B>::mul(F::<B>::mul(4, self.curve.b), sum),
        );
        let circuit = self.circuit.as_ref().expect("compiled circuit");
        let r = circuit.first_pole;
        if r != 0 {
            h = F::<B>::add(
                F::<B>::sub(h, F::<B>::mul(r, c)),
                F::<B>::mul(F::<B>::sq(r), d),
            );
            c = F::<B>::sub(c, F::<B>::mul(F::<B>::add(r, r), d));
        }
        let (mut d, mut c, mut h) = ([d], [c], [h]);
        circuit.evaluate::<B, Scalar, 1>(&mut d, &mut c, &mut h);
        h[0]
    }
    /// Find the first verified signed decomposition; no pair table is stored.
    pub fn decompose(
        &self,
        target: Point,
        workspace: &mut CandidateWorkspace,
    ) -> Result<Option<SignedRelation>> {
        if !self.curve.contains(Some(target)) {
            return Err(Error::Invalid("target is not on target curve"));
        }
        self.decompose_inner(target, workspace)
    }
    pub(crate) fn decompose_inner(
        &self,
        target: Point,
        workspace: &mut CandidateWorkspace,
    ) -> Result<Option<SignedRelation>> {
        if !self.uses_circuit() {
            return self.decompose_direct(target, workspace);
        }
        self.candidates(target.x(), workspace)?;
        for &i in &workspace.indices {
            for negative_i in [false, true] {
                let p = if negative_i {
                    self.curve.neg_inner(self.points[i])
                } else {
                    self.points[i]
                };
                let Some(q) = self
                    .curve
                    .add_inner(Some(target), Some(self.curve.neg_inner(p)))
                else {
                    continue;
                };
                let Ok(j) = self.points.binary_search_by_key(&q.x(), |p| p.x()) else {
                    continue;
                };
                let relation = SignedRelation {
                    i,
                    j,
                    negative_i,
                    negative_j: q.y() != self.points[j].y(),
                };
                if self.relation_point(relation) == Some(target) {
                    return Ok(Some(relation));
                }
            }
        }
        Ok(None)
    }
    fn decompose_direct(
        &self,
        target: Point,
        workspace: &mut CandidateWorkspace,
    ) -> Result<Option<SignedRelation>> {
        workspace
            .differences
            .resize(2 * self.points.len(), Some(target));
        workspace.differences.fill(Some(target));
        workspace.active = 0;
        workspace.indices.clear();
        self.curve.batch_add_inner(
            &mut workspace.differences,
            &self.direct_steps,
            &mut workspace.batch,
        );
        for (index, &difference) in workspace.differences.iter().enumerate() {
            let Some(q) = difference else {
                continue;
            };
            let Ok(j) = self.points.binary_search_by_key(&q.x(), |p| p.x()) else {
                continue;
            };
            let relation = SignedRelation {
                i: index / 2,
                j,
                negative_i: index % 2 == 1,
                negative_j: q.y() != self.points[j].y(),
            };
            if self.relation_point(relation) == Some(target) {
                return Ok(Some(relation));
            }
        }
        Ok(None)
    }
    /// Replay a signed row in the actual target group.
    pub fn check_relation(&self, target: Option<Point>, relation: SignedRelation) -> bool {
        relation.i < self.points.len()
            && relation.j < self.points.len()
            && self.curve.contains(target)
            && self.relation_point(relation) == target
    }
    pub(crate) fn relation_point(&self, relation: SignedRelation) -> Option<Point> {
        let (p, q) = self.signed_points(relation);
        self.curve.add_inner(Some(p), Some(q))
    }
    pub(crate) fn signed_points(&self, relation: SignedRelation) -> (Point, Point) {
        let p = self.points[relation.i];
        let q = self.points[relation.j];
        (
            if relation.negative_i {
                self.curve.neg_inner(p)
            } else {
                p
            },
            if relation.negative_j {
                self.curve.neg_inner(q)
            } else {
                q
            },
        )
    }
}
