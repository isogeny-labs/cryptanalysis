//! Exact old-observation parity, never a substitute for the unchanged full analyzer.
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
    exit(&new.join("cold-panel.exit"), 0);
    exit(&new.join("reused-panel.exit"), 0);
    // The original full120 cold requirement is retained, even though only12
    // cold packets have old observations for a direct historical comparison.
    for i in 0..60 {
        for arm in ["baseline", "direct"] {
            exit(&new.join(format!("cold-{arm}-{i}.exit")), 0);
        }
    }
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
    let result = json!({"schema":"n4-observer-storage-whole-parity-v1","all14_whole_process_packets":compared,"cold_original_population":"12complete/108missing preserved; all120 new exits required","reused_population":"both complete60-case streams, including every cumulative ledger","scope":"whole historical-observation parity only; unchanged original full analyzer separately required; no prices or timing claim"});
    let mut bytes = serde_json::to_vec_pretty(&result).unwrap();
    bytes.push(b'\n');
    fs::write(&args[4], bytes).unwrap();
    println!("ALL12 old cold and BOTH60-case reused WHOLE packets/ledgers exact; NO masks; full new120 exits present; original full analyzer still separately required");
}
