//! Complete actual intersection table and same-product collapse; protocola94132.
#![allow(dead_code, static_mut_refs)]
#[cfg(test)]
mod tests {
    use chained_n4_completed_v2::{AdapterV2, NormV2};
    use chained_n4_gluing_maps::{Adapter, NormNew};
    use chained_n4_gluing_models::{construct_all, er, three};
    use chained_n4_public_target::CheckedInstance;
    use chained_original_smith_engine::original;
    use isogeny_algos::field::Field;
    use serde_json::json;
    use std::collections::{BTreeMap, BTreeSet};
    fn vs(s: u64) -> Vec<u8> {
        (0..64).filter(|&i| s & (1u64 << i) != 0).collect()
    }
    fn pairing(a: u8, b: u8) -> u32 {
        ((((a & 0x15) << 1) | ((a & 0x2a) >> 1)) & b).count_ones() & 1
    }
    fn frob(x: u8) -> u8 {
        ((x << 2) & 63) | (x >> 4)
    }
    fn bits(v: &[u8]) -> u64 {
        v.iter().fold(0, |s, &v| s | (1u64 << v))
    }
    fn span(g: [u8; 3]) -> u64 {
        bits(
            &(0..8)
                .map(|v| {
                    g.iter().enumerate().fold(0, |out, (i, &b)| {
                        out ^ if v & (1 << i) != 0 { b } else { 0 }
                    })
                })
                .collect::<Vec<_>>(),
        )
    }
    fn dimension(s: u64) -> u32 {
        let count = s.count_ones();
        assert!(count.is_power_of_two());
        count.trailing_zeros()
    }
    fn audit(s: u64) {
        let v = vs(s);
        assert!(v.contains(&0));
        for &a in &v {
            for &b in &v {
                assert!(v.contains(&(a ^ b)));
                assert_eq!(pairing(a, b), 0);
            }
        }
    }
    fn original_all() -> BTreeSet<u64> {
        let basis = [3u8, 5, 15, 23, 63, 95];
        let mask = |v: u8| {
            basis
                .iter()
                .enumerate()
                .fold(0, |a, (i, &b)| a ^ if v & (1 << i) != 0 { b } else { 0 })
        };
        let mut inverse = [255; 128];
        for v in 0..64 {
            assert_eq!(inverse[mask(v) as usize], 255);
            inverse[mask(v) as usize] = v;
        }
        for a in 0..64 {
            for b in 0..64 {
                assert_eq!(pairing(a, b), (mask(a) & mask(b)).count_ones() & 1);
            }
        }
        let out: BTreeSet<_> = original::lagrangians()
            .iter()
            .map(|(v, _)| {
                let mut row = v
                    .iter()
                    .map(|&x| {
                        let y = inverse[x as usize];
                        assert!(y < 64);
                        y
                    })
                    .collect::<Vec<_>>();
                row.push(0);
                let s = bits(&row);
                assert_eq!(dimension(s), 3);
                audit(s);
                s
            })
            .collect();
        assert_eq!(out.len(), 135);
        out
    }
    #[test]
    fn all_intersections_geometric_kernel_types_and_actual_repeated_routes() {
        let c = CheckedInstance::construct().unwrap();
        let old = NormV2::new(AdapterV2::new(&c).unwrap()).unwrap();
        let (models, summary) = construct_all(&c, &old.a);
        let all = original_all();
        let from_models: BTreeSet<_> = summary["all135_kernels"]
            .as_array()
            .unwrap()
            .iter()
            .map(|r| r["mask"].as_u64().unwrap())
            .collect();
        assert_eq!(all, from_models);
        let gold = models
            .iter()
            .find(|m| (m.root_index, m.sign_index) == (1, 0))
            .unwrap();
        assert_eq!(gold.normalized, c.inst.f);
        let gold = gold.kernel_mask;
        let mut histogram = BTreeMap::new();
        let mut all_rows = vec![];
        for &g in &all {
            let i = g & gold;
            audit(i);
            let dim = dimension(i);
            *histogram.entry(dim).or_insert(0usize) += 1;
            all_rows.push(json!({"mask":g,"intersection":vs(i),"dimension":dim}));
        }
        let mut kernels = vec![];
        for q in 1..4 {
            kernels.push((format!("product-Q{q}"), span([q, q << 2, q << 4]), false));
        }
        for m in &models {
            kernels.push((
                format!("HLP-{}-{}", m.root_index, m.sign_index),
                m.kernel_mask,
                m.square_root.is_some(),
            ));
        }
        let stable: BTreeSet<_> = all
            .iter()
            .copied()
            .filter(|&s| vs(s).iter().all(|&v| s & (1u64 << frob(v)) != 0))
            .collect();
        assert_eq!(stable, kernels.iter().map(|r| r.1).collect());
        assert_eq!(stable.len(), 9);
        let roots: Vec<[u64; 3]> =
            serde_json::from_value(summary["actual_source_2torsion_roots"].clone()).unwrap();
        let actual = |v: u8| {
            std::array::from_fn::<_, 3, _>(|i| {
                let id = (v >> (2 * i)) & 3;
                if id == 0 {
                    None
                } else {
                    let mut x = er(roots[id as usize - 1]);
                    for _ in 0..i {
                        x = c.independent_field.frobenius(x);
                    }
                    Some(three(x))
                }
            })
        };
        let mut table = vec![];
        let mut types = vec![];
        for (name, g, eligible) in &kernels {
            for (other, h, _) in &kernels {
                let intersect = g & h;
                audit(intersect);
                assert_eq!(intersect, h & g);
                assert!(vs(intersect)
                    .iter()
                    .all(|&v| intersect & (1u64 << frob(v)) != 0));
                if g == h {
                    assert_eq!(dimension(intersect), 3);
                }
                table.push(json!({"first":name,"second":other,"whole_intersection":vs(intersect),"dimension":dimension(intersect),"actual_A2_triples":vs(intersect).into_iter().map(actual).collect::<Vec<_>>()}));
            }
            let d = dimension(g & gold);
            let a = 3 - d;
            let b = 2 * d;
            assert_eq!(2 * a + b, 6);
            assert_eq!(a + b, 3 + d);
            assert_eq!(4u64.pow(a) * 2u64.pow(b), 64);
            assert_eq!(2u64.pow(a + b), 8 * (g & gold).count_ones() as u64);
            types.push(json!({"kernel":name,"mask":g,"eligible_original_source_Jacobian":eligible,"intersection_dimension_with_Gold":d,"intersection_actual_A2_triples":vs(g&gold).into_iter().map(actual).collect::<Vec<_>>(),"geometric_kerF_C4_factors":a,"geometric_kerF_C2_factors":b,"geometric_kerF_order":64,"geometric_kerF_2torsion_order":2u64.pow(a+b),"free_rank3_over_Z4":d==0,"scope":"conditionalwrittenexact2torsionsequence/degree/exponent4/finiteabeliangroupclassification;notactualJ4divisorcoordinatesorrationalkernels"}));
        }
        println!(
            "N4_CHAIN_KERNEL_INTERSECTIONS {}",
            json!({"protocol":"a94132","all135_original_and_model_sets_equal":true,"all4096_pairings":true,"Gold_literal_original_mask":gold,"all135_intersections":all_rows,"actual_dimension_histogram":histogram,"predicted_histogram_match":histogram==BTreeMap::from([(0,64),(1,56),(2,14),(3,1)]),"all9x9_rational_intersections":table,"all81_closure_isotropy_Frobenius_symmetry_diagonal_controls":true})
        );
        println!(
            "N4_CHAIN_KERNEL_TYPES {}",
            json!({"all9_rational_cases":types,"characteristic":223,"written_geometric_degree_and_exponent":[64,4],"scope":"geometricgroupsnotrationalcofactors;etale/exactness/classificationbridgeswritten"})
        );
        let ns: Vec<_> = models
            .into_iter()
            .filter(|m| m.square_root.is_some())
            .map(|m| NormNew::new(Adapter::new(&c, &old.a, m).unwrap()).unwrap())
            .collect();
        assert_eq!(ns.len(), 4);
        let points = old.a.pic.rational_points_bruteforce();
        let inputs: Vec<_> = points
            .iter()
            .take(8)
            .map(|&p| {
                let x = old.a.pic.point_class(p);
                let q = old.norm(&x).unwrap();
                (p, x, q)
            })
            .collect();
        let mut collapse = vec![];
        for middle in &ns {
            for finaln in &ns {
                for (point, x, q) in &inputs {
                    let y = middle.a.transfer_point(q).unwrap();
                    let after = middle.norm(&y).unwrap();
                    let composed = finaln.a.transfer_point(&after).unwrap();
                    let direct = finaln.a.transfer_point(q).unwrap();
                    assert_eq!(composed, finaln.a.pic.double(&direct));
                    collapse.push(json!({"old_P":point,"old_class":x.key().0.to_vec(),"middle":middle.a.candidate,"final":finaln.a.candidate,"interior_class":y.key().0.to_vec(),"direct_class":direct.key().0.to_vec(),"repeated_class":composed.key().0.to_vec(),"repeated_equals_double_direct":true}));
                }
            }
        }
        assert_eq!(collapse.len(), 128);
        let mut cofactor = vec![old.a.pic.zero()];
        for &p in &points {
            let x = old
                .a
                .pic
                .mul_scalar(&old.a.pic.point_class(p), c.inst.ell as u128);
            if !cofactor.contains(&x) {
                cofactor.push(x);
            }
        }
        assert_eq!(cofactor.len(), 4);
        cofactor.sort_by_key(|x| x.key());
        let mut rational = vec![];
        for n in &ns {
            let images: Vec<_> = cofactor
                .iter()
                .map(|x| n.a.transfer_point(&old.norm(x).unwrap()).unwrap())
                .collect();
            let kernel: Vec<_> = images
                .iter()
                .enumerate()
                .filter_map(|(i, x)| n.a.pic.is_zero(x).then_some(i))
                .collect();
            assert_eq!(kernel.len(), 2);
            rational.push(json!({"candidate":n.a.candidate,"old_rational_cofactor":cofactor.iter().map(|x|x.key().0.to_vec()).collect::<Vec<_>>(),"actual_F_images":images.iter().map(|x|x.key().0.to_vec()).collect::<Vec<_>>(),"rational_kernel_indices":kernel,"geometric_order_is_not_rational_kernel_count":true}));
        }
        println!(
            "N4_CHAIN_COLLAPSE {}",
            json!({"all128_actual_repeated_routes":collapse,"actual_rational_cofactor_F_kernels":rational,"same_product_collapse":"F_CB F_Bold=[2]_C F_Cold;globalproofneedednotfittedscalar","all_four_interior_and_final_including_literal":true})
        );
        println!(
            "N4_CHAIN_KERNEL_SCOPE {}",
            json!({"native_one_unfiltered":true,"finite_intersections_and128_actual_map_equalities":true,"geometric_kernel_type":"writtenproof/exactness/abelianclassification;partialformalnext","actual_J4_kernel_basis_or_coordinates":false,"same_product_longer_paths":"reduce to direct transfer plus scalar;retained negative for extra route advantage","computational_advantage":"not established;originaladmission/counters/referencesopen","next":"different justified product or degree after fullpublication;preserveallcases"})
        );
    }
}
