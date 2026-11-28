//! Second native arithmetic replay and exhaustive finite-domain oracle.
//! This is producer validation, not a signed independent verdict.
use prime_field_auxiliary_ic::{Curve, FactorBase, Point};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::PathBuf,
};
const N: u64 = 2147505293;
fn add(a: u64, b: u64) -> u64 {
    (a + b) % N
}
fn sub(a: u64, b: u64) -> u64 {
    (a + N - b % N) % N
}
fn mul(a: u64, b: u64) -> u64 {
    (a as u128 * b as u128 % N as u128) as u64
}
fn point(c: Curve<31>, v: &Value) -> Option<Point> {
    if v.is_null() {
        None
    } else {
        Some(
            c.point(v[0].as_u64().unwrap(), v[1].as_u64().unwrap())
                .unwrap(),
        )
    }
}
fn points(c: Curve<31>, v: &Value) -> Vec<Point> {
    v.as_array()
        .unwrap()
        .iter()
        .map(|p| point(c, p).unwrap())
        .collect()
}
fn signed(c: Curve<31>, p: Point, s: i64) -> Point {
    assert!(s == 1 || s == -1);
    if s == 1 {
        p
    } else {
        c.negate(p).unwrap()
    }
}
fn witness(c: Curve<31>, input: &Value, w: &Value) -> bool {
    let base = points(c, &input["base"]);
    let xs = w["x"].as_array().unwrap();
    let signs = w["signs"].as_array().unwrap();
    if xs.len() != signs.len() {
        return false;
    }
    let mut acc = None;
    for (x, s) in xs.iter().zip(signs) {
        let Some(p) = base.iter().find(|p| p.x() == x.as_u64().unwrap()) else {
            return false;
        };
        acc = c
            .add(acc, Some(signed(c, *p, s.as_i64().unwrap())))
            .unwrap();
    }
    acc == point(c, &input["target"])
}
fn census(c: Curve<31>, base: &[Point], m: usize, target: Option<Point>) -> (u64, usize) {
    struct Oracle<'a> {
        c: Curve<31>,
        base: &'a [Point],
        target: Option<Point>,
        count: u64,
        rows: BTreeSet<Vec<i32>>,
    }
    fn walk(o: &mut Oracle, depth: usize, acc: Option<Point>, row: &mut [i32]) {
        if depth == 0 {
            if acc == o.target {
                o.count += 1;
                o.rows.insert(row.to_vec());
            }
            return;
        }
        for (i, p) in o.base.iter().enumerate() {
            for s in [-1, 1] {
                row[i] += s;
                walk(
                    o,
                    depth - 1,
                    o.c.add(acc, Some(signed(o.c, *p, s as i64))).unwrap(),
                    row,
                );
                row[i] -= s;
            }
        }
    }
    let mut o = Oracle {
        c,
        base,
        target,
        count: 0,
        rows: BTreeSet::new(),
    };
    walk(&mut o, m, None, &mut vec![0; base.len()]);
    (o.count, o.rows.len())
}
fn main() {
    let path = PathBuf::from(std::env::args().nth(1).expect("manifest path"));
    let d: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
    let cells = d["cells"].as_array().unwrap();
    assert!(!cells.is_empty() && cells.len() <= 10000);
    assert_eq!(d["p"].as_u64(), Some(2147483647));
    let c = Curve::<31>::new(2, 14).unwrap();
    let g = c.point(1, 814455902).unwrap();
    let qs = [
        c.point(2144058214, 807222724).unwrap(),
        c.point(1764015007, 688050509).unwrap(),
    ];
    let mut oracles = BTreeMap::new();
    let mut verified = 0;
    let mut checked_cells = 0;
    let mut refutations = 0;
    let mut mutations = 0;
    let mut all_unique = BTreeMap::new();
    let mut query_checks = 0;
    let mut raw_rows = 0;
    let mut outside_checks = 0;
    for cell in cells {
        let r = &cell["report"];
        match cell["kind"].as_str().unwrap() {
            "encoding" => {
                let name = cell["case"].as_str().unwrap().to_string();
                let input = &r["input"];
                let base = points(c, &input["base"]);
                let m = r["m"].as_u64().unwrap() as usize;
                let truth = *oracles
                    .entry(name.clone())
                    .or_insert_with(|| census(c, &base, m, point(c, &input["target"])));
                let mut unique = BTreeSet::new();
                for w in r["verified"].as_array().unwrap() {
                    assert!(witness(c, input, w));
                    assert!(truth.0 > 0);
                    verified += 1;
                    let mut row = vec![0i32; base.len()];
                    for (x, s) in w["x"]
                        .as_array()
                        .unwrap()
                        .iter()
                        .zip(w["signs"].as_array().unwrap())
                    {
                        let i = base
                            .iter()
                            .position(|p| p.x() == x.as_u64().unwrap())
                            .unwrap();
                        row[i] += s.as_i64().unwrap() as i32;
                    }
                    unique.insert(row);
                    if mutations == 0 {
                        let mut wrong = w.clone();
                        let sign = wrong["signs"][0].as_i64().unwrap();
                        wrong["signs"][0] = json!(-sign);
                        assert!(!witness(c, input, &wrong));
                        mutations += 1;
                    }
                }
                if !unique.is_empty() {
                    checked_cells += 1;
                }
                all_unique.insert(cell["id"].as_str().unwrap().to_string(), unique.len());
                if r["status"] == "refuted_encoded_system_only" {
                    assert_eq!(
                        truth.0, 0,
                        "native finite-domain oracle contradicts encoded refutation"
                    );
                    refutations += 1;
                }
            }
            "collection" => {
                let base = points(c, &r["base_coordinates"]);
                let split = r["final_columns"].as_u64().unwrap() as usize;
                let final_base = FactorBase::without_maps(
                    c,
                    &base[..split].iter().map(|p| p.x()).collect::<Vec<_>>(),
                )
                .unwrap();
                let use_base = if cell["method"] == "full" {
                    final_base.representatives()
                } else {
                    &base
                };
                let q = qs[cell["replicate"].as_u64().unwrap() as usize];
                let records = r["records"].as_array().unwrap();
                assert_eq!(records.len(), r["queries"].as_u64().unwrap() as usize);
                for rec in records {
                    let target = c
                        .add(
                            c.mul(Some(g), rec["a"].as_u64().unwrap()).unwrap(),
                            c.mul(Some(q), rec["b"].as_u64().unwrap()).unwrap(),
                        )
                        .unwrap();
                    assert_eq!(target, point(c, &rec["target"]));
                    query_checks += 1;
                    if !rec["relation"].is_null() {
                        let mut sum = None;
                        for t in rec["relation"]["terms"].as_array().unwrap() {
                            let p = use_base[t["column"].as_u64().unwrap() as usize];
                            sum = c
                                .add(sum, Some(signed(c, p, t["sign"].as_i64().unwrap())))
                                .unwrap();
                        }
                        assert_eq!(sum, target);
                        raw_rows += 1;
                    }
                }
                let indices = r["accepted_query_indices"].as_array().unwrap();
                assert_eq!(
                    indices.len(),
                    r["accepted_partial_rows"].as_u64().unwrap() as usize
                );
                for cert in r["combined_certificates"].as_array().unwrap() {
                    let mut h = vec![0; base.len() - split];
                    let mut f = vec![0; split];
                    let mut a = 0;
                    let mut b = 0;
                    for (weight, idx) in cert["weights"].as_array().unwrap().iter().zip(indices) {
                        let w = weight.as_u64().unwrap();
                        let rec = &records[idx.as_u64().unwrap() as usize];
                        a = add(a, mul(w, rec["a"].as_u64().unwrap()));
                        b = add(b, mul(w, rec["b"].as_u64().unwrap()));
                        for t in rec["relation"]["terms"].as_array().unwrap() {
                            let j = t["column"].as_u64().unwrap() as usize;
                            let coefficient = if t["sign"] == 1 { w } else { sub(0, w) };
                            if j < split {
                                f[j] = add(f[j], coefficient);
                            } else {
                                h[j - split] = add(h[j - split], coefficient);
                            }
                        }
                    }
                    assert!(h.iter().all(|x| *x == 0));
                    assert_eq!(a, cert["a"].as_u64().unwrap());
                    assert_eq!(b, cert["b"].as_u64().unwrap());
                    assert_eq!(
                        f,
                        cert["final_coefficients"]
                            .as_array()
                            .unwrap()
                            .iter()
                            .map(|x| x.as_u64().unwrap())
                            .collect::<Vec<_>>()
                    );
                    outside_checks += 1;
                }
            }
            _ => {}
        }
    }
    let mut salvage_checked = None;
    if let Some(control) = cells.iter().find(|cell| cell["id"] == "lead-target") {
        let target = &control["report"]["extension_control"];
        let salvage = &target["salvage"];
        let mut projected = None;
        for q in points(c, &salvage["projected_terms"]) {
            projected = c.add(projected, Some(q)).unwrap();
        }
        assert_eq!(projected, point(c, &salvage["projected_target"]));
        assert_eq!(
            projected,
            c.mul(
                Some(
                    c.point(
                        target["target"]["x"][0].as_u64().unwrap(),
                        target["target"]["y"][0].as_u64().unwrap()
                    )
                    .unwrap()
                ),
                2
            )
            .unwrap()
        );
        salvage_checked = Some(true);
    }
    let mut result = Vec::new();
    for (case, (assignments, rows)) in oracles {
        result.push(json!({"case":case,"exact_m_signed_assignments":assignments,"distinct_signed_coefficient_rows":rows}));
    }
    println!(
        "{}",
        json!({"schema":"m31-native-producer-replay/v1","p":2147483647,"standing":"pcc:unverified","manifest_path":path,"exact_finite_domain_oracles":result,"polynomial_cells_with_group_witness":checked_cells,"witness_assignments_replayed":verified,"distinct_rows_by_cell":all_unique,"encoded_refutations_corroborated_in_full_finite_group_domain":refutations,"wrong_sign_mutation_rejected":if mutations==1{Some(true)}else{None},"coefficient_walk_targets_replayed":query_checks,"collection_rows_replayed":raw_rows,"actual_outside_dependencies_replayed":outside_checks,"salvage_projection_replayed":salvage_checked,"qualification":"Separate native arithmetic implementation and full finite-domain enumeration; producer validation, no independent signature or execution attestation"})
    );
}
