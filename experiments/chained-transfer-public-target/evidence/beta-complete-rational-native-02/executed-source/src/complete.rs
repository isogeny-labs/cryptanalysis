//! Matched HLP(1,0) complete rational beta, under prospective5be5e0.
//! Finite cofactor preprocessing is explicit; no odd-DLP table or witness.
use crate::{descend_class, BaseChanged, Result};
use chained_n4_beta_rational_lift::{four_torsion, Rational6};
use chained_n4_completed_v2::{norm::EncodedClass as OldPacket, AdapterV2, NormV2};
use chained_n4_odd_product_maps::{norm::EncodedClass as NewPacket, Adapter, NormNew};
use chained_n4_odd_product_models::{construct_all, er, three, SourceE};
use chained_n4_odd_source::OddSourceIsogeny;
use chained_n4_public_target::CheckedInstance;
use ghs_original_engines::pic::PicClass;
use isogeny_algos::{
    curve::{self, Pt},
    fpr::{FpR, ER},
};
use std::collections::BTreeMap;

fn ep(p: Option<([u64; 3], [u64; 3])>) -> Pt<ER> {
    match p {
        None => Pt::Inf,
        Some((x, y)) => Pt::Aff(er(x), er(y)),
    }
}
fn kp(p: Pt<ER>) -> Option<([u64; 3], [u64; 3])> {
    match p {
        Pt::Inf => None,
        Pt::Aff(x, y) => Some((three(x), three(y))),
    }
}

pub struct CompleteBeta {
    old: NormV2,
    new: NormNew,
    iso: OddSourceIsogeny,
    old2: BaseChanged,
    new2: BaseChanged,
    cofactor: [BTreeMap<[u32; 19], PicClass>; 2],
    ell: u64,
    order: u64,
    source_field: FpR,
}
impl CompleteBeta {
    pub fn construct(c: &CheckedInstance) -> Result<Self> {
        Self::with_candidate(c, (1, 0))
    }
    pub fn with_candidate(c: &CheckedInstance, candidate: (usize, usize)) -> Result<Self> {
        if candidate != (1, 0) {
            return Err("complete beta requires the matched transported HLP(1,0) kernel".into());
        }
        c.check_field_basis()?;
        if c.inst.ell != 2773073 || c.inst.order != 11092292 {
            return Err("unsupported rational group order".into());
        }
        let iso = OddSourceIsogeny::construct(c);
        let source = SourceE::degree13_target(c, &iso);
        let a = AdapterV2::new(c)?;
        let (models, _) = construct_all(&source, &a);
        let m = models
            .into_iter()
            .find(|m| (m.root_index, m.sign_index) == candidate)
            .ok_or("missing actual matched model")?;
        let new = NormNew::new(Adapter::new(&source, &a, m)?)?;
        let old = NormV2::new(a)?;
        let a2 = AdapterV2::new(c)?;
        let (models, _) = construct_all(&source, &a2);
        let m = models
            .into_iter()
            .find(|m| (m.root_index, m.sign_index) == candidate)
            .ok_or("missing matched base-change model")?;
        let b2 = Adapter::new(&source, &a2, m)?;
        if a2.model_tag != old.a.model_tag
            || b2.model_tag != new.a.model_tag
            || b2.kernel_mask != new.a.kernel_mask
            || a2.pic.base_point() != old.a.pic.base_point()
            || b2.pic.base_point() != new.a.pic.base_point()
        {
            return Err("prime/quadratic model or origin identity mismatch".into());
        }
        let old2 = BaseChanged::old(a2)?;
        let new2 = BaseChanged::new(b2)?;
        let points = [
            four_torsion(&c.independent_field, &old2.f, iso.source()),
            four_torsion(&c.independent_field, &new2.f, iso.target()),
        ];
        let images = [
            points[0]
                .iter()
                .map(|&p| old2.transfer(p))
                .collect::<Result<Vec<_>>>()?,
            points[1]
                .iter()
                .map(|&p| new2.transfer(p))
                .collect::<Result<Vec<_>>>()?,
        ];
        let gamma = Rational6::new(&iso.certificate["forward"]);
        let delta = Rational6::new(&iso.certificate["actual_dual"]);
        let mut cofactor = [BTreeMap::new(), BTreeMap::new()];
        let mut counts = [BTreeMap::<[u32; 19], usize>::new(), BTreeMap::new()];
        for (side, a, map) in [(0, &old2, &gamma), (1, &new2, &delta)] {
            for (i, &p) in points[side].iter().enumerate() {
                let x = &images[side][i];
                if x.key().0.iter().any(|&x| x >= 223) {
                    continue;
                }
                let q = map.eval(&a.f, p);
                let j = points[1 - side]
                    .iter()
                    .position(|&v| v == q)
                    .ok_or("actual isogeny left complete E4 panel")?;
                let y = descend_class(&images[1 - side][j])?;
                let key = x.key().0;
                if let Some(old) = cofactor[side].insert(key, y.clone()) {
                    if old != y {
                        return Err("two actual lifts give different beta images".into());
                    }
                }
                *counts[side].entry(key).or_default() += 1;
            }
            if cofactor[side].len() != 4 || counts[side].values().any(|&n| n != 2) {
                return Err("actual rational four-torsion lift coverage is incomplete".into());
            }
        }
        let out = Self {
            old,
            new,
            iso,
            old2,
            new2,
            cofactor,
            ell: c.inst.ell,
            order: c.inst.order as u64,
            source_field: c.independent_field.clone(),
        };
        if 2 * 1386537 % out.ell != 1 || 26 * 319970 % out.ell != 1 || 13 * 3413013 % out.order != 1
        {
            return Err("fixed scalar inverse identity rejected".into());
        }
        // Bounded cofactor tables are checked as group maps, including both [13].
        for side in 0..2 {
            let p = if side == 0 {
                &out.old.a.pic
            } else {
                &out.new.a.pic
            };
            let target = if side == 0 {
                &out.new.a.pic
            } else {
                &out.old.a.pic
            };
            for (key, y) in &out.cofactor[side] {
                let x = out.class_from_key(side, *key)?;
                if !p.is_zero(&p.mul_scalar(&x, 4)) {
                    return Err("cofactor input exceeds exponent4".into());
                }
                let back = out.cofactor[1 - side]
                    .get(&y.key().0)
                    .ok_or("reverse cofactor domain mismatch")?;
                if *back != p.mul_scalar(&x, 13) {
                    return Err("cofactor dual composition is not [13]".into());
                }
                for (key2, y2) in &out.cofactor[side] {
                    let x2 = out.class_from_key(side, *key2)?;
                    let sum = p.add(&x, &x2);
                    if out.cofactor[side].get(&sum.key().0) != Some(&target.add(y, y2)) {
                        return Err("cofactor table is not additive".into());
                    }
                }
            }
        }
        Ok(out)
    }
    fn class_from_key(&self, side: usize, key: [u32; 19]) -> Result<PicClass> {
        if side == 0 {
            self.old.decode(&OldPacket {
                field: self.old.field_tag.clone(),
                model: self.old.model_tag.clone(),
                key,
            })
        } else {
            self.new.decode(&NewPacket {
                field: self.new.field_tag.clone(),
                model: self.new.model_tag.clone(),
                key,
            })
        }
    }
    pub fn old(&self) -> &NormV2 {
        &self.old
    }
    pub fn new(&self) -> &NormNew {
        &self.new
    }
    pub fn old_quadratic(&self) -> &BaseChanged {
        &self.old2
    }
    pub fn new_quadratic(&self) -> &BaseChanged {
        &self.new2
    }
    pub fn cofactor_pairs(&self, side: usize) -> Result<Vec<(PicClass, PicClass)>> {
        if side > 1 {
            return Err("unknown cofactor side".into());
        }
        self.cofactor[side]
            .iter()
            .map(|(k, y)| Ok((self.class_from_key(side, *k)?, y.clone())))
            .collect()
    }
    fn twice_forward(&self, x: &PicClass) -> Result<PicClass> {
        let p = self.iso.forward(ep(self.old.norm(x)?))?;
        self.new.a.transfer_point(&kp(p))
    }
    fn twice_reverse(&self, y: &PicClass) -> Result<PicClass> {
        let p = self.iso.dual(ep(self.new.norm(y)?))?;
        self.old.a.transfer_point(&kp(p))
    }
    fn evaluate(&self, side: usize, x: &PicClass) -> Result<PicClass> {
        let p = if side == 0 {
            &self.old.a.pic
        } else {
            &self.new.a.pic
        };
        let target = if side == 0 {
            &self.new.a.pic
        } else {
            &self.old.a.pic
        };
        if !p.is_zero(&p.mul_scalar(x, self.order as u128)) {
            return Err("class outside the written rational group order".into());
        }
        let x2 = p.mul_scalar(x, self.ell as u128);
        let xo = p.sub(x, &x2);
        if !p.is_zero(&p.mul_scalar(&x2, 4)) || !p.is_zero(&p.mul_scalar(&xo, self.ell as u128)) {
            return Err("odd/cofactor decomposition rejected".into());
        }
        let y2 = self.cofactor[side]
            .get(&x2.key().0)
            .ok_or("rational cofactor class missing from complete lift table")?;
        let twice = if side == 0 {
            self.twice_forward(&xo)?
        } else {
            self.twice_reverse(&xo)?
        };
        let yo = target.mul_scalar(&twice, 1386537);
        Ok(target.add(&yo, y2))
    }
    pub fn forward(&self, packet: &OldPacket) -> Result<NewPacket> {
        let x = self.old.decode(packet)?;
        Ok(self.new.encode(&self.evaluate(0, &x)?))
    }
    pub fn dual(&self, packet: &NewPacket) -> Result<OldPacket> {
        let y = self.new.decode(packet)?;
        Ok(self.old.encode(&self.evaluate(1, &y)?))
    }
    pub fn inverse(&self, packet: &NewPacket) -> Result<OldPacket> {
        let y = self.new.decode(packet)?;
        let back = self.evaluate(1, &y)?;
        // 13*3413013 = 4*11092292+1; valid on the FULL rational group.
        Ok(self.old.encode(&self.old.a.pic.mul_scalar(&back, 3413013)))
    }
    pub fn recover_source_odd(&self, packet: &NewPacket) -> Result<Pt<ER>> {
        let y = self.new.decode(packet)?;
        if !self
            .new
            .a
            .pic
            .is_zero(&self.new.a.pic.mul_scalar(&y, self.ell as u128))
        {
            return Err("source recovery requires the odd subgroup".into());
        }
        let back = self.evaluate(1, &y)?;
        let norm = ep(self.old.norm(&back)?);
        // N0 betaDual beta Phi0 = [26] on the original odd source.
        let p = curve::pmul(&self.source_field, self.iso.source(), &norm, 319970);
        let original_class = self.old.a.transfer_point(&kp(p))?;
        if self.evaluate(0, &original_class)? != y {
            return Err("recovered source forward roundtrip rejected".into());
        }
        Ok(p)
    }
}
