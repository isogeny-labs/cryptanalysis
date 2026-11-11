//! Actual geometric torsion certificates for the fixed Phi construction.
//! Existing FpR/tower/elliptic/Cantor engines are reused unchanged.
use super::super::frobenius_class;
use super::{
    extension_product_pull, lift_map, old_charts, Divisor, Element, Jacobian, SevenTransfer,
    TowerField,
};
use crate::reference::FpPoly;
use isogeny_algos::curve::{self, Curve, Isogeny, Pt, RatIsogeny};
use isogeny_algos::field::{Field, Rng};
use isogeny_algos::fpr::{FpR, ER};
use isogeny_algos::poly;
use num_bigint::BigUint;
use std::collections::HashSet;

struct Bridge {
    f: FpR,
    k: TowerField,
    gamma: Element,
    t: ER,
    s: ER,
}
impl Bridge {
    fn new() -> Self {
        let f = FpR::from_modulus(101, &[33, 46, 2, 18, 56, 12, 1]);
        let k = TowerField::new(super::super::CubicField::with_cubic(101, [56, 13, 6]).unwrap());
        assert_eq!(k.nonresidue, k.k.c(2));
        let tower_t = k.lift3(&FpPoly::x(BigUint::from(101_u64)));
        let tower_s = Element {
            a: k.k.z(),
            b: k.k.c(1),
        };
        let gamma = k.add(&tower_t, &tower_s);
        let g = f.gen();
        let lift = |a: &[u64]| a.iter().map(|c| f.from_u64(*c)).collect::<Vec<_>>();
        let numerator = poly::eval(&f, &lift(&[68, 19, 6, 1]), g);
        let denominator = poly::eval(&f, &lift(&[15, 12, 3]), g);
        assert_ne!(denominator, f.zero());
        let s = f.div(numerator, denominator);
        let t = f.sub(g, s);
        assert_eq!(f.sq(s), f.from_u64(2));
        assert_eq!(poly::eval(&f, &lift(&[56, 13, 6, 1]), t), f.zero());
        assert_eq!(f.frobenius(f.frobenius(f.frobenius(t))), t);
        assert_eq!(f.frobenius(f.frobenius(f.frobenius(s))), f.neg(s));
        let out = Self { f, k, gamma, t, s };
        assert_eq!(out.embed(out.t), tower_t);
        assert_eq!(out.embed(out.s), tower_s);
        let flat_modulus = [33, 46, 2, 18, 56, 12, 1].map(|c| out.k.c(c)).to_vec();
        assert!(out.k.zero(&out.k.value(&flat_modulus, &out.gamma)));
        out
    }

    fn embed(&self, a: ER) -> Element {
        assert!(a.iter().all(|c| *c < 101));
        assert!(a[6..].iter().all(|c| *c == 0));
        a[..6].iter().rev().fold(self.k.c(0), |acc, c| {
            self.k.add(&self.k.mul(&acc, &self.gamma), &self.k.c(*c))
        })
    }
}

fn multiply(j: &Jacobian<'_>, d: &Divisor, mut n: u64) -> Divisor {
    let mut out = j.zero();
    let mut term = d.clone();
    while n != 0 {
        if n & 1 != 0 {
            out = j.add(&out, &term).unwrap();
        }
        n >>= 1;
        if n != 0 {
            term = j.add(&term, &term).unwrap();
        }
    }
    out
}

fn frobenius_point(f: &FpR, p: Pt<ER>) -> Pt<ER> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => Pt::Aff(f.frobenius(x), f.frobenius(y)),
    }
}

fn elliptic_seven_points(f: &FpR, iso: &RatIsogeny<FpR>) -> Vec<Pt<ER>> {
    let mut rng = Rng::new(0x21_101_7);
    let roots = poly::roots(f, &iso.ker, &mut rng);
    assert_eq!(roots.len(), 3);
    assert_eq!(roots.iter().copied().collect::<HashSet<_>>().len(), 3);
    let mut all = vec![Pt::Inf];
    for x in roots {
        let y = f
            .sqrt(curve::rhs(f, &iso.dom, x))
            .expect("selected7-kernel splits over declaredFp6");
        assert_ne!(y, f.zero());
        all.extend([Pt::Aff(x, y), Pt::Aff(x, f.neg(y))]);
    }
    assert_eq!(all.iter().copied().collect::<HashSet<_>>().len(), 7);
    for p in &all {
        assert!(curve::on_curve(f, &iso.dom, p));
        assert_eq!(curve::pmul(f, &iso.dom, p, 7), Pt::Inf);
        assert_eq!(iso.eval(f, p), Pt::Inf);
    }
    let generator = all[1];
    let cyclic = (0..7)
        .map(|n| curve::pmul(f, &iso.dom, &generator, n))
        .collect::<Vec<_>>();
    assert_eq!(
        cyclic.iter().copied().collect::<HashSet<_>>(),
        all.into_iter().collect()
    );
    cyclic
}

#[test]
fn common_flat_tower_bridge_and_frobenius() {
    let b = Bridge::new();
    assert_eq!(b.embed(b.f.gen()), b.gamma);
    assert_eq!(b.k.pow(&b.gamma, 101_u64.pow(6)), b.gamma);
    println!("PASS exact fixedFp6 flat/tower primitive bridge,canonical tails,T/s inverse formulas,root equations and Frobenius3/6;unchanged independent128-witness receipt remains separate");
}

#[test]
fn explicit_geometric_seven_kernel_all49_group_and_frobenius() {
    let t = SevenTransfer::new();
    let b = Bridge::new();
    let source = Jacobian::new(&b.k, &t.source.first.balanced);
    let target = Jacobian::new(&b.k, &t.target.first.balanced);
    let maps = t.edges.each_ref().map(|e| lift_map(&b.f, e));
    let kernels: [Vec<Pt<ER>>; 2] = std::array::from_fn(|i| elliptic_seven_points(&b.f, &maps[i]));
    let eigen: [usize; 2] = std::array::from_fn(|i| {
        (1..7)
            .find(|n| {
                curve::pmul(&b.f, &maps[i].dom, &kernels[i][1], *n as u128)
                    == frobenius_point(&b.f, kernels[i][1])
            })
            .unwrap()
    });
    assert!([2, 5].contains(&eigen[0]));
    assert!([4, 6].contains(&eigen[1]));
    let mut points = vec![];
    for p in &kernels[0] {
        for q in &kernels[1] {
            let product = [*p, *q];
            let d =
                extension_product_pull(&source, &b.f, product, &old_charts(), 56, |a| b.embed(a))
                    .unwrap();
            assert!(
                !points.contains(&d),
                "P0 must be injective on product7-torsion"
            );
            assert_eq!(multiply(&source, &d, 7), source.zero());
            let image = std::array::from_fn(|i| maps[i].eval(&b.f, &product[i]));
            assert_eq!(
                extension_product_pull(&target, &b.f, image, &t.model.charts, 68, |a| b.embed(a))
                    .unwrap(),
                target.zero(),
                "Phi P0=P1 alpha kills actual product7-kernel"
            );
            points.push(d);
        }
    }
    assert_eq!(points.len(), 49);
    assert_eq!(points[0], source.zero());
    for i in 0..49 {
        let fi = ((i / 7 * eigen[0]) % 7) * 7 + (i % 7 * eigen[1]) % 7;
        assert_eq!(frobenius_class(&b.k, &points[i], 1), points[fi]);
        for j in 0..49 {
            let sum = ((i / 7 + j / 7) % 7) * 7 + (i % 7 + j % 7) % 7;
            assert_eq!(source.add(&points[i], &points[j]).unwrap(), points[sum]);
        }
    }
    println!("PASS actual49 geometric Phi-kernel points=P0(Ker alpha),all7-annihilators/all2401 additions/Frobenius closure,eigenscalars{eigen:?};degree49/prime-to2 quotient proof identifies the full kernel;not a solver or signed verdict");
}
