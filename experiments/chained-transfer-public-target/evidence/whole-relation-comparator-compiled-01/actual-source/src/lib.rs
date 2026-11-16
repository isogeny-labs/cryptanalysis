//! Complete comparisons under prospective 9aad0c / published 5f23dd29.
//! All original mathematical producers and auditors remain separate.
#[allow(dead_code)]
#[path = "../../../../../../crypto/src/hash/sha256.rs"]
mod original_sha256;
#[allow(dead_code)]
mod original_records {
    include!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../original-relation-kernel-01/derived/native_record_auditor.rs"
    ));
    pub fn whole(bytes: &[u8]) -> Vec<Value> {
        records(std::str::from_utf8(bytes).expect("entire native text"))
    }
}
use serde_json::{json, Value};
use std::{
    collections::BTreeSet,
    fs,
    path::{Path, PathBuf},
    process::Command,
};
pub type Result<T> = std::result::Result<T, String>;
pub const FILES: [&str; 7] = [
    "passive-whole100-native.json",
    "passive-whole60-trace.json",
    "relation-whole60-certificates.jsonl",
    "relation-whole60-verdict.json",
    "source-character-whole60-witnesses.jsonl",
    "source-character-whole60-verdict.json",
    "passive-acceptance.json",
];
const RAW: [&str; 4] = [
    "original-baseline.json",
    "native.txt",
    FILES[1],
    "journal.jsonl",
];
const CAP_SHA: &str = "1eef55e7fa9dd799e77967e9425e6cd3400dfb51f469dade0d6e99d4f97130a2";
const BASE_SHA: &str = "52d015cffa83af5796561a9ed15dc2a6a894ff9e70d299fd2e838fbffb703d6b";
const PHASES: [&str; 7] = [
    "fb",
    "relations",
    "matrix",
    "linear_algebra",
    "log_recovery",
    "descent",
    "verify",
];
fn require(ok: bool, label: &str) -> Result<()> {
    if ok {
        Ok(())
    } else {
        Err(label.into())
    }
}
pub fn hash(bytes: &[u8]) -> String {
    original_sha256::sha256(bytes)
        .iter()
        .map(|v| format!("{v:02x}"))
        .collect()
}
fn bytes(path: &Path) -> Result<Vec<u8>> {
    fs::read(path).map_err(|e| format!("{}: {e}", path.display()))
}
fn parse(bytes: &[u8]) -> Result<Value> {
    serde_json::from_slice(bytes).map_err(|e| e.to_string())
}
fn parse_lines(bytes: &[u8]) -> Result<Value> {
    let text = std::str::from_utf8(bytes).map_err(|e| e.to_string())?;
    require(text.ends_with('\n'), "whole JSONL final newline required")?;
    let mut rows = Vec::new();
    for line in text.lines() {
        rows.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    Ok(Value::Array(rows))
}
fn encode(index: usize, value: &Value) -> Result<Vec<u8>> {
    if index == 2 || index == 4 {
        let mut data = Vec::new();
        for row in value.as_array().ok_or("JSONL array required")? {
            serde_json::to_writer(&mut data, row).map_err(|e| e.to_string())?;
            data.push(b'\n');
        }
        Ok(data)
    } else {
        serde_json::to_vec(value).map_err(|e| e.to_string())
    }
}
#[derive(Clone)]
pub struct Bundle {
    pub values: Vec<Value>,
    pub raw: Vec<Vec<u8>>,
}
impl Bundle {
    pub fn load(dir: &Path) -> Result<Self> {
        let mut raw = Vec::new();
        let mut values = Vec::new();
        for (i, name) in FILES.iter().enumerate() {
            let data = bytes(&dir.join(name))?;
            values.push(if i == 2 || i == 4 {
                parse_lines(&data)?
            } else {
                parse(&data)?
            });
            raw.push(data);
        }
        Ok(Self { values, raw })
    }
    fn historical(pins: &Path, docs: &Path, capture: &Path) -> Result<Self> {
        let pins_bytes = bytes(pins)?;
        require(
            pins_bytes
                == include_bytes!(concat!(
                    env!("CARGO_MANIFEST_DIR"),
                    "/../historical-whole-fixture-pins-01.json"
                )),
            "exact published whole fixture pin file",
        )?;
        let p = parse(&pins_bytes)?;
        require(
            p["immutable_bot"] == "0b2bee203a133568f1c7e9a35bfe3be1a663a879",
            "immutable original bot pin",
        )?;
        let entries = p["fixtures"]
            .as_array()
            .ok_or("six entire fixture pins required")?;
        require(entries.len() == 6, "six historical fixture pins required")?;
        let mut raw = Vec::new();
        let mut values = Vec::new();
        for (i, name) in FILES[..6].iter().enumerate() {
            let matches: Vec<_> = entries
                .iter()
                .filter(|entry| entry["name"] == format!("{name}.xz"))
                .collect();
            require(matches.len() == 1, "unique whole historical fixture pin")?;
            let entry = matches[0];
            let compressed = docs.join(format!("{name}.xz"));
            require(
                entry["name"] == format!("{name}.xz"),
                "exact historical filename/order pin",
            )?;
            let data = bytes(&compressed)?;
            require(
                entry["compressed_bytes"].as_u64() == Some(data.len() as u64)
                    && entry["sha256"] == hash(&data),
                "complete compressed fixture size/SHA",
            )?;
            let result = Command::new("xz")
                .args(["--decompress", "--stdout", "--"])
                .arg(&compressed)
                .output()
                .map_err(|e| e.to_string())?;
            require(
                result.status.success(),
                "whole historical XZ integrity/decompression",
            )?;
            let data = result.stdout;
            require(
                entry["decoded_bytes"].as_u64() == Some(data.len() as u64)
                    && entry["decoded_sha256"] == hash(&data),
                "complete decoded fixture size/SHA",
            )?;
            values.push(if i == 2 || i == 4 {
                parse_lines(&data)?
            } else {
                parse(&data)?
            });
            raw.push(data);
        }
        let data = bytes(capture)?;
        require(
            data.len() == 19686
                && hash(&data) == CAP_SHA
                && p["passive_acceptance"]["bytes"] == 19686
                && p["passive_acceptance"]["sha256"] == CAP_SHA,
            "exact whole historical capture receipt pin",
        )?;
        values.push(parse(&data)?);
        raw.push(data);
        Ok(Self { values, raw })
    }
    fn bind(&mut self, dir: &Path, broken: bool) -> Result<()> {
        for i in 0..2 {
            self.raw[i] = encode(i, &self.values[i])?;
            fs::write(dir.join(FILES[i]), &self.raw[i]).map_err(|e| e.to_string())?;
        }
        let inputs = self.values[6]["whole_inputs"]
            .as_array_mut()
            .ok_or("whole input bindings required")?;
        require(inputs.len() == 4, "four entire capture inputs")?;
        for (row, name) in inputs.iter_mut().zip(RAW) {
            let path = dir.join(name);
            row["path"] = json!(path.to_str().ok_or("UTF8 input path")?);
            row["sha256"] = json!(hash(&bytes(&path)?));
        }
        self.raw[6] = encode(6, &self.values[6])?;
        fs::write(dir.join(FILES[6]), &self.raw[6]).map_err(|e| e.to_string())?;
        for i in [2, 3, 4, 5] {
            let trace = hash(&self.raw[1]);
            let capture = hash(&self.raw[6]);
            match i {
                2 => {
                    self.values[i][0]["whole_trace_sha256"] =
                        json!(if broken { "0".repeat(64) } else { trace });
                    self.values[i][0]["whole_capture_acceptance_sha256"] = json!(capture);
                }
                3 => {
                    self.values[i]["whole_trace_sha256"] = json!(trace);
                    self.values[i]["whole_capture_acceptance_sha256"] = json!(capture);
                    self.values[i]["whole_certificate_sha256"] = json!(hash(&self.raw[2]));
                }
                4 => {
                    self.values[i][0]["whole_trace_sha256"] = json!(trace);
                    self.values[i][0]["whole_rank_verdict_sha256"] = json!(hash(&self.raw[3]));
                }
                5 => {
                    self.values[i]["whole_trace_sha256"] = json!(trace);
                    self.values[i]["whole_rank_verdict_sha256"] = json!(hash(&self.raw[3]));
                    self.values[i]["whole_witnesses_sha256"] = json!(hash(&self.raw[4]));
                }
                _ => unreachable!(),
            }
            self.raw[i] = encode(i, &self.values[i])?;
            fs::write(dir.join(FILES[i]), &self.raw[i]).map_err(|e| e.to_string())?;
        }
        Ok(())
    }
}
fn bound(
    value: &mut Value,
    key: &str,
    want: &str,
    label: &str,
    locations: &mut Vec<Value>,
) -> Result<()> {
    let v = value
        .get_mut(key)
        .ok_or_else(|| format!("missing bound field {label}.{key}"))?;
    require(
        v.as_str() == Some(want),
        &format!("actual whole-input digest binding {label}.{key}"),
    )?;
    locations.push(json!({"location":format!("{label}.{key}"),"actual_sha256":want}));
    *v = Value::Null;
    Ok(())
}
fn report(value: &mut Value, label: &str, locations: &mut Vec<Value>) -> Result<()> {
    let phases = value
        .get_mut("phases")
        .and_then(Value::as_array_mut)
        .ok_or("seven original phases required")?;
    require(phases.len() == 7, "exactly seven original phases required")?;
    for (i, (phase, name)) in phases.iter_mut().zip(PHASES).enumerate() {
        require(
            phase["phase"] == name,
            "exact original phase name and order",
        )?;
        let v = phase.get_mut("wall").ok_or("missing elapsed wall")?;
        let n = v.as_f64().ok_or("numeric elapsed wall required")?;
        require(
            n.is_finite() && n >= 0.0,
            "nonnegative finite elapsed wall required",
        )?;
        locations.push(json!({"location":format!("{label}.phases[{i}].wall"),"seconds":n}));
        *v = Value::Null;
    }
    let stats = value
        .get_mut("stats")
        .and_then(Value::as_array_mut)
        .ok_or("whole statistics required")?;
    let mut total = 0;
    for (i, row) in stats.iter_mut().enumerate() {
        let pair = row.as_array_mut().ok_or("statistic pair required")?;
        require(
            pair.len() == 2 && pair[0].is_string(),
            "exact statistic pair schema",
        )?;
        if pair[0] == "wall_total" {
            let n = pair[1].as_f64().ok_or("numeric elapsed total required")?;
            require(n.is_finite() && n >= 0.0, "finite nonnegative wall_total")?;
            locations.push(json!({"location":format!("{label}.stats[{i}][1]"),"seconds":n}));
            pair[1] = Value::Null;
            total += 1;
        }
    }
    require(total == 1, "exactly one wall_total required")
}
fn normalize(bundle: &Bundle, label: &str, locations: &mut Vec<Value>) -> Result<Vec<Value>> {
    let mut v = bundle.values.clone();
    let native = v[0].as_array_mut().ok_or("entire100native array")?;
    require(native.len() == 100, "entire native record population100")?;
    let mut calls = 0;
    for (i, row) in native.iter_mut().enumerate() {
        if row["kind"] == "N4_ORIGINAL_MODEL_IC_ATTEMPT" {
            calls += 1;
            report(
                row["data"]
                    .get_mut("report")
                    .ok_or("complete native report")?,
                &format!("{label}.native[{i}].data.report"),
                locations,
            )?;
        }
    }
    require(calls == 60, "all sixty native solver calls")?;
    require(
        v[1]["schema"] == "original-fixed-model-passive-relation-trace/v1",
        "original passive trace schema",
    )?;
    let calls = v[1]["whole_calls"]
        .as_array_mut()
        .ok_or("all trace calls required")?;
    require(calls.len() == 60, "all sixty trace calls")?;
    for (i, call) in calls.iter_mut().enumerate() {
        report(
            call.get_mut("report").ok_or("complete trace report")?,
            &format!("{label}.trace.whole_calls[{i}].report"),
            locations,
        )?;
    }
    require(
        v[2].as_array().is_some_and(|a| a.len() == 61),
        "whole rank header and sixty call records",
    )?;
    require(
        v[4].as_array().is_some_and(|a| a.len() == 65),
        "whole character header/three models/sixty calls/completion",
    )?;
    for (i, key, which, header) in [
        (2, "whole_trace_sha256", 1, true),
        (2, "whole_capture_acceptance_sha256", 6, true),
        (3, "whole_trace_sha256", 1, false),
        (3, "whole_capture_acceptance_sha256", 6, false),
        (3, "whole_certificate_sha256", 2, false),
        (4, "whole_trace_sha256", 1, true),
        (4, "whole_rank_verdict_sha256", 3, true),
        (5, "whole_trace_sha256", 1, false),
        (5, "whole_rank_verdict_sha256", 3, false),
        (5, "whole_witnesses_sha256", 4, false),
    ] {
        let row = if header { &mut v[i][0] } else { &mut v[i] };
        bound(
            row,
            key,
            &hash(&bundle.raw[which]),
            &format!("{label}.{}{}", FILES[i], if header { "[0]" } else { "" }),
            locations,
        )?;
    }
    let inputs = v[6]["whole_inputs"]
        .as_array_mut()
        .ok_or("all four capture input bindings")?;
    require(inputs.len() == 4, "exact four capture inputs")?;
    for (i, row) in inputs.iter_mut().enumerate() {
        require(
            row.as_object().is_some_and(|m| {
                m.len() == 2 && m.contains_key("path") && m.contains_key("sha256")
            }),
            "exact capture path/hash schema",
        )?;
        require(
            row["path"].is_string()
                && row["sha256"].as_str().is_some_and(|s| {
                    s.len() == 64
                        && s.bytes()
                            .all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase())
                }),
            "full capture path/SHA schema",
        )?;
        locations.push(json!({"location":format!("{label}.acceptance.whole_inputs[{i}]"),"actual":row.clone()}));
        row["path"] = Value::Null;
        row["sha256"] = Value::Null;
    }
    Ok(v)
}
fn fresh_bindings(fresh: &Bundle, dir: &Path) -> Result<()> {
    let inputs = fresh.values[6]["whole_inputs"]
        .as_array()
        .ok_or("capture input roles")?;
    require(inputs.len() == 4, "four capture inputs")?;
    for (row, name) in inputs.iter().zip(RAW) {
        let p = dir.join(name);
        require(
            row["path"].as_str() == p.to_str(),
            "capture path equals actual role path",
        )?;
        require(
            row["sha256"] == hash(&bytes(&p)?),
            "capture whole input digest equals actual file",
        )?;
    }
    require(
        hash(&bytes(&dir.join(RAW[0]))?) == BASE_SHA,
        "unchanged genuine26 original unassisted100baseline",
    )?;
    let records = original_records::whole(&bytes(&dir.join(RAW[1]))?);
    require(
        Value::Array(records) == fresh.values[0],
        "same-run complete raw native and whole100JSON agree",
    )?;
    let journal = parse_lines(&bytes(&dir.join(RAW[3]))?)?;
    let journal = journal.as_array().ok_or("entire journal")?;
    require(journal.len() == 660, "all660journal events required")?;
    let calls = fresh.values[1]["whole_calls"]
        .as_array()
        .ok_or("sixty trace calls")?;
    require(calls.len() == 60, "whole trace60 required")?;
    let mut identities = BTreeSet::new();
    let native = fresh.values[0].as_array().ok_or("whole native array")?;
    let attempts: Vec<_> = native
        .iter()
        .filter(|r| r["kind"] == "N4_ORIGINAL_MODEL_IC_ATTEMPT")
        .collect();
    require(attempts.len() == 60, "whole60native attempts")?;
    for (i, call) in calls.iter().enumerate() {
        let id = call["identity"].as_array().ok_or("call identity")?;
        require(id.len() == 3, "three-part call identity")?;
        let key = serde_json::to_string(id).map_err(|e| e.to_string())?;
        require(identities.insert(key), "unique complete call identity")?;
        let record = attempts
            .iter()
            .find(|r| {
                r["data"]["side"] == id[0]
                    && r["data"]["public_index"] == id[1]
                    && r["data"]["attempt"] == id[2]
            })
            .ok_or("native call identity")?;
        require(
            call["report"] == record["data"]["report"],
            "same-run trace report includes exact raw native times/counters",
        )?;
        for (j, stage) in [
            "begin",
            "available",
            "selected",
            "kernel",
            "known_logs",
            "descent_starts",
            "descent_split",
            "descent_split",
            "descent_split",
            "recovery",
            "finish",
        ]
        .iter()
        .enumerate()
        {
            let row = &journal[i * 11 + j];
            require(
                row.as_object().is_some_and(|m| {
                    m.len() == 3
                        && m.contains_key("identity")
                        && m.contains_key("stage")
                        && m.contains_key("data")
                }),
                "exact complete journal row schema",
            )?;
            require(
                row["stage"] == *stage && row["identity"] == call["identity"],
                "journal stage/identity/order",
            )?;
            let wanted = if *stage == "begin" {
                let mut map = serde_json::Map::new();
                for name in [
                    "identity",
                    "field",
                    "model",
                    "generator",
                    "target",
                    "ell",
                    "q",
                    "quartic",
                    "params",
                    "seed",
                ] {
                    map.insert(name.into(), call[name].clone());
                }
                Value::Object(map)
            } else if *stage == "descent_split" {
                call["descent_splits"][j - 6].clone()
            } else if *stage == "finish" {
                call["report"].clone()
            } else {
                call[*stage].clone()
            };
            require(
                row["data"] == wanted,
                "whole journal stage data equals entire trace value",
            )?;
        }
    }
    Ok(())
}
pub fn compare(pins: &Path, docs: &Path, capture: &Path, dir: &Path, out: &Path) -> Result<()> {
    require(!out.exists(), "accepted output must not preexist")?;
    let historical = Bundle::historical(pins, docs, capture)?;
    let fresh = Bundle::load(dir)?;
    fresh_bindings(&fresh, dir)?;
    let mut locations = Vec::new();
    let h = normalize(&historical, "historical", &mut locations)?;
    let f = normalize(&fresh, "fresh", &mut locations)?;
    for i in 0..FILES.len() {
        require(
            h[i] == f[i],
            &format!(
                "whole strict scientific value/order/schema difference in {}",
                FILES[i]
            ),
        )?;
    }
    let inputs:Vec<_>=FILES.iter().enumerate().map(|(i,n)|json!({"name":n,"historical_bytes":historical.raw[i].len(),"historical_sha256":hash(&historical.raw[i]),"fresh_path":dir.join(n),"fresh_bytes":fresh.raw[i].len(),"fresh_sha256":hash(&fresh.raw[i])})).collect();
    let receipt = json!({"protocol":"9aad0c/published5f23dd29","entire_inputs":inputs,"all_permitted_actual_elapsed_hash_path_locations":locations,"whole_native_records":100,"whole_calls":60,"whole_journal_events":660,"rank_certificate_records":61,"character_witness_records":65,"all_complete_values_and_record_order_equal_under_only_published_locations":true,"fresh_actual_baseline_native_trace_journal_bindings_checked":true,"all_rank_character_header_links_checked_before_comparison":true,"scope":"unsigned complete historical equality; original mathematical controls, source/runtime/fullprepared custody and whole CI final phases remain separate requirements"});
    fs::write(
        out,
        serde_json::to_vec_pretty(&receipt).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())
}
fn absolute(path: &Path) -> Result<PathBuf> {
    fs::canonicalize(path).map_err(|e| e.to_string())
}
pub fn fixture_bundle(pins: &Path, docs: &Path, capture: &Path, out: &Path) -> Result<()> {
    require(!out.exists(), "new whole bundle path required")?;
    let mut bundle = Bundle::historical(pins, docs, capture)?;
    fs::create_dir_all(out).map_err(|e| e.to_string())?;
    let dir = absolute(out)?;
    for (row, name) in bundle.values[6]["whole_inputs"]
        .as_array()
        .ok_or("four historical inputs")?
        .iter()
        .zip(RAW)
    {
        let p = Path::new(row["path"].as_str().ok_or("pinned historical input path")?);
        let data = bytes(p)?;
        require(
            row["sha256"] == hash(&data),
            "whole historical raw role byte pin before materialization",
        )?;
        fs::write(dir.join(name), data).map_err(|e| e.to_string())?;
    }
    bundle.bind(&dir, false)
}
fn change_elapsed(report: &mut Value) {
    for phase in report["phases"].as_array_mut().unwrap() {
        phase["wall"] = json!(phase["wall"].as_f64().unwrap() + 1.0);
    }
    for row in report["stats"].as_array_mut().unwrap() {
        if row[0] == "wall_total" {
            row[1] = json!(row[1].as_f64().unwrap() + 1.0);
        }
    }
}
fn rewrite_native(original: &[u8], records: &Value) -> Result<Vec<u8>> {
    let rows = records.as_array().ok_or("whole native rows")?;
    let mut index = 0;
    let mut output = String::new();
    for line in std::str::from_utf8(original)
        .map_err(|e| e.to_string())?
        .split_inclusive('\n')
    {
        if let Some(start) = line.find("N4_") {
            let (kind, _) = line[start..]
                .split_once(' ')
                .ok_or("native record payload")?;
            if kind == "N4_ORIGINAL_MODEL_IC_TARGET" && rows.len() == 97 {
                continue;
            }
            let row = rows.get(index).ok_or("all native rows consumed")?;
            require(
                row["kind"] == kind,
                "native record rewrite preserves entire order",
            )?;
            output.push_str(&line[..start]);
            output.push_str(kind);
            output.push(' ');
            output.push_str(&serde_json::to_string(&row["data"]).map_err(|e| e.to_string())?);
            output.push('\n');
            index += 1;
        } else {
            output.push_str(line);
        }
    }
    require(index == rows.len(), "every whole native row rewritten")?;
    Ok(output.into_bytes())
}
pub fn controls(base: &Path, out: &Path) -> Result<()> {
    require(!out.exists(), "new complete control root required")?;
    let base = absolute(base)?;
    let original = Bundle::load(&base)?;
    fresh_bindings(&original, &base)?;
    let native = bytes(&base.join("native.txt"))?;
    let raw_journal = bytes(&base.join("journal.jsonl"))?;
    fs::create_dir_all(out).map_err(|e| e.to_string())?;
    let out = absolute(out)?;
    let names = [
        "timing-only",
        "missing-record-class",
        "changed-counter",
        "changed-relation",
        "changed-kernel",
        "missing-rank-call",
        "changed-character-scalar",
        "unexpected-verdict-field",
        "unbound-linked-hash",
    ];
    let mut manifest = Vec::new();
    for name in names {
        let dir = out.join(name);
        fs::create_dir(&dir).map_err(|e| e.to_string())?;
        let mut b = original.clone();
        let mut journal = parse_lines(&raw_journal)?;
        match name {
            "timing-only" => {
                for row in b.values[0].as_array_mut().unwrap() {
                    if row["kind"] == "N4_ORIGINAL_MODEL_IC_ATTEMPT" {
                        change_elapsed(&mut row["data"]["report"]);
                    }
                }
                for call in b.values[1]["whole_calls"].as_array_mut().unwrap() {
                    change_elapsed(&mut call["report"]);
                }
                for row in journal.as_array_mut().unwrap() {
                    if row["stage"] == "finish" {
                        change_elapsed(&mut row["data"]);
                    }
                }
            }
            "missing-record-class" => b.values[0]
                .as_array_mut()
                .unwrap()
                .retain(|r| r["kind"] != "N4_ORIGINAL_MODEL_IC_TARGET"),
            "changed-counter" => {
                let row = b.values[0]
                    .as_array_mut()
                    .unwrap()
                    .iter_mut()
                    .find(|r| r["kind"] == "N4_ORIGINAL_MODEL_IC_ATTEMPT")
                    .unwrap();
                let stat = row["data"]["report"]["stats"]
                    .as_array_mut()
                    .unwrap()
                    .iter_mut()
                    .find(|r| r[0] != "wall_total" && r[1].is_number())
                    .unwrap();
                stat[1] = json!(stat[1].as_f64().unwrap() + 1.0);
                let report = row["data"]["report"].clone();
                b.values[1]["whole_calls"][0]["report"] = report.clone();
                journal[10]["data"] = report;
            }
            "changed-relation" => {
                let v = &mut b.values[1]["whole_calls"][0]["available"]["full_rows"][0][0][1];
                *v = json!((v.as_u64().unwrap() + 1) % 2_773_073);
                journal[1]["data"] = b.values[1]["whole_calls"][0]["available"].clone();
            }
            "changed-kernel" => {
                let v = &mut b.values[1]["whole_calls"][0]["kernel"]["actual_vector"][0];
                *v = json!((v.as_u64().unwrap() + 1) % 2_773_073);
                journal[3]["data"] = b.values[1]["whole_calls"][0]["kernel"].clone();
            }
            "missing-rank-call" => {
                b.values[2].as_array_mut().unwrap().remove(1);
            }
            "changed-character-scalar" => {
                let row = b.values[4]
                    .as_array_mut()
                    .unwrap()
                    .iter_mut()
                    .find(|v| v["kind"] == "call")
                    .unwrap();
                let v = &mut row["generator_witness"]["scalar"];
                *v = json!((v.as_u64().unwrap() + 1) % 2_773_073);
            }
            "unexpected-verdict-field" => {
                b.values[5]["unexpected_scientific_field"] = json!(0);
            }
            "unbound-linked-hash" => {}
            _ => unreachable!(),
        }
        fs::copy(
            base.join("original-baseline.json"),
            dir.join("original-baseline.json"),
        )
        .map_err(|e| e.to_string())?;
        fs::write(
            dir.join("native.txt"),
            rewrite_native(&native, &b.values[0])?,
        )
        .map_err(|e| e.to_string())?;
        let mut data = Vec::new();
        for row in journal.as_array().unwrap() {
            serde_json::to_writer(&mut data, row).map_err(|e| e.to_string())?;
            data.push(b'\n');
        }
        fs::write(dir.join("journal.jsonl"), data).map_err(|e| e.to_string())?;
        b.bind(&dir, name == "unbound-linked-hash")?;
        let files: Vec<_> = FILES
            .iter()
            .chain(["original-baseline.json", "native.txt", "journal.jsonl"].iter())
            .map(|n| {
                let data = fs::read(dir.join(n)).unwrap();
                json!({"path":dir.join(n),"bytes":data.len(),"sha256":hash(&data)})
            })
            .collect();
        manifest.push(json!({"name":name,"whole_bundle":dir,"expected_exit":if name=="timing-only"{0}else{1},"all_whole_files":files}));
    }
    fs::write(out.join("whole-control-bundles.json"),serde_json::to_vec_pretty(&json!({"base":base,"complete_controls":manifest,"historical_inputs_modified":false,"scope":"unsigned whole fresh-side variations; actual comparator subprocess exits and no-output checks are required separately"})).unwrap()).map_err(|e|e.to_string())
}
