//! Factor-base toolkit behind `ca-ic fbkit`: sweep factor-base constructions
//! for one curve, measure their construction, yield and downstream solver
//! metrics at summand counts `m` in `2..=8`, rank them, and store or publish
//! the run directory (locally or on S3).
//!
//! The design is frozen in `docs/ic/FBKIT_SPEC.md`. Module ownership:
//! - [`registry`]: the technique registry (every family, its parameters,
//!   definition and prior verdict);
//! - [`families`]: materialising a recipe into a point set / factor base;
//! - [`metrics`]: construction, yield, F4 and SAT measurements of one cell;
//! - [`sweep`]: the parallel sweep driver and resume logic;
//! - [`rank`]: objectives, composite score and Pareto front;
//! - [`identity`]: canonical JSON, SHA-256 digests, curve IDs, PS1 labels,
//!   cell and sweep identifiers;
//! - [`store`]: the run-directory layout, archive export and S3 transport.
//!
//! Nothing here is an `IC1` result: every number is a stage diagnostic.

pub mod families;
pub mod identity;
pub mod metrics;
pub mod rank;
pub mod registry;
pub mod store;
pub mod sweep;

use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Schema tag of a cell file in a run directory.
pub const CELL_SCHEMA: &str = "ic-fbkit-cell/1";
/// Schema tag of a frozen sweep manifest.
pub const MANIFEST_SCHEMA: &str = "ic-fbkit-manifest/1";
/// Schema tag of the ranking file.
pub const RANKING_SCHEMA: &str = "ic-fbkit-ranking/1";

/// One measured factor-base construction at one summand count: the shared
/// currency of the sweep, ranking and store modules.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CellRecord {
    /// `ic-fbkit-cell/1`.
    pub schema: String,
    /// `<family>-<params-slug>-m<m>-l<l>-<8hex>` (see `identity::cell_id`).
    pub cell_id: String,
    /// Curve ID `EC1N<n>C<tag>h<12hex>` of the curve this cell was measured on.
    pub curve_id: String,
    /// Family name from the registry.
    pub family: String,
    /// The exact recipe (family, parameters, modifiers) as canonical JSON; the
    /// hash input of `factor_base_sha256`. No measurements, seeds included.
    pub recipe: Value,
    /// Summand count the yield/solver metrics refer to.
    pub m: u32,
    /// `complete` | `caps_hit` | `budget` | `not_applicable` | `error`.
    pub status: String,
    /// Reason string when `status` is not `complete`.
    pub reason: Option<String>,
    /// Metric groups (`construction`, `yield`, `system`, `f4`, `sat`, `xl`,
    /// `derived`); unmeasured values are `null` with a sibling `*_reason`.
    pub metrics: Value,
    /// Optional `PS1N...` stage label with `candidate_id: null`.
    pub ps1_label: Option<String>,
    /// SHA-256 over the sorted `[x, y]` hex pairs of the usable point set.
    pub point_set_sha256: Option<String>,
    /// SHA-256 over the canonical recipe record.
    pub factor_base_sha256: Option<String>,
    /// Wall seconds spent on this cell.
    pub elapsed_seconds: f64,
}
