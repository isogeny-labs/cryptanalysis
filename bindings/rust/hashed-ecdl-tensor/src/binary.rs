//! Native odd-degree binary Koblitz groups, invertible XOR hashes and certified
//! Frobenius orbit representatives. No subfield, coverage or speedup assumption.

use crate::arithmetic::{floor_root, inverse, is_prime, square_root, Seeded};
use crate::curve::Point;
use crate::finite::{Domain, Group};
use crate::primality::{verify_certificates, PrimeCertificate};
use crate::{integrity, invalid, overflow, BigUint, Meter, Result};
use num_integer::Integer;
use num_traits::{One, ToPrimitive, Zero};

/// An exactly checked polynomial-basis field GF(2^n).
#[derive(Clone, Debug)]
pub struct Field {
    degree: usize,
    modulus: BigUint,
}
impl Field {
    /// Check monicity, constant coefficient and Rabin's irreducibility criterion.
    pub fn new(degree: usize, modulus: BigUint, meter: &mut Meter) -> Result<Self> {
        meter.bits(
            degree
                .checked_add(1)
                .ok_or_else(|| overflow("binary degree"))?,
            "binary field width",
        )?;
        if degree < 2 || modulus.bits() != degree as u64 + 1 || !modulus.bit(0) {
            return Err(invalid("binary reduction polynomial"));
        }
        let field = Self { degree, modulus };
        let mut divisors = Vec::new();
        let mut left = degree;
        let mut q = 2usize;
        while q <= left / q {
            meter.charge(1, "binary degree factors")?;
            if left % q == 0 {
                divisors.push(q);
                while left % q == 0 {
                    left /= q;
                }
            }
            q += 1;
        }
        if left > 1 {
            divisors.push(left);
        }
        let x = BigUint::from(2u8);
        let mut power = x.clone();
        for i in 1..=degree {
            power = field.mul(&power, &power, meter)?;
            if divisors.iter().any(|&d| i == degree / d)
                && polynomial_gcd(&power ^ &x, field.modulus.clone(), meter)? != BigUint::one()
            {
                return Err(invalid("reducible binary polynomial"));
            }
        }
        if power != x {
            return Err(invalid("binary Frobenius irreducibility check"));
        }
        Ok(field)
    }
    /// Extension degree, not subgroup bit size.
    pub fn degree(&self) -> usize {
        self.degree
    }
    /// Pinned polynomial including its leading term.
    pub fn modulus(&self) -> &BigUint {
        &self.modulus
    }
    fn reduce(&self, mut value: BigUint, meter: &mut Meter) -> Result<BigUint> {
        while value.bits() > self.degree as u64 {
            meter.charge(1, "binary polynomial reduction")?;
            value ^= &self.modulus << (value.bits() as usize - self.degree - 1);
        }
        Ok(value)
    }
    fn check(&self, value: &BigUint) -> Result<()> {
        if value.bits() > self.degree as u64 {
            return Err(invalid("noncanonical binary element"));
        }
        Ok(())
    }
    /// Carryless multiplication with exact reduction; addition is XOR.
    pub fn mul(&self, a: &BigUint, b: &BigUint, meter: &mut Meter) -> Result<BigUint> {
        self.check(a)?;
        self.check(b)?;
        let mut out = BigUint::zero();
        let mut current = a.clone();
        for i in 0..b.bits() {
            meter.charge(1, "binary carryless multiply")?;
            if b.bit(i) {
                out ^= &current;
            }
            current <<= 1;
            if current.bit(self.degree as u64) {
                current ^= &self.modulus;
            }
        }
        Ok(out)
    }
    /// Polynomial extended-Euclidean inverse, rejecting zero.
    pub fn inverse(&self, a: &BigUint, meter: &mut Meter) -> Result<BigUint> {
        self.check(a)?;
        if a.is_zero() {
            return Err(invalid("binary inverse of zero"));
        }
        let (mut u, mut v) = (a.clone(), self.modulus.clone());
        let (mut x, mut y) = (BigUint::one(), BigUint::zero());
        while u != BigUint::one() {
            meter.charge(1, "binary Euclidean inverse")?;
            if u.is_zero() {
                return Err(integrity("binary field inverse gcd"));
            }
            if u.bits() < v.bits() {
                std::mem::swap(&mut u, &mut v);
                std::mem::swap(&mut x, &mut y);
            }
            let shift = (u.bits() - v.bits()) as usize;
            u ^= &v << shift;
            x ^= &y << shift;
            meter.bits(x.bits() as usize, "binary inverse coefficient")?;
        }
        self.reduce(x, meter)
    }
}
fn polynomial_gcd(mut a: BigUint, mut b: BigUint, meter: &mut Meter) -> Result<BigUint> {
    while !b.is_zero() {
        while !a.is_zero() && a.bits() >= b.bits() {
            meter.charge(1, "binary polynomial gcd")?;
            a ^= &b << (a.bits() - b.bits()) as usize;
        }
        std::mem::swap(&mut a, &mut b);
    }
    Ok(a)
}

/// Certified subgroup of y^2+xy=x^3+a*x^2+1, with a in GF(2), odd degree.
#[derive(Clone, Debug)]
pub struct Koblitz {
    field: Field,
    a: bool,
    order: BigUint,
    cofactor: BigUint,
    generator: Point,
}
impl Koblitz {
    /// Verify field, prime subgroup, generator, and full cardinality. Ambiguous
    /// Hasse intervals use exact bounded point counting, never an assumed order.
    pub fn new(
        field: Field,
        a: bool,
        order: BigUint,
        cofactor: BigUint,
        generator: Point,
        proofs: &[PrimeCertificate],
        meter: &mut Meter,
    ) -> Result<Self> {
        let certified = verify_certificates(proofs, meter)?;
        if field.degree % 2 == 0
            || order <= BigUint::from(2u8)
            || cofactor.is_zero()
            || (!certified.contains(&order) && !is_prime(&order, meter)?)
        {
            return Err(invalid("odd-degree Koblitz subgroup parameters"));
        }
        let curve = Self {
            field,
            a,
            order,
            cofactor,
            generator,
        };
        if curve.generator == Point::Infinity
            || !curve.contains(&curve.generator, meter)?
            || curve.mul(&curve.generator, &curve.order, meter)? != Point::Infinity
        {
            return Err(invalid("binary generator prime order"));
        }
        let q = BigUint::one() << curve.field.degree;
        let radius = floor_root(&(&q << 2), 2, meter)?;
        let center = &q + BigUint::one();
        let lower = &center - &radius;
        if lower.div_ceil(&curve.order) != curve.cofactor
            || (&center + &radius) / &curve.order != curve.cofactor
        {
            let mut size = BigUint::one();
            let mut code = BigUint::zero();
            while code < (&q << 1) {
                meter.charge(1, "ambiguous binary point count")?;
                if curve.decode(&code, meter)?.is_some() {
                    size += BigUint::one();
                }
                code += BigUint::one();
            }
            if size != &curve.order * &curve.cofactor {
                return Err(invalid("binary full cardinality"));
            }
        }
        Ok(curve)
    }
    /// Exactly checked binary field.
    pub fn field(&self) -> &Field {
        &self.field
    }
    /// Certified prime subgroup order.
    pub fn order(&self) -> &BigUint {
        &self.order
    }
    /// Certified full-group cofactor.
    pub fn cofactor(&self) -> &BigUint {
        &self.cofactor
    }
    /// Certified generator.
    pub fn generator(&self) -> &Point {
        &self.generator
    }
    /// Canonical curve membership.
    pub fn contains(&self, point: &Point, meter: &mut Meter) -> Result<bool> {
        let Point::Affine { x, y } = point else {
            return Ok(true);
        };
        if x.bits() > self.field.degree as u64 || y.bits() > self.field.degree as u64 {
            return Ok(false);
        }
        let xx = self.field.mul(x, x, meter)?;
        let rhs = self.field.mul(&xx, x, meter)?
            ^ if self.a { xx } else { BigUint::zero() }
            ^ BigUint::one();
        Ok(self.field.mul(y, y, meter)? ^ self.field.mul(x, y, meter)? == rhs)
    }
    /// Checked addition including identities, inverse pairs and x=0 doubling.
    pub fn add(&self, p: &Point, q: &Point, meter: &mut Meter) -> Result<Point> {
        if !self.contains(p, meter)? || !self.contains(q, meter)? {
            return Err(invalid("binary point"));
        }
        let (Point::Affine { x, y }, Point::Affine { x: xx, y: yy }) = (p, q) else {
            return Ok(if p == &Point::Infinity {
                q.clone()
            } else {
                p.clone()
            });
        };
        meter.charge(1, "binary point addition")?;
        if x == xx && (y != yy || x.is_zero()) {
            return Ok(Point::Infinity);
        }
        let a = BigUint::from(u8::from(self.a));
        let (nx, ny) = if x == xx {
            let slope = x ^ self.field.mul(y, &self.field.inverse(x, meter)?, meter)?;
            let nx = self.field.mul(&slope, &slope, meter)? ^ &slope ^ a;
            let ny = self.field.mul(x, x, meter)?
                ^ self.field.mul(&(&slope ^ BigUint::one()), &nx, meter)?;
            (nx, ny)
        } else {
            let slope = self
                .field
                .mul(&(y ^ yy), &self.field.inverse(&(x ^ xx), meter)?, meter)?;
            let nx = self.field.mul(&slope, &slope, meter)? ^ &slope ^ x ^ xx ^ a;
            let ny = self.field.mul(&slope, &(x ^ &nx), meter)? ^ &nx ^ y;
            (nx, ny)
        };
        let out = Point::Affine { x: nx, y: ny };
        if !self.contains(&out, meter)? {
            return Err(integrity("binary addition replay"));
        }
        Ok(out)
    }
    /// Checked negation (x,y) -> (x,x+y).
    pub fn negate(&self, point: &Point, meter: &mut Meter) -> Result<Point> {
        if !self.contains(point, meter)? {
            return Err(invalid("binary point"));
        }
        Ok(match point {
            Point::Infinity => Point::Infinity,
            Point::Affine { x, y } => Point::Affine {
                x: x.clone(),
                y: x ^ y,
            },
        })
    }
    /// Exact scalar multiplication without reducing the scalar first.
    pub fn mul(&self, point: &Point, scalar: &BigUint, meter: &mut Meter) -> Result<Point> {
        if !self.contains(point, meter)? {
            return Err(invalid("binary scalar point"));
        }
        meter.bits(scalar.bits() as usize, "binary scalar width")?;
        let mut out = Point::Infinity;
        let mut base = point.clone();
        for i in 0..scalar.bits() {
            if scalar.bit(i) {
                out = self.add(&out, &base, meter)?;
            }
            if i + 1 < scalar.bits() {
                base = self.add(&base, &base, meter)?;
            }
        }
        Ok(out)
    }
    /// Injective code 2*x + bit0(y/x); x=0 has the unique sign bit zero.
    pub fn encode(&self, point: &Point, meter: &mut Meter) -> Result<BigUint> {
        if !self.contains(point, meter)? {
            return Err(invalid("binary encoding point"));
        }
        let Point::Affine { x, y } = point else {
            return Err(invalid("binary identity encoding"));
        };
        let sign = if x.is_zero() {
            false
        } else {
            self.field
                .mul(y, &self.field.inverse(x, meter)?, meter)?
                .bit(0)
        };
        Ok((x << 1) + BigUint::from(u8::from(sign)))
    }
    /// Odd-degree half-trace decompression; invalid codes return None.
    pub fn decode(&self, code: &BigUint, meter: &mut Meter) -> Result<Option<Point>> {
        if code.bits() > self.field.degree as u64 + 1 {
            return Ok(None);
        }
        let x = code >> 1usize;
        if x.is_zero() {
            return Ok((!code.bit(0)).then(|| Point::Affine {
                x,
                y: BigUint::one(),
            }));
        }
        let inverse = self.field.inverse(&x, meter)?;
        let c = &x ^ BigUint::from(u8::from(self.a)) ^ self.field.mul(&inverse, &inverse, meter)?;
        let mut term = c.clone();
        let mut half = BigUint::zero();
        for _ in 0..=(self.field.degree - 1) / 2 {
            half ^= &term;
            let square = self.field.mul(&term, &term, meter)?;
            term = self.field.mul(&square, &square, meter)?;
        }
        if self.field.mul(&half, &half, meter)? ^ &half != c {
            return Ok(None);
        }
        if half.bit(0) != code.bit(0) {
            half ^= BigUint::one();
        }
        let y = self.field.mul(&x, &half, meter)?;
        Ok(Some(Point::Affine { x, y }))
    }
    /// Checked Frobenius automorphism; coefficients are in GF(2).
    pub fn frobenius(&self, point: &Point, meter: &mut Meter) -> Result<Point> {
        if !self.contains(point, meter)? {
            return Err(invalid("Frobenius point"));
        }
        Ok(match point {
            Point::Infinity => Point::Infinity,
            Point::Affine { x, y } => Point::Affine {
                x: self.field.mul(x, x, meter)?,
                y: self.field.mul(y, y, meter)?,
            },
        })
    }
}
impl Group for Koblitz {
    type Point = Point;
    fn identity(&self) -> Point {
        Point::Infinity
    }
    fn valid(&self, point: &Point, meter: &mut Meter) -> Result<bool> {
        Ok(self.contains(point, meter)? && self.mul(point, &self.order, meter)? == Point::Infinity)
    }
    fn add(&self, a: &Point, b: &Point, meter: &mut Meter) -> Result<Point> {
        self.add(a, b, meter)
    }
    fn negate(&self, a: &Point, meter: &mut Meter) -> Result<Point> {
        self.negate(a, meter)
    }
}

fn linear(rows: &[BigUint], value: &BigUint, meter: &mut Meter) -> Result<BigUint> {
    let mut out = BigUint::zero();
    for (i, row) in rows.iter().enumerate() {
        meter.charge(1, "XOR hash row")?;
        let mut parity = 0u32;
        for digit in (row & value).iter_u64_digits() {
            meter.charge(1, "XOR hash word")?;
            parity ^= digit.count_ones() & 1;
        }
        if parity != 0 {
            out.set_bit(i as u64, true);
        }
    }
    Ok(out)
}

/// Full-rank binary affine hash with explicitly invertible selector fibers.
#[derive(Clone, Debug)]
pub struct XorBase {
    rows: Vec<BigUint>,
    inverse: Vec<BigUint>,
    offset: BigUint,
    limit: BigUint,
}
impl XorBase {
    /// Check square full rank; arbitrary/conditioned hash distributions do not
    /// inherit the prime-affine manuscript's coverage theorem.
    pub fn new(
        rows: Vec<BigUint>,
        offset: BigUint,
        limit: BigUint,
        meter: &mut Meter,
    ) -> Result<Self> {
        let width = rows.len();
        meter.vector(
            width
                .checked_mul(width)
                .ok_or_else(|| overflow("XOR matrix"))?,
            "XOR matrix",
        )?;
        meter.bits(
            width.checked_add(1).ok_or_else(|| overflow("XOR width"))?,
            "XOR hash width",
        )?;
        if width == 0
            || offset.bits() > width as u64
            || rows.iter().any(|r| r.bits() > width as u64)
            || limit.is_zero()
            || limit > (BigUint::one() << width)
        {
            return Err(invalid("XOR hash dimensions"));
        }
        let mut left = rows.clone();
        let mut inverse: Vec<_> = (0..width).map(|i| BigUint::one() << i).collect();
        for col in 0..width {
            let pivot = (col..width)
                .find(|&i| left[i].bit(col as u64))
                .ok_or_else(|| invalid("singular XOR hash"))?;
            left.swap(col, pivot);
            inverse.swap(col, pivot);
            for row in 0..width {
                meter.charge(1, "XOR hash elimination")?;
                if row != col && left[row].bit(col as u64) {
                    let a = left[col].clone();
                    let b = inverse[col].clone();
                    left[row] ^= a;
                    inverse[row] ^= b;
                }
            }
        }
        Ok(Self {
            rows,
            inverse,
            offset,
            limit,
        })
    }
    /// Apply the affine binary hash to a canonical-width code.
    pub fn hash(&self, code: &BigUint, meter: &mut Meter) -> Result<BigUint> {
        if code.bits() > self.rows.len() as u64 {
            return Err(invalid("XOR hash code width"));
        }
        Ok(linear(&self.rows, code, meter)? ^ &self.offset)
    }
    /// Invert one selector exactly.
    pub fn code(&self, selector: &BigUint, meter: &mut Meter) -> Result<BigUint> {
        if selector >= &self.limit {
            return Err(invalid("XOR selector range"));
        }
        linear(&self.inverse, &(selector ^ &self.offset), meter)
    }
}
impl Domain<Koblitz> for XorBase {
    fn validate(&self, group: &Koblitz, _: &mut Meter) -> Result<()> {
        if self.rows.len() != group.field.degree + 1 {
            return Err(invalid("XOR base field width"));
        }
        Ok(())
    }
    fn limit(&self) -> &BigUint {
        &self.limit
    }
    fn decode(
        &self,
        group: &Koblitz,
        selector: &BigUint,
        meter: &mut Meter,
    ) -> Result<Option<Point>> {
        let point = group.decode(&self.code(selector, meter)?, meter)?;
        match point {
            Some(p) if group.valid(&p, meter)? => Ok(Some(p)),
            _ => Ok(None),
        }
    }
    fn contains(&self, group: &Koblitz, point: &Point, meter: &mut Meter) -> Result<bool> {
        if point == &Point::Infinity || !group.valid(point, meter)? {
            return Ok(false);
        }
        Ok(self.hash(&group.encode(point, meter)?, meter)? < self.limit)
    }
}

/// A checked Frobenius eigenvalue and optional negation folding.
#[derive(Clone, Debug)]
pub struct OrbitPolicy {
    eigenvalue: BigUint,
    negation: bool,
}
/// Orbit representative with the exact coefficient rep = [coefficient]point.
#[derive(Clone, Debug)]
pub struct OrbitRepresentative {
    /// Canonical representative.
    pub point: Point,
    /// Nonzero coefficient modulo the certified subgroup order.
    pub coefficient: BigUint,
}
impl OrbitPolicy {
    /// Derive eigenvalue candidates from the Koblitz characteristic polynomial,
    /// then verify the chosen candidate on the generator. No subgroup DLP search.
    pub fn derive(group: &Koblitz, negation: bool, meter: &mut Meter) -> Result<Self> {
        let r = group.order();
        let mu = if group.a {
            BigUint::one()
        } else {
            r - BigUint::one()
        };
        let discriminant = (&mu * &mu % r + r - BigUint::from(8u8) % r) % r;
        let Some(root) = square_root(&discriminant, r, &mut Seeded(0x46726f62656e6975), meter)?
        else {
            return Err(invalid("Frobenius eigenvalue discriminant"));
        };
        let half = inverse(&BigUint::from(2u8), r)?;
        let image = group.frobenius(group.generator(), meter)?;
        for root in [root.clone(), (r - root) % r] {
            let candidate = (&mu + root) * &half % r;
            if !candidate.is_zero() && group.mul(group.generator(), &candidate, meter)? == image {
                return Self::new(group, candidate, negation, meter);
            }
        }
        Err(invalid("no verified Frobenius eigenvalue candidate"))
    }
    /// Verify the eigenvalue on the prime-order generator.
    pub fn new(
        group: &Koblitz,
        eigenvalue: BigUint,
        negation: bool,
        meter: &mut Meter,
    ) -> Result<Self> {
        if eigenvalue.is_zero()
            || eigenvalue >= group.order
            || group.mul(group.generator(), &eigenvalue, meter)?
                != group.frobenius(group.generator(), meter)?
        {
            return Err(invalid("Frobenius eigenvalue certificate"));
        }
        Ok(Self {
            eigenvalue,
            negation,
        })
    }
    /// Canonicalize an orbit and independently replay the retained coefficient.
    pub fn representative(
        &self,
        group: &Koblitz,
        point: &Point,
        meter: &mut Meter,
    ) -> Result<OrbitRepresentative> {
        if !group.valid(point, meter)? {
            return Err(invalid("orbit subgroup point"));
        }
        let mut best = OrbitRepresentative {
            point: point.clone(),
            coefficient: BigUint::one(),
        };
        let mut current = point.clone();
        let mut coefficient = BigUint::one();
        for _ in 0..group.field.degree {
            meter.charge(1, "Frobenius orbit representative")?;
            if current < best.point {
                best = OrbitRepresentative {
                    point: current.clone(),
                    coefficient: coefficient.clone(),
                };
            }
            if self.negation {
                let negative = group.negate(&current, meter)?;
                if negative < best.point {
                    best = OrbitRepresentative {
                        point: negative,
                        coefficient: (&group.order - &coefficient) % &group.order,
                    };
                }
            }
            current = group.frobenius(&current, meter)?;
            coefficient = coefficient * &self.eigenvalue % &group.order;
        }
        if group.mul(point, &best.coefficient, meter)? != best.point {
            return Err(integrity("orbit coefficient replay"));
        }
        Ok(best)
    }
}

/// Orbit-invariant hash base. Enumeration expands every selected representative
/// orbit, so membership and decoder domains agree, including shorter orbits.
#[derive(Clone, Debug)]
pub struct OrbitBase {
    base: XorBase,
    policy: OrbitPolicy,
    limit: BigUint,
    span: usize,
}
impl OrbitBase {
    /// Prepare an explicitly changed base distribution; no coverage claim.
    pub fn new(
        group: &Koblitz,
        base: XorBase,
        policy: OrbitPolicy,
        meter: &mut Meter,
    ) -> Result<Self> {
        base.validate(group, meter)?;
        OrbitPolicy::new(group, policy.eigenvalue.clone(), policy.negation, meter)?;
        let span = group
            .field
            .degree
            .checked_mul(if policy.negation { 2 } else { 1 })
            .ok_or_else(|| overflow("orbit span"))?;
        let limit = &base.limit * BigUint::from(span);
        Ok(Self {
            base,
            policy,
            limit,
            span,
        })
    }
}
impl Domain<Koblitz> for OrbitBase {
    fn validate(&self, group: &Koblitz, meter: &mut Meter) -> Result<()> {
        self.base.validate(group, meter)?;
        OrbitPolicy::new(
            group,
            self.policy.eigenvalue.clone(),
            self.policy.negation,
            meter,
        )?;
        if self.span != group.field.degree * if self.policy.negation { 2 } else { 1 } {
            return Err(invalid("orbit field mismatch"));
        }
        Ok(())
    }
    fn limit(&self) -> &BigUint {
        &self.limit
    }
    fn decode(
        &self,
        group: &Koblitz,
        selector: &BigUint,
        meter: &mut Meter,
    ) -> Result<Option<Point>> {
        if selector >= &self.limit {
            return Err(invalid("orbit selector range"));
        }
        let (t, index) = selector.div_rem(&BigUint::from(self.span));
        let Some(point) = self.base.decode(group, &t, meter)? else {
            return Ok(None);
        };
        if self.policy.representative(group, &point, meter)?.point != point {
            return Ok(None);
        }
        let index = index.to_usize().ok_or_else(|| overflow("orbit index"))?;
        let mut out = point;
        for _ in 0..index % group.field.degree {
            out = group.frobenius(&out, meter)?;
        }
        if index >= group.field.degree {
            out = group.negate(&out, meter)?;
        }
        Ok(Some(out))
    }
    fn contains(&self, group: &Koblitz, point: &Point, meter: &mut Meter) -> Result<bool> {
        if point == &Point::Infinity || !group.valid(point, meter)? {
            return Ok(false);
        }
        let rep = self.policy.representative(group, point, meter)?;
        self.base.contains(group, &rep.point, meter)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::finite::{self, Options, Statistics};
    use crate::{Error, Limits};
    use std::collections::BTreeSet;

    fn tiny(meter: &mut Meter) -> Koblitz {
        tiny_with_a(false, meter)
    }
    fn tiny_with_a(a: bool, meter: &mut Meter) -> Koblitz {
        let field = Field::new(5, 37u8.into(), meter).unwrap();
        let mut draft = Koblitz {
            field,
            a,
            order: 11u8.into(),
            cofactor: if a { 2u8.into() } else { 4u8.into() },
            generator: Point::Infinity,
        };
        for x in 0..32u8 {
            for y in 0..32u8 {
                let point = Point::Affine {
                    x: x.into(),
                    y: y.into(),
                };
                if !draft.contains(&point, meter).unwrap() {
                    continue;
                }
                let point = draft.mul(&point, &draft.cofactor, meter).unwrap();
                if point != Point::Infinity
                    && draft.mul(&point, &11u8.into(), meter).unwrap() == Point::Infinity
                {
                    draft.generator = point;
                    return Koblitz::new(
                        draft.field,
                        a,
                        draft.order,
                        draft.cofactor,
                        draft.generator,
                        &[],
                        meter,
                    )
                    .unwrap();
                }
            }
        }
        panic!("missing known tiny subgroup");
    }
    fn xor(limit: u8, offset: u8, meter: &mut Meter) -> XorBase {
        let rows = (0..6)
            .map(|i| {
                (BigUint::one() << i)
                    ^ if i < 5 {
                        BigUint::one() << (i + 1)
                    } else {
                        BigUint::zero()
                    }
            })
            .collect();
        XorBase::new(rows, offset.into(), limit.into(), meter).unwrap()
    }
    #[test]
    fn both_koblitz_coefficients_and_derived_eigenvalues_have_pinned_fixture_identities() {
        let mut meter = Meter::new(Limits::default());
        for a in [false, true] {
            let curve = tiny_with_a(a, &mut meter);
            let policy = OrbitPolicy::derive(&curve, true, &mut meter).unwrap();
            let count = (0..64u8)
                .filter(|code| curve.decode(&(*code).into(), &mut meter).unwrap().is_some())
                .count();
            assert_eq!(count, if a { 21 } else { 43 });
            eprintln!(
                "binary fixture n=5 f=37 a={} r=11 h={} G={:?} lambda={}",
                u8::from(a),
                curve.cofactor(),
                curve.generator(),
                policy.eigenvalue
            );
            for k in 0..11u8 {
                let point = curve.mul(curve.generator(), &k.into(), &mut meter).unwrap();
                assert_eq!(
                    curve.frobenius(&point, &mut meter).unwrap(),
                    curve.mul(&point, &policy.eigenvalue, &mut meter).unwrap()
                );
            }
        }
    }
    #[test]
    fn binary_fields_check_irreducibility_inverse_and_official_131_polynomial() {
        let mut meter = Meter::new(Limits::default());
        assert!(Field::new(5, 33u8.into(), &mut meter).is_err());
        let field = Field::new(5, 37u8.into(), &mut meter).unwrap();
        for a in 0..32u16 {
            for b in 0..32u16 {
                let mut product = 0u16;
                for bit in 0..5 {
                    if b & (1 << bit) != 0 {
                        product ^= a << bit;
                    }
                }
                for bit in (5..10).rev() {
                    if product & (1 << bit) != 0 {
                        product ^= 37u16 << (bit - 5);
                    }
                }
                assert_eq!(
                    field
                        .mul(&BigUint::from(a), &BigUint::from(b), &mut meter)
                        .unwrap(),
                    BigUint::from(product)
                );
            }
        }
        for a in 1..32u8 {
            let inverse = field.inverse(&a.into(), &mut meter).unwrap();
            assert_eq!(
                field.mul(&a.into(), &inverse, &mut meter).unwrap(),
                BigUint::one()
            );
            let mut power = BigUint::from(a);
            for _ in 0..5 {
                power = field.mul(&power, &power, &mut meter).unwrap();
            }
            assert_eq!(power, BigUint::from(a));
        }
        assert!(field.inverse(&0u8.into(), &mut meter).is_err());
        assert!(field.mul(&32u8.into(), &1u8.into(), &mut meter).is_err());
        let polynomial =
            (BigUint::one() << 131usize) ^ (BigUint::one() << 13usize) ^ BigUint::from(7u8);
        let field = Field::new(131, polynomial, &mut meter).unwrap();
        assert_eq!(field.degree(), 131);
    }
    #[test]
    fn binary_group_roundtrip_full_cardinality_associativity_and_frobenius() {
        let mut meter = Meter::new(Limits::default());
        let curve = tiny(&mut meter);
        let mut points = BTreeSet::new();
        for code in 0..64u8 {
            if let Some(point) = curve.decode(&code.into(), &mut meter).unwrap() {
                assert!(curve.contains(&point, &mut meter).unwrap());
                assert_eq!(
                    curve.encode(&point, &mut meter).unwrap(),
                    BigUint::from(code)
                );
                points.insert(point);
            }
        }
        assert_eq!(points.len(), 43);
        assert!(curve.decode(&1u8.into(), &mut meter).unwrap().is_none());
        assert!(curve.decode(&64u8.into(), &mut meter).unwrap().is_none());
        assert!(curve.encode(&Point::Infinity, &mut meter).is_err());
        let subgroup: Vec<_> = (0..11u8)
            .map(|k| curve.mul(curve.generator(), &k.into(), &mut meter).unwrap())
            .collect();
        for p in &subgroup {
            for q in &subgroup {
                let sum = curve.add(p, q, &mut meter).unwrap();
                assert_eq!(
                    curve.frobenius(&sum, &mut meter).unwrap(),
                    curve
                        .add(
                            &curve.frobenius(p, &mut meter).unwrap(),
                            &curve.frobenius(q, &mut meter).unwrap(),
                            &mut meter
                        )
                        .unwrap()
                );
                for r in &subgroup {
                    assert_eq!(
                        curve.add(&sum, r, &mut meter).unwrap(),
                        curve
                            .add(p, &curve.add(q, r, &mut meter).unwrap(), &mut meter)
                            .unwrap()
                    );
                }
            }
        }
        let bad = Point::Affine {
            x: 32u8.into(),
            y: 0u8.into(),
        };
        assert!(!curve.contains(&bad, &mut meter).unwrap());
        assert!(curve.add(&bad, &Point::Infinity, &mut meter).is_err());
    }
    #[test]
    fn xor_hash_inverse_and_binary_selector_search_match_exhaustive_domains() {
        let mut meter = Meter::new(Limits::default());
        let curve = tiny(&mut meter);
        let base = xor(64, 7, &mut meter);
        for code in 0..64u8 {
            let selector = base.hash(&code.into(), &mut meter).unwrap();
            assert_eq!(
                base.code(&selector, &mut meter).unwrap(),
                BigUint::from(code)
            );
        }
        assert!(XorBase::new(
            vec![1u8.into(), 1u8.into()],
            0u8.into(),
            4u8.into(),
            &mut meter
        )
        .is_err());
        for limit in [1, 16, 64] {
            let bases = vec![xor(limit, 3, &mut meter), xor(limit, 9, &mut meter)];
            let members: Vec<Vec<Point>> = bases
                .iter()
                .map(|b| {
                    (0..limit)
                        .filter_map(|t| b.decode(&curve, &t.into(), &mut meter).unwrap())
                        .collect()
                })
                .collect();
            for k in 0..11u8 {
                let target = curve.mul(curve.generator(), &k.into(), &mut meter).unwrap();
                let expected = members[0].iter().any(|a| {
                    members[1]
                        .iter()
                        .any(|b| curve.add(a, b, &mut meter).unwrap() == target)
                });
                assert_eq!(
                    finite::decompose(
                        &curve,
                        &bases,
                        &target,
                        &Options::default(),
                        &mut Statistics::default(),
                        &mut meter
                    )
                    .unwrap()
                    .is_some(),
                    expected
                );
            }
        }
    }
    #[test]
    fn orbit_coefficients_and_orbit_hash_enumeration_are_complete() {
        let mut meter = Meter::new(Limits {
            steps: 500_000_000,
            ..Limits::default()
        });
        let curve = tiny(&mut meter);
        let image = curve.frobenius(curve.generator(), &mut meter).unwrap();
        let eigenvalue = (1..11u8)
            .find(|k| {
                curve
                    .mul(curve.generator(), &(*k).into(), &mut meter)
                    .unwrap()
                    == image
            })
            .unwrap();
        assert!(OrbitPolicy::new(&curve, 0u8.into(), true, &mut meter).is_err());
        let policy = OrbitPolicy::new(&curve, eigenvalue.into(), true, &mut meter).unwrap();
        assert_eq!(
            OrbitPolicy::derive(&curve, true, &mut meter)
                .unwrap()
                .eigenvalue,
            policy.eigenvalue
        );
        let base =
            OrbitBase::new(&curve, xor(32, 4, &mut meter), policy.clone(), &mut meter).unwrap();
        let mut enumerated = BTreeSet::new();
        for t in 0..base.limit.to_usize().unwrap() {
            if let Some(point) = base.decode(&curve, &t.into(), &mut meter).unwrap() {
                enumerated.insert(point);
            }
        }
        for k in 1..11u8 {
            let point = curve.mul(curve.generator(), &k.into(), &mut meter).unwrap();
            let rep = policy.representative(&curve, &point, &mut meter).unwrap();
            assert_eq!(
                curve.mul(&point, &rep.coefficient, &mut meter).unwrap(),
                rep.point
            );
            assert_eq!(
                base.contains(&curve, &point, &mut meter).unwrap(),
                enumerated.contains(&point)
            );
            let next = curve.frobenius(&point, &mut meter).unwrap();
            assert_eq!(
                policy
                    .representative(&curve, &next, &mut meter)
                    .unwrap()
                    .point,
                rep.point
            );
        }
        let target = curve.generator().clone();
        let domains = vec![base.clone(), base];
        let expected = enumerated.iter().any(|a| {
            enumerated
                .iter()
                .any(|b| curve.add(a, b, &mut meter).unwrap() == target)
        });
        assert_eq!(
            finite::decompose(
                &curve,
                &domains,
                &target,
                &Options::default(),
                &mut Statistics::default(),
                &mut meter
            )
            .unwrap()
            .is_some(),
            expected
        );
        meter.limits.steps = meter.used;
        assert!(matches!(
            curve.mul(curve.generator(), &3u8.into(), &mut meter),
            Err(Error::Limit(_))
        ));
    }
}
