//! Strictly enabled source arithmetic observations on the frozen complete maps.
use chained_n4_completed_v2::{norm::EncodedClass as Old, NormV2};
use chained_n4_norm_halving_evaluator::{direct::DirectNormHalving, StrongScalarBaseline, ORDER};
use chained_n4_odd_product_maps::{norm::EncodedClass as New, NormNew};
use chained_n4_public_target::CheckedInstance;
use n4_arithmetic_taps as tap;
use serde_json::{json, Value};
#[path = "../../arithmetic-controls.rs"]
mod old_controls;

enum Arm {
    Baseline(StrongScalarBaseline),
    Direct(DirectNormHalving),
}
impl Arm {
    fn construct(name: &str) -> Self {
        let c = tap::with_phase("construct.instance", || {
            CheckedInstance::construct().unwrap()
        });
        tap::with_phase("construct.arm", || match name {
            "baseline" => Self::Baseline(StrongScalarBaseline::construct(&c).unwrap()),
            "direct" => Self::Direct(DirectNormHalving::construct(&c).unwrap()),
            _ => panic!("unknown arm"),
        })
    }
    fn old(&self) -> &NormV2 {
        match self {
            Self::Baseline(s) => s.reference().old(),
            Self::Direct(d) => d.old(),
        }
    }
    fn new(&self) -> &NormNew {
        match self {
            Self::Baseline(s) => s.reference().new(),
            Self::Direct(d) => d.new(),
        }
    }
    fn reset_selected_calls(&self) {
        match self {
            Self::Baseline(s) => s.reset_calls(),
            Self::Direct(d) => d.reset_calls(),
        }
    }
    fn selected_calls(&self) -> Value {
        match self {
            Self::Baseline(s) => json!(s.calls()),
            Self::Direct(d) => json!(d.calls()),
        }
    }
    fn apply(&self, case: &Value) -> Value {
        let p = case["input"].clone();
        match case["kind"].as_str().unwrap() {
            "forward" => {
                let p: Old = serde_json::from_value(p).unwrap();
                match self {
                    Self::Baseline(s) => json!(s.forward(&p).unwrap()),
                    Self::Direct(d) => json!(d.forward(&p).unwrap()),
                }
            }
            "dual" => {
                let p: New = serde_json::from_value(p).unwrap();
                match self {
                    Self::Baseline(s) => json!(s.dual(&p).unwrap()),
                    Self::Direct(d) => json!(d.dual(&p).unwrap()),
                }
            }
            "inverse" => {
                let p: New = serde_json::from_value(p).unwrap();
                match self {
                    Self::Baseline(s) => json!(s.arithmetic_audit_full_inverse(&p).unwrap()),
                    Self::Direct(d) => json!(d.inverse(&p).unwrap()),
                }
            }
            _ => panic!("unknown frozen operation"),
        }
    }
    fn validate(&self, case: &Value, out: &Value) {
        assert_eq!(
            out, &case["expected"],
            "whole field/model/key output must equal the untouched reference"
        );
        if case["kind"] == "forward" {
            let p: New = serde_json::from_value(out.clone()).unwrap();
            let x = self.new().decode(&p).unwrap();
            assert!(self
                .new()
                .a
                .pic
                .is_zero(&self.new().a.pic.mul_scalar(&x, ORDER as u128)));
        } else {
            let p: Old = serde_json::from_value(out.clone()).unwrap();
            let x = self.old().decode(&p).unwrap();
            assert!(self
                .old()
                .a
                .pic
                .is_zero(&self.old().a.pic.mul_scalar(&x, ORDER as u128)));
        }
    }
}
fn read(path: &str) -> Value {
    serde_json::from_slice(&std::fs::read(path).unwrap()).unwrap()
}
fn execute(fixture: Value, arm_name: &str, index: Option<usize>) {
    assert_eq!(
        fixture["source"],
        "5ac59843a0cc6546b0f007c0bd2f79212d169c43"
    );
    let cases = fixture["cases"].as_array().unwrap();
    assert_eq!(cases.len(), 60);
    let context = Arm::construct(arm_name);
    let setup = tap::snapshot();
    let mut outputs = Vec::new();
    let indices: Vec<_> = index.map(|i| vec![i]).unwrap_or_else(|| (0..60).collect());
    for i in indices {
        let case = &cases[i];
        assert_eq!(case["index"], i);
        context.reset_selected_calls();
        let actual = tap::with_phase("runtime", || context.apply(case));
        let selected = context.selected_calls();
        tap::with_phase("validation.output", || context.validate(case, &actual));
        outputs.push(json!({"index":i,"kind":case["kind"],"input":case["input"],"expected":case["expected"],"actual":actual,"selected_calls":selected,"complete_cumulative_ledger_after_output_validation":tap::snapshot()}));
    }
    let final_ledger = tap::snapshot();
    assert!(!final_ledger["rows"].as_array().unwrap().is_empty());
    let complete = final_ledger["rows"]
        .as_array()
        .unwrap()
        .iter()
        .all(|r| r["operation"] != "unsupported_entry" || r["count"] == 0);
    println!(
        "N4_NORM_ARITHMETIC_CASE {}",
        json!({"protocol":"01e617","source":"5ac59843a0cc6546b0f007c0bd2f79212d169c43","arm":arm_name,"population":if index.is_some(){"separate-case-process"}else{"fixed-reused-context-process"},"observer_enabled":tap::observer_enabled(),"setup_ledger":setup,"all_outputs_and_full_cumulative_ledgers":outputs,"final_ledger":final_ledger,"covered_known_executed_field_backends":complete,"unpriced_work":"atomic inverse internals, encoding/auxiliary diagnostics, parsing, I/O, allocation, hashing and exponent/index bookkeeping; no calibrated runtime claim","scope":"source field arithmetic observations only; no signed execution standing or computational advantage"})
    );
    tap::assert_no_unsupported();
}
fn main() {
    // This must precede fixture loading, constructors and any accepted record.
    if !tap::observer_enabled() {
        eprintln!("measurement and primitive controls require enabled observation");
        std::process::exit(2);
    }
    let args: Vec<_> = std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("--controls") => {
            assert_eq!(args.len(), 2);
            old_controls::run();
            println!(
                "N4_NORM_QPIC_PRIMITIVES {}",
                chained_quadratic_picard_engine::norm_arithmetic_quadratic_controls()
            );
            tap::assert_no_unsupported();
        }
        Some("--case") => {
            assert_eq!(args.len(), 5);
            let i: usize = args[4].parse().unwrap();
            assert!(i < 60);
            execute(read(&args[2]), &args[3], Some(i));
        }
        Some("--reused") => {
            assert_eq!(args.len(), 4);
            execute(read(&args[2]), &args[3], None);
        }
        _ => {
            eprintln!("--controls | --case fixture baseline/direct index | --reused fixture baseline/direct");
            std::process::exit(2);
        }
    }
}
