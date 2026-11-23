use crate::ec::Group;
use crate::field::{Encoding, F, ONE, ZERO};
use crate::packet::Reader;
use crate::{need, AResult};

type Element = [F; 3];
type Projective = [Element; 3];
const ZERO_ELEMENT: Element = [ZERO; 3];
const ROTATION: [[i64; 3]; 3] = [[1, 5, 2], [0, 5, 0], [2, 1, 1]];
const INVERSE: [[i64; 3]; 3] = [[1, 5, 5], [0, 5, 0], [5, 6, 1]];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct Algebra {
    degree: usize,
    constant: F,
}
impl Algebra {
    fn scalar(self, c: F) -> Element {
        [c, ZERO, ZERO]
    }
    fn variable(self) -> Element {
        [ZERO, ONE, ZERO]
    }
    fn plus(self, a: Element, b: Element) -> Element {
        std::array::from_fn(|i| a[i].plus(b[i]))
    }
    fn neg(self, a: Element) -> Element {
        a.map(F::neg)
    }
    fn minus(self, a: Element, b: Element) -> Element {
        self.plus(a, self.neg(b))
    }
    fn scale(self, a: Element, c: F) -> Element {
        a.map(|x| x.times(c))
    }
    fn times(self, a: Element, b: Element) -> Element {
        let mut coefficients = [ZERO; 5];
        for (i, &x) in a.iter().take(self.degree).enumerate() {
            for (j, &y) in b.iter().take(self.degree).enumerate() {
                coefficients[i + j] = coefficients[i + j].plus(x.times(y));
            }
        }
        for k in (self.degree..5).rev() {
            let value = coefficients[k];
            coefficients[k - self.degree] =
                coefficients[k - self.degree].plus(value.times(self.constant));
            coefficients[k] = ZERO;
        }
        std::array::from_fn(|i| {
            if i < self.degree {
                coefficients[i]
            } else {
                ZERO
            }
        })
    }
    fn power(self, a: Element, n: usize) -> Element {
        (0..n).fold(self.scalar(ONE), |result, _| self.times(result, a))
    }
    fn linear(self, m: [[i64; 3]; 3], p: Projective) -> Projective {
        m.map(|row| {
            row.into_iter().zip(p).fold(ZERO_ELEMENT, |s, (c, a)| {
                self.plus(s, self.scale(a, F::prime(c)))
            })
        })
    }
    fn constant_unit(self, a: Element) -> bool {
        a[0] != ZERO && a[1..].iter().all(|&x| x == ZERO)
    }
}

fn read(
    reader: &mut Reader<'_>,
    expected_degree: usize,
    encoding: &Encoding,
) -> AResult<(Algebra, Projective)> {
    let degree = usize::from(reader.u8()?);
    need(degree == expected_degree, "fibre algebra degree")?;
    let constant = encoding.decode(reader.u32()?)?;
    let mut point = [[ZERO; 3]; 3];
    for coordinate in &mut point {
        for (j, value) in coordinate.iter_mut().enumerate() {
            *value = encoding.decode(reader.u32()?)?;
            need(j < degree || *value == ZERO, "fibre padded coefficient")?;
        }
    }
    Ok((Algebra { degree, constant }, point))
}

fn curve(r: Algebra, p: Projective) -> AResult<()> {
    let [x, y, z] = p;
    let mut quartic = ZERO_ELEMENT;
    for (exponents, coefficient) in [
        ([4, 0, 0], 1),
        ([1, 3, 0], 4),
        ([0, 4, 0], 2),
        ([2, 0, 2], 5),
        ([1, 1, 2], 6),
        ([0, 2, 2], 2),
        ([0, 0, 4], 1),
    ] {
        let term = p
            .into_iter()
            .zip(exponents)
            .fold(r.scalar(F::prime(coefficient)), |a, (v, n)| {
                r.times(a, r.power(v, n))
            });
        quartic = r.plus(quartic, term);
    }
    need(quartic == ZERO_ELEMENT, "whole fibre quartic equation")?;
    let g = r.plus(
        r.plus(
            r.plus(r.power(z, 2), r.scale(r.power(x, 2), F::prime(6))),
            r.scale(r.times(x, y), F::prime(3)),
        ),
        r.power(y, 2),
    );
    let rhs = r.times(
        y,
        r.plus(
            r.plus(
                r.power(x, 3),
                r.scale(r.times(x, r.power(y, 2)), F::prime(2)),
            ),
            r.scale(r.power(y, 3), F::prime(6)),
        ),
    );
    need(r.power(g, 2) == rhs, "whole fibre original curve equation")
}
fn deck(r: Algebra, p: Projective, target: (F, F)) -> AResult<()> {
    let [x, y, z] = p;
    need(r.constant_unit(y), "degree2 forward chart denominator")?;
    need(x == r.scale(y, target.0), "degree2 actual forward abscissa")?;
    let g = r.plus(
        r.plus(
            r.plus(r.power(z, 2), r.scale(r.power(x, 2), F::prime(6))),
            r.scale(r.times(x, y), F::prime(3)),
        ),
        r.power(y, 2),
    );
    need(
        g == r.scale(r.power(y, 2), target.1),
        "degree2 actual forward ordinate",
    )
}
fn cubic(r: Algebra, p: Projective, target: (F, F)) -> AResult<()> {
    let nx = r.scale(p[1], F::prime(3));
    need(r.constant_unit(nx), "degree3 normal coordinate chart")?;
    let scale = F::prime(4).over(nx[0]);
    let ny = r.scale(r.plus(r.minus(p[0], nx), p[2]), scale);
    let nz = r.scale(r.minus(r.minus(p[0], nx), p[2]), scale);
    let u = r.times(ny, nz);
    let w = r.plus(
        r.plus(
            r.plus(r.scale(r.power(ny, 3), F::prime(4)), r.scalar(ONE)),
            r.scale(u, F::prime(3)),
        ),
        r.scale(r.power(u, 2), F::prime(2)),
    );
    let delta = r.plus(
        r.plus(
            r.plus(w, r.scale(r.power(u, 2), F::prime(2))),
            r.scale(u, F::prime(6)),
        ),
        r.scalar(F::prime(3)),
    );
    need(
        r.plus(delta, r.scalar(ONE)) == r.scalar(target.0),
        "degree3 actual forward abscissa",
    )?;
    let ordinate = r.plus(
        r.times(
            r.plus(r.scale(u, F::prime(5)), r.scalar(F::prime(4))),
            delta,
        ),
        r.scalar(F::prime(4)),
    );
    need(
        ordinate == r.scalar(target.1),
        "degree3 actual forward ordinate",
    )
}

pub fn verify(bytes: &[u8], g: &Group, encoding: &Encoding) -> AResult<()> {
    let mut reader = Reader::new(bytes);
    for index in 1..16 {
        need(
            usize::from(reader.u8()?) == index,
            "fibre original point index",
        )?;
        need(
            usize::from(reader.u8()?) == g.frobenius[index],
            "fibre actual Frobenius target",
        )?;
        let (r0, p0) = read(&mut reader, 2, encoding)?;
        let (r1, p1) = read(&mut reader, 2, encoding)?;
        let (r3, p3) = read(&mut reader, 3, encoding)?;
        let (rj, pj) = read(&mut reader, 3, encoding)?;
        let (x, y) = g.points[index].ok_or("nonzero actual fibre target")?;
        let (fx, fy) = g.points[g.frobenius[index]].ok_or("nonzero actual Frobenius fibre")?;
        let constant = y.minus(x.pow(2).scale(6).plus(x.scale(3)).plus(ONE));
        need(
            r0.constant == constant && r1 == r0,
            "degree2 actual fibre modulus",
        )?;
        let expected = [r0.scalar(x), r0.scalar(ONE), r0.variable()];
        need(p0 == expected, "degree2 complete actual fibre coefficients")?;
        need(
            p1 == r0.linear(INVERSE, p0),
            "degree2 inverse R correspondence",
        )?;
        need(
            r0.linear(ROTATION, p1) == p0.map(|a| r0.scale(a, F::prime(4))),
            "projective RRinv scaling",
        )?;
        let delta = fx.minus(ONE);
        need(delta != ZERO, "degree3 inverse chart")?;
        let u = fy
            .minus(F::prime(4))
            .over(delta)
            .minus(F::prime(4))
            .scale(3);
        let w = delta
            .minus(u.pow(2).scale(2))
            .minus(u.scale(6))
            .minus(F::prime(3));
        let v = w
            .minus(ONE)
            .minus(u.scale(3))
            .minus(u.pow(2).scale(2))
            .scale(2);
        let (ny, nz) = if v == ZERO {
            need(
                u == ZERO && r3.constant == F::prime(3),
                "degree3 exceptional finite fibre chart",
            )?;
            (r3.scalar(ZERO), r3.variable())
        } else {
            need(r3.constant == v, "degree3 actual fibre modulus")?;
            (
                r3.variable(),
                r3.scale(r3.power(r3.variable(), 2), u.over(v)),
            )
        };
        need(
            p3 == [
                r3.plus(r3.plus(r3.scalar(ONE), ny), nz),
                r3.scalar(F::prime(5)),
                r3.minus(ny, nz),
            ],
            "degree3 complete actual fibre coefficients",
        )?;
        let t = rj.variable();
        need(rj.constant == ZERO, "origin nilpotent jet algebra")?;
        need(
            pj == [
                rj.minus(rj.plus(rj.scalar(ONE), t), rj.power(t, 2)),
                rj.scale(rj.power(t, 2), F::prime(2)),
                rj.minus(t, rj.scalar(ONE)),
            ],
            "complete origin jet coefficients",
        )?;
        for (r, p) in [(r0, p0), (r1, p1), (r3, p3), (rj, pj)] {
            curve(r, p)?;
        }
        deck(r0, p0, (x, y))?;
        deck(r1, r1.linear(ROTATION, p1), (x, y))?;
        cubic(r3, p3, (fx, fy))?;
        cubic(r3, r3.linear(ROTATION, p3), (fx, fy))?;
    }
    reader.end()?;
    println!("FIBRE_SCHEMES\tcomplete_points=15\tall4_records_curve_forward_R_origin_jet\tPASS");
    Ok(())
}
