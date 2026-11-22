//! Linear trail search: minimum number of active S-boxes and the best
//! concrete trail.
//!
//! Masks flow forwards through the rounds via the inverse transpose of each
//! linear layer (M. Matsui, "Linear cryptanalysis method for DES cipher",
//! EUROCRYPT 1993; the active-S-box bound for SPNs follows Daemen and
//! Rijmen, *The Design of Rijndael*, 2002). See the [parent module](super)
//! for the engines and their restrictions.

use super::{
    best_concrete_trail, min_active_sboxes as search, ActiveSboxResult, ConcreteTrail, Direction,
    SearchOptions, TrailError, TrailModel,
};
use crate::cryptanalysis::sym_ir::Primitive;

/// Minimum number of active S-boxes over the first `rounds` rounds of `p`
/// for linear trails, with the per-round active pattern. Engines as in
/// [`differential::min_active_sboxes`](super::differential::min_active_sboxes),
/// with the LAT support in place of the DDT.
pub fn min_active_sboxes(
    p: &Primitive,
    rounds: usize,
    opts: &SearchOptions,
) -> Result<ActiveSboxResult, TrailError> {
    let model = TrailModel::from_primitive(p, rounds, Direction::Linear)?;
    search(&model, opts)
}

/// Best concrete linear trail (maximum absolute correlation) over the first
/// `rounds` rounds of `p`. `weight` of the result is `-log2 |correlation|`;
/// the bias is `2^-(weight + 1)`.
pub fn best_trail(
    p: &Primitive,
    rounds: usize,
    node_budget: u64,
) -> Result<ConcreteTrail, TrailError> {
    let model = TrailModel::from_primitive(p, rounds, Direction::Linear)?;
    best_concrete_trail(&model, node_budget)
}
