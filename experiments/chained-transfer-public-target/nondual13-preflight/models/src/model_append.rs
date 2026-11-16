#[cfg(test)]
mod second_model_tests {
    use super::*;
    use chained_n4_nondual13_preflight::SecondHop;
    use chained_n4_odd_source::OddSourceIsogeny;
    use chained_n4_public_target::CheckedInstance;
    fn rows(models: &[GluingModel]) -> Vec<Value> {
        models.iter().map(|m| m.row.clone()).collect()
    }
    #[test]
    fn all_actual_torsion_transport_then_matched_prime_field_model() {
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
            "N4_NONDUAL13_MODEL_PARITY {}",
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
            "N4_NONDUAL13_CURRENT_J1 {}",
            json!({"actual_original_norm_model_tag":actual_j1.model_tag,"actual_original_field_tag":actual_j1.field_tag,"actual_original_source_curve":src1.identity(),"actual_kernel_mask":actual_j1_kernel,"same_as_literal_HLP10_mask":gold==actual_j1_kernel,"constructed_by_unchanged_original_adapter_norm":true})
        );
        let hop = SecondHop::construct(&c);
        assert_eq!(hop.source(), src1.curve());
        let transport = transported::audit_second(&hop, gold);
        let wanted = transport["actual_transported_mask"].as_u64().unwrap();
        println!(
            "N4_NONDUAL13_MODEL_SELECTION {}",
            json!({"fixed_transported_mask_before_model_builder":wanted,"literal_current_J1_model":"Ciani-Jac-odd-product-v1-7ea9d0f9d1a48a48489425beab48274fca7bd0848e47a0bac3a027c01601e2c4","uses_only_kernel_transport":true,"E2_square_or_smooth_outcome":"not yet constructed or read"})
        );
        println!("N4_NONDUAL13_PRODUCT_TRANSPORT {}", transport);
        let src2 = SourceE::second_actual(&c, &hop);
        assert_eq!(src2.curve(), hop.target());
        let (models, summary) = construct_all(&src2, &basis);
        let actual_all: BTreeSet<_> = summary["all135_kernels"]
            .as_array()
            .unwrap()
            .iter()
            .map(|r| r["mask"].as_u64().unwrap())
            .collect();
        let independent: BTreeSet<_> = transport["all135_independent_original_masks"]
            .as_array()
            .unwrap()
            .iter()
            .map(|r| r.as_u64().unwrap())
            .collect();
        assert_eq!(actual_all, independent);
        assert_eq!(actual_all.len(), 135);
        let selected: Vec<_> = models.iter().filter(|m| m.kernel_mask == wanted).collect();
        assert_eq!(
            selected.len(),
            1,
            "match actual transported mask before admissibility"
        );
        let selected = selected[0];
        let eligible = selected.row["eligible_for_supplied_source_maps"]
            .as_bool()
            .unwrap();
        if eligible {
            assert!(selected.p0.is_some());
            assert!(selected.square_root.is_some());
            assert_eq!(selected.row["smooth"], true);
        }
        println!(
            "N4_NONDUAL13_MATCHED_MODELS {}",
            json!({"E2_source_identity":src2.identity(),"all6_E2_model_rows":rows(&models),"all135_and_rational_kernel_summary":summary,"fixed_transported_mask":wanted,"matched_case":[selected.root_index,selected.sign_index],"whole_matched_row":selected.row,"matched_eligible_prime_field_model":eligible,"outcome":if eligible{"supported F223 model; complete second Jacobian maps not implemented"}else{"matched model unsupported; original endpoint requirement remains open; no retwist or reselection"},"selection":"exact pre-fixed mask only; square/smoothness read after unique match; all six outcomes retained","scope":"actual torsion and model preflight only, not a complete second Jacobian map or cost advantage"})
        );
    }
}
