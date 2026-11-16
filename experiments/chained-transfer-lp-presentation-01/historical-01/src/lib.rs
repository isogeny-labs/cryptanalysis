//! Strict public relation types and complete LP-first presentation assembly.
//! No target logarithm, character, curve engine or original candidate is used.
pub mod assembly;
pub mod controls;
pub mod public_view;
pub mod reconstruct;
pub mod stream;
pub mod types;

#[path = "../../../../../crypto/src/hash/sha256.rs"]
#[allow(dead_code)]
// Preserve the frozen upstream block iterator and every original test.
#[allow(clippy::chunks_exact_to_as_chunks)]
pub mod original_sha256;

mod original_counters;
// Preserve the literal original tuple and half-scalar spelling.
#[allow(clippy::type_complexity, clippy::manual_div_ceil)]
mod original_cycles;

use std::sync::Mutex;
use types::Graph;

static ORIGINAL_COUNTER_ACCESS: Mutex<()> = Mutex::new(());

#[derive(Clone, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RootedReceipt {
    pub target: String,
    pub usize_bits: u32,
    pub lmul: u64,
    pub ladd: u64,
    pub scope: String,
}

/// Serialize access to the unchanged original static counter plumbing.
/// This wrapper calls the literal routine, including its original counters.
fn rooted_uncapped(graph: &Graph, prime: u64, eta: u32) -> (Vec<types::Sparse>, RootedReceipt) {
    let raw = original_cycles::Rel2Out {
        full: graph.full.clone(),
        ground: graph.ground.clone(),
        edges: graph.edges.clone(),
        vertex_pts: graph.vertex_points.clone(),
        pairs: graph.pairs,
        no_roots: graph.no_roots,
    };
    let _guard = ORIGINAL_COUNTER_ACCESS
        .lock()
        .expect("original counter lock");
    let before = original_counters::snap();
    let rows = original_cycles::cycle_rows_2lp(&raw, prime, eta, usize::MAX);
    let delta = original_counters::snap().since(&before);
    (
        rows,
        RootedReceipt {
            target: "usize::MAX".into(),
            usize_bits: usize::BITS,
            lmul: delta.lmul,
            ladd: delta.ladd,
            scope: "original rooted routine counters only; no calibrated price".into(),
        },
    )
}
