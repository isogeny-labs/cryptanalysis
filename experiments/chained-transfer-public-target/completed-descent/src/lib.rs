//! Prospective protocol74e00a was actually published in093 before this crate.
//! Only individual-descent transfer admission uses completed divisor spaces.
#![allow(dead_code, static_mut_refs)]
pub use chained_n4_completed_v2::{AdapterV2, NormV2, Point, QuarticPoint};
use chained_n4_public_target::CheckedInstance;
pub use chained_n4_public_target::{common, ghs, ic, pic};
use ghs::EP;

#[path = "../derived/completed_solver.rs"]
pub mod completed_solver;

/// The completed raw legacy divisor, including its actual geometric origin.
/// I is the certified short-model change; kappa(lambda^-1 P)=T-I(P).
pub fn completed_legacy_space(
    checked: &CheckedInstance,
    adapter: &AdapterV2,
    point: EP,
) -> Result<pic::Gen, String> {
    let Some((tx, ty)) = adapter.short_point(QuarticPoint::InfinityMinus)? else {
        return Err("negative infinity is not finite in the completed model".into());
    };
    let f = &checked.inst.kf;
    let t_old = EP::A(f.sub(&tx, &checked.short_shift), ty);
    let raw = checked.inst.ec.add(&t_old, &checked.inst.ec.neg(&point));
    let short = match raw {
        EP::Inf => None,
        EP::A(x, y) => Some((f.add(&x, &checked.short_shift), y)),
    };
    adapter.trace_space(&short)
}

pub fn params(old: &chained_n4_public_target::public_solver::Params) -> completed_solver::Params {
    completed_solver::Params {
        nfb: old.nfb,
        rows_mult: old.rows_mult,
        max_desc: old.max_desc,
        sge: old.sge,
        maxw: old.maxw,
        lp2: old.lp2,
    }
}

#[cfg(test)]
mod tests;
