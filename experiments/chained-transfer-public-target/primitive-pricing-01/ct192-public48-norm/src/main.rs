//! CT192 scalar-blind 48-public-packet norm operand panel.
//! This is a source-only instrument until admitted native execution.
//! Produces no ECDLP answer and is NOT independent PCC.
use chained_n4_fixed_jacobian_chain::norm::EncodedClass;
use chained_n4_fixed_jacobian_chain_norm_reuse_ct192::Runtime;
use chained_n4_paired_fourth_preflight::models::even::back6;
use chained_n4_public_target::CheckedInstance;
use isogeny_algos::{curve::{self, Pt}, fpr::ER};
use serde_json::{json, Value};
use std::{collections::BTreeSet, hint::black_box, time::Instant};

const FROZEN: &str = include_str!(
    "../../../evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json"
);
const SCALARS: [u64; 6] = [0, 1, 2, 17, 12_345, 2_771_710];
const ROUTES: [&str; 2] = ["direct_composite", "strongest_retained_lift_chain"];
const ORIGINAL_BLOB: &str = "b80eb91a39ae1e87f0fcde95e52ea3d3634558bc";
const FROZEN_BLOB: &str = "9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3";

fn must(ok: bool, why: impl Into<String>) -> Result<(), String> {
    if ok { Ok(()) } else { Err(why.into()) }
}
fn number(v: &Value, name: &str) -> Result<u64, String> {
    v.as_u64().ok_or_else(|| format!("{name}: expected integer"))
}
fn key(v: &Value) -> Result<[u32; 19], String> {
    serde_json::from_value(v.clone()).map_err(|e| format!("canonical 19-u32 key: {e}"))
}
fn cohort(row: &Value) -> Result<(usize, usize, usize, u64), String> {
    let map = row.as_object().ok_or("row is not an object")?;
    let expected = ["from", "to", "sector", "scalar_OUTSIDE_runtime", "input",
                    "whole_outputs_equal", "direct_composite",
                    "literal_sequential_Jacobian_maps",
                    "strongest_retained_lift_chain"];
    must(map.len() == expected.len() &&
         expected.iter().all(|name| map.contains_key(*name)), "cohort schema changed")?;
    let from = usize::try_from(number(&row["from"], "from")?).map_err(|e| e.to_string())?;
    let to = usize::try_from(number(&row["to"], "to")?).map_err(|e| e.to_string())?;
    let sector = usize::try_from(number(&row["sector"], "sector")?).map_err(|e| e.to_string())?;
    let label = number(&row["scalar_OUTSIDE_runtime"], "scalar label")?;
    must(matches!((from, to), (0, 2) | (2, 0)) &&
         sector < 4 && SCALARS.contains(&label), "unexpected original cohort")?;
    key(&row["input"])?;
    key(&row["whole_outputs_equal"])?;
    for arm in ["direct_composite", "literal_sequential_Jacobian_maps",
                "strongest_retained_lift_chain"] {
        let c = row[arm].as_object().ok_or("missing complete counter dictionary")?;
        must(c.len() == 21 && c.values().all(|v| v.as_u64().is_some()),
             "changed 21-counter native fixture")?;
    }
    Ok((from, to, sector, label))
}
fn validate_grid(rows: &[Value]) -> Result<(), String> {
    must(rows.len() == 48, "expected exactly 48 packets")?;
    let mut labels = BTreeSet::new();
    let mut public = BTreeSet::new();
    for row in rows {
        let (from, to, sector, label) = cohort(row)?;
        must(labels.insert((from, to, sector, label)), "duplicate cohort")?;
        must(public.insert((from, to, key(&row["input"])?)),
             "duplicate public source packet")?;
    }
    for from_to in [(0usize, 2usize), (2, 0)] {
        for sector in 0..4 {
            for label in SCALARS {
                must(labels.contains(&(from_to.0, from_to.1, sector, label)),
                     "missing frozen grid cohort")?;
            }
        }
    }
    must(labels.iter().filter(|(_, _, _, label)| *label == 0).count() == 8,
         "eight exceptional rows required")?;
    Ok(())
}
fn descend(p: Pt<ER>) -> Pt<ER> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => Pt::Aff(back6(x), back6(y)),
    }
}
fn vmhwm_kib() -> Option<u64> {
    let file = std::fs::read_to_string("/proc/self/status").ok()?;
    file.lines().find_map(|line| {
        line.strip_prefix("VmHWM:")?
            .split_whitespace().next()?.parse::<u64>().ok()
    })
}
fn run() -> Result<(), String> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.is_empty() || (args.len() == 1 && args[0] == "--plan") {
        println!("{}", json!({
            "schema":"ct192-public48-norm-plan/v1",
            "standing":"[pcc:unverified]",
            "status":"no native arithmetic or timing executed",
            "public_packets":48, "physical_routes":2, "operands":96,
            "warmup_blocks":4, "measured_blocks":12,
            "four_slot_samples_per_block":4,
            "repetitions_per_slot":64, "expected_measured_slots":4608,
            "source_git_blob":ORIGINAL_BLOB,"fixture_git_blob":FROZEN_BLOB
        }));
        return Ok(());
    }
    must(args.len() == 1 && args[0] == "--run-admitted",
         "usage: ct192-public48-norm [--plan|--run-admitted]")?;
    // Explicit external approval is necessary but cannot be established by
    // an environmental assertion alone; caller/provider must check it.
    let admission = std::env::var("CT192_OWNER_ADMISSION_RECEIPT")
        .map_err(|_| "missing external owner/provider admission receipt")?;
    must(!admission.trim().is_empty(), "empty admission receipt")?;
    let total_start = Instant::now();
    let data: Value = serde_json::from_str(FROZEN).map_err(|e| e.to_string())?;
    must(data.as_object().is_some_and(|m| m.len() == 2 &&
         m.contains_key("all48") && m.contains_key("scope")),
         "changed top-level frozen fixture schema")?;
    let rows = data["all48"].as_array().ok_or("all48 is not an array")?;
    validate_grid(rows)?;
    let setup_start = Instant::now();
    let checked = CheckedInstance::construct().map_err(|e| e.to_string())?;
    let runtime = Runtime::construct(&checked)?;
    let setup_ns = setup_start.elapsed().as_nanos();
    let mut operands: Vec<(usize, usize, usize, u64, &str, Pt<ER>)> = Vec::new();
    for (index, row) in rows.iter().enumerate() {
        let (from, to, sector, external_label) = cohort(row)?;
        let source = &runtime.geometry.models[from].prime;
        let packet = EncodedClass {
            field: source.field_tag.clone(), model: source.model_tag.clone(),
            key: key(&row["input"])?,
        };
        for arm in ROUTES {
            // Critically: no source scalar or known generator is used to build
            // this operand; only the full 19-word public class is admitted.
            let operand = runtime.ct192_pre_norm_operand(from, to, &packet, arm)?;
            runtime.reset_calls();
            let admitted = runtime.admit(from, &packet)?;
            let entry = if arm == ROUTES[0] {
                runtime.transfer_entry(&admitted, to)?
            } else {
                runtime.retained_lift_entry(&admitted, to)?
            };
            let full = runtime.check_final(&entry)?;
            must(full.key == key(&row["whole_outputs_equal"])?,
                 format!("row {index} {arm}: canonical target mismatch"))?;
            must(json!(runtime.calls()) == row[arm],
                 format!("row {index} {arm}: exact native calls mismatch"))?;
            let target = &runtime.geometry.models[to].quadratic;
            let proxy = curve::padd(&target.f, &target.curve, &operand, &operand);
            let actual = runtime.ct192_actual_norm(to, operand);
            must(actual == descend(proxy),
                 format!("row {index} {arm}: N2 actual != descended D_padd"))?;
            operands.push((index, to, sector, external_label, arm, operand));
        }
    }
    must(operands.len() == 96, "expected 96 route-specific true operands")?;
    // Only the precomputed true target operands are timed. Every physical
    // route, direction, sector, and exceptional input retains raw records.
    let mut all = Vec::with_capacity(96);
    for (index, to, sector, external_label, arm, point) in operands {
        let target = &runtime.geometry.models[to].quadratic;
        let mut slots = Vec::with_capacity(64);
        for block in 0..16 {
            let order = if block % 2 == 0 {
                ["N2_actual", "D_padd", "D_padd", "N2_actual"]
            } else {
                ["D_padd", "N2_actual", "N2_actual", "D_padd"]
            };
            for (slot, treatment) in order.iter().enumerate() {
                let start = Instant::now();
                for _ in 0..64 {
                    match *treatment {
                        "N2_actual" => black_box(runtime.ct192_actual_norm(to, point)),
                        "D_padd" => black_box(curve::padd(
                            &target.f, &target.curve, &point, &point)),
                        _ => return Err("unexpected assigned treatment".into()),
                    };
                }
                let ns = start.elapsed().as_nanos();
                slots.push(json!({
                    "block":block, "slot":slot, "arm":treatment,
                    "recorded":block >= 4, "repetitions":64,
                    "raw_slot_ns_decimal":ns.to_string()
                }));
            }
        }
        all.push(json!({
            "packet_index":index, "target":to, "sector":sector,
            "scalar_label_outside_runtime":external_label,
            "physical_transfer_route":arm,
            "raw_slots":slots
        }));
    }
    println!("{}", json!({
        "schema":"ct192-public48-actual-norm-price/v1",
        "standing":"[pcc:unverified]",
        "scope":"same-process warm N2_actual vs D_padd, 48 selected public inputs x 2 routes; no complete ECDLP",
        "source_git_blob":ORIGINAL_BLOB, "fixture_git_blob":FROZEN_BLOB,
        "admission_producer_asserted_only":true,
        "public_packets":48, "true_route_operands":96,
        "same_process_setup_ns_decimal":setup_ns.to_string(),
        "in_process_total_ns_decimal":total_start.elapsed().as_nanos().to_string(),
        "peak_rss_kib_linux":vmhwm_kib(),
        "target_arch":std::env::consts::ARCH, "target_os":std::env::consts::OS,
        "raw_operands":all, "complete_single_target_ecdlp_solved":false
    }));
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("CT192 REFUSED: {e}");
        std::process::exit(1);
    }
}
