//! Certificate replay: separate arithmetic and validation from the producer.
//! Inverses use extended Euclid; no elimination or producer code is imported.
#[allow(dead_code)]
#[path = "../../../../../../crypto/src/hash/sha256.rs"]
mod original_sha256;
use serde_json::{json, Value};
use std::{
    collections::BTreeSet,
    env, fs,
    io::{BufRead, BufReader},
};
const Q: u64 = 2_773_073;
type Rows = Vec<Vec<(usize, u64)>>;
fn sha(b: &[u8]) -> String {
    original_sha256::sha256(b)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}
fn vecu(v: &Value) -> Vec<u64> {
    serde_json::from_value(v.clone()).unwrap()
}
fn us(v: &Value) -> usize {
    usize::try_from(v.as_u64().unwrap()).unwrap()
}
fn dot(a: &[u64], b: &[u64]) -> u64 {
    assert_eq!(a.len(), b.len());
    a.iter()
        .zip(b)
        .fold(0u64, |s, (&x, &y)| (s + x * y % Q) % Q)
}
fn euclid_inverse(x: u64) -> u64 {
    assert!(x > 0 && x < Q);
    let (mut r, mut nr, mut t, mut nt) = (Q as i128, x as i128, 0i128, 1i128);
    while nr != 0 {
        let k = r / nr;
        (r, nr) = (nr, r - k * nr);
        (t, nt) = (nt, t - k * nt);
    }
    assert_eq!(r, 1);
    let z = t.rem_euclid(Q as i128) as u64;
    assert_eq!(z * x % Q, 1);
    z
}
fn family(call: &Value, name: &str) -> Rows {
    let parse = |v: &Value| serde_json::from_value::<Rows>(v.clone()).unwrap();
    match name {
        "training" => parse(&call["selected"]["original_rows"]),
        "training_plus_all_heldout" => {
            let mut a = parse(&call["selected"]["original_rows"]);
            a.extend(parse(&call["selected"]["all_heldout_rows"]));
            a
        }
        "all_available" => {
            let mut a = parse(&call["available"]["full_rows"]);
            a.extend(parse(&call["available"]["combined_lp_cycle_rows"]));
            a
        }
        _ => panic!("unknown matrix family"),
    }
}
fn check_matrix(cert: &Value, call: &Value) -> (usize, usize) {
    let n = us(&call["available"]["columns"]);
    let cols: Vec<usize> = serde_json::from_value(cert["columns"].clone()).unwrap();
    assert_eq!(us(&cert["full_column_count"]), n);
    assert!(cols.windows(2).all(|v| v[0] < v[1]));
    assert!(cols.iter().all(|&c| c < n));
    let active: Vec<bool> = serde_json::from_value(call["selected"]["active"].clone()).unwrap();
    assert_eq!(active.len(), n);
    let wanted: Vec<_> = match cert["restriction"].as_str().unwrap() {
        "full" => (0..n).collect(),
        "active" => (0..n).filter(|&c| active[c]).collect(),
        _ => panic!("restriction"),
    };
    assert_eq!(cols, wanted);
    let raw: Rows = serde_json::from_value(cert["raw_sparse_rows"].clone()).unwrap();
    let m = us(&cert["rows"]);
    assert_eq!(raw.len(), m);
    // Validate the certificate algebra BEFORE binding it back to the source.
    let mut dense = vec![vec![0u64; cols.len()]; m];
    let mut dropped = Vec::new();
    for (i, row) in raw.iter().enumerate() {
        let mut absent = Vec::new();
        for &(c, a) in row {
            assert!(c < n);
            match cols.binary_search(&c) {
                Ok(j) => dense[i][j] = (dense[i][j] + a % Q) % Q,
                Err(_) => absent.push((c, a)),
            }
        }
        if !absent.is_empty() {
            dropped.push(json!({"row":i,"entire_dropped_sparse_entries":absent}));
        }
    }
    assert_eq!(
        serde_json::to_value(&dense).unwrap(),
        cert["dense_mod_ell_summed_original"],
        "entire dense projection"
    );
    let original = dense.clone();
    let mut operations = 0;
    for op in cert["operations"].as_array().unwrap() {
        let v = op.as_array().unwrap();
        let kind = v[0].as_str().unwrap();
        let dst = us(&v[1]);
        assert!(dst < m);
        match kind {
            "swap" => {
                assert_eq!(v.len(), 3);
                let src = us(&v[2]);
                assert!(src < m && src != dst);
                dense.swap(dst, src);
            }
            "scale" => {
                assert_eq!(v.len(), 4);
                let a = v[2].as_u64().unwrap();
                let pivot = v[3].as_u64().unwrap();
                assert_eq!(euclid_inverse(pivot), a);
                assert!(a > 0 && a < Q);
                for entry in &mut dense[dst] {
                    *entry = (*entry * a) % Q;
                }
            }
            "add" => {
                assert_eq!(v.len(), 4);
                let src = us(&v[2]);
                let k = v[3].as_u64().unwrap();
                assert!(src < m && src != dst && k > 0 && k < Q);
                for c in 0..cols.len() {
                    dense[dst][c] = (dense[dst][c] + k * dense[src][c] % Q) % Q;
                }
            }
            _ => panic!("unknown elementary operation"),
        }
        operations += 1;
    }
    let rref: Vec<Vec<u64>> = serde_json::from_value(cert["rref"].clone()).unwrap();
    assert_eq!(dense, rref, "row-operation replay matrix mismatch");
    let pivots: Vec<usize> = serde_json::from_value(cert["pivots"].clone()).unwrap();
    let rank = us(&cert["rank"]);
    assert_eq!(rank, pivots.len());
    assert!(rank <= m && rank <= cols.len());
    assert!(pivots.windows(2).all(|v| v[0] < v[1]));
    for (i, row) in rref.iter().enumerate() {
        assert_eq!(row.len(), cols.len());
        assert!(row.iter().all(|&v| v < Q));
        if i < rank {
            assert_eq!(row.iter().position(|&v| v != 0), Some(pivots[i]));
            assert_eq!(row[pivots[i]], 1);
            for j in 0..m {
                if j != i {
                    assert_eq!(rref[j][pivots[i]], 0);
                }
            }
        } else {
            assert!(row.iter().all(|&v| v == 0));
        }
    }
    let free: Vec<_> = (0..cols.len()).filter(|c| !pivots.contains(c)).collect();
    assert_eq!(serde_json::to_value(&free).unwrap(), cert["free_columns"]);
    let nullity = cols.len() - rank;
    assert_eq!(us(&cert["nullity"]), nullity);
    let basis: Vec<Vec<u64>> =
        serde_json::from_value(cert["full_nullspace_basis"].clone()).unwrap();
    assert_eq!(basis.len(), nullity);
    for (k, z) in basis.iter().enumerate() {
        assert_eq!(z.len(), cols.len());
        assert!(z.iter().all(|&v| v < Q));
        for (j, &c) in free.iter().enumerate() {
            assert_eq!(
                z[c],
                if j == k { 1 } else { 0 },
                "free-coordinate identity proves basis independence and completeness with rank"
            );
        }
        for row in &original {
            assert_eq!(dot(row, z), 0, "original matrix nullspace witness");
        }
        for row in &rref {
            assert_eq!(dot(row, z), 0, "rref nullspace witness");
        }
    }
    assert_eq!(
        raw,
        family(call, cert["family"].as_str().unwrap()),
        "whole original sparse row binding"
    );
    assert_eq!(
        serde_json::to_value(dropped).unwrap(),
        cert["dropped_inactive_entries"]
    );
    (rank, operations)
}
fn candidate_checks(raw: &Rows, z: &[Option<u64>]) -> Value {
    let mut accepted = Vec::new();
    let mut excluded = Vec::new();
    for (i, row) in raw.iter().enumerate() {
        let mut a = vec![0; z.len()];
        for &(c, v) in row {
            assert!(c < z.len());
            a[c] = (a[c] + v % Q) % Q;
        }
        let missing: Vec<_> = (0..z.len())
            .filter(|&c| a[c] != 0 && z[c].is_none())
            .collect();
        if missing.is_empty() {
            let b: Vec<_> = z.iter().map(|v| v.unwrap_or(0)).collect();
            accepted.push(json!({"row":i,"residual":dot(&a,&b)}));
        } else {
            excluded.push(json!({"row":i,"unknown_nonzero_dense_columns":missing}));
        }
    }
    json!({"all_supported_rows":accepted,"all_excluded_rows":excluded,"support_definition":"nonzero columns after explicit dense sum modulo ell; inactive values remain unknown"})
}
fn main() {
    let a: Vec<_> = env::args().collect();
    assert_eq!(a.len(), 5, "TRACE ACCEPTED_CAPTURE CERT_JSONL OUT_VERDICT");
    assert!(!std::path::Path::new(&a[4]).exists());
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
        .any(|v| v["sha256"] == sha(&tb)));
    let calls = trace["whole_calls"].as_array().unwrap();
    assert_eq!(calls.len(), 60);
    let mut lines = BufReader::new(fs::File::open(&a[3]).unwrap()).lines();
    let header: Value = serde_json::from_str(&lines.next().unwrap().unwrap()).unwrap();
    assert_eq!(header["kind"], "header");
    assert_eq!(header["schema"], "original-relation-rank-certificates/v1");
    assert_eq!(header["protocol"], "8e7e1c");
    assert_eq!(header["ell"], Q);
    assert_eq!(header["whole_trace_sha256"], sha(&tb));
    assert_eq!(header["whole_capture_acceptance_sha256"], sha(&gb));
    let mut seen = BTreeSet::new();
    let mut total_ops = 0;
    let mut summaries = Vec::new();
    for call in calls {
        let record: Value = serde_json::from_str(&lines.next().unwrap().unwrap()).unwrap();
        assert_eq!(record["kind"], "call");
        assert_eq!(record["identity"], call["identity"]);
        let id: [usize; 3] = serde_json::from_value(record["identity"].clone()).unwrap();
        assert!(id[0] < 3 && id[1] < 5 && id[2] < 4 && seen.insert(id));
        assert_eq!(call["ell"], Q);
        let n = us(&call["available"]["columns"]);
        assert_eq!(n, [30, 36, 48, 64][id[2]]);
        let z: Vec<Option<u64>> =
            serde_json::from_value(record["candidate_full_known_or_unknown"].clone()).unwrap();
        assert_eq!(z.len(), n);
        assert!(z.iter().flatten().all(|&v| v < Q));
        let mut checks = json!({});
        for name in ["training", "training_plus_all_heldout", "all_available"] {
            let check = candidate_checks(&family(call, name), &z);
            if name == "training" {
                assert!(check["all_excluded_rows"].as_array().unwrap().is_empty());
                for row in check["all_supported_rows"].as_array().unwrap() {
                    assert_eq!(
                        row["residual"], 0,
                        "constrained original candidate kernel coordinate"
                    );
                }
            }
            checks[name] = check;
        }
        assert_eq!(checks, record["candidate_residuals"]);
        let active: Vec<bool> = serde_json::from_value(call["selected"]["active"].clone()).unwrap();
        let remap: Vec<usize> = serde_json::from_value(call["selected"]["remap"].clone()).unwrap();
        let kernel = vecu(&call["kernel"]["actual_vector"]);
        assert_eq!(active.len(), n);
        assert_eq!(remap.len(), n);
        for c in 0..n {
            assert_eq!(
                z[c],
                if active[c] {
                    Some(kernel[remap[c]])
                } else {
                    None
                },
                "captured candidate binding; unknown is not zero"
            );
        }
        let certs = record["certificates"].as_array().unwrap();
        assert_eq!(certs.len(), 6);
        let mut keys = BTreeSet::new();
        let mut ranks = Vec::new();
        for cert in certs {
            let key = (
                cert["family"].as_str().unwrap(),
                cert["restriction"].as_str().unwrap(),
            );
            assert!(keys.insert(key));
            let (rank, ops) = check_matrix(cert, call);
            total_ops += ops;
            ranks.push(json!({"family":cert["family"],"restriction":cert["restriction"],"rows":cert["rows"],"columns":cert["columns"].as_array().unwrap().len(),"rank":rank,"nullity":cert["nullity"]}));
        }
        assert_eq!(keys.len(), 6);
        for name in ["training", "training_plus_all_heldout", "all_available"] {
            for restriction in ["full", "active"] {
                assert!(keys.contains(&(name, restriction)));
            }
        }
        summaries.push(json!({"identity":id,"certificates":ranks,"candidate_residuals":checks}));
    }
    let footer: Value = serde_json::from_str(&lines.next().unwrap().unwrap()).unwrap();
    assert!(lines.next().is_none());
    assert_eq!(footer["kind"], "complete");
    assert_eq!(footer["whole_calls"], 60);
    assert_eq!(footer["matrix_certificates"], 360);
    assert_eq!(
        footer["all60_call_summary"],
        serde_json::to_value(&summaries).unwrap()
    );
    let mut repeated = Vec::new();
    for side in 0..3 {
        for setting in 0..4 {
            let group: Vec<_> = calls
                .iter()
                .filter(|v| v["identity"][0] == side && v["identity"][2] == setting)
                .collect();
            assert_eq!(group.len(), 5);
            let mut map = serde_json::Map::new();
            for key in ["available", "selected", "kernel", "known_logs"] {
                map.insert(
                    key.to_owned(),
                    json!(group.iter().all(|v| v[key] == group[0][key])),
                );
            }
            repeated.push(json!({"side":side,"setting":setting,"entire_each_stage_equal_across_all_five":map}));
        }
    }
    assert_eq!(
        footer["repeated_full_observation_equality"],
        serde_json::to_value(&repeated).unwrap()
    );
    let outcome = json!({"protocol":"8e7e1c","whole_calls":seen.len(),"complete_matrix_certificates":360,"all_elementary_operations_replayed":total_ops,"full_sparse_dense_RREF_pivots_free_coordinate_basis_checked":true,"candidate_supported_and_excluded_rows_complete":true,"all60_call_summary":summaries,"repeated_full_observation_equality":repeated,"whole_trace_sha256":sha(&tb),"whole_capture_acceptance_sha256":sha(&gb),"whole_certificate_sha256":sha(&fs::read(&a[3]).unwrap()),"scope":"unsigned independent finite Rust certificate replay; no concrete Lean specialization, source-character/BSGS or causal conclusion"});
    fs::write(&a[4], serde_json::to_vec_pretty(&outcome).unwrap()).unwrap();
}
