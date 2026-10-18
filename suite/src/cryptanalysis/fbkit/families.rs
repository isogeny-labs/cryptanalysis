//! Materialising a recipe into a point set / factor base (spec section 3).
//!
//! A [`Recipe`] names a family of the registry ([`super::registry`]), its
//! parameters and its modifiers (`name:k=v,k=v;mod=v`). [`materialize`] turns
//! it into a [`Materialized`] base on a [`Curve`], or explains why it cannot
//! ([`Reason::NotApplicable`] for a mathematical or regime mismatch,
//! [`Reason::Error`] for a failure).
//!
//! Every family reduces to one of two sinks:
//!
//! * **Koblitz curves** hand a set of abscissa representatives to
//!   `build_explicit_frobenius_orbit_factor_base`, which closes it under the
//!   Frobenius and folds the points into signed orbits. A seed subspace that is
//!   not Frobenius-invariant is therefore replaced by the union of its
//!   Frobenius images (recorded in the construction notes); the decomposition
//!   *system* still ranges over the seed subspace only.
//! * **Random binary curves** lift the abscissae directly; one column per
//!   abscissa.
//!
//! Field arithmetic is single-word (`n <= 62`, [`Gf2`]); only the `divisor`
//! family reaches larger `n`, through the existing divisor builder.
//! "Usable" follows the cofactor-projection policy of the factor-base archive:
//! a point is usable when `[h]P != O`; `strict` points satisfy `[r]P = O`.

use std::collections::{BTreeMap, BTreeSet, HashSet};
use std::fmt;
use std::time::Instant;

use num_bigint::BigUint;
use num_traits::ToPrimitive;
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use crate::binary_ecc::F2mElement;
use crate::cryptanalysis::ic_boundary::{
    prime_factor_base, ArtinSchreier, BinaryInstance, PrimeInstance,
};
use crate::cryptanalysis::koblitz_factor_base_search::{
    greedy_prune, witness_list, FactorBaseSpec, TargetSet, Witness,
};
use crate::cryptanalysis::koblitz_fast::{FastCurve, FastPoint};
use crate::cryptanalysis::koblitz_index_calculus::{
    build_explicit_frobenius_orbit_factor_base, build_frobenius_union_factor_base,
    restrict_factor_base_to_orbits, saturate_factor_base_two_torsion, FrobeniusFactorBase,
    KoblitzCurve, PairSumTable,
};
use crate::cryptanalysis::semaev_decomp::Gf2;

use super::registry;

/// Largest abscissa set a family may hand to a sink.
pub const MAX_ABSCISSAE: usize = 1 << 22;
/// Largest field degree for which non-subspace families scan the field.
pub const MAX_ENUMERABLE_DEGREE: u32 = 26;
/// Largest field degree of the single-word arithmetic.
pub const MAX_WORD_DEGREE: u32 = 62;

// ── Recipes ────────────────────────────────────────────────────────

/// Modifiers that change the point set (spec 3.1).
pub const SET_MODIFIERS: [&str; 4] = ["trace_zero", "shift", "two_torsion", "frobenius_union"];
/// Modifiers that change the decomposition system (spec 3.4).
pub const SYSTEM_MODIFIERS: [&str; 5] = [
    "tau-twist",
    "per-summand-shift",
    "symmetry-breaking",
    "trace-constraint",
    "macaulay-implied",
];

/// A factor-base recipe: family, parameters and modifiers. Contains no
/// measurements and no run seed unless the user wrote one, so its canonical
/// JSON is a valid hash input.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Recipe {
    /// Registry name of the family.
    pub family: String,
    /// Parameters (`l`, `seed`, `indices`, ...); integers, strings, lists.
    #[serde(default)]
    pub params: BTreeMap<String, Value>,
    /// Modifiers (`trace_zero`, `shift`, `tau-twist`, ...).
    #[serde(default)]
    pub modifiers: BTreeMap<String, Value>,
}

/// The canonical spelling of a modifier key, or `None` when unknown.
pub fn canonical_modifier(key: &str) -> Option<&'static str> {
    let under = key.replace('-', "_");
    let hyph = key.replace('_', "-");
    SET_MODIFIERS
        .iter()
        .find(|m| **m == under)
        .or_else(|| SYSTEM_MODIFIERS.iter().find(|m| **m == hyph))
        .copied()
}

fn parse_value(raw: &str) -> Value {
    let raw = raw.trim();
    if raw.contains('+') && !raw.starts_with("0x") {
        return Value::Array(raw.split('+').map(parse_value).collect());
    }
    if let Ok(v) = raw.parse::<u64>() {
        return json!(v);
    }
    match raw {
        "true" => json!(1),
        "false" => json!(0),
        _ => Value::String(raw.to_string()),
    }
}

impl Recipe {
    /// A recipe with no parameters.
    pub fn new(family: &str) -> Self {
        Self {
            family: family.to_string(),
            params: BTreeMap::new(),
            modifiers: BTreeMap::new(),
        }
    }

    /// Builder: set a parameter.
    pub fn with(mut self, key: &str, value: impl Into<Value>) -> Self {
        self.params.insert(key.to_string(), value.into());
        self
    }

    /// Builder: set a modifier.
    pub fn with_modifier(mut self, key: &str, value: impl Into<Value>) -> Self {
        self.modifiers.insert(key.to_string(), value.into());
        self
    }

    /// Parse `name:k=v,k=v;mod=v;mod=v`. Integers stay integers, `a+b+c` is a
    /// list, `true/false` are `1/0`, anything else is a string. Unknown
    /// families, parameters and modifiers are rejected.
    pub fn parse(text: &str) -> Result<Self, String> {
        let (head, mods) = match text.split_once(';') {
            Some((h, m)) => (h, Some(m)),
            None => (text, None),
        };
        let (name, params) = match head.split_once(':') {
            Some((n, p)) => (n.trim(), Some(p)),
            None => (head.trim(), None),
        };
        let family = registry::find(name)
            .ok_or_else(|| format!("unknown family `{name}`; try `ca-ic fbkit list`"))?;
        let mut recipe = Recipe::new(family.name);
        for item in params
            .unwrap_or("")
            .split(',')
            .filter(|s| !s.trim().is_empty())
        {
            let (k, v) = item
                .split_once('=')
                .ok_or_else(|| format!("parameter `{item}` is not key=value"))?;
            let k = k.trim();
            let known = k == "seed"
                || k.starts_with("parent.")
                || family.parameters.iter().any(|p| p.name == k);
            if !known {
                return Err(format!(
                    "family `{}` has no parameter `{k}` (known: {})",
                    family.name,
                    family
                        .parameters
                        .iter()
                        .map(|p| p.name)
                        .collect::<Vec<_>>()
                        .join(", ")
                ));
            }
            recipe.params.insert(k.to_string(), parse_value(v));
        }
        for item in mods
            .unwrap_or("")
            .split([';', ','])
            .filter(|s| !s.trim().is_empty())
        {
            let (k, v) = item
                .split_once('=')
                .ok_or_else(|| format!("modifier `{item}` is not key=value"))?;
            let key = canonical_modifier(k.trim())
                .ok_or_else(|| format!("unknown modifier `{}`", k.trim()))?;
            recipe.modifiers.insert(key.to_string(), parse_value(v));
        }
        Ok(recipe)
    }

    /// The recipe as a JSON value (`family`, `params`, `modifiers`).
    pub fn to_value(&self) -> Value {
        json!({"family": self.family, "params": self.params, "modifiers": self.modifiers})
    }

    /// Compact sorted-key JSON: the hash input of the recipe.
    pub fn to_canonical_json(&self) -> String {
        self.to_value().to_string()
    }

    /// Integer parameter.
    pub fn param_u64(&self, key: &str) -> Option<u64> {
        self.params.get(key).and_then(Value::as_u64)
    }

    /// String parameter.
    pub fn param_str(&self, key: &str) -> Option<&str> {
        self.params.get(key).and_then(Value::as_str)
    }

    /// List-of-integers parameter; a lone integer is a one-element list.
    pub fn param_list(&self, key: &str) -> Option<Vec<u64>> {
        match self.params.get(key)? {
            Value::Array(a) => a.iter().map(Value::as_u64).collect(),
            v => v.as_u64().map(|x| vec![x]),
        }
    }

    /// A numeric or `0x..` hex parameter or modifier value.
    pub fn hex_or_int(v: &Value) -> Option<u64> {
        match v {
            Value::Number(n) => n.as_u64(),
            Value::String(s) => {
                let t = s.trim_start_matches("0x");
                u64::from_str_radix(t, 16).ok()
            }
            _ => None,
        }
    }

    /// Whether a modifier is present and not `0`.
    pub fn modifier_on(&self, key: &str) -> bool {
        match self.modifiers.get(key) {
            None => false,
            Some(Value::Number(n)) => n.as_u64() != Some(0),
            Some(Value::String(s)) => !s.is_empty() && s != "0",
            Some(_) => true,
        }
    }

    /// The seed this recipe asks for, else `default`.
    pub fn seed_or(&self, default: u64) -> u64 {
        self.param_u64("seed").unwrap_or(default)
    }

    /// The sub-recipe named by `parent=<family>` with `parent.<k>=v` parameters.
    pub fn parent(&self) -> Result<Recipe, Reason> {
        let name = self
            .param_str("parent")
            .ok_or_else(|| Reason::Error("missing parameter `parent`".into()))?;
        let mut sub = Recipe::new(name);
        for (k, v) in &self.params {
            if let Some(rest) = k.strip_prefix("parent.") {
                sub.params.insert(rest.to_string(), v.clone());
            }
        }
        if let Some(s) = self.params.get("seed") {
            sub.params.entry("seed".into()).or_insert_with(|| s.clone());
        }
        if registry::find(name).is_none() {
            return Err(Reason::Error(format!("unknown parent family `{name}`")));
        }
        Ok(sub)
    }

    /// The set modifiers present and on.
    pub fn set_modifiers(&self) -> BTreeMap<String, Value> {
        self.modifiers
            .iter()
            .filter(|(k, _)| SET_MODIFIERS.contains(&k.as_str()))
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect()
    }

    /// The system modifiers present.
    pub fn system_modifiers(&self) -> BTreeMap<String, Value> {
        self.modifiers
            .iter()
            .filter(|(k, _)| SYSTEM_MODIFIERS.contains(&k.as_str()))
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect()
    }

    /// The value of the family's size parameter (`l`, `K`, ...), if present.
    pub fn size(&self) -> Option<u64> {
        let name = registry::find(&self.family)?.size_param?;
        self.param_u64(name)
    }
}

/// Why a recipe produced no base.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Reason {
    /// The family does not apply to this curve or parameters (mathematics,
    /// regime or a documented cap); the cell is `not_applicable`.
    NotApplicable(String),
    /// Something failed; the cell is `error` and the sweep continues.
    Error(String),
}

impl fmt::Display for Reason {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Reason::NotApplicable(s) => write!(f, "not_applicable: {s}"),
            Reason::Error(s) => write!(f, "error: {s}"),
        }
    }
}

impl std::error::Error for Reason {}

fn na<T>(msg: impl Into<String>) -> Result<T, Reason> {
    Err(Reason::NotApplicable(msg.into()))
}

fn err<T>(msg: impl Into<String>) -> Result<T, Reason> {
    Err(Reason::Error(msg.into()))
}

// ── Curves ─────────────────────────────────────────────────────────

/// The curve a base is built on.
#[derive(Clone, Copy)]
pub enum Curve<'a> {
    /// A Koblitz (or subfield) curve with its Frobenius structure.
    Koblitz(&'a KoblitzCurve),
    /// A binary curve without Frobenius structure (random binary curve).
    Binary(&'a BinaryInstance),
    /// A prime-field curve.
    Prime(&'a PrimeInstance),
}

impl<'a> Curve<'a> {
    /// A binary instance as `Koblitz` when it carries a Koblitz curve.
    pub fn from_binary_instance(inst: &'a BinaryInstance) -> Self {
        match &inst.koblitz {
            Some(kc) => Curve::Koblitz(kc),
            None => Curve::Binary(inst),
        }
    }

    /// Regime label: `koblitz`, `binary` or `prime`.
    pub fn regime(&self) -> &'static str {
        match self {
            Curve::Koblitz(_) => "koblitz",
            Curve::Binary(_) => "binary",
            Curve::Prime(_) => "prime",
        }
    }

    /// Field degree for binary curves.
    pub fn degree(&self) -> Option<u32> {
        match self {
            Curve::Koblitz(kc) => Some(kc.n),
            Curve::Binary(i) => Some(i.n),
            Curve::Prime(_) => None,
        }
    }

    /// Prime-order subgroup order and cofactor when they fit a word.
    pub fn orders(&self) -> Option<(u64, u64)> {
        match self {
            Curve::Koblitz(kc) => Some((kc.subgroup_order.to_u64()?, kc.cofactor.to_u64()?)),
            Curve::Binary(i) => Some((i.r, i.cofactor)),
            Curve::Prime(i) => Some((i.r, i.cofactor)),
        }
    }
}

/// Single-word binary-curve context shared by the families and the metrics.
pub struct Ctx<'a> {
    /// Field degree.
    pub n: u32,
    /// Field arithmetic.
    pub gf: Gf2,
    /// Artin-Schreier solver and trace.
    pub ash: ArtinSchreier,
    /// Curve arithmetic.
    pub fast: FastCurve,
    /// Curve coefficient `a` (as a field word).
    pub a: u64,
    /// Curve coefficient `b`.
    pub b: u64,
    /// Prime subgroup order.
    pub r: u64,
    /// Cofactor.
    pub h: u64,
    /// Generator of the prime-order subgroup.
    pub generator: FastPoint,
    /// The Koblitz curve, when the regime is Koblitz.
    pub kc: Option<&'a KoblitzCurve>,
}

impl<'a> Ctx<'a> {
    /// Build the context; `NotApplicable` when the field does not fit a word.
    pub fn new(curve: &Curve<'a>) -> Result<Ctx<'a>, Reason> {
        match curve {
            Curve::Koblitz(kc) => {
                if kc.n > MAX_WORD_DEGREE {
                    return na(format!(
                        "n = {} exceeds the single-word field arithmetic (n <= {MAX_WORD_DEGREE})",
                        kc.n
                    ));
                }
                let fast = FastCurve::new(&kc.curve)
                    .ok_or_else(|| Reason::NotApplicable("no single-word curve".into()))?;
                let gf = Gf2::new(&kc.curve.irreducible);
                let ash = ArtinSchreier::new(&gf);
                let (r, h) = curve
                    .orders()
                    .ok_or_else(|| Reason::NotApplicable("subgroup order exceeds a word".into()))?;
                let generator = fast.lift(kc.generator());
                Ok(Ctx {
                    n: kc.n,
                    a: fast.a,
                    b: fast.b,
                    gf,
                    ash,
                    fast,
                    r,
                    h,
                    generator,
                    kc: Some(kc),
                })
            }
            Curve::Binary(i) => Ok(Ctx {
                n: i.n,
                gf: i.gf.clone(),
                ash: i.artin_schreier.clone(),
                fast: i.fast.clone(),
                a: i.a,
                b: i.b,
                r: i.r,
                h: i.cofactor,
                generator: i.generator,
                kc: None,
            }),
            Curve::Prime(_) => na("prime regime"),
        }
    }

    /// Both points above abscissa `x` (none when `Tr(x + a + b/x^2) = 1`).
    pub fn points_with_x(&self, x: u64) -> Vec<FastPoint> {
        let f = &self.gf;
        if x == 0 {
            return vec![FastPoint::affine(0, f.sqr_k(self.b, self.n - 1))];
        }
        let inv = f.inv(x);
        let c = x ^ self.a ^ f.mul(self.b, f.sqr(inv));
        match self.ash.solve(c) {
            Some(u) => {
                let p = FastPoint::affine(x, f.mul(x, u));
                vec![p, self.fast.neg(p)]
            }
            None => Vec::new(),
        }
    }

    /// `[k]P`.
    pub fn mul(&self, p: FastPoint, k: u64) -> FastPoint {
        self.fast.mul(p, &BigUint::from(k))
    }

    /// Absolute trace.
    pub fn trace(&self, v: u64) -> u64 {
        self.ash.trace(v)
    }

    /// `x^e` in the field.
    pub fn pow(&self, mut x: u64, mut e: u64) -> u64 {
        let mut acc = 1u64;
        while e > 0 {
            if e & 1 == 1 {
                acc = self.gf.mul(acc, x);
            }
            x = self.gf.sqr(x);
            e >>= 1;
        }
        acc
    }

    /// Field mask `2^n - 1`.
    pub fn mask(&self) -> u64 {
        if self.n >= 64 {
            u64::MAX
        } else {
            (1u64 << self.n) - 1
        }
    }
}

// ── F_2-linear algebra on words ────────────────────────────────────

/// Reduce `v` against an echelon list (each row has a distinct top bit).
fn reduce(rows: &[u64], mut v: u64) -> u64 {
    for &r in rows {
        let top = 63 - r.leading_zeros();
        if (v >> top) & 1 == 1 {
            v ^= r;
        }
    }
    v
}

/// Rank of a set of words.
pub fn rank(vectors: &[u64]) -> usize {
    let mut rows: Vec<u64> = Vec::new();
    for &v in vectors {
        let r = reduce(&rows, v);
        if r != 0 {
            rows.push(r);
            rows.sort_unstable_by_key(|x| std::cmp::Reverse(*x));
        }
    }
    rows.len()
}

/// The reduced row echelon form of a set of words (independent rows only).
pub fn rref(vectors: &[u64]) -> Vec<u64> {
    let mut rows: Vec<u64> = Vec::new();
    for &v in vectors {
        let r = reduce(&rows, v);
        if r != 0 {
            rows.push(r);
            rows.sort_unstable_by_key(|x| std::cmp::Reverse(*x));
        }
    }
    // Back-substitute so each pivot column is clear in the other rows.
    for i in 0..rows.len() {
        let top = 63 - rows[i].leading_zeros();
        for j in 0..rows.len() {
            if j != i && (rows[j] >> top) & 1 == 1 {
                rows[j] ^= rows[i];
            }
        }
    }
    rows.sort_unstable_by_key(|x| std::cmp::Reverse(*x));
    rows
}

/// All `2^l` elements of the span of `basis`, Gray-code order from 0.
pub fn span(basis: &[u64]) -> Vec<u64> {
    let mut out = Vec::with_capacity(1usize << basis.len());
    out.push(0u64);
    for &b in basis {
        let len = out.len();
        for i in 0..len {
            out.push(out[i] ^ b);
        }
    }
    out
}

/// Kernel of an `F_2`-linear map on `F_2^n`, as a basis.
fn kernel(n: u32, f: impl Fn(u64) -> u64) -> Vec<u64> {
    // Gaussian elimination tracking preimages.
    let mut rows: Vec<(u64, u64)> = Vec::new();
    let mut ker = Vec::new();
    for i in 0..n {
        let e = 1u64 << i;
        let (mut img, mut pre) = (f(e), e);
        for &(ri, rp) in &rows {
            let top = 63 - ri.leading_zeros();
            if (img >> top) & 1 == 1 {
                img ^= ri;
                pre ^= rp;
            }
        }
        if img == 0 {
            ker.push(pre);
        } else {
            rows.push((img, pre));
            rows.sort_unstable_by_key(|(a, _)| std::cmp::Reverse(*a));
        }
    }
    ker
}

fn splitmix(mut z: u64) -> u64 {
    z = z.wrapping_add(0x9e37_79b9_7f4a_7c15);
    z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    z ^ (z >> 31)
}

fn rng_for(seed: u64, tag: &str) -> StdRng {
    let mut h = 0xcbf2_9ce4_8422_2325u64;
    for b in tag.bytes() {
        h = (h ^ u64::from(b)).wrapping_mul(0x0100_0000_01b3);
    }
    StdRng::seed_from_u64(splitmix(seed ^ h))
}

fn random_nonzero(ctx: &Ctx, rng: &mut StdRng) -> u64 {
    loop {
        let v = rng.gen::<u64>() & ctx.mask();
        if v != 0 {
            return v;
        }
    }
}

fn random_independent(ctx: &Ctx, rng: &mut StdRng, l: usize) -> Vec<u64> {
    let mut basis: Vec<u64> = Vec::new();
    while basis.len() < l {
        let v = rng.gen::<u64>() & ctx.mask();
        basis.push(v);
        if rank(&basis) != basis.len() {
            basis.pop();
        }
    }
    basis
}

/// `dim span{b_i b_j : i <= j}`.
pub fn dim_v2(ctx: &Ctx, basis: &[u64]) -> usize {
    let mut prods = Vec::new();
    for i in 0..basis.len() {
        for j in i..basis.len() {
            prods.push(ctx.gf.mul(basis[i], basis[j]));
        }
    }
    rank(&prods)
}

// ── Plans and materialized bases ───────────────────────────────────

/// Construction metadata recorded with every base.
#[derive(Debug, Clone, Default, Serialize)]
pub struct Construction {
    /// Nominal dimension of the (seed) subspace; `None` for non-subspaces.
    pub dimension: Option<u32>,
    /// `dim V.V` (span of pairwise products of the basis).
    pub dim_v2: Option<u32>,
    /// `all_zero` when `Tr` vanishes on every abscissa, else `mixed`.
    pub trace_class: Option<String>,
    /// Sum of Hamming weights of the reduced echelon basis.
    pub basis_weight: Option<u32>,
    /// Abscissae in the final point set (after Frobenius closure).
    pub abscissae: usize,
    /// Abscissae a single decomposition summand ranges over in the system.
    pub pool_abscissae: Option<Vec<u64>>,
    /// Wall milliseconds spent building.
    pub build_ms: f64,
    /// Human-readable notes (closures applied, caps, proxies).
    pub notes: Vec<String>,
    /// Family-specific numbers (filtered dimension, ONB checks, ...).
    pub extra: BTreeMap<String, Value>,
    /// System modifiers of the recipe, carried to the metrics.
    pub system_modifiers: BTreeMap<String, Value>,
}

/// A materialized factor base.
#[allow(clippy::large_enum_variant)]
pub enum Materialized {
    /// Koblitz regime: a Frobenius-invariant base with orbit structure.
    Koblitz {
        /// The base, closed under the Frobenius.
        fb: FrobeniusFactorBase,
        /// The subspace the decomposition system ranges over (seed `V`).
        basis: Option<Vec<F2mElement>>,
        /// The affine shift `c` when the abscissae are `V + c`.
        shift: Option<F2mElement>,
        /// Construction metadata.
        info: Construction,
    },
    /// Random binary curve: lifted abscissae, one column per abscissa.
    Binary {
        /// All curve points above the abscissae, `(x, y)`.
        points: Vec<(u64, u64)>,
        /// The abscissa set, sorted.
        abscissae: Vec<u64>,
        /// The subspace basis (empty for non-subspace sets).
        subspace_basis: Vec<u64>,
        /// The affine shift when the set is `V + c`.
        shift: Option<u64>,
        /// Construction metadata.
        info: Construction,
    },
    /// Prime-field base: smallest abscissae on the curve, both signs.
    Prime {
        /// `(x, y)` points.
        points: Vec<(u64, u64)>,
        /// Number of abscissae.
        abscissae: usize,
        /// Construction metadata.
        info: Construction,
    },
}

impl Materialized {
    /// The construction metadata.
    pub fn info(&self) -> &Construction {
        match self {
            Materialized::Koblitz { info, .. }
            | Materialized::Binary { info, .. }
            | Materialized::Prime { info, .. } => info,
        }
    }

    /// Number of geometric points (before the usable filter).
    pub fn geometric_points(&self) -> usize {
        match self {
            Materialized::Koblitz { fb, .. } => fb.points.len(),
            Materialized::Binary { points, .. } | Materialized::Prime { points, .. } => {
                points.len()
            }
        }
    }
}

enum Gen {
    /// An abscissa set (plus the subspace it spans, if any).
    Xs(Plan),
    /// A Koblitz base built directly by an existing builder.
    Fb(
        Box<FrobeniusFactorBase>,
        Option<Vec<F2mElement>>,
        Vec<String>,
    ),
}

struct Plan {
    xs: Vec<u64>,
    basis: Option<Vec<u64>>,
    shift: Option<u64>,
    notes: Vec<String>,
    extra: BTreeMap<String, Value>,
}

impl Plan {
    fn from_xs(xs: Vec<u64>) -> Self {
        Self {
            xs,
            basis: None,
            shift: None,
            notes: Vec::new(),
            extra: BTreeMap::new(),
        }
    }

    fn from_basis(ctx: &Ctx, basis: Vec<u64>) -> Result<Self, Reason> {
        if basis.is_empty() {
            return na("dimension 0");
        }
        if rank(&basis) != basis.len() {
            return err("basis is linearly dependent");
        }
        if basis.len() > 22 {
            return na(format!("dimension {} exceeds the cap 22", basis.len()));
        }
        if basis.len() as u32 > ctx.n {
            return na("dimension exceeds the field degree");
        }
        let xs = span(&basis).into_iter().filter(|&x| x != 0).collect();
        Ok(Self {
            xs,
            basis: Some(basis),
            shift: None,
            notes: Vec::new(),
            extra: BTreeMap::new(),
        })
    }
}

fn need_l(r: &Recipe) -> Result<usize, Reason> {
    match r.param_u64("l") {
        Some(l) if l >= 1 => Ok(l as usize),
        Some(_) => na("l must be >= 1"),
        None => err("missing parameter `l`"),
    }
}

fn need_u64(r: &Recipe, key: &str) -> Result<u64, Reason> {
    r.param_u64(key)
        .ok_or_else(|| Reason::Error(format!("missing parameter `{key}`")))
}

fn koblitz_only<'a>(ctx: &Ctx<'a>, family: &str) -> Result<&'a KoblitzCurve, Reason> {
    ctx.kc.ok_or_else(|| {
        Reason::NotApplicable(format!("`{family}` needs a Koblitz curve (Frobenius)"))
    })
}

fn enumerable(ctx: &Ctx, family: &str) -> Result<(), Reason> {
    if ctx.n > MAX_ENUMERABLE_DEGREE {
        return na(format!(
            "`{family}` enumerates the field and 2^{} > 2^{MAX_ENUMERABLE_DEGREE}",
            ctx.n
        ));
    }
    Ok(())
}

// ── Subspace shapes (spec 3.1) ─────────────────────────────────────

fn gen_coordinate(ctx: &Ctx, r: &Recipe) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    Plan::from_basis(ctx, (0..l).map(|i| 1u64 << i).collect())
}

fn gen_random(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    let mut rng = rng_for(seed, "random");
    Plan::from_basis(ctx, random_independent(ctx, &mut rng, l))
}

/// Draw `(c, g)` until `c<1, g, ..., g^(l-1)>` has dimension `l`.
fn progression_basis(
    ctx: &Ctx,
    rng: &mut StdRng,
    l: usize,
    exponents: &[i64],
    draw_g: &dyn Fn(&mut StdRng) -> u64,
    scale: bool,
) -> Result<Vec<u64>, Reason> {
    for _ in 0..512 {
        let c = if scale { random_nonzero(ctx, rng) } else { 1 };
        let g = draw_g(rng);
        if g == 0 {
            continue;
        }
        let ginv = ctx.gf.inv(g);
        let basis: Vec<u64> = exponents
            .iter()
            .map(|&e| {
                let base = if e >= 0 { g } else { ginv };
                ctx.gf.mul(c, ctx.pow(base, e.unsigned_abs()))
            })
            .collect();
        if rank(&basis) == l {
            return Ok(basis);
        }
    }
    na("no ratio g with l independent powers found in 512 draws")
}

fn gen_geometric(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    let mut rng = rng_for(seed, "geometric");
    let mask = ctx.mask();
    let exps: Vec<i64> = (0..l as i64).collect();
    let basis = progression_basis(ctx, &mut rng, l, &exps, &|g| g.gen::<u64>() & mask, true)?;
    Plan::from_basis(ctx, basis)
}

fn gen_gp_scaled(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    let mut rng = rng_for(seed, "gp-scaled");
    let a = random_nonzero(ctx, &mut rng);
    let basis: Vec<u64> = (0..l).map(|i| ctx.gf.mul(a, 1u64 << i)).collect();
    Plan::from_basis(ctx, basis)
}

fn gen_gp_symmetric(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if l % 2 == 0 {
        return na("gp-symmetric needs l odd");
    }
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    let k = (l / 2) as i64;
    let mut rng = rng_for(seed, "gp-symmetric");
    let mask = ctx.mask();
    let exps: Vec<i64> = (-k..=k).collect();
    let basis = progression_basis(ctx, &mut rng, l, &exps, &|g| g.gen::<u64>() & mask, false)?;
    Plan::from_basis(ctx, basis)
}

fn gen_gp_order(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    let o = need_u64(r, "order")?;
    let group = (1u64 << ctx.n) - 1;
    if o == 0 || !group.is_multiple_of(o) {
        return na(format!("order {o} does not divide 2^{} - 1", ctx.n));
    }
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    let mut rng = rng_for(seed, "gp-order");
    let mask = ctx.mask();
    let exps: Vec<i64> = (0..l as i64).collect();
    let cofactor = group / o;
    let basis = progression_basis(
        ctx,
        &mut rng,
        l,
        &exps,
        &|g| {
            let h = g.gen::<u64>() & mask;
            if h == 0 {
                0
            } else {
                ctx.pow(h, cofactor)
            }
        },
        false,
    )
    .map_err(|_| {
        Reason::NotApplicable(format!(
            "elements of order dividing {o} span less than l = {l} dimensions"
        ))
    })?;
    Plan::from_basis(ctx, basis)
}

fn gen_frobenius_progression(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    let mut rng = rng_for(seed, "frobenius-progression");
    for _ in 0..512 {
        let a = random_nonzero(ctx, &mut rng);
        let basis: Vec<u64> = (0..l).map(|i| ctx.gf.sqr_k(a, i as u32)).collect();
        if rank(&basis) == l {
            return Plan::from_basis(ctx, basis);
        }
    }
    na("no element with l independent conjugates found")
}

/// The least integer `a >= 1` whose conjugates `a^(2^i)` are a basis.
fn normal_element(ctx: &Ctx) -> Option<u64> {
    let limit = (1u64 << ctx.n.min(20)).min(1 << 20);
    (1..limit).find(|&a| {
        let conj: Vec<u64> = (0..ctx.n).map(|i| ctx.gf.sqr_k(a, i)).collect();
        rank(&conj) == ctx.n as usize
    })
}

fn gen_normal(ctx: &Ctx, r: &Recipe) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    let a = normal_element(ctx)
        .ok_or_else(|| Reason::NotApplicable("no normal element found".into()))?;
    let basis: Vec<u64> = (0..l).map(|i| ctx.gf.sqr_k(a, i as u32)).collect();
    let mut plan = Plan::from_basis(ctx, basis)?;
    plan.extra
        .insert("normal_element".into(), json!(format!("{a:x}")));
    Ok(plan)
}

fn gen_subfield(ctx: &Ctx, r: &Recipe, seed: u64, scaled: bool) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if !ctx.n.is_multiple_of(l as u32) {
        return na(format!("l = {l} does not divide n = {}", ctx.n));
    }
    let sub = kernel(ctx.n, |x| ctx.gf.sqr_k(x, l as u32) ^ x);
    if sub.len() != l {
        return err("subfield kernel has the wrong dimension");
    }
    let mut basis = sub;
    if scaled {
        let mut rng = rng_for(seed, "scaled-subfield");
        let alpha = random_nonzero(ctx, &mut rng);
        basis = basis.into_iter().map(|b| ctx.gf.mul(alpha, b)).collect();
    }
    Plan::from_basis(ctx, basis)
}

/// ANF-size proxy of a basis: total Hamming weight of the basis vectors and of
/// all their pairwise products (each monomial `v_i v_j` of the descent expands
/// to the polynomial-basis coordinates of `b_i b_j`).
fn anf_proxy(ctx: &Ctx, basis: &[u64]) -> u64 {
    let mut total = 0u64;
    for i in 0..basis.len() {
        total += u64::from(basis[i].count_ones());
        for j in i..basis.len() {
            total += u64::from(ctx.gf.mul(basis[i], basis[j]).count_ones());
        }
    }
    total
}

fn gen_sparse_descent(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    let w = r.param_u64("w").unwrap_or(2).clamp(1, u64::from(ctx.n)) as u32;
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    let mut rng = rng_for(seed, "sparse-descent");
    // Pool: all vectors of weight <= w when small, else a seeded sample.
    let mut pool: Vec<u64> = Vec::new();
    let mut count = 0u64;
    for k in 1..=w {
        count += binom(ctx.n, k);
    }
    if count <= 4096 {
        for k in 1..=w {
            combos(ctx.n, k, &mut |mask| pool.push(mask));
        }
    } else {
        let mut seen = HashSet::new();
        while pool.len() < 4096 {
            let k = rng.gen_range(1..=w);
            let mut v = 0u64;
            while v.count_ones() < k {
                v |= 1u64 << rng.gen_range(0..ctx.n);
            }
            if seen.insert(v) {
                pool.push(v);
            }
        }
    }
    // Greedy: lowest weight class first, then the candidate that adds the
    // fewest ANF terms to the running basis.
    let mut basis: Vec<u64> = Vec::new();
    while basis.len() < l {
        let mut best: Option<(u64, u32, u64)> = None;
        for &c in &pool {
            let mut trial = basis.clone();
            trial.push(c);
            if rank(&trial) != trial.len() {
                continue;
            }
            let key = (anf_proxy(ctx, &trial), c.count_ones(), c);
            if best.is_none_or(|b| key < b) {
                best = Some(key);
            }
        }
        match best {
            Some((_, _, c)) => basis.push(c),
            None => {
                return na(format!(
                    "only {} independent vectors of weight <= {w}",
                    basis.len()
                ))
            }
        }
    }
    let proxy = anf_proxy(ctx, &basis);
    let mut plan = Plan::from_basis(ctx, basis)?;
    plan.extra.insert("anf_proxy_terms".into(), json!(proxy));
    plan.notes.push(
        "ANF term count approximated by the Hamming weight of the basis vectors and their pairwise products".into(),
    );
    Ok(plan)
}

fn binom(n: u32, k: u32) -> u64 {
    let mut acc = 1u128;
    for i in 0..k {
        acc = acc * u128::from(n - i) / u128::from(i + 1);
    }
    acc.min(u128::from(u64::MAX)) as u64
}

/// Visit every `k`-subset of `0..n` as a bit mask (Gosper's hack).
fn combos(n: u32, k: u32, f: &mut dyn FnMut(u64)) {
    if k == 0 || k > n {
        return;
    }
    let limit = if n >= 64 { u64::MAX } else { 1u64 << n };
    let mut v = (1u64 << k) - 1;
    loop {
        f(v);
        let c = v & v.wrapping_neg();
        let r = v + c;
        let next = (((r ^ v) >> 2) / c) | r;
        if next >= limit || next <= v {
            break;
        }
        v = next;
    }
}

// ── Type-II optimal normal basis ───────────────────────────────────

fn is_prime(p: u64) -> bool {
    p >= 2
        && (2..)
            .take_while(|d| d * d <= p)
            .all(|d| !p.is_multiple_of(d))
}

fn mult_order_of_two(p: u64) -> u64 {
    let mut acc = 2 % p;
    let mut k = 1;
    while acc != 1 {
        acc = acc * 2 % p;
        k += 1;
    }
    k
}

/// Polynomials over `F_{2^n}`, coefficients low to high.
fn ptrim(p: &mut Vec<u64>) {
    while p.last() == Some(&0) {
        p.pop();
    }
}

fn pdivrem(gf: &Gf2, a: &[u64], f: &[u64]) -> (Vec<u64>, Vec<u64>) {
    let mut rem = a.to_vec();
    ptrim(&mut rem);
    let df = f.len() - 1;
    let lead_inv = gf.inv(f[df]);
    let mut quo = vec![0u64; rem.len().saturating_sub(df).max(1)];
    while rem.len() > df {
        let shift = rem.len() - 1 - df;
        let c = gf.mul(*rem.last().unwrap_or(&0), lead_inv);
        quo[shift] = c;
        for (i, &fi) in f.iter().enumerate() {
            rem[shift + i] ^= gf.mul(c, fi);
        }
        ptrim(&mut rem);
    }
    ptrim(&mut quo);
    (quo, rem)
}

fn pmul(gf: &Gf2, a: &[u64], b: &[u64]) -> Vec<u64> {
    if a.is_empty() || b.is_empty() {
        return Vec::new();
    }
    let mut out = vec![0u64; a.len() + b.len() - 1];
    for (i, &x) in a.iter().enumerate() {
        for (j, &y) in b.iter().enumerate() {
            out[i + j] ^= gf.mul(x, y);
        }
    }
    ptrim(&mut out);
    out
}

fn pgcd(gf: &Gf2, a: &[u64], b: &[u64]) -> Vec<u64> {
    let (mut a, mut b) = (a.to_vec(), b.to_vec());
    ptrim(&mut a);
    ptrim(&mut b);
    while !b.is_empty() {
        let (_, r) = pdivrem(gf, &a, &b);
        a = b;
        b = r;
    }
    a
}

/// All roots of `f`, assumed to split completely over `F_{2^n}` with simple
/// roots (Cantor-Zassenhaus with the trace map).
fn split_roots(gf: &Gf2, n: u32, f: &[u64], rng: &mut StdRng, out: &mut Vec<u64>) -> bool {
    let d = f.len() - 1;
    if d == 0 {
        return true;
    }
    if d == 1 {
        out.push(gf.mul(f[0], gf.inv(f[1])));
        return true;
    }
    for _ in 0..200 {
        let c = rng.gen::<u64>() & ((1u64 << n) - 1);
        if c == 0 {
            continue;
        }
        let mut t = pdivrem(gf, &[0, c], f).1;
        let mut acc = t.clone();
        for _ in 1..n {
            let sq = pmul(gf, &t, &t);
            t = pdivrem(gf, &sq, f).1;
            if acc.len() < t.len() {
                acc.resize(t.len(), 0);
            }
            for (i, &v) in t.iter().enumerate() {
                acc[i] ^= v;
            }
        }
        ptrim(&mut acc);
        let g = pgcd(gf, f, &acc);
        if g.len() > 1 && g.len() < f.len() {
            let (q, _) = pdivrem(gf, f, &g);
            return split_roots(gf, n, &g, rng, out) && split_roots(gf, n, &q, rng, out);
        }
    }
    false
}

/// The conjugates `beta_j = gamma^(2^j) + gamma^(-2^j)` of a type-II ONB.
struct Onb2 {
    beta: Vec<u64>,
    /// `j_of_k[k]` for `k` in `1..=n`: `k = +-2^j mod 2n+1`.
    j_of_k: Vec<usize>,
}

fn onb2(ctx: &Ctx, seed: u64) -> Result<Onb2, Reason> {
    let n = ctx.n;
    let p = 2 * u64::from(n) + 1;
    if !is_prime(p) || mult_order_of_two(p) != 2 * u64::from(n) {
        return na(format!(
            "2n+1 = {p} must be prime with 2 primitive modulo it (no type-II optimal normal basis)"
        ));
    }
    // psi(t) = 1 + sum_{k=1..n} D_k(t) over F_2, D_{k+1} = t D_k + D_{k-1}.
    let (mut prev, mut cur) = (0u64, 2u64);
    let mut psi = 1u64 ^ cur;
    for _ in 2..=n {
        let next = (cur << 1) ^ prev;
        prev = cur;
        cur = next;
        psi ^= cur;
    }
    let f: Vec<u64> = (0..=n).map(|i| (psi >> i) & 1).collect();
    let mut rng = rng_for(seed, "onb2");
    let mut roots = Vec::new();
    if !split_roots(&ctx.gf, n, &f, &mut rng, &mut roots) || roots.len() != n as usize {
        return err("failed to split the type-II ONB polynomial over the field");
    }
    let beta0 = roots[0];
    let beta: Vec<u64> = (0..n).map(|j| ctx.gf.sqr_k(beta0, j)).collect();
    if beta.iter().fold(0u64, |a, &b| a ^ b) != 1 {
        return err("type-II ONB check failed: the conjugates do not sum to 1");
    }
    let mut j_of_k = vec![0usize; n as usize + 1];
    let mut pow2 = 1u64;
    for j in 0..n as usize {
        for k in [pow2 % p, (p - pow2 % p) % p] {
            if k >= 1 && k <= u64::from(n) {
                j_of_k[k as usize] = j;
            }
        }
        pow2 = pow2 * 2 % p;
    }
    Ok(Onb2 { beta, j_of_k })
}

// ── Non-subspace sets ──────────────────────────────────────────────

fn cap_check(len: usize, what: &str) -> Result<(), Reason> {
    if len > MAX_ABSCISSAE {
        return na(format!(
            "{what}: {len} abscissae exceed the cap {MAX_ABSCISSAE}"
        ));
    }
    Ok(())
}

fn gen_cyclotomic(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let w = need_u64(r, "w")? as u32;
    let onb = onb2(ctx, seed)?;
    let (pairs, with_one) = (w / 2, w % 2 == 1);
    if pairs == 0 && !with_one {
        return na("w must be >= 1");
    }
    if pairs > ctx.n {
        return na("w/2 exceeds n");
    }
    cap_check(binom(ctx.n, pairs) as usize, "cyclotomic")?;
    let mut xs = Vec::new();
    let mut emit = |mask: u64| {
        let mut x = if with_one { 1u64 } else { 0 };
        for j in 0..ctx.n {
            if (mask >> j) & 1 == 1 {
                x ^= onb.beta[j as usize];
            }
        }
        if x != 0 {
            xs.push(x);
        }
    };
    if pairs == 0 {
        emit(0);
    } else {
        combos(ctx.n, pairs, &mut emit);
    }
    let mut plan = Plan::from_xs(xs);
    plan.notes.push(
        "S = -S so the sum lies in the field: even w sums w/2 conjugates beta_j, odd w adds 1"
            .into(),
    );
    Ok(plan)
}

fn gen_index_set(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let onb = onb2(ctx, seed)?;
    let ks: Vec<u64> = match r.param_list("set") {
        Some(set) => set,
        None => {
            let size = need_u64(r, "size")? as usize;
            if size == 0 || size > ctx.n as usize {
                return na("size must be in 1..=n");
            }
            let mut rng = rng_for(seed, "index-set");
            let mut all: Vec<u64> = (1..=u64::from(ctx.n)).collect();
            for i in 0..size {
                let j = rng.gen_range(i..all.len());
                all.swap(i, j);
            }
            all.truncate(size);
            all.sort_unstable();
            all
        }
    };
    if ks.iter().any(|&k| k == 0 || k > u64::from(ctx.n)) {
        return na("index set entries must lie in 1..=n (classes of k mod +-)");
    }
    let basis: Vec<u64> = ks
        .iter()
        .map(|&k| onb.beta[onb.j_of_k[k as usize]])
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let mut plan = Plan::from_basis(ctx, basis)?;
    plan.extra.insert("index_set".into(), json!(ks));
    plan.notes.push(
        "span of the type-II ONB vectors beta_k, k in S (a subspace in the ONB frame)".into(),
    );
    Ok(plan)
}

fn gen_hamming_weight(ctx: &Ctx, r: &Recipe) -> Result<Plan, Reason> {
    let w = need_u64(r, "w")? as u32;
    if w == 0 || w > ctx.n {
        return na("w must be in 1..=n");
    }
    let total: u64 = (1..=w).map(|k| binom(ctx.n, k)).sum();
    cap_check(total as usize, "hamming-weight")?;
    let a = normal_element(ctx)
        .ok_or_else(|| Reason::NotApplicable("no normal element found".into()))?;
    let conj: Vec<u64> = (0..ctx.n).map(|i| ctx.gf.sqr_k(a, i)).collect();
    let mut xs = Vec::with_capacity(total as usize);
    for k in 1..=w {
        combos(ctx.n, k, &mut |mask| {
            let mut x = 0u64;
            for (j, &c) in conj.iter().enumerate() {
                if (mask >> j) & 1 == 1 {
                    x ^= c;
                }
            }
            xs.push(x);
        });
    }
    let mut plan = Plan::from_xs(xs);
    plan.extra
        .insert("normal_element".into(), json!(format!("{a:x}")));
    Ok(plan)
}

fn gen_gauss_period(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    let onb = onb2(ctx, seed)?;
    let window = onb.beta[..l].to_vec();
    let mut xs = BTreeSet::new();
    for s in span(&window).into_iter().filter(|&s| s != 0) {
        xs.extend(roots_of_u(ctx, s));
    }
    cap_check(xs.len(), "gauss-period")?;
    let mut plan = Plan::from_xs(xs.into_iter().collect());
    plan.extra.insert("u_window_dimension".into(), json!(l));
    Ok(plan)
}

/// Roots `x` of `x + 1/x = u` that lie in the field (none when `Tr(1/u) = 1`).
fn roots_of_u(ctx: &Ctx, u: u64) -> Vec<u64> {
    if u == 0 {
        return vec![1];
    }
    let uinv = ctx.gf.inv(u);
    let c = ctx.gf.sqr(uinv);
    match ctx.ash.solve(c) {
        Some(z) => {
            let x = ctx.gf.mul(u, z);
            vec![x, x ^ u]
        }
        None => Vec::new(),
    }
}

fn gen_dual_frobenius_u(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if l as u32 >= ctx.n {
        return na("l must be below n (ker Tr has dimension n-1)");
    }
    let mut rng = rng_for(seed, "dual-frobenius-u");
    let mut basis: Vec<u64> = Vec::new();
    let mut guard = 0;
    while basis.len() < l {
        guard += 1;
        if guard > 100_000 {
            return err("could not draw a basis inside ker Tr");
        }
        let v = rng.gen::<u64>() & ctx.mask();
        if ctx.trace(v) != 0 {
            continue;
        }
        basis.push(v);
        if rank(&basis) != basis.len() {
            basis.pop();
        }
    }
    let v0 = loop {
        let v = rng.gen::<u64>() & ctx.mask();
        if ctx.trace(v) == 1 {
            break v;
        }
    };
    let mut xs = BTreeSet::new();
    for v in span(&basis) {
        xs.extend(roots_of_u(ctx, v0 ^ v));
    }
    xs.remove(&0);
    let mut plan = Plan::from_xs(xs.into_iter().collect());
    plan.extra.insert("u_seed_dimension".into(), json!(l));
    plan.extra
        .insert("u_seed_shift".into(), json!(format!("{v0:x}")));
    Ok(plan)
}

fn gen_mobius_pole(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    let mut rng = rng_for(seed, "mobius-pole");
    let beta = match r.params.get("pole") {
        Some(v) => {
            Recipe::hex_or_int(v)
                .ok_or_else(|| Reason::Error("pole must be an integer or 0x.. hex".into()))?
                & ctx.mask()
        }
        None => rng.gen::<u64>() & ctx.mask(),
    };
    let basis = random_independent(ctx, &mut rng, l);
    if l > 22 {
        return na("l exceeds the cap 22");
    }
    let xs: BTreeSet<u64> = span(&basis)
        .into_iter()
        .filter(|&v| v != 0)
        .map(|v| beta ^ ctx.gf.inv(v))
        .filter(|&x| x != 0)
        .collect();
    let mut plan = Plan::from_xs(xs.into_iter().collect());
    plan.extra.insert("pole".into(), json!(format!("{beta:x}")));
    Ok(plan)
}

fn gen_trace_form(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    enumerable(ctx, "trace-form")?;
    let k = need_u64(r, "k")? as usize;
    let max_forms = (ctx.n as usize - 1) / 2;
    if k == 0 || k > max_forms {
        return na(format!(
            "k must be in 1..={max_forms} (distinct exponents e <= (n-1)/2)"
        ));
    }
    let mut rng = rng_for(seed, "trace-form");
    let mut exps: Vec<u32> = (1..=max_forms as u32).collect();
    for i in 0..k {
        let j = rng.gen_range(i..exps.len());
        exps.swap(i, j);
    }
    exps.truncate(k);
    let eps: Vec<u64> = (0..k).map(|_| rng.gen_range(0..2u64)).collect();
    let mut xs = Vec::new();
    for x in 1..(1u64 << ctx.n) {
        if exps.iter().zip(&eps).all(|(&e, &eps)| {
            let v = ctx.gf.mul(x, ctx.gf.sqr_k(x, e));
            ctx.trace(v) == eps
        }) {
            xs.push(x);
            if xs.len() > MAX_ABSCISSAE {
                return na("trace-form: more than the abscissa cap survive the forms");
            }
        }
    }
    let mut plan = Plan::from_xs(xs);
    plan.extra.insert("exponents".into(), json!(exps));
    plan.extra.insert("targets".into(), json!(eps));
    plan.notes
        .push("c_j = 1 so the set is Frobenius-stable; offsets eps_j drawn".into());
    Ok(plan)
}

fn gen_power_sum(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    let mut rng = rng_for(seed, "power-sum");
    let mask = ctx.mask();
    let exps: Vec<i64> = (0..l as i64).collect();
    let basis = progression_basis(ctx, &mut rng, l, &exps, &|g| g.gen::<u64>() & mask, true)?;
    // dim V.V^2 for the first j basis vectors; the conditions are n - dim.
    let vv2 = |j: usize| -> usize {
        let mut prods = Vec::new();
        for &a in &basis[..j] {
            for &b in &basis[..j] {
                prods.push(ctx.gf.mul(a, ctx.gf.sqr(b)));
            }
        }
        rank(&prods)
    };
    let mut j = l;
    while j > 1 && vv2(j) >= ctx.n as usize {
        j -= 1;
    }
    let dim = vv2(j);
    let conditions = ctx.n as usize - dim;
    let mut plan = Plan::from_basis(ctx, basis[..j].to_vec())?;
    plan.extra.insert("filtered_dimension".into(), json!(j));
    plan.extra.insert("dim_v_v2".into(), json!(dim));
    plan.extra
        .insert("power_sum_conditions".into(), json!(conditions));
    if j < l {
        plan.notes.push(format!(
            "filtered from l = {l} to {j}: dim V.V^2 reached n above that, leaving no power-sum condition"
        ));
    }
    Ok(plan)
}

// ── Koblitz-structured families (spec 3.2) ─────────────────────────

fn conv(ctx: &Ctx, v: &[u64]) -> Vec<F2mElement> {
    v.iter().map(|&x| ctx.gf.to_element(x)).collect()
}

/// Close an abscissa set under the Frobenius and fold into signed orbits.
fn koblitz_sink(ctx: &Ctx, kc: &KoblitzCurve, xs: &[u64]) -> Result<FrobeniusFactorBase, Reason> {
    let set: BTreeSet<u64> = xs.iter().copied().filter(|&x| x != 0).collect();
    if set.is_empty() {
        return na("empty abscissa set");
    }
    if set.len().saturating_mul(kc.extension_degree() as usize) > 4 * MAX_ABSCISSAE {
        return na("Frobenius closure exceeds the abscissa cap");
    }
    let elems: Vec<F2mElement> = set.iter().map(|&x| ctx.gf.to_element(x)).collect();
    build_explicit_frobenius_orbit_factor_base(kc, &elems)
        .ok_or_else(|| Reason::Error("the explicit orbit builder rejected the abscissa set".into()))
}

/// Scan `x = start, start+1, ...` and keep the abscissas whose cofactor
/// projection `[h]P` opens a new signed Frobenius orbit.
fn scan_projected_orbits(ctx: &Ctx, kc: &KoblitzCurve, start: u64, count: usize) -> Vec<u64> {
    let mut seen: HashSet<u64> = HashSet::new();
    let mut out = Vec::new();
    let mut x = start.max(1);
    let limit = 1u64 << ctx.n;
    while out.len() < count && x < limit && x - start.max(1) < (1 << 22) {
        if let Some(&p) = ctx.points_with_x(x).first() {
            let q = if ctx.h == 1 { p } else { ctx.mul(p, ctx.h) };
            if !q.infinity && !seen.contains(&q.pack()) {
                let mut cur = q;
                for _ in 0..ctx.n {
                    seen.insert(cur.pack());
                    seen.insert(ctx.fast.neg(cur).pack());
                    cur = ctx.fast.frobenius_k(cur, kc.k);
                }
                out.push(x);
            }
        }
        x += 1;
    }
    out
}

fn pool_witnesses(
    ctx: &Ctx,
    kc: &KoblitzCurve,
    pool: usize,
    m: usize,
    samples: usize,
    seed: u64,
) -> Result<(FrobeniusFactorBase, Vec<Witness>, usize), Reason> {
    if !(2..=3).contains(&m) {
        return na("pool selection supports m in 2..=3");
    }
    let xs = scan_projected_orbits(ctx, kc, 1, pool);
    let fb = koblitz_sink(ctx, kc, &xs)?;
    if PairSumTable::byte_size(fb.points.len()) > 1 << 28 {
        return na("pair table for the pool exceeds 256 MiB");
    }
    let table = PairSumTable::build(kc, &fb)
        .ok_or_else(|| Reason::NotApplicable("field too wide for the pair table".into()))?;
    let targets = TargetSet::new(kc, samples, 1 << 16, seed);
    let w = witness_list(kc, &fb, &table, &targets, m);
    Ok((fb, w, targets.len()))
}

fn gen_greedy_coverage(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Gen, Reason> {
    let kc = koblitz_only(ctx, "greedy-coverage")?;
    let k = need_u64(r, "K")? as usize;
    let pool = r.param_u64("pool").unwrap_or(4 * k as u64) as usize;
    let m = r.param_u64("m").unwrap_or(2) as usize;
    let (fb, witnesses, ntargets) = pool_witnesses(ctx, kc, pool, m, 2048, seed)?;
    let orbits = fb.signed_orbits.len();
    let mut chosen = vec![false; orbits];
    let mut covered = vec![false; ntargets];
    let mut count = 0;
    while count < k.min(orbits) {
        let mut gain: BTreeMap<usize, BTreeSet<u32>> = BTreeMap::new();
        let mut touch = vec![0usize; orbits];
        for w in &witnesses {
            if covered[w.target as usize] {
                continue;
            }
            let missing: Vec<usize> = w
                .orbits
                .iter()
                .map(|&o| o as usize)
                .filter(|&o| !chosen[o])
                .collect();
            for &o in &missing {
                touch[o] += 1;
            }
            if missing.len() == 1 {
                gain.entry(missing[0]).or_default().insert(w.target);
            }
        }
        let pick = gain
            .iter()
            .max_by_key(|(o, t)| (t.len(), std::cmp::Reverse(**o)))
            .map(|(o, _)| *o)
            .or_else(|| {
                (0..orbits)
                    .filter(|&o| !chosen[o])
                    .max_by_key(|&o| (touch[o], std::cmp::Reverse(o)))
            });
        let Some(o) = pick else { break };
        chosen[o] = true;
        count += 1;
        for w in &witnesses {
            if w.orbits.iter().all(|&x| chosen[x as usize]) {
                covered[w.target as usize] = true;
            }
        }
    }
    let keep: Vec<usize> = (0..orbits).filter(|&o| chosen[o]).collect();
    let covered_n = covered.iter().filter(|&&c| c).count();
    let fb2 = restrict_factor_base_to_orbits(kc, &fb, &keep)
        .ok_or_else(|| Reason::Error("orbit restriction produced no base".into()))?;
    Ok(Gen::Fb(
        Box::new(fb2),
        None,
        vec![format!(
            "greedy over a pool of {orbits} orbits at m={m}: {covered_n}/{ntargets} sampled targets covered"
        )],
    ))
}

fn gen_maxmin(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Gen, Reason> {
    let kc = koblitz_only(ctx, "maxmin-column-rate")?;
    let k = need_u64(r, "K")? as usize;
    let pool = r.param_u64("pool").unwrap_or(4 * k as u64) as usize;
    let samples = r.param_u64("samples").unwrap_or(256) as usize;
    let m = r.param_u64("m").unwrap_or(2) as usize;
    let (fb, witnesses, _) = pool_witnesses(ctx, kc, pool, m, samples, seed)?;
    let orbits = fb.signed_orbits.len();
    let score = |chosen: &[bool]| -> (f64, usize) {
        let mut hits = vec![0usize; orbits];
        let mut rel = 0usize;
        for w in &witnesses {
            if w.orbits.iter().all(|&o| chosen[o as usize]) {
                rel += 1;
                for &o in &w.orbits {
                    hits[o as usize] += 1;
                }
            }
        }
        if rel == 0 {
            return (0.0, 0);
        }
        let min = (0..orbits)
            .filter(|&o| chosen[o])
            .map(|o| hits[o] as f64 / rel as f64)
            .fold(f64::INFINITY, f64::min);
        (min, rel)
    };
    let mut chosen = vec![false; orbits];
    let mut total_touch = vec![0usize; orbits];
    for w in &witnesses {
        for &o in &w.orbits {
            total_touch[o as usize] += 1;
        }
    }
    for _ in 0..k.min(orbits) {
        let mut best: Option<(usize, (f64, usize, usize))> = None;
        for o in 0..orbits {
            if chosen[o] {
                continue;
            }
            chosen[o] = true;
            let (mr, rel) = score(&chosen);
            chosen[o] = false;
            let key = (mr, rel, total_touch[o]);
            if best.is_none_or(|(_, b)| key.partial_cmp(&b) == Some(std::cmp::Ordering::Greater)) {
                best = Some((o, key));
            }
        }
        match best {
            Some((o, _)) => chosen[o] = true,
            None => break,
        }
    }
    let (mr, rel) = score(&chosen);
    let keep: Vec<usize> = (0..orbits).filter(|&o| chosen[o]).collect();
    let fb2 = restrict_factor_base_to_orbits(kc, &fb, &keep)
        .ok_or_else(|| Reason::Error("orbit restriction produced no base".into()))?;
    Ok(Gen::Fb(
        Box::new(fb2),
        None,
        vec![format!(
            "maxmin over {orbits} pool orbits at m={m}: min column rate {mr:.4} on {rel} sampled relations"
        )],
    ))
}

fn gen_ztau(ctx: &Ctx, r: &Recipe, seed: u64, depth: u32) -> Result<Plan, Reason> {
    let kc = koblitz_only(ctx, "ztau-norm")?;
    let norm = need_u64(r, "norm")? as i64;
    let parent = parent_fb(ctx, r, seed, depth)?;
    let (mu, q) = (kc.trace, kc.q as i64);
    let bound = (norm as f64).sqrt().ceil() as i64 + 1;
    let mut xs = BTreeSet::new();
    let mul_signed = |p: FastPoint, k: i64| -> FastPoint {
        let m = ctx.fast.mul(p, &BigUint::from(k.unsigned_abs()));
        if k < 0 {
            ctx.fast.neg(m)
        } else {
            m
        }
    };
    for orbit in &parent.signed_orbits {
        let p = ctx.fast.lift(&parent.points[orbit[0]]);
        let fp = ctx.fast.frobenius_k(p, kc.k);
        for a in -bound..=bound {
            for b in -bound..=bound {
                let nm = a * a + mu * a * b + q * b * b;
                if (a, b) == (0, 0) || nm > norm {
                    continue;
                }
                let s = ctx.fast.add(mul_signed(p, a), mul_signed(fp, b));
                if !s.infinity {
                    xs.insert(s.x);
                }
            }
        }
    }
    Ok(Plan::from_xs(xs.into_iter().collect()))
}

/// The base of a `parent=` sub-recipe as a Frobenius base.
fn parent_fb(ctx: &Ctx, r: &Recipe, seed: u64, depth: u32) -> Result<FrobeniusFactorBase, Reason> {
    if depth > 3 {
        return err("parent recursion too deep");
    }
    let sub = r.parent()?;
    let kc = koblitz_only(ctx, "parent base")?;
    match dispatch(ctx, &sub, seed, depth + 1)? {
        Gen::Fb(fb, _, _) => Ok(*fb),
        Gen::Xs(plan) => koblitz_sink(ctx, kc, &plan.xs),
    }
}

fn gen_pruned(ctx: &Ctx, r: &Recipe, seed: u64, depth: u32) -> Result<Gen, Reason> {
    let kc = koblitz_only(ctx, "pruned")?;
    let m = r.param_u64("m").unwrap_or(3) as usize;
    let fb = parent_fb(ctx, r, seed, depth)?;
    if PairSumTable::byte_size(fb.points.len()) > 1 << 28 {
        return na("pair table for the parent exceeds 256 MiB");
    }
    let table = PairSumTable::build(kc, &fb)
        .ok_or_else(|| Reason::NotApplicable("field too wide for the pair table".into()))?;
    let targets = TargetSet::new(kc, 2048, 1 << 16, seed);
    let w = witness_list(kc, &fb, &table, &targets, m);
    let (keep, steps) = greedy_prune(&fb, &w, targets.len(), 0, 1);
    let out = restrict_factor_base_to_orbits(kc, &fb, &keep)
        .ok_or_else(|| Reason::Error("orbit restriction produced no base".into()))?;
    Ok(Gen::Fb(
        Box::new(out),
        None,
        vec![format!(
            "pruned {} of {} orbits at m={m}",
            steps.len(),
            fb.signed_orbits.len()
        )],
    ))
}

/// Subspace-shape families, in any binary regime.
fn gen_shape(ctx: &Ctx, r: &Recipe, seed: u64) -> Option<Result<Plan, Reason>> {
    Some(match r.family.as_str() {
        "coordinate" => gen_coordinate(ctx, r),
        "random" => gen_random(ctx, r, seed),
        "geometric" => gen_geometric(ctx, r, seed),
        "gp-scaled" => gen_gp_scaled(ctx, r, seed),
        "gp-symmetric" => gen_gp_symmetric(ctx, r, seed),
        "gp-order" => gen_gp_order(ctx, r, seed),
        "frobenius-progression" => gen_frobenius_progression(ctx, r, seed),
        "normal" => gen_normal(ctx, r),
        "subfield" => gen_subfield(ctx, r, seed, r.param_u64("scaled").unwrap_or(0) == 1),
        "scaled-subfield" => gen_subfield(ctx, r, seed, true),
        "sparse-descent" => gen_sparse_descent(ctx, r, seed),
        "cyclotomic" => gen_cyclotomic(ctx, r, seed),
        "index-set" => gen_index_set(ctx, r, seed),
        "hamming-weight" => gen_hamming_weight(ctx, r),
        "gauss-period" => gen_gauss_period(ctx, r, seed),
        "dual-frobenius-u" => gen_dual_frobenius_u(ctx, r, seed),
        "mobius-pole" => gen_mobius_pole(ctx, r, seed),
        "trace-form" => gen_trace_form(ctx, r, seed),
        "power-sum" => gen_power_sum(ctx, r, seed),
        "symmetrised-u" => gen_symmetrised_u(ctx, r, seed),
        _ => return None,
    })
}

fn gen_symmetrised_u(ctx: &Ctx, r: &Recipe, seed: u64) -> Result<Plan, Reason> {
    let l = need_l(r)?;
    if l as u32 > ctx.n {
        return na("l exceeds the field degree");
    }
    let mut v: Option<Vec<u64>> = None;
    if let Some(kc) = ctx.kc {
        use crate::cryptanalysis::koblitz_symmetrised::{
            build_symmetrised_factor_base, divisor_for_dimension,
        };
        if let Some(idx) = divisor_for_dimension(ctx.n, l as u32) {
            if let Some(sfb) = build_symmetrised_factor_base(kc, &idx) {
                if sfb.ell == l {
                    v = Some(sfb.v_basis.iter().map(|e| ctx.gf.from_element(e)).collect());
                }
            }
        }
    }
    let basis = match v {
        Some(b) => b,
        None => {
            let mut rng = rng_for(seed, "symmetrised-u");
            let mut b = vec![1u64];
            while b.len() < l {
                b.push(rng.gen::<u64>() & ctx.mask());
                if rank(&b) != b.len() {
                    b.pop();
                }
            }
            b
        }
    };
    if l > 22 {
        return na("l exceeds the cap 22");
    }
    let xs: BTreeSet<u64> = span(&basis)
        .into_iter()
        .filter(|&u| u != 0)
        .map(|u| ctx.gf.inv(u) ^ 1)
        .filter(|&x| x != 0)
        .collect();
    let mut plan = Plan::from_xs(xs.into_iter().collect());
    plan.extra.insert(
        "u_basis".into(),
        json!(basis.iter().map(|b| format!("{b:x}")).collect::<Vec<_>>()),
    );
    Ok(plan)
}

fn dispatch(ctx: &Ctx, r: &Recipe, seed: u64, depth: u32) -> Result<Gen, Reason> {
    if let Some(p) = gen_shape(ctx, r, seed) {
        return p.map(Gen::Xs);
    }
    let kc_name = |f: &str| koblitz_only(ctx, f);
    match r.family.as_str() {
        "divisor" => {
            let kc = kc_name("divisor")?;
            divisor_gen(kc, r)
        }
        "frobenius-union" => {
            let kc = kc_name("frobenius-union")?;
            let d = need_u64(r, "seed_dim")? as usize;
            if d == 0 || d > 12 || d as u32 > ctx.n {
                return na("seed_dim must be in 1..=12");
            }
            let mut rng = rng_for(seed, "frobenius-union");
            let basis = conv(ctx, &random_independent(ctx, &mut rng, d));
            let fb = build_frobenius_union_factor_base(kc, &basis)
                .ok_or_else(|| Reason::Error("union builder rejected the seed".into()))?;
            Ok(Gen::Fb(Box::new(fb), Some(basis), Vec::new()))
        }
        "explicit-orbits" => {
            kc_name("explicit-orbits")?;
            let reps = r
                .param_list("reps")
                .ok_or_else(|| Reason::Error("missing parameter `reps`".into()))?;
            Ok(Gen::Xs(Plan::from_xs(
                reps.into_iter().map(|x| x & ctx.mask()).collect(),
            )))
        }
        "compact-orbit-scan" => {
            let kc = kc_name("compact-orbit-scan")?;
            let k = need_u64(r, "K")? as usize;
            let xs = scan_projected_orbits(ctx, kc, r.param_u64("start_x").unwrap_or(1), k);
            if xs.len() < k {
                return na(format!(
                    "scan found only {} of {k} projected orbits",
                    xs.len()
                ));
            }
            Ok(Gen::Xs(Plan::from_xs(xs)))
        }
        "greedy-coverage" => gen_greedy_coverage(ctx, r, seed),
        "maxmin-column-rate" => gen_maxmin(ctx, r, seed),
        "pruned" => gen_pruned(ctx, r, seed, depth),
        "two-torsion-saturated" => {
            let kc = kc_name("two-torsion-saturated")?;
            let fb = parent_fb(ctx, r, seed, depth)?;
            let out = saturate_factor_base_two_torsion(kc, &fb).ok_or_else(|| {
                Reason::NotApplicable("2-torsion saturation needs an even cofactor".into())
            })?;
            Ok(Gen::Fb(Box::new(out), None, Vec::new()))
        }
        "subgroup-orbits" => {
            let kc = kc_name("subgroup-orbits")?;
            let spec = FactorBaseSpec::SubgroupOrbits {
                seed: r.seed_or(seed),
                points: need_u64(r, "points")? as usize,
            };
            let fb = spec.materialize(kc).map_err(Reason::Error)?;
            Ok(Gen::Fb(Box::new(fb), None, Vec::new()))
        }
        "ztau-norm" => gen_ztau(ctx, r, seed, depth).map(Gen::Xs),
        "prime-abscissa" => na("prime-abscissa applies to prime-field curves only"),
        "tau-twist" | "per-summand-shift" | "symmetry-breaking" | "trace-constraint"
        | "macaulay-implied" | "trace_zero" | "shift" | "two_torsion" | "frobenius_union" => {
            na("modifier entry, not a base family: pass it through `;name=value`")
        }
        "slope-sigma" => na("scoring lead computed by the sweep as `slope`, not a base"),
        other => err(format!("family `{other}` has no implementation")),
    }
}

fn divisor_gen(kc: &KoblitzCurve, r: &Recipe) -> Result<Gen, Reason> {
    let indices: Vec<usize> = r
        .param_list("indices")
        .ok_or_else(|| Reason::Error("missing parameter `indices`".into()))?
        .into_iter()
        .map(|i| i as usize)
        .collect();
    let fb = FactorBaseSpec::Divisor { indices }
        .materialize(kc)
        .map_err(Reason::NotApplicable)?;
    let basis = fb.subspace_basis.clone();
    Ok(Gen::Fb(Box::new(fb), Some(basis), Vec::new()))
}

// ── Modifiers and materialization ──────────────────────────────────

fn apply_set_modifiers(ctx: &Ctx, r: &Recipe, mut plan: Plan, seed: u64) -> Result<Plan, Reason> {
    if r.modifier_on("trace_zero") {
        match plan.basis.clone() {
            Some(basis) => {
                let tr: Vec<u64> = basis.iter().map(|&b| ctx.trace(b)).collect();
                if let Some(j) = tr.iter().position(|&t| t == 1) {
                    let bj = basis[j];
                    let nb: Vec<u64> = basis
                        .iter()
                        .enumerate()
                        .filter(|(i, _)| *i != j)
                        .map(|(i, &b)| if tr[i] == 1 { b ^ bj } else { b })
                        .collect();
                    if nb.is_empty() {
                        return na("trace_zero leaves dimension 0");
                    }
                    let mut np = Plan::from_basis(ctx, nb)?;
                    np.extra = plan.extra;
                    np.notes = plan.notes;
                    plan = np;
                    plan.notes
                        .push("trace_zero: V intersected with ker Tr".into());
                }
            }
            None => plan.xs.retain(|&x| ctx.trace(x) == 0),
        }
    }
    if let Some(v) = r.modifiers.get("shift") {
        let c = if v.as_str() == Some("invariant") {
            let kc = koblitz_only(ctx, "shift=invariant")?;
            let basis = plan.basis.as_ref().ok_or_else(|| {
                Reason::NotApplicable("shift=invariant needs a subspace base".into())
            })?;
            let shifts = crate::cryptanalysis::affine_factor_base::frobenius_invariant_shifts(
                kc,
                &conv(ctx, basis),
            );
            if shifts.is_empty() {
                return na("no nontrivial Frobenius-invariant coset (V is not invariant)");
            }
            ctx.gf.from_element(&shifts[(seed as usize) % shifts.len()])
        } else {
            Recipe::hex_or_int(v).ok_or_else(|| {
                Reason::Error("shift must be `invariant`, an integer or 0x.. hex".into())
            })? & ctx.mask()
        };
        plan.xs = match &plan.basis {
            Some(b) => span(b).into_iter().map(|x| x ^ c).collect(),
            None => plan.xs.iter().map(|&x| x ^ c).collect(),
        };
        plan.xs.retain(|&x| x != 0);
        plan.shift = Some(c);
    }
    if r.modifier_on("frobenius_union") {
        if ctx.kc.is_some() {
            plan.notes
                .push("frobenius_union: automatic on Koblitz curves".into());
        } else {
            let mut set = BTreeSet::new();
            for &x in &plan.xs {
                let mut y = x;
                for _ in 0..ctx.n {
                    set.insert(y);
                    y = ctx.gf.sqr(y);
                }
            }
            cap_check(set.len(), "frobenius_union")?;
            plan.xs = set.into_iter().collect();
            plan.notes
                .push("frobenius_union: abscissae closed under squaring".into());
        }
    }
    Ok(plan)
}

fn construction(ctx: Option<&Ctx>, basis: Option<&[u64]>, xs: &[u64]) -> Construction {
    let mut c = Construction::default();
    if let Some(ctx) = ctx {
        if let Some(b) = basis {
            c.dimension = Some(b.len() as u32);
            c.dim_v2 = Some(dim_v2(ctx, b) as u32);
            c.basis_weight = Some(rref(b).iter().map(|v| v.count_ones()).sum());
        }
        c.trace_class = Some(
            if xs.iter().all(|&x| ctx.trace(x) == 0) {
                "all_zero"
            } else {
                "mixed"
            }
            .into(),
        );
    }
    c
}

/// Build the base a recipe names on a curve.
pub fn materialize(recipe: &Recipe, curve: &Curve<'_>, seed: u64) -> Result<Materialized, Reason> {
    let t0 = Instant::now();
    let family = registry::find(&recipe.family)
        .ok_or_else(|| Reason::Error(format!("unknown family `{}`", recipe.family)))?;
    let seed = recipe.seed_or(seed);
    let sysmods = recipe.system_modifiers();
    if let Curve::Prime(inst) = curve {
        if recipe.family != "prime-abscissa" {
            return na("prime regime");
        }
        if !recipe.set_modifiers().is_empty() {
            return na("set modifiers are not defined on a prime field");
        }
        let size = need_u64(recipe, "size")? as usize;
        let fb = prime_factor_base(inst, size);
        let points = fb.points.iter().map(|p| (p.x, p.y)).collect();
        let info = Construction {
            abscissae: fb.abscissae,
            build_ms: t0.elapsed().as_secs_f64() * 1e3,
            system_modifiers: sysmods,
            ..Construction::default()
        };
        return Ok(Materialized::Prime {
            points,
            abscissae: fb.abscissae,
            info,
        });
    }
    if !recipe.set_modifiers().is_empty() && !family.modifiers_allowed {
        return na(format!(
            "family `{}` does not accept set modifiers",
            family.name
        ));
    }
    // Large Koblitz fields: only the divisor builder runs without word arithmetic.
    if let Curve::Koblitz(kc) = curve {
        if kc.n > MAX_WORD_DEGREE {
            if recipe.family != "divisor" || !recipe.set_modifiers().is_empty() {
                return na(format!(
                    "n = {} exceeds the single-word field arithmetic (n <= {MAX_WORD_DEGREE}); only `divisor` is built",
                    kc.n
                ));
            }
            let Gen::Fb(fb, basis, _) = divisor_gen(kc, recipe)? else {
                return err("divisor did not produce a base");
            };
            let info = Construction {
                dimension: Some(fb.ell),
                abscissae: fb.subspace.len(),
                build_ms: t0.elapsed().as_secs_f64() * 1e3,
                notes: vec![
                    "n > 62: dim V.V, trace class and basis weight need single-word arithmetic"
                        .into(),
                ],
                system_modifiers: sysmods,
                ..Construction::default()
            };
            return Ok(Materialized::Koblitz {
                fb: *fb,
                basis,
                shift: None,
                info,
            });
        }
    }
    let ctx = Ctx::new(curve)?;
    let two_torsion = recipe.modifier_on("two_torsion");
    let gen = dispatch(&ctx, recipe, seed, 0)?;
    let (plan_opt, fb_opt, fb_basis, mut notes) = match gen {
        Gen::Xs(p) => (
            Some(apply_set_modifiers(&ctx, recipe, p, seed)?),
            None,
            None,
            Vec::new(),
        ),
        Gen::Fb(fb, basis, notes) => {
            for m in ["trace_zero", "shift"] {
                if recipe.modifier_on(m) {
                    return na(format!(
                        "modifier `{m}` is not defined on a prebuilt Frobenius base"
                    ));
                }
            }
            (None, Some(*fb), basis, notes)
        }
    };
    let mut info;
    match (&ctx.kc, plan_opt, fb_opt) {
        (Some(kc), Some(plan), None) => {
            let mut fb = koblitz_sink(&ctx, kc, &plan.xs)?;
            if two_torsion {
                fb = saturate_factor_base_two_torsion(kc, &fb).ok_or_else(|| {
                    Reason::NotApplicable("2-torsion saturation needs an even cofactor".into())
                })?;
            }
            info = construction(Some(&ctx), plan.basis.as_deref(), &plan.xs);
            notes.extend(plan.notes);
            let seed_count = plan.xs.len();
            if plan.basis.is_some() && fb.subspace.len() > seed_count + 1 {
                info.pool_abscissae = Some(plan.xs.clone());
                notes.push(format!(
                    "Frobenius closure: {seed_count} seed abscissae -> {}; the system ranges over the seed only",
                    fb.subspace.len()
                ));
            }
            let basis = plan.basis.as_ref().map(|b| conv(&ctx, b));
            let shift = plan.shift.map(|c| ctx.gf.to_element(c));
            info.abscissae = fb.subspace.len();
            info.notes = notes;
            info.extra = plan.extra;
            info.build_ms = t0.elapsed().as_secs_f64() * 1e3;
            info.system_modifiers = sysmods;
            Ok(Materialized::Koblitz {
                fb,
                basis,
                shift,
                info,
            })
        }
        (Some(kc), None, Some(mut fb)) => {
            if two_torsion {
                fb = saturate_factor_base_two_torsion(kc, &fb).ok_or_else(|| {
                    Reason::NotApplicable("2-torsion saturation needs an even cofactor".into())
                })?;
            }
            let wb: Option<Vec<u64>> = fb_basis
                .as_ref()
                .map(|b| b.iter().map(|e| ctx.gf.from_element(e)).collect());
            let xs: Vec<u64> = fb.subspace.iter().map(|e| ctx.gf.from_element(e)).collect();
            info = construction(Some(&ctx), wb.as_deref(), &xs);
            if fb_basis.as_ref().is_some_and(|b| b.len() as u32 == fb.ell) {
                info.dimension = Some(fb.ell);
            } else {
                info.dimension = None;
                info.dim_v2 = None;
                info.basis_weight = None;
            }
            info.abscissae = fb.subspace.len();
            info.notes = notes;
            info.build_ms = t0.elapsed().as_secs_f64() * 1e3;
            info.system_modifiers = sysmods;
            if matches!(
                fb.domain,
                crate::cryptanalysis::koblitz_index_calculus::FactorBaseDomain::FrobeniusUnion { .. }
            ) {
                info.pool_abscissae =
                    wb.map(|b| span(&b).into_iter().filter(|&x| x != 0).collect());
            }
            let basis =
                fb_basis.filter(|_| info.dimension.is_some() || info.pool_abscissae.is_some());
            Ok(Materialized::Koblitz {
                fb,
                basis,
                shift: None,
                info,
            })
        }
        (None, Some(plan), None) => {
            let set: BTreeSet<u64> = plan.xs.iter().copied().collect();
            let mut pts: Vec<FastPoint> = set.iter().flat_map(|&x| ctx.points_with_x(x)).collect();
            if two_torsion {
                let t = FastPoint::affine(0, ctx.gf.sqr_k(ctx.b, ctx.n - 1));
                let mut seen: HashSet<u64> = pts.iter().map(|p| p.pack()).collect();
                let moved: Vec<FastPoint> = pts.iter().map(|&p| ctx.fast.add(p, t)).collect();
                for q in moved {
                    if !q.infinity && seen.insert(q.pack()) {
                        pts.push(q);
                    }
                }
                notes.push("two_torsion: base united with its translate by (0, sqrt b)".into());
            }
            let abscissae: Vec<u64> = pts
                .iter()
                .map(|p| p.x)
                .collect::<BTreeSet<_>>()
                .into_iter()
                .collect();
            info = construction(Some(&ctx), plan.basis.as_deref(), &plan.xs);
            notes.extend(plan.notes);
            info.abscissae = abscissae.len();
            info.notes = notes;
            info.extra = plan.extra;
            info.build_ms = t0.elapsed().as_secs_f64() * 1e3;
            info.system_modifiers = sysmods;
            let mut points: Vec<(u64, u64)> = pts.iter().map(|p| (p.x, p.y)).collect();
            points.sort_unstable();
            Ok(Materialized::Binary {
                points,
                abscissae,
                subspace_basis: plan.basis.unwrap_or_default(),
                shift: plan.shift,
                info,
            })
        }
        (None, None, Some(_)) => na("this family needs a Koblitz curve (Frobenius)"),
        _ => err("inconsistent materialization state"),
    }
}

// ── Usable points and columns ──────────────────────────────────────

/// Points of a base after the cofactor-projection policy, with the relation
/// column of each projected point.
pub struct BasePoints<E> {
    /// All geometric points of the base.
    pub geometric: usize,
    /// Points with `[h]P != O` (both signs).
    pub usable: Vec<E>,
    /// For each usable point `(column, k, negated)` of `[h]P` (`P ~ (-1)^neg pi^k rep`).
    pub loc: Vec<(usize, u32, bool)>,
    /// Number of distinct projected columns (effective columns).
    pub columns: usize,
    /// Points with `[r]P = O`, when counted.
    pub strict: Option<usize>,
}

/// Usable points and projected columns of a binary base.
pub fn base_points_binary(ctx: &Ctx, m: &Materialized) -> BasePoints<FastPoint> {
    let pts: Vec<FastPoint> = match m {
        Materialized::Koblitz { fb, .. } => fb.points.iter().map(|p| ctx.fast.lift(p)).collect(),
        Materialized::Binary { points, .. } => points
            .iter()
            .map(|&(x, y)| FastPoint::affine(x, y))
            .collect(),
        Materialized::Prime { .. } => Vec::new(),
    };
    let geometric = pts.len();
    let strict =
        (geometric <= 1 << 17).then(|| pts.iter().filter(|&&p| ctx.mul(p, ctx.r).infinity).count());
    let mut usable = Vec::new();
    let mut proj = Vec::new();
    for &p in &pts {
        let q = if ctx.h == 1 { p } else { ctx.mul(p, ctx.h) };
        if !q.infinity {
            usable.push(p);
            proj.push(q);
        }
    }
    let mut map: std::collections::HashMap<u64, (usize, u32, bool)> =
        std::collections::HashMap::new();
    let mut columns = 0usize;
    let steps = if ctx.kc.is_some() { ctx.n } else { 1 };
    let kfrob = ctx.kc.map_or(1, |kc| kc.k);
    let walk = |q: FastPoint, f: &mut dyn FnMut(FastPoint, u32, bool)| {
        let mut cur = q;
        for k in 0..steps {
            f(cur, k, false);
            f(ctx.fast.neg(cur), k, true);
            cur = ctx.fast.frobenius_k(cur, kfrob);
        }
    };
    let mut loc = Vec::with_capacity(proj.len());
    for &q in &proj {
        if !map.contains_key(&q.pack()) {
            let mut rep = q;
            walk(q, &mut |c, _, _| {
                if c.pack() < rep.pack() {
                    rep = c;
                }
            });
            walk(rep, &mut |c, k, neg| {
                map.entry(c.pack()).or_insert((columns, k, neg));
            });
            columns += 1;
        }
        loc.push(map[&q.pack()]);
    }
    BasePoints {
        geometric,
        usable,
        loc,
        columns,
        strict,
    }
}

// ── Tests ──────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    fn kc(n: u32) -> KoblitzCurve {
        [1u8, 0]
            .into_iter()
            .find_map(|a| KoblitzCurve::new(a, n))
            .unwrap_or_else(|| panic!("no usable Koblitz curve at n = {n}"))
    }

    /// Brute-force lifts of an abscissa set, by scanning y.
    fn brute_points(ctx: &Ctx, xs: &[u64]) -> usize {
        let mut count = 0;
        for &x in xs {
            for y in 0..(1u64 << ctx.n) {
                if ctx.fast.is_on_curve(FastPoint::affine(x, y)) {
                    count += 1;
                }
            }
        }
        count
    }

    fn check(recipe: &str, n: u32) -> Option<Materialized> {
        let curve = kc(n);
        let cv = Curve::Koblitz(&curve);
        let r = Recipe::parse(recipe).expect("parse");
        match materialize(&r, &cv, 7) {
            Ok(m) => {
                let ctx = Ctx::new(&cv).expect("ctx");
                if let Materialized::Koblitz { fb, .. } = &m {
                    for p in &fb.points {
                        assert!(curve.curve.is_on_curve(p), "{recipe} n={n}: off curve");
                    }
                    let xs: Vec<u64> = fb.subspace.iter().map(|e| ctx.gf.from_element(e)).collect();
                    assert_eq!(fb.points.len(), brute_points(&ctx, &xs), "{recipe} n={n}");
                }
                let bp = base_points_binary(&ctx, &m);
                assert!(bp.columns <= bp.usable.len());
                Some(m)
            }
            Err(Reason::NotApplicable(why)) => {
                eprintln!("{recipe} n={n}: {why}");
                None
            }
            Err(e) => panic!("{recipe} n={n}: {e}"),
        }
    }

    #[test]
    fn recipe_roundtrip() {
        let r = Recipe::parse("coordinate:l=4;trace_zero=1;tau-twist=1").expect("parse");
        assert_eq!(r.param_u64("l"), Some(4));
        assert!(r.modifier_on("trace_zero") && r.modifier_on("tau-twist"));
        assert_eq!(
            r.to_canonical_json(),
            r#"{"family":"coordinate","modifiers":{"tau-twist":1,"trace_zero":1},"params":{"l":4}}"#
        );
        assert!(Recipe::parse("nope:l=1").is_err());
        assert!(Recipe::parse("coordinate:q=1").is_err());
        let d = Recipe::parse("divisor:indices=0+1").expect("parse");
        assert_eq!(d.param_list("indices"), Some(vec![0, 1]));
    }

    #[test]
    fn subspace_shapes_match_their_definition() {
        for n in [7u32, 9, 11, 13] {
            let c = kc(n);
            let cv = Curve::Koblitz(&c);
            let ctx = Ctx::new(&cv).expect("ctx");
            // coordinate: closure of <1..z^(l-1)> minus 0.
            let m = check("coordinate:l=3", n).expect("coordinate builds");
            let Materialized::Koblitz { fb, info, .. } = &m else {
                panic!()
            };
            let mut want = BTreeSet::new();
            for v in span(&[1, 2, 4]).into_iter().filter(|&v| v != 0) {
                let mut y = v;
                for _ in 0..n {
                    want.insert(y);
                    y = ctx.gf.sqr(y);
                }
            }
            let got: BTreeSet<u64> = fb.subspace.iter().map(|e| ctx.gf.from_element(e)).collect();
            assert_eq!(got, want, "coordinate closure n={n}");
            assert_eq!(info.dimension, Some(3));
            for fam in [
                "random:l=3,seed=3",
                "geometric:l=3",
                "gp-scaled:l=3",
                "gp-symmetric:l=3",
                "frobenius-progression:l=3",
                "normal:l=3",
                "sparse-descent:l=3,w=2",
                "random:l=4;trace_zero=1",
                "random:l=3;shift=5",
                "random:l=3;two_torsion=1",
                "symmetrised-u:l=3",
                "mobius-pole:l=3",
                "dual-frobenius-u:l=3",
                "trace-form:k=1",
                "hamming-weight:w=1",
                "power-sum:l=3",
            ] {
                assert!(check(fam, n).is_some(), "{fam} n={n} should build");
            }
        }
    }

    #[test]
    fn subfield_and_orders() {
        assert!(check("subfield:l=3", 9).is_some());
        assert!(check("scaled-subfield:l=3", 9).is_some());
        assert!(check("subfield:l=3", 7).is_none(), "3 does not divide 7");
        assert!(check("gp-order:l=2,order=7", 9).is_some());
    }

    #[test]
    fn cyclotomic_family_needs_a_type_ii_onb() {
        // n = 9: 19 prime, 2 primitive mod 19.
        let m = check("cyclotomic:w=2", 9).expect("n=9 has a type-II ONB");
        assert_eq!(
            m.info().abscissae,
            9,
            "nine conjugates beta_j, closed under Frobenius"
        );
        assert!(check("cyclotomic:w=2", 13).is_none());
        assert!(check("gauss-period:l=3", 9).is_some());
        assert!(check("index-set:size=3", 9).is_some());
    }

    #[test]
    fn koblitz_structured_families() {
        for n in [9u32, 11, 13] {
            assert!(check("divisor:indices=0", n).is_some() || n == 13 || n == 11 || n == 9);
            assert!(check("frobenius-union:seed_dim=2", n).is_some());
            assert!(check("compact-orbit-scan:K=2", n).is_some());
            let _ = check("subgroup-orbits:points=4,seed=1", n);
            assert!(check("explicit-orbits:reps=3+5", n).is_some());
            assert!(check("ztau-norm:parent=compact-orbit-scan,parent.K=2,norm=4", n).is_some());
            assert!(check("greedy-coverage:K=2,pool=2", n).is_some());
            assert!(check("maxmin-column-rate:K=2,pool=2,samples=64", n).is_some());
            assert!(check(
                "two-torsion-saturated:parent=compact-orbit-scan,parent.K=2",
                n
            )
            .is_some());
            assert!(check("pruned:parent=compact-orbit-scan,parent.K=2,m=2", n).is_some());
        }
    }

    #[test]
    fn prime_regime_and_binary_curves() {
        let inst =
            crate::cryptanalysis::ic_boundary::random_binary_instance(11, 3, 8).expect("curve");
        let cv = Curve::Binary(&inst);
        let m =
            materialize(&Recipe::parse("random:l=3").expect("p"), &cv, 1).expect("binary builds");
        assert!(matches!(m, Materialized::Binary { .. }));
        let r = materialize(&Recipe::parse("divisor:indices=0").expect("p"), &cv, 1);
        assert!(matches!(r, Err(Reason::NotApplicable(_))));
        if let Some(p) = crate::cryptanalysis::ic_boundary::roster_prime_instance(20) {
            let pc = Curve::Prime(&p);
            let ok = materialize(&Recipe::parse("prime-abscissa:size=8").expect("p"), &pc, 1);
            assert!(ok.is_ok());
            let bad = materialize(&Recipe::parse("random:l=3").expect("p"), &pc, 1);
            assert_eq!(
                bad.err(),
                Some(Reason::NotApplicable("prime regime".into()))
            );
        }
    }
}
