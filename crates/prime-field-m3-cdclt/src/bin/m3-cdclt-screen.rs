//! Lead 2B m=3 compact-binary CDCL(Fp) scaling screen for rungs s=5..12.
//!
//! For each rung: emit structural sizing, generate a prime whole-group curve with
//! three disjoint windows of cardinality 2^s, then solve planted / natural /
//! exact-UNSAT targets with independent SAT group replay and UNSAT DRAT(T)
//! verification. Where |W|^2 is small enough, also require exact projected
//! model-set agreement with the two-window reference enumerator.

use prime_field_m3_cdclt::{
    canonical_ir, canonical_ir_sha256, generate_instance_for_class, generate_rung_curve_and_windows,
    sizing_comparison_row, validate_instance, verify_signed_group_replay, verify_unsat_transcript,
    CdclOutcome, CdcltStats, ChainedS3LambdaTheory, CompactBinarySelector, DeterministicRng,
    PreparedChainedS3Setup, PreparedTwoWindow, TargetClass, TranscriptProofSink,
};
use std::env;
use std::time::Instant;

#[derive(Clone, Debug)]
struct Row {
    s: u32,
    class: &'static str,
    outcome: &'static str,
    verified: bool,
    enum_agree: Option<bool>,
    decisions: u64,
    conflicts: u64,
    theory_calls: u64,
    fp_ops_total: u64,
    setup_fp_ops: u64,
    wall_ms: f64,
    verify_ms: f64,
    p: u64,
    log2_p_over_3: f64,
    instance_id: String,
    ir_sha256: String,
}

fn solve_one(
    s: u32,
    class: TargetClass,
    setup: &PreparedChainedS3Setup,
    two_win: &PreparedTwoWindow,
    group_order: u64,
    seed_label: &str,
    enum_budget: u64,
) -> Row {
    let mut rng = DeterministicRng::from_label(seed_label);
    let instance_id = format!("lead2b-s{s}-{}", class.as_str());
    let mut inst =
        generate_instance_for_class(instance_id.clone(), s, two_win, class, &mut rng);
    inst.group_order = group_order;
    validate_instance(&inst, false).unwrap_or_else(|e| panic!("invalid instance: {e}"));
    let ir = canonical_ir(&inst);
    let ir_sha256 = canonical_ir_sha256(&inst);
    let log2_p_over_3 = (inst.curve.p as f64).log2() / 3.0;

    let t0 = Instant::now();
    let mut solver = setup.base_solver.clone();
    let mut stats = CdcltStats::default();
    let mut theory = ChainedS3LambdaTheory::new(setup, inst.target, &mut stats);
    let mut sink = TranscriptProofSink::default();
    let outcome = solver.solve_with_theory(&mut theory, &mut sink, &mut stats);
    let wall_ms = t0.elapsed().as_secs_f64() * 1e3;

    let tv0 = Instant::now();
    let (outcome_str, verified, enum_agree) = match (&outcome, class) {
        (CdclOutcome::Sat(model), TargetClass::Planted | TargetClass::Natural) => {
            let w = theory.extract_witness(model);
            let mut ops = prime_field_m3_cdclt::FpOps::default();
            verify_signed_group_replay(&inst, &w, &mut ops)
                .unwrap_or_else(|e| panic!("SAT replay failed on {}: {e:?}", inst.instance_id));
            let agree = if (1u64 << (2 * s)) <= enum_budget {
                let (ref_models, _) = two_win.enumerate(inst.target, false);
                let keys: std::collections::BTreeSet<_> =
                    ref_models.iter().map(|m| m.model_key()).collect();
                Some(keys.contains(&w.model_key()) && !ref_models.is_empty())
            } else {
                None
            };
            if class == TargetClass::Planted {
                assert!(
                    agree.unwrap_or(true),
                    "planted witness missing from enum-ref at s={s}"
                );
            }
            ("SAT", true, agree)
        }
        (CdclOutcome::Unsat, TargetClass::ExactUnsat | TargetClass::Natural) => {
            verify_unsat_transcript(&inst, &sink.events).unwrap_or_else(|e| {
                panic!("UNSAT transcript failed on {}: {e:?}", inst.instance_id)
            });
            let agree = if (1u64 << (2 * s)) <= enum_budget {
                let (ref_models, _) = two_win.enumerate(inst.target, true);
                Some(ref_models.is_empty())
            } else {
                None
            };
            if class == TargetClass::ExactUnsat {
                if let Some(ok) = agree {
                    assert!(ok, "exact-UNSAT disagreed with enum-ref");
                }
            }
            ("UNSAT", true, agree)
        }
        (CdclOutcome::Sat(_), TargetClass::ExactUnsat) => {
            panic!("exact-UNSAT target returned SAT at s={s}");
        }
        (CdclOutcome::Unsat, TargetClass::Planted) => {
            panic!("planted target returned UNSAT at s={s}");
        }
    };
    let verify_ms = tv0.elapsed().as_secs_f64() * 1e3;
    let _ = ir;

    Row {
        s,
        class: class.as_str(),
        outcome: outcome_str,
        verified,
        enum_agree,
        decisions: stats.decisions,
        conflicts: stats.conflicts,
        theory_calls: stats.theory_calls,
        fp_ops_total: stats.fp_ops.total(),
        setup_fp_ops: setup.setup_ops.total(),
        wall_ms,
        verify_ms,
        p: inst.curve.p,
        log2_p_over_3,
        instance_id,
        ir_sha256,
    }
}

fn fit_log_slope(xs: &[(f64, f64)]) -> Option<f64> {
    if xs.len() < 2 {
        return None;
    }
    let n = xs.len() as f64;
    let (mut sx, mut sy, mut sxx, mut sxy) = (0.0, 0.0, 0.0, 0.0);
    for &(x, y) in xs {
        if y <= 0.0 {
            return None;
        }
        let ly = y.ln();
        sx += x;
        sy += ly;
        sxx += x * x;
        sxy += x * ly;
    }
    let den = n * sxx - sx * sx;
    if den.abs() < 1e-12 {
        return None;
    }
    Some((n * sxy - sx * sy) / den)
}

fn main() {
    let max_s: u32 = env::args()
        .nth(1)
        .and_then(|a| a.parse().ok())
        .unwrap_or(12)
        .clamp(5, 12);
    let enum_budget: u64 = env::var("LEAD2B_ENUM_BUDGET")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(1u64 << 20); // skip full enum-ref agreement above ~2^20 pair scans

    println!("# Lead 2B m=3 compact-binary CDCL(Fp) scaling screen");
    println!("# max_s={max_s} enum_budget={enum_budget}");
    println!("s,compact_total_vars,sinz_total_vars,compact_range_clauses,sinz_exactly_one_clauses");
    for s in 5u32..=max_s {
        let row = sizing_comparison_row(s);
        let w = 1usize << s;
        let _sel = CompactBinarySelector::new([w, w, w]);
        println!(
            "{},{},{},{},{}",
            s,
            row.compact_total_vars,
            row.sinz_total_vars_no_sign,
            row.compact_range_clauses,
            row.sinz_exactly_one_clauses
        );
    }

    println!();
    println!(
        "s,class,outcome,verified,enum_agree,decisions,conflicts,theory_calls,fp_ops,setup_fp_ops,wall_ms,verify_ms,p,log2_p_over_3,instance_id,ir_sha256"
    );

    let mut natural_online: Vec<(f64, f64)> = Vec::new();
    let mut setup_points: Vec<(f64, f64)> = Vec::new();
    let mut rows = Vec::new();

    for s in 5u32..=max_s {
        eprintln!("# generating curve/windows for s={s} …");
        let tgen = Instant::now();
        let (curve, order, windows) =
            generate_rung_curve_and_windows("lead2b-screen-20261120", s);
        eprintln!(
            "# s={s} p={} order={} gen_ms={:.1}",
            curve.p,
            order,
            tgen.elapsed().as_secs_f64() * 1e3
        );
        let two_win = PreparedTwoWindow::prepare(curve, windows.clone());
        let ir_bytes = 256 + windows.iter().map(|w| w.len() * 8).sum::<usize>();
        let setup = PreparedChainedS3Setup::prepare(curve, windows, ir_bytes);
        setup_points.push((s as f64, setup.setup_ops.total().max(1) as f64));

        for (class, seed_tag) in [
            (TargetClass::Planted, "planted"),
            (TargetClass::Natural, "natural"),
            (TargetClass::ExactUnsat, "exact-unsat"),
        ] {
            eprintln!("# solving s={s} class={seed_tag} …");
            let row = solve_one(
                s,
                class,
                &setup,
                &two_win,
                order,
                &format!("lead2b-screen-20261120:s={s}:{seed_tag}"),
                enum_budget,
            );
            println!(
                "{},{},{},{},{},{},{},{},{},{},{:.3},{:.3},{},{:.6},{},{}",
                row.s,
                row.class,
                row.outcome,
                row.verified,
                row.enum_agree
                    .map(|b| if b { "true" } else { "false" })
                    .unwrap_or("na"),
                row.decisions,
                row.conflicts,
                row.theory_calls,
                row.fp_ops_total,
                row.setup_fp_ops,
                row.wall_ms,
                row.verify_ms,
                row.p,
                row.log2_p_over_3,
                row.instance_id,
                row.ir_sha256
            );
            if class == TargetClass::Natural {
                natural_online.push((s as f64, row.fp_ops_total.max(1) as f64));
            }
            rows.push(row);
        }
    }

    let e_hat = fit_log_slope(&natural_online);
    let a_hat = fit_log_slope(&setup_points);
    println!();
    println!("# exponent_fits (log-linear in s; natural online fp_ops -> e, setup_fp_ops -> a)");
    println!(
        "# e_hat={} a_hat={} gate_e_lt_0.5={} gate_a_lt_1.5={} rows={} [pcc:unverified]",
        e_hat
            .map(|v| format!("{v:.6}"))
            .unwrap_or_else(|| "na".into()),
        a_hat
            .map(|v| format!("{v:.6}"))
            .unwrap_or_else(|| "na".into()),
        e_hat.map(|e| e < 0.5).unwrap_or(false),
        a_hat.map(|a| a < 1.5).unwrap_or(false),
        rows.len()
    );
}
