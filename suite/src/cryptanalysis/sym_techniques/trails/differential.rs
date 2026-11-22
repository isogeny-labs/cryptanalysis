//! Differential trail search: minimum number of active S-boxes and the best
//! concrete trail.
//!
//! Matsui-style branch and bound over the IR (M. Matsui, EUROCRYPT 1994),
//! with the truncated word-level model for wide S-boxes in the wide-trail
//! setting of Daemen and Rijmen (*The Design of Rijndael*, 2002). See the
//! [parent module](super) for the engines and their restrictions.

use super::{
    best_concrete_trail, min_active_sboxes as search, ActiveSboxResult, ConcreteTrail, Direction,
    SearchOptions, TrailError, TrailModel,
};
use crate::cryptanalysis::sym_ir::Primitive;

/// Minimum number of active S-boxes over the first `rounds` rounds of `p`
/// for differential trails, with the per-round active pattern.
///
/// For S-boxes of width at most 4 the exact value engine runs on the DDT
/// support; for wider S-boxes the word-level truncated engine runs (a lower
/// bound, tight for MDS diffusion such as AES). Set
/// [`SearchOptions::with_concrete`] to also get the best concrete
/// probability trail for small S-boxes.
pub fn min_active_sboxes(
    p: &Primitive,
    rounds: usize,
    opts: &SearchOptions,
) -> Result<ActiveSboxResult, TrailError> {
    let model = TrailModel::from_primitive(p, rounds, Direction::Differential)?;
    search(&model, opts)
}

/// Best concrete differential trail (maximum probability) over the first
/// `rounds` rounds of `p`, by weighted branch and bound on the DDT.
/// `weight` of the result is `-log2` of the trail probability.
pub fn best_trail(
    p: &Primitive,
    rounds: usize,
    node_budget: u64,
) -> Result<ConcreteTrail, TrailError> {
    let model = TrailModel::from_primitive(p, rounds, Direction::Differential)?;
    best_concrete_trail(&model, node_budget)
}
