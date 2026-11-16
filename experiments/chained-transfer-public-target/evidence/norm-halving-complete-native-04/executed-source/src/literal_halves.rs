//! Literal existing complete selector; only visibility/name change in the body.
use isogeny_algos::{
    curve::{self, Curve, Pt},
    field::{Field, Rng},
    fpr::{FpR, ER},
    poly,
};
use std::collections::HashSet;

#[rustfmt::skip]
pub fn literal_halves(f: &FpR, e: &Curve<ER>, q: Pt<ER>, two: &[Pt<ER>]) -> Vec<Pt<ER>> {
    let Pt::Aff(x, y) = q else {
        assert_eq!(two.len(), 4);
        return two.to_vec();
    };
    let u = vec![
        f.sub(f.sq(e.a), f.mul(f.from_u64(4), f.mul(e.b, x))),
        f.neg(f.add(
            f.mul(f.from_u64(8), e.b),
            f.mul(f.from_u64(4), f.mul(e.a, x)),
        )),
        f.neg(f.mul(f.from_u64(2), e.a)),
        f.neg(f.mul(f.from_u64(4), x)),
        f.one(),
    ];
    let mut xs = poly::roots(f, &u, &mut Rng::new(0x3916));
    xs.sort();
    assert_eq!(xs.len(), if y == f.zero() { 2 } else { 4 });
    let mut out = vec![];
    for x in xs {
        let rhs = curve::rhs(f, e, x);
        assert_ne!(rhs, f.zero());
        let mut ys = poly::roots(
            f,
            &vec![f.neg(rhs), f.zero(), f.one()],
            &mut Rng::new(0x3917),
        );
        ys.sort();
        assert_eq!(ys.len(), 2);
        for y in ys {
            let p = Pt::Aff(x, y);
            assert!(curve::on_curve(f, e, &p));
            if curve::pmul(f, e, &p, 2) == q {
                out.push(p);
            }
        }
    }
    assert_eq!(out.len(), 4);
    assert_eq!(out.iter().copied().collect::<HashSet<_>>().len(), 4);
    out
}
