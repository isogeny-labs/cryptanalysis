//! Fixed-case structural scout,c3b30d before code. No odd-subgroup DLP table.
#![allow(dead_code, static_mut_refs)]

#[cfg(test)]
mod tests {
    use chained_n4_completed_v2::{AdapterV2, NormV2, Point};
    use chained_n4_public_target::{ghs::EP, CheckedInstance};
    use isogeny_algos::{
        curve::{self, Pt},
        field::{Field, Rng},
        fpr::ER,
        poly,
    };
    use serde_json::json;

    fn er(a: [u64; 3]) -> ER {
        let mut x = [0; 16];
        x[..3].copy_from_slice(&a);
        x
    }
    fn ep(p: Point) -> Pt<ER> {
        match p {
            None => Pt::Inf,
            Some((x, y)) => Pt::Aff(er(x), er(y)),
        }
    }
    fn kp(p: Pt<ER>) -> Point {
        match p {
            Pt::Inf => None,
            Pt::Aff(x, y) => {
                assert!(x[3..].iter().chain(y[3..].iter()).all(|&x| x == 0));
                Some(([x[0], x[1], x[2]], [y[0], y[1], y[2]]))
            }
        }
    }

    #[test]
    fn actual_four_element_cofactor_group_and_both_map_kernels() {
        let c = CheckedInstance::construct().unwrap();
        let n = NormV2::new(AdapterV2::new(&c).unwrap()).unwrap();
        let p = &n.a.pic;
        let f = &c.independent_field;
        let ec = &c.independent_curve;
        let roots = poly::roots(
            f,
            &vec![ec.b, ec.a, f.zero(), f.one()],
            &mut Rng::new(0x5901),
        );
        assert_eq!(roots.len(), 3);
        let mut source = vec![None];
        for x in roots {
            let t = Pt::Aff(x, f.zero());
            assert!(curve::on_curve(f, ec, &t));
            assert_eq!(curve::pmul(f, ec, &t, 2), Pt::Inf);
            source.push(kp(t));
        }
        source.sort();
        source.dedup();
        assert_eq!(source.len(), 4);
        let phi: Vec<_> = source
            .iter()
            .map(|x| n.a.transfer_point(x).unwrap())
            .collect();
        let mut group = vec![p.zero()];
        let add_generator = |group: &mut Vec<_>, generator: &_| loop {
            let old = group.clone();
            for x in &old {
                let y = p.add(x, generator);
                if !group.contains(&y) {
                    group.push(y);
                }
            }
            assert!(
                group.len() <= 4,
                "cofactor subgroup exceeded written4ell bound"
            );
            if group.len() == old.len() {
                break;
            }
        };
        for x in &phi {
            assert!(p.is_zero(&p.double(x)));
            add_generator(&mut group, x);
        }
        let points = p.rational_points_bruteforce();
        assert_eq!(points.len(), 224);
        let mut rows = Vec::new();
        for &point in &points {
            let class = p.point_class(point);
            let projected = p.mul_scalar(&class, c.inst.ell as u128);
            assert!(p.is_zero(&p.mul_scalar(&projected, 4)));
            assert!(p.is_zero(&p.mul_scalar(&class, c.inst.order)));
            add_generator(&mut group, &projected);
            rows.push(json!({"P":point,"class":class.key().0.to_vec(),"ell_projection":projected.key().0.to_vec()}));
        }
        group.sort_by_key(|x| x.key());
        println!(
            "N4_TWO_PRIMARY_PANEL {}",
            json!({"q":223,"ell":c.inst.ell,"written_J_order":c.inst.order,"actual_rational_C_points":points.len(),"generated_cofactor_classes":group.len(),"all224_projection_rows":rows,"scope":"orderbound from standardwrittenCianiisogeny,notannihilatoralone;cofactor4 table,notoddDLPlookup"})
        );
        assert_eq!(
            group.len(),
            4,
            "bounded rational-point/Phi pool didnot establish full2Sylow"
        );
        let index = |x: &_| group.iter().position(|y| x == y).unwrap();
        let identity = index(&p.zero());
        let mut table = vec![];
        let mut inverses = vec![];
        let mut orders = vec![];
        for x in &group {
            assert!(p.is_zero(&p.mul_scalar(x, 4)));
            inverses.push(index(&p.neg(x)));
            orders.push((1..=4).find(|&i| p.is_zero(&p.mul_scalar(x, i))).unwrap());
            table.push(
                group
                    .iter()
                    .map(|y| index(&p.add(x, y)))
                    .collect::<Vec<_>>(),
            );
            for y in &group {
                for z in &group {
                    assert_eq!(p.add(&p.add(x, y), z), p.add(x, &p.add(y, z)));
                }
            }
        }
        let kind = if orders.contains(&4) { "C4" } else { "C2xC2" };
        let norm: Vec<_> = group.iter().map(|x| n.norm(x).unwrap()).collect();
        for (i, x) in group.iter().enumerate() {
            assert!(curve::on_curve(f, ec, &ep(norm[i])));
            assert_eq!(curve::pmul(f, ec, &ep(norm[i]), 4), Pt::Inf);
            assert_eq!(n.a.transfer_point(&norm[i]).unwrap(), p.double(x));
            for (j, y) in group.iter().enumerate() {
                assert_eq!(
                    n.norm(&p.add(x, y)).unwrap(),
                    kp(curve::padd(f, ec, &ep(norm[i]), &ep(norm[j])))
                );
            }
        }
        let mut source_table = vec![];
        for (i, &x) in source.iter().enumerate() {
            assert_eq!(n.norm(&phi[i]).unwrap(), kp(curve::pmul(f, ec, &ep(x), 2)));
            let mut row = vec![];
            for (j, &y) in source.iter().enumerate() {
                let sum = kp(curve::padd(f, ec, &ep(x), &ep(y)));
                let k = source.iter().position(|&p| p == sum).unwrap();
                assert_eq!(phi[k], p.add(&phi[i], &phi[j]));
                row.push(k);
            }
            source_table.push(row);
        }
        let phi_kernel: Vec<_> = phi
            .iter()
            .enumerate()
            .filter_map(|(i, x)| p.is_zero(x).then_some(i))
            .collect();
        let norm_kernel: Vec<_> = norm
            .iter()
            .enumerate()
            .filter_map(|(i, x)| x.is_none().then_some(i))
            .collect();
        let mut phi_images = phi.iter().map(index).collect::<Vec<_>>();
        phi_images.sort();
        phi_images.dedup();
        let mut norm_images = norm.clone();
        norm_images.sort();
        norm_images.dedup();
        assert_eq!(phi_kernel.len() * phi_images.len(), 4);
        assert_eq!(norm_kernel.len() * norm_images.len(), 4);
        assert_eq!(
            phi_kernel.len(),
            norm_kernel.len(),
            "dualpolarized2kernels shouldhaveequalrationalcardinality"
        );
        let old_g = match c.inst.g {
            EP::Inf => panic!("nonzeroG"),
            EP::A(x, y) => Some((c.inst.kf.add(&x, &c.short_shift), c.inst.kf.neg(&y))),
        };
        let h = n.a.transfer_point(&old_g).unwrap();
        assert!(!p.is_zero(&h));
        assert!(p.is_zero(&p.mul_scalar(&h, c.inst.ell as u128)));
        assert!(!group.contains(&h));
        assert_eq!(n.norm(&h).unwrap(), kp(curve::pmul(f, ec, &ep(old_g), 2)));
        println!(
            "N4_TWO_PRIMARY_GROUP {}",
            json!({"Jacobian_cofactor_type":kind,"identity_index":identity,"class_keys":group.iter().map(|x|x.key().0.to_vec()).collect::<Vec<_>>(),"exact_orders":orders,"all16addition_table":table,"inverses":inverses,"associativity_triples":64,"odd_generator_key":h.key().0.to_vec(),"odd_generator_exact_prime_order":c.inst.ell})
        );
        println!(
            "N4_TWO_PRIMARY_MAPS {}",
            json!({"source_cofactor_type":"C2xC2","source_points":source,"source_all16addition_table":source_table,"Phi_source_indices_to_Jac_indices":phi.iter().map(index).collect::<Vec<_>>(),"Norm_Jac_indices_to_source_points":norm,"Phi_kernel_source_indices":phi_kernel,"Norm_kernel_Jac_indices":norm_kernel,"Phi_distinct_images":phi_images.len(),"Norm_distinct_images":norm_images.len(),"all16homomorphism_pairs_each":true,"both2compositions_allfour_each":true,"no_assumed_kernel2":true,"no_geometric2torsion_Frobeniusbasis_or_nondualmap_claim":true})
        );
        let q3 = 223i128.pow(3);
        let trace = q3 + 1 - c.inst.order as i128;
        let polynomial = vec![q3, 0, 0, -trace, 0, 0, 1];
        let mod2: Vec<_> = polynomial.iter().map(|c| c.rem_euclid(2)).collect();
        assert_eq!(mod2, vec![1, 0, 0, 0, 0, 0, 1]);
        println!(
            "N4_TWO_PRIMARY_FROBENIUS_SCOPE {}",
            json!({"E_K_trace":trace,"J_Weil_polynomial_low_to_high":polynomial,"mod2_low_to_high":mod2,"written_consequence":"CayleyHamilton makesFrob^6 identityon geometricJ[2];actualgeometricbasis/actionmatrix NOTcomputed","scope":"polynomialfromstandardwrittenCianiResisogeny;notindependentCq2/q3enumeration oractualstablekernelcensus"})
        );
    }
}
