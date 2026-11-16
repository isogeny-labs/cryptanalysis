use super::*;
use chained_n4_odd_source::OddSourceIsogeny;
use chained_n4_public_target::CheckedInstance;

#[test]
fn generic_old_panel_parity_then_all_actual_degree13_product_gluings() {
    let c = CheckedInstance::construct().unwrap();
    let basis = AdapterV2::new(&c).unwrap();
    let old = SourceE::original(&c);
    let (original_models, _) = chained_n4_gluing_models::construct_all(&c, &basis);
    let (generic_old, _) = construct_all(&old, &basis);
    assert_eq!(generic_old.len(), 6);
    let mut parity = vec![];
    for (a, b) in generic_old.iter().zip(&original_models) {
        assert_eq!((a.root_index, a.sign_index), (b.root_index, b.sign_index));
        assert_eq!(a.root, b.root);
        assert_eq!(a.source_a, b.source_a);
        assert_eq!(a.source_b, b.source_b);
        assert_eq!(a.h, b.h);
        assert_eq!(a.d, b.d);
        assert_eq!(a.h_matrix, b.h_matrix);
        assert_eq!(a.q_matrix, b.q_matrix);
        assert_eq!(a.determinant, b.determinant);
        assert_eq!(a.factor, b.factor);
        assert_eq!(a.square_root, b.square_root);
        assert_eq!(a.kernel_mask, b.kernel_mask);
        assert_eq!(a.full_coefficients, b.full_coefficients);
        assert_eq!(a.normalized, b.normalized);
        assert_eq!(a.coefficient_scale, b.coefficient_scale);
        assert_eq!(a.p0, b.p0);
        assert_eq!(a.row["all_rational_points"], b.row["all_rational_points"]);
        assert_eq!(a.row["quotients"], b.row["quotients"]);
        parity.push(json!({"candidate":[a.root_index,a.sign_index],"all_equations_factors_kernels_origins_and_complete_quotients_equal":true}));
    }
    let transfer = OddSourceIsogeny::construct(&c);
    let new = SourceE::degree13_target(&c, &transfer);
    assert_ne!(new.source_tag(), old.source_tag());
    assert_ne!(new.curve(), old.curve());
    assert_eq!(new.field_tag(), old.field_tag());
    let f = new.field();
    let mut rng = Rng::new(0x6313);
    let mut old_roots = poly::roots(
        f,
        &vec![old.curve().b, old.curve().a, f.zero(), f.one()],
        &mut rng,
    );
    let mut new_roots = poly::roots(
        f,
        &vec![new.curve().b, new.curve().a, f.zero(), f.one()],
        &mut rng,
    );
    old_roots.sort();
    new_roots.sort();
    assert_eq!(old_roots.len(), 3);
    assert_eq!(new_roots.len(), 3);
    let mut permutation = vec![0];
    let mut torsion_rows = vec![];
    for &x in &old_roots {
        let image = transfer.forward(Pt::Aff(x, f.zero())).unwrap();
        let y = match image {
            Pt::Aff(y, z) => {
                assert_eq!(z, f.zero());
                y
            }
            Pt::Inf => panic!("odd isogeny killed nonzero2-torsion"),
        };
        let index = new_roots.iter().position(|&r| r == y).unwrap() + 1;
        assert!(!permutation.contains(&index));
        permutation.push(index);
        torsion_rows
            .push(json!({"source_x":three(x),"target_x":three(y),"target_sorted_index":index}));
    }
    assert_eq!(permutation.len(), 4);
    println!(
        "N4_ODD_PRODUCT_SOURCE {}",
        json!({"old":old.identity(),"target":new.identity(),"all6_old_parity":parity,"actual_source2_to_target2_permutation":permutation,"all3_nonzero_torsion_images":torsion_rows,"scope":"fresh checked SourceE; no original private state mutation; actual target independent Hasse certificate"})
    );
    let (models, summary) = construct_all(&new, &basis);
    println!("N4_ODD_PRODUCT_KERNELS {}", summary);
    for m in &models {
        println!("N4_ODD_PRODUCT_MODEL {}", m.row);
    }
    println!(
        "N4_ODD_PRODUCT_SCOPE {}",
        json!({"protocol":"56fbbb before code","source":new.identity(),"all_six_candidates_retained":true,
        "models":models.len(),"smooth_square":models.iter().filter(|m|m.p0.is_some()&&m.square_root.is_some()).count(),
        "smooth_nonsquare":models.iter().filter(|m|m.p0.is_some()&&m.square_root.is_none()).count(),
        "Tzero":models.iter().filter(|m|m.determinant==k(0)).count(),"singular":models.iter().filter(|m|m.p0.is_none()).count(),
        "actual_new_Phi_Norm_and_both52":"not implemented in this model phase","cost":"not benchmark/admitted","standing":"unsigned"})
    );
}
