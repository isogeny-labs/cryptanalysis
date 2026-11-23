use crate::field::{Encoding, F, ONE, ZERO};
use crate::packet::Reader;
use crate::{need, AResult};

pub type Point = Option<(F, F)>;

pub fn valid(point: Point) -> bool {
    point.is_none_or(|(x, y)| y.pow(2) == x.pow(3).plus(x.scale(2)).plus(F::prime(6)))
}
pub fn neg(point: Point) -> Point {
    point.map(|(x, y)| (x, y.neg()))
}
pub fn frob(point: Point) -> Point {
    point.map(|(x, y)| (x.pow(7), y.pow(7)))
}

// Jacobian-coordinate chord formulas; the producer used affine slope addition.
pub fn add(p: Point, q: Point) -> Point {
    let (Some((x, y)), Some((u, v))) = (p, q) else {
        return p.or(q);
    };
    if x == u && y.plus(v) == ZERO {
        return None;
    }
    let (xx, yy, zz) = if x == u {
        assert_eq!(y, v);
        let z = y.scale(2);
        let m = x.pow(2).scale(3).plus(F::prime(2));
        let s = x.times(z.pow(2));
        let xx = m.pow(2).minus(s.scale(2));
        let yy = m.times(s.minus(xx)).minus(y.times(z.pow(3)));
        (xx, yy, z)
    } else {
        let z = u.minus(x);
        let r = v.minus(y);
        let s = x.times(z.pow(2));
        let xx = r.pow(2).minus(z.pow(3)).minus(s.scale(2));
        let yy = r.times(s.minus(xx)).minus(y.times(z.pow(3)));
        (xx, yy, z)
    };
    let inverse = zz.inverse();
    let result = Some((xx.times(inverse.pow(2)), yy.times(inverse.pow(3))));
    assert!(valid(result), "new-model Jacobian addition on actual E7");
    result
}
pub fn times(mut p: Point, mut n: u32) -> Point {
    let mut result = None;
    while n != 0 {
        if n & 1 == 1 {
            result = add(result, p);
        }
        p = add(p, p);
        n >>= 1;
    }
    result
}

pub fn read_points(bytes: &[u8], count: usize, encoding: &Encoding) -> AResult<Vec<Point>> {
    let mut reader = Reader::new(bytes);
    let mut points = Vec::new();
    for _ in 0..count {
        let flag = reader.u8()?;
        let x = reader.u32()?;
        let y = reader.u32()?;
        need(flag <= 1, "point origin flag")?;
        let point = if flag == 1 {
            need(x == 0 && y == 0, "origin canonical coordinates")?;
            None
        } else {
            Some((encoding.decode(x)?, encoding.decode(y)?))
        };
        need(valid(point), "actual elliptic curve equation")?;
        need(!points.contains(&point), "duplicate actual point")?;
        points.push(point);
    }
    reader.end()?;
    need(points.first() == Some(&None), "group identity at index0")?;
    Ok(points)
}

pub struct Group {
    pub points: Vec<Point>,
    pub plus: Vec<Vec<usize>>,
    pub negative: Vec<usize>,
    pub frobenius: Vec<usize>,
    pub exponent: i64,
}
impl Group {
    pub fn new(points: Vec<Point>, exponent: i64) -> AResult<Self> {
        need(
            points.iter().all(|&p| times(p, exponent as u32).is_none()),
            "actual point exponent",
        )?;
        let index = |point| {
            points
                .iter()
                .position(|&p| p == point)
                .ok_or("actual group not closed")
        };
        let mut plus = Vec::new();
        for &p in &points {
            let mut row = Vec::new();
            for &q in &points {
                row.push(index(add(p, q))?);
            }
            plus.push(row);
        }
        let mut negative = Vec::new();
        let mut frobenius = Vec::new();
        for &p in &points {
            negative.push(index(neg(p))?);
            frobenius.push(index(frob(p))?);
        }
        let result = Self {
            points,
            plus,
            negative,
            frobenius,
            exponent,
        };
        for p in 0..result.points.len() {
            need(
                result.plus[p][result.negative[p]] == 0,
                "actual inverse table",
            )?;
            for q in 0..result.points.len() {
                need(
                    result.plus[p][q] == result.plus[q][p],
                    "actual group commutative",
                )?;
                need(
                    result.frobenius[result.plus[p][q]]
                        == result.plus[result.frobenius[p]][result.frobenius[q]],
                    "actual Frobenius homomorphism",
                )?;
                for r in 0..result.points.len() {
                    need(
                        result.plus[result.plus[p][q]][r] == result.plus[p][result.plus[q][r]],
                        "complete group associativity",
                    )?;
                }
            }
        }
        Ok(result)
    }
    pub fn index(&self, point: Point) -> AResult<usize> {
        self.points
            .iter()
            .position(|&p| p == point)
            .ok_or("point absent from full actual group")
    }
    pub fn scalar(&self, p: usize, n: i64) -> usize {
        (0..n.rem_euclid(self.exponent)).fold(0, |sum, _| self.plus[sum][p])
    }
    pub fn omega(&self, p: usize) -> usize {
        self.plus[self.frobenius[p]][self.scalar(p, 2)]
    }
    pub fn cm(&self, p: usize, coefficient: [i64; 2]) -> usize {
        self.plus[self.scalar(p, coefficient[0])][self.scalar(self.omega(p), coefficient[1])]
    }
    pub fn addition_records(&self, bytes: &[u8]) -> AResult<()> {
        need(
            bytes.len() == self.points.len().pow(2),
            "addition record length",
        )?;
        for (i, &value) in bytes.iter().enumerate() {
            need(
                usize::from(value) == self.plus[i / self.points.len()][i % self.points.len()],
                "actual addition record differs",
            )?;
        }
        Ok(())
    }
}

fn line_ratio(p: Point, q: Point, x: Point) -> Option<F> {
    let (Some((px, py)), Some((qx, qy))) = (p, q) else {
        return Some(ONE);
    };
    let (x, y) = x?;
    if px == qx && py.plus(qy) == ZERO {
        let vertical = x.minus(px);
        return (vertical != ZERO).then_some(vertical);
    }
    let (denominator_constant, slope_numerator) = if px == qx {
        (py.scale(2), px.pow(2).scale(3).plus(F::prime(2)))
    } else {
        (qx.minus(px), qy.minus(py))
    };
    let numerator = denominator_constant
        .times(y.minus(py))
        .minus(slope_numerator.times(x.minus(px)));
    let vertical = add(p, q).map_or(ONE, |(u, _)| x.minus(u));
    let denominator = denominator_constant.times(vertical);
    if numerator == ZERO || denominator == ZERO {
        None
    } else {
        Some(numerator.over(denominator))
    }
}

pub fn miller(p: Point, n: u32, x: Point) -> Option<F> {
    assert!(n > 0);
    let mut running = p;
    let mut value = ONE;
    for bit in (0..(u32::BITS - n.leading_zeros() - 1)).rev() {
        value = value.pow(2).times(line_ratio(running, running, x)?);
        running = add(running, running);
        if (n >> bit) & 1 == 1 {
            value = value.times(line_ratio(running, p, x)?);
            running = add(running, p);
        }
    }
    Some(value)
}
pub fn weil4(p: Point, q: Point, auxiliary: Point) -> Option<F> {
    let numerator = miller(p, 4, add(q, auxiliary))?.times(miller(q, 4, neg(auxiliary))?);
    let denominator = miller(p, 4, auxiliary)?.times(miller(q, 4, add(p, neg(auxiliary)))?);
    (denominator != ZERO).then(|| numerator.over(denominator))
}
