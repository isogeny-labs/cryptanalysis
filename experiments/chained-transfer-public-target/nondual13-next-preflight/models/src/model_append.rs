#[cfg(test)]
mod third_model_tests {
    use super::*;
    use chained_n4_nondual13_preflight::SecondHop;
    use chained_n4_odd_source::OddSourceIsogeny;
    use chained_n4_public_target::CheckedInstance;
    fn rows(models: &[GluingModel]) -> Vec<Value> {
        models.iter().map(|m| m.row.clone()).collect()
    }
    #[test]
    fn all_same_kernel_third_transport_then_matched_prime_field_model() {
        let c = CheckedInstance::construct().unwrap();
        let basis = AdapterV2::new(&c).unwrap();
        let src0 = SourceE::original(&c);
        let ext0 = chained_n4_odd_product_models::SourceE::original(&c);
        assert_eq!(src0.identity(), ext0.identity());
        let (ours0, summary0) = construct_all(&src0, &basis);
        let (theirs0, extsum0) = chained_n4_odd_product_models::construct_all(&ext0, &basis);
        assert_eq!(summary0, extsum0);
        assert_eq!(
            rows(&ours0),
            theirs0.iter().map(|m| m.row.clone()).collect::<Vec<_>>()
        );
        let first = OddSourceIsogeny::construct(&c);
        let src1 = SourceE::degree13_target(&c, &first);
        let ext1 = chained_n4_odd_product_models::SourceE::degree13_target(&c, &first);
        assert_eq!(src1.identity(), ext1.identity());
        let (ours1, summary1) = construct_all(&src1, &basis);
        let (theirs1, extsum1) = chained_n4_odd_product_models::construct_all(&ext1, &basis);
        assert_eq!(summary1, extsum1);
        assert_eq!(
            rows(&ours1),
            theirs1.iter().map(|m| m.row.clone()).collect::<Vec<_>>()
        );
        println!(
            "N4_NEXT13_MODEL_PARITY {}",
            json!({"original_E0_identity":src0.identity(),"original_E1_identity":src1.identity(),"all6_original_E0_rows":rows(&ours0),"all6_original_E1_rows":rows(&ours1),"E0_whole_original_summary":summary0,"E1_whole_original_summary":summary1,"both_whole_panels_exact":true,"masks":[]})
        );
        // Validate the literal current J1 identity with its unchanged original
        // adapter/norm constructors, rather than trusting the HLP label alone.
        let actual_j1_model = theirs1
            .into_iter()
            .find(|m| (m.root_index, m.sign_index) == (1, 0))
            .unwrap();
        let actual_j1_kernel = actual_j1_model.kernel_mask;
        let actual_j1 = chained_n4_odd_product_maps::NormNew::new(
            chained_n4_odd_product_maps::Adapter::new(&ext1, &basis, actual_j1_model).unwrap(),
        )
        .unwrap();
        assert_eq!(actual_j1.model_tag,"Ciani-Jac-odd-product-v1-7ea9d0f9d1a48a48489425beab48274fca7bd0848e47a0bac3a027c01601e2c4");
        assert_eq!(actual_j1.a.source_ec, *src1.curve());
        let gold = ours1
            .iter()
            .find(|m| (m.root_index, m.sign_index) == (1, 0))
            .unwrap()
            .kernel_mask;
        assert_eq!(gold, actual_j1_kernel);
        println!(
            "N4_NEXT13_CURRENT_J1 {}",
            json!({"actual_original_norm_model_tag":actual_j1.model_tag,"actual_original_field_tag":actual_j1.field_tag,"actual_original_source_curve":src1.identity(),"actual_kernel_mask":actual_j1_kernel,"same_as_literal_HLP10_mask":gold==actual_j1_kernel,"constructed_by_unchanged_original_adapter_norm":true})
        );
        let old_hop = SecondHop::construct(&c);
        let hop = chained_n4_nondual13_next_preflight::ThirdHop::construct(&c);
        assert_eq!(old_hop.certificate, hop.previous().certificate);
        assert_eq!(old_hop.target(), hop.source());
        let src2 = SourceE::second_actual(&c, &old_hop);
        let ext2 = chained_n4_nondual13_model_preflight::SourceE::second_actual(&c, &old_hop);
        let (models2, summary2) = construct_all(&src2, &basis);
        let (extmodels2, extsummary2) =
            chained_n4_nondual13_model_preflight::construct_all(&ext2, &basis);
        assert_eq!(src2.identity(), ext2.identity());
        assert_eq!(summary2, extsummary2);
        assert_eq!(
            rows(&models2),
            extmodels2.iter().map(|m| m.row.clone()).collect::<Vec<_>>()
        );
        let old_transport = transported::audit_second(&old_hop, gold);
        let g2 = old_transport["actual_transported_mask"].as_u64().unwrap();
        assert_eq!(g2, 1155175778390933505);
        let matched2: Vec<_> = models2.iter().filter(|m| m.kernel_mask == g2).collect();
        assert_eq!(matched2.len(), 1);
        assert_eq!((matched2[0].root_index, matched2[0].sign_index), (2, 1));
        assert_eq!(matched2[0].row["D"], json!([12, 0, 0]));
        assert_eq!(matched2[0].row["smooth"], true);
        assert_eq!(matched2[0].row["eligible_for_supplied_source_maps"], false);
        println!(
            "N4_NEXT13_INTERMEDIATE_NEGATIVE {}",
            json!({"E2_source_identity":src2.identity(),"all6_E2_model_rows":rows(&models2),"whole_original_E2_summary":summary2,"whole_prior_actual_transport":old_transport,"whole_prior_matched_row":matched2[0].row,"actual_G2":g2,"both_E2_panels_exact":true,"previous_constructor_certificates_exact":true,"outcome":"original23ab48 supplied-source endpoint remains unsupported; no retwist or reselection"})
        );
        let transport = transported::audit_third(&hop, g2);
        let wanted = transport["actual_transported_mask"].as_u64().unwrap();
        let src3 = SourceE::third_actual(&c, &hop);
        // Nothing about square-D or smoothness is read before this mask is fixed.
        println!(
            "N4_NEXT13_MODEL_SELECTION {}",
            json!({"fixed_transported_mask_before_model_builder":wanted,"actual_G2_before_third_edge":g2,"source_E3":src3.identity(),"selection":"same full transported kernel only; no admissibility filtering"})
        );
        let (models3, summary3) = construct_all(&src3, &basis);
        let all: BTreeSet<_> = summary3["all135_kernels"]
            .as_array()
            .unwrap()
            .iter()
            .map(|x| x["mask"].as_u64().unwrap())
            .collect();
        let independent: BTreeSet<_> = transport["all135_independent_original_masks"]
            .as_array()
            .unwrap()
            .iter()
            .map(|x| x.as_u64().unwrap())
            .collect();
        assert_eq!(all, independent);
        let selected: Vec<_> = models3.iter().filter(|m| m.kernel_mask == wanted).collect();
        assert_eq!(selected.len(), 1);
        let selected = selected[0];
        let eligible = selected.row["eligible_for_supplied_source_maps"]
            .as_bool()
            .unwrap();
        if eligible {
            assert!(selected.p0.is_some());
            assert!(selected.square_root.is_some());
            assert_eq!(selected.row["smooth"], true);
        }
        println!("N4_NEXT13_PRODUCT_TRANSPORT {}", transport);
        println!(
            "N4_NEXT13_MATCHED_MODELS {}",
            json!({"E3_source_identity":src3.identity(),"all6_E3_model_rows":rows(&models3),"all135_and_rational_kernel_summary":summary3,"fixed_transported_mask":wanted,"matched_case":[selected.root_index,selected.sign_index],"whole_matched_row":selected.row,"matched_eligible_prime_field_model":eligible,"outcome":if eligible{"supported F223 model after one fixed additional edge; complete second Jacobian maps not implemented"}else{"matched model unsupported; new endpoint requirement remains open; no retwist or reselection"},"scope":"third elliptic/product/model preflight; no full2197 rational expansion, complete Jacobian transfer or computational advantage"})
        );
    }
}
