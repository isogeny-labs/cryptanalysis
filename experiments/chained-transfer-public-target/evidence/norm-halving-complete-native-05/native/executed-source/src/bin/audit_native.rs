//! Whole native JSON comparison and rendering-input projection. No field masks.
use serde_json::{json, Value};
use std::{collections::BTreeMap, fs};

const BASE: &str = "N4_NORM_HALVING_STRONG_BASELINE";
const COMPLETE: &str = "N4_NORM_HALVING_COMPLETE";
const COORDINATES: &str = "N4_NORM_HALVING_COORDINATES";

fn records(path: &str) -> BTreeMap<String, Value> {
    let text = fs::read_to_string(path).unwrap();
    let mut rows = BTreeMap::new();
    for line in text.lines() {
        if let Some(i) = line.find("N4_NORM_HALVING_") {
            if let Some((kind, body)) = line[i..].split_once(' ') {
                if kind
                    .bytes()
                    .all(|c| c.is_ascii_uppercase() || c.is_ascii_digit() || c == b'_')
                    && body.starts_with('{')
                    && body.ends_with('}')
                {
                    let value = serde_json::from_str(body).unwrap();
                    assert!(
                        rows.insert(kind.to_owned(), value).is_none(),
                        "duplicate whole native kind"
                    );
                }
            }
        }
    }
    rows
}
fn load(path: &str) -> BTreeMap<String, Value> {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn save(path: &str, value: &impl serde::Serialize) {
    let mut bytes = serde_json::to_vec_pretty(value).unwrap();
    bytes.push(b'\n');
    fs::write(path, bytes).unwrap();
}
fn main() {
    let a: Vec<_> = std::env::args().collect();
    match a.get(1).map(String::as_str) {
        Some("--freeze") => {
            assert_eq!(a.len(),4);
            let rows=records(&a[2]);
            assert!(rows.contains_key(BASE)&&rows.contains_key(COMPLETE)&&rows.contains_key(COORDINATES));
            save(&a[3],&rows);
            println!("frozen all{}whole native records; development only, NO masks",rows.len());
        }
        Some("--compare") => {
            assert_eq!(a.len(),5);let expected=load(&a[2]);let actual=records(&a[3]);
            assert!(expected.keys().eq(actual.keys()),"whole native kind set mismatch");
            assert!(expected==actual,"whole native JSON mismatch; NO ignored fields");
            save(&a[4],&actual);println!("all{}whole native records exact; NO masks",actual.len());
        }
        Some("--inherit") => {
            assert_eq!(a.len(),5);let expected=load(&a[2]);let actual=records(&a[3]);
            for(kind,value)in &expected{assert!(actual.get(kind)==Some(value),"old whole native record changed: {kind}");}
            let added:Vec<_>=actual.keys().filter(|k|!expected.contains_key(*k)).collect();
            save(&a[4],&json!({"all_old_records_exact":expected.len(),"added_kinds":added,"masks":[]}));
            println!("all{}old whole records exact;{}new kinds",expected.len(),added.len());
        }
        Some("--baseline-compatible") => {
            assert_eq!(a.len(),5);let old=records(&a[2]);let new=records(&a[3]);
            assert!(old.contains_key(BASE)&&new.contains_key(BASE));assert!(old[BASE]==new[BASE],"baseline whole row changed");
            save(&a[4],&json!({"baseline_entire_record_exact":true,"all_fields_retained":true,"masks":[]}));
            println!("strong baseline entire original record preserved; NO masks");
        }
        Some("--report-inputs") => {
            assert_eq!(a.len(),4);let rows=records(&a[2]);let complete=&rows[COMPLETE];
            let mut generic=None;
            for panel in complete["all448_exceptionals"].as_array().unwrap(){
                for row in panel["all224"].as_array().unwrap(){let c=&row["case"];
                    if c["runtime_selected_calls"]["transfer_quartic_root_factorization"]==1{generic=Some(c.clone());break;}
                }
                if generic.is_some(){break;}
            }
            let selected=generic.unwrap();
            let mut branches=BTreeMap::<String,u64>::new();
            for panel in complete["all448_exceptionals"].as_array().unwrap(){for row in panel["all224"].as_array().unwrap(){
                let c=&row["case"]["runtime_selected_calls"];
                let name=if c["transfer_quartic_root_factorization"]==1{"generic quartic"}else if c["transfer_infinity_half_dictionary"]==1{"infinity"}else{assert_eq!(c["transfer_literal_two_torsion_selector"],1);"nonzero two-torsion"};
                *branches.entry(name.to_owned()).or_default()+=1;
            }}
            assert_eq!(branches.values().sum::<u64>(),448);
            let out=json!({"actual_generic_input":selected["input"],"side":selected["side"],"direct_calls":selected["runtime_selected_calls"],"baseline_calls":selected["baseline_runtime_selected_calls"],"all448_exceptional_branch_counts":branches,"all48_mixed":complete["all48_mixed"].as_array().unwrap().len(),"all96_addition_pairs":complete["all96_addition_pairs"].as_array().unwrap().len(),"all40_public_sectors":complete["all40_public_sector_directions"].as_array().unwrap().len(),"actual_selected_setup_calls":complete["actual_selected_setup_calls"],"fixed_L_order_from_existing_input":complete["fixed_L_order_from_existing_E_K_order_input"],"coordinate_non_K_halves":rows[COORDINATES]["actual_non_K_halves"],"coordinate_wrong_F_offcurve":rows[COORDINATES]["naive_coordinate_F_offcurve"],"scope":"project recorded Rust values for rendering; selectedentries are not primitivecosts orspeedups"});
            save(&a[3],&out);println!("actual genericrow/whole448branchpopulation projected; no timing orcost inference");
        }
        _=>panic!("--freeze raw expected; --compare expected raw actual; --inherit expected raw audit; --baseline-compatible oldraw newraw audit; --report-inputs raw output"),
    }
}
