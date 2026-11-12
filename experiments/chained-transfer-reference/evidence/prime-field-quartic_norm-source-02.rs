//! Direct finite-algebra trace of the fixed exact quartic cover. Reuses the
//! existing field/poly/elliptic engines and existing Balanced validation.
use super::SevenChain;
use crate::balanced::{Balanced, Class};
use isogeny_algos::curve::{self, Curve, Pt};
use isogeny_algos::field::{Field, Zp};
use isogeny_algos::poly;
use num_traits::ToPrimitive;
type Result<T> = std::result::Result<T, String>;

pub(super) struct DirectQuartic {
    fp: Zp,
    source: Balanced,
    curve: Curve<u64>,
    n: Vec<u64>,
    q: Vec<u64>,
    m: Vec<u64>,
    infinity: Pt<u64>,
}

impl DirectQuartic {
    pub(super) fn first() -> Self {
        Self {
            fp: Zp::new(101),
            source: Balanced::new(101, &[31, 75, 74, 54, 71, 55, 1]).unwrap(),
            curve: Curve::new(1, 46),
            n: vec![14, 0, 88, 97, 14],
            q: vec![63, 0, 1],
            m: vec![41, 40, 69, 73],
            infinity: Pt::Aff(14, 73),
        }
    }

    pub(super) fn second() -> Self {
        Self {
            curve: Curve::new(44, 21),
            n: vec![5, 49, 31, 0, 87],
            q: vec![35, 0, 1],
            m: vec![87, 1, 82, 87],
            infinity: Pt::Aff(87, 87),
            ..Self::first()
        }
    }

    fn point(&self, x: u64, y: u64) -> Result<Pt<u64>> {
        let f = &self.fp;
        let q = poly::eval(f, &self.q, x);
        if q == 0 {
            return Ok(Pt::Inf);
        }
        let p = Pt::Aff(
            f.div(poly::eval(f, &self.n, x), f.sq(q)),
            f.div(f.mul(y, poly::eval(f, &self.m, x)), f.pow(q, 3)),
        );
        if !curve::on_curve(f, &self.curve, &p) {
            return Err("quartic finite image off target".into());
        }
        Ok(p)
    }

    fn finite(&self, u: &Vec<u64>, v: &Vec<u64>) -> Result<(Pt<u64>, usize)> {
        let f = &self.fp;
        match u.len() {
            1 => Ok((Pt::Inf, 0)),
            2 => Ok((self.point(f.neg(u[0]), poly::eval(f, v, f.neg(u[0])))?, 1)),
            3 => {
                // gcd includes all support multiplicities lying over the pole divisor.
                let pole = poly::gcd(f, u, &poly::mul(f, &self.q, &self.q));
                match poly::deg(f, &pole) {
                    2 => return Ok((Pt::Inf, 2)),
                    1 => {
                        let (remaining, rem) = poly::divrem(f, u, &pole);
                        if poly::deg(f, &rem) >= 0 || remaining.len() != 2 {
                            return Err("nonexact pole support division".into());
                        }
                        let x = f.neg(remaining[0]);
                        return Ok((self.point(x, poly::eval(f, v, x))?, 3));
                    }
                    0 => {}
                    _ => return Err("invalid pole gcd".into()),
                }
                let inverse =
                    poly::invmod(f, &self.q, u).ok_or("unit pole denominator missing inverse")?;
                let inverse2 = poly::mulmod(f, &inverse, &inverse, u);
                let inverse3 = poly::mulmod(f, &inverse2, &inverse, u);
                let r = poly::mulmod(f, &self.n, &inverse2, u);
                let w = poly::mulmod(f, v, &poly::mulmod(f, &self.m, &inverse3, u), u);
                let [r0, r1] = [
                    r.first().copied().unwrap_or(0),
                    r.get(1).copied().unwrap_or(0),
                ];
                let [w0, w1] = [
                    w.first().copied().unwrap_or(0),
                    w.get(1).copied().unwrap_or(0),
                ];
                if r1 == 0 {
                    if w1 == 0 {
                        let p = Pt::Aff(r0, w0);
                        if !curve::on_curve(f, &self.curve, &p) {
                            return Err("coincident quartic image off target".into());
                        }
                        return Ok((curve::padd(f, &self.curve, &p, &p), 4));
                    }
                    if f.mul(2, w0) != f.mul(u[1], w1) {
                        return Err("conjugate cancellation identity failed".into());
                    }
                    return Ok((Pt::Inf, 5));
                }
                let slope = f.div(w1, r1);
                let x = f.add(f.sub(f.sq(slope), f.mul(2, r0)), f.mul(u[1], r1));
                let y = f.sub(f.mul(slope, f.sub(r0, x)), w0);
                let p = Pt::Aff(x, y);
                if !curve::on_curve(f, &self.curve, &p) {
                    return Err("quadratic finite-algebra trace off target".into());
                }
                Ok((p, 6))
            }
            _ => Err("unsupported balanced support".into()),
        }
    }

    pub(super) fn norm(&self, d: &Class) -> Result<(Pt<u64>, usize)> {
        self.source.check(d)?;
        let (u, v, n) = d.components();
        let coefficients = |p: &crate::reference::FpPoly| {
            let mut out: Vec<_> = p.coeffs.iter().map(|c| c.to_u64().unwrap()).collect();
            if out.is_empty() {
                out.push(0);
            }
            out
        };
        let u = coefficients(u);
        let (finite, route) = self.finite(&u, &coefficients(v))?;
        let correction = 2 * i32::from(n) + i32::try_from(u.len() - 1).unwrap() - 2;
        let point = curve::pmul(
            &self.fp,
            &self.curve,
            &self.infinity,
            u128::from(correction.unsigned_abs()),
        );
        let point = if correction < 0 {
            curve::neg(&self.fp, &point)
        } else {
            point
        };
        Ok((curve::padd(&self.fp, &self.curve, &finite, &point), route))
    }
}

fn complete_t0_component(component: usize) {
    let c = SevenChain::new();
    let direct = if component == 0 {
        DirectQuartic::first()
    } else {
        DirectQuartic::second()
    };
    let all = c.r0.target.classes().unwrap();
    assert_eq!(all.len(), 12317);
    let mut counts = [0_usize; 7];
    let mut repeated = 0;
    let mut images = Vec::new();
    for (i, d) in all.iter().enumerate() {
        let (image, route) = direct.norm(d).unwrap();
        let expected =
            c.t.source_coordinates(&c.r0.dual_closed(d).unwrap())
                .unwrap()[component];
        assert_eq!(image, expected, "complete T0 class{i},route{route}");
        counts[route] += 1;
        let (u, _, _) = d.components();
        if u.degree() == Some(2) {
            let a = u.coeffs[1].to_u64().unwrap();
            let b = u.coeffs[0].to_u64().unwrap();
            if direct.fp.sq(a) == direct.fp.mul(4, b) {
                repeated += 1;
            }
        }
        images.push(image);
    }
    assert_eq!(counts[0], 3);
    assert_eq!(counts[1], 236);
    assert!(
        counts[2] > 0,
        "actual closed pole classes must be exercised"
    );
    assert!(
        counts[4] + counts[5] > 0,
        "coincident elliptic x must be exercised"
    );
    assert!(repeated > 0);
    for (i, d) in all.iter().enumerate() {
        let j = (37 * i + 7) % all.len();
        let sum = c.r0.target.add(d, &all[j]).unwrap();
        assert_eq!(
            direct.norm(&sum).unwrap().0,
            curve::padd(&direct.fp, &direct.curve, &images[i], &images[j]),
            "paired norm addition{i}"
        );
        assert_eq!(
            direct.norm(&c.r0.target.neg(d).unwrap()).unwrap().0,
            curve::neg(&direct.fp, &images[i])
        );
    }
    assert!(direct.norm(&c.r1.target.zero()).is_err());
    assert_eq!(direct.norm(&c.r0.target.zero()).unwrap().0, Pt::Inf);
    assert_eq!(
        direct.norm(&c.r0.target.delta()).unwrap().0,
        curve::pmul(&direct.fp, &direct.curve, &direct.infinity, 2)
    );
    println!("PASS T0/component{component} directquarticnorm ALL12317 original H=NiR0Hat outputs/all negations/paired sums;routes{counts:?},repeated{repeated},all three degree0/infinity classes,actual closed poles/coincident-X/foreign model;existing arithmetic only,no timing claim");
}

#[test]
fn complete_first_t0_e109_direct_quartic_norm() {
    complete_t0_component(0);
}

#[test]
fn complete_second_t0_e113_direct_quartic_norm() {
    complete_t0_component(1);
}
