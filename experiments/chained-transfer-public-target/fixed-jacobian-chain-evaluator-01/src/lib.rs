//! Full rational group maps under prospective protocol5caf67.
#![allow(dead_code, static_mut_refs)]
use chained_n4_beta_rational_lift::{lift3, point_json, point_key, Rational6};
use chained_n4_fixed_jacobian_chain::{
    norm::EncodedClass, quadratic::descend_class, FixedGeometry, Point, ELL, ORDER,
};
use chained_n4_paired_fourth_preflight::models::{er, even::back6, three};
use chained_n4_public_target::CheckedInstance;
use ghs_original_engines::pic::PicClass;
use isogeny_algos::{
    curve::{self, Curve, Pt},
    field::{Field, Rng},
    fpr::{FpR, ER},
    poly,
};
use serde::Serialize;
use serde_json::{json, Value};
use std::{cell::Cell, collections::BTreeMap};
pub type Result<T> = std::result::Result<T, String>;
#[path = "../generated/literal_halves.rs"]
mod literal_halves;
mod rational;
include!("../generated/halving.rs");
include!("../generated/parse_packet.rs");

pub fn kp(p: Pt<ER>) -> Point {
    match p {
        Pt::Inf => None,
        Pt::Aff(x, y) => Some((three(x), three(y))),
    }
}
pub fn ep(p: Point) -> Pt<ER> {
    match p {
        None => Pt::Inf,
        Some((x, y)) => Pt::Aff(er(x), er(y)),
    }
}
pub fn lift(p: Pt<ER>) -> Pt<ER> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => Pt::Aff(lift3(x), lift3(y)),
    }
}
fn descend_point(p: Pt<ER>) -> Pt<ER> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => Pt::Aff(back6(x), back6(y)),
    }
}
pub fn degree(from: usize, to: usize) -> u128 {
    assert!(from < 3 && to < 3 && from != to);
    if from.abs_diff(to) == 2 {
        169
    } else {
        13
    }
}
pub fn inverse_scalar(n: u128) -> u128 {
    let (mut a, mut b, mut x, mut y) = (n as i128, ORDER as i128, 1i128, 0i128);
    while b != 0 {
        let q = a / b;
        (a, b) = (b, a - q * b);
        (x, y) = (y, x - q * y);
    }
    assert_eq!(a, 1);
    let inverse = x.rem_euclid(ORDER as i128) as u128;
    assert_eq!(n * inverse % ORDER, 1);
    inverse
}

/// Selected source entries, not a complete primitive census or calibrated price.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize)]
pub struct Calls {
    pub external_packet_parse: u64,
    pub external_norm_and_geometry: u64,
    pub external_full_order: u64,
    pub infinity_halves: u64,
    pub two_torsion_halves: u64,
    pub generic_halving_factorization: u64,
    pub generic_ordinate: u64,
    pub explicit_half_check: u64,
    pub quadratic_source_phi: u64,
    pub correction_difference: u64,
    pub correction_dictionary_lookup: u64,
    pub matching_corrections_checked: u64,
    pub source_lift_addition: u64,
    pub degree13_elliptic_evaluation: u64,
    pub degree169_elliptic_evaluation: u64,
    pub quadratic_target_phi: u64,
    pub target_correction_addition: u64,
    pub final_actual_norm: u64,
    pub final_full_order: u64,
    pub inverse_full_group_scalar: u64,
}
#[derive(Clone)]
struct Correction {
    point: Pt<ER>,
    image: PicClass,
}
type Dictionary = BTreeMap<[u32; 19], Vec<Correction>>;
#[derive(Clone)]
pub struct Entry {
    domain: usize,
    class: PicClass,
    norm: Pt<ER>,
}
pub struct Runtime {
    pub geometry: FixedGeometry,
    maps: [[Option<Rational6>; 3]; 3],
    two: [Vec<Pt<ER>>; 3],
    dictionaries: [[Option<Dictionary>; 3]; 3],
    pub setup: Value,
    calls: Cell<Calls>,
}
impl Runtime {
    pub fn construct(c: &CheckedInstance) -> Result<Self> {
        let geometry = FixedGeometry::construct(c)?;
        let (maps, composites) = rational::prepare(&geometry);
        let q3 = 223u128.pow(3);
        let twist_order = 2 * q3 + 2 - ORDER;
        if twist_order != c.inst.order || ORDER * twist_order % 13 == 0 {
            return Err("fixed quadratic extension no13-pole condition unavailable".into());
        }
        let mut two: [Vec<_>; 3] = std::array::from_fn(|_| Vec::new());
        let mut images: [Vec<_>; 3] = std::array::from_fn(|_| Vec::new());
        let mut constructor_points = Vec::new();
        for side in 0..3 {
            let m = &geometry.models[side];
            let f = m.source.field();
            let e = m.source.curve();
            let roots = poly::roots(
                f,
                &vec![e.b, e.a, f.zero(), f.one()],
                &mut Rng::new(0x8210 + side as u64),
            );
            if roots.len() != 3 {
                return Err("full rational E[2] unavailable".into());
            }
            two[side].push(Pt::Inf);
            two[side].extend(roots.into_iter().map(|x| Pt::Aff(x, f.zero())));
            two[side].sort_by_key(|p| point_key(*p));
            two[side].dedup();
            if two[side].len() != 4 {
                return Err("duplicate E[2] point".into());
            }
            for &p in &two[side] {
                if !curve::on_curve(f, e, &p) || curve::pmul(f, e, &p, 2) != Pt::Inf {
                    return Err("invalid actual E[2]".into());
                }
                let image = m.prime.a.transfer_point(&kp(p))?;
                if ep(m.prime.norm(&image)?) != Pt::Inf {
                    return Err("E[2] norm control".into());
                }
                constructor_points
                    .push(json!({"side":side,"point":point_json(p),"prime_image":image.key().0}));
                images[side].push(image);
            }
        }
        let mut dictionaries = std::array::from_fn(|_| std::array::from_fn(|_| None));
        let mut all_dictionaries = Vec::new();
        for from in 0..3 {
            for to in 0..3 {
                if from == to {
                    continue;
                }
                let mut dictionary: Dictionary = BTreeMap::new();
                let mut transports = Vec::new();
                for (i, &p) in two[from].iter().enumerate() {
                    let mapped = maps[from][to]
                        .as_ref()
                        .unwrap()
                        .eval(&geometry.models[from].quadratic.f, lift(p));
                    let mapped = descend_point(mapped);
                    let j = two[to]
                        .iter()
                        .position(|&q| q == mapped)
                        .ok_or("isogeny left rational E[2]")?;
                    let image = images[to][j].clone();
                    let key = images[from][i].key().0;
                    let fibre = dictionary.entry(key).or_default();
                    if fibre.iter().any(|prior| prior.image != image) {
                        return Err("duplicate corrections give different targets".into());
                    }
                    fibre.push(Correction {
                        point: lift(p),
                        image: image.clone(),
                    });
                    transports.push(json!({"source_point":point_json(p),"source_image":key,"target_point":point_json(mapped),"target_image":image.key().0}));
                }
                if dictionary.len() != 2 || dictionary.values().any(|f| f.len() != 2) {
                    return Err("expected two two-point correction fibres".into());
                }
                all_dictionaries
                    .push(json!({"from":from,"to":to,"all_four_transports":transports}));
                dictionaries[from][to] = Some(dictionary);
            }
        }
        let setup = json!({"actual_composite_certificates":composites,"all_actual_E2_images":constructor_points,"all_six_actual_correction_dictionaries":all_dictionaries,"certified_K_order":ORDER,"verified_quadratic_twist_K_order":twist_order,"quadratic_extension_order":ORDER*twist_order,"quadratic_order_formula_bridge":"standard elliptic quadratic-extension order identity","no13_poles":ORDER*twist_order%13!=0,"full_group_inverse13":inverse_scalar(13),"full_group_inverse169":inverse_scalar(169),"constructor_scope":"all three actual prime/quadratic geometries and origins included; selected source work unpriced, complete primitive census pending"});
        Ok(Self {
            geometry,
            maps,
            two,
            dictionaries,
            setup,
            calls: Cell::new(Calls::default()),
        })
    }
    fn bump(&self, f: impl FnOnce(&mut Calls)) {
        let mut c = self.calls.get();
        f(&mut c);
        self.calls.set(c);
    }
    pub fn reset_calls(&self) {
        self.calls.set(Calls::default());
    }
    pub fn calls(&self) -> Calls {
        self.calls.get()
    }
    pub fn encode(&self, side: usize, class: &PicClass) -> EncodedClass {
        self.geometry.models[side].prime.encode(class)
    }
    pub fn admit(&self, side: usize, input: &EncodedClass) -> Result<Entry> {
        if side >= 3 {
            return Err("unknown source domain".into());
        }
        let n = &self.geometry.models[side].prime;
        self.bump(|c| c.external_packet_parse += 1);
        let class = parse_packet(
            &input.field,
            &input.model,
            &input.key,
            &n.field_tag,
            &n.model_tag,
        )?;
        self.bump(|c| c.external_norm_and_geometry += 1);
        let norm = ep(n.norm(&class)?);
        self.bump(|c| c.external_full_order += 1);
        if !n.a.pic.is_zero(&n.a.pic.mul_scalar(&class, ORDER)) {
            return Err("class outside full rational order".into());
        }
        Ok(Entry {
            domain: side,
            class,
            norm,
        })
    }
    pub fn halves(&self, side: usize, q: Pt<ER>) -> Result<Vec<Pt<ER>>> {
        if side >= 3 {
            return Err("unknown halving domain".into());
        }
        let a = &self.geometry.models[side].quadratic;
        let f = &a.f;
        let e = &a.curve;
        let q = lift(q);
        a.admit(&q)?;
        let two = self.two[side].iter().copied().map(lift).collect::<Vec<_>>();
        let mut halves = match q {
            Pt::Inf => {
                self.bump(|c| c.infinity_halves += 1);
                two
            }
            Pt::Aff(_, v) if f.is_zero(v) => {
                self.bump(|c| c.two_torsion_halves += 1);
                literal_halves::literal_halves(f, e, q, &two)
            }
            Pt::Aff(u, _) => {
                self.bump(|c| c.generic_halving_factorization += 1);
                let mut xs = poly::roots(f, &halving_quartic(f, e, u), &mut Rng::new(0x8220));
                xs.sort();
                if xs.len() != 4 {
                    return Err("four generic half roots required".into());
                }
                let mut out = Vec::new();
                for x in xs {
                    self.bump(|c| {
                        c.generic_ordinate += 1;
                        c.explicit_half_check += 1;
                    });
                    out.push(generic_half(f, e, q, x)?);
                }
                out
            }
        };
        halves.sort_by_key(|p| point_key(*p));
        halves.dedup();
        if halves.len() != 4 {
            return Err("all four distinct halves required".into());
        }
        for p in &halves {
            a.admit(p)?;
            self.bump(|c| c.explicit_half_check += 1);
            if curve::pmul(f, e, p, 2) != q {
                return Err("actual doubling rejected half".into());
            }
        }
        Ok(halves)
    }
    fn gamma(&self, from: usize, to: usize, p: Pt<ER>) -> Result<Pt<ER>> {
        if from >= 3 || to >= 3 || from == to {
            return Err("unknown map direction".into());
        }
        self.geometry.models[from].quadratic.admit(&p)?;
        self.bump(|c| {
            if degree(from, to) == 13 {
                c.degree13_elliptic_evaluation += 1
            } else {
                c.degree169_elliptic_evaluation += 1
            }
        });
        let q = self.maps[from][to]
            .as_ref()
            .unwrap()
            .eval(&self.geometry.models[from].quadratic.f, p);
        self.geometry.models[to].quadratic.admit(&q)?;
        Ok(q)
    }
    fn corrected_lift(&self, input: &Entry, to: usize, p: Pt<ER>) -> Result<(Pt<ER>, Value)> {
        let from = input.domain;
        let source = &self.geometry.models[from];
        self.bump(|c| c.quadratic_source_phi += 1);
        let phi = descend_class(&source.quadratic.transfer(p)?)?;
        self.bump(|c| {
            c.correction_difference += 1;
            c.correction_dictionary_lookup += 1;
        });
        let delta = source.prime.a.pic.sub(&input.class, &phi);
        let candidates = self.dictionaries[from][to]
            .as_ref()
            .ok_or("unknown target")?
            .get(&delta.key().0)
            .ok_or("norm-half delta outside rational correction dictionary")?;
        if candidates.len() != 2 {
            return Err("whole two-point correction fibre required".into());
        }
        let first = &candidates[0];
        let mut rows = Vec::new();
        for correction in candidates {
            self.bump(|c| c.matching_corrections_checked += 1);
            if correction.image != first.image {
                return Err("unequal duplicate correction images".into());
            }
            rows.push(json!({"point":point_json(correction.point),"target_correction":correction.image.key().0}));
        }
        self.bump(|c| c.source_lift_addition += 1);
        let lifted = curve::padd(
            &source.quadratic.f,
            &source.quadratic.curve,
            &p,
            &first.point,
        );
        Ok((
            lifted,
            json!({"half":point_json(p),"source_phi":phi.key().0,"delta":delta.key().0,"all_matching_corrections":rows,"corrected_source_lift":point_json(lifted)}),
        ))
    }
    fn target_phi(&self, to: usize, p: Pt<ER>) -> Result<PicClass> {
        self.bump(|c| c.quadratic_target_phi += 1);
        descend_class(&self.geometry.models[to].quadratic.transfer(p)?)
    }
    pub fn transfer_entry(&self, input: &Entry, to: usize) -> Result<Entry> {
        if input.domain >= 3 || to >= 3 || input.domain == to {
            return Err("unknown map direction".into());
        }
        let p = self.halves(input.domain, input.norm)?[0];
        let (lifted, _) = self.corrected_lift(input, to, p)?;
        let class = self.target_phi(to, self.gamma(input.domain, to, lifted)?)?;
        let norm = descend_point(self.gamma(input.domain, to, lift(input.norm))?);
        Ok(Entry {
            domain: to,
            class,
            norm,
        })
    }
    /// Strong shared-admission sequential Jacobian evaluation, with an in-memory
    /// norm retained by the quotient norm identity. Only final checks are repeated.
    pub fn sequential_entry(&self, input: &Entry, to: usize) -> Result<Entry> {
        if input.domain.abs_diff(to) != 2 {
            return Err("two-hop endpoints required".into());
        }
        self.transfer_entry(&self.transfer_entry(input, 1)?, to)
    }
    /// Stronger final-output comparator: carry the corrected elliptic lift and
    /// evaluate the two degree13 maps before one final Phi. No second halving,
    /// correction search or intermediate Jacobian is needed for final output.
    pub fn retained_lift_entry(&self, input: &Entry, to: usize) -> Result<Entry> {
        if input.domain.abs_diff(to) != 2 {
            return Err("two-hop endpoints required".into());
        }
        let p = self.halves(input.domain, input.norm)?[0];
        let (lifted, _) = self.corrected_lift(input, to, p)?;
        let point = self.gamma(1, to, self.gamma(input.domain, 1, lifted)?)?;
        let class = self.target_phi(to, point)?;
        let norm =
            descend_point(self.gamma(1, to, self.gamma(input.domain, 1, lift(input.norm))?)?);
        Ok(Entry {
            domain: to,
            class,
            norm,
        })
    }
    pub fn check_final(&self, entry: &Entry) -> Result<EncodedClass> {
        let n = &self.geometry.models[entry.domain].prime;
        self.bump(|c| c.final_actual_norm += 1);
        if ep(n.norm(&entry.class)?) != entry.norm {
            return Err("actual final norm differs from transported source norm".into());
        }
        self.bump(|c| c.final_full_order += 1);
        if !n.a.pic.is_zero(&n.a.pic.mul_scalar(&entry.class, ORDER)) {
            return Err("final class outside full order".into());
        }
        Ok(n.encode(&entry.class))
    }
    pub fn evaluate(&self, from: usize, to: usize, input: &EncodedClass) -> Result<EncodedClass> {
        let input = self.admit(from, input)?;
        self.check_final(&self.transfer_entry(&input, to)?)
    }
    pub fn inverse_of(&self, from: usize, to: usize, input: &EncodedClass) -> Result<EncodedClass> {
        let input = self.admit(to, input)?;
        let back = self.transfer_entry(&input, from)?;
        let scalar = inverse_scalar(degree(from, to));
        self.bump(|c| c.inverse_full_group_scalar += 1);
        let m = &self.geometry.models[from];
        let class = m.prime.a.pic.mul_scalar(&back.class, scalar);
        let norm = curve::pmul(m.source.field(), m.source.curve(), &back.norm, scalar);
        self.check_final(&Entry {
            domain: from,
            class,
            norm,
        })
    }
    pub fn diagnose_half(&self, input: &Entry, to: usize, p: Pt<ER>) -> Result<(Entry, Value)> {
        let from = input.domain;
        let (lifted, correction) = self.corrected_lift(input, to, p)?;
        let corrected_class = self.target_phi(to, self.gamma(from, to, lifted)?)?;
        let half_image = self.target_phi(to, self.gamma(from, to, p)?)?;
        let delta_key: [u32; 19] =
            serde_json::from_value(correction["delta"].clone()).map_err(|e| e.to_string())?;
        let candidates = &self.dictionaries[from][to].as_ref().unwrap()[&delta_key];
        let pic = &self.geometry.models[to].prime.a.pic;
        let mut sums = Vec::new();
        for c in candidates {
            self.bump(|n| n.target_correction_addition += 1);
            let sum = pic.add(&half_image, &c.image);
            if sum != corrected_class {
                return Err(
                    "combined-lift formula differs from full published correction formula".into(),
                );
            }
            sums.push(json!({"point":point_json(c.point),"target_correction":c.image.key().0,"complete_sum":sum.key().0}));
        }
        let norm = descend_point(self.gamma(from, to, lift(input.norm))?);
        Ok((
            Entry {
                domain: to,
                class: corrected_class.clone(),
                norm,
            },
            json!({"correction":correction,"all_duplicate_sums":sums,"uncorrected_half_image":half_image.key().0,"image":corrected_class.key().0}),
        ))
    }
}

#[cfg(test)]
mod tests;
