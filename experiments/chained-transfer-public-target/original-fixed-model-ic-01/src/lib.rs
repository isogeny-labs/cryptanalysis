//! Fixed original-model IC under prospective3da7fe published7550409 before source.
#![allow(dead_code, static_mut_refs)]
use chained_n4_original_full_geometry::{
    norm::EncodedClass, FixedGeometry, NormNew, CASES, ELL, MASKS, ORDER,
};
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
    pub fn new(geometry: &'a FixedGeometry, side: usize) -> Result<Self, String> {
        let model = geometry
            .models
            .get(side)
            .ok_or("unknown fixed geometry side")?;
        let norm = &model.prime;
        let origins = [[1, 0, 28], [1, 0, 90], [1, 1, 165]];
        if norm.a.q != 223
            || norm.a.ell != ELL
            || norm.a.expected_order as u128 != ORDER
            || norm.a.candidate != CASES[side]
            || norm.a.kernel_mask != MASKS[side]
            || norm.a.pic.base_point() != origins[side]
            || norm.a.core.quartic.iter().any(|&x| x >= 223)
        {
            return Err("foreign frozen original field/order/model/mask/origin".into());
        }
        Ok(Self {
            q: norm.a.q,
            ell: ELL,
            f: norm.a.core.quartic.map(|x| x as u32),
            norm,
        })
    }
    fn admit(&self, packet: &EncodedClass, generator: bool) -> Result<PicClass, String> {
        let class = self.norm.decode(packet)?;
        let pic = &self.norm.a.pic;
        if !pic.is_zero(&pic.mul_scalar(&class, self.ell as u128))
            || (generator && pic.is_zero(&class))
        {
            return Err("non-ell input or zero generator".into());
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
