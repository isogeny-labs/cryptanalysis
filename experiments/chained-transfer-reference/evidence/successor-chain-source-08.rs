//! Second transported Richelot quotient, using the accepted existing engines.
use super::{successor_two_action, Bridge, SevenSuccessor, SuccessorTwoAction};
use crate::balanced::Class;
use crate::nonsplit::map::RichelotMap;
use crate::nonsplit::{Assessment, CubicField};
use crate::reference::FpPoly;
use isogeny_algos::curve::{self, Isogeny, Pt};
use isogeny_algos::field::Field;
use num_bigint::BigUint;
use num_traits::ToPrimitive;

struct SuccessorChain {
    s: SevenSuccessor,
    r1: RichelotMap,
    r2: RichelotMap,
}

impl SuccessorChain {
    fn new() -> Self {
        let s = SevenSuccessor::new();
        let b = Bridge::new();
        let r1 = super::super::super::transported_richelot(&s.old, &b);
        let r2 = successor_richelot(&s, &b);
        Self { s, r1, r2 }
    }

    /// P2 beta N1 /4 or its adjoint. Only the known odd elliptic group
    /// orders are used for division; no point has a discrete-log label.
    fn quarter_phi(&self, d: &Class, reverse: bool) -> Result<Class, String> {
        let s = &self.s;
        let f = &s.old.fp;
        let coordinates = if reverse {
            s.target_coordinates(d)?
        } else {
            s.old.target_coordinates(d)?
        };
        let actual = std::array::from_fn(|i| {
            let e = &s.beta[i];
            let n = [109_u64, 113][i];
            let inverse_four = (3 * n + 1) / 4;
            assert_eq!(4 * inverse_four % n, 1);
            let base = if reverse { &e.map.cod } else { &e.map.dom };
            assert_eq!(
                curve::pmul(f, base, &coordinates[i], u128::from(n)),
                Pt::Inf
            );
            let quarter = curve::pmul(f, base, &coordinates[i], u128::from(inverse_four));
            if reverse {
                e.reverse(f, &quarter)
            } else {
                e.map.eval(f, &quarter)
            }
        });
        if reverse {
            SevenSuccessor::pulls(f, &s.old.target, s.old.model.charts, actual)
        } else {
            SevenSuccessor::pulls(f, &s.target, s.charts, actual)
        }
    }

    fn forward(&self, d: &Class) -> Result<Class, String> {
        self.r2
            .forward_closed(&self.quarter_phi(&self.r1.dual_closed(d)?, false)?)
    }

    fn dual(&self, d: &Class) -> Result<Class, String> {
        self.r1
            .forward_closed(&self.quarter_phi(&self.r2.dual_closed(d)?, true)?)
    }

    fn naive(&self, d: &Class, reverse: bool) -> Result<Class, String> {
        if reverse {
            let half = self.r2.target.mul(d, 6159)?;
            self.r1.forward(&self.s.dual(&self.r2.dual(&half)?)?)
        } else {
            let half = self.r1.target.mul(d, 6159)?;
            self.r2.forward(&self.s.forward(&self.r1.dual(&half)?)?)
        }
    }
}

#[test]
fn successor_chain_both_source_components_two_hop_and_direct_recovery() {
    let c = SuccessorChain::new();
    let first = super::super::super::chain::SevenChain::new();
    let s = &c.s;
    let f = &s.old.fp;
    let r0 =
        RichelotMap::from_assessment(crate::nonsplit::construct_for(101, [56, 13, 6]).unwrap())
            .unwrap();
    for component in 0..2 {
        let n = [109_u64, 113][component];
        let base = &s.old.edges[component].map.dom;
        let generator = super::super::super::super::points(f, base)[1];
        let mut product = [Pt::Inf; 2];
        product[component] = generator;
        let start_generator = r0.forward(&s.original_pull(product).unwrap()).unwrap();
        let first_generator = first.forward(&start_generator).unwrap();
        let end_generator = c.forward(&first_generator).unwrap();
        assert_ne!(end_generator, c.r2.target.zero());
        assert_eq!(
            c.r2.target.mul(&end_generator, n).unwrap(),
            c.r2.target.zero()
        );
        let inverse196 = (1..n).find(|k| 196 * k % n == 1).unwrap();
        for k in 0..n {
            let p = curve::pmul(f, base, &generator, u128::from(k));
            product[component] = p;
            let original = s.original_pull(product).unwrap();
            let start = r0.forward(&original).unwrap();
            let middle = first.forward(&start).unwrap();
            let end = c.forward(&middle).unwrap();
            assert_eq!(end, c.r2.target.mul(&end_generator, k).unwrap());
            assert_eq!(end, c.naive(&middle, false).unwrap());
            assert_eq!(
                end,
                c.r2.forward(&s.forward(&s.old.forward(&original).unwrap()).unwrap())
                    .unwrap(),
                "two actual global commuting squares"
            );
            let reversed = c.dual(&end).unwrap();
            assert_eq!(reversed, c.naive(&end, true).unwrap());
            assert_eq!(reversed, c.r1.target.mul(&middle, 7).unwrap());
            let full_reverse = first.dual(&reversed).unwrap();
            assert_eq!(full_reverse, r0.target.mul(&start, 49).unwrap());
            let recovered_norm = s
                .old
                .source_coordinates_generic(&r0.dual(&full_reverse).unwrap())
                .unwrap();
            assert_eq!(recovered_norm[component], curve::pmul(f, base, &p, 196));
            assert_eq!(recovered_norm[1 - component], Pt::Inf);
            assert_eq!(
                curve::pmul(f, base, &recovered_norm[component], u128::from(inverse196)),
                p
            );
            let alpha = s.old.edges[component].map.eval(f, &p);
            let beta_alpha = s.beta[component].map.eval(f, &alpha);
            let mut expected = [Pt::Inf; 2];
            expected[component] = curve::pmul(f, &s.beta[component].map.cod, &beta_alpha, 4);
            assert_eq!(
                s.target_coordinates(&c.r2.dual(&end).unwrap()).unwrap(),
                expected
            );
        }
        println!("PASS Psi2 composed with accepted Psi1,ALL{n} original source scalars,nonzero order,naive/quarter in BOTH directions,commuting squares,dual7/composite49,fullreverse norm196/inverse{inverse196},actual target4 beta alpha component{component}");
    }
}

#[test]
fn successor_chain_both_full_domains_duals_and_additions() {
    let c = SuccessorChain::new();
    super::super::super::chain::assert_full_graph_pair(
        &c.r1.target,
        &c.r2.target,
        |d| c.forward(d),
        |d| c.dual(d),
        7,
    );
    assert!(c.forward(&c.r2.target.zero()).is_err());
    assert!(c.dual(&c.r1.target.zero()).is_err());
    println!("PASS actual Psi2 T1/T2 BOTH complete12317-class domains,dual7,bijections,all deterministic paired additions,coefficientwise descent and wrong-model rejection;global regular factor remains separately written");
}

#[test]
fn successor_chain_complete_geometric_two_kernel_and_embeddings() {
    use super::super::super::chain::{richelot_two_action, target_branch_roots};
    use super::{
        elliptic_two_points, extension_product_pull, frobenius_class, lift_map, two_action,
        Jacobian,
    };
    let c = SuccessorChain::new();
    let b = Bridge::new();
    let previous = two_action(&c.s.old, &b);
    let action = successor_two_action(&c.s, &b);
    let roots1 = target_branch_roots(&b, &c.r1);
    let roots2 = target_branch_roots(&b, &c.r2);
    let forward1 = richelot_two_action(&c.r1, &previous.roots, false);
    let forward2 = richelot_two_action(&c.r2, &action.roots, false);
    let reverse1 = richelot_two_action(&c.r1, &roots1, true);
    let reverse2 = richelot_two_action(&c.r2, &roots2, true);
    let j1 = Jacobian::new(&b.k, &c.r1.source);
    let j2 = Jacobian::new(&b.k, &c.r2.source);
    let t1 = Jacobian::new(&b.k, &c.r1.target);
    let t2 = Jacobian::new(&b.k, &c.r2.target);
    for row in &reverse1 {
        let image = &action.mapping.iter().find(|v| v.0 == row.1).unwrap().1;
        assert_eq!(
            forward2.iter().find(|v| v.0 == *image).unwrap().1,
            t2.zero()
        );
    }
    for row in &reverse2 {
        let image = &action.mapping.iter().find(|v| v.1 == row.1).unwrap().0;
        assert_eq!(
            forward1.iter().find(|v| v.0 == *image).unwrap().1,
            t1.zero()
        );
    }
    for table in [&forward1, &forward2, &reverse1, &reverse2] {
        assert_eq!(table.len(), 16);
        for row in table {
            let conjugate = frobenius_class(&b.k, &row.0, 1);
            let found = table.iter().find(|v| v.0 == conjugate).unwrap();
            assert_eq!(found.1, frobenius_class(&b.k, &row.1, 1));
        }
    }
    let alpha = c.s.old.edges.each_ref().map(|e| lift_map(&b.f, e));
    let beta = c.s.beta.each_ref().map(|e| lift_map(&b.f, e));
    let mut intersections = 0;
    for component in 0..2 {
        for p in elliptic_two_points(&b, component).iter().skip(1) {
            let mut product1 = [Pt::Inf; 2];
            product1[component] = alpha[component].eval(&b.f, p);
            let d1 = extension_product_pull(&j1, &b.f, product1, &c.s.old.model.charts, 68, |v| {
                b.embed(v)
            })
            .unwrap();
            assert_ne!(d1, j1.zero());
            assert_ne!(forward1.iter().find(|v| v.0 == d1).unwrap().1, t1.zero());
            let mut product2 = [Pt::Inf; 2];
            product2[component] = beta[component].eval(&b.f, &product1[component]);
            let d2 = extension_product_pull(&j2, &b.f, product2, &c.s.charts, 19, |v| b.embed(v))
                .unwrap();
            assert_ne!(d2, j2.zero());
            assert_ne!(forward2.iter().find(|v| v.0 == d2).unwrap().1, t2.zero());
            intersections += 2;
        }
    }
    assert_eq!(intersections, 12);
    println!("PASS actual R1/R2 forward/dual ALL16 geometric two-classes,all256 additions/Frobenius each;R2 Phi2 R1Hat and adjoint kill ALL16,all12 nonzero elliptic2 intersection controls retain embeddings. This certifies finite etale kernel inclusion;global regular quotient/degree/polarization/descent use the separate written proof.");
}

fn successor_assessment(s: &SevenSuccessor, action: &SuccessorTwoAction) -> Assessment {
    let field = CubicField::with_cubic(101, [56, 13, 6]).unwrap();
    let roots = action
        .roots
        .iter()
        .map(|r| {
            assert!(r.b.is_zero());
            r.a.clone()
        })
        .collect::<Vec<_>>();
    let permutation = std::array::from_fn(|i| {
        roots
            .iter()
            .position(|r| *r == field.pow(&roots[i], 101))
            .unwrap()
    });
    let pairs = crate::nonsplit::pairings()
        .into_iter()
        .filter(|p| crate::nonsplit::stable(p, &permutation))
        .collect::<Vec<_>>();
    assert_eq!(pairs.len(), 3);
    let source = s
        .target
        .first
        .balanced
        .equation_and_infinity()
        .0
        .coeffs
        .iter()
        .map(|c| c.to_u64().unwrap())
        .collect::<Vec<_>>();
    let mut targets = vec![];
    let mut degenerate = 0;
    for pair in &pairs {
        let g = pair.map(|(i, j)| {
            vec![
                field.mul(&roots[i], &roots[j]),
                roots[i].add(&roots[j]).neg(),
                field.c(1),
            ]
        });
        assert_eq!(
            field.product(&g),
            source.iter().map(|c| field.c(*c)).collect::<Vec<_>>()
        );
        let delta = field.determinant(&g);
        if delta.is_zero() {
            degenerate += 1;
            continue;
        }
        let h = field.dual_factors(&g, &delta);
        let product = field.product(&h);
        assert!(product.iter().all(|c| c.degree().is_none_or(|d| d == 0)));
        let raw = product.iter().map(|c| field.base(c)).collect::<Vec<_>>();
        assert_eq!(raw.len(), 7);
        let f = FpPoly::from_coeffs(
            raw.iter().copied().map(BigUint::from).collect(),
            BigUint::from(101_u64),
        );
        let df = FpPoly::from_coeffs(
            (1..7)
                .map(|i| f.coeff(i) * BigUint::from(i as u64) % &f.p)
                .collect(),
            f.p.clone(),
        );
        assert_eq!(f.gcd(&df), FpPoly::one(f.p.clone()));
        println!(
            "C2 stable pairing{pair:?},delta{},raw target{raw:?}",
            field.base(&delta)
        );
        targets.push(raw);
    }
    assert_eq!((targets.len(), degenerate), (2, 1));
    assert!(targets.contains(&action.raw_target));
    Assessment {
        field,
        roots,
        pairs,
        source,
        targets,
        degenerate,
    }
}

fn successor_richelot(s: &SevenSuccessor, b: &Bridge) -> RichelotMap {
    let action = successor_two_action(s, b);
    let r = RichelotMap::from_selected_pairing(successor_assessment(s, &action), action.pairing)
        .expect("actual transported R2 kernel must pass the existing chart checks");
    let normalized = r
        .target
        .equation_and_infinity()
        .0
        .coeffs
        .iter()
        .map(|c| c.to_u64().unwrap())
        .collect::<Vec<_>>();
    println!(
        "ACTUAL R2 target scale{},normalized T2{normalized:?}",
        r.target_scale
    );
    assert_eq!(r.target_scale, 50);
    assert_eq!(normalized, [95, 93, 43, 39, 92, 17, 1]);
    assert_eq!(
        r.source.equation_and_infinity(),
        s.target.first.balanced.equation_and_infinity()
    );
    r
}

#[test]
fn successor_richelot_both_full_domains_closed_reference_and_controls() {
    use std::cell::RefCell;
    let s = SevenSuccessor::new();
    let b = Bridge::new();
    let r = successor_richelot(&s, &b);
    let counts = RefCell::new([[0_usize; 5]; 2]);
    let evaluate = |d: &Class, reverse: bool| {
        let (image, route) = r.evaluate_closed(d, reverse)?;
        assert_eq!(
            image,
            r.evaluate(d, reverse)?,
            "R2 closed/pointwise reverse={reverse}"
        );
        counts.borrow_mut()[usize::from(reverse)][route as usize] += 1;
        Ok(image)
    };
    super::super::super::chain::assert_full_graph_pair(
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
    println!("PASS R2 BOTH complete12317 C2/T2 domains,closed/pointwise exact equality,both dual2,bijections,paired additions,descent,wrong-model rejection;route counts{:?}", counts.borrow());
}
