//! Actual geometric torsion certificates for the fixed Phi construction.
//! Existing FpR/tower/elliptic/Cantor engines are reused unchanged.
use super::super::frobenius_class;
use super::{
    extension_product_pull, lift_map, old_charts, source_branch_roots, Divisor, Element, Jacobian,
    SevenTransfer, TowerField,
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

fn elliptic_two_points(b: &Bridge, component: usize) -> [Pt<ER>; 4] {
    let f = &b.f;
    let a = [b.t, f.frobenius(b.t), f.frobenius(f.frobenius(b.t))];
    std::array::from_fn(|i| {
        if i == 0 {
            return Pt::Inf;
        }
        let x = if component == 0 {
            f.add(a[i - 1], f.from_u64(2))
        } else {
            f.add(f.div(f.from_u64(56), a[i - 1]), f.from_u64(38))
        };
        Pt::Aff(x, f.zero())
    })
}

fn four_halves(f: &FpR, e: &Curve<ER>, two: &[Pt<ER>; 4], index: usize) -> Vec<Pt<ER>> {
    let points = if index == 0 {
        two.to_vec()
    } else {
        let xs: [ER; 3] = std::array::from_fn(|i| match two[i + 1] {
            Pt::Aff(x, y) => {
                assert_eq!(y, f.zero());
                x
            }
            Pt::Inf => panic!("nonzero elliptic2-torsion missing"),
        });
        let i = index - 1;
        let r = xs[i];
        let disc = f.mul(f.sub(r, xs[(i + 1) % 3]), f.sub(r, xs[(i + 2) % 3]));
        let s = f
            .sqrt(disc)
            .expect("all elliptic4-torsion lies in declaredFp6");
        assert_ne!(s, f.zero());
        let mut out = vec![];
        for x in [f.add(r, s), f.sub(r, s)] {
            let y = f
                .sqrt(curve::rhs(f, e, x))
                .expect("actual elliptic4-point ordinate");
            assert_ne!(y, f.zero());
            out.extend([Pt::Aff(x, y), Pt::Aff(x, f.neg(y))]);
        }
        out
    };
    assert_eq!(points.iter().copied().collect::<HashSet<_>>().len(), 4);
    for p in &points {
        assert!(curve::on_curve(f, e, p));
        assert_eq!(curve::pmul(f, e, p, 2), two[index]);
        assert_eq!(curve::pmul(f, e, p, 4), Pt::Inf);
    }
    points
}

struct TwoAction {
    roots: Vec<Element>,
    mapping: Vec<(Divisor, Divisor)>,
    pairing: [(usize, usize); 3],
    raw_target: Vec<u64>,
}

fn two_action(t: &SevenTransfer, b: &Bridge) -> TwoAction {
    let f = &b.f;
    let k = &b.k;
    let source = Jacobian::new(k, &t.source.first.balanced);
    let target = Jacobian::new(k, &t.target.first.balanced);
    let source_roots = source_branch_roots(k);
    let actual_old = super::super::construct_for(101, [56, 13, 6]).unwrap();
    assert_eq!(
        actual_old.roots,
        source_roots.iter().map(|r| r.a.clone()).collect::<Vec<_>>()
    );
    let mut old_corpus = super::super::branch_two_torsion(&source, &source_roots);
    old_corpus.push(source.zero());
    let maps = t.edges.each_ref().map(|e| lift_map(f, e));
    let two = [elliptic_two_points(b, 0), elliptic_two_points(b, 1)];
    let halves: [[Vec<Pt<ER>>; 4]; 2] =
        std::array::from_fn(|i| std::array::from_fn(|h| four_halves(f, &maps[i].dom, &two[i], h)));
    let mut lifts = HashSet::new();
    let mut values: Vec<(Divisor, Divisor, usize)> = vec![];
    for h in 0..4 {
        let graph = [two[0][h], two[1][h]];
        assert_eq!(
            extension_product_pull(&source, f, graph, &old_charts(), 56, |a| b.embed(a)).unwrap(),
            source.zero()
        );
        for a in &halves[0][h] {
            for c in &halves[1][h] {
                let product = [*a, *c];
                assert!(lifts.insert(product));
                let old =
                    extension_product_pull(&source, f, product, &old_charts(), 56, |a| b.embed(a))
                        .unwrap();
                assert_eq!(source.add(&old, &old).unwrap(), source.zero());
                assert!(old_corpus.contains(&old));
                let image = std::array::from_fn(|i| maps[i].eval(f, &product[i]));
                let new =
                    extension_product_pull(&target, f, image, &t.model.charts, 68, |a| b.embed(a))
                        .unwrap();
                assert_eq!(target.add(&new, &new).unwrap(), target.zero());
                if let Some(row) = values.iter_mut().find(|row| row.0 == old) {
                    assert_eq!(
                        row.1, new,
                        "Phi P0=P1 alpha must be independent of the4-lift"
                    );
                    row.2 += 1;
                } else {
                    values.push((old, new, 1));
                }
            }
        }
    }
    assert_eq!(lifts.len(), 64);
    assert_eq!(values.len(), 16);
    assert!(values.iter().all(|row| row.2 == 4));
    for d in &old_corpus {
        assert!(values.iter().any(|row| row.0 == *d));
    }

    // New branch roots from the ACTUAL first quotient2-torsion coordinate.
    let chart = t.model.charts[0];
    assert_eq!(chart.destination, 1);
    let p = maps[1].eval(f, &two[1][1]);
    let Pt::Aff(x, y) = p else {
        panic!("odd map killed nonzero2-torsion")
    };
    assert_eq!(y, f.zero());
    let u = f.sub(
        f.mul(x, f.from_u64(t.fp.inv(t.fp.sq(chart.scale)))),
        f.from_u64(chart.shift),
    );
    let mut beta = b.embed(f.sqrt(u).expect("actual new branch square root"));
    assert!(
        beta.b.is_zero(),
        "odd Phi requires new branch roots in cubic subfield"
    );
    let negative = k.neg(&beta);
    if k.k.encoding(&negative.a) < k.k.encoding(&beta.a) {
        beta = negative;
    }
    let beta1 = k.pow(&beta, 101);
    let beta2 = k.pow(&beta1, 101);
    assert_eq!(k.pow(&beta2, 101), beta);
    let roots = vec![
        beta.clone(),
        beta1.clone(),
        beta2.clone(),
        k.neg(&beta),
        k.neg(&beta1),
        k.neg(&beta2),
    ];
    assert!(roots.iter().all(|r| r.b.is_zero()));
    let mut new_corpus = super::super::branch_two_torsion(&target, &roots);
    new_corpus.push(target.zero());
    for row in &values {
        assert!(new_corpus.contains(&row.1));
    }
    for d in &new_corpus {
        assert_eq!(values.iter().filter(|row| row.1 == *d).count(), 1);
    }
    for a in &values {
        let old_frob = frobenius_class(k, &a.0, 1);
        let row = values.iter().find(|row| row.0 == old_frob).unwrap();
        assert_eq!(row.1, frobenius_class(k, &a.1, 1));
        for c in &values {
            let sum = source.add(&a.0, &c.0).unwrap();
            let row = values.iter().find(|row| row.0 == sum).unwrap();
            assert_eq!(target.add(&a.1, &c.1).unwrap(), row.1);
        }
    }

    let labels = (0..6)
        .flat_map(|i| (i + 1..6).map(move |j| (i, j)))
        .collect::<Vec<_>>();
    let mut pairing = [(0, 0); 3];
    for (h, (i, j)) in [(0, 4), (1, 5), (2, 3)].into_iter().enumerate() {
        let d = source
            .pair(
                vec![
                    k.mul(&source_roots[i], &source_roots[j]),
                    k.neg(&k.add(&source_roots[i], &source_roots[j])),
                    k.c(1),
                ],
                vec![],
                0,
            )
            .unwrap();
        let image = &values.iter().find(|row| row.0 == d).unwrap().1;
        pairing[h] = labels[new_corpus
            .iter()
            .take(15)
            .position(|d| d == image)
            .expect("cross-kernel image nonzero branch class")];
    }
    pairing.sort_unstable();
    assert_eq!(
        pairing
            .iter()
            .flat_map(|(i, j)| [*i, *j])
            .collect::<HashSet<_>>()
            .len(),
        6
    );
    let permutation: [usize; 6] = std::array::from_fn(|i| {
        roots
            .iter()
            .position(|r| *r == k.pow(&roots[i], 101))
            .unwrap()
    });
    assert_eq!(permutation, [1, 2, 0, 4, 5, 3]);
    let mut frob_pairing = pairing.map(|(i, j)| {
        let (a, c) = (permutation[i], permutation[j]);
        if a < c {
            (a, c)
        } else {
            (c, a)
        }
    });
    frob_pairing.sort_unstable();
    assert_eq!(frob_pairing, pairing);
    let g = pairing.map(|(i, j)| {
        vec![
            k.k.mul(&roots[i].a, &roots[j].a),
            roots[i].a.add(&roots[j].a).neg(),
            k.k.c(1),
        ]
    });
    let delta = k.k.determinant(&g);
    assert!(!delta.is_zero());
    let h = k.k.dual_factors(&g, &delta);
    let raw_target =
        k.k.product(&h)
            .iter()
            .map(|c| k.k.base(c))
            .collect::<Vec<_>>();
    println!("transported actual R1 pairing{pairing:?},delta{},raw target{raw_target:?};normalization/map/duals are the next acceptance step",k.k.base(&delta));
    TwoAction {
        roots,
        mapping: values.into_iter().map(|(a, c, _)| (a, c)).collect(),
        pairing,
        raw_target,
    }
}

#[test]
fn sixty_four_lifts_actual_phi_two_action_and_transported_kernel() {
    let t = SevenTransfer::new();
    let b = Bridge::new();
    let action = two_action(&t, &b);
    assert_eq!(
        (
            action.roots.len(),
            action.mapping.len(),
            action.raw_target.len()
        ),
        (6, 16, 7)
    );
    println!("PASS64 actual product4-torsion lifts,all16 source/target2-classes,four consistent preimages each,bijection,all256 additions/Frobenius,transported cross-kernel{:?};no Jacobian halving or scalar labels;actual R1/Psi remain next",action.pairing);
}
