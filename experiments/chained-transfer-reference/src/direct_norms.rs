//! Fixed C0/C1 and explicit C2 direct norms,including balanced infinities.
//! Existing validation/field/elliptic engines only. Generic norms remain the
//! unchanged reference until both complete class corpora qualify this adapter.
use super::{short_point, Class};
use crate::balanced::{Balanced, SplitQuotients};
use isogeny_algos::curve::{self, Curve, Pt};
use isogeny_algos::field::{Field, Zp};
use isogeny_algos::genus2;
use num_traits::ToPrimitive;
use std::collections::HashMap;

type Result<T> = std::result::Result<T, String>;

pub(super) struct DirectNorms {
    fp: Zp,
    balanced: Balanced,
    curves: [Curve<u64>; 2],
    shifts: [u64; 2],
    b: u64,
}
impl DirectNorms {
    pub(super) fn new(coefficients: [u64; 3]) -> Result<Self> {
        if ![[56, 13, 6], [68, 42, 26]].contains(&coefficients) {
            return Err("direct norm prototype supports only the declared C0/C1 models".into());
        }
        Self::declared_model(coefficients)
    }

    pub(super) fn successor() -> Result<Self> {
        Self::declared_model([19, 10, 22])
    }

    fn declared_model(coefficients: [u64; 3]) -> Result<Self> {
        let fp = Zp::new(101);
        let [b, c, d] = coefficients;
        let balanced = Balanced::new(101, &[b, 0, c, 0, d, 0, 1])?;
        let cubics = [vec![b, c, d, 1], vec![fp.sq(b), fp.mul(b, d), c, 1]];
        let curves = cubics.each_ref().map(|c| genus2::cubic_to_short(&fp, c));
        let shifts = cubics.each_ref().map(|c| fp.div(c[2], 3));
        Ok(Self {
            fp,
            balanced,
            curves,
            shifts,
            b,
        })
    }

    fn second_point(&self, x: u64, y: u64) -> Pt<u64> {
        if x == 0 {
            return Pt::Inf;
        }
        let f = &self.fp;
        Pt::Aff(
            f.add(f.div(self.b, f.sq(x)), self.shifts[1]),
            f.div(f.mul(self.b, y), f.pow(x, 3)),
        )
    }

    /// Sum the two elliptic images of valid quadratic support. Repeated
    /// source roots use the Mumford jet encoded by v,not two arbitrary copies.
    fn pair_sum(
        &self,
        e: &Curve<u64>,
        ab: [u64; 2],
        v: [u64; 2],
        lambda: u64,
        s: u64,
    ) -> Result<Pt<u64>> {
        let f = &self.fp;
        let [a, b] = ab;
        let [v0, v1] = v;
        if lambda == 0 {
            return Err("zero quotient coordinate scale".into());
        }
        if a == 0 {
            if v1 == 0 {
                let p = Pt::Aff(f.sub(s, f.mul(lambda, b)), v0);
                if !curve::on_curve(f, e, &p) {
                    return Err("even-support doubled point is not on quotient".into());
                }
                return Ok(curve::pmul(f, e, &p, 2));
            }
            if v0 == 0 {
                return Ok(Pt::Inf);
            }
            return Err("valid even support must have V0*V1=0".into());
        }
        let m = f.neg(f.div(v1, f.mul(lambda, a)));
        let x = f.sub(
            f.sub(f.sq(m), f.mul(lambda, f.sub(f.sq(a), f.mul(2, b)))),
            f.mul(2, s),
        );
        let y = f.sub(f.mul(m, f.sub(f.sub(s, f.mul(lambda, b)), x)), v0);
        Ok(Pt::Aff(x, y))
    }

    pub(super) fn norms(&self, d: &Class) -> Result<[Pt<u64>; 2]> {
        self.balanced.check(d)?;
        let (u, v, plus) = d.components();
        let m = u.degree().ok_or("zero norm support")?;
        let c = |p: &crate::reference::FpPoly, i| p.coeff(i).to_u64().unwrap();
        let f = &self.fp;
        let mut out = match m {
            0 => [Pt::Inf; 2],
            1 => {
                let x = f.neg(c(u, 0));
                let y = c(v, 0);
                [
                    Pt::Aff(f.add(f.sq(x), self.shifts[0]), y),
                    self.second_point(x, y),
                ]
            }
            2 => {
                let a = c(u, 1);
                let b = c(u, 0);
                let v0 = c(v, 0);
                let v1 = c(v, 1);
                let first = self.pair_sum(&self.curves[0], [a, b], [v0, v1], 1, self.shifts[0])?;
                let second = if b == 0 {
                    if a == 0 {
                        Pt::Inf
                    } else {
                        self.second_point(f.neg(a), f.sub(v0, f.mul(a, v1)))
                    }
                } else {
                    let ap = f.div(a, b);
                    let bp = f.inv(b);
                    let w1 = f.mul(self.b, f.sub(f.mul(v0, f.sub(f.sq(ap), bp)), f.mul(v1, ap)));
                    let w0 = f.mul(self.b, f.sub(f.mul(f.mul(v0, ap), bp), f.mul(v1, bp)));
                    self.pair_sum(&self.curves[1], [ap, bp], [w0, w1], self.b, self.shifts[1])?
                };
                [first, second]
            }
            _ => return Err("norm support degree exceeds2".into()),
        };
        let coefficient = 2 * i64::from(plus) + m as i64 - 2;
        if coefficient != 0 {
            let mut q = Pt::Aff(self.shifts[1], self.b);
            if coefficient < 0 {
                q = curve::neg(f, &q);
            }
            let correction = curve::pmul(
                f,
                &self.curves[1],
                &q,
                u128::from(coefficient.unsigned_abs()),
            );
            out[1] = curve::padd(f, &self.curves[1], &out[1], &correction);
        }
        for (p, e) in out.iter().zip(&self.curves) {
            if !curve::on_curve(f, e, p) {
                return Err("direct norm did not land on actual quotient".into());
            }
        }
        Ok(out)
    }
}

fn assert_complete_model(coefficients: [u64; 3], d: DirectNorms) {
    let old = SplitQuotients::new(101, coefficients).unwrap();
    assert_eq!(
        d.balanced.equation_and_infinity(),
        old.first.balanced.equation_and_infinity()
    );
    let classes = d.balanced.classes().unwrap();
    assert_eq!(classes.len(), 12317);
    let mut categories = [0_usize; 7];
    let mut repeated = 0;
    let mut infinity_correction = 0;
    let outputs = classes
        .iter()
        .enumerate()
        .map(|(i, c)| {
            let out = d
                .norms(c)
                .unwrap_or_else(|e| panic!("direct{coefficients:?}class{i}:{e}"));
            let (a, b) = old.norms(c).unwrap();
            let reference = [
                short_point(&d.fp, &old.first.base, &a, d.shifts[0]),
                short_point(&d.fp, &old.second.base, &b, d.shifts[1]),
            ];
            assert_eq!(out, reference, "both norms model{coefficients:?}class{i}");
            let (u, _, plus) = c.components();
            let m = u.degree().unwrap();
            let ab = [u.coeff(1).to_u64().unwrap(), u.coeff(0).to_u64().unwrap()];
            let category = match m {
                0 => 0,
                1 => {
                    if ab[1] == 0 {
                        1
                    } else {
                        2
                    }
                }
                2 => match (ab[0] == 0, ab[1] == 0) {
                    (true, true) => 3,
                    (true, false) => 4,
                    (false, true) => 5,
                    (false, false) => 6,
                },
                _ => unreachable!(),
            };
            categories[category] += 1;
            if m == 2 && d.fp.sub(d.fp.sq(ab[0]), d.fp.mul(4, ab[1])) == 0 {
                repeated += 1;
            }
            if 2 * i64::from(plus) + m as i64 - 2 != 0 {
                infinity_correction += 1;
            }
            out
        })
        .collect::<Vec<_>>();
    assert_eq!(categories.iter().sum::<usize>(), 12317);
    assert!(categories.iter().all(|n| *n > 0));
    assert!(repeated > 0 && infinity_correction > 0);
    let index = classes
        .iter()
        .enumerate()
        .map(|(i, c)| (super::class_key(c), i))
        .collect::<HashMap<_, _>>();
    let orders = if coefficients == [56, 13, 6] {
        [109, 113]
    } else {
        [113, 109]
    };
    for i in 0..classes.len() {
        let j = (7919 * i + 37) % classes.len();
        let sum = d.balanced.add(&classes[i], &classes[j]).unwrap();
        let k = index[&super::class_key(&sum)];
        for (component, order) in orders.into_iter().enumerate() {
            assert_eq!(
                curve::pmul(&d.fp, &d.curves[component], &outputs[i][component], order),
                Pt::Inf
            );
            assert_eq!(
                curve::padd(
                    &d.fp,
                    &d.curves[component],
                    &outputs[i][component],
                    &outputs[j][component]
                ),
                outputs[k][component]
            );
        }
    }
    let other = DirectNorms::new(if coefficients == [56, 13, 6] {
        [68, 42, 26]
    } else {
        [56, 13, 6]
    })
    .unwrap();
    assert!(d.norms(&other.balanced.zero()).is_err());
    assert_eq!(d.norms(&d.balanced.zero()).unwrap(), [Pt::Inf; 2]);
    println!("PASS both direct norms versus generic reference onALL12317 model{coefficients:?}classes,allpaired additions/orders,wrongmodel rejection;disjointdegree/zero categories{categories:?},repeated{repeated},infinitycorrections{infinity_correction};not a benchmark or fullglobalnorm proof");
}

#[test]
fn direct_norms_both_complete_models_and_all_exceptions() {
    for coefficients in [[56, 13, 6], [68, 42, 26]] {
        assert_complete_model(coefficients, DirectNorms::new(coefficients).unwrap());
    }
    assert!(DirectNorms::new([0, 0, 0]).is_err());
}

#[test]
fn successor_direct_norms_complete_c2_and_all_exceptions() {
    let d = DirectNorms::successor().unwrap();
    assert_eq!(d.shifts, [41, 37]);
    assert_eq!(
        d.curves.each_ref().map(|e| (e.a, e.b)),
        [(17, 91), (48, 48)]
    );
    assert!(
        DirectNorms::new([19, 10, 22]).is_err(),
        "old C0/C1 constructor remains narrow"
    );
    assert_complete_model([19, 10, 22], d);
}
