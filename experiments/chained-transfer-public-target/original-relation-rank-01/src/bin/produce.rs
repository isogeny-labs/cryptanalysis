//! Exact finite matrix certificates under the published 8e7e1c protocol.
//! No solver, point arithmetic, source character or scalar oracle is called.
#[allow(dead_code)]
#[path = "../../../../../../crypto/src/hash/sha256.rs"]
mod original_sha256;
use serde_json::{json, Value};
use std::{
    collections::BTreeSet,
    env, fs,
    io::{BufWriter, Write},
};
const P: u64 = 2_773_073;
type Sparse = Vec<Vec<(usize, u64)>>;
fn hash(b: &[u8]) -> String {
    original_sha256::sha256(b)
        .iter()
        .map(|v| format!("{v:02x}"))
        .collect()
}
fn mul(a: u64, b: u64) -> u64 {
    ((a as u128 * b as u128) % P as u128) as u64
}
fn minus(a: u64) -> u64 {
    if a == 0 {
        0
    } else {
        P - a
    }
}
fn inverse(mut a: u64) -> u64 {
    assert!(a > 0 && a < P);
    let (mut b, mut e) = (1, P - 2);
    while e > 0 {
        if e & 1 != 0 {
            b = mul(b, a);
        }
        a = mul(a, a);
        e >>= 1;
    }
    b
}
fn rows(v: &Value) -> Sparse {
    serde_json::from_value(v.clone()).unwrap()
}
fn certificate(
    raw: &Sparse,
    columns: &[usize],
    n: usize,
    family: &str,
    restriction: &str,
) -> Value {
    let mut dense = vec![vec![0; columns.len()]; raw.len()];
    let mut map = vec![None; n];
    for (i, &c) in columns.iter().enumerate() {
        assert!(c < n);
        map[c] = Some(i);
    }
    let mut dropped = Vec::new();
    for (i, row) in raw.iter().enumerate() {
        let mut absent = Vec::new();
        for &(c, a) in row {
            assert!(c < n);
            if let Some(j) = map[c] {
                dense[i][j] = (dense[i][j] + a % P) % P;
            } else {
                absent.push((c, a));
            }
        }
        if !absent.is_empty() {
            dropped.push(json!({"row":i,"entire_dropped_sparse_entries":absent}));
        }
    }
    let original = dense.clone();
    let mut operations = Vec::new();
    let mut pivots = Vec::new();
    let mut r = 0;
    for c in 0..columns.len() {
        let Some(k) = (r..dense.len()).find(|&i| dense[i][c] != 0) else {
            continue;
        };
        if k != r {
            dense.swap(k, r);
            operations.push(json!(["swap", k, r]));
        }
        let pivot = dense[r][c];
        let inv = inverse(pivot);
        assert_eq!(mul(pivot, inv), 1);
        if inv != 1 {
            for a in &mut dense[r] {
                *a = mul(*a, inv);
            }
            operations.push(json!(["scale", r, inv, pivot]));
        }
        for i in 0..dense.len() {
            if i != r && dense[i][c] != 0 {
                let a = minus(dense[i][c]);
                for j in 0..columns.len() {
                    dense[i][j] = (dense[i][j] + mul(a, dense[r][j])) % P;
                }
                operations.push(json!(["add", i, r, a]));
            }
        }
        pivots.push(c);
        r += 1;
    }
    let frees: Vec<_> = (0..columns.len()).filter(|c| !pivots.contains(c)).collect();
    let basis: Vec<Vec<u64>> = frees
        .iter()
        .map(|&f| {
            let mut z = vec![0; columns.len()];
            z[f] = 1;
            for (i, &c) in pivots.iter().enumerate() {
                z[c] = minus(dense[i][f]);
            }
            z
        })
        .collect();
    json!({"family":family,"restriction":restriction,"full_column_count":n,"columns":columns,
        "rows":raw.len(),"raw_sparse_rows":raw,"dense_mod_ell_summed_original":original,
        "dropped_inactive_entries":dropped,"operations":operations,"pivots":pivots,
        "rref":dense,"free_columns":frees,"full_nullspace_basis":basis,"rank":r,"nullity":columns.len()-r})
}
fn residuals(raw: &Sparse, candidate: &[Option<u64>]) -> Value {
    let mut checked = Vec::new();
    let mut excluded = Vec::new();
    for (i, row) in raw.iter().enumerate() {
        let mut dense = vec![0; candidate.len()];
        for &(c, v) in row {
            assert!(c < dense.len());
            dense[c] = (dense[c] + v % P) % P;
        }
        let unknown: Vec<_> = (0..dense.len())
            .filter(|&c| dense[c] != 0 && candidate[c].is_none())
            .collect();
        if unknown.is_empty() {
            let value = dense
                .iter()
                .zip(candidate)
                .fold(0, |s, (&a, &v)| (s + mul(a, v.unwrap_or(0))) % P);
            checked.push(json!({"row":i,"residual":value}));
        } else {
            excluded.push(json!({"row":i,"unknown_nonzero_dense_columns":unknown}));
        }
    }
    json!({"all_supported_rows":checked,"all_excluded_rows":excluded,"support_definition":"nonzero columns after explicit dense sum modulo ell; inactive values remain unknown"})
}
fn main() {
    let a: Vec<_> = env::args().collect();
    assert_eq!(a.len(), 4, "TRACE ACCEPTED_CAPTURE OUT_JSONL");
    assert!(!std::path::Path::new(&a[3]).exists());
    for d in 2.. {
        if d * d > P {
            break;
        }
        assert_ne!(P % d, 0, "fixed modulus prime check");
    }
    let tb = fs::read(&a[1]).unwrap();
    let gb = fs::read(&a[2]).unwrap();
    let trace: Value = serde_json::from_slice(&tb).unwrap();
    let gate: Value = serde_json::from_slice(&gb).unwrap();
    assert_eq!(gate["whole_calls"], 60);
    assert_eq!(gate["whole_journal_events"], 660);
    assert_eq!(gate["whole_original_native_records"], 100);
    assert_eq!(
        gate["all60full_reports_inputs_scalar_checks_counters_nontime_values_match_original"],
        true
    );
    assert!(gate["whole_inputs"]
        .as_array()
        .unwrap()
        .iter()
        .any(|v| v["sha256"] == hash(&tb)));
    let calls = trace["whole_calls"].as_array().unwrap();
    assert_eq!(calls.len(), 60);
    let mut out = BufWriter::new(
        fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&a[3])
            .unwrap(),
    );
    writeln!(out,"{}",json!({"kind":"header","schema":"original-relation-rank-certificates/v1","protocol":"8e7e1c","ell":P,"whole_trace_sha256":hash(&tb),"whole_capture_acceptance_sha256":hash(&gb),"interpretation":"finite exact row constraints only; no source-character or causal attribution"})).unwrap();
    let mut ids = BTreeSet::new();
    let mut summary = Vec::new();
    for call in calls {
        let id: [usize; 3] = serde_json::from_value(call["identity"].clone()).unwrap();
        assert!(id[0] < 3 && id[1] < 5 && id[2] < 4 && ids.insert(id));
        let n = call["available"]["columns"].as_u64().unwrap() as usize;
        assert_eq!(n, [30, 36, 48, 64][id[2]]);
        assert_eq!(call["ell"], P);
        let train = rows(&call["selected"]["original_rows"]);
        let mut held = train.clone();
        held.extend(rows(&call["selected"]["all_heldout_rows"]));
        let mut available = rows(&call["available"]["full_rows"]);
        available.extend(rows(&call["available"]["combined_lp_cycle_rows"]));
        let active: Vec<bool> = serde_json::from_value(call["selected"]["active"].clone()).unwrap();
        let remap: Vec<u32> = serde_json::from_value(call["selected"]["remap"].clone()).unwrap();
        let z: Vec<u64> = serde_json::from_value(call["kernel"]["actual_vector"].clone()).unwrap();
        assert_eq!(active.len(), n);
        assert_eq!(remap.len(), n);
        let candidate: Vec<_> = (0..n)
            .map(|c| {
                if active[c] {
                    Some(z[remap[c] as usize])
                } else {
                    None
                }
            })
            .collect();
        let ac: Vec<_> = (0..n).filter(|&c| active[c]).collect();
        let full: Vec<_> = (0..n).collect();
        let mut certs = Vec::new();
        for (name, m) in [
            ("training", &train),
            ("training_plus_all_heldout", &held),
            ("all_available", &available),
        ] {
            for (restriction, columns) in [("full", &full), ("active", &ac)] {
                certs.push(certificate(m, columns, n, name, restriction));
            }
        }
        let checks = json!({"training":residuals(&train,&candidate),"training_plus_all_heldout":residuals(&held,&candidate),"all_available":residuals(&available,&candidate)});
        summary.push(json!({"identity":id,"certificates":certs.iter().map(|v|json!({"family":v["family"],"restriction":v["restriction"],"rows":v["rows"],"columns":v["columns"].as_array().unwrap().len(),"rank":v["rank"],"nullity":v["nullity"]})).collect::<Vec<_>>(),"candidate_residuals":checks}));
        writeln!(out,"{}",json!({"kind":"call","identity":id,"candidate_full_known_or_unknown":candidate,"certificates":certs,"candidate_residuals":checks})).unwrap();
        out.flush().unwrap();
    }
    let mut repeated = Vec::new();
    for side in 0..3 {
        for setting in 0..4 {
            let group: Vec<_> = calls
                .iter()
                .filter(|c| c["identity"][0] == side && c["identity"][2] == setting)
                .collect();
            assert_eq!(group.len(), 5);
            let fields = ["available", "selected", "kernel", "known_logs"];
            repeated.push(json!({"side":side,"setting":setting,"entire_each_stage_equal_across_all_five":fields.iter().map(|&f|(f.to_owned(),Value::Bool(group.iter().all(|c|c[f]==group[0][f])))).collect::<serde_json::Map<String,Value>>()}));
        }
    }
    writeln!(out,"{}",json!({"kind":"complete","whole_calls":ids.len(),"matrix_certificates":360,"all60_call_summary":summary,"repeated_full_observation_equality":repeated,"scope":"unsigned finite matrix certificates; independent replay required; no norm/BSGS/global character result"})).unwrap();
    out.flush().unwrap();
}
