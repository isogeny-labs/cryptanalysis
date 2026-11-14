//! Exact-class sampling; prospective4a6745 published b57b1024 BEFORE code.
#![allow(dead_code, static_mut_refs)]
use chained_n4_odd_product_maps::{norm::EncodedClass, NormNew, Point};
use chained_n4_odd_product_models::{er, three};
pub use chained_n4_public_target::{common, ic};
pub use ghs_original_engines::pic;
use isogeny_algos::curve::{self, Pt};
use pic::PicClass;
use serde::Serialize;
use std::cell::Cell;

#[path = "../arithmetic-derived/class_solver.rs"]
pub mod class_solver;

/// Explicit calls at this API boundary; not primitive operations or a price.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize)]
pub struct Calls {
    pub decode: u64,
    pub explicit_norm: u64,
    pub source_scalar: u64,
    pub source_order_check: u64,
    pub completed_transfer: u64,
    pub target_admission_scalar: u64,
    pub sampled: u64,
}
impl Calls {
    pub fn since(self, old: Self) -> Self {
        Self {
            decode: self.decode - old.decode,
            explicit_norm: self.explicit_norm - old.explicit_norm,
            source_scalar: self.source_scalar - old.source_scalar,
            source_order_check: self.source_order_check - old.source_order_check,
            completed_transfer: self.completed_transfer - old.completed_transfer,
            target_admission_scalar: self.target_admission_scalar - old.target_admission_scalar,
            sampled: self.sampled - old.sampled,
        }
    }
}
fn ep(p: Point) -> Pt<isogeny_algos::fpr::ER> {
    match p {
        None => Pt::Inf,
        Some((x, y)) => Pt::Aff(er(x), er(y)),
    }
}
fn kp(p: Pt<isogeny_algos::fpr::ER>) -> Point {
    match p {
        Pt::Inf => None,
        Pt::Aff(x, y) => Some((three(x), three(y))),
    }
}

pub struct SamplerContext<'a> {
    q: u64,
    ell: u64,
    f: [u32; 15],
    norm: &'a NormNew,
    generator_key: [u32; 19],
    prepared_source: Point,
    calls: Cell<Calls>,
}
impl<'a> SamplerContext<'a> {
    pub fn new(norm: &'a NormNew, generator: &EncodedClass) -> Result<Self, String> {
        // Reuse the original immutable model-identity admission.
        chained_n4_new_target_ic::TargetContext::new(norm)?;
        let mut out = Self {
            q: norm.a.q,
            ell: norm.a.ell,
            f: norm.a.core.quartic.map(|x| x as u32),
            norm,
            generator_key: generator.key,
            prepared_source: None,
            calls: Cell::new(Calls::default()),
        };
        let g = out.admit(generator, true)?;
        out.bump(|c| c.explicit_norm += 1);
        let n = norm.norm(&g)?;
        let f = &norm.a.f3;
        let e = &norm.a.source_ec;
        if n.is_none() || !curve::on_curve(f, e, &ep(n)) {
            return Err("norm is zero or off the actual source curve".into());
        }
        assert_eq!(2 * 1386537, out.ell + 1);
        out.bump(|c| c.source_scalar += 1);
        let u = curve::pmul(f, e, &ep(n), 1386537);
        out.bump(|c| c.source_order_check += 1);
        if u == Pt::Inf || curve::pmul(f, e, &u, out.ell as u128) != Pt::Inf {
            return Err("prepared source is not nonzero ell-torsion".into());
        }
        out.prepared_source = kp(u);
        norm.a.admit(&out.prepared_source)?;
        out.bump(|c| c.completed_transfer += 1);
        if norm.a.transfer_point(&out.prepared_source)? != g {
            return Err("actual Phi(inv2 Norm(G)) does not equal the exact G".into());
        }
        Ok(out)
    }
    fn bump(&self, update: impl FnOnce(&mut Calls)) {
        let mut calls = self.calls.get();
        update(&mut calls);
        self.calls.set(calls);
    }
    pub fn calls(&self) -> Calls {
        self.calls.get()
    }
    pub fn prepared_source(&self) -> Point {
        self.prepared_source
    }
    fn admit(&self, packet: &EncodedClass, generator: bool) -> Result<PicClass, String> {
        self.bump(|c| c.decode += 1);
        let class = self.norm.decode(packet)?;
        let p = &self.norm.a.pic;
        self.bump(|c| c.target_admission_scalar += 1);
        if !p.is_zero(&p.mul_scalar(&class, self.ell as u128)) || (generator && p.is_zero(&class)) {
            return Err("nonodd input or zero generator".into());
        }
        Ok(class)
    }
    pub fn sample(&self, r: u64) -> Result<PicClass, String> {
        if r >= self.ell {
            return Err("noncanonical scalar".into());
        }
        self.bump(|c| c.source_scalar += 1);
        let point = curve::pmul(
            &self.norm.a.f3,
            &self.norm.a.source_ec,
            &ep(self.prepared_source),
            r as u128,
        );
        self.bump(|c| c.completed_transfer += 1);
        let result = self.norm.a.transfer_point(&kp(point))?;
        self.bump(|c| c.sampled += 1);
        Ok(result)
    }
    pub fn solve(
        &self,
        generator: &EncodedClass,
        target: &EncodedClass,
        params: &class_solver::Params,
        seed: u64,
    ) -> Result<class_solver::Report, String> {
        if generator.key != self.generator_key {
            return Err("generator differs from prepared exact class".into());
        }
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

#[cfg(test)]
#[path = "../../../../../arithmetic-controls.rs"]
mod arithmetic_controls;
