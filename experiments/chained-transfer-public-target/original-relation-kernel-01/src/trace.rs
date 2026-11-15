//! Passive value capture under8e7e1c; no field/group operations or RNG calls.
//! The journal preserves completed observer events if a later step is interrupted.
use crate::{class_solver, FixedGeometry, TargetContext};
use chained_n4_public_target::ic::{Rel2Out, Row, P3};
use ghs_original_engines::pic::PicClass;
use serde_json::{json, Value};
use std::{
    cell::RefCell,
    collections::HashMap,
    fs::OpenOptions,
    io::Write,
    path::{Path, PathBuf},
};

#[derive(Default)]
struct Store {
    label: Option<[usize; 3]>,
    current: Option<Value>,
    calls: Vec<Value>,
}
thread_local! { static STORE: RefCell<Store> = RefCell::new(Store::default()); }
fn output() -> PathBuf {
    PathBuf::from(
        std::env::var("N4_RELATION_TRACE_OUTPUT").expect("explicit separate trace output required"),
    )
}
fn journal(stage: &str, identity: &Value, data: &Value, first: bool) {
    let path = output().with_extension("journal.jsonl");
    let mut options = OpenOptions::new();
    options.write(true);
    if first {
        options.create_new(true);
    } else {
        options.append(true);
    }
    let mut f = options.open(path).expect("preserve whole passive journal");
    let record = json!({"stage":stage,"identity":identity,"data":data});
    serde_json::to_writer(&mut f, &record).expect("serialize entire observer event");
    f.write_all(b"\n").unwrap();
    f.sync_data().unwrap();
}
fn set(stage: &str, value: Value) {
    STORE.with(|store| {
        let mut s = store.borrow_mut();
        let current = s.current.as_mut().expect("active original solve");
        assert!(current.get(stage).is_none(), "observer stage repeated");
        journal(stage, &current["identity"], &value, false);
        current[stage] = value;
    });
}
pub fn label(side: usize, public_index: usize, attempt: usize) {
    STORE.with(|store| {
        let mut s = store.borrow_mut();
        assert!(s.label.is_none() && s.current.is_none());
        s.label = Some([side, public_index, attempt]);
    });
}
pub fn begin(
    ctx: &TargetContext<'_>,
    generator: &crate::EncodedClass,
    target: &crate::EncodedClass,
    p: &class_solver::Params,
    seed: u64,
) {
    STORE.with(|store| {
        let mut s = store.borrow_mut();
        let identity = s.label.take().expect("explicit public call identity");
        assert!(s.current.is_none());
        let value = json!({"identity":identity,"field":&ctx.norm.field_tag,"model":&ctx.norm.model_tag,
            "generator":generator,"target":target,"ell":ctx.ell,"q":ctx.q,"quartic":ctx.f,
            "params":{"nfb":p.nfb,"rows_mult":p.rows_mult,"max_desc":p.max_desc,"sge":p.sge,"maxw":p.maxw,"lp2":p.lp2},"seed":seed});
        journal("begin", &value["identity"], &value, s.calls.is_empty());
        s.current = Some(value);
    });
}
pub fn available(
    fb: &[P3],
    full: &[Row],
    combined: &[Row],
    graph: Option<&Rel2Out>,
    columns: usize,
    eta: u32,
) {
    let graph = graph.map(|g| json!({"full":g.full,"ground":g.ground,"edges":g.edges,"vertex_points":g.vertex_pts,"pairs":g.pairs,"no_roots":g.no_roots}));
    set(
        "available",
        json!({"factor_base":fb,"full_rows":full,"combined_lp_cycle_rows":combined,"graph":graph,"columns":columns,"eta_column":eta}),
    );
}
pub fn selected(rows: &[Row], remapped: &[Row], heldout: &[Row], used: &[bool], remap: &[u32]) {
    set(
        "selected",
        json!({"original_rows":rows,"remapped_rows":remapped,"all_heldout_rows":heldout,"active":used,"remap":remap}),
    );
}
pub fn kernel(z: &[u64], used: &[bool], remap: &[u32], hold_ok: i32, hold_bad: i32) {
    set(
        "kernel",
        json!({"actual_vector":z,"active":used,"remap":remap,"heldout_ok":hold_ok,"heldout_bad":hold_bad}),
    );
}
pub fn known_logs(logs: &HashMap<u64, u64>) {
    let mut all: Vec<_> = logs.iter().map(|(&point, &value)| (point, value)).collect();
    all.sort_by_key(|v| v.0);
    set("known_logs", json!({"entire_known_point_log_table":all}));
}
pub fn starts(random_scalar: u64, classes: [PicClass; 3]) {
    // Original PicClass::key only copies canonical representation bytes into a
    // fixed array. It performs no field/group arithmetic or normalization.
    let keys: Vec<_> = classes.iter().map(|c| c.key().0).collect();
    set(
        "descent_starts",
        json!({"random_scalar":random_scalar,"three_raw_canonical_class_keys":keys}),
    );
}
pub fn split(added: &[u32], points: &[P3], value: u64) {
    STORE.with(|store| {
        let mut s = store.borrow_mut();
        let current = s.current.as_mut().expect("active solve");
        if current.get("descent_splits").is_none() { current["descent_splits"] = json!([]); }
        let leg = current["descent_splits"].as_array().unwrap().len();
        let record = json!({"leg":leg,"entire_added_factor_base_indices":added,"entire_split_points":points,"computed_y":value});
        journal("descent_split", &current["identity"], &record, false);
        current["descent_splits"].as_array_mut().unwrap().push(record);
    });
}
pub fn recovery(ys: &[u64], denominator: u64, candidate: u64) {
    set(
        "recovery",
        json!({"all_three_y":ys,"denominator":denominator,"candidate":candidate}),
    );
}
fn report(r: &class_solver::Report) -> Value {
    json!({"ok":r.ok,"fail":r.fail,"k_found":r.k_found,"stats":r.stats,
        "phases":r.phases.iter().map(|(phase,c,wall)|json!({"phase":phase,"mul":c.mul,"inv":c.inv,"add":c.add,"lmul":c.lmul,"ladd":c.ladd,"hash":c.hash,"cmp":c.cmp,"wall":wall})).collect::<Vec<_>>(),
        "counter_scope":"original IC and wrapped Picard diagnostics only; FpR/setup/admission/source verification unknown, no calibrated price"})
}
pub fn finish(result: &class_solver::Report) {
    STORE.with(|store| {
        let mut s = store.borrow_mut();
        let mut call = s.current.take().expect("active solve");
        call["report"] = report(result);
        journal("finish", &call["identity"], &call["report"], false);
        s.calls.push(call);
    });
}
pub fn write_after_reports(geometry: &FixedGeometry, path: &Path) {
    let calls = STORE.with(|store| {
        let mut s = store.borrow_mut();
        assert!(s.current.is_none() && s.label.is_none());
        std::mem::take(&mut s.calls)
    });
    // No norm, scalar, rank or logarithm calculations occur here. All original
    // reports and test acceptance checks have already been printed/frozen.
    let models: Vec<_> = geometry
        .models
        .iter()
        .enumerate()
        .map(|(side, m)| {
            json!({
        "side":side,"field":&m.prime.field_tag,"model":&m.prime.model_tag,
        "P0":m.prime.a.pic.base_point(),"case":crate::CASES[side],"mask":crate::MASKS[side]})
        })
        .collect();
    let value = json!({"schema":"original-fixed-model-passive-relation-trace/v1",
        "protocol":"8e7e1c/CBC published before code","models":models,"whole_calls":calls,
        "insertion_manifest":serde_json::from_str::<Value>(include_str!("../passive-insertion-manifest-01.json")).unwrap(),
        "scope":"whole passive original unassisted IC values only; rank/norm/BSGS interpretation not run"});
    let mut f = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .unwrap();
    serde_json::to_writer(&mut f, &value).unwrap();
    f.sync_data().unwrap();
}
