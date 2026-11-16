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

fn direct_case(
    d: &crate::direct::DirectNormHalving,
    s: &StrongScalarBaseline,
    side: usize,
    x: &PicClass,
) -> (PicClass, Value) {
    let b = s.reference();
    d.reset_calls();
    s.reset_calls();
    let (field, model, key, y, reference) = if side == 0 {
        let input = b.old().encode(x);
        let out = d.forward(&input).unwrap();
        let baseline = s.forward(&input).unwrap();
        let original = b.forward(&input).unwrap();
        assert_eq!(out.key, baseline.key);
        assert_eq!(out.key, original.key);
        assert_eq!(out.field, original.field);
        assert_eq!(out.model, original.model);
        (
            input.field,
            input.model,
            input.key,
            b.new().decode(&out).unwrap(),
            original.key,
        )
    } else {
        let input = b.new().encode(x);
        let out = d.dual(&input).unwrap();
        let baseline = s.dual(&input).unwrap();
        let original = b.dual(&input).unwrap();
        assert_eq!(out.key, baseline.key);
        assert_eq!(out.key, original.key);
        assert_eq!(out.field, original.field);
        assert_eq!(out.model, original.model);
        (
            input.field,
            input.model,
            input.key,
            b.old().decode(&out).unwrap(),
            original.key,
        )
    };
    let online = d.calls();
    assert_eq!(online.common_packet_parse, 1);
    assert_eq!(online.common_complete_norm_and_geometry_admission, 1);
    assert_eq!(online.common_full_group_order_scalar, 1);
    assert_eq!(online.transfer_quadratic_source_phi, 1);
    assert_eq!(online.transfer_source_isogeny, 1);
    assert_eq!(online.transfer_quadratic_target_phi, 1);
    assert_eq!(online.transfer_two_torsion_lookup, 1);
    assert_eq!(online.transfer_final_addition, 1);
    assert_eq!(online.full_inverse_jacobian_scalar, 0);
    assert_eq!(
        online.transfer_quartic_root_factorization
            + online.transfer_infinity_half_dictionary
            + online.transfer_literal_two_torsion_selector,
        1
    );
    let baseline_calls = s.calls();
    let (back, inverse_roundtrip) = if side == 0 {
        let out = b.new().encode(&y);
        let back = b.old().decode(&d.dual(&out).unwrap()).unwrap();
        let inverse = b.old().decode(&d.inverse(&out).unwrap()).unwrap();
        (back, inverse)
    } else {
        let back = b
            .new()
            .decode(&d.forward(&b.old().encode(&y)).unwrap())
            .unwrap();
        let inverse = d.inverse(&b.new().encode(x)).unwrap();
        let roundtrip = b.new().decode(&d.forward(&inverse).unwrap()).unwrap();
        (back, roundtrip)
    };
    let pic = if side == 0 {
        &b.old().a.pic
    } else {
        &b.new().a.pic
    };
    assert_eq!(back, pic.mul_scalar(x, 13));
    assert_eq!(&inverse_roundtrip, x);
    d.reset_calls();
    let diagnostic = d.diagnose_all_lifts(side, &field, &model, &key).unwrap();
    let rows = diagnostic["all4"].as_array().unwrap();
    assert_eq!(rows.len(), 4);
    for row in rows {
        assert_eq!(row["image"], json!(y.key().0.to_vec()));
    }
    let wrong_omissions = rows
        .iter()
        .filter(|row| row["psi_half"] != row["image"])
        .count();
    assert_eq!(
        wrong_omissions, 2,
        "two of four halves require actual nonzero correction"
    );
    let row = json!({"side":side,"input":x.key().0.to_vec(),"image":y.key().0.to_vec(),"strong_and_complete_reference":reference.to_vec(),"both_new_maps_composition":back.key().0.to_vec(),"full_new_inverse_roundtrip":inverse_roundtrip.key().0.to_vec(),"runtime_selected_calls":online,"baseline_runtime_selected_calls":baseline_calls,"all_four_lifts_and_actual_corrections":diagnostic,"omitting_nonzero_correction_wrong_on_exactly_two_halves":wrong_omissions});
    (y, row)
}

#[test]
fn complete_norm_halving_all_exceptionals_lifts_sectors_and_publics() {
    use crate::direct::DirectNormHalving;
    let c = CheckedInstance::construct().unwrap();
    assert!(DirectNormHalving::with_candidate(&c, (1, 1)).is_err());
    assert!(DirectNormHalving::with_candidate(&c, (2, 1)).is_err());
    let d = DirectNormHalving::construct(&c).unwrap();
    let s = StrongScalarBaseline::construct(&c).unwrap();
    let b = s.reference();
    assert_eq!(d.old().model_tag, b.old().model_tag);
    assert_eq!(d.new().model_tag, b.new().model_tag);
    let mut exceptionals = Vec::new();
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
            if i % 16 == 0 {
                eprintln!("direct norm-halving exceptional side{side}/input{i}");
            }
            let (_, row) = direct_case(&d, &s, side, &pic.exceptional(point));
            rows.push(json!({"point":point,"case":row}));
        }
        exceptionals.push(json!({"side":side,"all224":rows}));
    }
    let source = SourceE::original(&c);
    let g = b.old().a.transfer_point(&kp(source.generator())).unwrap();
    let gy = b
        .new()
        .decode(&b.forward(&b.old().encode(&g)).unwrap())
        .unwrap();
    let mut mixed = Vec::new();
    let mut inputs = [Vec::new(), Vec::new()];
    let mut outputs = [Vec::new(), Vec::new()];
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
                let (y, row) = direct_case(&d, &s, side, &x);
                inputs[side].push(x);
                outputs[side].push(y);
                mixed.push(json!({"scalar_OUTSIDE_runtime":scalar,"sector":sector,"case":row}));
            }
        }
    }
    assert_eq!(mixed.len(), 48);
    let mut additions = Vec::new();
    for side in 0..2 {
        let pic = if side == 0 {
            &b.old().a.pic
        } else {
            &b.new().a.pic
        };
        let target = if side == 0 {
            &b.new().a.pic
        } else {
            &b.old().a.pic
        };
        for i in 0..24 {
            for offset in [7, 11] {
                let j = (i + offset) % 24;
                let x = pic.add(&inputs[side][i], &inputs[side][j]);
                let (y, row) = direct_case(&d, &s, side, &x);
                assert_eq!(y, target.add(&outputs[side][i], &outputs[side][j]));
                additions.push(json!({"side":side,"i":i,"j":j,"case":row}));
            }
        }
    }
    assert_eq!(additions.len(), 96);
    let requests = c
        .parse(include_bytes!("../../fixtures/public-five.json"))
        .unwrap();
    let mut publics = Vec::new();
    for (i, raw) in requests.into_iter().enumerate() {
        let q = match raw {
            EP::Inf => Pt::Inf,
            EP::A(x, y) => Pt::Aff(c.independent_field.add(er(x), er(c.short_shift)), er(y)),
        };
        let x0 = b.old().a.transfer_point(&kp(q)).unwrap();
        let y0 = b
            .new()
            .decode(&d.forward(&b.old().encode(&x0)).unwrap())
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
                let (_, row) = direct_case(&d, &s, side, &x);
                publics.push(json!({"public_target":i,"sector":sector,"case":row}));
            }
        }
    }
    assert_eq!(publics.len(), 40);
    let mut bad = b.old().encode(&g);
    bad.model.push_str("-foreign-origin");
    assert!(d.forward(&bad).is_err());
    let mut bad = b.old().encode(&g);
    bad.field.push_str("-foreign");
    assert!(d.forward(&bad).is_err());
    let mut bad = b.old().encode(&g);
    bad.key[0] = 2;
    assert!(d.forward(&bad).is_err());
    println!(
        "N4_NORM_HALVING_COMPLETE {}",
        json!({"protocol":"6dc948","all448_exceptionals":exceptionals,"all48_mixed":mixed,"all96_addition_pairs":additions,"all40_public_sector_directions":publics,"actual_two_torsion_dictionaries":[d.correction_dictionary(0),d.correction_dictionary(1)],"actual_selected_setup_calls":d.setup(),"fixed_L_order_from_existing_E_K_order_input":d.quadratic_order_from_existing_input(),"field_pole_scope":"existingcurveorder plusstandardquadraticorderformula imply13doesnotdivide#E(L); frozenactualrationalisogeny usedonlyonthisfield, notageneralpolehandler","counter_scope":"selectedentrycalls only; everycontext/constructor/primitive/verificationcost INCLUDED andUNPRICED; actualfullinverse stillhaslargeJacobianinverse13scalar","scope":"finitecomplete-rationalnormhalving/everyhalfcorrection/fullnew13andinverse; no timing/calibratedcost/advantage orformalactualgeometry claim"})
    );
}

fn unlift_point(p: Pt<ER>) -> Pt<ER> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => {
            assert!(x.iter().chain(y.iter()).enumerate().all(|(i, &v)| {
                if i % 16 < 6 && (i % 16) % 2 == 0 {
                    true
                } else {
                    v == 0
                }
            }));
            let mut a = [0; 16];
            let mut b = [0; 16];
            for i in 0..3 {
                a[i] = x[2 * i];
                b[i] = y[2 * i]
            }
            Pt::Aff(a, b)
        }
    }
}

#[test]
fn all_halving_coordinate_branches_against_literal_original_selector() {
    use crate::direct::{generic_half, halving_quartic, lift_point, DirectNormHalving};
    use chained_n4_beta_rational_lift::{four_torsion, frob_point, point_json, point_key};
    use isogeny_algos::{field::Rng, poly};
    let c = CheckedInstance::construct().unwrap();
    let d = DirectNormHalving::construct(&c).unwrap();
    let iso = OddSourceIsogeny::construct(&c);
    let curves = [iso.source(), iso.target()];
    let mut panels = Vec::new();
    let mut naive_offcurve = 0;
    let mut non_k = 0;
    for side in 0..2 {
        let a = d.quadratic(side);
        let f = &a.f;
        let e = &a.curve;
        let four = four_torsion(&c.independent_field, f, curves[side]);
        let two = four
            .iter()
            .copied()
            .filter(|p| curve::pmul(f, e, p, 2) == Pt::Inf)
            .collect::<Vec<_>>();
        assert_eq!(two.len(), 4);
        let generator = if side == 0 {
            SourceE::original(&c).generator()
        } else {
            iso.forward(SourceE::original(&c).generator()).unwrap()
        };
        let mut qs = two.iter().copied().map(unlift_point).collect::<Vec<_>>();
        for scalar in [1u128, 2, 7, 17, ELL as u128 - 1] {
            let p = curve::pmul(&c.independent_field, curves[side], &generator, scalar);
            for t in &two {
                qs.push(curve::padd(
                    &c.independent_field,
                    curves[side],
                    &p,
                    &unlift_point(*t),
                ))
            }
        }
        qs.sort_by_key(|p| point_key(*p));
        qs.dedup();
        assert_eq!(qs.len(), 24);
        let mut rows = Vec::new();
        for q3 in qs {
            let q = lift_point(q3);
            let mut actual = d.halves_of_norm(side, q3).unwrap();
            let mut oracle = crate::literal_halves::literal_halves(f, e, q, &two);
            actual.sort_by_key(|p| point_key(*p));
            oracle.sort_by_key(|p| point_key(*p));
            assert_eq!(actual, oracle);
            for p in &actual {
                assert_eq!(frob_point(f, *p, 6), *p);
                assert_eq!(curve::pmul(f, e, p, 2), q);
                assert!(actual.contains(&frob_point(f, *p, 3)));
                if frob_point(f, *p, 3) != *p {
                    non_k += 1
                }
                if !curve::on_curve(f, e, &frob_point(f, *p, 1)) {
                    naive_offcurve += 1
                }
            }
            let mut wrong_control = Value::Null;
            if let Pt::Aff(u, v) = q {
                if f.is_zero(v) {
                    assert!(generic_half(
                        f,
                        e,
                        q,
                        actual
                            .iter()
                            .find_map(|p| if let Pt::Aff(x, _) = p {
                                Some(*x)
                            } else {
                                None
                            })
                            .unwrap()
                    )
                    .is_err())
                } else {
                    let mut wrong = halving_quartic(f, e, u);
                    wrong[0] = f.add(wrong[0], f.one());
                    let roots = poly::roots(f, &wrong, &mut Rng::new(0x74bad));
                    assert!(roots.iter().all(|&x| generic_half(f, e, q, x).is_err()));
                    wrong_control = json!({"constant_plus_one_quartic":wrong.iter().map(|x|x[..6].to_vec()).collect::<Vec<_>>(),"all_actual_wrong_roots":roots.iter().map(|x|x[..6].to_vec()).collect::<Vec<_>>(),"each_wrongroot_rejected":true});
                }
            } else {
                assert!(generic_half(f, e, q, f.zero()).is_err())
            }
            rows.push(json!({"Q":point_json(q),"all4_literal_and_fast_agree":actual.iter().copied().map(point_json).collect::<Vec<_>>(),"wrong_polynomial_control":wrong_control}));
        }
        panels.push(json!({"side":side,"all24_targets":rows}));
    }
    assert!(non_k > 0 && naive_offcurve > 0);
    println!(
        "N4_NORM_HALVING_COORDINATES {}",
        json!({"all48_norm_targets":panels,"actual_non_K_halves":non_k,"naive_coordinate_F_offcurve":naive_offcurve,"F3_preserves_all_halving_fibres":true,"literal_original_oracle":"literal-halves-provenance.json; bodyunchangedexceptnamevisibility","scope":"actualcompleteinfinity/two-torsion/genericquarticbranches; no speed orfullprimitivecost claim"})
    );
}

#[test]
fn wrong_origin_subtraction_fails_independent_odd_validation() {
    use crate::direct::DirectNormHalving;
    let c = CheckedInstance::construct().unwrap();
    let s = StrongScalarBaseline::construct(&c).unwrap();
    let b = s.reference();
    let mut rows = Vec::new();
    for side in 0..2 {
        let mut d = DirectNormHalving::construct(&c).unwrap();
        let pic = if side == 0 {
            &b.old().a.pic
        } else {
            &b.new().a.pic
        };
        let target = if side == 0 {
            &b.new().a.pic
        } else {
            &b.old().a.pic
        };
        let zero = pic.zero();
        let good = if side == 0 {
            b.new()
                .decode(&d.forward(&b.old().encode(&zero)).unwrap())
                .unwrap()
        } else {
            b.old()
                .decode(&d.dual(&b.new().encode(&zero)).unwrap())
                .unwrap()
        };
        assert!(target.is_zero(&good));
        let change = d.shift_origin_for_control(side).unwrap();
        let bad = if side == 0 {
            b.new()
                .decode(&d.forward(&b.old().encode(&zero)).unwrap())
                .unwrap()
        } else {
            b.old()
                .decode(&d.dual(&b.new().encode(&zero)).unwrap())
                .unwrap()
        };
        assert_ne!(bad, good);
        let residue = target.mul_scalar(&bad, ELL as u128);
        assert!(
            !target.is_zero(&residue),
            "original odd-subgroup validation must reject the wrong-origin result"
        );
        if side == 0 {
            assert!(b.recover_source_odd(&b.new().encode(&bad)).is_err())
        }
        rows.push(json!({"change":change,"zero_input":zero.key().0.to_vec(),"correct_image":good.key().0.to_vec(),"wrong_image":bad.key().0.to_vec(),"independent_original_odd_membership_residue":residue.key().0.to_vec(),"independent_validation_rejected":true}));
    }
    println!(
        "N4_NORM_HALVING_WRONG_ORIGIN {}",
        json!({"both_actual_shifted_origin_controls":rows,"scope":"intentional cfg(test) origin-subtraction corruption; no corrupt production context or omitted primitive work"})
    );
}
