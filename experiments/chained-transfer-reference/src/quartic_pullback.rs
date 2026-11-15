//! Direct rational elliptic pullback through exact quartic covers. Existing
//! polynomial arithmetic and the unchanged existing balanced reducer only.
use super::{long_point, scale_point, Class, MumfordDivisorP, SevenChain};
use crate::balanced::Balanced;
use crate::reference::FpPoly;
use isogeny_algos::curve::{self, Curve, Pt};
use isogeny_algos::field::{Field, Zp};
use isogeny_algos::poly;
use num_bigint::BigUint;
use num_traits::ToPrimitive;
use std::collections::{HashMap, HashSet};
#[path = "quartic_pullback_points.rs"]
mod existing_points;
pub(super) fn rational_points(f: &Zp, e: &Curve<u64>) -> Vec<Pt<u64>> {
    existing_points::points(f, e)
}

pub(super) struct Pullback {
    fp: Zp,
    source: Balanced,
    curve: Curve<u64>,
    n: Vec<u64>,
    q: Vec<u64>,
    m: Vec<u64>,
    infinity: Pt<u64>,
}
impl Pullback {
    pub(super) fn fixed(model: usize, component: usize) -> Self {
        let (equation, curve, n, q, m, infinity) = match (model, component) {
            (0, 0) => (
                [31, 75, 74, 54, 71, 55, 1],
                Curve::new(1, 46),
                vec![14, 0, 88, 97, 14],
                vec![63, 0, 1],
                vec![41, 40, 69, 73],
                Pt::Aff(14, 73),
            ),
            (0, 1) => (
                [31, 75, 74, 54, 71, 55, 1],
                Curve::new(44, 21),
                vec![5, 49, 31, 0, 87],
                vec![35, 0, 1],
                vec![87, 1, 82, 87],
                Pt::Aff(87, 87),
            ),
            (1, 0) => (
                [95, 26, 19, 27, 94, 91, 1],
                Curve::new(26, 58),
                vec![8, 60, 36, 0, 84],
                vec![47, 0, 1],
                vec![98, 45, 84, 37],
                Pt::Aff(84, 37),
            ),
            (1, 1) => (
                [95, 26, 19, 27, 94, 91, 1],
                Curve::new(69, 50),
                vec![3, 0, 76, 42, 46],
                vec![70, 0, 1],
                vec![4, 76, 75, 41],
                Pt::Aff(46, 41),
            ),
            _ => panic!("fixed models/components only"),
        };
        Self {
            fp: Zp::new(101),
            source: Balanced::new(101, &equation).unwrap(),
            curve,
            n,
            q,
            m,
            infinity,
        }
    }
    pub(super) fn pull(&self, point: &Pt<u64>) -> Result<(Class, (usize, i64)), String> {
        let f = &self.fp;
        if !curve::on_curve(f, &self.curve, point) {
            return Err("foreign/off-curve elliptic point".into());
        }
        let Pt::Aff(x, y) = *point else {
            return Ok((self.source.zero(), (0, 1)));
        };
        if y == 0 {
            return Err("fixed odd-order rational domain has no nonzero two-torsion".into());
        }
        let q2 = poly::mul(f, &self.q, &self.q);
        let u = poly::monic(f, &poly::sub(f, &self.n, &poly::scale(f, &q2, x)));
        let degree = usize::try_from(poly::deg(f, &u)).map_err(|_| "zero fibre support")?;
        if degree > 4 {
            return Err("quartic fibre exceeds degree4".into());
        }
        let inverse = poly::invmod(f, &self.m, &u)
            .ok_or("ordinate denominator is nonunit on non-two-torsion fibre")?;
        let q3 = poly::mul(f, &q2, &self.q);
        let v = poly::scale(f, &poly::mulmod(f, &q3, &inverse, &u), y);
        let plus = if degree == 4 {
            -1
        } else {
            let Pt::Aff(qx, qy) = self.infinity else {
                return Err("fixed finite infinity image required".into());
            };
            if x != qx {
                return Err("degree drop without the actual infinity image".into());
            }
            if y == qy {
                i64::try_from(4 - degree).unwrap() - 1
            } else if y == f.neg(qy) {
                -1
            } else {
                return Err("invalid infinity branch".into());
            }
        };
        let polynomial = |p: Vec<u64>| {
            FpPoly::from_coeffs(
                p.into_iter().map(BigUint::from).collect(),
                BigUint::from(101_u64),
            )
        };
        let output = self
            .source
            .reduce_support(polynomial(u), polynomial(v), plus)?;
        Ok((output, (degree, plus)))
    }
}

fn old_pull(c: &SevenChain, model: usize, component: usize, p: Pt<u64>) -> Class {
    let f = &c.t.fp;
    if model == 0 {
        let points = if component == 0 {
            [p, Pt::Inf]
        } else {
            [Pt::Inf, p]
        };
        let d =
            c.t.source
                .pulls(
                    &long_point(f, &c.t.source.first.base, points[0], 2),
                    &long_point(f, &c.t.source.second.base, points[1], 38),
                )
                .unwrap();
        c.r0.forward_closed(&d).unwrap()
    } else {
        let bases = [&c.t.target.first.base, &c.t.target.second.base];
        let points = if component == 0 {
            [p, Pt::Inf]
        } else {
            [Pt::Inf, p]
        };
        let components: [MumfordDivisorP; 2] = std::array::from_fn(|i| {
            let chart = c.t.model.charts[i];
            let internal = scale_point(f, points[chart.destination], f.inv(chart.scale));
            long_point(f, bases[i], internal, chart.shift)
        });
        let d = c.t.target.pulls(&components[0], &components[1]).unwrap();
        c.r1.forward_closed(&d).unwrap()
    }
}
fn key(d: &Class) -> (Vec<u64>, Vec<u64>, u8) {
    let (u, v, n) = d.components();
    let coefficients = |p: &FpPoly| p.coeffs.iter().map(|c| c.to_u64().unwrap()).collect();
    (coefficients(u), coefficients(v), n)
}

#[test]
fn all_four_direct_quartic_pullbacks_match_existing_r_p() {
    let c = SevenChain::new();
    for model in 0..2 {
        for component in 0..2 {
            let direct = Pullback::fixed(model, component);
            let points = existing_points::points(&direct.fp, &direct.curve);
            assert_eq!(points.len(), [109, 113][component]);
            let mut outputs = Vec::new();
            let mut shapes = HashMap::new();
            let mut distinct = HashSet::new();
            for &p in &points {
                let (image, shape) = direct.pull(&p).unwrap();
                assert_eq!(
                    image,
                    old_pull(&c, model, component, p),
                    "T{model}/component{component},point{p:?}"
                );
                assert!(distinct.insert(key(&image)));
                *shapes.entry(shape).or_insert(0_usize) += 1;
                let coords = if model == 0 {
                    c.t.source_coordinates(&c.r0.dual_closed(&image).unwrap())
                        .unwrap()
                } else {
                    c.t.target_coordinates(&c.r1.dual_closed(&image).unwrap())
                        .unwrap()
                };
                let mut expected = [Pt::Inf; 2];
                expected[component] = curve::pmul(&direct.fp, &direct.curve, &p, 4);
                assert_eq!(coords, expected, "global norm4/off-diagonal0 point control");
                outputs.push(image);
            }
            assert_eq!(distinct.len(), points.len());
            assert_eq!(shapes.get(&(0, 1)), Some(&1));
            let k = if (model, component) == (0, 1) || (model, component) == (1, 0) {
                2
            } else {
                1
            };
            assert_eq!(
                shapes.get(&(4 - k, i64::try_from(k).unwrap() - 1)),
                Some(&1)
            );
            assert_eq!(shapes.get(&(4 - k, -1)), Some(&1));
            let indices: HashMap<_, _> = points.iter().enumerate().map(|(i, p)| (*p, i)).collect();
            for (i, p) in points.iter().enumerate() {
                for (j, q) in points.iter().enumerate() {
                    let sum = curve::padd(&direct.fp, &direct.curve, p, q);
                    assert_eq!(
                        direct.source.add(&outputs[i], &outputs[j]).unwrap(),
                        outputs[indices[&sum]],
                        "pullback group T{model}/component{component},pair{i},{j}"
                    );
                }
            }
            assert!(direct.pull(&Pt::Aff(0, 0)).is_err());
            println!("PASS direct T{model}/component{component} quartic pullback all{} points/exact old RiPi/embedding/all{} ordered sums/norm4+offdiagonal0,raw fibre shapes{shapes:?};existing reduction body only,actual infinity multiplicity{k},no timing claim",points.len(),points.len()*points.len());
        }
    }
}
