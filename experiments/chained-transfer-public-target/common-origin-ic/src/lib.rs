//! Common-origin control, prospective2dd807 published0a3412cd BEFORE code.
#![allow(dead_code, static_mut_refs)]
use chained_n4_completed_v2::{norm::EncodedClass, NormV2};
pub use chained_n4_public_target::{common, ic};
pub use ghs_original_engines::pic;
use pic::{PicClass, PlaneQuartic};

#[path = "../derived/class_solver.rs"]
pub mod class_solver;

pub struct BridgeContext<'a> {
    q: u64,
    ell: u64,
    f: [u32; 15],
    pic: &'a PlaneQuartic,
    norm: &'a NormV2,
}
impl<'a> BridgeContext<'a> {
    pub fn new(norm: &'a NormV2) -> Result<Self, String> {
        if norm.a.q != 223 || norm.a.ell != 2773073 || norm.a.expected_order != 11092292 {
            return Err("foreign original-model identity".into());
        }
        Ok(Self {
            q: norm.a.q,
            ell: norm.a.ell,
            f: norm.a.core.quartic.map(|v| v as u32),
            pic: &norm.a.pic,
            norm,
        })
    }
    fn admit(&self, packet: &EncodedClass, generator: bool) -> Result<PicClass, String> {
        let x = self.norm.decode(packet)?;
        if !self.pic.is_zero(&self.pic.mul_scalar(&x, self.ell as u128))
            || (generator && self.pic.is_zero(&x))
        {
            return Err("nonodd input or zero generator".into());
        }
        Ok(x)
    }
    pub fn solve(
        &self,
        generator: &EncodedClass,
        target: &EncodedClass,
        params: &class_solver::Params,
        seed: u64,
    ) -> Result<class_solver::Report, String> {
        if !(4..=224).contains(&params.nfb)
            || params.max_desc == 0
            || !params.rows_mult.is_finite()
            || params.rows_mult <= 0.0
        {
            return Err("invalid bounded IC parameters".into());
        }
        let g = self.admit(generator, true)?;
        let q = self.admit(target, false)?;
        Ok(class_solver::solve_class(self, params, &g, &q, seed, true))
    }
}

#[cfg(test)]
mod tests;
