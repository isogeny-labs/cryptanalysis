//! Supplemental dispatcher. The frozen exact-m benchmark path is unchanged.
use super::{build, solver, Encoding, Input, Schedule};
use serde_json::{json, Value};
use std::time::{Duration, Instant};

/// Search the original signed base at lengths0..max_m with one absolute
/// deadline, including construction, F4, recovery, and final verification.
/// Positive results are witnesses; nonpositive results remain incomplete.
pub fn run_up_to(
    input: &Input,
    max_m: usize,
    encoding: Encoding,
    schedule: Schedule,
    total_budget: Duration,
    max_degree: u32,
    construction_cap: Duration,
) -> Result<Value, String> {
    let started = Instant::now();
    let deadline = started + total_budget;
    input.validate()?;
    if !(2..=4).contains(&max_m) || max_degree == 0 {
        return Err("up-to search requires m2..4 and positive degree".into());
    }
    let mut reports = Vec::<Value>::new();
    let mut issues = Vec::<Value>::new();
    let mut found: Option<(usize, Value)> = None;
    if Instant::now() >= deadline {
        issues.push(json!({"reason":"shared_total_deadline","length":0}));
    } else if input.target.is_none() {
        reports.push(
            json!({"length":0,"method":"public identity check","status":"verified_direct_witness"}),
        );
        found = Some((0, json!({"x":[],"signs":[],"group_verified":true})));
    } else {
        reports.push(json!({"length":0,"method":"public identity check","status":"finite_target"}));
        let target = input.target.unwrap();
        let matched = input.base.iter().enumerate().find_map(|(i, &p)| {
            if p == target {
                Some((i, 1))
            } else if p[0] == target[0] && (input.p - p[1]) % input.p == target[1] {
                Some((i, -1))
            } else {
                None
            }
        });
        if Instant::now() >= deadline {
            issues.push(json!({"reason":"shared_total_deadline","length":1}));
        } else if let Some((index, sign)) = matched {
            reports.push(json!({"length":1,"method":"public signed-base membership","status":"verified_direct_witness"}));
            found = Some((
                1,
                json!({"x":[target[0]],"signs":[sign],"base_indices":[index],"group_verified":true}),
            ));
        } else {
            reports.push(json!({"length":1,"method":"public signed-base membership","status":"not_in_signed_base"}));
            for length in 2..=max_m {
                let remaining = deadline.saturating_duration_since(Instant::now());
                if remaining.is_zero() {
                    issues.push(json!({"length":length,"reason":"shared_total_deadline"}));
                    break;
                }
                let construction_started = Instant::now();
                let system = match build(input, length, encoding, remaining.min(construction_cap)) {
                    Ok(system) => system,
                    Err(error) => {
                        reports.push(json!({"length":length,"status":"construction_incomplete","reason":error,"construction_ns":construction_started.elapsed().as_nanos()}));
                        issues.push(json!({"length":length,"reason":"construction_incomplete"}));
                        continue;
                    }
                };
                if Instant::now() >= deadline {
                    reports.push(json!({"length":length,"status":"construction_consumed_shared_deadline","construction_ns":system.construction_ns,"scope":system.scope}));
                    issues.push(json!({"length":length,"reason":"shared_total_deadline"}));
                    break;
                }
                // run_until does not start a fresh per-length allowance.
                let mut report = solver::run_until(&system, schedule, deadline, max_degree);
                report["length"] = json!(length);
                let over_deadline = Instant::now() >= deadline;
                report["shared_deadline_exceeded_after_validation"] = json!(over_deadline);
                let candidate = report
                    .get("verified")
                    .and_then(Value::as_array)
                    .and_then(|v| v.first())
                    .cloned();
                let status = report["status"].as_str().unwrap_or("unknown").to_owned();
                reports.push(report);
                if over_deadline {
                    issues.push(json!({"length":length,"reason":"shared_total_deadline"}));
                    break;
                }
                if let Some(witness) = candidate {
                    found = Some((length, witness));
                    break;
                }
                if !matches!(
                    status.as_str(),
                    "refuted_encoded_system_only" | "encoded_system_no_rational_group_witness"
                ) {
                    issues.push(json!({"length":length,"reason":status}));
                }
            }
        }
    }
    let status = match found.as_ref() {
        Some((length, _)) if *length < max_m => "found_shorter",
        Some(_) => "found_decomposition",
        None => "incomplete",
    };
    let total_construction_ns = reports
        .iter()
        .filter_map(|r| r["construction_ns"].as_u64())
        .sum::<u64>();
    let total_f4_ns = reports
        .iter()
        .filter_map(|r| r["f4_ns"].as_u64())
        .sum::<u64>();
    let total_root_recovery_ns = reports
        .iter()
        .filter_map(|r| r["root_recovery_ns"].as_u64())
        .sum::<u64>();
    let total_group_validation_ns = reports
        .iter()
        .filter_map(|r| r["independent_group_validation_ns"].as_u64())
        .sum::<u64>();
    Ok(
        json!({"schema":"m31-relation-encodings-up-to/v1","producer_only":true,"supplemental_control_only":true,
        "search_mode":"up_to_m","status":status,"input":input,"m":max_m,"encoding":encoding,"schedule":schedule,
        "total_budget_ms":total_budget.as_millis(),"deadline_policy":"one absolute deadline; construction+F4+recovery+validation; late candidates are not accepted",
        "elapsed_ns":started.elapsed().as_nanos(),"first_found_length":found.as_ref().map(|(m,_)|m),"verified_witness":found.map(|(_,w)|w),
        "length_reports":reports,"unresolved_lengths":issues,"total_construction_ns":total_construction_ns,"total_f4_ns":total_f4_ns,
        "total_root_recovery_ns":total_root_recovery_ns,"total_group_validation_ns":total_group_validation_ns,
        "coverage":"Original public signed leaf domain at every length. Minimal rational decompositions have no zero-sum subset, so searching shorter lengths addresses identity cancellations; finite charts and bounded solving outcomes remain explicit. No nonpositive output asserts general absence or global ECDLP hardness.",
        "nonpositive_policy":"incomplete even when encoded lengths are refuted; inspect per-length chart scope, degree bounds and recovery status"}),
    )
}
