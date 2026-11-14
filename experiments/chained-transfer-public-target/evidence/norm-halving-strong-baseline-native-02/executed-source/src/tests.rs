use super::*;
use chained_n4_odd_product_models::SourceE;
use chained_n4_public_target::ghs::EP;
use isogeny_algos::field::Field;
use serde_json::{json, Value};

fn run_case(s: &StrongScalarBaseline, side: usize, x: &PicClass) -> Value {
    let b = s.reference();
    s.reset_calls();
    let (y, expected, reference_decode) = if side == 0 {
        let packet = b.old().encode(x);
        let y = s.forward(&packet).unwrap();
        let expected = b.forward(&packet).unwrap();
        assert_eq!(y.key, expected.key);
        assert_eq!(y.field, expected.field);
        assert_eq!(y.model, expected.model);
        let decoded = b.new().decode(&y).unwrap();
        (decoded, expected.key, b.old().decode(&packet).unwrap())
    } else {
        let packet = b.new().encode(x);
        let y = s.dual(&packet).unwrap();
        let expected = b.dual(&packet).unwrap();
        assert_eq!(y.key, expected.key);
        assert_eq!(y.field, expected.field);
        assert_eq!(y.model, expected.model);
        let decoded = b.old().decode(&y).unwrap();
        (decoded, expected.key, b.new().decode(&packet).unwrap())
    };
    assert_eq!(&reference_decode, x);
    assert_eq!(
        s.calls(),
        Calls {
            common_packet_parse: 1,
            common_complete_norm_and_geometry_admission: 1,
            common_full_group_order_scalar: 1,
            transfer_jacobian_crt_projection: 1,
            transfer_elliptic_half_odd_scalar: 1,
            transfer_source_isogeny: 1,
            transfer_prime_field_phi: 1,
            transfer_cofactor_lookup: 1,
            transfer_final_subtraction: 1,
        }
    );
    let back = if side == 0 {
        b.old()
            .decode(&b.dual(&b.new().encode(&y)).unwrap())
            .unwrap()
    } else {
        b.new()
            .decode(&b.forward(&b.old().encode(&y)).unwrap())
            .unwrap()
    };
    let pic = if side == 0 {
        &b.old().a.pic
    } else {
        &b.new().a.pic
    };
    assert_eq!(back, pic.mul_scalar(x, 13));
    json!({"side":side,"input":x.key().0.to_vec(),"strong_baseline":y.key().0.to_vec(),"unchanged_complete_C":expected.to_vec(),"dual_composition":back.key().0.to_vec(),"actual_selected_calls":s.calls()})
}

#[test]
fn strongest_norm_assisted_scalar_baseline_all_declared_inputs() {
    let c = CheckedInstance::construct().unwrap();
    let s = StrongScalarBaseline::construct(&c).unwrap();
    let b = s.reference();
    let mut exceptional = Vec::new();
    for side in 0..2 {
        let pic = if side == 0 {
            &b.old().a.pic
        } else {
            &b.new().a.pic
        };
        let points = pic.rational_points_bruteforce();
        assert_eq!(points.len(), 224);
        let mut rows = Vec::new();
        for (i, point) in points.into_iter().enumerate() {
            if i % 32 == 0 {
                eprintln!("strong baseline exceptional side{side}/input{i}");
            }
            let x = pic.exceptional(point);
            rows.push(json!({"point":point,"case":run_case(&s,side,&x)}));
        }
        exceptional.push(json!({"side":side,"all224":rows}));
    }
    let source = SourceE::original(&c);
    let g = b.old().a.transfer_point(&kp(source.generator())).unwrap();
    let gy = b
        .new()
        .decode(&b.forward(&b.old().encode(&g)).unwrap())
        .unwrap();
    let mut mixed = Vec::new();
    for side in 0..2 {
        let pic = if side == 0 {
            &b.old().a.pic
        } else {
            &b.new().a.pic
        };
        let generator = if side == 0 { &g } else { &gy };
        for scalar in [0u128, 1, 2, 7, 17, ELL as u128 - 1] {
            let odd = pic.mul_scalar(generator, scalar);
            for (sector, (t, _)) in b.cofactor_pairs(side).unwrap().iter().enumerate() {
                let x = pic.add(&odd, t);
                mixed.push(json!({"scalar_OUTSIDE_runtime":scalar,"sector":sector,"case":run_case(&s,side,&x)}));
            }
        }
    }
    assert_eq!(mixed.len(), 48);
    let requests = c
        .parse(include_bytes!("../../fixtures/public-five.json"))
        .unwrap();
    assert_eq!(requests.len(), 5);
    let mut publics = Vec::new();
    for (i, raw) in requests.into_iter().enumerate() {
        let q = match raw {
            EP::Inf => Pt::Inf,
            EP::A(x, y) => Pt::Aff(c.independent_field.add(er(x), er(c.short_shift)), er(y)),
        };
        let x0 = b.old().a.transfer_point(&kp(q)).unwrap();
        let y0 = b
            .new()
            .decode(&s.forward(&b.old().encode(&x0)).unwrap())
            .unwrap();
        assert_eq!(b.recover_source_odd(&b.new().encode(&y0)).unwrap(), q);
        for side in 0..2 {
            let pic = if side == 0 {
                &b.old().a.pic
            } else {
                &b.new().a.pic
            };
            let point = if side == 0 { &x0 } else { &y0 };
            for (sector, (t, _)) in b.cofactor_pairs(side).unwrap().iter().enumerate() {
                let x = pic.add(point, t);
                publics
                    .push(json!({"public_target":i,"sector":sector,"case":run_case(&s,side,&x)}));
            }
        }
    }
    assert_eq!(publics.len(), 40);
    let (t, _) = b
        .cofactor_pairs(0)
        .unwrap()
        .into_iter()
        .find(|(x, _)| !b.old().a.pic.is_zero(x))
        .unwrap();
    let packet = b.old().encode(&t);
    let wrong = s
        .evaluate(0, &packet.field, &packet.model, &packet.key, false)
        .unwrap();
    let right = b.new().decode(&b.forward(&packet).unwrap()).unwrap();
    assert_ne!(
        wrong, right,
        "omitting cofactor subtraction must change actual result"
    );
    let mut bad = b.old().encode(&g);
    bad.model.push_str("-foreign");
    assert!(s.forward(&bad).is_err());
    let mut bad = b.old().encode(&g);
    bad.field.push_str("-foreign");
    assert!(s.forward(&bad).is_err());
    let mut bad = b.old().encode(&g);
    bad.key[0] = 2;
    assert!(s.forward(&bad).is_err());
    let mut bad = b.old().encode(&g);
    bad.key[3] = 223;
    assert!(s.forward(&bad).is_err());
    let mut bad = b.old().encode(&t);
    bad.key[0] = 0;
    bad.key[4] = 1;
    assert!(s.forward(&bad).is_err());
    println!(
        "N4_NORM_HALVING_STRONG_BASELINE {}",
        json!({"protocol":"6dc948 publishedd5db7698 beforecode","all448_exceptionals":exceptional,"all48_mixed":mixed,"all40_public_sector_directions":publics,"wrong_omitted_cofactor":{"input":t.key().0.to_vec(),"wrong":wrong.key().0.to_vec(),"right":right.key().0.to_vec()},"foreign_model_field_tag_coefficient_and_exceptional_trailing_controls_rejected":true,"constructor_complete_C_selected_calls":b.preprocessing_calls(),"constructor_other_work":"complete_C contexts/model/validation plus additional actualsourceisogeny construction INCLUDED and UNPRICED; no complete primitive ledger","common_admission":"literal packet parser; one unchangedpublicnorm retains validationnorm; fullORDER Jacobian admission scalar remains","optimized_transfer":"oneJacobianELLprojection; halfoddscalaronELLIPTICsource; actual13isogeny andoriginalprimefieldPhi; subtractactualcofactorimage","scope":"finite unfiltered correctness and actual selectedcallentries only; no fullprimitivecost/timing/advantage claim; directnormhalving candidate stillnext"})
    );
}
