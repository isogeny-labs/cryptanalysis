//! Complete norm-halving route, with explicit E[2](K) correction and admission.
//! No complete-C evaluator or four-class cofactor table is used by this runtime.
use crate::{admit_common, kp, CommonEntry, Result, ELL, ORDER};
use chained_n4_beta_complete_evaluator::{descend_class, BaseChanged};
use chained_n4_beta_rational_lift::{frob_point, lift3, point_json, point_key, Rational6};
use chained_n4_completed_v2::{norm::EncodedClass as OldPacket, AdapterV2, NormV2};
use chained_n4_odd_product_maps::{norm::EncodedClass as NewPacket, Adapter, NormNew};
use chained_n4_odd_product_models::{construct_all, SourceE};
use chained_n4_odd_source::OddSourceIsogeny;
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

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize)]
pub struct DirectCalls {
    pub common_packet_parse: u64,
    pub common_complete_norm_and_geometry_admission: u64,
    pub common_full_group_order_scalar: u64,
    pub transfer_quartic_root_factorization: u64,
    pub transfer_generic_ordinate_recovery: u64,
    /// Explicit checks in this module. The literal selector's internal work is unpriced.
    pub transfer_explicit_double_check: u64,
    pub transfer_infinity_half_dictionary: u64,
    pub transfer_literal_two_torsion_selector: u64,
    pub transfer_quadratic_source_phi: u64,
    pub transfer_source_isogeny: u64,
    pub transfer_quadratic_target_phi: u64,
    pub transfer_two_torsion_lookup: u64,
    pub transfer_final_addition: u64,
    pub full_inverse_jacobian_scalar: u64,
}

#[derive(Clone, Debug, Default, Serialize)]
pub struct SetupCalls {
    pub prime_two_torsion_factorizations: [u64; 2],
    pub prime_two_point_phi: [u64; 2],
    pub two_point_source_isogeny: [u64; 2],
    pub separate_quadratic_origin_traces: [u64; 2],
}

pub fn lift_point(p: Pt<ER>) -> Pt<ER> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => Pt::Aff(lift3(x), lift3(y)),
    }
}

/// H(X), in ascending coefficient order, from the already proved duplication identity.
pub fn halving_quartic(f: &FpR, e: &Curve<ER>, u: ER) -> Vec<ER> {
    vec![
        f.sub(f.sq(e.a), f.mul(f.from_u64(4), f.mul(e.b, u))),
        f.neg(f.mul(
            f.from_u64(4),
            f.add(f.mul(e.a, u), f.mul(f.from_u64(2), e.b)),
        )),
        f.neg(f.mul(f.from_u64(2), e.a)),
        f.neg(f.mul(f.from_u64(4), u)),
        f.one(),
    ]
}

/// Fast ordinate recovery, followed by actual on-curve and full doubling checks.
/// Infinity and v=0 have separate complete branches and are rejected here.
pub fn generic_half(f: &FpR, e: &Curve<ER>, q: Pt<ER>, x: ER) -> Result<Pt<ER>> {
    let Pt::Aff(u, v) = q else {
        return Err("generic ordinate requires finite non-two-torsion Q".into());
    };
    let denominator = f.mul(f.from_u64(2), v);
    if f.is_zero(denominator) {
        return Err("zero generic ordinate denominator".into());
    }
    let t = f.sub(
        f.sub(
            f.sub(
                f.sub(f.mul(f.sq(x), x), f.mul(f.from_u64(3), f.mul(u, f.sq(x)))),
                f.mul(e.a, x),
            ),
            f.mul(e.a, u),
        ),
        f.mul(f.from_u64(2), e.b),
    );
    let p = Pt::Aff(x, f.div(t, denominator));
    if !curve::on_curve(f, e, &p) || curve::pmul(f, e, &p, 2) != q {
        return Err("ordinate did not give an actual half".into());
    }
    Ok(p)
}

fn adapters(c: &CheckedInstance, iso: &OddSourceIsogeny) -> Result<(AdapterV2, Adapter)> {
    let a = AdapterV2::new(c)?;
    let source = SourceE::degree13_target(c, iso);
    let (models, _) = construct_all(&source, &a);
    let m = models
        .into_iter()
        .find(|m| (m.root_index, m.sign_index) == (1, 0))
        .ok_or("missing matched HLP(1,0) model")?;
    let b = Adapter::new(&source, &a, m)?;
    Ok((a, b))
}

pub struct DirectNormHalving {
    old: NormV2,
    new: NormNew,
    quadratic: [BaseChanged; 2],
    isogenies: [Rational6; 2],
    two: [Vec<Pt<ER>>; 2],
    corrections: [BTreeMap<[u32; 19], (Pt<ER>, PicClass)>; 2],
    setup: SetupCalls,
    calls: Cell<DirectCalls>,
    elliptic_quadratic_order_from_existing_input: u128,
}
impl DirectNormHalving {
    pub fn construct(c: &CheckedInstance) -> Result<Self> {
        Self::with_candidate(c, (1, 0))
    }
    pub fn with_candidate(c: &CheckedInstance, candidate: (usize, usize)) -> Result<Self> {
        if candidate != (1, 0) {
            return Err("direct norm-halving requires matched HLP(1,0)".into());
        }
        c.check_field_basis()?;
        if c.inst.ell != ELL || c.inst.order != ORDER as u128 {
            return Err("unsupported rational domain".into());
        }
        let iso = OddSourceIsogeny::construct(c);
        let (a, b) = adapters(c, &iso)?;
        let old = NormV2::new(a)?;
        let new = NormNew::new(b)?;
        let (a, b) = adapters(c, &iso)?;
        if a.model_tag != old.model_tag
            || b.model_tag != new.model_tag
            || a.pic.base_point() != old.a.pic.base_point()
            || b.pic.base_point() != new.a.pic.base_point()
        {
            return Err("prime/quadratic model or origin mismatch".into());
        }
        let quadratic = [BaseChanged::old(a)?, BaseChanged::new(b)?];
        let f3 = c.independent_field.clone();
        let curves = [iso.source(), iso.target()];
        let mut setup = SetupCalls::default();
        let mut two = [Vec::new(), Vec::new()];
        let mut prime_images = [Vec::new(), Vec::new()];
        for side in 0..2 {
            setup.prime_two_torsion_factorizations[side] += 1;
            let roots = poly::roots(
                &f3,
                &vec![curves[side].b, curves[side].a, f3.zero(), f3.one()],
                &mut Rng::new(0x7410 + side as u64),
            );
            if roots.len() != 3 {
                return Err("actual full E[2](K) required".into());
            }
            two[side].push(Pt::Inf);
            for x in roots {
                two[side].push(Pt::Aff(x, f3.zero()))
            }
            two[side].sort_by_key(|p| point_key(*p));
            two[side].dedup();
            if two[side].len() != 4 {
                return Err("two-torsion panel is incomplete".into());
            }
            for &p in &two[side] {
                if !curve::on_curve(&f3, curves[side], &p)
                    || curve::pmul(&f3, curves[side], &p, 2) != Pt::Inf
                {
                    return Err("invalid actual E[2] point".into());
                }
                setup.prime_two_point_phi[side] += 1;
                prime_images[side].push(if side == 0 {
                    old.a.transfer_point(&kp(p))?
                } else {
                    new.a.transfer_point(&kp(p))?
                });
            }
            setup.separate_quadratic_origin_traces[side] = quadratic[side].origin_trace_calls();
        }
        let mut corrections = [
            BTreeMap::<[u32; 19], (Pt<ER>, PicClass)>::new(),
            BTreeMap::new(),
        ];
        for side in 0..2 {
            let mut fibres = BTreeMap::<[u32; 19], usize>::new();
            for (i, &p) in two[side].iter().enumerate() {
                setup.two_point_source_isogeny[side] += 1;
                let q = if side == 0 {
                    iso.forward(p)?
                } else {
                    iso.dual(p)?
                };
                let j = two[1 - side]
                    .iter()
                    .position(|&t| t == q)
                    .ok_or("source isogeny left E[2](K)")?;
                let key = prime_images[side][i].key().0;
                let y = prime_images[1 - side][j].clone();
                if let Some((_, prior)) = corrections[side].get(&key) {
                    if prior != &y {
                        return Err("two equal Phi torsion images give unequal Psi values".into());
                    }
                } else {
                    corrections[side].insert(key, (lift_point(p), y));
                }
                *fibres.entry(key).or_default() += 1;
            }
            if corrections[side].len() != 2 || fibres.values().any(|&n| n != 2) {
                return Err("actual E[2] correction dictionary is not two two-point fibres".into());
            }
        }
        // The original rational maps have no degree13 kernel point over this L.
        // This uses the existing #E(K) input and the standard quadratic order formula;
        // it is not a new formal point-count certificate or a general pole handler.
        let q3 = 223u128.pow(3);
        let n = ORDER as u128;
        let quadratic_order = n * (2 * q3 + 2 - n);
        if quadratic_order % 13 == 0 {
            return Err("fixed-field no13-pole condition unavailable".into());
        }
        Ok(Self {
            old,
            new,
            quadratic,
            isogenies: [
                Rational6::new(&iso.certificate["forward"]),
                Rational6::new(&iso.certificate["actual_dual"]),
            ],
            two,
            corrections,
            setup,
            calls: Cell::default(),
            elliptic_quadratic_order_from_existing_input: quadratic_order,
        })
    }
    pub fn old(&self) -> &NormV2 {
        &self.old
    }
    pub fn new(&self) -> &NormNew {
        &self.new
    }
    pub fn quadratic(&self, side: usize) -> &BaseChanged {
        &self.quadratic[side]
    }
    pub fn setup(&self) -> &SetupCalls {
        &self.setup
    }
    pub fn calls(&self) -> DirectCalls {
        self.calls.get()
    }
    pub fn reset_calls(&self) {
        self.calls.set(DirectCalls::default())
    }
    fn count(&self, f: impl FnOnce(&mut DirectCalls)) {
        let mut c = self.calls.get();
        f(&mut c);
        self.calls.set(c)
    }
    fn admit(
        &self,
        side: usize,
        field: &str,
        model: &str,
        key: &[u32; 19],
    ) -> Result<(PicClass, Pt<ER>)> {
        admit_common(&self.old, &self.new, side, field, model, key, |event| {
            self.count(|c| match event {
                CommonEntry::Packet => c.common_packet_parse += 1,
                CommonEntry::Norm => c.common_complete_norm_and_geometry_admission += 1,
                CommonEntry::Order => c.common_full_group_order_scalar += 1,
            })
        })
    }
    pub fn halves_of_norm(&self, side: usize, norm: Pt<ER>) -> Result<Vec<Pt<ER>>> {
        if side > 1 {
            return Err("unknown half direction".into());
        }
        let q = lift_point(norm);
        let a = &self.quadratic[side];
        let f = &a.f;
        let e = &a.curve;
        a.admit(&q)?;
        let two = self.two[side]
            .iter()
            .copied()
            .map(lift_point)
            .collect::<Vec<_>>();
        let mut halves = match q {
            Pt::Inf => {
                self.count(|c| c.transfer_infinity_half_dictionary += 1);
                two
            }
            Pt::Aff(_, v) if f.is_zero(v) => {
                self.count(|c| c.transfer_literal_two_torsion_selector += 1);
                crate::literal_halves::literal_halves(f, e, q, &two)
            }
            Pt::Aff(u, _) => {
                self.count(|c| c.transfer_quartic_root_factorization += 1);
                let mut roots = poly::roots(f, &halving_quartic(f, e, u), &mut Rng::new(0x7416));
                roots.sort();
                if roots.len() != 4 {
                    return Err("generic quartic did not give four distinct roots".into());
                }
                let mut out = Vec::new();
                for x in roots {
                    self.count(|c| {
                        c.transfer_generic_ordinate_recovery += 1;
                        c.transfer_explicit_double_check += 1
                    });
                    out.push(generic_half(f, e, q, x)?)
                }
                out
            }
        };
        halves.sort_by_key(|p| point_key(*p));
        halves.dedup();
        if halves.len() != 4 {
            return Err("complete halving did not give four points".into());
        }
        for p in &halves {
            a.admit(p)?;
            self.count(|c| c.transfer_explicit_double_check += 1);
            if curve::pmul(f, e, p, 2) != q {
                return Err("half verification rejected".into());
            }
        }
        Ok(halves)
    }
    fn phi(&self, side: usize, p: Pt<ER>) -> Result<PicClass> {
        self.count(|c| c.transfer_quadratic_source_phi += 1);
        descend_class(&self.quadratic[side].transfer(p)?)
    }
    fn psi(&self, side: usize, p: Pt<ER>) -> Result<PicClass> {
        self.quadratic[side].admit(&p)?;
        self.count(|c| c.transfer_source_isogeny += 1);
        let q = self.isogenies[side].eval(&self.quadratic[side].f, p);
        self.quadratic[1 - side].admit(&q)?;
        self.count(|c| c.transfer_quadratic_target_phi += 1);
        descend_class(&self.quadratic[1 - side].transfer(q)?)
    }
    fn evaluate_lift(
        &self,
        side: usize,
        x: &PicClass,
        a: Pt<ER>,
    ) -> Result<(PicClass, Pt<ER>, PicClass, PicClass, PicClass)> {
        let phi = self.phi(side, a)?;
        let pic = if side == 0 {
            &self.old.a.pic
        } else {
            &self.new.a.pic
        };
        let target = if side == 0 {
            &self.new.a.pic
        } else {
            &self.old.a.pic
        };
        let d = pic.sub(x, &phi);
        self.count(|c| c.transfer_two_torsion_lookup += 1);
        let (t, correction) = self.corrections[side]
            .get(&d.key().0)
            .ok_or("norm half difference is outside actual E[2](K) image")?;
        let psi = self.psi(side, a)?;
        self.count(|c| c.transfer_final_addition += 1);
        let y = target.add(&psi, correction);
        Ok((y, *t, phi, d, psi))
    }
    fn evaluate(&self, side: usize, field: &str, model: &str, key: &[u32; 19]) -> Result<PicClass> {
        let (x, q) = self.admit(side, field, model, key)?;
        let halves = self.halves_of_norm(side, q)?;
        Ok(self.evaluate_lift(side, &x, halves[0])?.0)
    }
    pub fn forward(&self, p: &OldPacket) -> Result<NewPacket> {
        Ok(self
            .new
            .encode(&self.evaluate(0, &p.field, &p.model, &p.key)?))
    }
    pub fn dual(&self, p: &NewPacket) -> Result<OldPacket> {
        Ok(self
            .old
            .encode(&self.evaluate(1, &p.field, &p.model, &p.key)?))
    }
    pub fn inverse(&self, p: &NewPacket) -> Result<OldPacket> {
        let y = self.evaluate(1, &p.field, &p.model, &p.key)?;
        self.count(|c| c.full_inverse_jacobian_scalar += 1);
        Ok(self.old.encode(&self.old.a.pic.mul_scalar(&y, 3413013)))
    }
    pub fn diagnose_all_lifts(
        &self,
        side: usize,
        field: &str,
        model: &str,
        key: &[u32; 19],
    ) -> Result<Value> {
        let (x, q) = self.admit(side, field, model, key)?;
        let halves = self.halves_of_norm(side, q)?;
        let f = &self.quadratic[side].f;
        let e = &self.quadratic[side].curve;
        let mut rows = Vec::new();
        let mut common = None;
        for a in halves {
            let (y, t, phi, d, psi) = self.evaluate_lift(side, &x, a)?;
            if let Some(ref previous) = common {
                if previous != &y {
                    return Err("four corrected halves disagree".into());
                }
            } else {
                common = Some(y.clone())
            }
            let corrected = curve::padd(f, e, &a, &t);
            if self.phi(side, corrected)? != x || self.psi(side, corrected)? != y {
                return Err("actual corrected lift roundtrip rejected".into());
            }
            let gamma = self.isogenies[side].eval(f, a);
            let dual = self.isogenies[1 - side].eval(f, gamma);
            if dual != curve::pmul(f, e, &a, 13) {
                return Err("actual source-isogeny [13] composition on half failed".into());
            }
            if frob_point(f, curve::pmul(f, e, &a, 2), 3) != curve::pmul(f, e, &a, 2) {
                return Err("norm half did not double to a K point".into());
            }
            rows.push(json!({"half":point_json(a),"phi_half":phi.key().0.to_vec(),"difference":d.key().0.to_vec(),"correction_t":point_json(t),"psi_half":psi.key().0.to_vec(),"corrected_lift":point_json(corrected),"image":y.key().0.to_vec(),"source_isogeny_then_actual_dual":point_json(dual)}));
        }
        Ok(
            json!({"all4":rows,"norm":point_json(lift_point(q)),"selected_calls_including_diagnostic_verification":self.calls()}),
        )
    }
    pub fn correction_dictionary(&self, side: usize) -> Value {
        json!(self.corrections[side].iter().map(|(key,(t,y))|json!({"phi_t":key.to_vec(),"representative_t":point_json(*t),"psi_t":y.key().0.to_vec()})).collect::<Vec<_>>())
    }
    pub fn quadratic_order_from_existing_input(&self) -> u128 {
        self.elliptic_quadratic_order_from_existing_input
    }
}
