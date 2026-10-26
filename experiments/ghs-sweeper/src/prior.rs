//! Frozen local history is a deduplication aid, never a novelty certificate.
use crate::search::{Candidate, Model};
use anyhow::Result;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::BTreeMap;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SourceClass {
    pub absolute_degree: u32,
    pub trace: i64,
    pub historical_witness_paths: Vec<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Snapshot {
    pub scope: String,
    pub inputs_sha256: BTreeMap<String, String>,
    pub spectral_controls: BTreeMap<String, String>,
    pub source_classes: BTreeMap<String, SourceClass>,
}
pub fn snapshot() -> Result<Snapshot> {
    let mut result = Snapshot {
        scope: "Frozen prototype fixtures only. Catalogue map witnesses are not vendored. Local absence proves no publication novelty.".into(),
        inputs_sha256: BTreeMap::new(), spectral_controls: BTreeMap::new(), source_classes: BTreeMap::new(),
    };
    let catalogue = include_bytes!("../reference/prototype-catalogue.csv");
    result.inputs_sha256.insert(
        "reference/prototype-catalogue.csv".into(),
        crate::digest(catalogue),
    );
    let mut reader = csv::Reader::from_reader(&catalogue[..]);
    for record in reader.deserialize::<BTreeMap<String, String>>() {
        let record = record?;
        if record["affected"] != "True" || record["source_log_independently_verified"] != "True" {
            continue;
        }
        let degree: u32 = record["n"].parse()?;
        let trace = (1_i64 << degree) + 1 - record["source_order"].parse::<i64>()?;
        let class = result
            .source_classes
            .entry(format!("{degree}:{trace}"))
            .or_insert_with(|| SourceClass {
                absolute_degree: degree,
                trace,
                historical_witness_paths: Vec::new(),
            });
        let path = format!("prototype:{}", record["witness_json"]);
        if !class.historical_witness_paths.contains(&path) {
            class.historical_witness_paths.push(path);
        }
    }
    for (d, name, bytes) in [
        (
            1,
            "reference/f2-genus5.json",
            include_bytes!("../reference/f2-genus5.json").as_slice(),
        ),
        (
            2,
            "reference/f4-genus5.json",
            include_bytes!("../reference/f4-genus5.json").as_slice(),
        ),
    ] {
        result
            .inputs_sha256
            .insert(name.into(), crate::digest(bytes));
        let data: Value = serde_json::from_slice(bytes)?;
        for old in data["candidates"].as_array().unwrap() {
            let model = if d == 1 {
                Model {
                    base_degree: 1,
                    relative_degree: 5,
                    genus: 5,
                    h: crate::field::decode(old["H"].as_u64().unwrap() as u32, 6, 1),
                    r: crate::field::decode(old["R"].as_u64().unwrap() as u32, 5, 1),
                    a: 1,
                    c: old["c"].as_u64().unwrap() as u32,
                }
            } else {
                Model {
                    base_degree: 2,
                    relative_degree: 5,
                    genus: 5,
                    h: serde_json::from_value(old["H"].clone())?,
                    r: serde_json::from_value(old["numerator"].clone())?,
                    a: old["leading"].as_u64().unwrap() as u32,
                    c: old["constant"].as_u64().unwrap() as u32,
                }
            };
            result
                .spectral_controls
                .insert(crate::identifier(&model)?, name.into());
        }
    }
    Ok(result)
}
pub fn overlap(saved: &Snapshot, c: &Candidate) -> Value {
    let degree = c.model.base_degree * c.model.relative_degree;
    let t = c.elliptic_trace;
    let exact = saved.source_classes.get(&format!("{degree}:{t}"));
    let twist = saved.source_classes.get(&format!("{degree}:{}", -t));
    json!({"previous_local_spectral_record":saved.spectral_controls.get(&c.spectral_model_id),
        "source_isogeny_class_in_local_catalogue":exact,"quadratic_twist_class_in_local_catalogue":twist,
        "local_source_class_overlap":exact.is_some() || twist.is_some(),"scope":saved.scope})
}
