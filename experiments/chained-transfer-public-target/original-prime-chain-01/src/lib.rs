//! Prime-only original-instance reprojection under published protocol38b827.
#![allow(dead_code, static_mut_refs)]
#[path = "../generated/adapter.rs"]
pub mod adapter;
#[path = "../generated/norm.rs"]
pub mod norm;
mod rational;
pub use adapter::{Adapter, EncodedPoint, Point, QuarticPoint};
use chained_n4_completed_v2::AdapterV2;
use chained_n4_paired_fourth_preflight::{
    models::{construct_all, er, three, GluingModel, SourceE},
    PairedFourth, ThirdHop, TwistedPair,
};
use chained_n4_public_target::CheckedInstance;
use ghs_original_engines::pic::PicClass;
use isogeny_algos::{
    curve::{self, Pt},
    field::Field,
    fpr::ER,
};
pub use norm::EncodedClass;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::cell::Cell;
pub type Result<T> = std::result::Result<T, String>;
pub const ELL: u64 = 2773073;
pub const ORDER: u128 = 11092292;
pub const HALF: u128 = 1386537;
pub const CASES: [(usize, usize); 3] = [(0, 0), (0, 1), (1, 0)];
pub const MASKS: [u64; 3] = [
    9511681577844867105,
    5188291906266857505,
    2341872925073736705,
];
include!("../generated/parse_packet.rs");
pub fn ep(p: Point) -> Pt<ER> {
    match p {
        None => Pt::Inf,
        Some((x, y)) => Pt::Aff(er(x), er(y)),
    }
}
pub fn kp(p: Pt<ER>) -> Point {
    match p {
        Pt::Inf => None,
        Pt::Aff(x, y) => Some((three(x), three(y))),
    }
}
pub fn point_json(p: Pt<ER>) -> Value {
    json!(kp(p))
}
pub fn degree(from: usize, to: usize) -> u128 {
    assert!(from < 3 && to < 3 && from != to);
    if from.abs_diff(to) == 2 {
        169
    } else {
        13
    }
}
pub fn inverse(n: u128) -> u128 {
    let (mut a, mut b, mut x, mut y) = (n as i128, ELL as i128, 1i128, 0i128);
    while b != 0 {
        let q = a / b;
        (a, b) = (b, a - q * b);
        (x, y) = (y, x - q * y);
    }
    assert_eq!(a, 1);
    let result = x.rem_euclid(ELL as i128) as u128;
    assert_eq!(n * result % ELL as u128, 1);
    result
}
pub struct Geometry {
    pub source: SourceE,
    pub prime: norm::NormNew,
    pub all_six: Vec<Value>,
    pub summary: Value,
}
#[derive(Clone)]
pub struct Entry {
    domain: usize,
    class: PicClass,
    norm: Pt<ER>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourcePoint {
    pub field: String,
    pub source: String,
    pub point: Point,
}
#[derive(Clone, Copy, Debug, Default, Serialize)]
pub struct Calls {
    pub external_class_parse: u64,
    pub external_norm_and_geometry: u64,
    pub external_prime_check: u64,
    pub external_norm_prime_check: u64,
    pub external_point_parse: u64,
    pub external_point_prime_check: u64,
    pub elliptic_inverse_two: u64,
    pub degree13_evaluation: u64,
    pub degree169_evaluation: u64,
    pub target_prime_phi: u64,
    pub norm_point_doubling: u64,
    pub final_actual_norm: u64,
    pub final_prime_check: u64,
    pub inverse_jacobian_scalar: u64,
}
pub struct Runtime {
    pub geometry: [Geometry; 3],
    maps: rational::Maps,
    pub setup: Value,
    calls: Cell<Calls>,
}
impl Runtime {
    pub fn construct(c: &CheckedInstance) -> Result<Self> {
        let old = ThirdHop::construct(c);
        let pair = TwistedPair::construct(c);
        let fourth = PairedFourth::construct(c, &pair);
        Self::from_preflights(c, &old, &fourth)
    }
    pub fn from_preflights(
        c: &CheckedInstance,
        old: &ThirdHop,
        fourth: &PairedFourth<'_>,
    ) -> Result<Self> {
        if c.inst.ell != ELL || c.inst.order as u128 != ORDER {
            return Err("foreign original prime/order".into());
        }
        c.check_field_basis()?;
        let basis = AdapterV2::new(c)?;
        let initial = SourceE::original(c);
        let g2 = old.original_to_source(initial.generator())?;
        let g3 = old.forward(g2)?;
        let branch = fourth.branch(false);
        let g4 = branch.forward(g3)?;
        let equations = [*old.source(), *old.target(), *branch.target()];
        let generators = [g2, g3, g4];
        let tags = [
            old.certificate["E2_id"].as_str().ok_or("E2 tag")?,
            old.certificate["E3_id"].as_str().ok_or("E3 tag")?,
            fourth.certificate["original_target_id"]
                .as_str()
                .ok_or("E4 tag")?,
        ];
        let mut geometry = Vec::new();
        for i in 0..3 {
            let source =
                SourceE::paired_source(c, equations[i], ELL, ORDER, generators[i], tags[i]);
            let (mut all, summary) = construct_all(&source, &basis);
            let rows = all.iter().map(|m| m.row.clone()).collect::<Vec<_>>();
            if all.len() != 6 {
                return Err("entire six-model population required".into());
            }
            let matched = all
                .iter()
                .enumerate()
                .filter(|(_, m)| (m.root_index, m.sign_index) == CASES[i])
                .map(|(k, _)| k)
                .collect::<Vec<_>>();
            if matched.len() != 1 {
                return Err("fixed case missing/duplicated".into());
            }
            let model: GluingModel = all.remove(matched[0]);
            if model.kernel_mask != MASKS[i] || model.p0.is_none() || model.square_root.is_none() {
                return Err("fixed mask or source support".into());
            }
            let prime = norm::NormNew::new(Adapter::new(&source, &basis, model)?)?;
            geometry.push(Geometry {
                source,
                prime,
                all_six: rows,
                summary,
            });
        }
        let maps = rational::Maps::new(
            &equations,
            old.field(),
            &old.certificate,
            &fourth.certificate,
        );
        let setup = json!({"source_identities":geometry.iter().map(|g|g.source.identity()).collect::<Vec<_>>(),"original_third_certificate":old.certificate,"original_fourth_certificate":fourth.certificate,"composites":maps.certificates,"prime":ELL,"full_order":ORDER,"inverse_two":HALF,"inverse13":inverse(13),"inverse169":inverse(169),"scope":"correctness setup retains extra original preflight checks, including independent twist certificates; not minimal production setup or a priced benchmark"});
        Ok(Self {
            geometry: geometry.try_into().map_err(|_| "domain population")?,
            maps,
            setup,
            calls: Cell::new(Calls::default()),
        })
    }
    fn bump(&self, f: impl FnOnce(&mut Calls)) {
        let mut c = self.calls.get();
        f(&mut c);
        self.calls.set(c)
    }
    pub fn reset_calls(&self) {
        self.calls.set(Calls::default())
    }
    pub fn calls(&self) -> Calls {
        self.calls.get()
    }
    pub fn encode(&self, side: usize, class: &PicClass) -> EncodedClass {
        self.geometry[side].prime.encode(class)
    }
    pub fn encode_point(&self, side: usize, p: Pt<ER>) -> SourcePoint {
        let s = &self.geometry[side].source;
        SourcePoint {
            field: s.field_tag().into(),
            source: s.source_tag().into(),
            point: kp(p),
        }
    }
    pub fn admit(&self, side: usize, input: &EncodedClass) -> Result<Entry> {
        if side >= 3 {
            return Err("unknown source domain".into());
        }
        let n = &self.geometry[side].prime;
        self.bump(|c| c.external_class_parse += 1);
        let class = parse_packet(
            &input.field,
            &input.model,
            &input.key,
            &n.field_tag,
            &n.model_tag,
        )?;
        self.bump(|c| c.external_norm_and_geometry += 1);
        let norm = ep(n.norm(&class)?);
        self.bump(|c| c.external_prime_check += 1);
        if !n.a.pic.is_zero(&n.a.pic.mul_scalar(&class, ELL as u128)) {
            return Err("nonprime cofactor input".into());
        }
        self.bump(|c| c.external_norm_prime_check += 1);
        let s = &self.geometry[side].source;
        if curve::pmul(s.field(), s.curve(), &norm, ELL as u128) != Pt::Inf {
            return Err("norm outside source prime subgroup".into());
        }
        Ok(Entry {
            domain: side,
            class,
            norm,
        })
    }
    pub fn gamma(&self, from: usize, to: usize, p: Pt<ER>) -> Result<Pt<ER>> {
        if from >= 3 || to >= 3 || from == to {
            return Err("unknown map direction".into());
        }
        let s = &self.geometry[from].source;
        let t = &self.geometry[to].source;
        if !curve::on_curve(s.field(), s.curve(), &p) {
            return Err("off source curve".into());
        }
        self.bump(|c| {
            if degree(from, to) == 13 {
                c.degree13_evaluation += 1
            } else {
                c.degree169_evaluation += 1
            }
        });
        let q = self.maps.eval(s.field(), s.curve(), t.curve(), from, to, p);
        if !curve::on_curve(t.field(), t.curve(), &q) {
            return Err("off target curve".into());
        }
        Ok(q)
    }
    fn normalized_point(&self, input: &Entry) -> Pt<ER> {
        let s = &self.geometry[input.domain].source;
        self.bump(|c| c.elliptic_inverse_two += 1);
        curve::pmul(s.field(), s.curve(), &input.norm, HALF)
    }
    fn finish_point(&self, to: usize, p: Pt<ER>) -> Result<Entry> {
        let g = &self.geometry[to];
        self.bump(|c| c.target_prime_phi += 1);
        let class = g.prime.a.transfer_point(&kp(p))?;
        self.bump(|c| c.norm_point_doubling += 1);
        let norm = curve::pmul(g.source.field(), g.source.curve(), &p, 2);
        Ok(Entry {
            domain: to,
            class,
            norm,
        })
    }
    pub fn transfer_entry(&self, input: &Entry, to: usize) -> Result<Entry> {
        let p = self.normalized_point(input);
        self.finish_point(to, self.gamma(input.domain, to, p)?)
    }
    pub fn sequential_entry(&self, input: &Entry, to: usize) -> Result<Entry> {
        if input.domain.abs_diff(to) != 2 {
            return Err("two-hop endpoints required".into());
        }
        self.transfer_entry(&self.transfer_entry(input, 1)?, to)
    }
    pub fn retained_entry(&self, input: &Entry, to: usize) -> Result<Entry> {
        if input.domain.abs_diff(to) != 2 {
            return Err("two-hop endpoints required".into());
        }
        let p = self.normalized_point(input);
        self.finish_point(to, self.gamma(1, to, self.gamma(input.domain, 1, p)?)?)
    }
    pub fn check_final(&self, entry: &Entry) -> Result<EncodedClass> {
        let n = &self.geometry[entry.domain].prime;
        self.bump(|c| c.final_actual_norm += 1);
        if ep(n.norm(&entry.class)?) != entry.norm {
            return Err("actual target norm mismatch".into());
        }
        self.bump(|c| c.final_prime_check += 1);
        if !n
            .a
            .pic
            .is_zero(&n.a.pic.mul_scalar(&entry.class, ELL as u128))
        {
            return Err("target outside prime subgroup".into());
        }
        Ok(n.encode(&entry.class))
    }
    pub fn evaluate(&self, from: usize, to: usize, input: &EncodedClass) -> Result<EncodedClass> {
        let entry = self.admit(from, input)?;
        self.check_final(&self.transfer_entry(&entry, to)?)
    }
    pub fn known_point(&self, from: usize, to: usize, input: &SourcePoint) -> Result<EncodedClass> {
        if from >= 3 || to >= 3 || from == to {
            return Err("unknown known-point direction".into());
        }
        let s = &self.geometry[from];
        self.bump(|c| c.external_point_parse += 1);
        if input.field != s.source.field_tag() || input.source != s.source.source_tag() {
            return Err("foreign source point field/model".into());
        }
        s.prime.a.admit(&input.point)?;
        let p = ep(input.point);
        self.bump(|c| c.external_point_prime_check += 1);
        if curve::pmul(s.source.field(), s.source.curve(), &p, ELL as u128) != Pt::Inf {
            return Err("nonprime source point".into());
        }
        self.check_final(&self.finish_point(to, self.gamma(from, to, p)?)?)
    }

    pub fn known_point_factored(
        &self,
        from: usize,
        to: usize,
        input: &SourcePoint,
    ) -> Result<EncodedClass> {
        if from >= 3 || to >= 3 || from.abs_diff(to) != 2 {
            return Err("two-hop known-point endpoints required".into());
        }
        let s = &self.geometry[from];
        self.bump(|c| c.external_point_parse += 1);
        if input.field != s.source.field_tag() || input.source != s.source.source_tag() {
            return Err("foreign source point field/model".into());
        }
        s.prime.a.admit(&input.point)?;
        let p = ep(input.point);
        self.bump(|c| c.external_point_prime_check += 1);
        if curve::pmul(s.source.field(), s.source.curve(), &p, ELL as u128) != Pt::Inf {
            return Err("nonprime source point".into());
        }
        self.check_final(&self.finish_point(to, self.gamma(1, to, self.gamma(from, 1, p)?)?)?)
    }
    pub fn inverse_of(&self, from: usize, to: usize, input: &EncodedClass) -> Result<EncodedClass> {
        if from >= 3 || to >= 3 || from == to {
            return Err("unknown inverse direction".into());
        }
        let admitted = self.admit(to, input)?;
        let back = self.transfer_entry(&admitted, from)?;
        let scalar = inverse(degree(from, to));
        let g = &self.geometry[from];
        self.bump(|c| c.inverse_jacobian_scalar += 1);
        let class = g.prime.a.pic.mul_scalar(&back.class, scalar);
        let norm = curve::pmul(g.source.field(), g.source.curve(), &back.norm, scalar);
        self.check_final(&Entry {
            domain: from,
            class,
            norm,
        })
    }
}
#[cfg(test)]
mod tests;
