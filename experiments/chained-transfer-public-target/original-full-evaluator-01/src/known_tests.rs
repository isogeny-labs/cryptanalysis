fn known_point_vectors(runtime: &Runtime) {
    let mut rows = Vec::new();
    for (from, to) in [(0, 2), (2, 0)] {
        let source = &runtime.geometry.models[from];
        for scalar in [0, 1, 2, 17, 12345, ELL as u128 - 1] {
            let prime = curve::pmul(
                source.source.field(),
                source.source.curve(),
                &source.source.generator(),
                scalar,
            );
            for (index, two) in runtime.two[from].iter().enumerate() {
                let point = curve::padd(source.source.field(), source.source.curve(), &prime, two);
                let class = source.prime.a.transfer_point(&kp(point)).unwrap();
                let opaque = runtime.encode(from, &class);
                let presentation = runtime.encode_known_point(from, kp(point));
                runtime.reset_calls();
                let ordinary = runtime.evaluate(from, to, &opaque).unwrap();
                let ordinary_calls = runtime.calls();
                runtime.reset_calls();
                let direct = runtime
                    .evaluate_known_point(from, to, &presentation, false)
                    .unwrap();
                let direct_calls = runtime.calls();
                runtime.reset_calls();
                let factored = runtime
                    .evaluate_known_point(from, to, &presentation, true)
                    .unwrap();
                let factored_calls = runtime.calls();
                assert_eq!(
                    serde_json::to_value(&ordinary).unwrap(),
                    serde_json::to_value(&direct).unwrap()
                );
                assert_eq!(
                    serde_json::to_value(&direct).unwrap(),
                    serde_json::to_value(&factored).unwrap()
                );
                for c in [direct_calls, factored_calls] {
                    assert_eq!(c.external_point_parse, 1);
                    assert_eq!(c.external_point_full_order, 1);
                    assert_eq!(c.external_packet_parse, 0);
                    assert_eq!(c.external_norm_and_geometry, 0);
                    assert_eq!(c.external_full_order, 0);
                    assert_eq!(c.quadratic_source_phi, 0);
                    assert_eq!(c.quadratic_target_phi, 0);
                    assert_eq!(c.target_prime_phi, 1);
                    assert_eq!(c.final_actual_norm, 1);
                    assert_eq!(c.final_full_order, 1);
                    assert_eq!(c.transported_norm_doubling, 1);
                }
                assert_eq!(direct_calls.degree169_elliptic_evaluation, 1);
                assert_eq!(direct_calls.degree13_elliptic_evaluation, 0);
                assert_eq!(factored_calls.degree169_elliptic_evaluation, 0);
                assert_eq!(factored_calls.degree13_elliptic_evaluation, 2);
                let back = runtime.inverse_of(from, to, &direct).unwrap();
                assert_eq!(back.key, class.key().0);
                rows.push(json!({"from":from,"to":to,"scalar_OUTSIDE_runtime":scalar,"source_E2_index":index,"whole_known_point_packet":presentation,"whole_source_phi_packet":opaque,"whole_three_equal_outputs":ordinary,"opaque_full_group_calls":ordinary_calls,"known_point_direct169_calls":direct_calls,"known_point_factored13_calls":factored_calls,"full_group_inverse_recovery":back}));
            }
        }
    }
    assert_eq!(rows.len(), 48);
    let g = &runtime.geometry.models[0];
    let packet = runtime.encode_known_point(0, kp(g.source.generator()));
    let mut field = packet.clone();
    field.field.push_str("foreign");
    assert!(runtime.evaluate_known_point(0, 2, &field, false).is_err());
    let mut model = packet.clone();
    model.model.push_str("foreign");
    assert!(runtime.evaluate_known_point(0, 2, &model, false).is_err());
    let mut noncanonical = packet.clone();
    noncanonical.coordinates.as_mut().unwrap().0[0] = 223;
    assert!(runtime
        .evaluate_known_point(0, 2, &noncanonical, false)
        .is_err());
    assert!(runtime.evaluate_known_point(0, 0, &packet, false).is_err());
    assert!(runtime.evaluate_known_point(3, 2, &packet, false).is_err());
    println!(
        "N4_ORIGINAL_FULL_KNOWN_POINT_VECTORS {}",
        json!({"all48":rows,"actual_foreign_field_model_noncanonical_direction_rejected":true,"source_presentation":"actual full-order elliptic P+T; all4E2 points andduplicateJacobianimages retained; notallJacobiancofactorsectors areassertedcovered","scope":"samewholeoutputs forknownpointdirect/factored andopaqueclass routes; selected callsunpriced, no scalarwitness passed"})
    );
}

fn original_point_json(p: Pt<ER>) -> Value {
    json!(kp(p))
}
fn inverse_original_prime(n: u128) -> u128 {
    let (mut a, mut b, mut x, mut y) = (n as i128, ELL as i128, 1i128, 0i128);
    while b != 0 {
        let q = a / b;
        (a, b) = (b, a - q * b);
        (x, y) = (y, x - q * y);
    }
    assert_eq!(a, 1);
    let inverse = x.rem_euclid(ELL as i128) as u128;
    assert_eq!(n * inverse % ELL as u128, 1);
    inverse
}

fn original_public_controls(
    runtime: &Runtime,
    c: &CheckedInstance,
    pair: &ThirdHop,
    fourth: &PairedFourth<'_>,
) {
    let initial = chained_n4_paired_fourth_preflight::models::SourceE::original(c);
    let first = chained_n4_odd_source::OddSourceIsogeny::construct(c);
    let edge = fourth.branch(false);
    let f = initial.field();
    let mut original_controls = Vec::new();
    let mut transfers = Vec::new();
    for k in [1u64, 2, 17, 12345, ELL - 1] {
        let p0 = curve::pmul(f, initial.curve(), &initial.generator(), k as u128);
        let p1 = first.forward(p0).unwrap();
        let p2 = pair.previous().forward(p1).unwrap();
        assert_eq!(p2, pair.original_to_source(p0).unwrap());
        let p3 = pair.forward(p2).unwrap();
        let p4 = edge.forward(p3).unwrap();
        let d3 = edge.dual(p4).unwrap();
        let d2 = pair.dual(d3).unwrap();
        let d1 = pair.previous().dual(d2).unwrap();
        let d0 = first.dual(d1).unwrap();
        assert_eq!(d1, curve::pmul(f, first.target(), &p1, 2197));
        assert_eq!(d0, curve::pmul(f, initial.curve(), &p0, 28561));
        let original_point = match p0 {
            Pt::Inf => chained_n4_public_target::ghs::EP::Inf,
            Pt::Aff(x, y) => {
                chained_n4_public_target::ghs::EP::A(three(f.sub(x, er(c.short_shift))), three(y))
            }
        };
        assert!(c.verify_recovered(original_point, k));
        original_controls.push(json!({"known_scalar":k,"actual_E0":original_point_json(p0),"actual_E1":original_point_json(p1),"actual_E2":original_point_json(p2),"actual_E3":original_point_json(p3),"actual_E4":original_point_json(p4),"actual_reverse3_to_E1":original_point_json(d1),"actual_reverse4_to_E0":original_point_json(d0),"independent_original_source_check":true,"sequential_norms":[2197,28561],"whole_composite_rational_expansion":false}));
        for (domain, p) in [p2, p3, p4].into_iter().enumerate() {
            let g = &runtime.geometry.models[domain];
            let image = g.prime.a.transfer_point(&kp(p)).unwrap();
            let actual_norm = ep(g.prime.norm(&image).unwrap());
            assert_eq!(
                actual_norm,
                curve::pmul(g.source.field(), g.source.curve(), &p, 2)
            );
            let mut reverse = actual_norm;
            if domain == 2 {
                reverse = edge.dual(reverse).unwrap()
            }
            if domain >= 1 {
                reverse = pair.dual(reverse).unwrap()
            }
            reverse = first.dual(pair.previous().dual(reverse).unwrap()).unwrap();
            let n = 13u128.pow(domain as u32 + 2);
            assert_eq!(reverse, curve::pmul(f, initial.curve(), &p0, 2 * n));
            let recovered =
                curve::pmul(f, initial.curve(), &reverse, inverse_original_prime(2 * n));
            assert_eq!(recovered, p0);
            assert!(g
                .prime
                .a
                .pic
                .is_zero(&g.prime.a.pic.mul_scalar(&image, ELL as u128)));
            transfers.push(json!({"known_scalar_OUTSIDE_runtime":k,"domain":domain,"original_E0_public_point":original_point_json(p0),"factored_prefix_point":original_point_json(p),"whole_target_class":runtime.encode(domain,&image),"actual_target_norm":original_point_json(actual_norm),"actual_signed_dual_prefix":original_point_json(reverse),"elliptic_prefix_norm":n,"inverse_twice_prefix_norm":inverse_original_prime(2*n),"actual_original_point_recovered":original_point_json(recovered)}));
        }
    }
    assert_eq!(original_controls.len(), 5);
    assert_eq!(transfers.len(), 15);
    println!(
        "N4_ORIGINAL_FULL_ORIGINAL_PUBLIC {}",
        json!({"whole_original_five_controls":original_controls,"all15":transfers})
    );
}
