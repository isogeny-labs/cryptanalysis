//! Transport the actual seven-isogeny square across the accepted Richelot
//! maps. Regular quotient descent remains an explicit written obligation.
use super::super::super::{branch_two_torsion, RichelotMap};
use super::super::{long_point, scale_point, Class, MumfordDivisorP, SevenTransfer};
use super::{extension_product_pull, lift_map, old_charts, source_branch_roots};
use super::{transported_assessment, two_action, Bridge, Divisor, Element, Jacobian};
use isogeny_algos::curve::{self, Isogeny, Pt};
use isogeny_algos::field::Field;
use isogeny_algos::fpr::ER;
use num_bigint::BigUint;
use num_traits::ToPrimitive;
use std::collections::{HashMap, HashSet};

#[test]
fn closed_fibre_targeted_r0_r1_both_directions() {
    let chain = SevenChain::new();
    for (name, r) in [("R0", &chain.r0), ("R1", &chain.r1)] {
        for reverse in [false, true] {
            let source = if reverse { &r.target } else { &r.source };
            let all = source.classes().unwrap();
            let mut counts = [0_usize; 5];
            for i in 0..192 {
                let index = if i < 12 {
                    i
                } else {
                    (i * 113 + 47) % all.len()
                };
                let d = &all[index];
                let (image, route) = r.evaluate_closed(d, reverse).unwrap();
                counts[route as usize] += 1;
                assert_eq!(
                    image,
                    r.evaluate(d, reverse).unwrap(),
                    "{name} reverse={reverse} index={index}"
                );
            }
            assert!(counts[1] > 100, "closed chart must actually be exercised");
            println!("{name} reverse={reverse} targeted192 route counts{counts:?};closed/pointwise exact equality");
        }
    }
}

#[test]
fn closed_fibre_geometric_two_boundaries_and_reference() {
    use super::super::super::closed_fibres::ClosedFibre;
    let c = SevenChain::new();
    let b = Bridge::new();
    let source0 = source_branch_roots(&b.k);
    let action = two_action(&c.t, &b);
    let target0 = target_branch_roots(&b, &c.r0);
    let target1 = target_branch_roots(&b, &c.r1);
    for (name, r, roots, reverse) in [
        ("R0", &c.r0, &source0, false),
        ("R0", &c.r0, &target0, true),
        ("R1", &c.r1, &action.roots, false),
        ("R1", &c.r1, &target1, true),
    ] {
        let values = richelot_two_action(r, roots, reverse);
        let mut counts = [0_usize; 5];
        for (d, expected) in values {
            match r.closed_extension(&d, reverse).unwrap() {
                ClosedFibre::Image(value, route) => {
                    assert_eq!(value, expected);
                    counts[route as usize] += 1;
                }
                ClosedFibre::Boundary(route) => {
                    counts[route as usize] += 1;
                }
            }
        }
        assert_eq!(counts.iter().sum::<usize>(), 16);
        assert_eq!(counts[0], 1);
        assert_eq!(counts[1], 0, "branch ordinates must not be inverted");
        assert_eq!(counts[2..].iter().sum::<usize>(), 15);
        println!("{name} reverse={reverse} ALL16 actual geometric2-torsion route counts{counts:?};identity agrees with pointwise table,all15 nonzero branch classes have explicit chart boundaries;completed pointwise action retained");
    }
}

#[test]
fn closed_fibre_all_r0_r1_domains_and_group_controls() {
    use std::cell::RefCell;
    let chain = SevenChain::new();
    let reference = SevenChain::new();
    for (name, r, old) in [
        ("R0", &chain.r0, &reference.r0),
        ("R1", &chain.r1, &reference.r1),
    ] {
        assert!(r.square_roots.get().is_none());
        assert!(old.square_roots.get().is_none());
        let counts = RefCell::new([[0_usize; 5]; 2]);
        let evaluate = |d: &Class, reverse: bool| {
            let (image, route) = r.evaluate_closed(d, reverse)?;
            assert!(r.square_roots.get().is_none(), "closed {name} used table");
            assert_eq!(
                image,
                old.evaluate(d, reverse)?,
                "all-class old/closed {name} reverse={reverse}"
            );
            counts.borrow_mut()[usize::from(reverse)][route as usize] += 1;
            Ok(image)
        };
        assert_full_graph_pair(
            &r.source,
            &r.target,
            |d| evaluate(d, false),
            |d| evaluate(d, true),
            2,
        );
        for row in *counts.borrow() {
            assert_eq!(row.iter().sum::<usize>(), 12317);
            assert!(row[1] > 10000);
        }
        assert!(r.evaluate_closed(&r.target.zero(), false).is_err());
        assert!(r.evaluate_closed(&r.source.zero(), true).is_err());
        assert!(r.square_roots.get().is_none());
        assert!(old.square_roots.get().is_some());
        println!("{name} BOTH complete12317 domains route counts{:?};old/closed equality,both dual2,bijections,paired additions,descent,wrong-model rejection pass",counts.borrow());
    }
}

#[test]
fn closed_fibre_explicit_psi_kernel49_group_dual_and_frobenius() {
    use super::super::super::closed_fibres::ClosedFibre;
    let c = SevenChain::new();
    let b = Bridge::new();
    assert_eq!(c.r0.k.k.q, b.k.k.q);
    let source = Jacobian::new(&b.k, &c.r0.source);
    let target = Jacobian::new(&c.r0.k, &c.r0.target);
    let c1 = Jacobian::new(&b.k, &c.r1.source);
    let maps = c.t.edges.each_ref().map(|e| lift_map(&b.f, e));
    let kernels = maps
        .each_ref()
        .map(|m| super::elliptic_seven_points(&b.f, m));
    let eigen: [usize; 2] = std::array::from_fn(|i| {
        (1..7)
            .find(|n| {
                curve::pmul(&b.f, &maps[i].dom, &kernels[i][1], *n as u128)
                    == super::frobenius_point(&b.f, kernels[i][1])
            })
            .unwrap()
    });
    assert_eq!(eigen, [5, 6]);
    let image = |d: &Divisor, reverse| match c.r0.closed_extension(d, reverse).unwrap() {
        ClosedFibre::Image(value, _) => value,
        ClosedFibre::Boundary(route) => {
            panic!("actual7-kernel closed chart boundary {route:?}: {d:?}")
        }
    };
    let mut points = vec![];
    for p in &kernels[0] {
        for q in &kernels[1] {
            let product = [*p, *q];
            let d =
                extension_product_pull(&source, &b.f, product, &old_charts(), 56, |a| b.embed(a))
                    .unwrap();
            let pushed = image(&d, false);
            target.check(&pushed).unwrap();
            assert!(!points.contains(&pushed));
            assert_eq!(super::multiply(&target, &pushed, 7), target.zero());
            assert_eq!(
                image(&pushed, true),
                source.add(&d, &d).unwrap(),
                "actual geometric dualR0 norm2"
            );
            let alpha = std::array::from_fn(|i| maps[i].eval(&b.f, &product[i]));
            assert_eq!(
                extension_product_pull(&c1, &b.f, alpha, &c.t.model.charts, 68, |a| b.embed(a))
                    .unwrap(),
                c1.zero(),
                "Phi kills each actual lift,so Psi R0=R1 Phi identifies the displayed kernel"
            );
            points.push(pushed);
        }
    }
    assert_eq!(points.len(), 49);
    assert_eq!(points[0], target.zero());
    let pack = |p: &[Element]| {
        p.iter()
            .map(|e| {
                std::array::from_fn::<u64, 6, _>(|i| {
                    if i < 3 {
                        e.a.coeff(i).to_u64().unwrap()
                    } else {
                        e.b.coeff(i - 3).to_u64().unwrap()
                    }
                })
            })
            .collect::<Vec<_>>()
    };
    println!("# explicit-psi-kernel/v1;p101;T^3+6T^2+13T+56=0;S^2=2;basis[1,T,T2,S,ST,ST2];T0[31,75,74,54,71,55,1];index,u_coefficients,v_coefficients,plus");
    for i in 0..49 {
        println!(
            "actualPsiKernel\t{i}\t{:?}\t{:?}\t{}",
            pack(&points[i].u),
            pack(&points[i].v),
            points[i].plus
        );
        let fi = ((i / 7 * eigen[0]) % 7) * 7 + (i % 7 * eigen[1]) % 7;
        assert_eq!(
            super::super::super::frobenius_class(&c.r0.k, &points[i], 1),
            points[fi]
        );
        for j in 0..49 {
            let sum = ((i / 7 + j / 7) % 7) * 7 + (i % 7 + j % 7) % 7;
            assert_eq!(target.add(&points[i], &points[j]).unwrap(), points[sum]);
        }
    }
    println!("PASS actual49 distinct KerPsi=R0(KerPhi) classes over existingFp6,no support-root splitting;all7-annihilators/all49 geometric dualR0 norm2/all2401 additions/Frobenius eigenscalars{eigen:?};identification uses retained global square and degree49");
}

impl Bridge {
    pub(super) fn flat(&self, a: &Element) -> ER {
        let eval = |p: &crate::reference::FpPoly| {
            p.coeffs.iter().rev().fold(self.f.zero(), |v, c| {
                self.f
                    .add(self.f.mul(v, self.t), self.f.from_u64(c.to_u64().unwrap()))
            })
        };
        let out = self.f.add(eval(&a.a), self.f.mul(self.s, eval(&a.b)));
        assert_eq!(self.embed(out), *a, "actual flat/tower round trip");
        out
    }
}

pub(super) fn target_branch_roots(b: &Bridge, r: &RichelotMap) -> Vec<Element> {
    let mut roots = vec![];
    for h in &r.h {
        assert_eq!(h.len(), 3);
        let [c, d, a] = std::array::from_fn(|i| b.flat(&h[i]));
        let disc = b.f.sub(b.f.sq(d), b.f.mul(b.f.from_u64(4), b.f.mul(a, c)));
        let s =
            b.f.sqrt(disc)
                .expect("Richelot target branches split in declaredFp6");
        assert_ne!(s, b.f.zero());
        let den = b.f.mul(b.f.from_u64(2), a);
        for v in [b.f.add(b.f.neg(d), s), b.f.sub(b.f.neg(d), s)] {
            let x = b.embed(b.f.div(v, den));
            assert!(r.k.zero(&r.k.value(h, &x)));
            assert!(!roots.contains(&x));
            roots.push(x);
        }
    }
    assert_eq!(roots.len(), 6);
    roots
}

/// Branch divisors have degree2 finite support,so their balanced-infinity
/// correction is zero. Reverse sign is the existing polarized-dual choice.
pub(super) fn richelot_two_action(
    r: &RichelotMap,
    roots: &[Element],
    reverse: bool,
) -> Vec<(Divisor, Divisor)> {
    let (a, c, g, h, scale) = if reverse {
        (&r.target, &r.source, &r.h, &r.g, 1)
    } else {
        (&r.source, &r.target, &r.g, &r.h, r.target_scale)
    };
    let source = Jacobian::new(&r.k, a);
    let target = Jacobian::new(&r.k, c);
    let ds = branch_two_torsion(&source, roots);
    let mut values = vec![(source.zero(), target.zero())];
    let mut index = 0;
    for i in 0..6 {
        for j in i + 1..6 {
            let left = r.fiber(&roots[i], &r.k.c(0), g, h, scale, &target).unwrap();
            let right = r.fiber(&roots[j], &r.k.c(0), g, h, scale, &target).unwrap();
            let mut image = target.add(&left, &right).unwrap();
            if reverse {
                image = target.neg(&image);
            }
            assert_eq!(target.add(&image, &image).unwrap(), target.zero());
            values.push((ds[index].clone(), image));
            index += 1;
        }
    }
    assert_eq!(values.len(), 16);
    for a in &values {
        for c in &values {
            let sum = source.add(&a.0, &c.0).unwrap();
            let row = values.iter().find(|v| v.0 == sum).unwrap();
            assert_eq!(target.add(&a.1, &c.1).unwrap(), row.1);
        }
    }
    let mut images = vec![];
    for v in &values {
        if !images.contains(&v.1) {
            images.push(v.1.clone());
        }
    }
    assert_eq!(images.len(), 4);
    assert!(images
        .iter()
        .all(|d| values.iter().filter(|v| v.1 == *d).count() == 4));
    values
}

#[test]
fn composite_kills_all_geometric_two_and_retains_elliptic_embeddings() {
    let t = SevenTransfer::new();
    let b = Bridge::new();
    let action = two_action(&t, &b);
    let r0 =
        RichelotMap::from_assessment(crate::nonsplit::construct_for(101, [56, 13, 6]).unwrap())
            .unwrap();
    let r1 =
        RichelotMap::from_selected_pairing(transported_assessment(&t, &action), action.pairing)
            .unwrap();
    assert_eq!(r0.k.k.q, b.k.k.q);
    assert_eq!(r1.k.k.q, b.k.k.q);
    let roots0 = source_branch_roots(&b.k);
    let forward0 = richelot_two_action(&r0, &roots0, false);
    let forward1 = richelot_two_action(&r1, &action.roots, false);
    let reverse0 = richelot_two_action(&r0, &target_branch_roots(&b, &r0), true);
    let zero0 = Jacobian::new(&b.k, &r0.source).zero();
    let zero1 = Jacobian::new(&b.k, &r1.target).zero();
    let kernel0 = forward0
        .iter()
        .filter(|v| v.1 == Jacobian::new(&b.k, &r0.target).zero())
        .map(|v| v.0.clone())
        .collect::<Vec<_>>();
    let kernel1 = forward1
        .iter()
        .filter(|v| v.1 == zero1)
        .map(|v| v.0.clone())
        .collect::<Vec<_>>();
    assert_eq!((kernel0.len(), kernel1.len()), (4, 4));
    assert!(kernel0.contains(&zero0));
    for d in &kernel0 {
        assert_eq!(reverse0.iter().filter(|v| v.1 == *d).count(), 4);
        assert!(kernel1.contains(&action.mapping.iter().find(|v| v.0 == *d).unwrap().1));
    }
    for row in &reverse0 {
        let phi = &action.mapping.iter().find(|v| v.0 == row.1).unwrap().1;
        assert_eq!(forward1.iter().find(|v| v.0 == *phi).unwrap().1, zero1);
    }

    // Cross-kernels meet both embedded elliptic2-torsion groups trivially.
    // Combined with the old pull embeddings this preserves their isomorphism
    // types after R0/R1,needed for the unpolarized-Jacobian distinction.
    let source = Jacobian::new(&b.k, &r0.source);
    let target = Jacobian::new(&b.k, &r1.source);
    for component in 0..2 {
        let two = super::elliptic_two_points(&b, component);
        let map = lift_map(&b.f, &t.edges[component]);
        for point in two.iter().skip(1) {
            let mut product = [Pt::Inf; 2];
            product[component] = *point;
            let old =
                extension_product_pull(&source, &b.f, product, &old_charts(), 56, |a| b.embed(a))
                    .unwrap();
            assert!(!kernel0.contains(&old));
            product[component] = map.eval(&b.f, point);
            let new =
                extension_product_pull(&target, &b.f, product, &t.model.charts, 68, |a| b.embed(a))
                    .unwrap();
            assert!(!kernel1.contains(&new));
        }
    }
    println!("PASS actualR0/R1/dualR0 geometric16-class actions,all256 additions each,image4/four preimages,exact kernel transport,compositeR1 Phi R0Hat kills ALL16 T0[2] classes;all12 elliptic2-torsion intersection controls preserve embeddings;global regular quotient/degree/polarization/nonisomorphism argument remains written");
}

pub(super) struct SevenChain {
    t: SevenTransfer,
    r0: RichelotMap,
    r1: RichelotMap,
}
impl SevenChain {
    pub(super) fn new() -> Self {
        let t = SevenTransfer::new();
        let b = Bridge::new();
        let r0 =
            RichelotMap::from_assessment(crate::nonsplit::construct_for(101, [56, 13, 6]).unwrap())
                .unwrap();
        let r1 = super::transported_richelot(&t, &b);
        let coefficients = |r: &RichelotMap| {
            r.target
                .equation_and_infinity()
                .0
                .coeffs
                .iter()
                .map(|c| c.to_u64().unwrap())
                .collect::<Vec<_>>()
        };
        println!(
            "actual chain sourceT0{:?},targetT1{:?}",
            coefficients(&r0),
            coefficients(&r1)
        );
        assert_eq!(coefficients(&r0), [31, 75, 74, 54, 71, 55, 1]);
        assert_eq!(coefficients(&r1), [95, 26, 19, 27, 94, 91, 1]);
        Self { t, r0, r1 }
    }

    /// P1 alpha N0 /4 or its adjoint on the odd rational point groups.
    /// This moves the rational division into existing elliptic coordinates;
    /// it never labels an unknown point by its discrete logarithm.
    fn quarter_phi(&self, d: &Class, reverse: bool) -> super::super::super::Result<Class> {
        let f = &self.t.fp;
        let points = if reverse {
            self.t.target_coordinates(d)?
        } else {
            self.t.source_coordinates(d)?
        };
        let images: [Pt<u64>; 2] = std::array::from_fn(|i| {
            let e = &self.t.edges[i];
            let n = [109_u64, 113][i];
            let inverse_four = (3 * n + 1) / 4;
            assert_eq!(4 * inverse_four % n, 1);
            let curve = if reverse { &e.map.cod } else { &e.map.dom };
            assert_eq!(curve::pmul(f, curve, &points[i], u128::from(n)), Pt::Inf);
            let quarter = curve::pmul(f, curve, &points[i], u128::from(inverse_four));
            if reverse {
                e.reverse(f, &quarter)
            } else {
                e.map.eval(f, &quarter)
            }
        });
        if reverse {
            self.t.source.pulls(
                &long_point(f, &self.t.source.first.base, images[0], 2),
                &long_point(f, &self.t.source.second.base, images[1], 38),
            )
        } else {
            let bases = [&self.t.target.first.base, &self.t.target.second.base];
            let components: [MumfordDivisorP; 2] = std::array::from_fn(|i| {
                let c = self.t.model.charts[i];
                let internal = scale_point(f, images[c.destination], f.inv(c.scale));
                long_point(f, bases[i], internal, c.shift)
            });
            self.t.target.pulls(&components[0], &components[1])
        }
    }
    pub(super) fn forward(&self, d: &Class) -> super::super::super::Result<Class> {
        self.r1
            .forward_closed(&self.quarter_phi(&self.r0.dual_closed(d)?, false)?)
    }
    pub(super) fn dual(&self, d: &Class) -> super::super::super::Result<Class> {
        self.r0
            .forward_closed(&self.quarter_phi(&self.r1.dual_closed(d)?, true)?)
    }
    fn naive(&self, d: &Class, reverse: bool) -> super::super::super::Result<Class> {
        if reverse {
            let half = self.r1.target.mul(d, 6159)?;
            self.r0
                .forward(&self.t.dual_generic(&self.r1.dual(&half)?)?)
        } else {
            let half = self.r0.target.mul(d, 6159)?;
            self.r1
                .forward(&self.t.forward_generic(&self.r0.dual(&half)?)?)
        }
    }
}

#[test]
fn seven_chain_prime109_source_recovery_and_direct_coordinates() {
    let c = SevenChain::new();
    let base = &c.t.source.first.base;
    let g = MumfordDivisorP::try_from_point(base, &BigUint::from(0_u64), &BigUint::from(37_u64))
        .unwrap();
    let generator = c
        .forward(&c.r0.forward(&c.t.source.first.pull(&g).unwrap()).unwrap())
        .unwrap();
    assert_ne!(generator, c.r1.target.zero());
    assert_eq!(
        c.r1.target.mul(&generator, 109).unwrap(),
        c.r1.target.zero()
    );
    for n in 0..109_u64 {
        let point = g.checked_scalar_mul(&BigUint::from(n), base).unwrap();
        let old = c.t.source.first.pull(&point).unwrap();
        let start = c.r0.forward(&old).unwrap();
        let image = c.forward(&start).unwrap();
        assert_eq!(image, c.r1.target.mul(&generator, n).unwrap());
        assert_eq!(image, c.naive(&start, false).unwrap());
        assert_eq!(
            image,
            c.r1.forward(&c.t.forward(&old).unwrap()).unwrap(),
            "actual commuting square"
        );
        let reversed = c.dual(&image).unwrap();
        assert_eq!(reversed, c.naive(&image, true).unwrap());
        assert_eq!(reversed, c.r0.target.mul(&start, 7).unwrap());
        assert_eq!(c.r0.target.mul(&reversed, 78).unwrap(), start);
        let (a, b) = c.t.source.norms(&c.r0.dual(&reversed).unwrap()).unwrap();
        assert!(b.is_identity());
        assert_eq!(
            a,
            point
                .checked_scalar_mul(&BigUint::from(28_u64), base)
                .unwrap()
        );
        assert_eq!(
            a.checked_scalar_mul(&BigUint::from(74_u64), base).unwrap(),
            point
        );
        let p = super::super::short_point(&c.t.fp, base, &point, 2);
        let alpha = c.t.edges[0].map.eval(&c.t.fp, &p);
        assert_eq!(
            c.t.target_coordinates(&c.r1.dual(&image).unwrap()).unwrap(),
            [
                curve::pmul(&c.t.fp, &c.t.edges[0].map.cod, &alpha, 4),
                Pt::Inf
            ]
        );
    }
    println!("PASS genuine T0-to-T1 seven-chain,all109 originalsource scalars/nonzero image,both naive-halving/quarter-coordinate evaluators,commuting square,dual[7]/inverse78,fullreverse norm[28]/inverse74 andactual target([4]alpha1(P),0);no scalar labels or benchmark");
}

/// Evaluate each immutable map on EVERY input exactly once,then use its
/// complete graph for norms and paired sums. Lookups are test data only:
/// neither map evaluator has a scalar label or a corpus/table dependency.
pub(super) fn assert_full_graph_pair(
    source: &crate::balanced::Balanced,
    target: &crate::balanced::Balanced,
    forward: impl Fn(&Class) -> super::super::super::Result<Class>,
    dual: impl Fn(&Class) -> super::super::super::Result<Class>,
    norm: u64,
) {
    let xs = source.classes().unwrap();
    let ys = target.classes().unwrap();
    assert_eq!((xs.len(), ys.len()), (12317, 12317));
    let images = xs
        .iter()
        .enumerate()
        .map(|(i, d)| {
            let out = forward(d).unwrap_or_else(|e| panic!("full graph forward{i}: {e}"));
            target.check(&out).unwrap();
            out
        })
        .collect::<Vec<_>>();
    let duals = ys
        .iter()
        .enumerate()
        .map(|(i, d)| {
            let out = dual(d).unwrap_or_else(|e| panic!("full graph dual{i}: {e}"));
            source.check(&out).unwrap();
            out
        })
        .collect::<Vec<_>>();
    assert_eq!(
        images
            .iter()
            .map(super::super::class_key)
            .collect::<HashSet<_>>(),
        ys.iter().map(super::super::class_key).collect()
    );
    assert_eq!(
        duals
            .iter()
            .map(super::super::class_key)
            .collect::<HashSet<_>>(),
        xs.iter().map(super::super::class_key).collect()
    );
    let xi = xs
        .iter()
        .enumerate()
        .map(|(i, d)| (super::super::class_key(d), i))
        .collect::<HashMap<_, _>>();
    let yi = ys
        .iter()
        .enumerate()
        .map(|(i, d)| (super::super::class_key(d), i))
        .collect::<HashMap<_, _>>();
    assert_eq!((xi.len(), yi.len()), (12317, 12317));
    for i in 0..xs.len() {
        let j = (7919 * i + 37) % xs.len();
        assert_eq!(
            duals[yi[&super::super::class_key(&images[i])]],
            source.mul(&xs[i], norm).unwrap(),
            "full graph source dual{i}"
        );
        assert_eq!(
            images[xi[&super::super::class_key(&duals[i])]],
            target.mul(&ys[i], norm).unwrap(),
            "full graph target dual{i}"
        );
        assert_eq!(
            images[xi[&super::super::class_key(&source.add(&xs[i], &xs[j]).unwrap())]],
            target.add(&images[i], &images[j]).unwrap(),
            "full graph source addition{i}"
        );
        assert_eq!(
            duals[yi[&super::super::class_key(&target.add(&ys[i], &ys[j]).unwrap())]],
            source.add(&duals[i], &duals[j]).unwrap(),
            "full graph target addition{i}"
        );
    }
}

#[test]
fn seven_chain_both_full_rational_domains_duals_and_additions() {
    let c = SevenChain::new();
    assert_full_graph_pair(
        &c.r0.target,
        &c.r1.target,
        |d| c.forward(d),
        |d| c.dual(d),
        7,
    );
    assert!(c.forward(&c.r1.target.zero()).is_err());
    assert!(c.dual(&c.r0.target.zero()).is_err());
    println!("PASS genuinePsi BOTH complete12317-class rational domains,bothfull bijections,dual[7] inbothdirections,12317 deterministicpaired additions eachdirection,canonical coefficientwiseF101 descent andwrongcurve rejection;global quotient/polarization proof andcostcontrols remain separate");
}
