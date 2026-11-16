//! Direct exceptional input coverage complements the mixed cyclic panels.
use crate::complete::CompleteBeta;
use chained_n4_odd_product_maps::Chain;
use chained_n4_odd_source::OddSourceIsogeny;
use chained_n4_public_target::CheckedInstance;
use serde_json::json;

#[test]
fn every_rational_exceptional_class_both_directions() {
    let c = CheckedInstance::construct().unwrap();
    let b = CompleteBeta::construct(&c).unwrap();
    let iso = OddSourceIsogeny::construct(&c);
    let chain = Chain::new(&c, b.old(), b.new(), &iso).unwrap();
    let mut panels = Vec::new();
    for side in 0..2 {
        let p = if side == 0 {
            &b.old().a.pic
        } else {
            &b.new().a.pic
        };
        let target = if side == 0 {
            &b.new().a.pic
        } else {
            &b.old().a.pic
        };
        let points = p.rational_points_bruteforce();
        assert_eq!(points.len(), 224);
        let cof = b.cofactor_pairs(side).unwrap();
        let mut sectors = [0usize; 4];
        let mut output_exceptional = 0;
        let mut rows = Vec::new();
        for (i, point) in points.into_iter().enumerate() {
            if i % 32 == 0 {
                eprintln!("direct exceptional side{side}/input{i}");
            }
            let x = p.exceptional(point);
            let x2 = p.mul_scalar(&x, 2773073);
            let sector = cof.iter().position(|(t, _)| t == &x2).unwrap();
            sectors[sector] += 1;
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
            assert_eq!(p.mul_scalar(&back, 3413013), x);
            let twice = if side == 0 {
                chain.forward_old(&x).unwrap()
            } else {
                chain.reverse_new(&x).unwrap()
            };
            assert_eq!(target.double(&y), twice);
            if matches!(y, ghs_original_engines::pic::PicClass::Exc(_)) {
                output_exceptional += 1;
            }
            rows.push(json!({"rational_C_point":point,"input_exceptional":x.key().0.to_vec(),"cofactor_sector":sector,"image":y.key().0.to_vec(),"dual_composition":back.key().0.to_vec(),"original_F_or_G":twice.key().0.to_vec(),"full_inverse_of_composition":true}));
        }
        assert_eq!(sectors.iter().sum::<usize>(), 224);
        panels.push(json!({"side":side,"all224_exceptional_inputs":rows,"cofactor_sector_histogram":sectors,"exceptional_outputs":output_exceptional}));
    }
    println!(
        "N4_BETA_ALL_EXCEPTIONAL {}",
        json!({"protocol":"5be5e0/32283c; direct exceptional validation of complete canonical domain","all448_inputs":panels,"actual_original_chain_used_for_both_F_equals_2beta":true,"both13_and_full_inverse_on_every_input":true,"scope":"all224 rational exceptional classes on each actual model; not enumeration of all11092292 classes; unsigned finite correctness, no performance claim"})
    );
}
