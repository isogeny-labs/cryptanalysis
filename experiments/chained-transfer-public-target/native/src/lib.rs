//! Public-Q plumbing for the unchanged original N4/B2 algorithm.
//! Prospective protocol7e016c/f888 was published in ready PR1523 before code.
#![allow(dead_code, static_mut_refs)]

#[path = "../original/common.rs"]
pub mod common;
#[path = "../original/ghs.rs"]
pub mod ghs;
#[path = "../original/ic.rs"]
pub mod ic;
#[path = "../derived/public_solver.rs"]
pub mod public_solver;
pub use ghs_original_engines::pic;
#[cfg(test)]
#[path = "../original/solver.rs"]
mod legacy_solver;

use common::K;
use ghs::{Inst, EP};
use isogeny_algos::curve::{self, Curve, Pt};
use isogeny_algos::field::Field;
use isogeny_algos::fpr::{FpR, ER};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

pub const MAX_INPUT_BYTES: usize = 65536;
pub const MAX_TARGETS: usize = 5;
pub type Result<T> = std::result::Result<T, String>;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EncodedTarget {
    pub field: String,
    pub model: String,
    pub coordinates: Option<[K; 2]>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub schema: String,
    pub q: u64,
    pub targets: Vec<EncodedTarget>,
}

fn er(k: K) -> ER {
    let mut a = [0; 16];
    a[..3].copy_from_slice(&k);
    a
}

fn digest(v: &Value) -> String {
    ghs_original_engines::digest::sha256(&serde_json::to_vec(v).unwrap())
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}

pub fn encode_point(p: EP) -> Option<[K; 2]> {
    match p {
        EP::Inf => None,
        EP::A(x, y) => Some([x, y]),
    }
}

pub struct CheckedInstance {
    pub inst: Inst,
    pub independent_field: FpR,
    pub independent_curve: Curve<ER>,
    pub short_shift: K,
    pub field_tag: String,
    pub model_tag: String,
    pub order_certificate: Value,
}

impl CheckedInstance {
    pub fn construct() -> Result<Self> {
        let inst = Inst::search(223, 1, 200000).ok_or("frozen original constructor exhausted")?;
        let kf = &inst.kf;
        let modulus = [223 - kf.c, 0, 0, 1];
        // ORIGINAL Rabin irreducibility checker, including the actual basis.
        let independent_field = FpR::from_modulus(223, &modulus);
        let f = &independent_field;
        let inv3 = f.inv(f.from_u64(3));
        let b2 = er(inst.ec.a2);
        let b4 = er(inst.ec.a4);
        let b6 = er(inst.ec.a6);
        let shift = f.mul(b2, inv3);
        let a = f.sub(b4, f.mul(f.mul(b2, b2), inv3));
        let b = f.add(
            f.sub(b6, f.mul(f.mul(b2, b4), inv3)),
            f.mul(
                f.mul(f.from_u64(2), f.mul(f.mul(b2, b2), b2)),
                f.inv(f.from_u64(27)),
            ),
        );
        if !curve::is_smooth(f, &Curve::new(a, b)) {
            return Err("independent original engine rejects singular source".into());
        }
        if !isogeny_algos::field::is_prime(inst.ell) || inst.ell <= 4 {
            return Err("independent original prime-order checker rejects".into());
        }
        if inst.g == EP::Inf || !inst.ec.on(&inst.g) {
            return Err("invalid original generator".into());
        }
        let mut short_shift = [0; 3];
        short_shift.copy_from_slice(&shift[..3]);
        let generator = match inst.g {
            EP::Inf => Pt::Inf,
            EP::A(x, y) => Pt::Aff(f.add(er(x), shift), er(y)),
        };
        let independent_curve = Curve::new(a, b);
        if !curve::on_curve(f, &independent_curve, &generator)
            || curve::pmul(f, &independent_curve, &generator, inst.ell as u128) != Pt::Inf
        {
            return Err("independent original generator/order check rejects".into());
        }
        let size = 223_u128.pow(3);
        let radius = ghs_original_engines::cover::isqrt_u128(4 * size);
        let (lower, upper) = (size + 1 - radius, size + 1 + radius);
        let first = lower.div_ceil(inst.ell as u128);
        let last = upper / inst.ell as u128;
        if first != last || first * inst.ell as u128 != inst.order || first != 4 {
            return Err("exact Hasse interval does not certify original order4ell".into());
        }
        // With #E=4ell and ell>4, the ell-Sylow subgroup has order ell.
        // Thus ellQ=O plus on-curve membership identifies <G>, not rank-two torsion.
        let order_certificate = json!({
            "field_size":size,"Hasse_radius_floor_2sqrt":radius,
            "Hasse_lower":lower,"Hasse_upper":upper,"ell":inst.ell,
            "unique_Hasse_multiple":first,"certified_order":inst.order,
            "prime_checker":"original isogeny_algos::field::is_prime",
            "nonzero_G_and_ellG_zero":"original independent FpR/curve engine",
            "scope":"native certificate plus written Hasse/Lagrange argument;unsigned"
        });
        let field_tag = format!("K3-223-{}", digest(&json!(modulus)));
        let model_tag = format!(
            "N4-E0-quadratic-v1-{}",
            digest(&json!({
                "q":223,"a2":inst.ec.a2,"a4":inst.ec.a4,"a6":inst.ec.a6,
                "quartic":inst.f,"generator":encode_point(inst.g),"ell":inst.ell,
                "order":inst.order,"constructor_seed":1
            }))
        );
        let checked = Self {
            inst,
            independent_field,
            independent_curve,
            short_shift,
            field_tag,
            model_tag,
            order_certificate,
        };
        checked.check_field_basis()?;
        Ok(checked)
    }

    pub fn check_field_basis(&self) -> Result<()> {
        let f = &self.independent_field;
        let kf = &self.inst.kf;
        let basis = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
        for a in basis {
            if er(kf.frob(&a)) != f.pow(er(a), 223) {
                return Err("basis Frobenius identity failed".into());
            }
            for b in basis {
                if er(kf.mul(&a, &b)) != f.mul(er(a), er(b)) {
                    return Err("basis product identity failed".into());
                }
            }
        }
        Ok(())
    }

    fn independent_point(&self, p: EP) -> Pt<ER> {
        match p {
            EP::Inf => Pt::Inf,
            EP::A(x, y) => Pt::Aff(
                self.independent_field.add(er(x), er(self.short_shift)),
                er(y),
            ),
        }
    }

    pub fn verify_recovered(&self, target: EP, k: u64) -> bool {
        let f = &self.independent_field;
        let c = &self.independent_curve;
        k < self.inst.ell
            && curve::on_curve(f, c, &self.independent_point(target))
            && curve::pmul(f, c, &self.independent_point(self.inst.g), k as u128)
                == self.independent_point(target)
    }

    pub fn encode(&self, p: EP) -> EncodedTarget {
        EncodedTarget {
            field: self.field_tag.clone(),
            model: self.model_tag.clone(),
            coordinates: encode_point(p),
        }
    }

    pub fn parse(&self, input: &[u8]) -> Result<Vec<EP>> {
        if input.len() > MAX_INPUT_BYTES {
            return Err("input exceeds65536 bytes".into());
        }
        let request: Request = serde_json::from_slice(input).map_err(|e| e.to_string())?;
        if request.schema != "chained-n4-public-target/v1" || request.q != 223 {
            return Err("wrong schema or fixed field".into());
        }
        if request.targets.is_empty() || request.targets.len() > MAX_TARGETS {
            return Err("expected one to five targets".into());
        }
        request
            .targets
            .into_iter()
            .map(|encoded| {
                if encoded.field != self.field_tag || encoded.model != self.model_tag {
                    return Err("field/model tag mismatch".into());
                }
                let point = match encoded.coordinates {
                    None => EP::Inf,
                    Some([x, y]) => {
                        if x.iter().chain(&y).any(|&v| v >= 223) {
                            return Err("noncanonical field coefficient".into());
                        }
                        EP::A(x, y)
                    }
                };
                let f = &self.independent_field;
                let c = &self.independent_curve;
                if !curve::on_curve(f, c, &self.independent_point(point)) {
                    return Err("off-curve public target".into());
                }
                if curve::pmul(f, c, &self.independent_point(point), self.inst.ell as u128)
                    != Pt::Inf
                {
                    return Err("target outside certified unique order-ell subgroup".into());
                }
                Ok(point)
            })
            .collect()
    }

    pub fn description(&self) -> Value {
        let f = &self.independent_field;
        let j = curve::jinv(f, &self.independent_curve);
        json!({"schema":"chained-n4-public-instance/v1","q":223,"seed":1,
            "field":self.field_tag,"model":self.model_tag,
            "modulus":[223-self.inst.kf.c,0,0,1],
            "quadratic_source":{"a2":self.inst.ec.a2,"a4":self.inst.ec.a4,"a6":self.inst.ec.a6},
            "short_source":{"a":self.independent_curve.a,"b":self.independent_curve.b,"x_shift":self.short_shift},
            "quartic":self.inst.f,"u":self.inst.u,"constructor_tries":self.inst.tries,
            "G":encode_point(self.inst.g),"ell":self.inst.ell,"order":self.inst.order,
            "order_certificate":self.order_certificate,"j":j,"j_in_prime_field":f.pow(j,223)==j,
            "candidate_id":null,"scope":"bounded correctness fixture;no timing/advantage verdict"})
    }
}

pub fn frozen_params(c: f64) -> public_solver::Params {
    public_solver::Params {
        nfb: (c * 223_f64.sqrt()).ceil() as usize,
        rows_mult: 1.2,
        max_desc: 100000,
        sge: false,
        maxw: 12,
        lp2: true,
    }
}

fn report_json(rep: &public_solver::Report) -> Value {
    let phases: Vec<_> = rep
        .phases
        .iter()
        .map(|(name, cnt, wall)| {
            json!({
                "phase":name,"mul":cnt.mul,"inv":cnt.inv,"add":cnt.add,
                "lmul":cnt.lmul,"ladd":cnt.ladd,"hash":cnt.hash,"cmp":cnt.cmp,"wall":wall
            })
        })
        .collect();
    json!({"ok":rep.ok,"fail":rep.fail,"k_found":rep.k_found,
        "phases":phases,"stats":rep.stats,"scope":"original correctness counters;no cost ratio"})
}

pub fn solve_one(checked: &CheckedInstance, target: EP) -> Value {
    let mut attempts = Vec::new();
    let mut c = 2.0;
    for attempt in 1..=6 {
        let params = frozen_params(c);
        let rep =
            public_solver::ic_solve_target(&checked.inst, &params, target, 100 + attempt, true);
        let independently_checked = rep
            .k_found
            .is_some_and(|k| checked.verify_recovered(target, k));
        let accepted = rep.ok && independently_checked;
        attempts.push(json!({"attempt":attempt,"c":c,"nfb":params.nfb,
            "original":report_json(&rep),"independent_original_source_check":independently_checked}));
        if accepted {
            return json!({"ok":true,"k_found":rep.k_found,"attempts":attempts});
        }
        if rep.ok && !independently_checked {
            return json!({"ok":false,"fail":"original solver success rejected by independent original engine","attempts":attempts});
        }
        c += 0.4;
    }
    json!({"ok":false,"fail":"frozen six-attempt B2 cap exhausted","attempts":attempts})
}

pub fn solve_public(checked: &CheckedInstance, input: &[u8]) -> Result<Value> {
    let targets = checked.parse(input)?;
    let results: Vec<_> = targets
        .into_iter()
        .map(|target| solve_one(checked, target))
        .collect();
    Ok(json!({"schema":"chained-n4-public-result/v1","q":223,
        "field":checked.field_tag,"model":checked.model_tag,
        "ok":results.iter().all(|v|v["ok"]==true),"results":results,
        "scope":"public-Q IC;all retries retained;independent original source checks;no benchmark"}))
}

#[cfg(test)]
mod tests;
