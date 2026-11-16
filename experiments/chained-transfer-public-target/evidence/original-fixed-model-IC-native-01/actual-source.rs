use serde_json::{json, Value};
use std::{collections::BTreeMap, env, fs};

fn main() {
    let args:Vec<String>=env::args().collect();assert_eq!(args.len(),3);
    let records:Vec<Value>=serde_json::from_slice(&fs::read(&args[1]).unwrap()).unwrap();
    let mut counts=BTreeMap::<String,usize>::new();
    let mut groups=BTreeMap::<(u64,u64),(u64,u64,BTreeMap<String,u64>,Vec<String>,f64)>::new();
    let mut inputs=Vec::new();let mut cases=Vec::new();let mut scope=None;let mut setup_calls=None;
    for row in &records {
        let kind=row["kind"].as_str().unwrap();*counts.entry(kind.to_owned()).or_default()+=1;
        let d=&row["data"];
        match kind {
            "N4_ORIGINAL_MODEL_IC_INPUT"=>inputs.push(d.clone()),
            "N4_ORIGINAL_MODEL_IC_CASE"=>cases.push(d.clone()),
            "N4_ORIGINAL_MODEL_IC_SCOPE"=>{assert!(scope.is_none());scope=Some(d.clone());},
            "N4_ORIGINAL_MODEL_IC_SETUP"=>setup_calls=Some(d["actual_input_transfer_calls"].clone()),
            "N4_ORIGINAL_MODEL_IC_ATTEMPT"=>{
                let side=d["side"].as_u64().unwrap();let fb=d["nfb"].as_u64().unwrap();let r=&d["report"];
                let g=groups.entry((side,fb)).or_default();g.0+=1;
                if r["ok"]==true {assert_eq!(d["actual_target_group_check"],true);assert_eq!(d["independent_original_source_check"],true);g.1+=1;}
                else {g.3.push(r["fail"].as_str().unwrap().to_owned());}
                for phase in r["phases"].as_array().unwrap() {
                    for metric in ["mul","inv","add","lmul","ladd","hash","cmp"] { *g.2.entry(metric.to_owned()).or_default()+=phase[metric].as_u64().unwrap(); }
                    g.4+=phase["wall"].as_f64().unwrap();
                }
            },
            _=>{},
        }
    }
    assert_eq!(inputs.len(),3);assert_eq!(cases.len(),15);assert_eq!(groups.len(),12);
    let scope=scope.unwrap();assert_eq!(scope["attempts"],60);assert_eq!(scope["public_cases_solved"],15);
    let mut diagnostics=Vec::new();let mut all_attempts=0;let mut all_successes=0;
    for ((side,nfb),(attempts,successes,metrics,failures,wall)) in groups {
        assert_eq!(attempts,5);all_attempts+=attempts;all_successes+=successes;
        diagnostics.push(json!({"side":side,"nfb":nfb,"all_attempts":attempts,"verified_successes":successes,"failed_attempts":attempts-successes,"all_failure_reasons":failures,"summed_original_partial_phase_counters":metrics,"summed_reported_phase_wall_seconds_diagnostic_only":wall,"cost_scope":"all five attempts including failures; partial IC/Picard counters and uncalibrated raw phase walls, not complete pipeline cost or price"}));
    }
    assert_eq!(all_attempts,60);
    fs::write(&args[2],serde_json::to_vec_pretty(&json!({"whole_record_count":records.len(),"every_record_kind_count":counts,"actual_target_inputs":inputs,"all15_public_case_summaries":cases,"actual_Rust_scope":scope,"all12_attempt_setting_groups":diagnostics,"all_attempts":all_attempts,"verified_successful_attempts":all_successes,"failed_attempts":all_attempts-all_successes,"actual_input_transfer_API_calls":setup_calls,"complete_primitive_setup_source_admission_independent_verification_and_matched_reference_costs":"unknown; no admitted calibrated ratio or ECDLP advantage","scope":"Rust-only exact complete-record aggregation; no field arithmetic in the orchestration and no scientific raw record removed"})).unwrap()).unwrap();
}
