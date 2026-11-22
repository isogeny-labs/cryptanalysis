//! Technique library entry point: the applicability rules, the common
//! [`Technique`] trait and the [`TechniqueResult`] row shared by every
//! technique (work packages WP1–WP5 of
//! `docs/plans/2026-11-21-generic-symmetric-cryptanalysis.md`, section 2.2).
//!
//! This file defines only the common vocabulary. Each technique lives in its
//! own file under this module, implements [`Technique`], and is registered in
//! `auto_attack::default_techniques`. Applicability is decided from the
//! structure of the [`Primitive`] (its [`Kind`], S-box widths, ARX layers,
//! feed-forward), never from its name; see [`applicable_techniques`].
//!
//! A [`TechniqueResult`] reports what a run observed and what it cost. It is
//! not a claim about the security of the primitive.

use crate::cryptanalysis::sym_bridge;
use crate::cryptanalysis::sym_ir::{FeedForward, Kind, Layer, Primitive};
use serde::{Deserialize, Serialize};
use std::time::{Duration, Instant};

// WP2: differential and linear trail search (branch and bound, MILP, SAT).
pub mod trails;
// WP2: division-property integral distinguishers.
pub mod integral;
// WP3: impossible-differential (miss-in-the-middle) search.
pub mod impossible;
// WP3: zero-correlation linear hulls.
pub mod zero_correlation;
// WP3: Demirci-Selcuk delta-set meet-in-the-middle cost table.
pub mod mitm;
// WP4: ARX techniques (differential-linear, PNB, rotational).
pub mod arx;
// WP5: hash techniques (local collisions, Merkle-Damgard generic attacks).
pub mod hash;
// Panel wrappers that register the packages' entry points as `Technique`s.
pub mod panel;

/// Identifier of a technique in the plan's section 2.2 table (plus the
/// pre-existing S-box and rectangle analyses).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TechniqueId {
    /// DDT/LAT/BCT/DLCT report on the primitive's S-box.
    SboxAnalysis,
    /// `trails::differential`: differential trail search.
    DifferentialTrails,
    /// `trails::linear`: linear trail search.
    LinearTrails,
    /// `trails::milp`: trail bounds through a MILP model.
    MilpTrails,
    /// `trails::sat`: trail bounds through a SAT model.
    SatTrails,
    /// `integral::division_property`.
    DivisionProperty,
    /// `impossible`: impossible-differential (miss-in-the-middle) search.
    ImpossibleDifferential,
    /// `zero_correlation`: zero-correlation linear hulls.
    ZeroCorrelation,
    /// `mitm::delta_set`: Demirci-Selcuk-style meet-in-the-middle.
    DeltaSetMitm,
    /// `boomerang`: boomerang distinguisher (needs a decryption oracle).
    Boomerang,
    /// Rectangle attack (chosen plaintext only).
    Rectangle,
    /// `arx::diff_linear`: differential-linear analysis of ARX layers.
    ArxDiffLinear,
    /// `arx::pnb`: probabilistic neutral bits for ARX permutations.
    ArxPnb,
    /// `arx::rotational`: rotational distinguishers.
    ArxRotational,
    /// `arx::rx`: rotational-XOR distinguishers.
    ArxRx,
    /// `hash::local_collision`: local collisions on a Davies-Meyer function.
    HashLocalCollision,
    /// `hash::md_generic`: generic Merkle-Damgard attacks.
    HashMdGeneric,
}

impl TechniqueId {
    /// Every identifier, in declaration order.
    pub const ALL: [TechniqueId; 17] = [
        TechniqueId::SboxAnalysis,
        TechniqueId::DifferentialTrails,
        TechniqueId::LinearTrails,
        TechniqueId::MilpTrails,
        TechniqueId::SatTrails,
        TechniqueId::DivisionProperty,
        TechniqueId::ImpossibleDifferential,
        TechniqueId::ZeroCorrelation,
        TechniqueId::DeltaSetMitm,
        TechniqueId::Boomerang,
        TechniqueId::Rectangle,
        TechniqueId::ArxDiffLinear,
        TechniqueId::ArxPnb,
        TechniqueId::ArxRotational,
        TechniqueId::ArxRx,
        TechniqueId::HashLocalCollision,
        TechniqueId::HashMdGeneric,
    ];

    /// Stable snake-case name, the same string serde uses.
    pub fn as_str(self) -> &'static str {
        match self {
            TechniqueId::SboxAnalysis => "sbox_analysis",
            TechniqueId::DifferentialTrails => "differential_trails",
            TechniqueId::LinearTrails => "linear_trails",
            TechniqueId::MilpTrails => "milp_trails",
            TechniqueId::SatTrails => "sat_trails",
            TechniqueId::DivisionProperty => "division_property",
            TechniqueId::ImpossibleDifferential => "impossible_differential",
            TechniqueId::ZeroCorrelation => "zero_correlation",
            TechniqueId::DeltaSetMitm => "delta_set_mitm",
            TechniqueId::Boomerang => "boomerang",
            TechniqueId::Rectangle => "rectangle",
            TechniqueId::ArxDiffLinear => "arx_diff_linear",
            TechniqueId::ArxPnb => "arx_pnb",
            TechniqueId::ArxRotational => "arx_rotational",
            TechniqueId::ArxRx => "arx_rx",
            TechniqueId::HashLocalCollision => "hash_local_collision",
            TechniqueId::HashMdGeneric => "hash_md_generic",
        }
    }
}

/// Structural summary of a [`Primitive`] used by the applicability rules.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct IrFacts {
    /// Structural family.
    pub kind: Kind,
    /// Widths (bits) of the S-box layers in the rounds, sorted, deduplicated.
    pub sbox_widths: Vec<usize>,
    /// Whether some round contains an ARX layer.
    pub has_arx: bool,
    /// Whether some round contains a GF(2)-linear or permutation layer.
    pub has_linear_layer: bool,
    /// Whether the primitive has a feed-forward (Davies-Meyer, ChaCha).
    pub has_feed_forward: bool,
    /// Whether the key input is non-empty.
    pub keyed: bool,
}

/// Read the [`IrFacts`] off a primitive's rounds.
pub fn ir_facts(p: &Primitive) -> IrFacts {
    let mut widths = Vec::new();
    let (mut has_arx, mut has_linear_layer) = (false, false);
    for r in &p.rounds {
        for l in &r.layers {
            match l {
                Layer::SboxParallel { width_bits, .. } => widths.push(*width_bits),
                Layer::Arx { .. } => has_arx = true,
                Layer::LinearGf2 { .. } | Layer::Permute { .. } => has_linear_layer = true,
                _ => {}
            }
        }
    }
    widths.sort_unstable();
    widths.dedup();
    IrFacts {
        kind: p.kind,
        sbox_widths: widths,
        has_arx,
        has_linear_layer,
        has_feed_forward: p.feed_forward != FeedForward::None,
        keyed: p.key_bits > 0,
    }
}

/// The techniques whose input requirements `p` meets, decided from the IR
/// (see [`ir_facts`]) and from whether a decryption oracle can be derived
/// (`sym_bridge::is_invertible`). Applicability says the technique can be
/// pointed at the primitive, not that it will find anything.
///
/// Rules (each is the condition under which the panel wrapper in
/// [`panel`] actually runs the technique; a wrapper may still report
/// `unsupported` or `not_found` for the instance):
/// * S-box analysis: at least one S-box layer.
/// * Differential/linear trails, MILP, SAT: S-box layers all at most 8 bits
///   wide and the trail model of the whole primitive can be built (MILP and
///   SAT use the differential model).
/// * Division property: S-boxes at most 8 bits wide (bit-based) or ARX
///   layers (word-based).
/// * Impossible differential, zero correlation: an SPN with a linear layer.
/// * Delta-set MITM: an SPN with 8-bit S-boxes (the cost table of a window
///   of `min(4, rounds)` rounds, see [`panel::delta_set_window`]).
/// * Boomerang: invertible primitive; rectangle: any keyed or unkeyed block
///   function with a non-empty block.
/// * ARX diff-linear: ARX layers. Rotational: the walk models the structure
///   (no `Shr`/`And`, only ARX and AddRoundKey layers, ARX key schedule;
///   [`arx::rotational::rotational_structure_gap`]) and some rotation amount
///   keeps every constant invariant. RX: the same structure condition.
///   PNB: the primitive
///   computes the reduced-width ChaCha permutation of its round count
///   ([`panel::chacha_word_bits`]).
/// * Hash local collision: the primitive computes the first `n >= 9` steps
///   of SHA-256 or SHA-512 ([`panel::sha2_family`]; a local collision spans
///   at least nine steps); generic Merkle-Damgard
///   attacks: SHA-256, SHA-512 or MD5 steps.
pub fn applicable_techniques(p: &Primitive) -> Vec<TechniqueId> {
    use panel::Sha2Family;
    use trails::Direction;
    use TechniqueId::*;
    let f = ir_facts(p);
    let small_sboxes = !f.sbox_widths.is_empty() && f.sbox_widths.iter().all(|&w| w <= 8);
    let mut out = Vec::new();
    if !f.sbox_widths.is_empty() {
        out.push(SboxAnalysis);
    }
    if small_sboxes {
        if panel::trail_model_ok(p, Direction::Differential) {
            out.extend([DifferentialTrails, MilpTrails, SatTrails]);
        }
        if panel::trail_model_ok(p, Direction::Linear) {
            out.push(LinearTrails);
        }
    }
    if small_sboxes || f.has_arx {
        out.push(DivisionProperty);
    }
    if f.kind == Kind::Spn && f.has_linear_layer && !f.sbox_widths.is_empty() {
        out.extend([ImpossibleDifferential, ZeroCorrelation]);
    }
    if f.kind == Kind::Spn && f.sbox_widths == [8] {
        out.push(DeltaSetMitm);
    }
    if sym_bridge::is_invertible(p) {
        out.push(Boomerang);
    }
    if p.block_bits > 0 {
        out.push(Rectangle);
    }
    if f.has_arx {
        out.push(ArxDiffLinear);
        if arx::rotational::rotational_applicable(p).is_ok() {
            out.push(ArxRotational);
        }
        if arx::rotational::rotational_structure_gap(p).is_none() {
            out.push(ArxRx);
        }
    }
    if panel::chacha_word_bits(p).is_some() {
        out.push(ArxPnb);
    }
    match panel::sha2_family(p) {
        Some(Sha2Family::Sha256 | Sha2Family::Sha512) => {
            if p.num_rounds() >= panel::LOCAL_COLLISION_MIN_STEPS {
                out.push(HashLocalCollision);
            }
            out.push(HashMdGeneric)
        }
        Some(Sha2Family::Md5) => out.push(HashMdGeneric),
        None => {}
    }
    out.sort();
    out.dedup();
    out
}

/// Resource limits for one technique run. A technique stops early when a
/// limit would be exceeded and sets [`TechniqueResult::budget_exhausted`].
#[derive(Clone, Debug)]
pub struct Budget {
    /// Maximum number of chosen/known plaintext-ciphertext queries.
    pub max_data: u64,
    /// Maximum number of primitive evaluations.
    pub max_time_evals: u64,
    /// Maximum memory in bytes.
    pub max_memory: u64,
    /// Wall-clock limit, checked between units of work (not preemptive).
    pub max_wall: Duration,
    /// Tunable parameters shared by the panel's techniques.
    pub params: TechniqueParams,
    /// Key to bind the oracle to; `None` means
    /// `sym_bridge::default_key` of the primitive. The panel sets this to the
    /// key the registry registered the primitive with.
    pub key: Option<Vec<u8>>,
    /// When this budget was created; the wall limit counts from here unless
    /// [`Budget::restart_clock`] is called.
    pub started: Instant,
}

/// Technique parameters that the CLI exposes (they predate [`Budget`]).
#[derive(Clone, Debug)]
pub struct TechniqueParams {
    /// Plaintext pairs for the boomerang distinguisher.
    pub boomerang_pairs: usize,
    /// Pool size for the rectangle attack.
    pub rectangle_pool: usize,
    /// Trail-search threshold: the panel reports whether the best concrete
    /// trail has `p >= threshold`.
    pub trail_threshold: f64,
    /// Maximum number of trails to report (kept for CLI compatibility; the
    /// panel's trail cells report one optimal trail and do not use it).
    pub trail_top_k: usize,
}

impl Default for TechniqueParams {
    fn default() -> Self {
        TechniqueParams {
            boomerang_pairs: 65_536,
            rectangle_pool: 2048,
            trail_threshold: 2f64.powi(-12),
            trail_top_k: 5,
        }
    }
}

impl Default for Budget {
    fn default() -> Self {
        Budget {
            max_data: 1 << 20,
            max_time_evals: 1 << 26,
            max_memory: 1 << 30,
            max_wall: Duration::from_secs(15),
            params: TechniqueParams::default(),
            key: None,
            started: Instant::now(),
        }
    }
}

impl Budget {
    /// Reset the wall-clock origin to now (the panel does this per cell).
    pub fn restart_clock(&mut self) {
        self.started = Instant::now();
    }

    /// The oracle for `p` under [`Budget::key`] (or the default key).
    pub fn oracle(&self, p: &Primitive) -> sym_bridge::KeyedPrimitive {
        let key = self
            .key
            .clone()
            .unwrap_or_else(|| sym_bridge::default_key(p));
        sym_bridge::KeyedPrimitive::new(p.clone(), key)
    }

    /// Whether the wall-clock limit has passed.
    pub fn wall_expired(&self) -> bool {
        self.started.elapsed() >= self.max_wall
    }
}

/// Cost of a run in the attack's own accounting.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Cost {
    /// Queries made to the encryption/decryption oracle.
    pub data: u64,
    /// Primitive evaluations performed.
    pub time_evals: u64,
    /// Bytes held at peak (an estimate).
    pub memory: u64,
}

/// What one technique run on one primitive observed. Not a security claim.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct TechniqueResult {
    /// Which technique ran.
    pub technique: TechniqueId,
    /// Name of the primitive ([`Primitive::name`]).
    pub primitive: String,
    /// Data, time and memory used.
    pub cost: Cost,
    /// Technique-specific observations.
    pub outcome: serde_json::Value,
    /// Whether the run stopped early because a [`Budget`] limit was reached.
    pub budget_exhausted: bool,
}

/// A cryptanalytic technique that can be run on any [`Primitive`] it applies
/// to. Implementations live next to this file and are registered in
/// `auto_attack::default_techniques`.
pub trait Technique: Send + Sync {
    /// Which technique this is.
    fn id(&self) -> TechniqueId;

    /// Whether to run on `p`. Defaults to membership of [`Technique::id`] in
    /// [`applicable_techniques`]; override to narrow it further.
    fn applies_to(&self, p: &Primitive) -> bool {
        applicable_techniques(p).contains(&self.id())
    }

    /// Run on `p` within `budget` and report.
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult;

    /// Section title in the panel report. Defaults to the snake-case id.
    fn title(&self) -> String {
        self.id().as_str().to_string()
    }

    /// Markdown for the panel report. Defaults to the outcome as JSON.
    fn markdown(&self, r: &TechniqueResult) -> String {
        format!(
            "- **cost**: data {}, evals {}, memory {} B\n- **budget exhausted**: {}\n- **outcome**: `{}`\n",
            r.cost.data, r.cost.time_evals, r.cost.memory, r.budget_exhausted, r.outcome
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::sym_ir::primitives::{
        aes128, chacha, present80, sha256_compress, speck,
    };

    #[test]
    fn applicability_follows_structure() {
        use TechniqueId::*;
        let aes = applicable_techniques(&aes128::reduced(2, true));
        assert!(aes.contains(&DeltaSetMitm) && aes.contains(&Boomerang));
        assert!(!aes.contains(&ArxPnb));
        let present = applicable_techniques(&present80::present80());
        assert!(!present.contains(&DeltaSetMitm) && present.contains(&DifferentialTrails));
        let sp = applicable_techniques(&speck::speck64_128());
        // Speck's round counters are rotation-variant constants for every
        // rotation amount, so the pure rotational estimate is zero: only RX.
        assert!(!sp.contains(&ArxRotational) && sp.contains(&ArxRx));
        assert!(sp.contains(&Boomerang));
        assert!(!sp.contains(&SboxAnalysis));
        let cc = applicable_techniques(&chacha::chacha8());
        assert!(cc.contains(&ArxPnb) && !cc.contains(&Boomerang));
        let sha = applicable_techniques(&sha256_compress::steps(8));
        assert!(!sha.contains(&HashLocalCollision) && !sha.contains(&Boomerang));
        assert!(sha.contains(&HashMdGeneric));
        assert!(!sha.contains(&ArxRotational) && !sha.contains(&ArxRx));
        let sha9 = applicable_techniques(&sha256_compress::steps(9));
        assert!(sha9.contains(&HashLocalCollision));
    }

    #[test]
    fn technique_id_names_match_serde() {
        for id in TechniqueId::ALL {
            let s = serde_json::to_string(&id).unwrap();
            assert_eq!(s, format!("\"{}\"", id.as_str()));
        }
    }
}
