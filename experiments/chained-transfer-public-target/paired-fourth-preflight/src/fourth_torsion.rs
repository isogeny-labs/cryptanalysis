pub fn audit_fourth_square(
    original: &crate::FourthBranch,
    twisted: &crate::FourthBranch,
    source_rescaling: &Value,
    original_transport: &Value,
    twisted_transport: &Value,
) -> Value {
    let f = original.field();
    let original_g4 = original_transport["actual_transported_mask"]
        .as_u64()
        .unwrap();
    let twisted_g4 = twisted_transport["actual_transported_mask"]
        .as_u64()
        .unwrap();
    let (rescaled_g4, target_rescaling) =
        rescale_endpoint(f, original.target(), twisted.target(), original_g4);
    assert_eq!(rescaled_g4, twisted_g4);
    let r3: [u8; 4] =
        serde_json::from_value(source_rescaling["actual_2torsion_permutation"].clone()).unwrap();
    let r4: [u8; 4] =
        serde_json::from_value(target_rescaling["actual_2torsion_permutation"].clone()).unwrap();
    let o: [u8; 4] =
        serde_json::from_value(original_transport["actual_basis_permutation"].clone()).unwrap();
    let t: [u8; 4] =
        serde_json::from_value(twisted_transport["actual_basis_permutation"].clone()).unwrap();
    let os = torsion(f, original.source());
    let ot = torsion(f, original.target());
    let ts = torsion(f, twisted.source());
    let tt = torsion(f, twisted.target());
    let v = f.from_u64(12);
    let scale = |p: Pt<ER>| match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => {
            assert!(f.is_zero(y));
            Pt::Aff(f.mul(v, x), f.zero())
        }
    };
    let mut points = vec![];
    for a in 0..64u8 {
        let old_image = encoded(&o, a);
        let new_source = encoded(&r3, a);
        let new_image = encoded(&t, new_source);
        let rescaled_image = encoded(&r4, old_image);
        assert_eq!(new_image, rescaled_image);
        let source = tuple(f, &os, a);
        let scaled_source = tuple(f, &ts, new_source);
        let image = tuple(f, &ot, old_image);
        let scaled_image = tuple(f, &tt, new_image);
        assert_eq!(source.map(scale), scaled_source);
        assert_eq!(image.map(scale), scaled_image);
        // Each edge/conjugate map was independently evaluated on all coordinates
        // by the unchanged full audit_edge4 algorithm before this comparison.
        assert_eq!(
            original_transport["all64_actual_coordinate_transports"][a as usize]
                ["image_actual_coordinates"],
            tuple_json(image)
        );
        assert_eq!(
            twisted_transport["all64_actual_coordinate_transports"][new_source as usize]
                ["image_actual_coordinates"],
            tuple_json(scaled_image)
        );
        points.push(json!({"original_source_index":a,"original_source":tuple_json(source),"twisted_source_index":new_source,"twisted_source":tuple_json(scaled_source),"original_image_index":old_image,"original_image":tuple_json(image),"twisted_image_index":new_image,"twisted_image":tuple_json(scaled_image),"rescaled_original_image_index":rescaled_image,"actual_square_commutes":true}));
    }
    let mask_image = |perm: &[u8; 4], g: u64| {
        bits(
            &vs(g)
                .into_iter()
                .map(|a| encoded(perm, a))
                .collect::<Vec<_>>(),
        )
    };
    let mut masks = vec![];
    for g in original_all() {
        let upper = mask_image(&r4, mask_image(&o, g));
        let lower = mask_image(&t, mask_image(&r3, g));
        assert_eq!(upper, lower);
        masks.push(
            json!({"original_source_mask":g,"upper_then_rescale":upper,"rescale_then_lower":lower}),
        );
    }
    json!({"all64_actual_coordinate_commuting_rows":points,"all135_actual_mask_commuting_rows":masks,"complete_E4_rescaling":target_rescaling,"fixed_original_G4":original_g4,"fixed_twisted_G4":twisted_g4,"rescaled_original_G4":rescaled_g4,"all_masks_fixed_before_E4_models":true,"scope":"actual coordinate commutation and original alternating form; no new Miller pairing or Jacobian evaluator"})
}
