//! Actual target-class IC;prospective98c6f0 published2aee9ef5 BEFORE code.
#![allow(dead_code, static_mut_refs)]
use chained_n4_odd_product_maps::{norm::EncodedClass, NormNew};
pub use chained_n4_public_target::{common, ic};
pub use ghs_original_engines::pic;
use pic::PicClass;

#[path = "../derived/class_solver.rs"]
pub mod class_solver;

pub struct TargetContext<'a> {
    q: u64,
    ell: u64,
    f: [u32; 15],
    norm: &'a NormNew,
}
impl<'a> TargetContext<'a> {
    pub fn new(norm: &'a NormNew) -> Result<Self, String> {
        if norm.a.q != 223
            || norm.a.ell != 2773073
            || norm.a.expected_order != 11092292
            || norm.a.core.quartic.iter().any(|&x| x >= norm.a.q)
        {
            return Err("foreign target field/order/curve identity".into());
        }
        Ok(Self {
            q: norm.a.q,
            ell: norm.a.ell,
            f: norm.a.core.quartic.map(|x| x as u32),
            norm,
        })
    }
    fn admit(&self, packet: &EncodedClass, generator: bool) -> Result<PicClass, String> {
        let class = self.norm.decode(packet)?;
        let p = &self.norm.a.pic;
        if !p.is_zero(&p.mul_scalar(&class, self.ell as u128)) || (generator && p.is_zero(&class)) {
            return Err("nonodd input or zero generator".into());
        }
        Ok(class)
    }
    pub fn solve(
        &self,
        generator: &EncodedClass,
        target: &EncodedClass,
        params: &class_solver::Params,
        seed: u64,
    ) -> Result<class_solver::Report, String> {
        if params.nfb < 4
            || params.nfb > 224
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
