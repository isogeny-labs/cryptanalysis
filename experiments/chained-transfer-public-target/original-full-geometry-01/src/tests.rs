use super::*;
use chained_n4_beta_rational_lift::{lift3, point_json, point_key};
use chained_n4_odd_product_maps as original;
use chained_n4_odd_product_models as original_models;
use chained_n4_odd_source::OddSourceIsogeny;
use chained_n4_paired_fourth_preflight::models::{er, three};
use isogeny_algos::{
    curve,
    field::{Field, Rng},
    poly,
};
use std::collections::BTreeMap;

fn kp(p: Pt<ER>) -> Point {
    match p {
        Pt::Inf => None,
        Pt::Aff(x, y) => Some((three(x), three(y))),
    }
}
fn lift(p: Pt<ER>) -> Pt<ER> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => Pt::Aff(lift3(x), lift3(y)),
    }
}
fn torsion(source: &SourceE) -> Vec<Pt<ER>> {
    let f = source.field();
    let e = source.curve();
    let mut roots = poly::roots(f, &vec![e.b, e.a, f.zero(), f.one()], &mut Rng::new(0x8302));
    roots.sort();
    assert_eq!(roots.len(), 3);
    let mut points = vec![Pt::Inf];
    points.extend(roots.into_iter().map(|x| Pt::Aff(x, f.zero())));
    points.sort_by_key(|p| point_key(*p));
    points.dedup();
    assert_eq!(points.len(), 4);
    for p in &points {
        assert!(curve::on_curve(f, e, p));
        assert_eq!(curve::pmul(f, e, p, 2), Pt::Inf);
    }
    points
}

fn old_known_answer(c: &CheckedInstance) -> Value {
    let basis = AdapterV2::new(c).unwrap();
    let iso = OddSourceIsogeny::construct(c);
    let old_source = original_models::SourceE::degree13_target(c, &iso);
    let source = SourceE::degree13_target(c, &iso);
    let (mut old_all, old_summary) = original_models::construct_all(&old_source, &basis);
    let (mut all, summary) = construct_all(&source, &basis);
    let rows: Vec<_> = all.iter().map(|m| m.row.clone()).collect();
    assert_eq!(
        rows,
        old_all.iter().map(|m| m.row.clone()).collect::<Vec<_>>()
    );
    assert_eq!(old_summary, summary);
    let old_model = old_all.remove(
        old_all
            .iter()
            .position(|m| (m.root_index, m.sign_index) == (1, 0))
            .unwrap(),
    );
    let model = all.remove(
        all.iter()
            .position(|m| (m.root_index, m.sign_index) == (1, 0))
            .unwrap(),
    );
    let old =
        original::NormNew::new(original::Adapter::new(&old_source, &basis, old_model).unwrap())
            .unwrap();
    let new = NormNew::new(Adapter::new(&source, &basis, model).unwrap()).unwrap();
    let (mut old_all, _) = original_models::construct_all(&old_source, &basis);
    let (mut all, _) = construct_all(&source, &basis);
    let old_model = old_all.remove(
        old_all
            .iter()
            .position(|m| (m.root_index, m.sign_index) == (1, 0))
            .unwrap(),
    );
    let model = all.remove(
        all.iter()
            .position(|m| (m.root_index, m.sign_index) == (1, 0))
            .unwrap(),
    );
    let old2 = chained_n4_beta_complete_evaluator::BaseChanged::new(
        original::Adapter::new(&old_source, &basis, old_model).unwrap(),
    )
    .unwrap();
    let new2 = quadratic::BaseChanged::new(Adapter::new(&source, &basis, model).unwrap()).unwrap();
    assert_eq!(old.a.core.quartic, new.a.core.quartic);
    assert_eq!(old.a.core.omi, new.a.core.omi);
    assert_eq!(old.a.origin_shift(), new.a.origin_shift());
    assert_eq!(old.a.model_tag, new.a.model_tag);
    assert_eq!(old.model_tag, new.model_tag);
    assert_eq!(old.offset, new.offset);
    assert_eq!(old2.origin, new2.origin);
    assert_eq!(old2.origin_trace_calls(), 1);
    assert_eq!(new2.origin_trace_calls(), 1);
    let old_offsets = old.line_offsets().unwrap();
    let offsets = new.line_offsets().unwrap();
    assert_eq!(old_offsets.len(), 224);
    assert_eq!(old_offsets, offsets);
    let mut points = torsion(&source);
    for n in [0, 1, 2, 17, 12345, c.inst.ell - 1] {
        points.push(curve::pmul(
            source.field(),
            source.curve(),
            &source.generator(),
            n as u128,
        ));
    }
    let mut packets = Vec::new();
    for p in points {
        let d = old.a.transfer_point(&kp(p)).unwrap();
        let e = new.a.transfer_point(&kp(p)).unwrap();
        assert_eq!(d, e);
        assert_eq!(old.norm(&d).unwrap(), new.norm(&e).unwrap());
        assert_eq!(
            serde_json::to_value(old.encode(&d)).unwrap(),
            serde_json::to_value(new.encode(&e)).unwrap()
        );
        let d2 = old2.transfer(lift(p)).unwrap();
        let e2 = new2.transfer(lift(p)).unwrap();
        assert_eq!(d2, e2);
        assert_eq!(quadratic::descend_class(&e2).unwrap(), e);
        packets.push(json!({"point":point_json(p),"prime_key":d.key().0,"quadratic_key":d2.key().0,"norm":old.norm(&d).unwrap()}));
    }
    json!({"all_six_original_and_derivative_rows":rows,"whole_original_product_summary":summary,"all224_original_and_derivative_line_offsets":offsets.iter().map(|p|point_json(*p)).collect::<Vec<_>>(),"prime_origin":new.a.origin_shift().key().0,"separate_quadratic_origin":new2.origin.key().0,"all_actual_packets":packets,"original_identity_label":old_source.identity(),"declared_generalized_identity_label":source.identity(),"scope":"original and nominal derivative literal-module parity, with identity description difference explicitly retained"})
}

fn panic_text(error: Box<dyn std::any::Any + Send>) -> String {
    if let Some(s) = error.downcast_ref::<String>() {
        s.clone()
    } else if let Some(s) = error.downcast_ref::<&str>() {
        (*s).to_owned()
    } else {
        "nonstring panic payload".to_owned()
    }
}

#[test]
fn whole_old_parity_and_all_three_fixed_geometry_models() {
    let c = CheckedInstance::construct().unwrap();
    println!("N4_CHAIN_OLD_LITERAL_PARITY {}", old_known_answer(&c));
    let geometry = FixedGeometry::construct(&c).unwrap();
    println!(
        "N4_CHAIN_ACTUAL_ELLIPTIC_CERTIFICATES {}",
        geometry.map_certificates
    );
    let fixtures =
        std::path::PathBuf::from(std::env::var("N4_ORIGINAL_FULL_MODEL_FIXTURES").unwrap());
    let mut whole_parity = Vec::new();
    for (i, model) in geometry.models.iter().enumerate() {
        let original: Value = serde_json::from_slice(
            &std::fs::read(fixtures.join(format!("originalE{}-whole-six-rows.json", i + 2)))
                .unwrap(),
        )
        .unwrap();
        assert_eq!(
            json!(model.all_six_rows),
            original["all_six_whole_rows"],
            "all18 original census rows required"
        );
        whole_parity.push(json!({"domain":i,"all_six_whole_original_rows":original,"all_six_actual_runtime_rows":model.all_six_rows}));
    }
    println!(
        "N4_ORIGINAL_FULL_CENSUS_PARITY {}",
        json!({"all_three_whole_parities":whole_parity,"all18_equal":true})
    );
    let basis = AdapterV2::new(&c).unwrap();
    for (i, model) in geometry.models.iter().enumerate() {
        let source = &model.source;
        let norm = &model.prime;
        assert_eq!(source.ell(), ELL);
        assert_eq!(source.order(), ORDER);
        assert_eq!(norm.a.ell, ELL);
        assert_eq!(norm.a.expected_order as u128, ORDER);
        assert_eq!(norm.a.source_ec, *source.curve());
        assert_eq!(norm.a.kernel_mask, MASKS[i]);
        assert_eq!(norm.a.candidate, CASES[i]);
        let offsets = norm.line_offsets().unwrap();
        assert_eq!(offsets.len(), 224);
        assert!(offsets.iter().all(|x| *x == norm.offset));
        assert_eq!(model.quadratic.origin_trace_calls(), 1);
        let mut fibres: BTreeMap<[u32; 19], Vec<Value>> = BTreeMap::new();
        let mut controls = Vec::new();
        for p in torsion(source).into_iter().chain([
            source.generator(),
            curve::pmul(source.field(), source.curve(), &source.generator(), 17),
        ]) {
            let d = norm.a.transfer_point(&kp(p)).unwrap();
            let q = norm.norm(&d).unwrap();
            let expected = curve::pmul(source.field(), source.curve(), &p, 2);
            assert_eq!(q, kp(expected));
            let d2 = model.quadratic.transfer(lift(p)).unwrap();
            assert_eq!(quadratic::descend_class(&d2).unwrap(), d);
            if curve::pmul(source.field(), source.curve(), &p, 2) == Pt::Inf {
                fibres.entry(d.key().0).or_default().push(point_json(p));
            }
            controls.push(json!({"point":point_json(p),"Phi":d.key().0,"quadratic_Phi":d2.key().0,"actual_norm":q,"independent_double":point_json(expected)}));
        }
        let fibre_rows: Vec<_> = fibres
            .iter()
            .map(|(key, points)| json!({"key":key,"all_actual_preimages":points}))
            .collect();
        // Print the complete observation before checking the frozen criterion.
        println!(
            "N4_CHAIN_FIXED_GEOMETRY {}",
            json!({"index":i,"source":source.identity(),"all_six_rows":model.all_six_rows,"whole_product_summary":model.product_summary,"mask":MASKS[i],"case":CASES[i],"all224_line_offsets":offsets.iter().map(|p|point_json(*p)).collect::<Vec<_>>(),"separate_prime_origin":norm.a.origin_shift().key().0,"separate_quadratic_origin":model.quadratic.origin.key().0,"quadratic_origin_calls":model.quadratic.origin_trace_calls(),"all_point_controls":controls,"all_correction_fibres":fibre_rows})
        );
        assert_eq!(
            fibres.len(),
            2,
            "retain a different actual correction structure without model reselection"
        );
        assert!(fibres.values().all(|p| p.len() == 2));
        let wrong_order = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            SourceE::paired_source(
                &c,
                *source.curve(),
                ELL,
                ORDER + 1,
                source.generator(),
                source.source_tag(),
            )
        }))
        .err()
        .map(panic_text)
        .expect("wrong order accepted");
        let wrong_prime = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            SourceE::paired_source(
                &c,
                *source.curve(),
                2_771_711,
                ORDER,
                source.generator(),
                source.source_tag(),
            )
        }))
        .err()
        .map(panic_text)
        .expect("foreign prime accepted");
        let (mut all, _) = construct_all(source, &basis);
        let wrong_mask = take_fixed_model(&mut all, i, MASKS[i] ^ 2)
            .err()
            .expect("foreign mask accepted");
        let other = &geometry.models[(i + 1) % 3].source;
        let (mut all, _) = construct_all(other, &basis);
        let other_model = take_fixed_model(&mut all, (i + 1) % 3, MASKS[(i + 1) % 3]).unwrap();
        let wrong_source = Adapter::new(source, &basis, other_model)
            .err()
            .expect("foreign source accepted");
        let zero_generator = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            SourceE::paired_source(
                &c,
                *source.curve(),
                ELL,
                ORDER,
                Pt::Inf,
                source.source_tag(),
            )
        }))
        .err()
        .map(panic_text)
        .expect("zero generator accepted");
        let point_packet = norm.a.encode(kp(source.generator()));
        let mut bad = point_packet.clone();
        bad.field.push_str("foreign");
        let foreign_point_field = norm.a.decode(&bad).unwrap_err();
        let mut bad = point_packet;
        bad.model.push_str("foreign");
        let foreign_point_model = norm.a.decode(&bad).unwrap_err();
        let actual_class = norm.a.transfer_point(&kp(source.generator())).unwrap();
        let class_packet = norm.encode(&actual_class);
        let mut bad = class_packet.clone();
        bad.field.push_str("foreign");
        let foreign_class_field = norm.decode(&bad).unwrap_err();
        let mut bad = class_packet;
        bad.model.push_str("foreign");
        let foreign_class_model = norm.decode(&bad).unwrap_err();
        let altered_curve = curve::Curve::new(
            source.curve().a,
            source.field().add(source.curve().b, source.field().one()),
        );
        assert!(!curve::on_curve(
            source.field(),
            &altered_curve,
            &source.generator()
        ));
        let foreign_curve = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            SourceE::paired_source(
                &c,
                altered_curve,
                ELL,
                ORDER,
                source.generator(),
                source.source_tag(),
            )
        }))
        .err()
        .map(panic_text)
        .expect("altered curve accepted");
        println!(
            "N4_CHAIN_ACTUAL_REJECTIONS {}",
            json!({"index":i,"wrong_order":wrong_order,"foreign_prime":wrong_prime,"foreign_mask":wrong_mask,"foreign_source":wrong_source,"zero_generator":zero_generator,"foreign_point_field":foreign_point_field,"foreign_point_model":foreign_point_model,"foreign_class_field":foreign_class_field,"foreign_class_model":foreign_class_model,"altered_curve":foreign_curve})
        );
    }
}
