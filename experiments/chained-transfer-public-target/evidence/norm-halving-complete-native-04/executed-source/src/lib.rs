//! Prospective6dc948, published d5db7698 before this sibling crate.
//! Selected live call sites are counted; context/primitive costs remain unpriced.
use chained_n4_beta_complete_evaluator::complete::CompleteBeta;
use chained_n4_completed_v2::norm::EncodedClass as OldPacket;
use chained_n4_completed_v2::NormV2;
use chained_n4_odd_product_maps::norm::EncodedClass as NewPacket;
use chained_n4_odd_product_maps::NormNew;
use chained_n4_odd_product_models::er;
use chained_n4_odd_source::OddSourceIsogeny;
use chained_n4_public_target::CheckedInstance;
use ghs_original_engines::pic::PicClass;
use isogeny_algos::{
    curve::{self, Pt},
    fpr::{FpR, ER},
};
use serde::Serialize;
use std::{cell::Cell, collections::BTreeMap};

pub type Result<T> = std::result::Result<T, String>;
pub const ELL: u64 = 2773073;
pub const ORDER: u64 = 11092292;
pub const HALF_ODD: u64 = 1386537;

pub mod direct;
pub mod literal_halves;

pub fn ep(point: Option<([u64; 3], [u64; 3])>) -> Pt<ER> {
    match point {
        None => Pt::Inf,
        Some((x, y)) => Pt::Aff(er(x), er(y)),
    }
}
pub fn kp(point: Pt<ER>) -> Option<([u64; 3], [u64; 3])> {
    match point {
        Pt::Inf => None,
        Pt::Aff(x, y) => {
            assert!(x[3..].iter().chain(&y[3..]).all(|&v| v == 0));
            Some(([x[0], x[1], x[2]], [y[0], y[1], y[2]]))
        }
    }
}

/// The tag/canonical packet predicates match the frozen old/new norm decoders.
/// Both frozen decoders then call norm_ext and discard its result. The shared
/// admission here calls the unchanged public norm once and retains that result.
/// Thus it also retains K projection, curve admission and every scheme check.
fn parse_packet(
    field: &str,
    model: &str,
    key: &[u32; 19],
    wanted_field: &str,
    wanted_model: &str,
) -> Result<PicClass> {
    if field != wanted_field || model != wanted_model || key.iter().any(|&x| x >= 223) {
        return Err("foreign or noncanonical class".into());
    }
    match key[0] {
        0 => {
            if key[4..].iter().any(|&x| x != 0) {
                return Err("exceptional trailing data".into());
            }
            Ok(PicClass::Exc([key[1], key[2], key[3]]))
        }
        1 => Ok(PicClass::Typ(std::array::from_fn(|i| {
            std::array::from_fn(|j| key[1 + 6 * i + j])
        }))),
        _ => Err("unknown class tag".into()),
    }
}

#[derive(Clone, Copy)]
pub(crate) enum CommonEntry {
    Packet,
    Norm,
    Order,
}

/// Shared byte/tag/scheme/K-curve/full-order admission for both comparison arms.
/// The one complete norm is retained for subsequent transfer evaluation.
pub(crate) fn admit_common(
    old: &NormV2,
    new: &NormNew,
    side: usize,
    field: &str,
    model: &str,
    key: &[u32; 19],
    mut count: impl FnMut(CommonEntry),
) -> Result<(PicClass, Pt<ER>)> {
    if side > 1 {
        return Err("unknown map direction".into());
    }
    count(CommonEntry::Packet);
    let (wanted_field, wanted_model) = if side == 0 {
        (&old.field_tag, &old.model_tag)
    } else {
        (&new.field_tag, &new.model_tag)
    };
    let x = parse_packet(field, model, key, wanted_field, wanted_model)?;
    count(CommonEntry::Norm);
    let q = if side == 0 {
        ep(old.norm(&x)?)
    } else {
        ep(new.norm(&x)?)
    };
    let pic = if side == 0 { &old.a.pic } else { &new.a.pic };
    count(CommonEntry::Order);
    if !pic.is_zero(&pic.mul_scalar(&x, ORDER as u128)) {
        return Err("class outside the written rational group order".into());
    }
    Ok((x, q))
}

/// Actual selected entries, not primitive arithmetic or a complete cost ledger.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize)]
pub struct Calls {
    pub common_packet_parse: u64,
    pub common_complete_norm_and_geometry_admission: u64,
    pub common_full_group_order_scalar: u64,
    pub transfer_jacobian_crt_projection: u64,
    pub transfer_elliptic_half_odd_scalar: u64,
    pub transfer_source_isogeny: u64,
    pub transfer_prime_field_phi: u64,
    pub transfer_cofactor_lookup: u64,
    pub transfer_final_subtraction: u64,
}

pub struct StrongScalarBaseline {
    reference: CompleteBeta,
    iso: OddSourceIsogeny,
    f: FpR,
    cofactor: [BTreeMap<[u32; 19], PicClass>; 2],
    calls: Cell<Calls>,
}
impl StrongScalarBaseline {
    pub fn construct(c: &CheckedInstance) -> Result<Self> {
        let reference = CompleteBeta::construct(c)?;
        let iso = OddSourceIsogeny::construct(c);
        let mut cofactor = [BTreeMap::new(), BTreeMap::new()];
        for (side, table) in cofactor.iter_mut().enumerate() {
            for (x, y) in reference.cofactor_pairs(side)? {
                table.insert(x.key().0, y);
            }
            if table.len() != 4 {
                return Err("incomplete original cofactor reference table".into());
            }
        }
        if c.inst.ell != ELL || c.inst.order != ORDER as u128 || 2 * HALF_ODD != ELL + 1 {
            return Err("fixed rational-domain scalar identity rejected".into());
        }
        Ok(Self {
            reference,
            iso,
            f: c.independent_field.clone(),
            cofactor,
            calls: Cell::default(),
        })
    }
    pub fn reference(&self) -> &CompleteBeta {
        &self.reference
    }
    pub fn calls(&self) -> Calls {
        self.calls.get()
    }
    pub fn reset_calls(&self) {
        self.calls.set(Calls::default());
    }
    fn count(&self, change: impl FnOnce(&mut Calls)) {
        let mut calls = self.calls.get();
        change(&mut calls);
        self.calls.set(calls);
    }
    fn admit(
        &self,
        side: usize,
        field: &str,
        model: &str,
        key: &[u32; 19],
    ) -> Result<(PicClass, Pt<ER>)> {
        let b = &self.reference;
        admit_common(b.old(), b.new(), side, field, model, key, |event| {
            self.count(|calls| match event {
                CommonEntry::Packet => calls.common_packet_parse += 1,
                CommonEntry::Norm => calls.common_complete_norm_and_geometry_admission += 1,
                CommonEntry::Order => calls.common_full_group_order_scalar += 1,
            })
        })
    }
    fn evaluate(
        &self,
        side: usize,
        field: &str,
        model: &str,
        key: &[u32; 19],
        correct_cofactor: bool,
    ) -> Result<PicClass> {
        let (x, norm) = self.admit(side, field, model, key)?;
        let b = &self.reference;
        let pic = if side == 0 {
            &b.old().a.pic
        } else {
            &b.new().a.pic
        };
        let target = if side == 0 {
            &b.new().a.pic
        } else {
            &b.old().a.pic
        };
        self.count(|c| c.transfer_jacobian_crt_projection += 1);
        let x2 = pic.mul_scalar(&x, ELL as u128);
        self.count(|c| c.transfer_cofactor_lookup += 1);
        let y2 = self.cofactor[side]
            .get(&x2.key().0)
            .ok_or("actual cofactor reference table has no class")?;
        let curve = if side == 0 {
            self.iso.source()
        } else {
            self.iso.target()
        };
        self.count(|c| c.transfer_elliptic_half_odd_scalar += 1);
        let q = curve::pmul(&self.f, curve, &norm, HALF_ODD as u128);
        self.count(|c| c.transfer_source_isogeny += 1);
        let q = if side == 0 {
            self.iso.forward(q)?
        } else {
            self.iso.dual(q)?
        };
        self.count(|c| c.transfer_prime_field_phi += 1);
        let twice_scaled = if side == 0 {
            b.new().a.transfer_point(&kp(q))?
        } else {
            b.old().a.transfer_point(&kp(q))?
        };
        if correct_cofactor {
            self.count(|c| c.transfer_final_subtraction += 1);
            Ok(target.sub(&twice_scaled, y2))
        } else {
            // Only the unit control calls this private branch.
            Ok(twice_scaled)
        }
    }
    pub fn forward(&self, packet: &OldPacket) -> Result<NewPacket> {
        let y = self.evaluate(0, &packet.field, &packet.model, &packet.key, true)?;
        Ok(self.reference.new().encode(&y))
    }
    pub fn dual(&self, packet: &NewPacket) -> Result<OldPacket> {
        let y = self.evaluate(1, &packet.field, &packet.model, &packet.key, true)?;
        Ok(self.reference.old().encode(&y))
    }
}

#[cfg(test)]
mod tests;
