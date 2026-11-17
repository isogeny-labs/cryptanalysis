//! CT172: full 48-real-public-packet parity and counter replay (no benchmark).
//! Producer-only evidence. No known scalar is supplied to any runtime method.
use chained_n4_fixed_jacobian_chain::norm::EncodedClass;
use chained_n4_fixed_jacobian_chain_norm_reuse::Runtime;
use chained_n4_public_target::CheckedInstance;
use serde_json::{json, Value};
use std::collections::BTreeSet;
use std::hint::black_box;
use std::time::Instant;

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


/* CT174 prospective source-only implementation of the frozen paired-price protocol.
 * This code must not run until the original native/admission budget gates permit it.
 * It uses actual CT125 routines, not a fresh substitute norm/map evaluator. */
fn sample_route(runtime: &Runtime, packet: &EncodedClass, from: usize, to: usize,
                arm: &str, expected: &Value) -> Result<Value, String> {
    runtime.reset_calls();
    let t = Instant::now();
    let input = runtime.admit(from, packet)?;
    let output = match arm {
        "direct_composite" => runtime.transfer_entry(&input, to)?,
        "strongest_retained_lift_chain" => runtime.retained_lift_entry(&input, to)?,
        _ => return Err("CT174: unexpected timed route".to_owned()),
    };
    let final_key = runtime.check_final(&output)?.key;
    black_box(&final_key);
    let elapsed_ns = t.elapsed().as_nanos();
    must(final_key == key(&expected["whole_outputs_equal"], "CT174 expected output")?,
         "CT174: source/target canonical output mismatch")?;
    let calls = json!(runtime.calls());
    must(calls == expected[arm], "CT174: real native cost-counter mismatch")?;
    Ok(json!({"elapsed_ns_decimal": elapsed_ns.to_string(),
              "complete_counter_match": true}))
}

fn peak_rss_kib() -> Option<u64> {
    let raw = std::fs::read_to_string("/proc/self/status").ok()?;
    raw.lines().find_map(|line| {
        line.strip_prefix("VmHWM:")?.split_whitespace().next()?.parse::<u64>().ok()
    })
}

fn toolchain_version() -> Option<String> {
    let output = std::process::Command::new("rustc").arg("--version").output().ok()?;
    if !output.status.success() { return None; }
    Some(String::from_utf8_lossy(&output.stdout).trim().to_owned())
}

fn paired_price(runtime: &Runtime, rows: &[Value], setup_ns: u128) -> Result<Value, String> {
    const A: &str = "direct_composite";
    const B: &str = "strongest_retained_lift_chain";
    let mut result = Vec::with_capacity(rows.len());
    for (i, row) in rows.iter().enumerate() {
        let (from, to, sector, scalar_label) = cohort(row)?;
        let source = &runtime.geometry.models[from].prime;
        let packet = EncodedClass {
            field: source.field_tag.clone(),
            model: source.model_tag.clone(),
            key: key(&row["input"], "CT174 actual source packet")?,
        };
        // Actual ABBA sequence: all routes include admission, map/corrections,
        // final norm/order check and output, not JSON serialization.
        let order = [A, B, B, A];
        let mut abba = Vec::with_capacity(4);
        for arm in order {
            abba.push(json!({"arm":arm, "sample":sample_route(
                runtime, &packet, from, to, arm, row)?}));
        }
        // A/A control is a separately measured pair on the same operand/host.
        let aa = [
            sample_route(runtime, &packet, from, to, A, row)?,
            sample_route(runtime, &packet, from, to, A, row)?,
        ];
        let target = &runtime.geometry.models[to].prime;
        let encoded_target = EncodedClass {
            field: target.field_tag.clone(),
            model: target.model_tag.clone(),
            key: key(&row["whole_outputs_equal"], "CT174 real target key")?,
        };
        runtime.reset_calls();
        let start_inv = Instant::now();
        let inverse = runtime.inverse_of(from, to, &encoded_target)?;
        black_box(&inverse.key);
        let inverse_ns = start_inv.elapsed().as_nanos();
        must(inverse.key == packet.key,
             format!("CT174: row {i} explicit inverse wrong"))?;
        result.push(json!({
            "index":i, "from":from, "to":to, "sector":sector,
            "scalar_label_outside_runtime":scalar_label,
            "abba":abba, "aa":aa,
            "inverse_ns_decimal":inverse_ns.to_string(),
            "inverse_counters":runtime.calls(),
            "public_output_verified":true
        }));
    }
    Ok(json!({
        "schema":"ct174-native-selected48-paired-route-price/v1",
        "standing":"[pcc:unverified]",
        "scope":"warm same-process real CT125 route pricing; NOT individual N2/C169/C13 timers, cold solve, independent replay or signed PCC",
        "original_public_packets":rows.len(),
        "samples_per_packet":{"direct":4,"retained":2,"inverse":1},
        "same_process_setup_ns_decimal":setup_ns.to_string(),
        "peak_rss_kib_linux":peak_rss_kib(),
        "target_arch":std::env::consts::ARCH,
        "target_os":std::env::consts::OS,
        "rustc_version_if_present":toolchain_version(),
        "raw_rows":result
    }))
}

fn run() -> Result<(), String> {
    // This clock starts before public fixture validation and native geometry setup.
    // It excludes OS process loading and final stdout serialization.
    let started_in_process = Instant::now();
    let args = std::env::args().skip(1).collect::<Vec<_>>();
    let cold_requested = args.first().is_some_and(|a| a == "--cold-route");
    must(args.is_empty() ||
         (args.len() == 1 && (args[0] == "--self-test" || args[0] == "--paired-price")) ||
         (args.len() == 3 && cold_requested),
         "usage: ct172-replay [--self-test|--paired-price|--cold-route INDEX ARM]")?;
    let data: Value = serde_json::from_str(FROZEN).map_err(|e| e.to_string())?;
    must(data.as_object().is_some_and(|d| d.len() == 2
         && d.contains_key("all48") && d.contains_key("scope")),
         "frozen fixture schema mismatch")?;
    let rows = data["all48"].as_array().ok_or("all48 must be an array")?;
    validate_grid(rows)?;
    let started_setup = Instant::now();
    let checked = CheckedInstance::construct().map_err(|e| e.to_string())?;
    let runtime = Runtime::construct(&checked)?;
    let setup_ns = started_setup.elapsed().as_nanos();
    if cold_requested {
        let literal_index = &args[1];
        must(!literal_index.is_empty() && literal_index.bytes().all(|b| b.is_ascii_digit()),
             "CT175: packet index must be canonical decimal digits")?;
        let index = literal_index.parse::<usize>()
            .map_err(|_| "CT175: packet index overflow")?;
        must(index.to_string() == *literal_index, "CT175: packet index must be canonical")?;
        let row = rows.get(index).ok_or("CT175: packet index outside frozen 48")?;
        let arm = args[2].as_str();
        must(matches!(arm, "direct_composite" | "strongest_retained_lift_chain"),
             "CT175: arm must be direct_composite or strongest_retained_lift_chain")?;
        let (from, to, sector, scalar_label) = cohort(row)?;
        let source = &runtime.geometry.models[from].prime;
        let packet = EncodedClass {
            field: source.field_tag.clone(),
            model: source.model_tag.clone(),
            key: key(&row["input"], "CT175 public source packet")?,
        };
        // Crucially no observe(48), no inverse, no known-scalar multiplication
        // and no warmup precede this one selected native transfer.
        let native_sample = sample_route(&runtime, &packet, from, to, arm, row)?;
        let actual_calls = json!(runtime.calls());
        must(actual_calls == row[arm], "CT175: actual complete counters changed")?;
        let expected_output = key(&row["whole_outputs_equal"], "CT175 canonical output")?;
        let total_ns = started_in_process.elapsed().as_nanos();
        println!("{}", json!({
            "schema":"ct175-single-public-packet-cold-route/v1",
            "standing":"[pcc:unverified]",
            "scope":"one fresh in-process CT125 public-packet transfer; not external cold wall, a complete ECDLP, or independent signed execution",
            "packet_index":index, "from":from, "to":to,
            "sector":sector, "scalar_label_outside_runtime":scalar_label,
            "arm":arm, "public_source_packet":packet.key,
            "verified_canonical_target":expected_output,
            "native_sample":native_sample,
            "native_calls":actual_calls,
            "fixture_rows_checked":rows.len(),
            "preflight_native_routes":0,
            "preflight_native_inverses":0,
            "same_process_setup_ns_decimal":setup_ns.to_string(),
            "in_process_total_ns_decimal":total_ns.to_string(),
            "external_os_loader_wall_included":false,
            "peak_rss_kib_linux":peak_rss_kib(),
            "target_arch":std::env::consts::ARCH,
            "target_os":std::env::consts::OS,
            "rustc_version_if_present":toolchain_version()
        }));
        return Ok(());
    }
    let mut observations = Vec::with_capacity(48);
    for (i, row) in rows.iter().enumerate() {
        let obs = observe(&runtime, row).map_err(|e| format!("row {i}: {e}"))?;
        audit(row, &obs).map_err(|e| format!("row {i}: {e}"))?;
        observations.push(obs);
    }
    if args.first().is_some_and(|v| v == "--paired-price") {
        println!("{}", paired_price(&runtime, rows, setup_ns)?);
        return Ok(());
    }
    let rejected = if args.first().is_some_and(|v| v == "--self-test") {
        controls(rows, &observations)?
    } else { 0 };
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
