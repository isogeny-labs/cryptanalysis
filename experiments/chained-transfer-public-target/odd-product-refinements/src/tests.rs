use crate::{
    fast_source::{ep, kp},
    kernels, FastSourceChain,
};
use chained_n4_completed_v2::{AdapterV2, NormV2};
use chained_n4_odd_product_maps::{Adapter, Chain, NormNew, Point};
use chained_n4_odd_product_models::{construct_all, three, SourceE};
use chained_n4_odd_source::OddSourceIsogeny;
use chained_n4_public_target::{ghs::EP, CheckedInstance};
use isogeny_algos::{
    curve::{self, Pt},
    field::{Field, Rng},
    poly,
};
use serde_json::{json, Value};

fn short(c: &CheckedInstance, p: EP) -> Point {
    match p {
        EP::Inf => None,
        EP::A(x, y) => Some((c.inst.kf.add(&x, &c.short_shift), y)),
    }
}

#[test]
fn actual_transported_kernel_census_and_identical_output_source_api() {
    let c = CheckedInstance::construct().unwrap();
    let old = NormV2::new(AdapterV2::new(&c).unwrap()).unwrap();
    let t = OddSourceIsogeny::construct(&c);
    let source = SourceE::degree13_target(&c, &t);
    let f = source.field();
    let original = SourceE::original(&c);
    let (mut original_models, _) = construct_all(&original, &old.a);
    let literal = original_models
        .iter()
        .find(|m| (m.root_index, m.sign_index) == (1, 0))
        .unwrap();
    assert_eq!(literal.normalized, c.inst.f);
    let old_gold = literal.kernel_mask;
    let (models, summary) = construct_all(&source, &old.a);
    let types = kernels::audit_all(&c, &old, &source, &t, &models, &summary, old_gold);
    let wrong_index = original_models
        .iter()
        .position(|m| m.square_root.is_some())
        .unwrap();
    let wrong =
        NormNew::new(Adapter::new(&original, &old.a, original_models.remove(wrong_index)).unwrap())
            .unwrap();
    assert!(FastSourceChain::new(&c, &wrong, &t).is_err());
    let sg = short(&c, c.inst.g);
    let ec = &c.independent_curve;
    let mut roots = poly::roots(
        f,
        &vec![ec.b, ec.a, f.zero(), f.one()],
        &mut Rng::new(0x6621),
    );
    roots.sort();
    assert_eq!(roots.len(), 3);
    let old2: Vec<_> = roots.iter().map(|&x| Some((three(x), [0; 3]))).collect();
    let requests = c
        .parse(include_bytes!("../../fixtures/public-five.json"))
        .unwrap();
    let answers: Vec<Value> =
        serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
            .unwrap();
    let mut panel = vec![(0, None)];
    for i in 0..32 {
        let scalar = 1 + 2 * i;
        panel.push((scalar, kp(curve::pmul(f, ec, &ep(sg), scalar as u128))));
    }
    assert_eq!(panel.len(), 33);
    let mut results = vec![];
    let mut nonsquares = vec![];
    for m in models {
        let id = [m.root_index, m.sign_index];
        if m.square_root.is_none() {
            assert!(Adapter::new(&source, &old.a, m).is_err());
            nonsquares.push(id);
            continue;
        }
        let n = NormNew::new(Adapter::new(&source, &old.a, m).unwrap()).unwrap();
        let p = &n.a.pic;
        let reference = Chain::new(&c, &old, &n, &t).unwrap();
        let candidate = FastSourceChain::new(&c, &n, &t).unwrap();
        let g = candidate.from_source_odd_coords(sg).unwrap();
        assert!(!p.is_zero(&g));
        assert!(p.is_zero(&p.mul_scalar(&g, c.inst.ell as u128)));
        let undoubled = n.a.transfer_point(&kp(t.forward(ep(sg)).unwrap())).unwrap();
        assert_ne!(g, undoubled);
        assert_eq!(g, p.double(&undoubled));
        let mut rows = vec![];
        for &(scalar, q) in &panel {
            let image = candidate.from_source_odd_coords(q).unwrap();
            let expected = reference.from_source_odd_coords(q).unwrap();
            assert_eq!(image, expected);
            assert_eq!(image, p.mul_scalar(&g, scalar as u128));
            assert_eq!(candidate.recover_source_odd_coords(&image).unwrap(), q);
            assert_eq!(reference.recover_source_odd_coords(&image).unwrap(), q);
            let packet = candidate.encode_source(q);
            assert_eq!(
                serde_json::to_value(&packet).unwrap(),
                serde_json::to_value(reference.encode_source(q)).unwrap()
            );
            let encoded = candidate.from_source(&packet).unwrap();
            assert_eq!(
                serde_json::to_value(&encoded).unwrap(),
                serde_json::to_value(reference.from_source(&packet).unwrap()).unwrap()
            );
            assert_eq!(
                serde_json::to_value(candidate.recover_source(&encoded).unwrap()).unwrap(),
                serde_json::to_value(&packet).unwrap()
            );
            rows.push(json!({"outside_runtime_scalar":scalar,"source":q,"candidate_image":image.key().0.to_vec(),"reference_image":expected.key().0.to_vec(),"tagged":encoded,"both_source_recoveries":true}));
        }
        let mut publics = vec![];
        for (i, &raw) in requests.iter().enumerate() {
            let q = short(&c, raw);
            let scalar = answers[i]["original_native_recovered_scalar"]
                .as_u64()
                .unwrap();
            assert!(c.verify_recovered(raw, scalar));
            assert_eq!(ep(q), curve::pmul(f, ec, &ep(sg), scalar as u128));
            let image = candidate.from_source_odd_coords(q).unwrap();
            let expected = reference.from_source_odd_coords(q).unwrap();
            assert_eq!(image, expected);
            assert_eq!(image, p.mul_scalar(&g, scalar as u128));
            assert_eq!(candidate.recover_source_odd_coords(&image).unwrap(), q);
            let packet = candidate.encode_source(q);
            let encoded = candidate.from_source(&packet).unwrap();
            assert_eq!(
                serde_json::to_value(&encoded).unwrap(),
                serde_json::to_value(reference.from_source(&packet).unwrap()).unwrap()
            );
            assert_eq!(candidate.recover_source(&encoded).unwrap().coordinates, q);
            publics.push(json!({"index":i,"literal_original_target":chained_n4_public_target::encode_point(raw),"outside_runtime_scalar":scalar,"original_independent_answer_check":true,"source":q,"candidate_image":image.key().0.to_vec(),"reference_image":expected.key().0.to_vec(),"tagged_image":encoded,"recovered_source":q}));
        }
        let mut rejection_rows = vec![];
        let mut noncanonical = sg.unwrap();
        noncanonical.0[0] += 223;
        for (label, q) in std::iter::once(("offcurve", Some(([0; 3], [0; 3]))))
            .chain(std::iter::once(("noncanonical", Some(noncanonical))))
            .chain(old2.iter().copied().map(|q| ("nonodd-source", q)))
        {
            assert!(candidate.from_source_odd_coords(q).is_err());
            assert!(reference.from_source_odd_coords(q).is_err());
            rejection_rows.push(json!({"control":label,"input":q,"both_reject":true}));
        }
        let packet = candidate.encode_source(sg);
        for label in ["field", "model"] {
            let mut bad = packet.clone();
            if label == "field" {
                bad.field.push('x');
            } else {
                bad.model.push('x');
            }
            assert!(candidate.from_source(&bad).is_err());
            assert!(reference.from_source(&bad).is_err());
            rejection_rows.push(json!({"control":format!("source-{label}"),"both_reject":true}));
        }
        let encoded = candidate.from_source(&packet).unwrap();
        for label in ["field", "model"] {
            let mut bad = encoded.clone();
            if label == "field" {
                bad.field.push('x');
            } else {
                bad.model.push('x');
            }
            assert!(candidate.recover_source(&bad).is_err());
            assert!(reference.recover_source(&bad).is_err());
            rejection_rows.push(json!({"control":format!("target-{label}"),"both_reject":true}));
        }
        let mut cofactor = vec![p.zero()];
        for point in p.rational_points_bruteforce() {
            let cof = p.mul_scalar(&p.point_class(point), c.inst.ell as u128);
            for start in cofactor.clone() {
                let mut z = start;
                for _ in 0..4 {
                    if !cofactor.contains(&z) {
                        cofactor.push(z.clone());
                    }
                    z = p.add(&z, &cof);
                }
            }
            assert!(cofactor.len() <= 4);
        }
        assert_eq!(cofactor.len(), 4);
        for class in cofactor.iter().filter(|x| !p.is_zero(x)) {
            assert!(candidate.recover_source_odd_coords(class).is_err());
            assert!(reference.recover_source_odd_coords(class).is_err());
            rejection_rows.push(json!({"control":"nonodd-target","input":class.key().0.to_vec(),"both_reject":true}));
        }
        assert_eq!(
            candidate.recover_source_odd_coords(&p.zero()).unwrap(),
            None
        );
        let row = json!({"target":id,"target_model":n.model_tag,"source_model":source.identity(),"same33_odd_and_zero":rows,"same_public5":publics,"all_rejections":rejection_rows,"mismatched_actual_target_constructor_rejects":true,"undoubled_map_control_changes_generator":true,"candidate_generator_equals_double_direct_generator":true,"nonzero_exact_ell_image":true,"structural_forward_algorithm":{"reference":["old-Phi","old-Norm","gamma","new-Phi"],"candidate":["original-E-double","gamma","new-Phi"],"constructor_holds_old_Phi_or_Norm":false},"cost_scope":"no measured cost or speedup;admission and complete counters remain open"});
        println!("N4_REFINEMENT_SOURCE_API {}", row);
        results.push(id);
    }
    assert_eq!(results, vec![[1, 0], [1, 1], [2, 1]]);
    assert_eq!(nonsquares, vec![[0, 0], [0, 1], [2, 0]]);
    println!(
        "N4_REFINEMENT_SCOPE {}",
        json!({"protocol":"579e08","eligible":results,"nonsquare_constructor_rejections":nonsquares,"all9_kernel_types":types,"all3_33oddzero_and5_public_exact_same_images":true,"immutable_reference":"45ee45d2 Chain and675 inputs","scope":"correctness/structural call removal;written global kernel bridges and faithful partial Lean next;no performance claim"})
    );
}
