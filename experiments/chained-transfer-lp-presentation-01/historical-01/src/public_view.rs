//! Whole-source binding is checked here, separately from matrix arithmetic.
use crate::{original_sha256, types::PublicCall};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashSet;

pub const ORIGINAL_BYTES: usize = 3_529_635;
pub const ORIGINAL_SHA256: &str =
    "57c1fa52a7c58768a907707aba54e025e1d911d3376423a7b87dd94bb1af9b8a";
const SCHEMA: &str = "complete-lp-public-relations/v1";

pub fn sha256(bytes: &[u8]) -> String {
    original_sha256::sha256(bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceBinding {
    pub bytes: usize,
    pub sha256: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "record", rename_all = "snake_case", deny_unknown_fields)]
enum Record {
    Header {
        schema: String,
        source: SourceBinding,
        call_count: usize,
    },
    Call {
        call: PublicCall,
    },
    Complete {
        call_count: usize,
        canonical_call_records_sha256: String,
    },
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PublicView {
    pub source: SourceBinding,
    pub calls: Vec<PublicCall>,
}

/// Only the three declared public fields are copied from the full private call.
pub fn project_call(value: &Value) -> Result<PublicCall, String> {
    let object = value.as_object().ok_or("original call must be an object")?;
    Ok(PublicCall {
        identity: serde_json::from_value(object.get("identity").ok_or("identity absent")?.clone())
            .map_err(|e| e.to_string())?,
        ell: serde_json::from_value(object.get("ell").ok_or("ell absent")?.clone())
            .map_err(|e| e.to_string())?,
        available: serde_json::from_value(
            object.get("available").ok_or("available absent")?.clone(),
        )
        .map_err(|e| e.to_string())?,
    })
}

fn project_document(bytes: &[u8]) -> Result<PublicView, String> {
    let whole: Value = serde_json::from_slice(bytes).map_err(|e| e.to_string())?;
    if whole["schema"] != "original-fixed-model-passive-relation-trace/v1" {
        return Err("original trace schema".into());
    }
    let raw = whole["whole_calls"]
        .as_array()
        .ok_or("whole_calls absent")?;
    if raw.len() != 60 {
        return Err("complete sixty-call population required".into());
    }
    let mut calls = Vec::new();
    let mut identities = HashSet::new();
    for value in raw {
        let call = project_call(value)?;
        call.validate_fixed()?;
        if !identities.insert(call.identity) {
            return Err("duplicate public identity".into());
        }
        calls.push(call);
    }
    Ok(PublicView {
        source: SourceBinding {
            bytes: bytes.len(),
            sha256: sha256(bytes),
        },
        calls,
    })
}

pub fn extract_original(bytes: &[u8]) -> Result<PublicView, String> {
    if bytes.len() != ORIGINAL_BYTES || sha256(bytes) != ORIGINAL_SHA256 {
        return Err("whole historical source does not match its immutable size/SHA pin".into());
    }
    project_document(bytes)
}

fn call_records(calls: &[PublicCall]) -> Result<Vec<u8>, String> {
    let mut body = Vec::new();
    for call in calls {
        serde_json::to_writer(&mut body, &Record::Call { call: call.clone() })
            .map_err(|e| e.to_string())?;
        body.push(b'\n');
    }
    Ok(body)
}

pub fn encode(view: &PublicView) -> Result<Vec<u8>, String> {
    if view.calls.len() != 60 {
        return Err("complete sixty-call view required".into());
    }
    let body = call_records(&view.calls)?;
    let mut output = serde_json::to_vec(&Record::Header {
        schema: SCHEMA.into(),
        source: view.source.clone(),
        call_count: 60,
    })
    .map_err(|e| e.to_string())?;
    output.push(b'\n');
    output.extend(&body);
    serde_json::to_writer(
        &mut output,
        &Record::Complete {
            call_count: 60,
            canonical_call_records_sha256: sha256(&body),
        },
    )
    .map_err(|e| e.to_string())?;
    output.push(b'\n');
    Ok(output)
}

pub fn parse(bytes: &[u8]) -> Result<PublicView, String> {
    let complete = bytes
        .strip_suffix(b"\n")
        .ok_or("public view requires final newline")?;
    let records: Vec<Record> = complete
        .split(|&b| b == b'\n')
        .map(|line| serde_json::from_slice(line).map_err(|e| e.to_string()))
        .collect::<Result<_, _>>()?;
    if records.len() != 62 {
        return Err("public view needs header,60 calls,mandatory footer".into());
    }
    let source = match &records[0] {
        Record::Header {
            schema,
            source,
            call_count: 60,
        } if schema == SCHEMA => source.clone(),
        _ => return Err("public header".into()),
    };
    let mut identities = HashSet::new();
    let mut calls = Vec::new();
    for record in &records[1..61] {
        let Record::Call { call } = record else {
            return Err("public call record order".into());
        };
        call.validate_fixed()?;
        if !identities.insert(call.identity) {
            return Err("duplicate public identity".into());
        }
        calls.push(call.clone());
    }
    let body = call_records(&calls)?;
    match &records[61] {
        Record::Complete {
            call_count: 60,
            canonical_call_records_sha256,
        } if *canonical_call_records_sha256 == sha256(&body) => {}
        _ => return Err("public completion/hash".into()),
    }
    let view = PublicView { source, calls };
    if encode(&view)? != bytes {
        return Err("noncanonical or incomplete public encoding".into());
    }
    Ok(view)
}

/// The independent caller must supply the actual complete immutable source;
/// a self-asserted header digest alone is never accepted as source binding.
pub fn bind_original(original: &[u8], public: &[u8]) -> Result<PublicView, String> {
    let expected = extract_original(original)?;
    let actual = parse(public)?;
    if expected != actual {
        return Err("public view differs from the actual complete source".into());
    }
    Ok(actual)
}

/// Control-only entry: primary is still required to match the historical pin.
/// Every private call field becomes the same fixed null/string canary. Public
/// bodies must remain exact; this never accepts control bytes as the primary.
pub fn extract_feedback_control(original: &[u8], control: &[u8]) -> Result<PublicView, String> {
    let primary = extract_original(original)?;
    let original_value: Value = serde_json::from_slice(original).map_err(|e| e.to_string())?;
    let control_value: Value = serde_json::from_slice(control).map_err(|e| e.to_string())?;
    let a = original_value.as_object().ok_or("primary object")?;
    let b = control_value.as_object().ok_or("control object")?;
    if a.keys().collect::<Vec<_>>() != b.keys().collect::<Vec<_>>() {
        return Err("control whole-source keys".into());
    }
    for (key, value) in a {
        if key != "whole_calls" && b.get(key) != Some(value) {
            return Err("control changed noncall source data".into());
        }
    }
    let raw = a["whole_calls"].as_array().ok_or("primary calls")?;
    let changed = b["whole_calls"].as_array().ok_or("control calls")?;
    if raw.len() != changed.len() {
        return Err("control call count".into());
    }
    for (old, new) in raw.iter().zip(changed) {
        let old = old.as_object().ok_or("primary call")?;
        let new = new.as_object().ok_or("control call")?;
        if old.keys().collect::<Vec<_>>() != new.keys().collect::<Vec<_>>() {
            return Err("control call keys".into());
        }
        for (key, value) in new {
            if !["identity", "ell", "available"].contains(&key.as_str())
                && !value.is_null()
                && value.as_str() != Some("LP_PRIVATE_FIELD_CANARY")
            {
                return Err("every private field must use the fixed canary".into());
            }
        }
    }
    let result = project_document(control)?;
    if result.calls != primary.calls {
        return Err("private feedback changed public bodies".into());
    }
    Ok(result)
}
