//! Retrospective PARTIAL observation parity after actual04cold124; NEVER full acceptance.
use serde_json::{json, Value};
use std::{fs, path::Path};
fn exit(path: &Path, expected: i32) {
    assert_eq!(
        fs::read_to_string(path).unwrap().trim(),
        expected.to_string()
    );
}
fn packet(path: &Path) -> Value {
    let raw = fs::read_to_string(path).unwrap();
    let values: Vec<Value> = raw
        .lines()
        .filter_map(|line| {
            line.split_once("N4_NORM_ARITHMETIC_CASE ")
                .map(|(_, body)| serde_json::from_str(body).unwrap())
        })
        .collect();
    assert_eq!(
        values.len(),
        1,
        "exactly one entire process packet required"
    );
    let value = values.into_iter().next().unwrap();
    assert_eq!(value["observer_enabled"], true);
    assert_eq!(value["covered_known_executed_field_backends"], true);
    assert_eq!(value["protocol"], "01e617");
    assert_eq!(value["source"], "5ac59843a0cc6546b0f007c0bd2f79212d169c43");
    value
}
fn main() {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(
        args.len(),
        5,
        "--old-parity old-panel new-panel output.json"
    );
    assert_eq!(args[1], "--old-parity");
    let old = Path::new(&args[2]);
    let new = Path::new(&args[3]);
    exit(&old.join("cold-panel.exit"), 124);
    exit(&old.join("reused-panel.exit"), 0);
    exit(&new.join("cold-panel.exit"), 124);
    exit(&new.join("reused-panel.exit"), 0);
    let mut completed = vec![];
    let mut missing = vec![];
    for i in 0..60 {
        for arm in ["baseline", "direct"] {
            let stem = format!("cold-{arm}-{i}");
            let status = fs::read_to_string(new.join(format!("{stem}.exit"))).ok();
            if status.as_deref().map(str::trim) == Some("0") {
                let whole = packet(&new.join(format!("{stem}.txt")));
                assert_eq!(whole["population"], "separate-case-process");
                assert_eq!(whole["arm"], arm);
                let output = whole["all_outputs_and_full_cumulative_ledgers"]
                    .as_array()
                    .unwrap();
                assert_eq!(output.len(), 1);
                assert_eq!(output[0]["index"], i);
                completed.push(json!({"file":stem,"whole_new_packet":whole}));
            } else {
                missing.push(json!({"file":stem,"actual_exit":status,"raw_exists":new.join(format!("{stem}.txt")).exists(),"accepted":false}));
            }
        }
    }
    assert!(
        !missing.is_empty(),
        "partial diagnostic must never label a full population"
    );
    let mut names: Vec<_> = fs::read_dir(old)
        .unwrap()
        .map(|x| x.unwrap().file_name().to_string_lossy().into_owned())
        .filter(|x| x.starts_with("cold-") && x.ends_with(".exit") && x != "cold-panel.exit")
        .filter(|x| fs::read_to_string(old.join(x)).unwrap().trim() == "0")
        .collect();
    names.sort();
    assert_eq!(
        names.len(),
        12,
        "retain ALL12 actual old completed cold cases"
    );
    let mut compared = vec![];
    for name in names {
        let base = name.strip_suffix(".exit").unwrap();
        let (arm, index) = base
            .strip_prefix("cold-")
            .unwrap()
            .rsplit_once('-')
            .unwrap();
        assert!(["baseline", "direct"].contains(&arm));
        let index: usize = index.parse().unwrap();
        let first = packet(&old.join(format!("{base}.txt")));
        let second = packet(&new.join(format!("{base}.txt")));
        assert_eq!(first["population"], "separate-case-process");
        assert_eq!(first["arm"], arm);
        assert_eq!(
            first["all_outputs_and_full_cumulative_ledgers"]
                .as_array()
                .unwrap()
                .len(),
            1
        );
        assert_eq!(
            first["all_outputs_and_full_cumulative_ledgers"][0]["index"],
            index
        );
        assert_eq!(first, second, "WHOLE cold packet/ledger differs; NO masks");
        compared.push(json!({"file":base,"whole_old_packet":first,"whole_new_packet":second}));
    }
    for arm in ["baseline", "direct"] {
        exit(&old.join(format!("reused-{arm}.exit")), 0);
        exit(&new.join(format!("reused-{arm}.exit")), 0);
        let first = packet(&old.join(format!("reused-{arm}.txt")));
        let second = packet(&new.join(format!("reused-{arm}.txt")));
        assert_eq!(first["arm"], arm);
        assert_eq!(first["population"], "fixed-reused-context-process");
        assert_eq!(
            first["all_outputs_and_full_cumulative_ledgers"]
                .as_array()
                .unwrap()
                .len(),
            60
        );
        assert_eq!(
            first, second,
            "WHOLE reused process packet/ALL60 cumulative ledgers differ; NO masks"
        );
        compared.push(json!({"file":format!("reused-{arm}"),"whole_old_packet":first,"whole_new_packet":second}));
    }
    let result = json!({"schema":"n4-observer-storage-partial-observation-parity-v1","analysis_design":"RETROSPECTIVE diagnostic after actual04cold124; unchanged full analyzer and full parity checker reject101","full_cold_population_accepted":false,"new_cold_panel_actual_exit":124,"all_actual_completed_new_cold_packets":completed,"all_missing_or_incomplete_new_cold_cases":missing,"all14_whole_old_new_packet_pairs":compared,"reused_population":"both complete60-output process packets with EVERY cumulative canonical ledger","scope":"no masks/dedup/extrapolation/prices/time or performance claim; does not discharge original full120cold acceptance"});
    let mut bytes = serde_json::to_vec_pretty(&result).unwrap();
    bytes.push(b'\n');
    assert!(!Path::new(&args[4]).exists());
    fs::write(&args[4], bytes).unwrap();
    println!("PARTIAL ONLY: ALL12 old cold and BOTH60-case reuse WHOLE packets/ledgers exact; all actual new complete cold packets retained; FULL120cold remains rejected");
}
