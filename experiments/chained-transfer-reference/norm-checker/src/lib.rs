//! Independent fixed-model F101 norm and completed pullback adapters.
//! Runtime maps use only the existing prime-field, polynomial and divisor engines.
use balanced_source_engine::{Coordinates, Divisor, Model};
use isogeny_algos::curve::{self, Curve, Pt};
use isogeny_algos::field::{Field, Zp};
use isogeny_algos::poly;
use serde::{Deserialize, Serialize};

#[allow(dead_code)]
#[path = "../../../../../crypto/research/chained_jacobian_transfers_20261110/successor-preflight/src/legacy_jacobian.rs"]
mod original_cantor;
#[path = "../../src/quartic_pullback_points.rs"]
mod original_points;

pub type Result<T> = std::result::Result<T, String>;
pub type Pair = [Pt<u64>; 2];
pub const MAX_FIXTURE_BYTES: usize = 1_048_576;
const SOURCE: [u64; 7] = [100, 12, 74, 50, 6, 46, 1];
const RAW_SOURCE: [u64; 7] = [25, 3, 69, 63, 52, 62, 76];

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Target {
    pub component: String,
    pub a: u64,
    pub b: u64,
    pub order: u64,
    pub q: Vec<u64>,
    pub n: Vec<u64>,
    pub m: Vec<u64>,
    pub infinity: [u64; 2],
}
impl Target {
    pub fn curve(&self) -> Curve<u64> {
        Curve::new(self.a, self.b)
    }
    pub fn infinity_point(&self) -> Pt<u64> {
        Pt::Aff(self.infinity[0], self.infinity[1])
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Fixture {
    pub schema: String,
    pub field: u64,
    pub raw_source: [u64; 7],
    pub monic_source: [u64; 7],
    pub raw_y_scale: u64,
    pub targets: [Target; 2],
}

// An access adapter, not a second field implementation.
struct PrimeAdapter(Zp);
impl original_cantor::Fld for PrimeAdapter {
    type E = u64;
    fn zero(&self) -> u64 {
        self.0.zero()
    }
    fn one(&self) -> u64 {
        self.0.one()
    }
    fn add(&self, a: &u64, b: &u64) -> u64 {
        self.0.add(*a, *b)
    }
    fn sub(&self, a: &u64, b: &u64) -> u64 {
        self.0.sub(*a, *b)
    }
    fn neg(&self, a: &u64) -> u64 {
        self.0.neg(*a)
    }
    fn mul(&self, a: &u64, b: &u64) -> u64 {
        self.0.mul(*a, *b)
    }
    fn inv(&self, a: &u64) -> u64 {
        self.0.inv(*a)
    }
}

#[derive(Clone)]
pub struct Maps {
    fixture: Fixture,
    field: Zp,
    model: Model,
}

#[derive(Clone, Debug, Serialize)]
pub struct Fibre {
    pub u: Vec<u64>,
    pub v: Vec<u64>,
    pub infinity_plus: usize,
    pub infinity_minus: usize,
}

impl Maps {
    pub fn load(bytes: &[u8]) -> Result<Self> {
        if bytes.len() > MAX_FIXTURE_BYTES {
            return Err("fixture exceeds 1MiB".into());
        }
        let fixture: Fixture = serde_json::from_slice(bytes).map_err(|e| e.to_string())?;
        if fixture.schema != "chained-t20-prime-norm/v1"
            || fixture.field != 101
            || fixture.raw_source != RAW_SOURCE
            || fixture.monic_source != SOURCE
            || fixture.raw_y_scale != 50
        {
            return Err("wrong fixed source/field/schema/ordinate normalization".into());
        }
        let field = Zp::new(101);
        let source = fixture.monic_source.to_vec();
        if poly::scale(&field, &source, field.sq(fixture.raw_y_scale)) != fixture.raw_source {
            return Err("raw/monic source mismatch".into());
        }
        for (i, t) in fixture.targets.iter().enumerate() {
            let (name, a, b, order, anchor) = if i == 0 {
                ("E2", 59, 27, 109, [10, 100])
            } else {
                ("F0", 44, 21, 113, [71, 48])
            };
            if t.component != name || (t.a, t.b, t.order, t.infinity) != (a, b, order, anchor) {
                return Err("wrong fixed target/order/infinity tag".into());
            }
            for (p, len) in [(&t.q, 3), (&t.n, 5), (&t.m, 4)] {
                if p.len() != len || p.last() == Some(&0) || p.iter().any(|&c| c >= 101) {
                    return Err("noncanonical or overlong cover polynomial".into());
                }
            }
            if t.q[2] != 1
                || poly::gcd(&field, &t.n, &t.q) != vec![1]
                || poly::gcd(&field, &t.q, &poly::derivative(&field, &t.q)) != vec![1]
            {
                return Err("nonmonic/repeated pole or noncoprime coordinate".into());
            }
            let q2 = poly::mul(&field, &t.q, &t.q);
            let q4 = poly::mul(&field, &q2, &q2);
            let q6 = poly::mul(&field, &q4, &q2);
            let n3 = poly::mul(&field, &poly::mul(&field, &t.n, &t.n), &t.n);
            let rhs = poly::add(
                &field,
                &n3,
                &poly::add(
                    &field,
                    &poly::scale(&field, &poly::mul(&field, &t.n, &q4), t.a),
                    &poly::scale(&field, &q6, t.b),
                ),
            );
            let lhs = poly::mul(&field, &source, &poly::mul(&field, &t.m, &t.m));
            if lhs != rhs
                || t.infinity != [t.n[4], t.m[3]]
                || !curve::is_smooth(&field, &t.curve())
                || !curve::on_curve(&field, &t.curve(), &t.infinity_point())
                || original_points::points(&field, &t.curve()).len() as u64 != t.order
            {
                return Err("cover equation/degree4 anchor/target count failed".into());
            }
        }
        let model = Model::new(&fixture.monic_source)?;
        Ok(Self {
            fixture,
            field,
            model,
        })
    }

    pub fn model(&self) -> &Model {
        &self.model
    }
    pub fn field(&self) -> &Zp {
        &self.field
    }
    pub fn fixture(&self) -> &Fixture {
        &self.fixture
    }
    pub fn target_points(&self, component: usize) -> Result<Vec<Pt<u64>>> {
        let t = self.target(component)?;
        Ok(original_points::points(&self.field, &t.curve()))
    }
    fn target(&self, component: usize) -> Result<&Target> {
        self.fixture
            .targets
            .get(component)
            .ok_or_else(|| "bad component tag".into())
    }
    fn admit_point(&self, component: usize, point: &Pt<u64>) -> Result<&Target> {
        let t = self.target(component)?;
        if let Pt::Aff(x, y) = *point {
            if x >= 101 || y >= 101 || !curve::on_curve(&self.field, &t.curve(), point) {
                return Err("noncanonical/off-curve elliptic input".into());
            }
        }
        Ok(t)
    }
    pub fn add_pairs(&self, a: &Pair, b: &Pair) -> Pair {
        std::array::from_fn(|i| {
            curve::padd(&self.field, &self.fixture.targets[i].curve(), &a[i], &b[i])
        })
    }
    pub fn scale_pair(&self, a: &Pair, scalars: [u64; 2]) -> Pair {
        std::array::from_fn(|i| {
            curve::pmul(
                &self.field,
                &self.fixture.targets[i].curve(),
                &a[i],
                scalars[i] as u128,
            )
        })
    }

    /// Push forward a validated balanced class, without choosing support roots.
    pub fn norm(&self, input: &Divisor) -> Result<Pair> {
        let coordinates = self.model.coordinates(input)?;
        Ok([
            self.norm_component(&coordinates, 0)?,
            self.norm_component(&coordinates, 1)?,
        ])
    }
    pub fn norm_coordinates(&self, input: &Coordinates) -> Result<Pair> {
        self.norm(&self.model.from_coordinates(input)?)
    }
    fn norm_component(&self, input: &Coordinates, component: usize) -> Result<Pt<u64>> {
        let f = &self.field;
        let t = self.target(component)?;
        let original_degree = input.u.len() - 1;
        let q2 = poly::mul(f, &t.q, &t.q);
        // The square keeps the full multiplicity of all possible degree<=2 poles.
        let poles = poly::gcd(f, &input.u, &q2);
        let (u, remainder) = poly::divrem(f, &input.u, &poles);
        if !remainder.is_empty() {
            return Err("nonexact pole removal".into());
        }
        let mut image = Pt::Inf;
        if u.len() > 1 {
            let q3 = poly::mul(f, &q2, &t.q);
            let qi2 = poly::invmod(f, &q2, &u).ok_or("remaining X pole")?;
            let qi3 = poly::invmod(f, &q3, &u).ok_or("remaining Y pole")?;
            let x = poly::mulmod(f, &t.n, &qi2, &u);
            let y = poly::mulmod(f, &poly::mul(f, &input.v, &t.m), &qi3, &u);
            let coefficient = |p: &[u64], i: usize| p.get(i).copied().unwrap_or(0);
            let (a, b, c, d) = (
                coefficient(&x, 0),
                coefficient(&x, 1),
                coefficient(&y, 0),
                coefficient(&y, 1),
            );
            image = if u.len() == 2 {
                Pt::Aff(a, c)
            } else if b == 0 && d == 0 {
                curve::pmul(f, &t.curve(), &Pt::Aff(a, c), 2)
            } else if b == 0 {
                // Exact source relation forces the two ordinates to be opposite,
                // including the repeated-image two-torsion limit.
                if f.add(c, c) != f.mul(u[1], d) {
                    return Err("constant-X opposite-image relation failed".into());
                }
                Pt::Inf
            } else {
                let slope = f.div(d, b);
                let image_divisor = original_cantor::Div {
                    u: vec![
                        f.add(
                            f.sub(f.sq(a), f.mul(u[1], f.mul(a, b))),
                            f.mul(u[0], f.sq(b)),
                        ),
                        f.sub(f.mul(u[1], b), f.add(a, a)),
                        1,
                    ],
                    v: poly::add(
                        f,
                        &poly::constant(f, f.sub(c, f.mul(slope, a))),
                        &vec![0, slope],
                    ),
                };
                let adapter = PrimeAdapter(*f);
                let genus_one = original_cantor::Hyp {
                    f: &adapter,
                    h: vec![t.b, t.a, 0, 1],
                    g: 1,
                };
                if !genus_one.is_valid(&image_divisor) {
                    return Err("image Mumford relation failed".into());
                }
                let reduced = genus_one.reduce(image_divisor);
                if !genus_one.is_valid(&reduced) {
                    return Err("genus1 reduction failed".into());
                }
                if genus_one.is_identity(&reduced) {
                    Pt::Inf
                } else {
                    Pt::Aff(f.neg(reduced.u[0]), coefficient(&reduced.v, 0))
                }
            };
        }
        let infinity_coefficient = 2 * i64::from(input.plus) + original_degree as i64 - 2;
        let mut correction = curve::pmul(
            f,
            &t.curve(),
            &t.infinity_point(),
            infinity_coefficient.unsigned_abs() as u128,
        );
        if infinity_coefficient < 0 {
            correction = curve::neg(f, &correction);
        }
        let result = curve::padd(f, &t.curve(), &image, &correction);
        if !curve::on_curve(f, &t.curve(), &result) {
            return Err("norm image off curve".into());
        }
        Ok(result)
    }

    /// The finite scheme together with every missing infinity of a degree4 fibre.
    pub fn fibre(&self, component: usize, point: &Pt<u64>) -> Result<Option<Fibre>> {
        let t = self.admit_point(component, point)?;
        let Pt::Aff(x, y) = *point else {
            return Ok(None);
        };
        if y == 0 {
            return Err("unsupported rational two-torsion (fixed groups are odd)".into());
        }
        let f = &self.field;
        let q2 = poly::mul(f, &t.q, &t.q);
        let raw = poly::sub(f, &t.n, &poly::scale(f, &q2, x));
        if raw.len() < 2 || raw.len() > 5 {
            return Err("bad finite fibre degree".into());
        }
        let u = poly::monic(f, &raw);
        let inverse_m = poly::invmod(f, &t.m, &u).ok_or("nonunit fibre ordinate denominator")?;
        let v = poly::mulmod(
            f,
            &poly::scale(f, &poly::mul(f, &q2, &t.q), y),
            &inverse_m,
            &u,
        );
        if !poly::rem(
            f,
            &poly::sub(
                f,
                &poly::mul(f, &v, &v),
                &self.fixture.monic_source.to_vec(),
            ),
            &u,
        )
        .is_empty()
        {
            return Err("whole finite fibre is off source".into());
        }
        let delta = 5 - u.len();
        let (infinity_plus, infinity_minus) = if delta == 0 {
            (0, 0)
        } else {
            if x != t.infinity[0] {
                return Err("degree drop outside infinity fibre".into());
            }
            if y == t.infinity[1] {
                (delta, 0)
            } else if y == f.neg(t.infinity[1]) {
                (0, delta)
            } else {
                return Err("degree drop with wrong infinity sign".into());
            }
        };
        Ok(Some(Fibre {
            u,
            v,
            infinity_plus,
            infinity_minus,
        }))
    }
    pub fn pull_component(&self, component: usize, point: &Pt<u64>) -> Result<Divisor> {
        match self.fibre(component, point)? {
            None => Ok(self.model.identity()),
            Some(fibre) => {
                self.model
                    .reduce_fibre(&fibre.u, &fibre.v, fibre.infinity_plus as i64 - 1)
            }
        }
    }
    pub fn pull(&self, pair: &Pair) -> Result<Divisor> {
        self.model.add(
            &self.pull_component(0, &pair[0])?,
            &self.pull_component(1, &pair[1])?,
        )
    }
    pub fn recover(&self, pair: &Pair) -> Result<Divisor> {
        self.model.mul(&self.pull(pair)?, 9238)
    }
    pub fn recover_components(&self, pair: &Pair) -> Result<Divisor> {
        self.pull(&self.scale_pair(pair, [82, 85]))
    }
}

pub fn pinned() -> Result<Maps> {
    Maps::load(include_bytes!("../fixtures/t20-norms.json"))
}

#[cfg(test)]
mod tests;
