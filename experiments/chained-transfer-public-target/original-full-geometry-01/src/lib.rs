//! Complete original-source geometry under1539b6, publishedd4f9d6b before code.
//! Phase A geometry first; later phases retain their full published obligations.
#![allow(dead_code, static_mut_refs)]
#[path = "../generated/adapter.rs"]
pub mod adapter;
#[path = "../generated/norm.rs"]
pub mod norm;
#[path = "../generated/quadratic.rs"]
pub mod quadratic;
pub use adapter::{Adapter, EncodedPoint, Point, QuarticPoint};
pub use norm::NormNew;

use chained_n4_completed_v2::AdapterV2;
use chained_n4_paired_fourth_preflight::{
    models::{construct_all, GluingModel, SourceE},
    PairedFourth, ThirdHop, TwistedPair,
};
use chained_n4_public_target::CheckedInstance;
use isogeny_algos::curve::{Curve, Pt};
use isogeny_algos::fpr::ER;
use serde_json::{json, Value};

pub const ELL: u64 = 2_773_073;
pub const ORDER: u128 = 11_092_292;
pub const MASKS: [u64; 3] = [
    1155177839943778305,
    5188291906266857505,
    1155177839943778305,
];
pub const CASES: [(usize, usize); 3] = [(2, 0), (0, 1), (2, 0)];
pub type Result<T> = std::result::Result<T, String>;

pub fn take_fixed_model(
    all: &mut Vec<GluingModel>,
    index: usize,
    requested_mask: u64,
) -> Result<GluingModel> {
    if index >= 3 || requested_mask != MASKS[index] {
        return Err("foreign frozen model mask".into());
    }
    let indices: Vec<_> = all
        .iter()
        .enumerate()
        .filter(|(_, m)| m.kernel_mask == requested_mask)
        .map(|(i, _)| i)
        .collect();
    if all.len() != 6 || indices.len() != 1 {
        return Err("whole six-model fixed-mask population mismatch".into());
    }
    let m = all.remove(indices[0]);
    if (m.root_index, m.sign_index) != CASES[index] || m.p0.is_none() || m.square_root.is_none() {
        return Err("fixed model source support or case mismatch".into());
    }
    Ok(m)
}

pub struct ModelGeometry {
    pub source: SourceE,
    pub prime: NormNew,
    pub quadratic: quadratic::BaseChanged,
    pub all_six_rows: Vec<Value>,
    pub product_summary: Value,
}
pub struct FixedGeometry {
    pub models: [ModelGeometry; 3],
    pub map_certificates: Value,
}
impl FixedGeometry {
    pub fn construct(c: &CheckedInstance) -> Result<Self> {
        c.check_field_basis()?;
        // The old fixture supplies only the checked field/Moore/Picard basis.
        // Its old prime and order are never changed or used as new certificates.
        let basis = AdapterV2::new(c)?;
        if c.inst.ell != ELL || c.inst.order as u128 != ORDER {
            return Err("foreign original prime or order".into());
        }
        let old = ThirdHop::construct(c);
        let pair = TwistedPair::construct(c);
        let fourth = PairedFourth::construct(c, &pair);
        let branch = fourth.branch(false);
        let original = SourceE::original(c);
        let g2 = old.original_to_source(original.generator())?;
        let g3 = old.forward(g2)?;
        let g4 = branch.forward(g3)?;
        let equations: [Curve<ER>; 3] = [*old.source(), *old.target(), *branch.target()];
        let generators = [g2, g3, g4];
        let tags = [
            old.certificate["E2_id"].as_str().ok_or("E2 identity")?,
            old.certificate["E3_id"].as_str().ok_or("E3 identity")?,
            fourth.certificate["original_target_id"]
                .as_str()
                .ok_or("E4 identity")?,
        ];
        let complementary_order = 2 * 223u128.pow(3) + 2 - ORDER;
        if pair.order != complementary_order || pair.ell == ELL || pair.order * ORDER % 13 == 0 {
            return Err("independent complementary order or quadratic no13-pole control".into());
        }
        let mut models = Vec::new();
        for i in 0..3 {
            let source =
                SourceE::paired_source(c, equations[i], ELL, ORDER, generators[i], tags[i]);
            let (mut all, summary) = construct_all(&source, &basis);
            let rows = all.iter().map(|m| m.row.clone()).collect::<Vec<_>>();
            // Rebuild from the same source to retain the independent origins.
            let (mut other, other_summary) = construct_all(&source, &basis);
            if rows != other.iter().map(|m| m.row.clone()).collect::<Vec<_>>()
                || summary != other_summary
            {
                return Err("prime/quadratic whole model reconstruction mismatch".into());
            }
            let prime = NormNew::new(Adapter::new(
                &source,
                &basis,
                take_fixed_model(&mut all, i, MASKS[i])?,
            )?)?;
            let quadratic = quadratic::BaseChanged::new(Adapter::new(
                &source,
                &basis,
                take_fixed_model(&mut other, i, MASKS[i])?,
            )?)?;
            if prime.a.model_tag != quadratic.model
                || prime.a.field_tag != quadratic.field
                || prime.a.pic.base_point() != quadratic.pic.base_point()
                || quadratic.origin_trace_calls() != 1
            {
                return Err("prime/quadratic tags, base point or separate origin mismatch".into());
            }
            models.push(ModelGeometry {
                source,
                prime,
                quadratic,
                all_six_rows: rows,
                product_summary: summary,
            });
        }
        Ok(Self {
            models: models.try_into().map_err(|_| "model population")?,
            map_certificates: json!({"pair":old.certificate,"fourth":fourth.certificate,"original_prime":ELL,"original_full_order":ORDER,"independent_complementary_twist":pair.certificate,"complementary_order":complementary_order,"quadratic_no13_poles_checked":true,"scope":"original supported compatible source models; extra preflight checks retained, setup not claimed minimal"}),
        })
    }
}

#[cfg(test)]
mod tests;
