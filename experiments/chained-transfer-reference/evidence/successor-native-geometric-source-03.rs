//! Actual geometric certificates for Phi2 and transport of the accepted R1 kernel.
use super::super::super::{branch_two_torsion, extension_product_pull, lift_map};
use super::super::{
    elliptic_seven_points, elliptic_two_points, four_halves, frobenius_class, frobenius_point,
    multiply, two_action, Bridge, Divisor, Element, Jacobian,
};
use super::SevenSuccessor;
use isogeny_algos::curve::{self, Isogeny, Pt};
use isogeny_algos::field::Field;
use isogeny_algos::fpr::ER;
use std::collections::HashSet;

#[test]
fn successor_seven_geometric_kernel49_group_and_frobenius() {
    let s = SevenSuccessor::new();
    let b = Bridge::new();
    let source = Jacobian::new(&b.k, &s.old.target.first.balanced);
    let target = Jacobian::new(&b.k, &s.target.first.balanced);
    let maps = s.beta.each_ref().map(|e| lift_map(&b.f, e));
    let kernels = maps.each_ref().map(|e| elliptic_seven_points(&b.f, e));
    let eigen: [usize; 2] = std::array::from_fn(|i| {
        (1..7)
            .find(|n| {
                curve::pmul(&b.f, &maps[i].dom, &kernels[i][1], *n as u128)
                    == frobenius_point(&b.f, kernels[i][1])
            })
            .unwrap()
    });
    assert_eq!(eigen, [5, 6]);
    let mut points = vec![];
    for p in &kernels[0] {
        for q in &kernels[1] {
            let product = [*p, *q];
            let d = extension_product_pull(&source, &b.f, product, &s.old.model.charts, 68, |a| {
                b.embed(a)
            })
            .unwrap();
            assert!(!points.contains(&d));
            assert_eq!(multiply(&source, &d, 7), source.zero());
            let images = std::array::from_fn(|i| maps[i].eval(&b.f, &product[i]));
            assert_eq!(
                extension_product_pull(&target, &b.f, images, &s.charts, 19, |a| b.embed(a))
                    .unwrap(),
                target.zero()
            );
            points.push(d);
        }
    }
    assert_eq!(points.len(), 49);
    for i in 0..49 {
        let fi = ((i / 7 * 5) % 7) * 7 + (i % 7 * 6) % 7;
        assert_eq!(frobenius_class(&b.k, &points[i], 1), points[fi]);
        for j in 0..49 {
            let sum = ((i / 7 + j / 7) % 7) * 7 + (i % 7 + j % 7) % 7;
            assert_eq!(source.add(&points[i], &points[j]).unwrap(), points[sum]);
        }
    }
    println!("PASS actual49 Phi2-kernel classes=P1(Ker beta),all7-annihilators/all2401 additions/Frobenius5/6 and targetP2 beta killing,using existingFp6;full composite49² kernel still requiresFp42 by separate proof");
}

fn branch_norm(s: &SevenSuccessor, b: &Bridge, p: &Element, q: &Element) -> [Pt<ER>; 2] {
    let f = &b.f;
    let maps = s.beta.each_ref().map(|e| lift_map(f, e));
    let mut norm = [Pt::Inf; 2];
    for r in [p, q] {
        let x2 = f.sq(b.flat(r));
        assert_ne!(x2, f.zero());
        let coordinates = [
            f.add(x2, f.from_u64(s.old.model.charts[0].shift)),
            f.add(
                f.div(f.from_u64(68), x2),
                f.from_u64(s.old.model.charts[1].shift),
            ),
        ];
        for (c, x) in s.old.model.charts.into_iter().zip(coordinates) {
            let point = Pt::Aff(f.mul(f.from_u64(s.old.fp.sq(c.scale)), x), f.zero());
            assert!(curve::on_curve(f, &maps[c.destination].dom, &point));
            norm[c.destination] =
                curve::padd(f, &maps[c.destination].dom, &norm[c.destination], &point);
        }
    }
    norm
}

#[test]
fn successor_seven_geometric_two_kernel_before_factor() {
    let s = SevenSuccessor::new();
    let b = Bridge::new();
    let previous = two_action(&s.old, &b);
    let source = Jacobian::new(&b.k, &s.old.target.first.balanced);
    let target = Jacobian::new(&b.k, &s.target.first.balanced);
    let maps = s.beta.each_ref().map(|e| lift_map(&b.f, e));
    let mut values = vec![(source.zero(), [Pt::Inf; 2])];
    for i in 0..6 {
        for j in i + 1..6 {
            let p = &previous.roots[i];
            let q = &previous.roots[j];
            let d = source
                .pair(
                    vec![b.k.mul(p, q), b.k.neg(&b.k.add(p, q)), b.k.c(1)],
                    vec![],
                    0,
                )
                .unwrap();
            let norm = branch_norm(&s, &b, p, q);
            assert_eq!(
                extension_product_pull(&source, &b.f, norm, &s.old.model.charts, 68, |a| b
                    .embed(a))
                .unwrap(),
                source.zero()
            );
            let images = std::array::from_fn(|h| maps[h].eval(&b.f, &norm[h]));
            assert_eq!(
                extension_product_pull(&target, &b.f, images, &s.charts, 19, |a| b.embed(a))
                    .unwrap(),
                target.zero()
            );
            values.push((d, norm));
        }
    }
    assert_eq!(values.len(), 16);
    assert_eq!(values.iter().map(|v| v.1).collect::<HashSet<_>>().len(), 4);
    assert_eq!(values.iter().filter(|v| v.1 == [Pt::Inf; 2]).count(), 4);
    for row in &values {
        let conjugate = frobenius_class(&b.k, &row.0, 1);
        let found = values.iter().find(|v| v.0 == conjugate).unwrap();
        assert_eq!(found.1, row.1.map(|p| frobenius_point(&b.f, p)));
        for other in &values {
            let sum = source.add(&row.0, &other.0).unwrap();
            let found = values.iter().find(|v| v.0 == sum).unwrap();
            for i in 0..2 {
                assert_eq!(
                    found.1[i],
                    curve::padd(&b.f, &maps[i].dom, &row.1[i], &other.1[i])
                );
            }
        }
    }
    println!("PASS ALL16 actual geometric C1J[2],matched N1 graph4/kernel4,all256 norm additions/Frobenius and complete P2 beta N1 annihilation;global regular Phi2 quotient is the separate written proof");
}

struct SuccessorTwoAction {
    roots: Vec<Element>,
    mapping: Vec<(Divisor, Divisor)>,
    pairing: [(usize, usize); 3],
    raw_target: Vec<u64>,
}

fn successor_two_action(s: &SevenSuccessor, b: &Bridge) -> SuccessorTwoAction {
    let previous = two_action(&s.old, b);
    let f = &b.f;
    let k = &b.k;
    let source = Jacobian::new(k, &s.old.target.first.balanced);
    let target = Jacobian::new(k, &s.target.first.balanced);
    let alpha = s.old.edges.each_ref().map(|e| lift_map(f, e));
    let beta = s.beta.each_ref().map(|e| lift_map(f, e));
    let old_two = [elliptic_two_points(b, 0), elliptic_two_points(b, 1)];
    let halves: [[Vec<Pt<ER>>; 4]; 2] = std::array::from_fn(|i| {
        std::array::from_fn(|h| four_halves(f, &alpha[i].dom, &old_two[i], h))
    });
    let mut lifts = HashSet::new();
    let mut values: Vec<(Divisor, Divisor, usize)> = vec![];
    let mut source_corpus = branch_two_torsion(&source, &previous.roots);
    source_corpus.push(source.zero());
    for h in 0..4 {
        let graph = std::array::from_fn(|i| alpha[i].eval(f, &old_two[i][h]));
        assert_eq!(
            extension_product_pull(&source, f, graph, &s.old.model.charts, 68, |a| b.embed(a))
                .unwrap(),
            source.zero()
        );
        for p in &halves[0][h] {
            for q in &halves[1][h] {
                let original = [*p, *q];
                assert!(lifts.insert(original));
                let product = std::array::from_fn(|i| alpha[i].eval(f, &original[i]));
                let d = extension_product_pull(&source, f, product, &s.old.model.charts, 68, |a| {
                    b.embed(a)
                })
                .unwrap();
                assert_eq!(source.add(&d, &d).unwrap(), source.zero());
                assert!(source_corpus.contains(&d));
                let image = std::array::from_fn(|i| beta[i].eval(f, &product[i]));
                let out = extension_product_pull(&target, f, image, &s.charts, 19, |a| b.embed(a))
                    .unwrap();
                assert_eq!(target.add(&out, &out).unwrap(), target.zero());
                if let Some(row) = values.iter_mut().find(|v| v.0 == d) {
                    assert_eq!(row.1, out);
                    row.2 += 1;
                } else {
                    values.push((d, out, 1));
                }
            }
        }
    }
    assert_eq!(lifts.len(), 64);
    assert_eq!(values.len(), 16);
    assert!(values.iter().all(|v| v.2 == 4));
    let c = s.charts[0];
    assert_eq!(c.destination, 1);
    let point = beta[1].eval(f, &alpha[1].eval(f, &old_two[1][1]));
    let Pt::Aff(x, y) = point else {
        panic!("odd chain killed nonzero2-point")
    };
    assert_eq!(y, f.zero());
    let u = f.sub(
        f.mul(x, f.from_u64(s.old.fp.inv(s.old.fp.sq(c.scale)))),
        f.from_u64(c.shift),
    );
    let mut root = b.embed(f.sqrt(u).expect("actual C2 branch square root in Fp6"));
    assert!(root.b.is_zero());
    let negative = k.neg(&root);
    if k.k.encoding(&negative.a) < k.k.encoding(&root.a) {
        root = negative;
    }
    let root1 = k.pow(&root, 101);
    let root2 = k.pow(&root1, 101);
    assert_eq!(k.pow(&root2, 101), root);
    let roots = vec![
        root.clone(),
        root1.clone(),
        root2.clone(),
        k.neg(&root),
        k.neg(&root1),
        k.neg(&root2),
    ];
    assert!(roots.iter().all(|r| r.b.is_zero()));
    let mut corpus = branch_two_torsion(&target, &roots);
    corpus.push(target.zero());
    for d in &corpus {
        assert_eq!(values.iter().filter(|v| v.1 == *d).count(), 1);
    }
    for row in &values {
        let conjugate = frobenius_class(k, &row.0, 1);
        let found = values.iter().find(|v| v.0 == conjugate).unwrap();
        assert_eq!(found.1, frobenius_class(k, &row.1, 1));
        for other in &values {
            let sum = source.add(&row.0, &other.0).unwrap();
            let found = values.iter().find(|v| v.0 == sum).unwrap();
            assert_eq!(target.add(&row.1, &other.1).unwrap(), found.1);
        }
    }
    let labels = (0..6)
        .flat_map(|i| (i + 1..6).map(move |j| (i, j)))
        .collect::<Vec<_>>();
    let mut pairing = [(0, 0); 3];
    for (h, (i, j)) in previous.pairing.into_iter().enumerate() {
        let a = &previous.roots[i];
        let c = &previous.roots[j];
        let d = source
            .pair(vec![k.mul(a, c), k.neg(&k.add(a, c)), k.c(1)], vec![], 0)
            .unwrap();
        let out = &values.iter().find(|v| v.0 == d).unwrap().1;
        pairing[h] = labels[corpus
            .iter()
            .take(15)
            .position(|v| v == out)
            .expect("transported R1 kernel nonzero")];
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
    let mut conjugate = pairing.map(|(i, j)| {
        let (a, c) = (permutation[i], permutation[j]);
        if a < c {
            (a, c)
        } else {
            (c, a)
        }
    });
    conjugate.sort_unstable();
    assert_eq!(conjugate, pairing);
    let g = pairing.map(|(i, j)| {
        vec![
            k.k.mul(&roots[i].a, &roots[j].a),
            roots[i].a.add(&roots[j].a).neg(),
            k.k.c(1),
        ]
    });
    let coefficients = s
        .target
        .first
        .balanced
        .equation_and_infinity()
        .0
        .coeffs
        .iter()
        .map(|c| k.lift3(&k.k.c(c.to_u64().unwrap())))
        .collect::<Vec<_>>();
    assert_eq!(
        k.k.product(&g)
            .iter()
            .map(|c| k.lift3(c))
            .collect::<Vec<_>>(),
        coefficients
    );
    let delta = k.k.determinant(&g);
    assert!(!delta.is_zero());
    let h = k.k.dual_factors(&g, &delta);
    let raw_target =
        k.k.product(&h)
            .iter()
            .map(|c| k.k.base(c))
            .collect::<Vec<_>>();
    println!("ACTUAL R2 transported pairing{pairing:?},delta{},raw target{raw_target:?};normalization/map/dual acceptance next",k.k.base(&delta));
    SuccessorTwoAction {
        roots,
        mapping: values.into_iter().map(|(a, c, _)| (a, c)).collect(),
        pairing,
        raw_target,
    }
}

#[test]
fn successor_seven_geometric_two_action_and_r2_transport() {
    let s = SevenSuccessor::new();
    let b = Bridge::new();
    let action = successor_two_action(&s, &b);
    assert_eq!(action.roots.len(), 6);
    assert_eq!(action.mapping.len(), 16);
    assert_eq!(action.pairing.len(), 3);
    assert_eq!(action.raw_target.len(), 7);
    println!("PASS64 actual old product4-lifts mapped through alpha then beta,all16 C1/C2 two-classes/four consistent preimages,bijection/all256 additions/Frobenius and actual transported R1 kernel;no Jacobian halving or scalar labels");
}
