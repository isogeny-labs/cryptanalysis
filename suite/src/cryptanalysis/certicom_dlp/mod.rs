//! Exact-curve rho, BSGS, and index calculus for the Certicom 131-bit challenges.
//!
//! Field elements, scalar bounds, relation coefficients and recovered logs retain
//! their full width. Work limits return an incomplete result; no method switches
//! to a smaller curve or to another discrete-log algorithm.

use std::collections::HashMap;
use std::hash::{Hash, Hasher};

use num_bigint::BigUint;
use num_traits::{One, ToPrimitive, Zero};
use serde::Serialize;
use serde_json::{json, Value};

use crate::binary_ecc::curve::{self as binary, BinaryCurve, BinaryPoint};
use crate::binary_ecc::F2mElement;
use crate::ecc::{certicom, CurveParams, Point};

mod index;
pub use index::{index_calculus, index_calculus_on_device, IndexInput, IndexReport};
mod gpu;
pub use gpu::{bsgs_on_device, rho_on_device};
pub mod worker;
use worker::ExecutionReport;

#[cfg(all(test, unix))]
mod device_tests;
#[cfg(test)]
mod tests;

/// A point in one of the two exact challenge fields.
#[derive(Clone, Debug, PartialEq)]
pub enum ChallengePoint {
    Prime(Point),
    Binary(BinaryPoint),
}

#[derive(Clone)]
enum Curve {
    Prime(CurveParams),
    Binary(Box<BinaryCurve>),
}

/// The complete field, curve, generator and subgroup for one challenge.
#[derive(Clone)]
pub struct ChallengeGroup {
    name: &'static str,
    curve: Curve,
    published: ChallengePoint,
}

impl ChallengeGroup {
    pub fn by_name(name: &str) -> Result<Self, String> {
        if let Some((curve, target)) = certicom::prime_challenge(name) {
            return Ok(Self {
                name: "eccp-131",
                curve: Curve::Prime(curve),
                published: ChallengePoint::Prime(target),
            });
        }
        if let Some((curve, target)) = certicom::binary_challenge(name) {
            return Ok(Self {
                name: "ecc2-131",
                curve: Curve::Binary(Box::new(curve)),
                published: ChallengePoint::Binary(target),
            });
        }
        Err(format!(
            "unknown Certicom challenge {name:?}; use ECC2-131 or ECCp-131 (130 aliases accepted)"
        ))
    }

    pub fn name(&self) -> &'static str {
        self.name
    }

    pub fn order(&self) -> &BigUint {
        match &self.curve {
            Curve::Prime(c) => &c.n,
            Curve::Binary(c) => &c.order,
        }
    }

    pub fn published_target(&self) -> ChallengePoint {
        self.published.clone()
    }

    pub fn target_from_scalar(&self, scalar: &BigUint) -> ChallengePoint {
        self.mul(&self.generator(), &(scalar % self.order()))
    }

    pub fn generator(&self) -> ChallengePoint {
        match &self.curve {
            Curve::Prime(c) => ChallengePoint::Prime(c.generator()),
            Curve::Binary(c) => ChallengePoint::Binary(c.generator.clone()),
        }
    }

    fn identity(&self) -> ChallengePoint {
        match self.curve {
            Curve::Prime(_) => ChallengePoint::Prime(Point::Infinity),
            Curve::Binary(_) => ChallengePoint::Binary(BinaryPoint::Infinity),
        }
    }

    fn add(&self, p: &ChallengePoint, q: &ChallengePoint) -> ChallengePoint {
        match (&self.curve, p, q) {
            (Curve::Prime(c), ChallengePoint::Prime(p), ChallengePoint::Prime(q)) => {
                ChallengePoint::Prime(p.add(q, &c.a_fe()))
            }
            (Curve::Binary(c), ChallengePoint::Binary(p), ChallengePoint::Binary(q)) => {
                ChallengePoint::Binary(binary::point_add(c, p, q))
            }
            _ => unreachable!("solver points have been validated against their field"),
        }
    }

    fn neg(&self, p: &ChallengePoint) -> ChallengePoint {
        match p {
            ChallengePoint::Prime(p) => ChallengePoint::Prime(p.neg()),
            ChallengePoint::Binary(p) => ChallengePoint::Binary(binary::point_neg(p)),
        }
    }

    fn mul(&self, p: &ChallengePoint, k: &BigUint) -> ChallengePoint {
        match (&self.curve, p) {
            (Curve::Prime(c), ChallengePoint::Prime(p)) => {
                ChallengePoint::Prime(p.scalar_mul(k, &c.a_fe()))
            }
            (Curve::Binary(c), ChallengePoint::Binary(p)) => {
                ChallengePoint::Binary(binary::scalar_mul(c, p, k))
            }
            _ => unreachable!("solver points have been validated against their field"),
        }
    }

    pub fn coordinates(&self, point: &ChallengePoint) -> Option<(BigUint, BigUint)> {
        match point {
            ChallengePoint::Prime(Point::Affine { x, y }) => {
                Some((x.value.clone(), y.value.clone()))
            }
            ChallengePoint::Binary(BinaryPoint::Affine { x, y }) => {
                Some((x.to_biguint(), y.to_biguint()))
            }
            _ => None,
        }
    }

    // The complete coordinates are the lookup key, including their lengths.
    // Neither BSGS nor point decomposition relies on a truncated fingerprint.
    fn key(&self, point: &ChallengePoint) -> Option<(BigUint, BigUint)> {
        self.coordinates(point)
    }

    pub fn point(&self, x: &BigUint, y: &BigUint) -> Result<ChallengePoint, String> {
        let point = self.point_on_curve(x, y)?;
        self.validate(&point)?;
        Ok(point)
    }

    // Device proposals must be canonical and on-curve. Final answers and IC
    // relations receive independent CPU scalar replay; table points need not
    // each incur an additional full subgroup scalar multiplication.
    fn point_on_curve(&self, x: &BigUint, y: &BigUint) -> Result<ChallengePoint, String> {
        let point = match &self.curve {
            Curve::Prime(c) if x < &c.p && y < &c.p => ChallengePoint::Prime(Point::Affine {
                x: c.fe(x.clone()),
                y: c.fe(y.clone()),
            }),
            Curve::Binary(c) if x.bits() <= c.m as u64 && y.bits() <= c.m as u64 => {
                ChallengePoint::Binary(BinaryPoint::Affine {
                    x: F2mElement::from_biguint(x, c.m),
                    y: F2mElement::from_biguint(y, c.m),
                })
            }
            _ => return Err("point coordinates are outside the exact challenge field".into()),
        };
        if !self.on_curve(&point) {
            return Err("point is not on the selected exact curve".into());
        }
        Ok(point)
    }

    fn on_curve(&self, point: &ChallengePoint) -> bool {
        match (&self.curve, point) {
            (Curve::Prime(c), ChallengePoint::Prime(p @ Point::Affine { x, y })) => {
                x.modulus == c.p
                    && y.modulus == c.p
                    && x.value < c.p
                    && y.value < c.p
                    && c.is_on_curve(p)
            }
            (Curve::Binary(c), ChallengePoint::Binary(p @ BinaryPoint::Affine { x, y })) => {
                x.m_value() == c.m && y.m_value() == c.m && c.is_on_curve(p)
            }
            (Curve::Prime(_), ChallengePoint::Prime(Point::Infinity))
            | (Curve::Binary(_), ChallengePoint::Binary(BinaryPoint::Infinity)) => true,
            _ => false,
        }
    }

    pub fn validate(&self, point: &ChallengePoint) -> Result<(), String> {
        if !self.on_curve(point) {
            return Err("point is not on the selected challenge curve".into());
        }
        if self.mul(point, self.order()) != self.identity() {
            return Err("point is outside the declared prime-order subgroup".into());
        }
        Ok(())
    }

    pub fn parameters(&self) -> Value {
        let (kind, bits, field, a, b, cofactor) = match &self.curve {
            Curve::Prime(c) => (
                "prime",
                c.p.bits(),
                json!({"p": c.p.to_string()}),
                c.a.to_string(),
                c.b.to_string(),
                BigUint::from(c.h),
            ),
            Curve::Binary(c) => (
                "binary",
                c.m as u64,
                json!({"degree": c.m, "polynomial_low_terms": c.irreducible.low_terms}),
                c.a.to_biguint().to_string(),
                c.b.to_biguint().to_string(),
                c.cofactor.clone(),
            ),
        };
        json!({"name": self.name, "field_type": kind, "field_bits": bits, "field": field, "a": a, "b": b, "subgroup_order": self.order().to_string(), "cofactor": cofactor.to_string(), "generator": self.point_json(&self.generator())})
    }

    pub fn point_json(&self, point: &ChallengePoint) -> Value {
        match self.coordinates(point) {
            Some((x, y)) => json!({"x": format!("0x{x:x}"), "y": format!("0x{y:x}")}),
            None => json!({"infinity": true}),
        }
    }
}

/// Resource limits. Rho's iteration limit is per restart, as in the existing
/// generic rho engine. BSGS bounds giant steps; IC bounds relation and descent
/// queries separately. All three retain the same exact challenge subgroup.
#[derive(Clone, Debug)]
pub struct SolverOptions {
    pub max_iterations: u64,
    pub max_restarts: u32,
    pub max_table_entries: usize,
    pub max_matrix_entries: usize,
    pub factor_base_size: usize,
    pub max_base_candidates: u64,
    pub seed: u64,
}

impl Default for SolverOptions {
    fn default() -> Self {
        Self {
            max_iterations: 10_000,
            max_restarts: 8,
            max_table_entries: 65_536,
            max_matrix_entries: 1_048_576,
            factor_base_size: 16,
            max_base_candidates: 4096,
            seed: 1,
        }
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct SolveReport {
    pub method: &'static str,
    pub curve: &'static str,
    pub exact_curve: bool,
    pub status: &'static str,
    pub verified: bool,
    pub scalar: Option<String>,
    #[serde(skip)]
    pub scalar_value: Option<BigUint>,
    pub iterations: Option<u64>,
    pub table_entries: usize,
    pub index_calculus: Option<IndexReport>,
    pub reason: Option<String>,
    pub execution: ExecutionReport,
}

impl SolveReport {
    fn pending(group: &ChallengeGroup, method: &'static str) -> Self {
        Self {
            method,
            curve: group.name(),
            exact_curve: true,
            status: "budget_exhausted",
            verified: false,
            scalar: None,
            scalar_value: None,
            iterations: None,
            table_entries: 0,
            index_calculus: None,
            reason: None,
            execution: ExecutionReport::default(),
        }
    }

    fn recover(
        &mut self,
        group: &ChallengeGroup,
        target: &ChallengePoint,
        scalar: BigUint,
    ) -> Result<(), String> {
        if group.target_from_scalar(&scalar) != *target {
            return Err("solver candidate fails independent [k]G = Q verification".into());
        }
        self.scalar = Some(scalar.to_string());
        self.scalar_value = Some(scalar);
        self.verified = true;
        self.status = "complete";
        self.reason = None;
        Ok(())
    }
}

/// Execute the existing generic Floyd rho with arbitrary-precision tags and
/// exact prime/binary point operations. No interval or alternate solver is used.
pub fn rho(
    group: &ChallengeGroup,
    target: &ChallengePoint,
    opts: &SolverOptions,
) -> Result<SolveReport, String> {
    use crate::cryptanalysis::pollard_rho::{pollard_rho_dlp, RhoOptions};
    group.validate(target)?;
    let mut report = SolveReport::pending(group, "rho");
    if *target == group.identity() {
        report.recover(group, target, BigUint::zero())?;
        return Ok(report);
    }
    if opts.max_iterations == 0 {
        report.reason = Some("rho iteration budget is zero".into());
        return Ok(report);
    }
    let partition = |point: &ChallengePoint| {
        let mut h = std::collections::hash_map::DefaultHasher::new();
        group.key(point).hash(&mut h);
        (h.finish() % 3) as u8
    };
    match pollard_rho_dlp(
        &group.generator(),
        target,
        group.order(),
        |p, q| group.add(p, q),
        |p, q| p == q,
        partition,
        |p, k| group.mul(p, k),
        &RhoOptions {
            max_iterations: opts.max_iterations,
            max_restarts: opts.max_restarts,
            seed: Some(opts.seed),
        },
    ) {
        Ok(solution) => {
            report.iterations = Some(solution.iterations);
            report.recover(group, target, solution.x)?;
        }
        Err(reason) if reason.contains("max_iterations") || reason.contains("max_restarts") => {
            report.reason = Some(reason.to_string());
        }
        Err(reason) => return Err(format!("rho failed: {reason}")),
    }
    Ok(report)
}

/// Rectangular BSGS on an exact scalar interval. A capped baby table remains a
/// valid BSGS search; the giant-step budget can stop it before the interval ends.
pub fn bsgs(
    group: &ChallengeGroup,
    target: &ChallengePoint,
    lo: &BigUint,
    width: &BigUint,
    opts: &SolverOptions,
) -> Result<SolveReport, String> {
    group.validate(target)?;
    if width.is_zero() || lo >= group.order() || lo + width > *group.order() {
        return Err("BSGS requires a nonempty interval contained in [0,n)".into());
    }
    if opts.max_table_entries == 0 {
        return Err("BSGS needs at least one baby-table entry".into());
    }
    let mut report = SolveReport::pending(group, "bsgs");
    if opts.max_iterations == 0 {
        report.reason = Some("BSGS giant-step budget is zero".into());
        return Ok(report);
    }
    let root = width.sqrt();
    let root = if &root * &root < *width {
        root + BigUint::one()
    } else {
        root
    };
    let m = root
        .min(BigUint::from(opts.max_table_entries))
        .to_usize()
        .ok_or("baby-table size does not fit this host")?;
    let mut table = HashMap::new();
    table
        .try_reserve(m)
        .map_err(|e| format!("cannot allocate baby table: {e}"))?;
    let generator = group.generator();
    let mut baby = group.identity();
    for j in 0..m {
        table.insert(group.key(&baby), j);
        baby = group.add(&baby, &generator);
    }
    report.table_entries = table.len();
    let stride = BigUint::from(m);
    let giant_step = group.neg(&group.mul(&generator, &stride));
    let mut current = group.add(target, &group.neg(&group.mul(&generator, lo)));
    let mut offset = BigUint::zero();
    for giant in 0..opts.max_iterations {
        if offset >= *width {
            report.status = "interval_exhausted";
            report.reason = Some("target logarithm is outside the supplied interval".into());
            report.iterations = Some(giant);
            return Ok(report);
        }
        if let Some(j) = table.get(&group.key(&current)) {
            let candidate = &offset + BigUint::from(*j);
            if candidate < *width {
                report.iterations = Some(giant + 1);
                report.recover(group, target, lo + candidate)?;
                return Ok(report);
            }
        }
        current = group.add(&current, &giant_step);
        offset += &stride;
    }
    report.iterations = Some(opts.max_iterations);
    if offset >= *width {
        report.status = "interval_exhausted";
        report.reason = Some("target logarithm is outside the supplied interval".into());
    } else {
        report.reason = Some("BSGS giant-step budget exhausted".into());
    }
    Ok(report)
}
