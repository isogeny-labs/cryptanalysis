mod fixed_pair_tests {
    use super::*;
    fn torsion(f: &FpR, ec: &Curve<ER>) -> Vec<Pt<ER>> {
        let mut roots = poly::roots(f, &cubic(f, ec), &mut Rng::new(0x1222));
        roots.sort();
        roots.dedup();
        assert_eq!(roots.len(), 3);
        std::iter::once(Pt::Inf)
            .chain(roots.into_iter().map(|x| Pt::Aff(x, f.zero())))
            .collect()
    }
    fn point_panels(pair: &TwistedPair) -> Value {
        let f = pair.field();
        let t2 = torsion(f, pair.source());
        let t3 = torsion(f, pair.target());
        let mut source = vec![];
        for k in [1, 3, 5, 7, 17, 31, 101, pair.ell - 2] {
            let p = curve::pmul(f, pair.source(), &pair.generator, k as u128);
            for t in &t2 {
                source.push(curve::padd(f, pair.source(), &p, t));
            }
        }
        source.extend(&t2);
        assert_eq!(source.len(), 36);
        let mut targets = vec![Pt::Inf];
        let mut rng = Rng::new(0x121336);
        for _ in 0..31 {
            targets.push(curve::random_point_f(f, pair.target(), &mut rng));
        }
        targets.extend(&t3);
        assert_eq!(targets.len(), 36);
        let sr = source
            .iter()
            .map(|&p| {
                let q = pair.forward(p);
                let back = pair.dual(q);
                assert_eq!(back, curve::pmul(f, pair.source(), &p, 13));
                json!({"source":point(p),"image":point(q),"dual_image":point(back)})
            })
            .collect::<Vec<_>>();
        let tr = targets
            .iter()
            .map(|&p| {
                let q = pair.dual(p);
                let back = pair.forward(q);
                assert_eq!(back, curve::pmul(f, pair.target(), &p, 13));
                json!({"target":point(p),"dual_image":point(q),"forward_image":point(back)})
            })
            .collect::<Vec<_>>();
        let mut pairs = vec![];
        for i in 0..32 {
            for j in 0..32 {
                let s = curve::padd(f, pair.source(), &source[i], &source[j]);
                let qs = pair.forward(s);
                assert_eq!(
                    qs,
                    curve::padd(
                        f,
                        pair.target(),
                        &pair.forward(source[i]),
                        &pair.forward(source[j])
                    )
                );
                let t = curve::padd(f, pair.target(), &targets[i], &targets[j]);
                let qt = pair.dual(t);
                assert_eq!(
                    qt,
                    curve::padd(
                        f,
                        pair.source(),
                        &pair.dual(targets[i]),
                        &pair.dual(targets[j])
                    )
                );
                pairs.push(json!({"i":i,"j":j,"actual_source_sum":point(s),"actual_forward_sum":point(qs),"actual_target_sum":point(t),"actual_dual_sum":point(qt)}));
            }
        }
        let torsion = t2
            .iter()
            .map(|&p| {
                let q = pair.forward(p);
                assert!(t3.contains(&q));
                assert_eq!(pair.dual(q), p);
                json!({"source":point(p),"target":point(q)})
            })
            .collect::<Vec<_>>();
        let public=[1,2,17,12345,pair.ell-1].into_iter().map(|k|{let q=curve::pmul(f,pair.source(),&pair.generator,k as u128);let image=pair.forward(q);assert_eq!(image,curve::pmul(f,pair.target(),&pair.target_generator,k as u128));assert_eq!(pair.dual(image),curve::pmul(f,pair.source(),&q,13));assert!(curve::on_curve(f,pair.source(),&q));json!({"known_test_scalar":k,"public_source":point(q),"actual_image":point(image),"actual_dual_image":point(pair.dual(image)),"original_source_arithmetic_check":true})}).collect::<Vec<_>>();
        json!({"all36_source":sr,"all36_target":tr,"all1024_addition_pairs_each_way":pairs,"all4_actual2torsion_images":torsion,"all5_new_instance_public_targets":public,"scope":"known-scalar correctness tests for the new twist instance, not solves or an original-logarithm transfer"})
    }
    fn old_matches() -> (Value, Value) {
        let second: Value =
            serde_json::from_str(include_str!("../generated/old-second-model.json")).unwrap();
        let third: Value =
            serde_json::from_str(include_str!("../generated/old-third-model.json")).unwrap();
        let third = third
            .as_array()
            .unwrap()
            .iter()
            .filter(|x| x["kind"] == "N4_NEXT13_MATCHED_MODELS")
            .collect::<Vec<_>>();
        assert_eq!(third.len(), 1);
        (
            second["N4_NONDUAL13_MATCHED_MODELS"].clone(),
            third[0]["data"].clone(),
        )
    }
    fn check_models(
        f: &FpR,
        all: &[models::GluingModel],
        old: &Value,
        gold: u64,
        name: &str,
    ) -> Value {
        let old_rows = old[format!("all6_{name}_model_rows")].as_array().unwrap();
        assert_eq!(old_rows.len(), 6);
        assert_eq!(all.len(), 6);
        let v = f.from_u64(12);
        let v2 = f.pow(v, 2);
        let v3 = f.pow(v, 3);
        let mut parity = vec![];
        for m in all {
            let candidates = old_rows
                .iter()
                .filter(|r| {
                    let root: [u64; 3] =
                        serde_json::from_value(r["original_root"].clone()).unwrap();
                    let h: Vec<[u64; 3]> = serde_json::from_value(r["h"].clone()).unwrap();
                    f.mul(v, er(root)) == m.root && f.mul(v, er(h[0])) == m.h[0]
                })
                .collect::<Vec<_>>();
            assert_eq!(candidates.len(), 1);
            let o = candidates[0];
            for (key, new, scale) in [
                ("original_A", m.source_a, v),
                ("original_B", m.source_b, v2),
                ("h", m.h, v),
                ("d", m.d, v),
            ] {
                let before: Vec<[u64; 3]> = serde_json::from_value(o[key].clone()).unwrap();
                assert_eq!(before.len(), 3);
                for i in 0..3 {
                    assert_eq!(f.mul(scale, er(before[i])), new[i]);
                }
            }
            let delta: Vec<[u64; 3]> = serde_json::from_value(o["Delta"].clone()).unwrap();
            for i in 0..3 {
                assert_eq!(
                    f.mul(v2, er(delta[i])),
                    f.sub(
                        f.mul(m.source_a[i], m.source_a[i]),
                        f.mul(f.from_u64(4), m.source_b[i])
                    )
                );
            }
            for (key, new, scale) in [("H", m.h_matrix, v), ("Q", m.q_matrix, v2)] {
                let before: [[[u64; 3]; 3]; 3] = serde_json::from_value(o[key].clone()).unwrap();
                for i in 0..3 {
                    for j in 0..3 {
                        assert_eq!(f.mul(scale, er(before[i][j])), new[i][j]);
                    }
                }
            }
            let old_d: [u64; 3] = serde_json::from_value(o["D"].clone()).unwrap();
            assert_eq!(f.mul(v3, er(old_d)), m.factor);
            let old_det: [u64; 3] = serde_json::from_value(o["T_equals_detH"].clone()).unwrap();
            assert_eq!(f.mul(v3, er(old_det)), m.determinant);
            assert_eq!(
                serde_json::to_value(m.normalized).unwrap(),
                o["normalized_Fp_coefficients"]
            );
            parity.push(json!({"whole_old_model_row":o,"whole_new_model_row":m.row,"actual_root_sign_correspondence":[m.root_index,m.sign_index],"all_original_A_B_Delta_h_d_H_Q_T_D_scalings_exact":true,"whole_normalized_coefficients_exact":true}));
        }
        let chosen = all
            .iter()
            .filter(|m| m.kernel_mask == gold)
            .collect::<Vec<_>>();
        assert_eq!(chosen.len(), 1);
        let m = chosen[0];
        assert_eq!(
            old["whole_matched_row"]["eligible_for_supplied_source_maps"],
            false
        );
        assert_eq!(
            serde_json::to_value(m.normalized).unwrap(),
            old["whole_matched_row"]["normalized_Fp_coefficients"]
        );
        let eligible = m.row["eligible_for_supplied_source_maps"]
            .as_bool()
            .unwrap();
        json!({"endpoint":name,"all6_homogeneity_and_whole_coefficient_parity":parity,"fixed_mask_before_model_builder":gold,"unique_matched_row":m.row,"supported_fixed_new_source":eligible,"old_complete_matched_record":old,"scope":"supported HLP source/model preflight only; geometric quotient uses primary theorem, complete rational Jacobian evaluator not implemented"})
    }
    #[test]
    fn all_fixed_twisted_pair_checks() {
        let c = CheckedInstance::construct().unwrap();
        let pair = TwistedPair::construct(&c);
        let f = pair.field();
        println!("N4_TWIST_MAPS_AND_CERTIFICATES {}", pair.certificate);
        println!("N4_TWIST_POINTS {}", point_panels(&pair));
        let (old2, old3) = old_matches();
        assert_eq!(old2["fixed_transported_mask"], 1155175778390933505u64);
        assert_eq!(old3["fixed_transported_mask"], 9511681577844867105u64);
        let (g2, g3, _transport) = twisted_torsion::audit_twist(&pair);
        let basis = chained_n4_completed_v2::AdapterV2::new(&c).unwrap();
        let source = models::SourceE::fixed_twisted(
            &c,
            *pair.source(),
            pair.ell,
            pair.order,
            pair.generator,
            pair.certificate["source_id"].as_str().unwrap(),
        );
        let target = models::SourceE::fixed_twisted(
            &c,
            *pair.target(),
            pair.ell,
            pair.order,
            pair.target_generator,
            pair.certificate["target_id"].as_str().unwrap(),
        );
        let (all2, summary2) = models::construct_all(&source, &basis);
        let (all3, summary3) = models::construct_all(&target, &basis);
        println!(
            "N4_TWIST_ALL_MODELS {}",
            json!({"source":source.identity(),"target":target.identity(),"all6_source_rows":all2.iter().map(|m|m.row.clone()).collect::<Vec<_>>(),"all6_target_rows":all3.iter().map(|m|m.row.clone()).collect::<Vec<_>>(),"whole_source_summary":summary2,"whole_target_summary":summary3,"fixed_G2":g2,"fixed_G3":g3,"all12_retained_before_acceptance":true})
        );
        let a = check_models(f, &all2, &old2, g2, "E2");
        let b = check_models(f, &all3, &old3, g3, "E3");
        println!(
            "N4_TWIST_MATCHED_PAIR {}",
            json!({"source":a,"target":b,"new_instance":true,"original_D12_D24_negatives_preserved":true,"no_old_logarithm_transport_to_twist":true,"complete_Jacobian_evaluator":"not implemented"})
        );
        assert!(a["supported_fixed_new_source"].as_bool().unwrap() && b["supported_fixed_new_source"].as_bool().unwrap(),"fixed twisted pair has an unsupported endpoint; retain every outcome without reselection");
    }
}
