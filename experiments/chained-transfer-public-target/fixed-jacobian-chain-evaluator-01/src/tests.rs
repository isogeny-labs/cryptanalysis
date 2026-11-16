use super::*;
use chained_n4_paired_fourth_preflight::{PairedFourth, TwistedPair};

fn independent_point(
    pair: &TwistedPair,
    fourth: &PairedFourth<'_>,
    from: usize,
    to: usize,
    p: Pt<ER>,
) -> Pt<ER> {
    let fourth = fourth.branch(true);
    match (from, to) {
        (0, 1) => pair.forward(p),
        (1, 0) => pair.dual(p),
        (1, 2) => fourth.forward(p).unwrap(),
        (2, 1) => fourth.dual(p).unwrap(),
        (0, 2) => fourth.forward(pair.forward(p)).unwrap(),
        (2, 0) => pair.dual(fourth.dual(p).unwrap()),
        _ => panic!("unknown independent map"),
    }
}

fn complete_case(runtime: &Runtime, input: &Entry, to: usize) -> (Entry, Value) {
    let from = input.domain;
    let source = &runtime.geometry.models[from];
    let halves = runtime.halves(from, input.norm).unwrap();
    assert_eq!(halves.len(), 4);
    let mut rows = Vec::new();
    let mut outputs = Vec::new();
    for half in halves {
        let (output, row) = runtime.diagnose_half(input, to, half).unwrap();
        outputs.push(output);
        rows.push(row);
    }
    let output = outputs.remove(0);
    assert!(outputs
        .iter()
        .all(|x| x.class == output.class && x.norm == output.norm));
    let optimized = runtime.transfer_entry(input, to).unwrap();
    assert_eq!(optimized.class, output.class);
    assert_eq!(optimized.norm, output.norm);
    runtime.check_final(&output).unwrap();
    let back = runtime.transfer_entry(&output, from).unwrap();
    runtime.check_final(&back).unwrap();
    let expected = source
        .prime
        .a
        .pic
        .mul_scalar(&input.class, degree(from, to));
    assert_eq!(back.class, expected);
    assert_eq!(
        back.norm,
        curve::pmul(
            source.source.field(),
            source.source.curve(),
            &input.norm,
            degree(from, to)
        )
    );
    let inverse = inverse_scalar(degree(from, to));
    let recovery = source.prime.a.pic.mul_scalar(&back.class, inverse);
    assert_eq!(
        recovery, input.class,
        "full-group inverse, including the cofactor, is required"
    );
    let mut chain = Value::Null;
    if from.abs_diff(to) == 2 {
        let sequential = runtime.sequential_entry(input, to).unwrap();
        runtime.check_final(&sequential).unwrap();
        let retained = runtime.retained_lift_entry(input, to).unwrap();
        runtime.check_final(&retained).unwrap();
        assert_eq!(output.class, sequential.class);
        assert_eq!(output.class, retained.class);
        assert_eq!(output.norm, sequential.norm);
        assert_eq!(output.norm, retained.norm);
        chain = json!({"literal_two_map_Jacobian_chain":sequential.class.key().0,"strong_retained_elliptic_lift_chain":retained.class.key().0,"direct_composite":output.class.key().0,"all_exact":true});
    }
    (
        output.clone(),
        json!({"from":from,"to":to,"input":input.class.key().0,"source_norm":point_json(input.norm),"all_four_half_diagnostics":rows,"output":output.class.key().0,"actual_target_norm":point_json(output.norm),"dual_back":back.class.key().0,"independent_degree_scalar":expected.key().0,"full_group_inverse_scalar":inverse,"full_source_recovery":recovery.key().0,"chain_comparison":chain}),
    )
}

fn cofactor_panel(runtime: &Runtime, side: usize) -> Vec<PicClass> {
    let m = &runtime.geometry.models[side];
    let pic = &m.prime.a.pic;
    let mut points = pic.rational_points_bruteforce();
    points.sort();
    assert_eq!(points.len(), 224);
    let mut found = BTreeMap::new();
    let mut attempts = Vec::new();
    for point in points {
        let class = pic.exceptional(point);
        let projection = pic.mul_scalar(&class, ELL as u128);
        attempts.push(json!({"kind":"exceptional","point":point,"class":class.key().0,"actual_ell_projection":projection.key().0}));
        found.insert(projection.key().0, projection);
    }
    for p in &runtime.two[side] {
        let class = m.prime.a.transfer_point(&kp(*p)).unwrap();
        attempts.push(
            json!({"kind":"source_two_torsion","point":point_json(*p),"class":class.key().0}),
        );
        found.insert(class.key().0, class);
    }
    println!(
        "N4_FIXED_CHAIN_COFACTOR_ATTEMPTS {}",
        json!({"side":side,"all228_attempts":attempts,"all_actual_distinct_classes":found.keys().collect::<Vec<_>>()})
    );
    assert_eq!(
        found.len(),
        4,
        "retain missing or larger cofactor populations without reselection"
    );
    for class in found.values() {
        assert!(pic.is_zero(&pic.mul_scalar(class, 4)));
    }
    for a in found.values() {
        for b in found.values() {
            assert!(found.contains_key(&pic.add(a, b).key().0));
        }
    }
    found.into_values().collect()
}

fn assert_public_case(
    runtime: &Runtime,
    pair: &TwistedPair,
    fourth: &PairedFourth<'_>,
    from: usize,
    to: usize,
    scalar: u128,
    sector: usize,
    cofactors: &[Vec<PicClass>; 3],
    cofactor_images: &[Vec<Vec<Option<PicClass>>>; 3],
) -> Value {
    let m = &runtime.geometry.models[from];
    let target = &runtime.geometry.models[to];
    let point = curve::pmul(
        m.source.field(),
        m.source.curve(),
        &m.source.generator(),
        scalar,
    );
    let prime = m.prime.a.transfer_point(&kp(point)).unwrap();
    let class = m.prime.a.pic.add(&prime, &cofactors[from][sector]);
    let input = runtime.admit(from, &runtime.encode(from, &class)).unwrap();
    let recovered = curve::pmul(m.source.field(), m.source.curve(), &input.norm, 1_385_856);
    assert_eq!(
        recovered, point,
        "independent prime-source recovery must include all cofactor sectors"
    );
    let (output, case) = complete_case(runtime, &input, to);
    let independent = independent_point(pair, fourth, from, to, point);
    let independent_phi = target.prime.a.transfer_point(&kp(independent)).unwrap();
    let expected = target.prime.a.pic.add(
        &independent_phi,
        cofactor_images[from][to][sector].as_ref().unwrap(),
    );
    assert_eq!(output.class, expected);
    let recovered_target = curve::pmul(
        target.source.field(),
        target.source.curve(),
        &output.norm,
        1_385_856,
    );
    assert_eq!(recovered_target, independent);
    // Exercise the actual complete public interface and full-group inverse.
    let actual = runtime
        .evaluate(from, to, &runtime.encode(from, &class))
        .unwrap();
    assert_eq!(actual.key, output.class.key().0);
    let inverse = runtime.inverse_of(from, to, &actual).unwrap();
    assert_eq!(inverse.key, class.key().0);
    json!({"scalar_OUTSIDE_runtime":scalar,"sector":sector,"independent_source_point":point_json(point),"actual_source_recovered":point_json(recovered),"independent_original_elliptic_map_point":point_json(independent),"actual_target_recovered":point_json(recovered_target),"expected_prime_plus_actual_cofactor_image":expected.key().0,"complete_case":case})
}

#[test]
fn all_fixed_three_model_complete_maps_and_full_panels() {
    let c = CheckedInstance::construct().unwrap();
    let runtime = Runtime::construct(&c).unwrap();
    println!("N4_FIXED_CHAIN_SETUP {}", runtime.setup);
    assert_eq!(inverse_scalar(13), 5_117_005);
    assert_eq!(inverse_scalar(169), 7_216_289);
    let cofactors = std::array::from_fn(|side| cofactor_panel(&runtime, side));
    let mut cofactor_images: [Vec<Vec<Option<PicClass>>>; 3] =
        std::array::from_fn(|_| (0..3).map(|_| vec![None; 4]).collect());
    for from in 0..3 {
        for to in 0..3 {
            if from == to {
                continue;
            }
            for (sector, class) in cofactors[from].iter().enumerate() {
                let input = runtime.admit(from, &runtime.encode(from, class)).unwrap();
                let (out, _) = complete_case(&runtime, &input, to);
                cofactor_images[from][to][sector] = Some(out.class);
            }
        }
    }
    for from in 0..3 {
        let pic = &runtime.geometry.models[from].prime.a.pic;
        let mut points = pic.rational_points_bruteforce();
        points.sort();
        assert_eq!(points.len(), 224);
        let mut rows = Vec::new();
        for (i, point) in points.into_iter().enumerate() {
            if i % 16 == 0 {
                eprintln!("fixed full-chain exceptional domain{from}/input{i}/224");
            }
            let class = pic.exceptional(point);
            let input = runtime.admit(from, &runtime.encode(from, &class)).unwrap();
            let mut outgoing = Vec::new();
            for to in 0..3 {
                if to != from {
                    outgoing.push(complete_case(&runtime, &input, to).1);
                }
            }
            assert_eq!(outgoing.len(), 2);
            let row = json!({"point":point,"both_outgoing_maps":outgoing});
            println!(
                "N4_FIXED_CHAIN_EXCEPTIONAL_CASE {}",
                json!({"domain":from,"index":i,"whole_descriptor":row})
            );
            rows.push(row);
        }
        assert_eq!(rows.len(), 224);
        println!(
            "N4_FIXED_CHAIN_ALL_EXCEPTIONALS {}",
            json!({"domain":from,"all224_descriptors":rows})
        );
    }
    let pair = TwistedPair::construct(&c);
    let fourth = PairedFourth::construct(&c, &pair);
    let mut mixed = Vec::new();
    let mut publics = Vec::new();
    for from in 0..3 {
        for to in 0..3 {
            if from == to {
                continue;
            }
            for scalar in [0, 1, 2, 17, 12345, ELL as u128 - 1] {
                for sector in 0..4 {
                    mixed.push(assert_public_case(
                        &runtime,
                        &pair,
                        &fourth,
                        from,
                        to,
                        scalar,
                        sector,
                        &cofactors,
                        &cofactor_images,
                    ));
                }
            }
            for scalar in [1, 2, 17, 12345, ELL as u128 - 1] {
                for sector in 0..4 {
                    publics.push(assert_public_case(
                        &runtime,
                        &pair,
                        &fourth,
                        from,
                        to,
                        scalar,
                        sector,
                        &cofactors,
                        &cofactor_images,
                    ));
                }
            }
        }
    }
    assert_eq!(mixed.len(), 144);
    assert_eq!(publics.len(), 120);
    println!("N4_FIXED_CHAIN_ALL_MIXED {}", json!({"all144":mixed}));
    println!("N4_FIXED_CHAIN_ALL_PUBLIC {}", json!({"all120":publics}));
    let mut additions = Vec::new();
    for (left, right) in [(0, 1), (1, 2), (0, 2)] {
        let mut pair_rows = Vec::new();
        for (from, to) in [(left, right), (right, left)] {
            let m = &runtime.geometry.models[from];
            let pic = &m.prime.a.pic;
            let target = &runtime.geometry.models[to].prime.a.pic;
            let generator = m.prime.a.transfer_point(&kp(m.source.generator())).unwrap();
            let mut pool = Vec::new();
            let mut images = Vec::new();
            for scalar in [0, 1, 2, 17, 12345, ELL as u128 - 1] {
                let odd = pic.mul_scalar(&generator, scalar);
                for t in &cofactors[from] {
                    let x = pic.add(&odd, t);
                    let y = runtime
                        .evaluate(from, to, &runtime.encode(from, &x))
                        .unwrap();
                    let y = runtime.admit(to, &y).unwrap();
                    pool.push(x);
                    images.push(y.class);
                }
            }
            assert_eq!(pool.len(), 24);
            for i in 0..8 {
                for j in 0..6 {
                    let sum = pic.add(&pool[i], &pool[j]);
                    let input = runtime.admit(from, &runtime.encode(from, &sum)).unwrap();
                    let (out, case) = complete_case(&runtime, &input, to);
                    let expected = target.add(&images[i], &images[j]);
                    assert_eq!(out.class, expected);
                    pair_rows.push(json!({"from":from,"to":to,"i":i,"j":j,"expected_independent_sum":expected.key().0,"case":case}));
                }
            }
        }
        assert_eq!(pair_rows.len(), 96);
        additions.push(json!({"pair":[left,right],"all96":pair_rows}));
    }
    println!(
        "N4_FIXED_CHAIN_ALL_ADDITIONS {}",
        json!({"all_three_pairs":additions})
    );
    let mut vectors = Vec::new();
    for (from, to) in [(0, 2), (2, 0)] {
        for scalar in [0, 1, 2, 17, 12345, ELL as u128 - 1] {
            for (sector, t) in cofactors[from].iter().enumerate() {
                let m = &runtime.geometry.models[from];
                let p = curve::pmul(
                    m.source.field(),
                    m.source.curve(),
                    &m.source.generator(),
                    scalar,
                );
                let odd = m.prime.a.transfer_point(&kp(p)).unwrap();
                let x = m.prime.a.pic.add(&odd, t);
                let packet = runtime.encode(from, &x);
                runtime.reset_calls();
                let input = runtime.admit(from, &packet).unwrap();
                let out = runtime.transfer_entry(&input, to).unwrap();
                runtime.check_final(&out).unwrap();
                let direct = runtime.calls();
                runtime.reset_calls();
                let input = runtime.admit(from, &packet).unwrap();
                let seq = runtime.sequential_entry(&input, to).unwrap();
                runtime.check_final(&seq).unwrap();
                let sequential = runtime.calls();
                runtime.reset_calls();
                let input = runtime.admit(from, &packet).unwrap();
                let retained = runtime.retained_lift_entry(&input, to).unwrap();
                runtime.check_final(&retained).unwrap();
                let strongest = runtime.calls();
                assert_eq!(out.class, seq.class);
                assert_eq!(out.class, retained.class);
                for c in [direct, sequential, strongest] {
                    assert_eq!(c.external_packet_parse, 1);
                    assert_eq!(c.external_norm_and_geometry, 1);
                    assert_eq!(c.external_full_order, 1);
                    assert_eq!(c.final_actual_norm, 1);
                    assert_eq!(c.final_full_order, 1);
                }
                assert_eq!(direct.quadratic_source_phi, 1);
                assert_eq!(direct.quadratic_target_phi, 1);
                assert_eq!(strongest.quadratic_source_phi, 1);
                assert_eq!(strongest.quadratic_target_phi, 1);
                assert_eq!(sequential.quadratic_source_phi, 2);
                assert_eq!(sequential.quadratic_target_phi, 2);
                vectors.push(json!({"from":from,"to":to,"scalar_OUTSIDE_runtime":scalar,"sector":sector,"input":x.key().0,"direct_composite":direct,"literal_sequential_Jacobian_maps":sequential,"strongest_retained_lift_chain":strongest,"whole_outputs_equal":out.class.key().0}));
            }
        }
    }
    assert_eq!(vectors.len(), 48);
    println!(
        "N4_FIXED_CHAIN_SELECTED_CALL_VECTORS {}",
        json!({"all48":vectors,"scope":"actual selected source entries only; all setup/primitive work unpriced and complete primitive census still open; no measured speed advantage"})
    );
    let m = &runtime.geometry.models[0];
    let g = m.prime.a.transfer_point(&kp(m.source.generator())).unwrap();
    let packet = runtime.encode(0, &g);
    let mut rejections = Vec::new();
    let mut bad = packet.clone();
    bad.model.push_str("foreign");
    rejections.push(runtime.evaluate(0, 1, &bad).unwrap_err());
    let mut bad = packet.clone();
    bad.field.push_str("foreign");
    rejections.push(runtime.evaluate(0, 1, &bad).unwrap_err());
    let mut bad = packet.clone();
    bad.key[1] = 223;
    rejections.push(runtime.evaluate(0, 1, &bad).unwrap_err());
    let mut bad = runtime.encode(0, &m.prime.a.pic.zero());
    bad.key[18] = 1;
    rejections.push(runtime.evaluate(0, 1, &bad).unwrap_err());
    rejections.push(runtime.evaluate(0, 0, &packet).unwrap_err());
    rejections.push(runtime.evaluate(3, 1, &packet).unwrap_err());
    assert!(generic_half(
        &m.quadratic.f,
        &m.quadratic.curve,
        Pt::Inf,
        m.quadratic.f.zero()
    )
    .is_err());
    assert!(generic_half(
        &m.quadratic.f,
        &m.quadratic.curve,
        lift(runtime.two[0][1]),
        m.quadratic.f.zero()
    )
    .is_err());
    println!(
        "N4_FIXED_CHAIN_ACTUAL_REJECTIONS {}",
        json!({"all_actual_interface_errors":rejections,"generic_infinity_and_zero_ordinate_rejected":true})
    );
    println!(
        "N4_FIXED_CHAIN_FULL_POPULATION {}",
        json!({"domains":3,"exceptional_descriptors":672,"exceptional_outgoing_evaluations":1344,"mixed":144,"public":120,"addition_pairs_per_undirected_pair":96,"undirected_pairs":3,"comparison_vectors":48,"all_four_halves_and_duplicate_corrections_required":true,"full_group_order":ORDER,"source_prime":ELL,"scope":"finite complete-chain population under explicit geometric and program bridges; no calibrated advantage, complete primitive census or signed standing"})
    );
}
