fn fourth_torsion_points(f: &FpR, ec: &Curve<ER>) -> Vec<Pt<ER>> {
    let mut roots = poly::roots(f, &cubic(f, ec), &mut Rng::new(0x4f13));
    roots.sort();
    roots.dedup();
    assert_eq!(roots.len(), 3);
    std::iter::once(Pt::Inf)
        .chain(roots.into_iter().map(|x| Pt::Aff(x, f.zero())))
        .collect()
}
fn fourth_point_panel(branch: &FourthBranch, seed: u64) -> Value {
    let f = branch.field();
    let dom = branch.source();
    let cod = branch.target();
    let source_torsion = fourth_torsion_points(f, dom);
    let target_torsion = fourth_torsion_points(f, cod);
    let mut source = vec![];
    for k in [1, 3, 5, 7, 17, 31, 101, branch.ell - 2] {
        let p = curve::pmul(f, dom, &branch.generator, k as u128);
        for t in &source_torsion {
            source.push(curve::padd(f, dom, &p, t));
        }
    }
    source.extend(&source_torsion);
    assert_eq!(source.len(), 36);
    let mut rng = Rng::new(seed);
    let mut target = vec![Pt::Inf];
    for _ in 0..31 {
        target.push(curve::random_point_f(f, cod, &mut rng));
    }
    target.extend(&target_torsion);
    assert_eq!(target.len(), 36);
    let left = source
        .iter()
        .map(|&p| {
            let q = branch.forward(p).unwrap();
            let back = branch.dual(q).unwrap();
            assert_eq!(back, curve::pmul(f, dom, &p, 13));
            json!({"source":point(p),"image":point(q),"dual_image":point(back)})
        })
        .collect::<Vec<_>>();
    let right = target
        .iter()
        .map(|&p| {
            let q = branch.dual(p).unwrap();
            let back = branch.forward(q).unwrap();
            assert_eq!(back, curve::pmul(f, cod, &p, 13));
            json!({"target":point(p),"dual_image":point(q),"forward_image":point(back)})
        })
        .collect::<Vec<_>>();
    let mut sums = vec![];
    for i in 0..32 {
        for j in 0..32 {
            let s = curve::padd(f, dom, &source[i], &source[j]);
            let image = branch.forward(s).unwrap();
            assert_eq!(
                image,
                curve::padd(
                    f,
                    cod,
                    &branch.forward(source[i]).unwrap(),
                    &branch.forward(source[j]).unwrap()
                )
            );
            let t = curve::padd(f, cod, &target[i], &target[j]);
            let reverse = branch.dual(t).unwrap();
            assert_eq!(
                reverse,
                curve::padd(
                    f,
                    dom,
                    &branch.dual(target[i]).unwrap(),
                    &branch.dual(target[j]).unwrap()
                )
            );
            sums.push(json!({"i":i,"j":j,"actual_source_sum":point(s),"actual_forward_sum":point(image),"actual_target_sum":point(t),"actual_dual_sum":point(reverse)}));
        }
    }
    let torsion = source_torsion
        .into_iter()
        .map(|p| {
            let q = branch.forward(p).unwrap();
            assert!(target_torsion.contains(&q));
            assert_eq!(branch.dual(q).unwrap(), p);
            json!({"source":point(p),"target":point(q)})
        })
        .collect::<Vec<_>>();
    json!({"all36_source":left,"all36_target":right,"all1024_additions_each_direction":sums,"all4_torsion_images":torsion})
}
fn fourth_public(c: &CheckedInstance, hop: &PairedFourth) -> Value {
    let f = hop.pair.field();
    let original = hop.branch(false);
    let twisted = hop.branch(true);
    let g0 = match c.inst.g {
        EP::Inf => panic!("nonzero original generator"),
        EP::A(x, y) => Pt::Aff(f.add(er(x), er(c.short_shift)), er(y)),
    };
    let first = &hop.pair.old.previous.first;
    let mut old = vec![];
    for k in [1, 2, 17, 12345, c.inst.ell - 1] {
        let p0 = curve::pmul(f, first.source(), &g0, k as u128);
        let ep = match p0 {
            Pt::Inf => EP::Inf,
            Pt::Aff(x, y) => EP::A(three(f.sub(x, er(c.short_shift))), three(y)),
        };
        assert!(c.verify_recovered(ep, k));
        let p1 = first.forward(p0).unwrap();
        let p2 = hop.pair.old.previous.forward(p1).unwrap();
        let p3 = hop.pair.old.forward(p2).unwrap();
        assert_eq!(
            p3,
            curve::pmul(f, original.source(), &original.generator, k as u128)
        );
        let p4 = original.forward(p3).unwrap();
        assert_eq!(
            p4,
            curve::pmul(
                f,
                original.target(),
                &hop.original_target_generator,
                k as u128
            )
        );
        let d3 = original.dual(p4).unwrap();
        let d2 = hop.pair.old.dual(d3).unwrap();
        let d1 = hop.pair.old.previous.dual(d2).unwrap();
        let d0 = first.dual(d1).unwrap();
        assert_eq!(d1, curve::pmul(f, first.target(), &p1, 13u128.pow(3)));
        assert_eq!(d0, curve::pmul(f, first.source(), &p0, 13u128.pow(4)));
        old.push(json!({"known_scalar":k,"actual_E0":point(p0),"actual_E1":point(p1),"actual_E2":point(p2),"actual_E3":point(p3),"actual_E4":point(p4),"actual_reverse3_to_E1":point(d1),"actual_reverse4_to_E0":point(d0),"independent_original_source_check":true,"sequential_norms":[2197,28561],"whole_composite_rational_expansion":false}));
    }
    let mut new = vec![];
    for k in [1, 2, 17, 12345, hop.pair.ell - 1] {
        let p2 = curve::pmul(f, hop.pair.source(), &hop.pair.generator, k as u128);
        let p3 = hop.pair.forward(p2);
        let p4 = twisted.forward(p3).unwrap();
        assert_eq!(
            p3,
            curve::pmul(f, twisted.source(), &twisted.generator, k as u128)
        );
        assert_eq!(
            p4,
            curve::pmul(f, twisted.target(), &hop.twist_target_generator, k as u128)
        );
        let d3 = twisted.dual(p4).unwrap();
        let d2 = hop.pair.dual(d3);
        assert_eq!(d2, curve::pmul(f, hop.pair.source(), &p2, 169));
        new.push(json!({"known_scalar":k,"actual_E2nu":point(p2),"actual_E3nu":point(p3),"actual_E4nu":point(p4),"actual_reverse2_to_E2nu":point(d2),"separate_new_instance":true}));
    }
    json!({"all5_original_public_controls":old,"all5_separate_instance_public_controls":new,"scope":"known-scalar correctness controls, not solves or an old-logarithm map to a twist"})
}
fn fourth_homogeneity(
    f: &FpR,
    original: &[models::GluingModel],
    twisted: &[models::GluingModel],
) -> Value {
    assert_eq!(original.len(), 6);
    assert_eq!(twisted.len(), 6);
    let v = f.from_u64(12);
    let v2 = f.pow(v, 2);
    let v3 = f.pow(v, 3);
    let mut rows = vec![];
    for new in twisted {
        let matches = original
            .iter()
            .filter(|old| f.mul(v, old.root) == new.root && f.mul(v, old.h[0]) == new.h[0])
            .collect::<Vec<_>>();
        assert_eq!(matches.len(), 1);
        let old = matches[0];
        for (a, b, scale) in [
            (old.source_a, new.source_a, v),
            (old.source_b, new.source_b, v2),
            (old.h, new.h, v),
            (old.d, new.d, v),
        ] {
            for i in 0..3 {
                assert_eq!(f.mul(scale, a[i]), b[i]);
            }
        }
        for i in 0..3 {
            let old_delta = f.sub(
                f.mul(old.source_a[i], old.source_a[i]),
                f.mul(f.from_u64(4), old.source_b[i]),
            );
            let new_delta = f.sub(
                f.mul(new.source_a[i], new.source_a[i]),
                f.mul(f.from_u64(4), new.source_b[i]),
            );
            assert_eq!(f.mul(v2, old_delta), new_delta);
            for j in 0..3 {
                assert_eq!(f.mul(v, old.h_matrix[i][j]), new.h_matrix[i][j]);
                assert_eq!(f.mul(v2, old.q_matrix[i][j]), new.q_matrix[i][j]);
            }
        }
        assert_eq!(f.mul(v3, old.factor), new.factor);
        assert_eq!(f.mul(v3, old.determinant), new.determinant);
        assert_eq!(old.normalized, new.normalized);
        rows.push(json!({"whole_original_row":old.row,"whole_twisted_row":new.row,"original_case":[old.root_index,old.sign_index],"twisted_case":[new.root_index,new.sign_index],"all_A_B_Delta_h_d_H_Q_T_D_scalings_exact":true,"whole_normalized_quartic_equal":true}));
    }
    json!(rows)
}
fn collect_old_arrays(value: &Value, path: String, out: &mut Vec<(String, Value)>) {
    match value {
        Value::Object(map) => {
            for (key, child) in map {
                let p = format!("{path}/{key}");
                if key == "normalized_Fp_coefficients" {
                    out.push((p.clone(), child.clone()));
                }
                collect_old_arrays(child, p, out);
            }
        }
        Value::Array(rows) => {
            for (i, child) in rows.iter().enumerate() {
                collect_old_arrays(child, format!("{path}/{i}"), out);
            }
        }
        _ => {}
    }
}
pub fn run_paired_fourth(
    c: &CheckedInstance,
    pair: &TwistedPair,
    previous_twist_models: &[models::GluingModel],
    twisted_g3: u64,
    old_transport: &Value,
) {
    assert_eq!(twisted_g3, 1155177839943778305);
    assert_eq!(
        previous_twist_models
            .iter()
            .filter(|m| m.kernel_mask == twisted_g3)
            .count(),
        1
    );
    let hop = PairedFourth::construct(c, pair);
    let f = pair.field();
    println!("N4_FOURTH_MAPS {}", hop.certificate);
    let original = hop.branch(false);
    let twisted = hop.branch(true);
    println!(
        "N4_FOURTH_POINT_PANELS {}",
        json!({"original":fourth_point_panel(&original,0x4041),"separate_twist":fourth_point_panel(&twisted,0x4042)})
    );
    println!("N4_FOURTH_PUBLIC {}", fourth_public(c, &hop));
    let original_transport = twisted_torsion::audit_edge4(&original, 9511681577844867105);
    let twisted_transport = twisted_torsion::audit_edge4(&twisted, twisted_g3);
    let original_g4 = original_transport["actual_transported_mask"]
        .as_u64()
        .unwrap();
    let twisted_g4 = twisted_transport["actual_transported_mask"]
        .as_u64()
        .unwrap();
    let square = twisted_torsion::audit_fourth_square(
        &original,
        &twisted,
        &old_transport["target_rescaling"],
        &original_transport,
        &twisted_transport,
    );
    println!(
        "N4_FOURTH_FIXED_KERNELS {}",
        json!({"all_original_transport":original_transport,"all_twisted_transport":twisted_transport,"whole_commuting_square":square,"original_G4_fixed_BEFORE_models":original_g4,"twisted_G4_fixed_BEFORE_models":twisted_g4})
    );
    let basis = chained_n4_completed_v2::AdapterV2::new(c).unwrap();
    let old_source = models::SourceE::paired_source(
        c,
        *original.target(),
        c.inst.ell,
        c.inst.order,
        hop.original_target_generator,
        hop.certificate["original_target_id"].as_str().unwrap(),
    );
    let new_source = models::SourceE::paired_source(
        c,
        *twisted.target(),
        pair.ell,
        pair.order,
        hop.twist_target_generator,
        hop.certificate["twist_target_id"].as_str().unwrap(),
    );
    let (old_models, old_summary) = models::construct_all(&old_source, &basis);
    let (new_models, new_summary) = models::construct_all(&new_source, &basis);
    let homogeneity = fourth_homogeneity(f, &old_models, &new_models);
    let original_chosen = old_models
        .iter()
        .filter(|m| m.kernel_mask == original_g4)
        .collect::<Vec<_>>();
    let twist_chosen = new_models
        .iter()
        .filter(|m| m.kernel_mask == twisted_g4)
        .collect::<Vec<_>>();
    assert_eq!(original_chosen.len(), 1);
    assert_eq!(twist_chosen.len(), 1);
    let old = original_chosen[0];
    let new = twist_chosen[0];
    assert_eq!(old.normalized, new.normalized);
    let mut previous_arrays = vec![];
    for (name, text) in [
        (
            "entire-original-second-fixture",
            include_str!("../generated/old-second-model.json"),
        ),
        (
            "entire-original-third-fixture",
            include_str!("../generated/old-third-model.json"),
        ),
    ] {
        collect_old_arrays(
            &serde_json::from_str::<Value>(text).unwrap(),
            name.to_owned(),
            &mut previous_arrays,
        );
    }
    let repeats=old_models.iter().map(|m|{let current=serde_json::to_value(m.normalized).unwrap();let all=previous_arrays.iter().map(|(path,array)|json!({"original_fixture_path":path,"whole_prior_coefficients":array,"whole_current_coefficients":current,"exact_equal":*array==current})).collect::<Vec<_>>();json!({"current_case":[m.root_index,m.sign_index],"all_prior_array_comparisons":all})}).collect::<Vec<_>>();
    println!(
        "N4_FOURTH_ALL_MODELS {}",
        json!({"original_source_identity":old_source.identity(),"twisted_source_identity":new_source.identity(),"all6_original_rows":old_models.iter().map(|m|m.row.clone()).collect::<Vec<_>>(),"all6_twisted_rows":new_models.iter().map(|m|m.row.clone()).collect::<Vec<_>>(),"whole_original_summary":old_summary,"whole_twisted_summary":new_summary,"all6_corresponding_homogeneity_pairs":homogeneity,"all_prior_whole_array_comparisons":repeats,"original_G4":original_g4,"twisted_G4":twisted_g4,"all12_retained_before_acceptance":true})
    );
    for m in [old, new] {
        if m.row["eligible_for_supplied_source_maps"]
            .as_bool()
            .unwrap()
        {
            assert!(m.square_root.is_some() && m.p0.is_some());
            assert_eq!(m.row["smooth"], true);
        }
    }
    println!(
        "N4_FOURTH_MATCHED_ENDPOINTS {}",
        json!({"original":{"fixed_G4":original_g4,"case":[old.root_index,old.sign_index],"whole_matched_row":old.row,"eligible":old.row["eligible_for_supplied_source_maps"],"conditional_candidate":"original J1 to J4 skipping unsupported intermediate Jacobian models"},"separate_twist":{"fixed_G4":twisted_g4,"case":[new.root_index,new.sign_index],"whole_matched_row":new.row,"eligible":new.row["eligible_for_supplied_source_maps"],"conditional_candidate":"separate-instance C2nu to C3nu to C4nu"},"original_D12_D24_negatives_preserved":true,"no_original_logarithm_to_twist":true,"complete_Jacobian_evaluators":"not implemented","scope":"retain each matched endpoint outcome; no model reselection, universal classification or computational advantage"})
    );
}
