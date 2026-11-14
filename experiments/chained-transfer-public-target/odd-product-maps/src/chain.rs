//! Reusable actual prime-field chain, with no scalar witness in runtime inputs.
use crate::{norm::EncodedClass, Adapter, EncodedPoint, NormNew, Point};
use chained_n4_completed_v2::NormV2;
use chained_n4_odd_product_models::{er, three, SourceE};
use chained_n4_odd_source::OddSourceIsogeny;
use chained_n4_public_target::CheckedInstance;
use ghs_original_engines::pic::PicClass;
use isogeny_algos::{
    curve::{self, Pt},
    field::Field,
    fpr::ER,
};

pub type Result<T> = std::result::Result<T, String>;
fn ep(p: Point) -> Pt<ER> {
    match p {
        None => Pt::Inf,
        Some((x, y)) => Pt::Aff(er(x), er(y)),
    }
}
fn kp(p: Pt<ER>) -> Point {
    match p {
        Pt::Inf => None,
        Pt::Aff(x, y) => Some((three(x), three(y))),
    }
}

pub struct Chain<'a> {
    source: &'a CheckedInstance,
    old: &'a NormV2,
    new: &'a NormNew,
    isogeny: &'a OddSourceIsogeny,
    source_tag: String,
}
impl<'a> Chain<'a> {
    pub fn new(
        source: &'a CheckedInstance,
        old: &'a NormV2,
        new: &'a NormNew,
        isogeny: &'a OddSourceIsogeny,
    ) -> Result<Self> {
        if isogeny.source() != &source.independent_curve
            || isogeny.target() != &new.a.source_ec
            || old.a.field_tag != source.field_tag
            || new.a.field_tag != source.field_tag
            || old.a.core.quartic != source.inst.f.map(u64::from)
            || old.a.ell != source.inst.ell
            || new.a.ell != source.inst.ell
            || old.a.expected_order as u128 != source.inst.order
            || new.a.expected_order as u128 != source.inst.order
        {
            return Err("foreign source/target/field/order identity in chain".into());
        }
        Ok(Self {
            source,
            old,
            new,
            isogeny,
            source_tag: SourceE::original(source).source_tag().to_owned(),
        })
    }
    pub fn forward_old(&self, x: &PicClass) -> Result<PicClass> {
        let old_norm = self.old.norm(x)?;
        let transported = kp(self.isogeny.forward(ep(old_norm))?);
        self.new.a.transfer_point(&transported)
    }
    pub fn reverse_new(&self, y: &PicClass) -> Result<PicClass> {
        let new_norm = self.new.norm(y)?;
        let transported = kp(self.isogeny.dual(ep(new_norm))?);
        self.old.a.transfer_point(&transported)
    }
    fn admit_source_odd(&self, p: Point) -> Result<()> {
        if let Some((x, y)) = p {
            if x.iter().chain(y.iter()).any(|&v| v >= 223) {
                return Err("noncanonical source coordinates".into());
            }
        }
        let f = &self.source.independent_field;
        let e = &self.source.independent_curve;
        if !curve::on_curve(f, e, &ep(p))
            || curve::pmul(f, e, &ep(p), self.source.inst.ell as u128) != Pt::Inf
        {
            return Err("source point is off curve or outside the odd subgroup".into());
        }
        Ok(())
    }
    pub fn from_source_odd_coords(&self, p: Point) -> Result<PicClass> {
        self.admit_source_odd(p)?;
        self.forward_old(&self.old.a.transfer_point(&p)?)
    }
    pub fn recover_source_odd_coords(&self, y: &PicClass) -> Result<Point> {
        let p = &self.new.a.pic;
        if !p.is_zero(&p.mul_scalar(y, self.source.inst.ell as u128)) {
            return Err("new class is outside the odd subgroup".into());
        }
        let norm = self.new.norm(y)?;
        let original = self.isogeny.dual(ep(norm))?;
        let recovered = kp(curve::pmul(
            &self.source.independent_field,
            &self.source.independent_curve,
            &original,
            159985,
        ));
        self.admit_source_odd(recovered)?;
        if self.from_source_odd_coords(recovered)? != *y {
            return Err("source recovery forward roundtrip rejected".into());
        }
        Ok(recovered)
    }
    pub fn encode_source(&self, p: Point) -> EncodedPoint {
        EncodedPoint {
            field: self.source.field_tag.clone(),
            model: self.source_tag.clone(),
            coordinates: p,
        }
    }
    pub fn from_source(&self, p: &EncodedPoint) -> Result<EncodedClass> {
        if p.field != self.source.field_tag || p.model != self.source_tag {
            return Err("foreign original short-source field/model tag".into());
        }
        Ok(self
            .new
            .encode(&self.from_source_odd_coords(p.coordinates)?))
    }
    pub fn recover_source(&self, y: &EncodedClass) -> Result<EncodedPoint> {
        let class = self.new.decode(y)?;
        Ok(self.encode_source(self.recover_source_odd_coords(&class)?))
    }
    pub fn target(&self) -> &Adapter {
        &self.new.a
    }
}
