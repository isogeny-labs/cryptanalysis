//! Supplemental coordinate/certificate replay with the suite's other arithmetic.
//! Producing-session check, not an independent signed verification service.
use cryptanalysis_suite::cryptanalysis::ic_boundary::{
    CountedGroup, GroupOps, PrimeCurve, PrimePoint,
};
use serde_json::{json, Value};
use std::{fs, path::PathBuf};
const N: u64 = 2147505293;
fn add(a: u64, b: u64) -> u64 {
    (a + b) % N
}
fn mul(a: u64, b: u64) -> u64 {
    (a as u128 * b as u128 % N as u128) as u64
}
fn neg(a: u64) -> u64 {
    if a == 0 {
        0
    } else {
        N - a
    }
}
fn point(c: &PrimeCurve, v: &Value) -> PrimePoint {
    let x = v[0].as_u64().unwrap();
    let y = v[1].as_u64().unwrap();
    assert!(x < c.p && y < c.p);
    let q = PrimePoint::affine(x, y);
    assert!(c.is_on_curve(q));
    q
}
fn columns(cert: &Value, size: usize) -> Vec<u64> {
    let mut cols = vec![0; size];
    for (r, w) in cert["relations"]
        .as_array()
        .unwrap()
        .iter()
        .zip(cert["weights"].as_array().unwrap())
    {
        let w = w.as_u64().unwrap();
        assert!(w < N);
        for t in r["terms"].as_array().unwrap() {
            let i = t["column"].as_u64().unwrap() as usize;
            let sign = t["sign"].as_i64().unwrap();
            assert!(sign == 1 || sign == -1);
            cols[i] = add(cols[i], if sign == 1 { w } else { neg(w) });
        }
    }
    cols
}
fn main() {
    let path = PathBuf::from(std::env::args().nth(1).expect("manifest path"));
    let m: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
    let c = PrimeCurve {
        p: 2147483647,
        a: 2,
        b: 14,
    };
    let mut ops = GroupOps::default();
    let mut results = Vec::new();
    for cell in m["cells"].as_array().unwrap() {
        if cell["stage"] != "heldout" || cell["arm"] != "selected-aa0" {
            continue;
        }
        let r = &cell["report"];
        assert_eq!(r["status"], "solved");
        assert_eq!(r["p"], 2147483647u64);
        assert_eq!(r["n"], N);
        let cert = &r["certificate"];
        assert_eq!(cert["order"], N);
        assert_eq!(cert["generator"], r["G"]);
        assert_eq!(cert["target"], r["Q"]);
        assert_eq!(cert["summands"], r["summands"]);
        let g = point(&c, &r["G"]);
        let q = point(&c, &r["Q"]);
        let d = cert["scalar"].as_u64().unwrap();
        assert!(d < N);
        assert_eq!(c.mul(&mut ops, g, d), q);
        let base: Vec<_> = r["base_points"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| point(&c, v))
            .collect();
        let final_cols = 3 * base.len() / 4;
        let mut partial_rows = 0;
        let rows = cert["relations"].as_array().unwrap();
        let weights = cert["weights"].as_array().unwrap();
        assert_eq!(rows.len(), weights.len());
        assert!(weights.iter().filter(|w| w.as_u64().unwrap() != 0).count() >= 3);
        let mut a = 0;
        let mut b = 0;
        for (row, w) in rows.iter().zip(weights) {
            assert_eq!(
                row["terms"].as_array().unwrap().len(),
                cert["summands"].as_u64().unwrap() as usize
            );
            let aa = row["a"].as_u64().unwrap();
            let bb = row["b"].as_u64().unwrap();
            assert!(aa < N && bb < N);
            let ag = c.mul(&mut ops, g, aa);
            let bq = c.mul(&mut ops, q, bb);
            let lhs = c.add(&mut ops, ag, bq);
            let mut rhs = c.identity();
            let mut outside = false;
            for t in row["terms"].as_array().unwrap() {
                let i = t["column"].as_u64().unwrap() as usize;
                let p = base[i];
                outside |= i >= final_cols;
                let term = if t["sign"] == 1 { p } else { c.neg(p) };
                rhs = c.add(&mut ops, rhs, term);
            }
            assert_eq!(lhs, rhs);
            partial_rows += usize::from(outside);
            a = add(a, mul(aa, w.as_u64().unwrap()));
            b = add(b, mul(bb, w.as_u64().unwrap()));
        }
        assert!(columns(cert, base.len()).iter().all(|v| *v == 0));
        assert_ne!(b, 0);
        assert_eq!(add(a, mul(b, d)), 0);
        let mut forged = cert.clone();
        let w = forged["weights"][0].as_u64().unwrap();
        forged["weights"][0] = json!((w + 1) % N);
        assert!(columns(&forged, base.len()).iter().any(|v| *v != 0));
        assert_ne!(c.mul(&mut ops, g, (d + 1) % N), q);
        results.push(json!({"replicate":cell["replicate"],"rows_replayed":rows.len(),"scalar_replayed":true,"all_column_weights_zero":true,"wrong_scalar_rejected":true,"wrong_weight_rejected":true,"diagnostic_final_columns":final_cols,"diagnostic_outside_columns":base.len()-final_cols,"rows_using_diagnostic_outside_pool":partial_rows,"outside_coefficients_cancelled":true,"qualification":"All ambient columns are priced and eliminated together; this diagnostic partition is not an unknown-count or speed improvement"}));
    }
    assert_eq!(results.len(), 5);
    println!(
        "{}",
        json!({"schema":"m31-e2e-supplemental-replay/v1","standing":"pcc:unverified","arithmetic":"ic_boundary::PrimeCurve, distinct from native Mersenne Curve backend","targets":results,"counted_scalar_multiplications":ops.scalar_mults,"counted_additions":ops.adds,"independent_signature":false})
    );
}
