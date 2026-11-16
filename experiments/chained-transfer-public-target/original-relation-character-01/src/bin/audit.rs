//! Checks BSGS proposals with the existing actual norm and direct source group
//! equations, then compares scalar and point-group residuals independently.
//! No BSGS search or producer implementation is imported.
use chained_n4_original_full_evaluator::{ep, kp, Runtime};
use chained_n4_original_full_geometry::{norm::EncodedClass, NormNew, ELL};
use chained_n4_public_target::{ic, CheckedInstance};
use ghs_original_engines::pic::PicClass;
use isogeny_algos::{
    curve::{self, Pt},
    fpr::ER,
};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    env, fs,
    io::{BufRead, BufReader},
};
type Sparse = Vec<Vec<(usize, u64)>>;
fn sha(b: &[u8]) -> String {
    ghs_original_engines::digest::sha256(b)
        .iter()
        .map(|v| format!("{v:02x}"))
        .collect()
}
fn u(v: &Value) -> u64 {
    v.as_u64().unwrap()
}
fn inv(v: u64) -> u64 {
    assert!(v > 0 && v < ELL);
    let (mut a, mut b, mut x, mut y) = (ELL as i128, v as i128, 0i128, 1i128);
    while b != 0 {
        let q = a / b;
        (a, b) = (b, a - q * b);
        (x, y) = (y, x - q * y);
    }
    assert_eq!(a, 1);
    let z = x.rem_euclid(ELL as i128) as u64;
    assert_eq!(z * v % ELL, 1);
    z
}
fn subtract(a: u64, b: u64) -> u64 {
    (a + ELL - b) % ELL
}
fn scalar_dot(row: &[(usize, u64)], w: &[u64]) -> u64 {
    row.iter()
        .fold(0, |s, &(c, a)| (s + (a % ELL) * w[c] % ELL) % ELL)
}
fn expected_points(call: &Value) -> BTreeMap<u64, [u64; 3]> {
    let mut keys = BTreeSet::new();
    for p in call["available"]["factor_base"]
        .as_array()
        .unwrap()
        .iter()
        .chain(
            call["available"]["graph"]["vertex_points"]
                .as_array()
                .unwrap(),
        )
    {
        let p: [u64; 3] = serde_json::from_value(p.clone()).unwrap();
        keys.insert(ic::pack(&p));
    }
    for v in call["known_logs"]["entire_known_point_log_table"]
        .as_array()
        .unwrap()
    {
        keys.insert(u(&v[0]));
    }
    for leg in call["descent_splits"].as_array().unwrap() {
        for v in leg["entire_split_points"].as_array().unwrap() {
            let p: [u64; 3] = serde_json::from_value(v.clone()).unwrap();
            keys.insert(ic::pack(&p));
        }
    }
    keys.into_iter()
        .map(|key| {
            let mask = (1u64 << 21) - 1;
            (key, [key >> 42, (key >> 21) & mask, key & mask])
        })
        .collect()
}
fn checked_witness(
    norm: &NormNew,
    base: &Pt<ER>,
    m: u64,
    class: &PicClass,
    w: &Value,
) -> (u64, Pt<ER>) {
    assert_eq!(
        w["status"], "witness",
        "whole witness failure retained by producer; no accepted interpretation"
    );
    assert_eq!(w["class_key"], json!(class.key().0));
    let n = norm
        .norm(class)
        .expect("actual norm must accept each proposed witness");
    assert_eq!(w["actual_norm_point"], json!(n));
    let f = &norm.a.f3;
    let e = &norm.a.source_ec;
    let point = curve::pmul(f, e, &ep(n), 4);
    assert_eq!(w["cofactor"], 4);
    assert_eq!(w["projected_norm_point"], json!(kp(point)));
    assert_eq!(curve::pmul(f, e, &point, ELL as u128), Pt::Inf);
    assert_eq!(w["projected_killed_by_ell"], true);
    let scalar = u(&w["scalar"]);
    assert!(scalar < ELL);
    assert_eq!(
        curve::pmul(f, e, base, scalar as u128),
        point,
        "independent direct source scalar witness equation"
    );
    assert_eq!(w["direct_scalar_equation"], true);
    let i = u(&w["giant_i"]);
    let j = u(&w["baby_j"]);
    assert!(i <= m && j < m);
    assert_eq!(i * m + j, scalar);
    assert_eq!(u(&w["unreduced_i_m_plus_j"]), scalar);
    (scalar, point)
}
fn main() {
    let a: Vec<_> = env::args().collect();
    assert_eq!(a.len(), 5, "TRACE RANK_VERDICT WHOLE_WITNESSES OUT_VERDICT");
    assert!(!std::path::Path::new(&a[4]).exists());
    let tb = fs::read(&a[1]).unwrap();
    let rb = fs::read(&a[2]).unwrap();
    let trace: Value = serde_json::from_slice(&tb).unwrap();
    let rank: Value = serde_json::from_slice(&rb).unwrap();
    assert_eq!(rank["whole_calls"], 60);
    assert_eq!(rank["complete_matrix_certificates"], 360);
    assert_eq!(rank["whole_trace_sha256"], sha(&tb));
    let mut lines = BufReader::new(fs::File::open(&a[3]).unwrap()).lines();
    let mut next = || {
        serde_json::from_str::<Value>(&lines.next().expect("complete whole population").unwrap())
            .unwrap()
    };
    let header = next();
    assert_eq!(header["kind"], "header");
    assert_eq!(header["schema"], "original-post-solver-source-character/v1");
    assert_eq!(header["protocol"], "8e7e1c");
    assert_eq!(header["ell"], ELL);
    assert_eq!(header["cofactor"], 4);
    assert_eq!(header["post_solver_only"], true);
    assert_eq!(header["solving_API_called"], false);
    assert_eq!(header["whole_trace_sha256"], sha(&tb));
    assert_eq!(header["whole_rank_verdict_sha256"], sha(&rb));
    let c = CheckedInstance::construct().unwrap();
    let runtime = Runtime::construct(&c).unwrap();
    let mut bounds = Vec::new();
    let mut model_records = Vec::new();
    for side in 0..3 {
        let record = next();
        let model = &runtime.geometry.models[side];
        let norm = &model.prime;
        let f = &norm.a.f3;
        let e = &norm.a.source_ec;
        let base = model.source.generator();
        assert_ne!(base, Pt::Inf);
        assert_eq!(curve::pmul(f, e, &base, ELL as u128), Pt::Inf);
        assert_eq!(record["kind"], "model");
        assert_eq!(record["side"], side);
        assert_eq!(record["whole_source_identity"], model.source.identity());
        assert_eq!(record["field"], norm.field_tag);
        assert_eq!(record["model"], norm.model_tag);
        assert_eq!(record["P0"], json!(norm.a.pic.base_point()));
        assert_eq!(record["base"], json!(kp(base)));
        assert_eq!(record["base_nonzero_order_ell"], true);
        assert_eq!(trace["models"][side]["model"], norm.model_tag);
        assert_eq!(trace["models"][side]["P0"], json!(norm.a.pic.base_point()));
        let m = u(&record["integer_ceil_sqrt_ell"]);
        assert!(m > 0 && (m - 1) * (m - 1) < ELL && ELL <= m * m);
        assert_eq!(u(&record["giant_inclusive_bound"]), m);
        let table = record["entire_baby_table"].as_array().unwrap();
        assert_eq!(table.len() as u64, m);
        let mut current = Pt::Inf;
        let mut points = BTreeSet::new();
        for (j, row) in table.iter().enumerate() {
            assert_eq!(u(&row["j"]), j as u64);
            assert_eq!(row["point"], json!(kp(current)));
            assert!(points.insert(serde_json::to_string(&row["point"]).unwrap()));
            current = curve::padd(f, e, &current, &base);
        }
        assert_eq!(current, curve::pmul(f, e, &base, m as u128));
        assert_eq!(
            record["negative_giant_stride"],
            json!(kp(curve::neg(f, &current)))
        );
        bounds.push(m);
        model_records.push(record);
    }
    let calls = trace["whole_calls"].as_array().unwrap();
    assert_eq!(calls.len(), 60);
    let mut seen = BTreeSet::new();
    let mut results = Vec::new();
    let mut total_witnesses = 0;
    let mut total_rows = 0;
    for (index, call) in calls.iter().enumerate() {
        let record = next();
        let id: [usize; 3] = serde_json::from_value(call["identity"].clone()).unwrap();
        assert!(id[0] < 3 && id[1] < 5 && id[2] < 4 && seen.insert(id));
        assert_eq!(record["kind"], "call");
        assert_eq!(record["identity"], call["identity"]);
        let model = &runtime.geometry.models[id[0]];
        let norm = &model.prime;
        let pic = &norm.a.pic;
        let f = &norm.a.f3;
        let e = &norm.a.source_ec;
        let base = model.source.generator();
        let m = bounds[id[0]];
        let wanted = expected_points(call);
        let point_rows = record["entire_point_witnesses"].as_array().unwrap();
        assert_eq!(point_rows.len(), wanted.len());
        let mut values = BTreeMap::new();
        let mut norm_points = BTreeMap::new();
        let quartic = ic::Curve::new(223, &norm.a.core.quartic.map(|v| v as u32));
        for (row, (&key, &point)) in point_rows.iter().zip(&wanted) {
            assert_eq!(u(&row["packed_point"]), key);
            assert_eq!(row["point"], json!(point));
            assert!(point.iter().all(|&v| v < 223));
            assert_eq!(point.iter().find(|&&v| v != 0), Some(&1));
            assert_eq!(quartic.eval(&point), 0);
            let class = pic.point_class(point.map(|v| v as u32));
            let (w, p) = checked_witness(norm, &base, m, &class, &row["witness"]);
            values.insert(key, w);
            norm_points.insert(key, p);
            total_witnesses += 1;
        }
        let fb: Vec<[u64; 3]> =
            serde_json::from_value(call["available"]["factor_base"].clone()).unwrap();
        let n = fb.len();
        let eta_col = n - 1;
        // Independent eta construction from the retained geometric full relation,
        // rather than the producer's sparse-matrix representation.
        let geometric: Vec<(usize, u64)> =
            serde_json::from_value(call["available"]["graph"]["full"][0].clone()).unwrap();
        let mut eta = pic.zero();
        let mut expected_terms = Vec::new();
        for &(i, mult) in &geometric {
            assert!(i < n && mult <= 4);
            let cls = pic.point_class(fb[i].map(|v| v as u32));
            eta = pic.add(&eta, &pic.mul_scalar(&cls, mult as u128));
            if i != 0 {
                expected_terms.push(json!({"factor_base_index":i,"multiplicity":mult}));
            }
        }
        assert_eq!(
            record["eta_source_full_row"],
            call["available"]["full_rows"][0]
        );
        assert_eq!(
            record["eta_entire_positive_point_terms"],
            json!(expected_terms)
        );
        let (weta, teta) = checked_witness(norm, &base, m, &eta, &record["eta_witness"]);
        total_witnesses += 1;
        let g = norm
            .decode(&serde_json::from_value::<EncodedClass>(call["generator"].clone()).unwrap())
            .unwrap();
        let q = norm
            .decode(&serde_json::from_value::<EncodedClass>(call["target"].clone()).unwrap())
            .unwrap();
        let (wg, _) = checked_witness(norm, &base, m, &g, &record["generator_witness"]);
        let (wq, _) = checked_witness(norm, &base, m, &q, &record["target_witness"]);
        total_witnesses += 2;
        let mut vector: Vec<_> = fb.iter().skip(1).map(|p| values[&ic::pack(p)]).collect();
        vector.push(weta);
        let mut point_vector: Vec<_> = fb
            .iter()
            .skip(1)
            .map(|p| norm_points[&ic::pack(p)])
            .collect();
        point_vector.push(teta);
        let mut available: Sparse =
            serde_json::from_value(call["available"]["full_rows"].clone()).unwrap();
        let full_count = available.len();
        available.extend(
            serde_json::from_value::<Sparse>(call["available"]["combined_lp_cycle_rows"].clone())
                .unwrap(),
        );
        let mut relation_checks = Vec::new();
        let mut relation_bad = 0;
        for (row_index, row) in available.iter().enumerate() {
            let residual = scalar_dot(row, &vector);
            let mut actual = Pt::Inf;
            for &(col, coef) in row {
                assert!(col < n);
                actual = curve::padd(
                    f,
                    e,
                    &actual,
                    &curve::pmul(f, e, &point_vector[col], (coef % ELL) as u128),
                );
            }
            assert_eq!(
                curve::pmul(f, e, &base, residual as u128),
                actual,
                "separate direct point-group row residual"
            );
            if residual != 0 {
                relation_bad += 1;
            }
            relation_checks.push(json!({"available_row":row_index,"family":if row_index<full_count{"full"}else{"combined_or_cycle"},"scalar_residual":residual,"direct_source_group_residual":kp(actual),"character_constraint_holds":residual==0}));
            total_rows += 1;
        }
        let active: Vec<bool> = serde_json::from_value(call["selected"]["active"].clone()).unwrap();
        let remap: Vec<usize> = serde_json::from_value(call["selected"]["remap"].clone()).unwrap();
        let kernel: Vec<u64> =
            serde_json::from_value(call["kernel"]["actual_vector"].clone()).unwrap();
        assert_eq!(active.len(), n);
        assert_eq!(remap.len(), n);
        let candidate: Vec<Option<u64>> = (0..n)
            .map(|col| {
                if active[col] {
                    Some(kernel[remap[col]])
                } else {
                    None
                }
            })
            .collect();
        let anchor = (0..n).find(|&col| active[col] && vector[col] != 0);
        let multiplier = anchor.map(|col| candidate[col].unwrap() * inv(vector[col]) % ELL);
        let mut column_checks = Vec::new();
        let mut column_bad = 0;
        for col in 0..n {
            if let (Some(value), Some(a)) = (candidate[col], multiplier) {
                let expected = a * vector[col] % ELL;
                let equal = value == expected;
                let group_equal = curve::pmul(f, e, &base, value as u128)
                    == curve::pmul(f, e, &point_vector[col], a as u128);
                assert_eq!(equal, group_equal);
                if !equal {
                    column_bad += 1;
                }
                column_checks.push(json!({"column":col,"candidate":value,"character":vector[col],"expected":expected,"equal":equal,"direct_group_equal":group_equal}));
            } else {
                column_checks.push(json!({"column":col,"candidate":candidate[col],"character":vector[col],"comparison":"unknown candidate or degenerate character anchor"}));
            }
        }
        let logs: Vec<(u64, u64)> =
            serde_json::from_value(call["known_logs"]["entire_known_point_log_table"].clone())
                .unwrap();
        let logmap: BTreeMap<_, _> = logs.iter().copied().collect();
        assert_eq!(logmap.len(), logs.len());
        let mut known_checks = Vec::new();
        let mut known_bad = 0;
        for &(point, value) in &logs {
            let w = values[&point];
            if let Some(a) = multiplier {
                let expected = a * w % ELL;
                let equal = value == expected;
                let group_equal = curve::pmul(f, e, &base, value as u128)
                    == curve::pmul(f, e, &norm_points[&point], a as u128);
                assert_eq!(equal, group_equal);
                if !equal {
                    known_bad += 1;
                }
                known_checks.push(json!({"point":point,"candidate_log":value,"character":w,"expected":expected,"equal":equal,"direct_group_equal":group_equal}));
            } else {
                known_checks.push(json!({"point":point,"candidate_log":value,"character":w,"comparison":"degenerate character anchor"}));
            }
        }
        let start_keys = &call["descent_starts"]["three_raw_canonical_class_keys"];
        let start_witnesses = record["all_three_descent_start_witnesses"]
            .as_array()
            .unwrap();
        assert_eq!(start_witnesses.len(), 3);
        let random = u(&call["descent_starts"]["random_scalar"]);
        let r = pic.mul_scalar(&g, random as u128);
        let expected_starts = [r.clone(), pic.add(&r, &g), pic.add(&r, &q)];
        let legs = call["descent_splits"].as_array().unwrap();
        assert_eq!(legs.len(), 3);
        let mut descent = Vec::new();
        for leg in 0..3 {
            let packet = EncodedClass {
                field: norm.field_tag.clone(),
                model: norm.model_tag.clone(),
                key: serde_json::from_value(start_keys[leg].clone()).unwrap(),
            };
            let class = norm.decode(&packet).unwrap();
            assert_eq!(class, expected_starts[leg]);
            let (ws, ts) = checked_witness(norm, &base, m, &class, &start_witnesses[leg]);
            total_witnesses += 1;
            let walk: Vec<usize> =
                serde_json::from_value(legs[leg]["entire_added_factor_base_indices"].clone())
                    .unwrap();
            let split: Vec<[u64; 3]> =
                serde_json::from_value(legs[leg]["entire_split_points"].clone()).unwrap();
            assert_eq!(split.len(), 3);
            let mut left = class.clone();
            let mut right = pic.zero();
            let mut predicted = 0;
            let mut y = 0;
            for point in &split {
                let key = ic::pack(point);
                right = pic.add(&right, &pic.point_class(point.map(|v| v as u32)));
                predicted = (predicted + values[&key]) % ELL;
                y = (y + logmap[&key]) % ELL;
            }
            right = pic.sub(&right, &eta);
            predicted = subtract(predicted, weta);
            y = subtract(
                y,
                candidate[eta_col].expect("actual solver eta must be known"),
            );
            for &i in &walk {
                assert!(i < n);
                let key = ic::pack(&fb[i]);
                left = pic.add(&left, &pic.point_class(fb[i].map(|v| v as u32)));
                predicted = subtract(predicted, values[&key]);
                y = subtract(y, logmap[&key]);
            }
            let captured = u(&legs[leg]["computed_y"]);
            assert_eq!(
                y, captured,
                "complete retained split/walk candidate-log calculation"
            );
            let expected = multiplier.map(|a| a * ws % ELL);
            let consistent = expected.map(|v| v == captured);
            let group_consistent = multiplier.map(|a| {
                curve::pmul(f, e, &base, captured as u128) == curve::pmul(f, e, &ts, a as u128)
            });
            assert_eq!(consistent, group_consistent);
            descent.push(json!({"leg":leg,"start_class_key":class.key().0,"character":ws,"actual_class_decomposition_equal":left==right,"entire_walk_length":walk.len(),"left_class_key":left.key().0,"right_class_key":right.key().0,"source_character_from_split_walk":predicted,"source_decomposition_equal":predicted==ws,"captured_y":captured,"recomputed_from_entire_known_log_decomposition":y,"expected_from_character_multiplier":expected,"candidate_y_agrees":consistent,"direct_source_group_agrees":group_consistent}));
        }
        let source_ratio = if wg != 0 {
            Some(wq * inv(wg) % ELL)
        } else {
            None
        };
        let direct_ratio_solution = source_ratio.map(|k| pic.mul_scalar(&g, k as u128) == q);
        let candidate_scalar = u(&call["recovery"]["candidate"]);
        let actual_candidate_solution = pic.mul_scalar(&g, candidate_scalar as u128) == q;
        assert_eq!(call["report"]["ok"], actual_candidate_solution);
        let rank_call = &rank["all60_call_summary"][index];
        assert_eq!(rank_call["identity"], call["identity"]);
        results.push(json!({"identity":id,"rank_certificates":rank_call["certificates"],"point_witnesses":point_rows.len(),"source_character_vector":vector,"eta_character":weta,"generator_character":wg,"target_character":wq,"all_available_relation_checks":relation_checks,"available_relation_character_failures":relation_bad,"candidate_full_known_or_unknown":candidate,"anchor_column":anchor,"multiplier":multiplier,"nonzero_multiplier":multiplier.map(|v|v!=0),"all_candidate_column_checks":column_checks,"candidate_column_disagreements":column_bad,"all_known_log_checks":known_checks,"known_log_disagreements":known_bad,"all_three_descent_checks":descent,"source_character_ratio":source_ratio,"direct_actual_target_ratio_solution":direct_ratio_solution,"original_candidate_scalar":candidate_scalar,"original_candidate_actual_solution":actual_candidate_solution,"source_ratio_matches_candidate":source_ratio.map(|k|k==candidate_scalar)}));
    }
    let footer = next();
    drop(next);
    assert!(lines.next().is_none());
    assert_eq!(footer["kind"], "complete");
    assert_eq!(footer["whole_calls"], 60);
    assert_eq!(footer["all_class_witness_attempts"], total_witnesses);
    assert_eq!(footer["whole_witness_failures"], 0);
    let result = json!({"protocol":"8e7e1c","whole_calls":seen.len(),"whole_checked_class_witnesses":total_witnesses,"whole_checked_available_relations":total_rows,"all_three_complete_BSGS_tables_checked":true,"each_witness_actual_norm_cofactor4_and_direct_source_scalar_equation_checked":true,"each_relation_log_column_descent_scalar_comparison_crosschecked_in_source_point_group":true,"all_model_records":model_records,"all60_call_results":results,"whole_trace_sha256":sha(&tb),"whole_rank_verdict_sha256":sha(&rb),"whole_witnesses_sha256":sha(&fs::read(&a[3]).unwrap()),"scope":"unsigned finite post-solver source-character/decomposition checks; no oracle supplied to original solving API; no global Picard character or concrete Lean numeric specialization, no calibrated cost or causal theorem"});
    fs::write(&a[4], serde_json::to_vec_pretty(&result).unwrap()).unwrap();
}
