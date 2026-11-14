use super::*;
use crate::complete::CompleteBeta;
use chained_n4_beta_rational_lift::point_json;
use chained_n4_odd_product_models::SourceE;
use chained_n4_public_target::{ghs::EP, CheckedInstance};
use serde_json::{json, Value};

fn kp(p: Pt<ER>) -> Option<([u64; 3], [u64; 3])> {
    match p {
        Pt::Inf => None,
        Pt::Aff(x, y) => Some(([x[0], x[1], x[2]], [y[0], y[1], y[2]])),
    }
}
#[test]
fn complete_rational_beta_all_sectors_both13_and_public_targets() {
    let c = CheckedInstance::construct().unwrap();
    assert!(CompleteBeta::with_candidate(&c, (1, 1)).is_err());
    assert!(CompleteBeta::with_candidate(&c, (2, 1)).is_err());
    let b = CompleteBeta::construct(&c).unwrap();
    let old = &b.old().a.pic;
    let new = &b.new().a.pic;
    let source = SourceE::original(&c);
    let sg = source.generator();
    let g = b.old().a.transfer_point(&kp(sg)).unwrap();
    assert!(!old.is_zero(&g));
    assert!(old.is_zero(&old.mul_scalar(&g, 2773073)));
    let gy = b
        .new()
        .decode(&b.forward(&b.old().encode(&g)).unwrap())
        .unwrap();
    assert!(!new.is_zero(&gy));
    assert!(new.is_zero(&new.mul_scalar(&gy, 2773073)));
    let cof = [b.cofactor_pairs(0).unwrap(), b.cofactor_pairs(1).unwrap()];
    let mut panels = Vec::new();
    let mut inputs = [Vec::new(), Vec::new()];
    let mut outputs = [Vec::new(), Vec::new()];
    let scalars = [0, 1, 2, 7, 17, 2773072u128];
    for side in 0..2 {
        let p = if side == 0 { old } else { new };
        let target = if side == 0 { new } else { old };
        let generator = if side == 0 { &g } else { &gy };
        let mut rows = Vec::new();
        for scalar in scalars {
            let odd = p.mul_scalar(generator, scalar);
            for (sector, (t, _)) in cof[side].iter().enumerate() {
                let x = p.add(&odd, t);
                let y = if side == 0 {
                    b.new()
                        .decode(&b.forward(&b.old().encode(&x)).unwrap())
                        .unwrap()
                } else {
                    b.old()
                        .decode(&b.dual(&b.new().encode(&x)).unwrap())
                        .unwrap()
                };
                let back = if side == 0 {
                    b.old()
                        .decode(&b.dual(&b.new().encode(&y)).unwrap())
                        .unwrap()
                } else {
                    b.new()
                        .decode(&b.forward(&b.old().encode(&y)).unwrap())
                        .unwrap()
                };
                assert_eq!(back, p.mul_scalar(&x, 13));
                let twice = if side == 0 {
                    let a = b.old().norm(&x).unwrap();
                    let p = match a {
                        None => Pt::Inf,
                        Some((x, y)) => Pt::Aff(
                            chained_n4_odd_product_models::er(x),
                            chained_n4_odd_product_models::er(y),
                        ),
                    };
                    let q = chained_n4_odd_source::OddSourceIsogeny::construct(&c)
                        .forward(p)
                        .unwrap();
                    b.new().a.transfer_point(&kp(q)).unwrap()
                } else {
                    let a = b.new().norm(&x).unwrap();
                    let p = match a {
                        None => Pt::Inf,
                        Some((x, y)) => Pt::Aff(
                            chained_n4_odd_product_models::er(x),
                            chained_n4_odd_product_models::er(y),
                        ),
                    };
                    let q = chained_n4_odd_source::OddSourceIsogeny::construct(&c)
                        .dual(p)
                        .unwrap();
                    b.old().a.transfer_point(&kp(q)).unwrap()
                };
                assert_eq!(target.double(&y), twice);
                let round = if side == 0 {
                    b.old()
                        .decode(&b.inverse(&b.new().encode(&y)).unwrap())
                        .unwrap()
                } else {
                    let pre = b
                        .old()
                        .decode(&b.inverse(&b.new().encode(&x)).unwrap())
                        .unwrap();
                    b.new()
                        .decode(&b.forward(&b.old().encode(&pre)).unwrap())
                        .unwrap()
                };
                assert_eq!(round, x);
                rows.push(json!({"odd_scalar_OUTSIDE_runtime":scalar,"cofactor_sector":sector,"input":x.key().0.to_vec(),"image":y.key().0.to_vec(),"dual_composition":back.key().0.to_vec(),"original_F_or_G":twice.key().0.to_vec(),"full_group_inverse":round.key().0.to_vec()}));
                inputs[side].push(x);
                outputs[side].push(y);
            }
        }
        panels.push(json!({"side":side,"all24_mixed_inputs":rows}));
    }
    let mut addition = Vec::new();
    for side in 0..2 {
        let p = if side == 0 { old } else { new };
        let target = if side == 0 { new } else { old };
        for i in 0..24 {
            for offset in [7, 11] {
                let j = (i + offset) % 24;
                let x = p.add(&inputs[side][i], &inputs[side][j]);
                let y = if side == 0 {
                    b.new()
                        .decode(&b.forward(&b.old().encode(&x)).unwrap())
                        .unwrap()
                } else {
                    b.old()
                        .decode(&b.dual(&b.new().encode(&x)).unwrap())
                        .unwrap()
                };
                assert_eq!(y, target.add(&outputs[side][i], &outputs[side][j]));
                addition.push(json!({"side":side,"i":i,"j":j,"sum":x.key().0.to_vec(),"mapped_sum":y.key().0.to_vec()}));
            }
        }
    }
    let requests = c
        .parse(include_bytes!("../../fixtures/public-five.json"))
        .unwrap();
    assert_eq!(requests.len(), 5);
    let answers: Vec<Value> =
        serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
            .unwrap();
    let mut publics = Vec::new();
    for (i, raw) in requests.into_iter().enumerate() {
        let q = match raw {
            EP::Inf => Pt::Inf,
            EP::A(x, y) => Pt::Aff(
                c.independent_field.add(
                    chained_n4_odd_product_models::er(x),
                    chained_n4_odd_product_models::er(c.short_shift),
                ),
                chained_n4_odd_product_models::er(y),
            ),
        };
        let scalar = answers[i]["original_native_recovered_scalar"]
            .as_u64()
            .unwrap();
        assert!(c.verify_recovered(raw, scalar));
        assert_eq!(
            curve::pmul(
                &c.independent_field,
                &c.independent_curve,
                &sg,
                scalar as u128
            ),
            q
        );
        let x0 = b.old().a.transfer_point(&kp(q)).unwrap();
        let y0 = b
            .new()
            .decode(&b.forward(&b.old().encode(&x0)).unwrap())
            .unwrap();
        assert_eq!(y0, new.mul_scalar(&gy, scalar as u128));
        assert_eq!(b.recover_source_odd(&b.new().encode(&y0)).unwrap(), q);
        for (sector, (t, _)) in cof[0].iter().enumerate() {
            let x = old.add(&x0, t);
            let y = b
                .new()
                .decode(&b.forward(&b.old().encode(&x)).unwrap())
                .unwrap();
            let back = b
                .old()
                .decode(&b.dual(&b.new().encode(&y)).unwrap())
                .unwrap();
            assert_eq!(back, old.mul_scalar(&x, 13));
            assert_eq!(
                b.old()
                    .decode(&b.inverse(&b.new().encode(&y)).unwrap())
                    .unwrap(),
                x
            );
            if !old.is_zero(t) {
                assert!(b.recover_source_odd(&b.new().encode(&y)).is_err());
            }
            publics.push(json!({"public_index":i,"source_Q":point_json(q),"outside_runtime_scalar":scalar,"cofactor_sector":sector,"input":x.key().0.to_vec(),"beta":y.key().0.to_vec(),"betaDual_beta":back.key().0.to_vec(),"odd_source_recovery_on_zero_sector_only":true}));
        }
    }
    let mut wrong = b.old().encode(&old.zero());
    wrong.field.push('x');
    assert!(b.forward(&wrong).is_err());
    let mut wrong = b.old().encode(&old.zero());
    wrong.model.push('x');
    assert!(b.forward(&wrong).is_err());
    let mut wrong = b.old().encode(&old.zero());
    wrong.key[1] = 223;
    assert!(b.forward(&wrong).is_err());
    let mut wrong = b.old().encode(&old.zero());
    wrong.key[0] = 2;
    assert!(b.forward(&wrong).is_err());
    let mut wrong = b.new().encode(&new.zero());
    wrong.model.push('x');
    assert!(b.dual(&wrong).is_err());
    assert!(b.inverse(&wrong).is_err());
    println!(
        "N4_BETA_COMPLETE_RATIONAL {}",
        json!({"protocol":"5be5e0/32283c","candidate":[1,0],"ell":2773073,"rational_order":11092292,"old_model":b.old().model_tag,"new_model":b.new().model_tag,"old_quartic":b.old().a.core.quartic,"old_P0":old.base_point(),"new_quartic":b.new().a.core.quartic,"new_P0":new.base_point(),"both4entry_cofactor_maps":cof.iter().map(|v|v.iter().map(|(x,y)|json!({"input":x.key().0.to_vec(),"image":y.key().0.to_vec()})).collect::<Vec<_>>()).collect::<Vec<_>>(),"all48_mixed_sector_rows":panels,"all96_addition_rows":addition,"all5publics_times4sectors":publics,"unmatched_kernel_rejections":2,"field_model_noncanonical_and_unknown_tag_rejections":6,"full_rational_inverse_scalar":3413013,"source_recovery_inverse26modell":319970,"inverse_identities_checked_in_constructor":true,"explicit_preprocessing":"32completeFp2fibre evaluations/32rational13isogenyevaluations on actualE4/eachside4entrytable; original prime andquadratic setup included in implementation, not cost-free","scope":"native finite controls and reusable full-rational evaluator under written geometric/order/kernel hypotheses; global closed coordinates/formalgeometry/calibratedcost remain open; no speedup or DLP attack claimed"})
    );
}
