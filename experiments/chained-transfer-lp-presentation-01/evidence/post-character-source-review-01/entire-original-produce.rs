//! Post-solver witnesses only. No solving API or private target scalar is used.
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
    collections::{BTreeMap, BTreeSet, HashMap},
    env, fs,
    io::{BufWriter, Write},
};
fn digest(b: &[u8]) -> String {
    ghs_original_engines::digest::sha256(b)
        .iter()
        .map(|v| format!("{v:02x}"))
        .collect()
}
fn unpack(v: u64) -> [u64; 3] {
    [v >> 42, (v >> 21) & ((1 << 21) - 1), v & ((1 << 21) - 1)]
}
struct Search<'a> {
    norm: &'a NormNew,
    base: Pt<ER>,
    m: u64,
    baby: HashMap<Pt<ER>, u64>,
    negative_stride: Pt<ER>,
    whole_table: Value,
}
impl<'a> Search<'a> {
    fn new(norm: &'a NormNew, base: Pt<ER>) -> Self {
        let f = &norm.a.f3;
        let e = &norm.a.source_ec;
        assert_ne!(base, Pt::Inf);
        assert!(curve::on_curve(f, e, &base));
        assert_eq!(curve::pmul(f, e, &base, ELL as u128), Pt::Inf);
        let mut m = 1;
        while m * m < ELL {
            m += 1;
        }
        let mut baby = HashMap::new();
        let mut table = Vec::new();
        let mut p = Pt::Inf;
        for j in 0..m {
            assert!(baby.insert(p, j).is_none());
            table.push(json!({"j":j,"point":kp(p)}));
            p = curve::padd(f, e, &p, &base);
        }
        let stride = curve::pmul(f, e, &base, m as u128);
        assert_eq!(stride, p);
        Self {
            norm,
            base,
            m,
            baby,
            negative_stride: curve::neg(f, &stride),
            whole_table: json!(table),
        }
    }
    fn witness(&self, class: &PicClass) -> Value {
        let key = class.key().0;
        let norm_point = match self.norm.norm(class) {
            Ok(p) => p,
            Err(error) => return json!({"class_key":key,"status":"norm-error","error":error}),
        };
        let f = &self.norm.a.f3;
        let e = &self.norm.a.source_ec;
        let projected = curve::pmul(f, e, &ep(norm_point), 4);
        let killed = curve::pmul(f, e, &projected, ELL as u128) == Pt::Inf;
        let mut current = projected;
        for i in 0..=self.m {
            if let Some(&j) = self.baby.get(&current) {
                let w = i * self.m + j;
                if w < ELL {
                    let direct = curve::pmul(f, e, &self.base, w as u128) == projected;
                    if direct {
                        return json!({"class_key":key,"status":"witness","actual_norm_point":norm_point,"cofactor":4,"projected_norm_point":kp(projected),"projected_killed_by_ell":killed,"scalar":w,"giant_i":i,"baby_j":j,"unreduced_i_m_plus_j":w,"direct_scalar_equation":true});
                    }
                }
            }
            current = curve::padd(f, e, &current, &self.negative_stride);
        }
        json!({"class_key":key,"status":"bounded-BSGS-failure","actual_norm_point":norm_point,"projected_norm_point":kp(projected),"projected_killed_by_ell":killed,"m":self.m,"last_giant_inclusive":self.m})
    }
}
fn point_set(call: &Value) -> BTreeMap<u64, [u64; 3]> {
    let mut points = BTreeMap::new();
    for list in [
        &call["available"]["factor_base"],
        &call["available"]["graph"]["vertex_points"],
    ] {
        for p in list.as_array().unwrap() {
            let p: [u64; 3] = serde_json::from_value(p.clone()).unwrap();
            points.insert(ic::pack(&p), p);
        }
    }
    for row in call["known_logs"]["entire_known_point_log_table"]
        .as_array()
        .unwrap()
    {
        let k = row[0].as_u64().unwrap();
        let p = unpack(k);
        assert_eq!(ic::pack(&p), k);
        points.insert(k, p);
    }
    for leg in call["descent_splits"].as_array().unwrap() {
        for p in leg["entire_split_points"].as_array().unwrap() {
            let p: [u64; 3] = serde_json::from_value(p.clone()).unwrap();
            points.insert(ic::pack(&p), p);
        }
    }
    points
}
fn main() {
    let a: Vec<_> = env::args().collect();
    assert_eq!(a.len(), 4, "TRACE WHOLE_RANK_VERDICT OUT_JSONL");
    assert!(!std::path::Path::new(&a[3]).exists());
    let tb = fs::read(&a[1]).unwrap();
    let rb = fs::read(&a[2]).unwrap();
    let trace: Value = serde_json::from_slice(&tb).unwrap();
    let rank: Value = serde_json::from_slice(&rb).unwrap();
    assert_eq!(rank["whole_calls"], 60);
    assert_eq!(rank["complete_matrix_certificates"], 360);
    assert_eq!(rank["whole_trace_sha256"], digest(&tb));
    let c = CheckedInstance::construct().unwrap();
    let runtime = Runtime::construct(&c).unwrap();
    let mut out = BufWriter::new(
        fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&a[3])
            .unwrap(),
    );
    writeln!(out,"{}",json!({"kind":"header","schema":"original-post-solver-source-character/v1","protocol":"8e7e1c","ell":ELL,"cofactor":4,"whole_trace_sha256":digest(&tb),"whole_rank_verdict_sha256":digest(&rb),"post_solver_only":true,"solving_API_called":false})).unwrap();
    out.flush().unwrap();
    let searches: Vec<_> = runtime
        .geometry
        .models
        .iter()
        .map(|m| Search::new(&m.prime, m.source.generator()))
        .collect();
    for (side, search) in searches.iter().enumerate() {
        let model = &runtime.geometry.models[side];
        assert_eq!(trace["models"][side]["model"], model.prime.model_tag);
        assert_eq!(
            trace["models"][side]["P0"],
            json!(model.prime.a.pic.base_point())
        );
        writeln!(out,"{}",json!({"kind":"model","side":side,"whole_source_identity":model.source.identity(),"field":model.prime.field_tag,"model":model.prime.model_tag,"P0":model.prime.a.pic.base_point(),"base":kp(search.base),"base_nonzero_order_ell":true,"integer_ceil_sqrt_ell":search.m,"giant_inclusive_bound":search.m,"negative_giant_stride":kp(search.negative_stride),"entire_baby_table":search.whole_table})).unwrap();
        out.flush().unwrap();
    }
    let calls = trace["whole_calls"].as_array().unwrap();
    assert_eq!(calls.len(), 60);
    let mut seen = BTreeSet::new();
    let mut failures = 0;
    let mut witnesses = 0;
    for call in calls {
        let id: [usize; 3] = serde_json::from_value(call["identity"].clone()).unwrap();
        assert!(id[0] < 3 && id[1] < 5 && id[2] < 4 && seen.insert(id));
        let search = &searches[id[0]];
        let norm = search.norm;
        let pic = &norm.a.pic;
        let fb: Vec<[u64; 3]> =
            serde_json::from_value(call["available"]["factor_base"].clone()).unwrap();
        let quartic = ic::Curve::new(223, &norm.a.core.quartic.map(|v| v as u32));
        let mut points = Vec::new();
        for (key, p) in point_set(call) {
            assert!(p.iter().all(|&x| x < 223));
            assert_eq!(p.iter().find(|&&x| x != 0), Some(&1));
            assert_eq!(quartic.eval(&p), 0);
            let class = pic.point_class(p.map(|v| v as u32));
            let w = search.witness(&class);
            if w["status"] != "witness" {
                failures += 1;
            }
            witnesses += 1;
            points.push(json!({"packed_point":key,"point":p,"witness":w}));
        }
        let first: Vec<(usize, u64)> =
            serde_json::from_value(call["available"]["full_rows"][0].clone()).unwrap();
        let eta_col = fb.len() - 1;
        let mut eta = pic.zero();
        let mut eta_terms = Vec::new();
        for &(col, multiplicity) in &first {
            if col == eta_col {
                assert_eq!(multiplicity, ELL - 1);
            } else {
                assert!(col + 1 < fb.len() && multiplicity <= 4);
                let class = pic.point_class(fb[col + 1].map(|v| v as u32));
                eta = pic.add(&eta, &pic.mul_scalar(&class, multiplicity as u128));
                eta_terms.push(json!({"factor_base_index":col+1,"multiplicity":multiplicity}));
            }
        }
        let eta_witness = search.witness(&eta);
        if eta_witness["status"] != "witness" {
            failures += 1;
        }
        witnesses += 1;
        let mut special = Vec::new();
        for name in ["generator", "target"] {
            let packet: EncodedClass = serde_json::from_value(call[name].clone()).unwrap();
            let class = norm.decode(&packet).unwrap();
            let witness = search.witness(&class);
            if witness["status"] != "witness" {
                failures += 1;
            }
            witnesses += 1;
            special.push(witness);
        }
        let mut starts = Vec::new();
        for key in call["descent_starts"]["three_raw_canonical_class_keys"]
            .as_array()
            .unwrap()
        {
            let packet = EncodedClass {
                field: norm.field_tag.clone(),
                model: norm.model_tag.clone(),
                key: serde_json::from_value(key.clone()).unwrap(),
            };
            let class = norm.decode(&packet).unwrap();
            let witness = search.witness(&class);
            if witness["status"] != "witness" {
                failures += 1;
            }
            witnesses += 1;
            starts.push(witness);
        }
        writeln!(out,"{}",json!({"kind":"call","identity":id,"entire_point_witnesses":points,"eta_source_full_row":first,"eta_entire_positive_point_terms":eta_terms,"eta_witness":eta_witness,"generator_witness":special[0],"target_witness":special[1],"all_three_descent_start_witnesses":starts})).unwrap();
        out.flush().unwrap();
    }
    writeln!(out,"{}",json!({"kind":"complete","whole_calls":seen.len(),"all_class_witness_attempts":witnesses,"whole_witness_failures":failures,"scope":"unsigned post-solver BSGS proposals only; every witness requires separate actual norm and direct source scalar verification"})).unwrap();
    out.flush().unwrap();
}
