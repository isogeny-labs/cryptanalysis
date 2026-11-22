//! **Auto-attack panel runner** — apply every applicable technique to a
//! named primitive under a budget and emit a Markdown report plus one JSON
//! row per `(technique, primitive)` cell.
//!
//! The registry ([`cipher_registry`](crate::cryptanalysis::cipher_registry))
//! resolves a name to a [`Primitive`] of the
//! [`sym_ir`](crate::cryptanalysis::sym_ir) IR. [`default_techniques`] lists
//! the registered [`Technique`]s; a technique runs on a primitive when its
//! [`Technique::applies_to`] holds (by default: membership in
//! [`applicable_techniques`](crate::cryptanalysis::sym_techniques::applicable_techniques),
//! which reads the IR, not the name). Other work packages add their
//! techniques to [`default_techniques`].
//!
//! The first registered techniques are the pre-existing analyses: S-box
//! report, boomerang distinguisher, rectangle attack, and the legacy 4x4-bit
//! SPN differential trail search (ToySpn-shaped primitives only).
//!
//! ## What this does NOT do
//!
//! - Pick the *optimal* trail for each cipher: the boomerang and rectangle
//!   cells use the registry's canonical `(alpha, delta)`.
//! - Mount key-recovery attacks. These are distinguishers and structural
//!   reports; a result is an observation under the stated budget.
//! - Emit `experiment.export/v1` records: the JSON row is this panel's own
//!   format (see [`CELL_SCHEMA`]).

use crate::cryptanalysis::boomerang::{
    boomerang_distinguisher, differential_trail_search, rectangle_attack, SpnTrailModel, ToySpn,
};
use crate::cryptanalysis::cipher_registry::{first_sbox, CipherEntry, RegisteredCipher};
use crate::cryptanalysis::sym_ir::{Kind, Layer, Primitive};
use crate::cryptanalysis::sym_techniques::{
    ir_facts, Budget, Cost, Technique, TechniqueId, TechniqueParams, TechniqueResult,
};
use serde_json::json;
use std::time::Instant;

/// Tag stored in every JSON row's `schema` field.
pub const CELL_SCHEMA: &str = "ca-suite.sym_panel_cell/v0";

/// Result of one panel run on one primitive.
#[derive(Clone, Debug)]
pub struct AutoAttackReport {
    /// The registry name that was run.
    pub cipher_name: String,
    /// Markdown report.
    pub markdown: String,
    /// Wall time of the whole panel in milliseconds.
    pub elapsed_ms: u128,
    /// Number of techniques that ran (applicable cells).
    pub sections_run: usize,
    /// One JSON object per registered technique: either the run
    /// (`applicable: true`, with the [`TechniqueResult`] under `result`) or
    /// the reason it was skipped.
    pub rows: Vec<serde_json::Value>,
}

/// Knobs for the auto-attack runner (the legacy CLI parameters). They are
/// copied into [`TechniqueParams`]; the resource limits stay at their
/// [`Budget::default`] values unless [`run_panel`] is called directly.
#[derive(Clone, Debug)]
pub struct AutoAttackOptions {
    /// Number of plaintext pairs for the boomerang distinguisher.
    pub boomerang_pairs: usize,
    /// Pool size for the rectangle attack.
    pub rectangle_pool: usize,
    /// Trail-search threshold (`p >= threshold` to keep a trail).
    pub trail_threshold: f64,
    /// Max trails to render in the report.
    pub trail_top_k: usize,
}

impl Default for AutoAttackOptions {
    fn default() -> Self {
        let p = TechniqueParams::default();
        Self {
            boomerang_pairs: p.boomerang_pairs,
            rectangle_pool: p.rectangle_pool,
            trail_threshold: p.trail_threshold,
            trail_top_k: p.trail_top_k,
        }
    }
}

impl AutoAttackOptions {
    /// The default [`Budget`] carrying these parameters.
    pub fn budget(&self) -> Budget {
        Budget {
            params: TechniqueParams {
                boomerang_pairs: self.boomerang_pairs,
                rectangle_pool: self.rectangle_pool,
                trail_threshold: self.trail_threshold,
                trail_top_k: self.trail_top_k,
            },
            ..Budget::default()
        }
    }
}

/// The registered techniques, in report order. Later work packages append
/// their implementations here.
pub fn default_techniques() -> Vec<Box<dyn Technique>> {
    vec![
        Box::new(SboxTechnique),
        Box::new(BoomerangTechnique),
        Box::new(RectangleTechnique),
        Box::new(LegacyTrailTechnique),
    ]
}

/// **Run the default panel** on `cipher_name` with default options.
pub fn auto_attack(cipher_name: &str) -> Result<AutoAttackReport, String> {
    auto_attack_with(cipher_name, AutoAttackOptions::default())
}

/// Run the default panel on `cipher_name` with custom `opts`. Returns
/// `Err(msg)` if the name is unknown.
pub fn auto_attack_with(
    cipher_name: &str,
    opts: AutoAttackOptions,
) -> Result<AutoAttackReport, String> {
    run_panel(cipher_name, &default_techniques(), &opts.budget())
}

/// **Panel runner.** For each technique in `techniques`: if it applies to the
/// registered primitive, run it under a copy of `budget` (wall clock restarted
/// per cell, oracle key set to the registry key) and record the result;
/// otherwise record a skipped row.
pub fn run_panel(
    cipher_name: &str,
    techniques: &[Box<dyn Technique>],
    budget: &Budget,
) -> Result<AutoAttackReport, String> {
    let cipher = RegisteredCipher::from_name(cipher_name)
        .ok_or_else(|| format!("unknown cipher: {}", cipher_name))?;
    let entry = cipher.entry();
    let p = cipher.primitive();
    let t0 = Instant::now();
    let mut md = String::new();
    let mut rows = Vec::new();
    let mut sections_run = 0;
    md.push_str(&format!("# Auto-cryptanalysis: `{}`\n\n", cipher_name));
    md.push_str(&format!("**Cipher**: {}\n\n", entry.description));
    md.push_str(&format!(
        "**Block size**: {} bytes ({} bits)\n\n",
        entry.block_bytes, entry.block_bits
    ));
    md.push_str(&format!("**Rounds**: {}\n\n", entry.rounds));
    md.push_str(&format!(
        "**Canonical (α, δ)**: `{}` / `{}`\n\n",
        hex(&entry.canonical_alpha),
        hex(&entry.canonical_delta)
    ));
    let mut cell_budget = budget.clone();
    cell_budget.key = Some(cipher.keyed().key().to_vec());
    for t in techniques {
        md.push_str(&format!("## {}\n\n", t.title()));
        if !t.applies_to(p) {
            md.push_str("_Skipped._ The primitive's structure does not meet this technique's input requirements.\n\n");
            rows.push(json!({
                "schema": CELL_SCHEMA,
                "cipher": cipher_name,
                "technique": t.id(),
                "applicable": false,
            }));
            continue;
        }
        cell_budget.restart_clock();
        let t_cell = Instant::now();
        let r = t.run(p, &cell_budget);
        let elapsed_ms = t_cell.elapsed().as_millis();
        md.push_str(&format!("- **elapsed**: {} ms\n", elapsed_ms));
        md.push_str(&t.markdown(&r));
        md.push('\n');
        rows.push(json!({
            "schema": CELL_SCHEMA,
            "cipher": cipher_name,
            "technique": t.id(),
            "applicable": true,
            "elapsed_ms": elapsed_ms as u64,
            "result": r,
        }));
        sections_run += 1;
    }
    md.push_str("---\n");
    md.push_str(&format!(
        "**Total elapsed**: {} ms across {} attack sections.\n",
        t0.elapsed().as_millis(),
        sections_run
    ));
    Ok(AutoAttackReport {
        cipher_name: cipher_name.to_string(),
        markdown: md,
        elapsed_ms: t0.elapsed().as_millis(),
        sections_run,
        rows,
    })
}

/// The panel rows as JSON Lines (one object per line).
pub fn rows_jsonl(report: &AutoAttackReport) -> String {
    report
        .rows
        .iter()
        .map(|r| r.to_string())
        .collect::<Vec<_>>()
        .join("\n")
}

// ── Existing analyses as Techniques ──────────────────────────────────

fn canonical(p: &Primitive) -> CipherEntry {
    CipherEntry::from_primitive(&p.name, p)
}

/// DDT/LAT/BCT/DLCT report on the primitive's first S-box.
pub struct SboxTechnique;

impl Technique for SboxTechnique {
    fn id(&self) -> TechniqueId {
        TechniqueId::SboxAnalysis
    }
    fn title(&self) -> String {
        "S-box analysis".into()
    }
    fn run(&self, p: &Primitive, _budget: &Budget) -> TechniqueResult {
        let sbox = first_sbox(p).expect("applicable only with an S-box layer");
        let r = sbox.report();
        let table = 1u64 << (r.n_in + r.n_out.min(r.n_in));
        TechniqueResult {
            technique: self.id(),
            primitive: p.name.clone(),
            cost: Cost {
                data: 0,
                time_evals: table,
                memory: table * 4,
            },
            outcome: json!({
                "bits_in": r.n_in,
                "bits_out": r.n_out,
                "bijective": r.bijective,
                "balanced": r.balanced,
                "differential_uniformity": r.differential_uniformity,
                "max_differential_probability": r.max_differential_probability,
                "max_linear_bias": r.max_linear_bias,
                "nonlinearity": r.nonlinearity,
                "algebraic_degree": r.algebraic_degree,
                "boomerang_uniformity": r.boomerang_uniformity,
                "max_dlct_bias": r.max_dlct_bias,
            }),
            budget_exhausted: false,
        }
    }
    fn markdown(&self, r: &TechniqueResult) -> String {
        let o = &r.outcome;
        let f = |k: &str| o[k].to_string();
        let bu = match o["boomerang_uniformity"].as_u64() {
            Some(v) => v.to_string(),
            None => "—".into(),
        };
        format!(
            "| metric | value |\n|---|---|\n\
             | bits in / out | {} / {} |\n\
             | bijective | {} |\n\
             | balanced | {} |\n\
             | max DDT entry (differential uniformity) | {} |\n\
             | max differential probability | {:.4} |\n\
             | max linear bias | {:.4} |\n\
             | nonlinearity | {} |\n\
             | algebraic degree | {} |\n\
             | boomerang uniformity | {} |\n\
             | max DLCT bias | {:.4} |\n",
            f("bits_in"),
            f("bits_out"),
            f("bijective"),
            f("balanced"),
            f("differential_uniformity"),
            o["max_differential_probability"]
                .as_f64()
                .unwrap_or(f64::NAN),
            o["max_linear_bias"].as_f64().unwrap_or(f64::NAN),
            f("nonlinearity"),
            f("algebraic_degree"),
            bu,
            o["max_dlct_bias"].as_f64().unwrap_or(f64::NAN),
        )
    }
}

/// Generic boomerang distinguisher with the canonical `(alpha, delta)`;
/// needs a decryption oracle.
pub struct BoomerangTechnique;

impl Technique for BoomerangTechnique {
    fn id(&self) -> TechniqueId {
        TechniqueId::Boomerang
    }
    fn title(&self) -> String {
        "Boomerang distinguisher".into()
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let oracle = budget.oracle(p);
        let e = canonical(p);
        // Each pair costs 2 encryptions and 2 decryptions.
        let cap = (budget.max_data.min(budget.max_time_evals) / 4) as usize;
        let want = budget.params.boomerang_pairs;
        let target = want.min(cap);
        let mut exhausted = target < want;
        let (mut done, mut right) = (0usize, 0u64);
        let chunk = 4096usize;
        let mut baseline = 0.0;
        while done < target {
            if budget.wall_expired() {
                exhausted = true;
                break;
            }
            let n = chunk.min(target - done);
            let r =
                boomerang_distinguisher(&oracle, &e.canonical_alpha, &e.canonical_delta, n, None);
            right += r.right_quartets;
            baseline = r.random_baseline;
            done += n;
        }
        if baseline == 0.0 {
            baseline = 2f64.powi(-(p.block_bits as i32));
        }
        let emp = if done > 0 {
            right as f64 / done as f64
        } else {
            0.0
        };
        TechniqueResult {
            technique: self.id(),
            primitive: p.name.clone(),
            cost: Cost {
                data: 4 * done as u64,
                time_evals: 4 * done as u64,
                memory: 0,
            },
            outcome: json!({
                "alpha": hex(&e.canonical_alpha),
                "delta": hex(&e.canonical_delta),
                "n_pairs": done,
                "right_quartets": right,
                "empirical_probability": emp,
                "random_baseline": baseline,
                "exceeds_10x_random_baseline": emp > 10.0 * baseline,
            }),
            budget_exhausted: exhausted,
        }
    }
    fn markdown(&self, r: &TechniqueResult) -> String {
        let o = &r.outcome;
        format!(
            "Run on `{}` random pairs `(P, P ⊕ α)`; count quartets with `P₃ ⊕ P₄ = α` after the `C → C ⊕ δ → decrypt` chain.\n\n\
             - **right quartets**: {} / {}\n\
             - **empirical (pq)²**: {:.4e}\n\
             - **random baseline**: {:.4e}\n\
             - **exceeds 10× random baseline**: {}\n\
             - **budget exhausted**: {}\n",
            o["n_pairs"],
            o["right_quartets"],
            o["n_pairs"],
            o["empirical_probability"].as_f64().unwrap_or(f64::NAN),
            o["random_baseline"].as_f64().unwrap_or(f64::NAN),
            if o["exceeds_10x_random_baseline"].as_bool() == Some(true) {
                "✓"
            } else {
                "✗"
            },
            r.budget_exhausted,
        )
    }
}

/// Chosen-plaintext rectangle attack with the canonical `(alpha, delta)`.
pub struct RectangleTechnique;

impl Technique for RectangleTechnique {
    fn id(&self) -> TechniqueId {
        TechniqueId::Rectangle
    }
    fn title(&self) -> String {
        "Rectangle attack".into()
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let oracle = budget.oracle(p);
        let e = canonical(p);
        // A pool of N plaintexts costs 2N encryptions.
        let cap = (budget.max_data.min(budget.max_time_evals) / 2) as usize;
        let mem_cap = (budget.max_memory / (4 * p.block_bytes().max(1) as u64 + 64)) as usize;
        let want = budget.params.rectangle_pool;
        let pool = want.min(cap).min(mem_cap);
        let mut exhausted = pool < want;
        let (right, used) = if budget.wall_expired() {
            exhausted = true;
            (0, 0)
        } else {
            let r = rectangle_attack(&oracle, &e.canonical_alpha, &e.canonical_delta, pool, None);
            (r.right_quartets, r.pool_size)
        };
        TechniqueResult {
            technique: self.id(),
            primitive: p.name.clone(),
            cost: Cost {
                data: 2 * used as u64,
                time_evals: 2 * used as u64,
                memory: used as u64 * (4 * p.block_bytes() as u64 + 64),
            },
            outcome: json!({
                "alpha": hex(&e.canonical_alpha),
                "delta": hex(&e.canonical_delta),
                "pool_size": used,
                "right_rectangles": right,
            }),
            budget_exhausted: exhausted,
        }
    }
    fn markdown(&self, r: &TechniqueResult) -> String {
        format!(
            "Chosen-plaintext variant: pairs `(P, P ⊕ α)`, quartets found by hash bucketing on `C ⊕ δ`.\n\n\
             - **right rectangles**: {}\n\
             - **pool size**: {}\n\
             - **budget exhausted**: {}\n",
            r.outcome["right_rectangles"], r.outcome["pool_size"], r.budget_exhausted
        )
    }
}

/// The permutation of ToySpn's bit layer is the only linear layer the legacy
/// [`SpnTrailModel`] can express, so the legacy search applies to a primitive
/// iff it is a 16-bit SPN with 4-bit S-boxes whose permute layers match it.
fn matches_toyspn_layer(p: &Primitive) -> bool {
    let f = ir_facts(p);
    if p.kind != Kind::Spn || p.block_bits != 16 || f.sbox_widths != [4] || p.scratch_bits != 0 {
        return false;
    }
    let mut all_layers_ok = true;
    for r in &p.rounds {
        for l in &r.layers {
            match l {
                Layer::Permute { perm } => {
                    all_layers_ok &= (0..16).all(|i| {
                        let y = ToySpn::bit_permutation(1u16 << i);
                        perm.len() == 16 && perm[y.trailing_zeros() as usize] == i
                    });
                }
                Layer::LinearGf2 { .. } | Layer::Arx { .. } => all_layers_ok = false,
                _ => {}
            }
        }
    }
    all_layers_ok
}

/// Branch-and-bound differential trail search over the legacy
/// [`SpnTrailModel`] (4x4-bit ToySpn-shaped SPNs). Registered under
/// [`TechniqueId::DifferentialTrails`]; a general IR-based search replaces it.
pub struct LegacyTrailTechnique;

impl Technique for LegacyTrailTechnique {
    fn id(&self) -> TechniqueId {
        TechniqueId::DifferentialTrails
    }
    fn title(&self) -> String {
        "Differential trail search".into()
    }
    fn applies_to(&self, p: &Primitive) -> bool {
        matches_toyspn_layer(p)
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let e = canonical(p);
        let sbox = first_sbox(p).expect("matches_toyspn_layer implies an S-box");
        let model = SpnTrailModel {
            ddt: sbox.ddt(),
            sbox_bits: 4,
            n_sboxes: 4,
            linear_layer: |x| ToySpn::bit_permutation(x as u16) as u64,
        };
        let alpha = u16::from_le_bytes([e.canonical_alpha[0], e.canonical_alpha[1]]) as u64;
        let th = budget.params.trail_threshold;
        let mut trails = differential_trail_search(&model, alpha, p.rounds.len(), th);
        trails.truncate(budget.params.trail_top_k);
        let rows: Vec<_> = trails
            .iter()
            .map(|t| {
                json!({
                    "alpha": t.alpha,
                    "omega": t.omega,
                    "probability": t.probability,
                    "log2_probability": t.probability.log2(),
                })
            })
            .collect();
        TechniqueResult {
            technique: self.id(),
            primitive: p.name.clone(),
            cost: Cost::default(),
            outcome: json!({
                "model": "legacy 4x4-bit SPN (ToySpn permutation)",
                "seed_alpha": hex(&e.canonical_alpha),
                "threshold_log2": th.log2().round() as i32,
                "trails": rows,
            }),
            budget_exhausted: false,
        }
    }
    fn markdown(&self, r: &TechniqueResult) -> String {
        let o = &r.outcome;
        let trails = o["trails"].as_array().cloned().unwrap_or_default();
        let mut s = format!(
            "Branch-and-bound over a 4×4-bit SPN model, threshold `2^{{{}}}`, seeded with `α = {}`.\n\n- **trails found**: {}\n\n",
            o["threshold_log2"],
            o["seed_alpha"].as_str().unwrap_or(""),
            trails.len()
        );
        if !trails.is_empty() {
            s.push_str("| rank | input α | output ω | probability | log₂ p |\n");
            s.push_str("|----:|---------|----------|------------:|-------:|\n");
            for (rank, t) in trails.iter().enumerate() {
                s.push_str(&format!(
                    "| {} | 0x{:04x} | 0x{:04x} | {:.4e} | {:.2} |\n",
                    rank + 1,
                    t["alpha"].as_u64().unwrap_or(0),
                    t["omega"].as_u64().unwrap_or(0),
                    t["probability"].as_f64().unwrap_or(0.0),
                    t["log2_probability"].as_f64().unwrap_or(0.0),
                ));
            }
        }
        s
    }
}

/// Format a byte slice as `0x` hex.
fn hex(bytes: &[u8]) -> String {
    let mut s = String::from("0x");
    for b in bytes {
        s.push_str(&format!("{:02x}", b));
    }
    s
}

// ── Tests ────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    /// **Auto-attack runs on each registered cipher**: produces a
    /// non-empty Markdown report with at least one section that ran.
    #[test]
    fn auto_attack_runs_on_all_registered_ciphers() {
        // Small overrides so this is fast.
        let opts = AutoAttackOptions {
            boomerang_pairs: 256,
            rectangle_pool: 64,
            trail_threshold: 2f64.powi(-8),
            trail_top_k: 3,
        };
        for name in crate::cryptanalysis::cipher_registry::list_ciphers() {
            let report = auto_attack_with(name, opts.clone())
                .unwrap_or_else(|e| panic!("auto_attack failed for {}: {}", name, e));
            assert!(
                report.sections_run >= 1,
                "cipher {} ran only {} sections",
                name,
                report.sections_run,
            );
            assert!(
                report.markdown.contains("Boomerang distinguisher"),
                "missing boomerang section for {}",
                name
            );
        }
    }

    /// **Auto-attack rejects unknown cipher**.
    #[test]
    fn auto_attack_rejects_unknown_cipher() {
        let r = auto_attack("not-a-cipher");
        assert!(r.is_err());
    }

    /// **Auto-attack on `toyspn-2r` includes a trail-search section**
    /// (trail_searchable is true).
    #[test]
    fn auto_attack_toyspn_runs_trail_search() {
        let opts = AutoAttackOptions {
            boomerang_pairs: 256,
            rectangle_pool: 64,
            trail_threshold: 2f64.powi(-10),
            trail_top_k: 5,
        };
        let report = auto_attack_with("toyspn-2r", opts).unwrap();
        assert!(
            report.markdown.contains("Differential trail search"),
            "expected trail-search section"
        );
        assert!(
            report.sections_run == 4,
            "toyspn-2r should run all 4 sections, got {}",
            report.sections_run
        );
    }

    /// **Auto-attack on AES skips the trail search** (8-bit S-box not
    /// in the SPN trail-search model).
    #[test]
    fn auto_attack_aes_skips_trail_search() {
        let opts = AutoAttackOptions {
            boomerang_pairs: 32,
            rectangle_pool: 32,
            trail_threshold: 2f64.powi(-8),
            trail_top_k: 3,
        };
        let report = auto_attack_with("aes-2r", opts).unwrap();
        assert!(report.markdown.contains("_Skipped._"));
        // 3 sections: sbox + boomerang + rectangle.
        assert_eq!(report.sections_run, 3);
    }

    /// **Report is well-formed Markdown**: starts with a level-1 header.
    #[test]
    fn auto_attack_report_is_markdown() {
        let opts = AutoAttackOptions {
            boomerang_pairs: 32,
            rectangle_pool: 32,
            trail_threshold: 2f64.powi(-8),
            trail_top_k: 3,
        };
        let report = auto_attack_with("toyspn-1r", opts).unwrap();
        assert!(report.markdown.starts_with("# Auto-cryptanalysis"));
    }

    /// **`present80-4r` runs end to end**: S-box, boomerang and rectangle
    /// cells run, the legacy 16-bit trail search is skipped, and the JSON
    /// rows carry the technique ids and costs.
    #[test]
    fn auto_present80_4r_end_to_end() {
        let opts = AutoAttackOptions {
            boomerang_pairs: 512,
            rectangle_pool: 128,
            trail_threshold: 2f64.powi(-8),
            trail_top_k: 3,
        };
        let r = auto_attack_with("present80-4r", opts).unwrap();
        assert_eq!(r.sections_run, 3);
        assert_eq!(r.rows.len(), 4);
        let ids: Vec<_> = r
            .rows
            .iter()
            .map(|x| x["technique"].as_str().unwrap())
            .collect();
        assert_eq!(
            ids,
            [
                "sbox_analysis",
                "boomerang",
                "rectangle",
                "differential_trails"
            ]
        );
        assert_eq!(r.rows[1]["result"]["outcome"]["n_pairs"], 512);
        assert_eq!(r.rows[1]["result"]["cost"]["data"], 2048);
        assert_eq!(r.rows[3]["applicable"], false);
        assert_eq!(rows_jsonl(&r).lines().count(), 4);
    }

    /// **`speck64-128-6r` runs end to end**: no S-box cell, boomerang and
    /// rectangle run through the IR-derived Feistel-free inverse.
    #[test]
    fn auto_speck64_128_6r_end_to_end() {
        let opts = AutoAttackOptions {
            boomerang_pairs: 512,
            rectangle_pool: 128,
            trail_threshold: 2f64.powi(-8),
            trail_top_k: 3,
        };
        let r = auto_attack_with("speck64-128-6r", opts).unwrap();
        assert_eq!(r.sections_run, 2);
        assert!(r.markdown.contains("## Boomerang distinguisher"));
        assert_eq!(r.rows[1]["applicable"], true);
        assert_eq!(r.rows[0]["applicable"], false);
    }

    /// A budget smaller than the request truncates the run and says so.
    #[test]
    fn budget_truncates_boomerang() {
        let mut b = AutoAttackOptions::default().budget();
        b.max_data = 400;
        b.params.boomerang_pairs = 10_000;
        let r = run_panel("toyspn-2r", &default_techniques(), &b).unwrap();
        let cell = &r.rows[1]["result"];
        assert_eq!(cell["budget_exhausted"], true);
        assert_eq!(cell["outcome"]["n_pairs"], 100);
    }
}
