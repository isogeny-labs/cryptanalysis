//! Complete fixed-model F101 rational C0/T20 adapters through actual norms.
//! Global degree196 chain equality is via the accepted norm diagram/injectivity.
use balanced_source_engine::{Coordinates, Divisor, Model};
use chained_t20_prime_norm_checker::{Maps as T20Maps, Pair};
use elliptic_chain_engine::Alpha49;
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
pub const MAX_BYTES: usize = 1_048_576;
const C0: [u64; 7] = [56, 0, 13, 0, 6, 0, 1];

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Cover {
    pub component: String,
    pub a: u64,
    pub b: u64,
    pub order: u64,
    pub n: Vec<u64>,
    pub q: Vec<u64>,
    pub m: Vec<u64>,
    pub infinity: Option<[u64; 2]>,
}
impl Cover {
    pub fn curve(&self) -> Curve<u64> {
        Curve::new(self.a, self.b)
    }
    pub fn infinity_point(&self) -> Pt<u64> {
        self.infinity.map_or(Pt::Inf, |[x, y]| Pt::Aff(x, y))
    }
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct AlphaTag {
    pub source: [u64; 2],
    pub middle: [u64; 2],
    pub target: [u64; 2],
    pub order: u64,
    pub degree: u64,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Fixture {
    pub schema: String,
    pub field: u64,
    pub source: [u64; 7],
    pub jacobian_order: u64,
    pub covers: [Cover; 2],
    pub alpha49: AlphaTag,
    pub t20_fixture_sha256: String,
    pub global_chain_degree: u64,
    pub forward_halves: [u64; 2],
    pub inverse_components: [u64; 2],
    pub inverse_norm_components: [u64; 2],
}

// Trait access only:all field arithmetic delegates to the existing Zp engine.
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

pub struct Maps {
    fixture: Fixture,
    field: Zp,
    source: Model,
    t20: T20Maps,
    alpha: Alpha49,
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
        if bytes.len() > MAX_BYTES {
            return Err("fixture exceeds1MiB".into());
        }
        let fixture: Fixture = serde_json::from_slice(bytes).map_err(|e| e.to_string())?;
        if fixture.schema != "chained-f101-c0-t20/v1"
            || fixture.field != 101
            || fixture.source != C0
            || fixture.jacobian_order != 12317
            || fixture.global_chain_degree != 196
        {
            return Err("wrong fixed schema/field/source/order/chain tag".into());
        }
        if fixture.forward_halves != [55, 57]
            || fixture.inverse_components != [104, 85]
            || fixture.inverse_norm_components != [99, 57]
        {
            return Err("wrong public component normalization".into());
        }
        let a = &fixture.alpha49;
        if a.source != [1, 46]
            || a.middle != [26, 58]
            || a.target != [59, 27]
            || a.order != 109
            || a.degree != 49
        {
            return Err("wrong fixed alpha49 route/tag".into());
        }
        let actual_hash = hex::encode(balanced_source_engine::sha256_native::sha256(
            include_bytes!("../../norm-checker/fixtures/t20-norms.json"),
        ));
        if fixture.t20_fixture_sha256 != actual_hash {
            return Err("wrong old T20 fixture digest".into());
        }
        let field = Zp::new(101);
        for (i, c) in fixture.covers.iter().enumerate() {
            let expected = if i == 0 {
                ("E0", 1, 46, 109, vec![2, 0, 1], vec![1], vec![1], None)
            } else {
                (
                    "F0",
                    44,
                    21,
                    113,
                    vec![56, 0, 38],
                    vec![0, 1],
                    vec![56],
                    Some([38, 56]),
                )
            };
            if (
                c.component.as_str(),
                c.a,
                c.b,
                c.order,
                &c.n,
                &c.q,
                &c.m,
                c.infinity,
            ) != (
                expected.0,
                expected.1,
                expected.2,
                expected.3,
                &expected.4,
                &expected.5,
                &expected.6,
                expected.7,
            ) {
                return Err("wrong fixed C0 cover coefficients/target/anchor".into());
            }
            if c.n.iter().chain(&c.q).chain(&c.m).any(|&x| x >= 101)
                || c.q.last() != Some(&1)
                || poly::gcd(&field, &c.n, &c.q) != vec![1]
                || poly::gcd(&field, &c.q, &poly::derivative(&field, &c.q)) != vec![1]
            {
                return Err("noncanonical/noncoprime C0 coordinate".into());
            }
            let q2 = poly::mul(&field, &c.q, &c.q);
            let q4 = poly::mul(&field, &q2, &q2);
            let q6 = poly::mul(&field, &q4, &q2);
            let rhs = poly::add(
                &field,
                &poly::mul(&field, &poly::mul(&field, &c.n, &c.n), &c.n),
                &poly::add(
                    &field,
                    &poly::scale(&field, &poly::mul(&field, &c.n, &q4), c.a),
                    &poly::scale(&field, &q6, c.b),
                ),
            );
            if poly::mul(
                &field,
                &fixture.source.to_vec(),
                &poly::mul(&field, &c.m, &c.m),
            ) != rhs
                || !curve::is_smooth(&field, &c.curve())
                || !curve::on_curve(&field, &c.curve(), &c.infinity_point())
                || original_points::points(&field, &c.curve()).len() as u64 != c.order
            {
                return Err("C0 cleared equation/target count/anchor failed".into());
            }
        }
        for [a, b] in [fixture.alpha49.middle, fixture.alpha49.target] {
            if original_points::points(&field, &Curve::new(a, b)).len() != 109 {
                return Err("alpha49 curve point count failed".into());
            }
        }
        let source = Model::new(&fixture.source)?;
        let t20 = chained_t20_prime_norm_checker::pinned()?;
        let alpha = Alpha49::new()?;
        Ok(Self {
            fixture,
            field,
            source,
            t20,
            alpha,
        })
    }
    pub fn fixture(&self) -> &Fixture {
        &self.fixture
    }
    pub fn field(&self) -> &Zp {
        &self.field
    }
    pub fn source(&self) -> &Model {
        &self.source
    }
    pub fn target(&self) -> &Model {
        self.t20.model()
    }
    pub fn t20(&self) -> &T20Maps {
        &self.t20
    }
    pub fn alpha(&self) -> &Alpha49 {
        &self.alpha
    }
    pub fn points(&self, component: usize) -> Result<Vec<Pt<u64>>> {
        let c = self.cover(component)?;
        Ok(original_points::points(&self.field, &c.curve()))
    }
    fn cover(&self, component: usize) -> Result<&Cover> {
        self.fixture
            .covers
            .get(component)
            .ok_or_else(|| "bad C0 component tag".into())
    }
    fn admit_point(&self, component: usize, point: &Pt<u64>) -> Result<&Cover> {
        let c = self.cover(component)?;
        if let Pt::Aff(x, y) = *point {
            if x >= 101 || y >= 101 || !curve::on_curve(&self.field, &c.curve(), point) {
                return Err("noncanonical/off-curve C0 elliptic input".into());
            }
        }
        Ok(c)
    }
    pub fn source_pair_add(&self, a: &Pair, b: &Pair) -> Pair {
        std::array::from_fn(|i| {
            curve::padd(&self.field, &self.fixture.covers[i].curve(), &a[i], &b[i])
        })
    }
    pub fn source_pair_scale(&self, a: &Pair, k: [u64; 2]) -> Pair {
        std::array::from_fn(|i| {
            curve::pmul(
                &self.field,
                &self.fixture.covers[i].curve(),
                &a[i],
                k[i] as u128,
            )
        })
    }
    pub fn source_norm_coordinates(&self, c: &Coordinates) -> Result<Pair> {
        self.source_norm(&self.source.from_coordinates(c)?)
    }
    pub fn source_norm(&self, input: &Divisor) -> Result<Pair> {
        let c = self.source.coordinates(input)?;
        Ok([self.norm_component(&c, 0)?, self.norm_component(&c, 1)?])
    }
    fn norm_component(&self, input: &Coordinates, component: usize) -> Result<Pt<u64>> {
        let f = &self.field;
        let c = self.cover(component)?;
        let degree = input.u.len() - 1;
        let q2 = poly::mul(f, &c.q, &c.q);
        let poles = poly::gcd(f, &input.u, &q2);
        let (u, r) = poly::divrem(f, &input.u, &poles);
        if !r.is_empty() {
            return Err("nonexact C0 pole removal".into());
        }
        let coefficient = |p: &[u64], i: usize| p.get(i).copied().unwrap_or(0);
        let image = if u.len() == 1 {
            Pt::Inf
        } else {
            let q3 = poly::mul(f, &q2, &c.q);
            let xi = poly::invmod(f, &q2, &u).ok_or("remaining C0 X pole")?;
            let yi = poly::invmod(f, &q3, &u).ok_or("remaining C0 Y pole")?;
            let x = poly::mulmod(f, &c.n, &xi, &u);
            let y = poly::mulmod(f, &poly::mul(f, &input.v, &c.m), &yi, &u);
            let (a, b, cy, d) = (
                coefficient(&x, 0),
                coefficient(&x, 1),
                coefficient(&y, 0),
                coefficient(&y, 1),
            );
            if u.len() == 2 {
                Pt::Aff(a, cy)
            } else if b == 0 && d == 0 {
                curve::pmul(f, &c.curve(), &Pt::Aff(a, cy), 2)
            } else if b == 0 {
                if f.add(cy, cy) != f.mul(u[1], d) {
                    return Err("C0 opposite-image relation failed".into());
                }
                Pt::Inf
            } else {
                let slope = f.div(d, b);
                let divisor = original_cantor::Div {
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
                        &poly::constant(f, f.sub(cy, f.mul(slope, a))),
                        &vec![0, slope],
                    ),
                };
                let adapter = PrimeAdapter(*f);
                let genus1 = original_cantor::Hyp {
                    f: &adapter,
                    h: vec![c.b, c.a, 0, 1],
                    g: 1,
                };
                if !genus1.is_valid(&divisor) {
                    return Err("C0 image Mumford relation failed".into());
                }
                let reduced = genus1.reduce(divisor);
                if !genus1.is_valid(&reduced) {
                    return Err("C0 genus1 reduction failed".into());
                }
                if genus1.is_identity(&reduced) {
                    Pt::Inf
                } else {
                    Pt::Aff(f.neg(reduced.u[0]), coefficient(&reduced.v, 0))
                }
            }
        };
        let k = 2 * i64::from(input.plus) + degree as i64 - 2;
        let mut correction =
            curve::pmul(f, &c.curve(), &c.infinity_point(), k.unsigned_abs() as u128);
        if k < 0 {
            correction = curve::neg(f, &correction);
        }
        let out = curve::padd(f, &c.curve(), &image, &correction);
        if !curve::on_curve(f, &c.curve(), &out) {
            return Err("C0 norm off target".into());
        }
        Ok(out)
    }
    pub fn fibre(&self, component: usize, point: &Pt<u64>) -> Result<Option<Fibre>> {
        let c = self.admit_point(component, point)?;
        let Pt::Aff(x, y) = *point else {
            return Ok(None);
        };
        if y == 0 {
            return Err("fixed odd C0 target groups have no nonzero rational two-torsion".into());
        }
        let f = &self.field;
        let q2 = poly::mul(f, &c.q, &c.q);
        let raw = poly::sub(f, &c.n, &poly::scale(f, &q2, x));
        if raw.is_empty() || raw.len() > 3 {
            return Err("bad degree2 finite fibre".into());
        }
        let u = poly::monic(f, &raw);
        let inverse = poly::invmod(f, &c.m, &u).ok_or("nonunit C0 fibre ordinate")?;
        let v = poly::mulmod(
            f,
            &poly::scale(f, &poly::mul(f, &q2, &c.q), y),
            &inverse,
            &u,
        );
        if !poly::rem(
            f,
            &poly::sub(f, &poly::mul(f, &v, &v), &self.fixture.source.to_vec()),
            &u,
        )
        .is_empty()
        {
            return Err("whole C0 finite fibre off source".into());
        }
        let delta = 3 - u.len();
        let (infinity_plus, infinity_minus) = if delta == 0 {
            (0, 0)
        } else {
            let [ix, iy] = c.infinity.ok_or("C0 drop with infinity mapped toO")?;
            if x != ix {
                return Err("C0 degree drop outside infinity image".into());
            }
            if y == iy {
                (delta, 0)
            } else if y == f.neg(iy) {
                (0, delta)
            } else {
                return Err("wrong C0 infinity sign".into());
            }
        };
        Ok(Some(Fibre {
            u,
            v,
            infinity_plus,
            infinity_minus,
        }))
    }
    pub fn source_pull_component(&self, component: usize, point: &Pt<u64>) -> Result<Divisor> {
        match self.fibre(component, point)? {
            None => Ok(self.source.identity()),
            Some(fibre) => self
                .source
                .reduce_fibre(&fibre.u, &fibre.v, fibre.infinity_plus as i64),
        }
    }
    pub fn source_pull(&self, points: &Pair) -> Result<Divisor> {
        self.source.add(
            &self.source_pull_component(0, &points[0])?,
            &self.source_pull_component(1, &points[1])?,
        )
    }
    pub fn source_recover(&self, points: &Pair) -> Result<Divisor> {
        self.source.mul(&self.source_pull(points)?, 6159)
    }
    pub fn source_recover_components(&self, points: &Pair) -> Result<Divisor> {
        self.source_pull(&self.source_pair_scale(points, [55, 57]))
    }
    pub fn chain_norm_image(&self, input: &Divisor) -> Result<Pair> {
        let n = self.source_norm(input)?;
        let image = [self.alpha.forward(&n[0])?, n[1]];
        Ok(self.t20.scale_pair(&image, [2, 2]))
    }
    pub fn forward(&self, input: &Divisor) -> Result<Divisor> {
        let n = self.source_norm(input)?;
        let image = [self.alpha.forward(&n[0])?, n[1]];
        self.t20.pull(&self.t20.scale_pair(&image, [55, 57]))
    }
    pub fn forward_alternative(&self, input: &Divisor) -> Result<Divisor> {
        self.t20.recover(&self.chain_norm_image(input)?)
    }
    pub fn inverse(&self, input: &Divisor) -> Result<Divisor> {
        let n = self.t20.norm(input)?;
        let image = [self.alpha.reverse(&n[0])?, n[1]];
        self.source_pull(&self.source_pair_scale(&image, [104, 85]))
    }
    pub fn inverse_alternative(&self, input: &Divisor) -> Result<Divisor> {
        let n = self.t20.norm(input)?;
        let image = [self.alpha.reverse(&n[0])?, n[1]];
        self.source_recover(&self.source_pair_scale(&image, [99, 57]))
    }
}
pub fn pinned() -> Result<Maps> {
    Maps::load(include_bytes!("../fixtures/c0-t20.json"))
}

#[cfg(test)]
mod tests;
