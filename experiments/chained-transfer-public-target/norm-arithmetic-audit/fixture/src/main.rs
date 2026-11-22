//! Case extraction and inverse expectations using only untouched pinned libraries.
use chained_n4_beta_complete_evaluator::complete::CompleteBeta;
use chained_n4_completed_v2::norm::EncodedClass as Old;
use chained_n4_odd_product_maps::norm::EncodedClass as New;
use chained_n4_public_target::CheckedInstance;
use serde_json::{json, Value};
fn key(v: &Value) -> [u32; 19] {
    serde_json::from_value(v.clone()).unwrap()
}
fn main() {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(args.len(), 3);
    let native: Value = serde_json::from_slice(&std::fs::read(&args[1]).unwrap()).unwrap();
    let rows = native["N4_NORM_HALVING_COMPLETE"]["all40_public_sector_directions"]
        .as_array()
        .unwrap();
    assert_eq!(rows.len(), 40);
    let c = CheckedInstance::construct().unwrap();
    let b = CompleteBeta::construct(&c).unwrap();
    let mut cases = vec![];
    let mut inverses = vec![];
    for (index, row) in rows.iter().enumerate() {
        let case = &row["case"];
        let side = case["side"].as_u64().unwrap();
        let input = key(&case["input"]);
        if side == 0 {
            let p = Old {
                field: b.old().field_tag.clone(),
                model: b.old().model_tag.clone(),
                key: input,
            };
            let out = b.forward(&p).unwrap();
            assert_eq!(out.key, key(&case["image"]));
            let back = b.dual(&out).unwrap();
            let x = b.old().decode(&p).unwrap();
            assert_eq!(
                b.old().decode(&back).unwrap(),
                b.old().a.pic.mul_scalar(&x, 13)
            );
            assert_eq!(b.inverse(&out).unwrap().key, p.key);
            cases.push(
                json!({"index":index,"kind":"forward","source_row":row,"input":p,"expected":out}),
            );
        } else {
            assert_eq!(side, 1);
            let p = New {
                field: b.new().field_tag.clone(),
                model: b.new().model_tag.clone(),
                key: input,
            };
            let out = b.dual(&p).unwrap();
            assert_eq!(out.key, key(&case["image"]));
            let x = b.new().decode(&p).unwrap();
            let back = b.forward(&out).unwrap();
            assert_eq!(
                b.new().decode(&back).unwrap(),
                b.new().a.pic.mul_scalar(&x, 13)
            );
            let inv = b.inverse(&p).unwrap();
            assert_eq!(b.forward(&inv).unwrap().key, p.key);
            cases.push(
                json!({"index":index,"kind":"dual","source_row":row,"input":p,"expected":out}),
            );
            inverses.push(json!({"index":40+inverses.len(),"kind":"inverse","source_row":row,"input":p,"expected":inv}));
        }
    }
    assert_eq!(inverses.len(), 20);
    cases.extend(inverses);
    assert_eq!(cases.len(), 60);
    let data = json!({"source":"5ac59843a0cc6546b0f007c0bd2f79212d169c43","producer":"3d49af7f3d0a28e76b79e4825c9d2324e85853d2","protocol":"01e617 published e7f4befa before derivative","cases":cases,"scope":"all40 original public-sector-direction rows plus all20 original complete-C full inverse expectations; no scalar witness in maps"});
    std::fs::write(&args[2], serde_json::to_vec_pretty(&data).unwrap()).unwrap();
    println!("N4_NORM_ARITHMETIC_FIXTURE60 original whole rows and inverse references frozen; original maps and composition checks complete");
}
