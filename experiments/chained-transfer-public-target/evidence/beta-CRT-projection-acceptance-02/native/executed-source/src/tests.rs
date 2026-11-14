use super::*;
use chained_n4_beta_rational_lift::{four_torsion, frob_point, point_json, Rational6};
use chained_n4_odd_product_models::{construct_all, three, SourceE};
use chained_n4_odd_source::OddSourceIsogeny;
use chained_n4_public_target::CheckedInstance;
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

fn kp(p: Pt<ER>) -> Option<([u64; 3], [u64; 3])> {
    match p {
        Pt::Inf => None,
        Pt::Aff(x, y) => Some((three(x), three(y))),
    }
}
fn ext(p: Pt<ER>) -> Pt<ER> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => Pt::Aff(lift3(x), lift3(y)),
    }
}

#[test]
fn complete_quadratic_fibres_all_four_torsion_and_original_agreement() {
    let c = CheckedInstance::construct().unwrap();
    let iso = OddSourceIsogeny::construct(&c);
    let source = SourceE::degree13_target(&c, &iso);
    let original = SourceE::original(&c);
    let old = AdapterV2::new(&c).unwrap();
    let (models, _) = construct_all(&source, &old);
    let model = models
        .into_iter()
        .find(|m| (m.root_index, m.sign_index) == (1, 0))
        .unwrap();
    let new = Adapter::new(&source, &old, model).unwrap();
    assert_eq!(new.candidate, (1, 0));
    let mut original_checks = Vec::new();
    // Original K inputs are independent calls to the immutable adapters.
    let mut old_inputs = vec![Pt::Inf];
    let mut new_inputs = vec![Pt::Inf];
    for n in [1, 2, 3, 7, 17, 31] {
        old_inputs.push(curve::pmul(
            original.field(),
            original.curve(),
            &original.generator(),
            n,
        ));
        new_inputs.push(curve::pmul(
            source.field(),
            source.curve(),
            &source.generator(),
            n,
        ));
    }
    let mut old_expected = Vec::new();
    let mut new_expected = Vec::new();
    for p in &old_inputs {
        old_expected.push(old.transfer_point(&kp(*p)).unwrap());
    }
    for p in &new_inputs {
        new_expected.push(new.transfer_point(&kp(*p)).unwrap());
    }
    let old = BaseChanged::old(old).unwrap();
    let new = BaseChanged::new(new).unwrap();
    for (side, a, inputs, expected) in [
        (0, &old, &old_inputs, &old_expected),
        (1, &new, &new_inputs, &new_expected),
    ] {
        for (p, want) in inputs.iter().zip(expected) {
            let got = a.transfer(ext(*p)).unwrap();
            assert_eq!(got, embed_class(want));
            original_checks.push(json!({"side":side,"point":point_json(ext(*p)),"old_class":want.key().0.to_vec(),"quadratic_class":got.key().0.to_vec()}));
        }
    }
    let points = [
        four_torsion(&c.independent_field, &old.f, iso.source()),
        four_torsion(&c.independent_field, &new.f, iso.target()),
    ];
    let mut images = Vec::new();
    let mut panels = Vec::new();
    for (side, a) in [&old, &new].into_iter().enumerate() {
        let mut mapped = Vec::new();
        for (i, &p) in points[side].iter().enumerate() {
            eprintln!(
                "actual quadratic fibre side{side}/point{i} {}",
                point_json(p)
            );
            mapped.push(a.transfer(p).unwrap());
        }
        let mut rows = Vec::new();
        let mut nonbase = 0;
        let mut branches = 0;
        for (i, &p) in points[side].iter().enumerate() {
            let fp = frob_point(&a.f, p, 3);
            let fi = points[side].iter().position(|&x| x == fp).unwrap();
            assert_eq!(a.pic.frobenius_class(&mapped[i]), mapped[fi]);
            assert!(a.pic.is_zero(&a.pic.mul_scalar(&mapped[i], 4)));
            let rational = mapped[i].key().0.iter().all(|&x| x < 223);
            if !rational {
                nonbase += 1;
            }
            if side == 1 {
                assert_eq!(a.transfer_negative(p).unwrap(), mapped[i]);
                branches += 1;
            }
            // Every original K four-torsion input (including E[2]) agrees independently.
            if let Pt::Aff(x, y) = p {
                if x.iter()
                    .chain(y.iter())
                    .enumerate()
                    .all(|(i, &x)| [0, 2, 4].contains(&(i % 16)) || x == 0)
                {
                    let back = |x: ER| [x[0], x[2], x[4]];
                    let q = Some((back(x), back(y)));
                    let expected = match &a.formula {
                        Formula::Old(b) => b.transfer_point(&q).unwrap(),
                        Formula::New(b) => b.transfer_point(&q).unwrap(),
                    };
                    assert_eq!(mapped[i], embed_class(&expected));
                }
            }
            rows.push(json!({"point":point_json(p),"class":mapped[i].key().0.to_vec(),"F3_source_index":fi,"rational_Fp":rational,"both_kappa_branches":side==1}));
        }
        let mut all_pairs = Vec::new();
        for (i, &p) in points[side].iter().enumerate() {
            for (j, &q) in points[side].iter().enumerate() {
                let sum = curve::padd(&a.f, &a.curve, &p, &q);
                let k = points[side].iter().position(|&v| v == sum).unwrap();
                assert_eq!(a.pic.add(&mapped[i], &mapped[j]), mapped[k]);
                all_pairs.push(json!([i, j, k]));
            }
        }
        let distinct: BTreeSet<_> = mapped.iter().map(|x| x.key().0).collect();
        let rational: BTreeSet<_> = distinct
            .iter()
            .filter(|x| x.iter().all(|&c| c < 223))
            .copied()
            .collect();
        assert_eq!(distinct.len(), 8);
        assert_eq!(rational.len(), 4);
        assert!(nonbase > 0);
        panels.push(json!({"side":side,"model":a.model,"quartic":a.pic.coefficients(),"P0":a.pic.base_point(),"raw_complete_origin":a.origin.key().0.to_vec(),"all16":rows,"all256addition_pairs":all_pairs,"distinct_images":distinct,"rational_images":rational,"nonbase_inputs":nonbase,"both_kappa_branch_checks":branches}));
        images.push(mapped);
    }
    let golden: Value =
        serde_json::from_str(include_str!("../../ci_two_primary/expected-native.json")).unwrap();
    let g = golden
        .as_array()
        .unwrap()
        .iter()
        .find(|x| x["kind"] == "N4_TWO_PRIMARY_GROUP")
        .unwrap();
    let keys: BTreeSet<Vec<u32>> = serde_json::from_value(g["data"]["class_keys"].clone()).unwrap();
    let ours: BTreeSet<_> = images[0]
        .iter()
        .filter(|x| descend_class(x).is_ok())
        .map(|x| x.key().0.to_vec())
        .collect();
    assert_eq!(ours, keys);
    let gamma = Rational6::new(&iso.certificate["forward"]);
    let delta = Rational6::new(&iso.certificate["actual_dual"]);
    let mut lift_maps = Vec::new();
    for (side, a, map) in [(0, &old, &gamma), (1, &new, &delta)] {
        let mut by_lift: BTreeMap<[u32; 19], Vec<[u32; 19]>> = BTreeMap::new();
        for (i, &p) in points[side].iter().enumerate() {
            let q = map.eval(&a.f, p);
            let j = points[1 - side].iter().position(|&x| x == q).unwrap();
            by_lift
                .entry(images[side][i].key().0)
                .or_default()
                .push(images[1 - side][j].key().0);
        }
        for (x, ys) in &by_lift {
            assert_eq!(ys.len(), 2);
            assert!(ys.iter().all(|y| y == &ys[0]));
            if x.iter().all(|&v| v < 223) {
                assert!(ys[0].iter().all(|&v| v < 223));
            }
        }
        lift_maps.push(json!({"side":side,"all8_lift_fibres":by_lift.into_iter().map(|(x,ys)|json!({"source":x.to_vec(),"all_lift_images":ys.into_iter().map(|x|x.to_vec()).collect::<Vec<_>>()})).collect::<Vec<_>>()}));
    }
    let mut bad = [0; 16];
    bad[0] = 223;
    assert!(old.admit(&Pt::Aff(bad, [0; 16])).is_err());
    let mut bad = [0; 16];
    bad[6] = 1;
    assert!(old.admit(&Pt::Aff(bad, [0; 16])).is_err());
    assert!(old.admit(&Pt::Aff([0; 16], [0; 16])).is_err());
    println!(
        "N4_BETA_BASECHANGE_FIBRES {}",
        json!({"protocol":"5be5e0/32283c","field":"F2232=F223[v]/(v2-3),v=w3;L=F223[w]/(w6-3)","Kagreement":original_checks,"panels":panels,"matched_lift_independence":lift_maps,"old_rational_images_exact_original_cofactor_golden":true,"noncanonical_and_offcurve_rejections":3,"scope":"actual full fibre ideals and origins over Fp2/all16 E4 each; full rational beta evaluator and global closed coordinates still separate; unsigned/not a benchmark"})
    );
}
