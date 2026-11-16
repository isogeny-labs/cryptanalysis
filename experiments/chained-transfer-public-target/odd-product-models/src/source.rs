//! A fresh explicit checked source, independent of the old instance's private state.
use chained_n4_odd_source::OddSourceIsogeny;
use chained_n4_public_target::{ghs::EP, CheckedInstance};
use isogeny_algos::{
    curve::{self, Curve, Pt},
    field::{is_prime, Field},
    fpr::{FpR, ER},
};
use serde_json::{json, Value};

pub struct SourceE {
    pub(crate) independent_field: FpR,
    pub(crate) independent_curve: Curve<ER>,
    pub(crate) field_tag: String,
    pub(crate) source_tag: String,
    pub(crate) ell: u64,
    pub(crate) order: u128,
    pub(crate) generator: Pt<ER>,
    pub(crate) reference_quartic: Option<[u32; 15]>,
}
impl SourceE {
    fn original_generator(c: &CheckedInstance) -> Pt<ER> {
        match c.inst.g {
            EP::Inf => Pt::Inf,
            EP::A(x, y) => Pt::Aff(
                c.independent_field
                    .add(super::er(x), super::er(c.short_shift)),
                super::er(y),
            ),
        }
    }
    pub fn original(c: &CheckedInstance) -> Self {
        c.check_field_basis().unwrap();
        let out = Self {
            independent_field: c.independent_field.clone(),
            independent_curve: c.independent_curve,
            field_tag: c.field_tag.clone(),
            source_tag: format!("{}:short", c.model_tag),
            ell: c.inst.ell,
            order: c.inst.order,
            generator: Self::original_generator(c),
            reference_quartic: Some(c.inst.f),
        };
        out.check();
        out
    }
    pub fn degree13_target(c: &CheckedInstance, transfer: &OddSourceIsogeny) -> Self {
        c.check_field_basis().unwrap();
        assert_eq!(transfer.source(), &c.independent_curve);
        let out = Self {
            independent_field: c.independent_field.clone(),
            independent_curve: *transfer.target(),
            field_tag: c.field_tag.clone(),
            source_tag: transfer.certificate["target_id"]
                .as_str()
                .unwrap()
                .to_owned(),
            ell: c.inst.ell,
            order: c.inst.order,
            generator: transfer.forward(Self::original_generator(c)).unwrap(),
            reference_quartic: None,
        };
        out.check();
        out
    }
    fn check(&self) {
        let f = &self.independent_field;
        assert_eq!(f.size(), 223u128.pow(3));
        assert!(curve::is_smooth(f, &self.independent_curve));
        assert!(is_prime(self.ell));
        assert_ne!(self.generator, Pt::Inf);
        assert!(curve::on_curve(f, &self.independent_curve, &self.generator));
        assert_eq!(
            curve::pmul(
                f,
                &self.independent_curve,
                &self.generator,
                self.ell as u128
            ),
            Pt::Inf
        );
        let size = f.size();
        let radius = ghs_original_engines::cover::isqrt_u128(4 * size);
        let first = (size + 1 - radius).div_ceil(self.ell as u128);
        let last = (size + 1 + radius) / self.ell as u128;
        assert_eq!(first, last);
        assert_eq!(first, 4);
        assert_eq!(first * self.ell as u128, self.order);
    }
    pub fn field(&self) -> &FpR {
        &self.independent_field
    }
    pub fn curve(&self) -> &Curve<ER> {
        &self.independent_curve
    }
    pub fn field_tag(&self) -> &str {
        &self.field_tag
    }
    pub fn source_tag(&self) -> &str {
        &self.source_tag
    }
    pub fn ell(&self) -> u64 {
        self.ell
    }
    pub fn order(&self) -> u128 {
        self.order
    }
    pub fn generator(&self) -> Pt<ER> {
        self.generator
    }
    pub fn identity(&self) -> Value {
        json!({"field_modulus":[220,0,0,1],"field_tag":self.field_tag,"source_tag":self.source_tag,
            "a":super::three(self.independent_curve.a),"b":super::three(self.independent_curve.b),
            "ell":self.ell,"order":self.order,"generator":match self.generator {Pt::Inf=>None,Pt::Aff(x,y)=>Some([super::three(x),super::three(y)])},
            "order_certificate":"actual nonzero prime-ell generator plus unique Hasse multiple4;original arithmetic and written Hasse bridge"})
    }
}
