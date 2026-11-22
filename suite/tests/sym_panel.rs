//! Exit-criterion tests of the IR-derived technique panel (plan
//! `docs/plans/2026-11-21-generic-symmetric-cryptanalysis.md`, section 6):
//! `auto` runs a panel on AES-4r, PRESENT-5r, SPECK64/128-8r, 32-bit
//! ChaCha-6r and SHA-256-20-step, every applicable technique produces a row,
//! and the positive-control numbers appear in them. The numbers are
//! observations at the default budget, not claims.

use cryptanalysis_suite::cryptanalysis::auto_attack::{auto_attack, default_techniques};
use cryptanalysis_suite::cryptanalysis::cipher_registry::RegisteredCipher;
use cryptanalysis_suite::cryptanalysis::sym_techniques::applicable_techniques;
use serde_json::Value;
use std::process::Command;

/// Run the default panel and check the structural properties common to all
/// five ciphers; return the rows.
fn panel(name: &str) -> Vec<Value> {
    let t0 = std::time::Instant::now();
    let report = auto_attack(name).unwrap();
    let elapsed = t0.elapsed();
    assert!(
        elapsed.as_secs() < 60,
        "{name}: panel took {elapsed:?}, over the 60 s target"
    );
    let applicable: Vec<String> = {
        let c = RegisteredCipher::from_name(name).unwrap();
        applicable_techniques(c.primitive())
            .iter()
            .map(|t| t.as_str().to_string())
            .collect()
    };
    // One row per registered technique, in registration order.
    assert_eq!(report.rows.len(), default_techniques().len());
    for row in &report.rows {
        let t = row["technique"].as_str().unwrap();
        let should = applicable.iter().any(|a| a == t);
        assert_eq!(
            row["applicable"].as_bool().unwrap(),
            should,
            "{name}: row {t} disagrees with applicable_techniques"
        );
        if should {
            let st = row["result"]["outcome"]["status"].as_str();
            assert_ne!(st, Some("error"), "{name}: {t} panicked: {row}");
            assert!(row["result"]["cost"].is_object(), "{name}: {t} has no cost");
        }
    }
    // Every applicable technique has a row that ran.
    assert_eq!(
        report.sections_run,
        applicable.len(),
        "{name}: applicable {applicable:?}"
    );
    report.rows
}

fn row<'a>(rows: &'a [Value], t: &str) -> &'a Value {
    rows.iter().find(|r| r["technique"] == t).unwrap()
}

fn outcome<'a>(rows: &'a [Value], t: &str) -> &'a Value {
    let r = row(rows, t);
    assert_eq!(r["applicable"], true, "{t} should be applicable");
    &r["result"]["outcome"]
}

#[test]
fn aes_4r_panel() {
    let rows = panel("aes-4r");
    for t in [
        "differential_trails",
        "linear_trails",
        "milp_trails",
        "sat_trails",
    ] {
        let o = outcome(&rows, t);
        assert_eq!(o["status"], "ok", "{t}");
        assert_eq!(
            o["min_active_sboxes"], 25,
            "AES 4 rounds: 25 active S-boxes ({t})"
        );
    }
    for t in ["impossible_differential", "zero_correlation"] {
        let o = outcome(&rows, t);
        assert_eq!(o["status"], "ok", "{t}");
        assert_eq!(o["best"]["rounds"], 4, "AES 4-round {t}");
    }
    let d = outcome(&rows, "division_property");
    assert_eq!(d["best"]["rounds"], 3, "AES 3-round integral distinguisher");
    assert_eq!(outcome(&rows, "delta_set_mitm")["status"], "ok");
    assert_eq!(row(&rows, "arx_pnb")["applicable"], false);
}

#[test]
fn present80_5r_panel() {
    let rows = panel("present80-5r");
    for t in ["differential_trails", "sat_trails"] {
        let o = outcome(&rows, t);
        assert_eq!(o["status"], "ok", "{t}");
        assert_eq!(o["min_active_sboxes"], 10, "PRESENT 5 rounds: 10 ({t})");
    }
    assert_eq!(outcome(&rows, "differential_trails")["exact"], true);
    // Linear trails of PRESENT can keep one active S-box per round.
    assert_eq!(outcome(&rows, "linear_trails")["min_active_sboxes"], 5);
    // The built-in MILP solver does not finish PRESENT at bit level within
    // the small default budget (recorded shortfall of WP2); the cell says so.
    let m = outcome(&rows, "milp_trails");
    assert!(
        m["status"] == "ok" || m["status"] == "budget_exhausted",
        "{m}"
    );
    assert_eq!(outcome(&rows, "division_property")["best"]["rounds"], 5);
    assert_eq!(row(&rows, "delta_set_mitm")["applicable"], false);
}

#[test]
fn speck64_128_8r_panel() {
    let rows = panel("speck64-128-8r");
    assert_eq!(row(&rows, "sbox_analysis")["applicable"], false);
    assert_eq!(row(&rows, "boomerang")["applicable"], true);
    let dl = outcome(&rows, "arx_diff_linear");
    assert!(!dl["per_round"].as_array().unwrap().is_empty());
    assert_eq!(outcome(&rows, "arx_rotational")["status"], "ok");
    assert_eq!(outcome(&rows, "arx_rx")["status"], "ok");
    assert_eq!(row(&rows, "arx_pnb")["applicable"], false);
    assert_eq!(row(&rows, "hash_local_collision")["applicable"], false);
}

#[test]
fn chacha_w32_6r_panel() {
    let rows = panel("chacha-w32-6r");
    assert_eq!(row(&rows, "boomerang")["applicable"], false, "feed-forward");
    let dl = outcome(&rows, "arx_diff_linear");
    // Published control: 3 rounds, ID bit 13 of word 13, OD bit 0 of word
    // 11, eps about -0.027 (measured here on 2^22 pairs, sigma 0.0005).
    let c = &dl["published_control"];
    let eps = c["eps"].as_f64().unwrap();
    assert!(
        eps < 0.0 && (0.0255..=0.0285).contains(&eps.abs()),
        "ChaCha 3-round DL control: {c}"
    );
    // The single-bit search itself reaches a significant bias at 3 rounds.
    assert!(dl["longest_significant_rounds"].as_u64().unwrap() >= 3);
    let pnb = outcome(&rows, "arx_pnb");
    assert_eq!(pnb["status"], "ok");
    let best = &pnb["best_significant_row"];
    assert!(best["m"].as_u64().unwrap() > 0);
    assert_eq!(best["key_bits"], 256);
    assert_eq!(outcome(&rows, "arx_rotational")["status"], "ok");
}

#[test]
fn sha256_20steps_panel() {
    let rows = panel("sha256-20steps");
    let lc = outcome(&rows, "hash_local_collision");
    assert_eq!(lc["status"], "ok");
    assert_eq!(lc["collision_found"], true);
    assert_eq!(lc["steps"], 20);
    assert_eq!(lc["verified_by_ir_eval"], true);
    let md = outcome(&rows, "hash_md_generic");
    assert_eq!(md["status"], "ok");
    assert_eq!(md["length_extension_verified"], true);
    assert_eq!(md["joux_replay_single_final_state"], true);
    assert_eq!(md["birthday_24bit_verified"], true);
    assert_eq!(row(&rows, "boomerang")["applicable"], false);
    assert_eq!(row(&rows, "sbox_analysis")["applicable"], false);
}

#[test]
fn cli_auto_json_emits_one_row_per_technique() {
    let out = Command::new(env!("CARGO_BIN_EXE_ca-suite"))
        .args(["auto", "--cipher", "aes-4r", "--json"])
        .output()
        .unwrap();
    assert!(out.status.success());
    let rows: Vec<Value> = String::from_utf8(out.stdout)
        .unwrap()
        .lines()
        .map(|l| serde_json::from_str(l).unwrap())
        .collect();
    assert_eq!(rows.len(), default_techniques().len());
    assert_eq!(
        row(&rows, "differential_trails")["result"]["outcome"]["min_active_sboxes"],
        25
    );
}

#[test]
fn cli_boomerang_on_feed_forward_primitive_is_an_error_not_a_panic() {
    let out = Command::new(env!("CARGO_BIN_EXE_ca-suite"))
        .args(["boomerang", "--cipher", "chacha8", "--pairs", "16"])
        .output()
        .unwrap();
    let err = String::from_utf8_lossy(&out.stderr);
    assert_eq!(out.status.code(), Some(1), "{err}");
    assert!(err.contains("no decryption"), "{err}");
    assert!(!err.contains("panicked"), "{err}");
}
