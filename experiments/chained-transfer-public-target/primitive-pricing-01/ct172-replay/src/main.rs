//! CT172: full 48-real-public-packet parity and counter replay (no benchmark).
//! Producer-only evidence. No known scalar is supplied to any runtime method.
use chained_n4_fixed_jacobian_chain::norm::EncodedClass;
use chained_n4_fixed_jacobian_chain_norm_reuse::Runtime;
use chained_n4_public_target::CheckedInstance;
use serde_json::{json, Value};
use std::collections::BTreeSet;

const FROZEN: &str = include_str!(
    "../../../evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json"
);
const SCALARS: [u64; 6] = [0, 1, 2, 17, 12_345, 2_771_710];
const ROUTES: [&str; 3] = [
    "direct_composite",
    "literal_sequential_Jacobian_maps",
    "strongest_retained_lift_chain",
];

fn must(ok: bool, message: impl Into<String>) -> Result<(), String> {
    if ok { Ok(()) } else { Err(message.into()) }
}

fn unsigned(v: &Value, label: &str) -> Result<u64, String> {
    v.as_u64().ok_or_else(|| format!("{label}: expected nonnegative JSON integer"))
}

fn key(v: &Value, label: &str) -> Result<[u32; 19], String> {
    serde_json::from_value(v.clone())
        .map_err(|e| format!("{label}: expected exactly 19 u32 words: {e}"))
}

fn cohort(row: &Value) -> Result<(usize, usize, usize, u64), String> {
    let obj = row.as_object().ok_or("cohort: expected JSON object")?;
    let fields = [
        "from", "to", "sector", "scalar_OUTSIDE_runtime", "input",
        "whole_outputs_equal", ROUTES[0], ROUTES[1], ROUTES[2],
    ];
    must(obj.len() == fields.len() && fields.iter().all(|k| obj.contains_key(*k)),
         "cohort: field set mismatch")?;
    let from = usize::try_from(unsigned(&row["from"], "from")?).map_err(|e| e.to_string())?;
    let to = usize::try_from(unsigned(&row["to"], "to")?).map_err(|e| e.to_string())?;
    let sector = usize::try_from(unsigned(&row["sector"], "sector")?).map_err(|e| e.to_string())?;
    let label = unsigned(&row["scalar_OUTSIDE_runtime"], "external scalar label")?;
    must(matches!((from, to), (0, 2) | (2, 0)), "invalid direction")?;
    must(sector < 4 && SCALARS.contains(&label), "unknown cofactor/scalar label")?;
    key(&row["input"], "input")?;
    key(&row["whole_outputs_equal"], "expected output")?;
    for route in ROUTES {
        must(row[route].is_object(), format!("{route}: absent counter dictionary"))?;
    }
    Ok((from, to, sector, label))
}

fn validate_grid(rows: &[Value]) -> Result<(), String> {
    must(rows.len() == 48, "fixture must have exactly 48 records")?;
    let mut labels = BTreeSet::new();
    let mut inputs = BTreeSet::new();
    for row in rows {
        let (from, to, sector, label) = cohort(row)?;
        must(labels.insert((from, to, sector, label)), "duplicate cohort")?;
        must(inputs.insert((from, to, key(&row["input"], "public input")?)),
             "duplicate public packet")?;
    }
    for (from, to) in [(0, 2), (2, 0)] {
        for sector in 0..4 {
            for label in SCALARS {
                must(labels.contains(&(from, to, sector, label)),
                     "missing direction/sector/scalar cohort")?;
            }
        }
    }
    must(labels.iter().filter(|(_, _, _, label)| *label == 0).count() == 8,
         "identity branch population differs from 8")?;
    Ok(())
}

fn route(runtime: &Runtime, packet: &EncodedClass, from: usize, to: usize,
         arm: &str) -> Result<Value, String> {
    runtime.reset_calls();
    let admitted = runtime.admit(from, packet)?;
    let out = match arm {
        "direct_composite" => runtime.transfer_entry(&admitted, to)?,
        "literal_sequential_Jacobian_maps" => runtime.sequential_entry(&admitted, to)?,
        "strongest_retained_lift_chain" => runtime.retained_lift_entry(&admitted, to)?,
        _ => return Err("unknown native route".to_owned()),
    };
    let public = runtime.check_final(&out)?;
    Ok(json!({"public_output": public.key, "calls": runtime.calls()}))
}

fn observe(runtime: &Runtime, row: &Value) -> Result<Value, String> {
    let (from, to, sector, label) = cohort(row)?;
    // Construct the packet solely from the frozen PUBLIC class key and true model tags.
    // The diagnostic scalar label is NEVER used for scalar multiplication or admission.
    let source = &runtime.geometry.models[from].prime;
    let packet = EncodedClass {
        field: source.field_tag.clone(),
        model: source.model_tag.clone(),
        key: key(&row["input"], "public packet")?,
    };
    let mut arms = serde_json::Map::new();
    for arm in ROUTES {
        arms.insert(arm.to_owned(), route(runtime, &packet, from, to, arm)?);
    }
    let public = EncodedClass {
        field: runtime.geometry.models[to].prime.field_tag.clone(),
        model: runtime.geometry.models[to].prime.model_tag.clone(),
        key: key(&arms[ROUTES[0]]["public_output"], "computed direct output")?,
    };
    // Full-group inverse after the three forward arms. Its cost is NOT included
    // in the forward call counters or presented as free recovery.
    let inverse = runtime.inverse_of(from, to, &public)?;
    must(inverse.key == packet.key, "full-group inverse failed")?;
    Ok(json!({
        "from": from, "to": to, "sector": sector,
        "scalar_label_outside_runtime": label,
        "input": packet.key, "arms": arms, "inverse_source_key": inverse.key
    }))
}

fn audit(row: &Value, obs: &Value) -> Result<(), String> {
    let (from, to, sector, label) = cohort(row)?;
    must(obs["from"] == json!(from) && obs["to"] == json!(to)
         && obs["sector"] == json!(sector)
         && obs["scalar_label_outside_runtime"] == json!(label),
         "cohort metadata mismatch")?;
    must(obs["input"] == row["input"], "public input changed")?;
    must(obs["inverse_source_key"] == row["input"], "round trip mismatch")?;
    for arm in ROUTES {
        must(obs["arms"][arm]["public_output"] == row["whole_outputs_equal"],
             format!("{arm}: complete 19-word public output differs"))?;
        must(obs["arms"][arm]["calls"] == row[arm],
             format!("{arm}: exact full native counter object differs"))?;
    }
    Ok(())
}

fn controls(rows: &[Value], observed: &[Value]) -> Result<usize, String> {
    let mut attacked = rows[0].clone();
    attacked["whole_outputs_equal"][0] = json!(999);
    must(audit(&attacked, &observed[0]).is_err(),
         "accepted falsified complete target key")?;
    attacked = rows[0].clone();
    attacked[ROUTES[2]]["transported_norm_doubling"] = json!(12);
    must(audit(&attacked, &observed[0]).is_err(),
         "accepted falsified transported doubling count")?;
    attacked = rows[0].clone();
    attacked["input"][0] = json!(999);
    must(audit(&attacked, &observed[0]).is_err(),
         "accepted falsified public input")?;
    attacked = rows[0].clone();
    attacked["scalar_OUTSIDE_runtime"] = json!(false);
    must(cohort(&attacked).is_err(), "accepted scalar bool")?;
    attacked = rows[0].clone();
    attacked["from"] = json!(2);
    must(cohort(&attacked).is_err(), "accepted invalid direction")?;
    attacked = rows[0].clone();
    attacked["extra_claim"] = json!(1);
    must(cohort(&attacked).is_err(), "accepted unexpected evidence field")?;
    let mut duplicates = rows.to_vec();
    duplicates[1] = duplicates[0].clone();
    must(validate_grid(&duplicates).is_err(), "accepted duplicated cohort")?;
    let mut truncated = rows.to_vec();
    truncated.pop();
    must(validate_grid(&truncated).is_err(), "accepted missing cohort")?;
    Ok(8)
}

fn run() -> Result<(), String> {
    let args = std::env::args().skip(1).collect::<Vec<_>>();
    must(args.is_empty() || args == ["--self-test"], "usage: ct172-replay [--self-test]")?;
    let data: Value = serde_json::from_str(FROZEN).map_err(|e| e.to_string())?;
    must(data.as_object().is_some_and(|d| d.len() == 2
         && d.contains_key("all48") && d.contains_key("scope")),
         "frozen fixture schema mismatch")?;
    let rows = data["all48"].as_array().ok_or("all48 must be an array")?;
    validate_grid(rows)?;
    let checked = CheckedInstance::construct().map_err(|e| e.to_string())?;
    let runtime = Runtime::construct(&checked)?;
    let mut observations = Vec::with_capacity(48);
    for (i, row) in rows.iter().enumerate() {
        let obs = observe(&runtime, row).map_err(|e| format!("row {i}: {e}"))?;
        audit(row, &obs).map_err(|e| format!("row {i}: {e}"))?;
        observations.push(obs);
    }
    let rejected = if !args.is_empty() { controls(rows, &observations)? } else { 0 };
    println!("{}", json!({
        "schema": "ct172-real48-native-public-replay/v1",
        "standing": "[pcc:unverified]",
        "scope": "producer shared-evaluator native parity only; NOT independent, cold ECDLP or pricing",
        "actual_public_packets_replayed": observations.len(),
        "direction_0_to_2": 24,
        "direction_2_to_0": 24,
        "identity_rows": 8,
        "nonzero_rows": 40,
        "complete_native_counter_objects_verified": 144,
        "full_group_inverse_checks": 48,
        "in_memory_mutations_rejected": rejected,
        "observations": observations
    }));
    Ok(())
}

fn main() {
    if let Err(e) = run() {
        eprintln!("CT172 REFUSED: {e}");
        std::process::exit(1);
    }
}
