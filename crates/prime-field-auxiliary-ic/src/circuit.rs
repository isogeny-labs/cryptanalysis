use crate::field::F;
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

#[derive(Clone, Copy, Debug)]
struct Center {
    residue: u64,
    delta: u64,
    delta_squared: u64,
}

/// Reusable target-independent circuit and signed factor-base representatives.
///
/// Construction checks the entire root fiber. The input must contain exactly
/// `2^maps.len()` distinct roots of the composed membership polynomial.
/// Nonliftable coordinates are discarded only after that completeness check.
#[derive(Clone, Debug)]
pub struct FactorBase<const B: u32> {
    pub(crate) curve: Curve<B>,
    points: Vec<Point>,
    xs: Vec<u64>,
    squares: Vec<u64>,
    maps: Vec<AuxiliaryMap>,
    centered: Vec<Center>,
    terminal: u64,
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
        if points.is_empty() {
            return Err(Error::Invalid(
                "factor base contains no rational target points",
            ));
        }
        points.sort_unstable_by_key(|p| p.x());
        let backend = backend.select::<B>()?;
        let mut xs: Vec<u64> = points.iter().map(|p| p.x()).collect();
        if backend != Backend::Scalar {
            let tile = 3 * backend.width();
            let padded = xs.len().div_ceil(tile) * tile;
            xs.resize(padded, xs[0]);
        }
        let squares = xs.iter().map(|&x| F::<B>::sq(x)).collect();
        let centered = maps
            .iter()
            .enumerate()
            .map(|(i, m)| {
                let next = maps.get(i + 1).map_or(terminal, |next| next.r);
                let delta = F::<B>::sub(m.offset, next);
                Center {
                    residue: m.residue,
                    delta,
                    delta_squared: F::<B>::sq(delta),
                }
            })
            .collect();
        Ok(Self {
            curve,
            points,
            xs,
            squares,
            maps,
            centered,
            terminal,
            roots: roots.len(),
            backend,
            direct_steps: Vec::new(),
        })
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
        if points.is_empty() {
            return Err(Error::Invalid(
                "factor base contains no rational target points",
            ));
        }
        points.sort_unstable_by_key(|p| p.x());
        let xs: Vec<_> = points.iter().map(|p| p.x()).collect();
        let squares = xs.iter().map(|&x| F::<B>::sq(x)).collect();
        let direct_steps = points
            .iter()
            .flat_map(|&p| [Some(curve.neg_inner(p)), Some(p)])
            .collect();
        Ok(Self {
            curve,
            points,
            xs,
            squares,
            maps: Vec::new(),
            centered: Vec::new(),
            terminal: 0,
            roots: roots.len(),
            backend: Backend::Scalar,
            direct_steps,
        })
    }
    /// Whether decomposition uses a complete auxiliary-map fiber.
    pub fn uses_auxiliary_maps(&self) -> bool {
        !self.maps.is_empty()
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
        self.terminal
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
        if !self.uses_auxiliary_maps() {
            return Err(Error::Invalid(
                "direct factor base has no auxiliary circuit",
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
        let mut d = F::<B>::sub(
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
        let r = self.maps[0].r;
        if r != 0 {
            h = F::<B>::add(
                F::<B>::sub(h, F::<B>::mul(r, c)),
                F::<B>::mul(F::<B>::sq(r), d),
            );
            c = F::<B>::sub(c, F::<B>::mul(F::<B>::add(r, r), d));
        }
        for (i, map) in self.centered.iter().enumerate() {
            let bd = if map.residue == 1 {
                d
            } else {
                F::<B>::mul(map.residue, d)
            };
            let nd = F::<B>::mul(h, d);
            let cc = F::<B>::sq(c);
            let norm = F::<B>::add(
                F::<B>::sq(F::<B>::sub(h, bd)),
                if map.residue == 1 {
                    cc
                } else {
                    F::<B>::mul(map.residue, cc)
                },
            );
            let cd = F::<B>::mul(c, F::<B>::add(h, bd));
            if i + 1 == self.centered.len() {
                return F::<B>::add(
                    F::<B>::add(norm, F::<B>::mul(map.delta, cd)),
                    F::<B>::mul(map.delta_squared, nd),
                );
            }
            // t = delta*nd shares the shift between both state updates:
            // norm + delta*(cd + 2*t) - delta^2*nd
            //      = norm + delta*(cd + t).
            // Two multiplications replace the previous three; doubling t
            // uses an addition.
            let t = F::<B>::mul(map.delta, nd);
            h = F::<B>::add(norm, F::<B>::mul(map.delta, F::<B>::add(cd, t)));
            c = F::<B>::add(cd, F::<B>::add(t, t));
            d = nd;
        }
        unreachable!("nonempty centered circuit")
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
        if !self.uses_auxiliary_maps() {
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
        let p = self.points[relation.i];
        let q = self.points[relation.j];
        self.curve.add_inner(
            Some(if relation.negative_i {
                self.curve.neg_inner(p)
            } else {
                p
            }),
            Some(if relation.negative_j {
                self.curve.neg_inner(q)
            } else {
                q
            }),
        )
    }
}
