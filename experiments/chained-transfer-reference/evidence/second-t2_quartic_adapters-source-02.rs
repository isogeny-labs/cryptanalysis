//! Actual accepted T2 finite-algebra norm/pullback acceptance,without interpolation.
use super::SuccessorChain;
use crate::nonsplit::map::seven_glue::torsion::chain::{
    quartic_norm::DirectQuartic,
    quartic_pullback::{rational_points, Pullback},
};
use isogeny_algos::curve::{self, Pt};
use isogeny_algos::field::Field;
use num_traits::ToPrimitive;
use std::collections::HashMap;

#[test]
fn both_t2_direct_pullbacks_match_old_r2_p2_and_all_group_pairs() {
    let c = SuccessorChain::new();
    let f = &c.s.old.fp;
    let mut pairs = 0;
    for component in 0..2 {
        let direct = Pullback::fixed(2, component);
        let e = &c.s.beta[component].map.cod;
        let points = rational_points(f, e);
        assert_eq!(points.len(), [109, 113][component]);
        let mut images = Vec::new();
        let mut degrees = [0_usize; 5];
        for &p in &points {
            let (image, (degree, plus)) = direct.pull(&p).unwrap();
            let mut product = [Pt::Inf; 2];
            product[component] = p;
            let old = super::SevenSuccessor::pulls(f, &c.s.target, c.s.charts, product).unwrap();
            assert_eq!(image, c.r2.forward_closed(&old).unwrap());
            assert!(!images.contains(&image));
            let mut expected = [Pt::Inf; 2];
            expected[component] = curve::pmul(f, e, &p, 4);
            assert_eq!(
                c.s.target_coordinates(&c.r2.dual_closed(&image).unwrap())
                    .unwrap(),
                expected
            );
            let q = [Pt::Aff(97, 63), Pt::Aff(64, 35)][component];
            if p == q {
                assert_eq!(degree, [2, 3][component]);
                assert_eq!(plus, [1, 0][component]);
            } else if p == curve::neg(f, &q) {
                assert_eq!(degree, [2, 3][component]);
                assert_eq!(plus, -1);
            } else if p != Pt::Inf {
                assert_eq!((degree, plus), (4, -1));
            }
            degrees[degree] += 1;
            images.push(image);
        }
        assert_eq!(
            degrees,
            if component == 0 {
                [1, 0, 2, 0, 106]
            } else {
                [1, 0, 0, 2, 110]
            }
        );
        let indices: HashMap<_, _> = points.iter().enumerate().map(|(i, p)| (*p, i)).collect();
        for (i, p) in points.iter().enumerate() {
            for (j, q) in points.iter().enumerate() {
                let sum = curve::padd(f, e, p, q);
                assert_eq!(
                    images[indices[&sum]],
                    c.r2.target.add(&images[i], &images[j]).unwrap()
                );
                pairs += 1;
            }
        }
        assert!(direct.pull(&Pt::Aff(0, 0)).is_err());
        println!("PASS directT2 pull component{component}:all{} exact oldR2P2 outputs/injective/norm4/offdiag0/all ordered group sums/signed infinity degrees{degrees:?}/offcurve;existing finite-algebra reducer only",points.len());
    }
    assert_eq!(pairs, 24650);
}

#[test]
fn both_t2_direct_norms_match_all_old_h2_outputs_and_group_controls() {
    let c = SuccessorChain::new();
    let f = &c.s.old.fp;
    let all = c.r2.target.classes().unwrap();
    assert_eq!(all.len(), 12317);
    for component in 0..2 {
        let direct = DirectQuartic::t2(component);
        let e = &c.s.beta[component].map.cod;
        let mut counts = [0_usize; 7];
        let mut linear_poles = 0;
        let mut repeated = 0;
        let mut images = Vec::with_capacity(all.len());
        for (i, d) in all.iter().enumerate() {
            let (image, route) = direct.norm(d).unwrap();
            assert_eq!(
                image,
                c.s.target_coordinates(&c.r2.dual_closed(d).unwrap())
                    .unwrap()[component],
                "T2norm{component}/class{i}"
            );
            counts[route] += 1;
            let (u, _, _) = d.components();
            if u.degree() == Some(1) {
                let x = f.neg(u.coeffs[0].to_u64().unwrap());
                if f.add(f.sq(x), [55, 23][component]) == 0 {
                    linear_poles += 1;
                }
            } else if u.degree() == Some(2) {
                let a = u.coeffs[1].to_u64().unwrap();
                let b = u.coeffs[0].to_u64().unwrap();
                if f.sq(a) == f.mul(4, b) {
                    repeated += 1;
                }
            }
            images.push(image);
        }
        assert_eq!(counts[0], 3);
        assert_eq!(counts[1], 236);
        assert_eq!(counts[2], [0, 2][component]);
        assert_eq!(counts[3], [0, 232][component]);
        assert_eq!(linear_poles, [0, 4][component]);
        assert_eq!(repeated, 118);
        assert!(counts[4] > 0 && counts[5] > 0);
        for (i, d) in all.iter().enumerate() {
            let j = (37 * i + 7) % all.len();
            assert_eq!(
                direct
                    .norm(&c.r2.target.add(d, &all[j]).unwrap())
                    .unwrap()
                    .0,
                curve::padd(f, e, &images[i], &images[j])
            );
            assert_eq!(
                direct.norm(&c.r2.target.neg(d).unwrap()).unwrap().0,
                curve::neg(f, &images[i])
            );
        }
        assert_eq!(direct.norm(&c.r2.target.zero()).unwrap().0, Pt::Inf);
        assert_eq!(
            direct.norm(&c.r2.target.delta()).unwrap().0,
            curve::pmul(f, e, &[Pt::Aff(97, 63), Pt::Aff(64, 35)][component], 2)
        );
        assert!(direct.norm(&c.r1.target.zero()).is_err());
        println!("PASS directT2 norm component{component}:all12317 exact oldH2 outputs/negations/paired sums/identity/infinities/wrongmodel;routes{counts:?},linear_poles{linear_poles},repeated{repeated};degree4 pole orbit creates no degree<=2 rational pole support in first component;existing arithmetic only,no timing claim");
    }
}
