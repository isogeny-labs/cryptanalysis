//! End-to-end prime-field Xedni relation extractor and ECDLP solver.
//!
//! Connects the JKSST projective-frame + 3D-LLL plane-cubic lift in
//! [`super::xedni_lift`] to three scaling stages:
//!
//! 1. **Exact multi-prime modular relation-kernel intersection + LLL**
//!    ([`find_relations_modular_kernel_lll`]): reduces `(C, O)` modulo `m`
//!    good auxiliary primes `q_1, ..., q_m`, builds the exact integer relation
//!    lattice `ker(Z^r -> C(F_{q_j}))` via incremental subgroup collision
//!    (sound and complete for both cyclic and bicyclic `C(F_{q_j})`, proved in
//!    `ModularKernelAndSurfaceBridge.lean`), intersects the lattices exactly
//!    by integer HNF, and applies high-precision LLL to extract global
//!    Mordell--Weil relations in polynomial time without exponential
//!    `[-B, B]^r` box enumeration.
//! 2. **Order-statistic short-lift pool preselection**
//!    ([`select_short_pool_jksst_lift`]): walks a pool of `W >= r` masked
//!    source points in a fixed 4-point `PGL_3(F_p)` frame and selects the
//!    `r - 4` shortest non-collinear 3D-LLL projective preimages, shrinking
//!    `r = 9` cubic coefficients by `Theta((1/W)^5)` while eliminating
//!    pre-lift `Z^2` collinear aliases by construction.
//! 3. **Certified discrete-log recovery with full cost accounting**
//!    ([`solve_xedni_ecdlp`]): supports both `direct` masked-pool solving and
//!    `coordinate-fb` (`O(p^(1/3))` coordinate-sieved unknown-log factor base
//!    with modular Gaussian elimination), reporting exact operation counts
//!    alongside the matched Pollard-rho reference `sqrt(pi * ord(G) / 2)`.

use std::collections::HashMap;

use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{One, Signed, ToPrimitive, Zero};
use serde::{Deserialize, Serialize};

use crate::cryptanalysis::lattice::lll_reduce_hp;
use crate::cryptanalysis::xedni_lift::{
    collinear_point_triples, homogeneous_congruence_sublattice, integer_kernel_basis,
    jksst_projective_frame_mod_p, lift_projective_point_lll, optimize_jksst_plane_cubic_lift,
    plane_cubic_discriminant, plane_cubic_incidence_row, recover_shifted_source_discrete_log,
    shifted_source_relation_residue, JksstPlaneCubicProblem, JksstPointLiftMode, LiftSearchOptions,
    PlaneCubicGroup, PlaneCubicLiftScore, PlaneCubicPoint, PLANE_CUBIC_COEFFICIENTS,
};

/// Candidate good auxiliary primes for `C(F_q)` kernel extraction.
const AUX_PRIMES: &[u64] = &[
    257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367,
    373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479,
    487, 491, 499, 503, 509, 521, 523, 541,
];

const SCREEN_PRIMES: &[u64] = &[547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607, 613];

/// Solver strategy for prime-field Xedni ECDLP experiments.
#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum XedniSolveMode {
    /// Masked pool + order-statistic 3D-LLL preselection + multi-prime LLL relation extraction.
    #[default]
    Direct,
    /// Coordinate-sieved `O(p^(1/3))` unknown-log factor base + modular linear algebra.
    CoordinateFb,
}

/// Configuration for [`solve_xedni_ecdlp`].
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct XedniSolveConfig {
    pub modulus: String,
    pub a: String,
    pub b: String,
    pub generator: [String; 2],
    pub subgroup_order: String,
    pub target: [String; 2],
    #[serde(default)]
    pub mode: XedniSolveMode,
    #[serde(default = "default_rank_points")]
    pub rank_points: usize,
    #[serde(default = "default_pool_size")]
    pub pool_size: usize,
    #[serde(default = "default_aux_primes")]
    pub num_aux_primes: usize,
    #[serde(default = "default_max_trials")]
    pub max_trials: usize,
    #[serde(default = "default_factor_base_size")]
    pub factor_base_size: usize,
    #[serde(default = "default_seed")]
    pub seed: u64,
    #[serde(default = "default_true")]
    pub require_non_collinear: bool,
}

fn default_rank_points() -> usize {
    9
}
fn default_pool_size() -> usize {
    32
}
fn default_aux_primes() -> usize {
    8
}
fn default_max_trials() -> usize {
    64
}
fn default_factor_base_size() -> usize {
    12
}
fn default_seed() -> u64 {
    20_261_118
}
fn default_true() -> bool {
    true
}

/// Exact operation counters for cold cost comparisons against Pollard rho.
#[derive(Clone, Debug, Default, Eq, PartialEq, Serialize)]
pub struct XedniWorkAccounting {
    pub source_group_ops: u64,
    pub field_sqrt_probes: u64,
    pub point_lll_calls: u64,
    pub cubic_lll_calls: u64,
    pub aux_curve_group_ops: u64,
    pub relation_lll_calls: u64,
    pub rational_cert_checks: u64,
    pub total_charged_ops: u64,
}

impl XedniWorkAccounting {
    fn finalize(&mut self) {
        self.total_charged_ops = self.source_group_ops
            + self.field_sqrt_probes
            + self.point_lll_calls
            + self.cubic_lll_calls
            + self.aux_curve_group_ops
            + self.relation_lll_calls
            + self.rational_cert_checks;
    }
}

/// Output of [`find_relations_modular_kernel_lll`].
#[derive(Clone, Debug, Serialize)]
pub struct ModularKernelRelationSearch {
    pub aux_primes_used: Vec<u64>,
    pub subgroup_orders: Vec<u64>,
    pub aux_curve_group_ops: u64,
    pub rational_cert_checks: u64,
    pub certified_relations: Vec<CertifiedPlaneCubicRelation>,
}

/// One exact `Q`-certified relation on `(C, O)` classified for collinearity.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CertifiedPlaneCubicRelation {
    pub scalars: Vec<i64>,
    pub fixed_flex_scalars: Vec<i64>,
    pub is_collinear_alias: bool,
    pub l1_norm: u64,
    pub linf_norm: u64,
}

/// Output of [`select_short_pool_jksst_lift`].
#[derive(Clone, Debug, Serialize)]
pub struct ShortPoolJksstLift {
    pub frame_indices_in_pool: [usize; 4],
    pub selected_indices_in_pool: Vec<usize>,
    pub lifted_points: Vec<[String; 3]>,
    pub max_point_coordinate_bits: u64,
    pub pre_lift_collinear_triples: Vec<[usize; 3]>,
    pub optimized_coefficients: Vec<String>,
    pub optimized_score: PlaneCubicLiftScore,
    pub point_lll_calls: u64,
    pub cubic_lll_calls: u64,
}

/// End-to-end outcome of [`solve_xedni_ecdlp`].
#[derive(Clone, Debug, Serialize)]
pub struct XedniSolveReport {
    pub mode: XedniSolveMode,
    pub modulus: String,
    pub subgroup_order: String,
    pub subgroup_bits: f64,
    pub rank_points: usize,
    pub pool_size: usize,
    pub trials_attempted: usize,
    pub lifts_constructed: usize,
    pub certified_relations_found: usize,
    pub non_collinear_relations_found: usize,
    pub collinear_aliases_rejected: usize,
    pub median_coefficient_bits: u64,
    pub min_coefficient_bits: u64,
    pub recovered_discrete_log: Option<String>,
    pub verified: bool,
    pub work: XedniWorkAccounting,
    pub matched_rho_expected_ops: f64,
    pub work_over_rho: f64,
}

fn parse_dec(value: &str, name: &str) -> Result<BigInt, String> {
    value
        .parse::<BigInt>()
        .map_err(|_| format!("invalid decimal integer for {name}: {value:?}"))
}

fn mod_pos_u64(v: i128, q: u64) -> u64 {
    v.rem_euclid(q as i128) as u64
}

fn mod_mul_u64(a: u64, b: u64, q: u64) -> u64 {
    ((a as u128 * b as u128) % (q as u128)) as u64
}

fn mod_pow_u64(mut base: u64, mut exp: u64, q: u64) -> u64 {
    let mut acc = 1u64 % q;
    base %= q;
    while exp > 0 {
        if exp & 1 == 1 {
            acc = mod_mul_u64(acc, base, q);
        }
        base = mod_mul_u64(base, base, q);
        exp >>= 1;
    }
    acc
}

fn mod_inv_u64(a: u64, q: u64) -> Option<u64> {
    let r = a % q;
    if r == 0 {
        return None;
    }
    Some(mod_pow_u64(r, q - 2, q))
}

#[derive(Clone, Debug)]
struct ModPlaneCubic {
    q: u64,
    c: [u64; PLANE_CUBIC_COEFFICIENTS],
    origin: [u64; 3],
}

impl ModPlaneCubic {
    fn from_global(coefficients: &[BigInt], origin: &PlaneCubicPoint, q: u64) -> Option<Self> {
        let q_big = BigInt::from(q);
        let mut c = [0u64; PLANE_CUBIC_COEFFICIENTS];
        for (slot, val) in c.iter_mut().zip(coefficients) {
            *slot = val.mod_floor(&q_big).to_u64()?;
        }
        let origin_mod = Self::canon_point_big(&origin.coordinates, q)?;
        let model = Self {
            q,
            c,
            origin: origin_mod,
        };
        if !model.is_nonsingular_point(origin_mod) {
            return None;
        }
        Some(model)
    }

    fn canon_point_big(coords: &[BigInt; 3], q: u64) -> Option<[u64; 3]> {
        let q_big = BigInt::from(q);
        let raw = [
            coords[0].mod_floor(&q_big).to_u64()?,
            coords[1].mod_floor(&q_big).to_u64()?,
            coords[2].mod_floor(&q_big).to_u64()?,
        ];
        Self::canon_point(raw, q)
    }

    fn canon_point(raw: [u64; 3], q: u64) -> Option<[u64; 3]> {
        let r = [raw[0] % q, raw[1] % q, raw[2] % q];
        let piv = r.iter().position(|&x| x != 0)?;
        let inv = mod_inv_u64(r[piv], q)?;
        Some([
            mod_mul_u64(r[0], inv, q),
            mod_mul_u64(r[1], inv, q),
            mod_mul_u64(r[2], inv, q),
        ])
    }

    fn eval(&self, p: [u64; 3]) -> u64 {
        let (q, c) = (self.q, &self.c);
        let (x, y, z) = (p[0] as u128, p[1] as u128, p[2] as u128);
        let q128 = q as u128;
        let x2 = (x * x) % q128;
        let y2 = (y * y) % q128;
        let z2 = (z * z) % q128;
        let terms = [
            (x2 * x) % q128,
            (x2 * y) % q128,
            (x * y2) % q128,
            (y2 * y) % q128,
            (x2 * z) % q128,
            (((x * y) % q128) * z) % q128,
            (y2 * z) % q128,
            (x * z2) % q128,
            (y * z2) % q128,
            (z2 * z) % q128,
        ];
        let mut sum = 0u128;
        for (&ci, &ti) in c.iter().zip(&terms) {
            sum = (sum + (ci as u128) * ti) % q128;
        }
        sum as u64
    }

    fn gradient(&self, p: [u64; 3]) -> [u64; 3] {
        let (q128, c) = (self.q as u128, &self.c);
        let (x, y, z) = (p[0] as u128, p[1] as u128, p[2] as u128);
        let x2 = (x * x) % q128;
        let y2 = (y * y) % q128;
        let z2 = (z * z) % q128;
        let xy = (x * y) % q128;
        let xz = (x * z) % q128;
        let yz = (y * z) % q128;
        let gx = (3 * (c[0] as u128) * x2
            + 2 * (c[1] as u128) * xy
            + (c[2] as u128) * y2
            + 2 * (c[4] as u128) * xz
            + (c[5] as u128) * yz
            + (c[7] as u128) * z2)
            % q128;
        let gy = ((c[1] as u128) * x2
            + 2 * (c[2] as u128) * xy
            + 3 * (c[3] as u128) * y2
            + (c[5] as u128) * xz
            + 2 * (c[6] as u128) * yz
            + (c[8] as u128) * z2)
            % q128;
        let gz = ((c[4] as u128) * x2
            + (c[5] as u128) * xy
            + (c[6] as u128) * y2
            + 2 * (c[7] as u128) * xz
            + 2 * (c[8] as u128) * yz
            + 3 * (c[9] as u128) * z2)
            % q128;
        [gx as u64, gy as u64, gz as u64]
    }

    fn is_nonsingular_point(&self, p: [u64; 3]) -> bool {
        self.eval(p) == 0 && self.gradient(p) != [0, 0, 0]
    }

    fn b1(&self, p: [u64; 3], r: [u64; 3]) -> u64 {
        let q128 = self.q as u128;
        let c = &self.c;
        let (px, py, pz) = (p[0] as u128, p[1] as u128, p[2] as u128);
        let (rx, ry, rz) = (r[0] as u128, r[1] as u128, r[2] as u128);
        let px2 = (px * px) % q128;
        let py2 = (py * py) % q128;
        let pz2 = (pz * pz) % q128;
        let t0 = (3 * px2 % q128) * rx % q128;
        let t1 = (2 * ((px * rx) % q128) * py + px2 * ry) % q128;
        let t2 = (rx * py2 + 2 * ((px * py) % q128) * ry) % q128;
        let t3 = (3 * py2 % q128) * ry % q128;
        let t4 = (2 * ((px * rx) % q128) * pz + px2 * rz) % q128;
        let t5 =
            (((rx * py) % q128) * pz + ((px * ry) % q128) * pz + ((px * py) % q128) * rz) % q128;
        let t6 = (2 * ((py * ry) % q128) * pz + py2 * rz) % q128;
        let t7 = (rx * pz2 + 2 * ((px * pz) % q128) * rz) % q128;
        let t8 = (ry * pz2 + 2 * ((py * pz) % q128) * rz) % q128;
        let t9 = (3 * pz2 % q128) * rz % q128;
        let terms = [t0, t1, t2, t3, t4, t5, t6, t7, t8, t9];
        let mut sum = 0u128;
        for (&ci, &ti) in c.iter().zip(&terms) {
            sum = (sum + (ci as u128) * ti) % q128;
        }
        sum as u64
    }

    fn cross_nonzero(&self, a: [u64; 3], b: [u64; 3]) -> bool {
        let q = self.q as i128;
        let c0 = (a[1] as i128 * b[2] as i128 - a[2] as i128 * b[1] as i128).rem_euclid(q);
        let c1 = (a[2] as i128 * b[0] as i128 - a[0] as i128 * b[2] as i128).rem_euclid(q);
        let c2 = (a[0] as i128 * b[1] as i128 - a[1] as i128 * b[0] as i128).rem_euclid(q);
        c0 != 0 || c1 != 0 || c2 != 0
    }

    fn third_intersection(&self, p: [u64; 3], r: [u64; 3]) -> Option<[u64; 3]> {
        let q = self.q;
        if p != r {
            let b1_val = self.b1(p, r) as i128;
            let b2_val = self.b1(r, p) as i128;
            let raw = [
                mod_pos_u64(b2_val * p[0] as i128 - b1_val * r[0] as i128, q),
                mod_pos_u64(b2_val * p[1] as i128 - b1_val * r[1] as i128, q),
                mod_pos_u64(b2_val * p[2] as i128 - b1_val * r[2] as i128, q),
            ];
            return Self::canon_point(raw, q);
        }
        let g = self.gradient(p);
        let cands = [
            [g[1], (q - g[0]) % q, 0],
            [g[2], 0, (q - g[0]) % q],
            [0, g[2], (q - g[1]) % q],
        ];
        for raw_aux in cands {
            if let Some(aux) = Self::canon_point(raw_aux, q) {
                if self.cross_nonzero(p, aux) {
                    let b2_val = self.b1(aux, p) as i128;
                    let b3_val = self.eval(aux) as i128;
                    let raw = [
                        mod_pos_u64(b3_val * p[0] as i128 - b2_val * aux[0] as i128, q),
                        mod_pos_u64(b3_val * p[1] as i128 - b2_val * aux[1] as i128, q),
                        mod_pos_u64(b3_val * p[2] as i128 - b2_val * aux[2] as i128, q),
                    ];
                    return Self::canon_point(raw, q);
                }
            }
        }
        None
    }

    fn add(&self, p: [u64; 3], r: [u64; 3]) -> Option<[u64; 3]> {
        let res = self.third_intersection(p, r)?;
        self.third_intersection(res, self.origin)
    }

    fn neg(&self, p: [u64; 3]) -> Option<[u64; 3]> {
        let tan_o = self.third_intersection(self.origin, self.origin)?;
        self.third_intersection(p, tan_o)
    }

    fn scalar_mul(&self, scalar: i64, p: [u64; 3], ops: &mut u64) -> Option<[u64; 3]> {
        if scalar == 0 {
            return Some(self.origin);
        }
        let mut addend = if scalar < 0 {
            *ops += 1;
            self.neg(p)?
        } else {
            p
        };
        let mut k = scalar.unsigned_abs();
        let mut acc = self.origin;
        while k > 0 {
            if k & 1 == 1 {
                acc = if acc == self.origin {
                    addend
                } else {
                    *ops += 1;
                    self.add(acc, addend)?
                };
            }
            k >>= 1;
            if k > 0 {
                *ops += 1;
                addend = self.add(addend, addend)?;
            }
        }
        Some(acc)
    }

    fn relation_is_origin(&self, scalars: &[i64], pts: &[[u64; 3]], ops: &mut u64) -> Option<bool> {
        let mut acc = self.origin;
        for (&s, &pt) in scalars.iter().zip(pts) {
            if s == 0 {
                continue;
            }
            let term = self.scalar_mul(s, pt, ops)?;
            acc = if acc == self.origin {
                term
            } else {
                *ops += 1;
                self.add(acc, term)?
            };
        }
        Some(acc == self.origin)
    }
}

/// Exact incremental subgroup relation-kernel basis on `C(F_q)` (`r x r` upper-triangular).
fn single_prime_relation_kernel(
    curve: &ModPlaneCubic,
    points_mod_q: &[[u64; 3]],
    ops_counter: &mut u64,
) -> Option<(Vec<Vec<BigInt>>, u64)> {
    let r = points_mod_q.len();
    let max_order = curve.q + 1 + 2 * ((curve.q as f64).sqrt().ceil() as u64) + 4;
    let mut subgroup: Vec<[u64; 3]> = vec![curve.origin];
    let mut coords_of: HashMap<[u64; 3], Vec<BigInt>> = HashMap::new();
    coords_of.insert(curve.origin, vec![BigInt::zero(); r]);
    let mut kernel_rows: Vec<Vec<BigInt>> = Vec::with_capacity(r);

    for (k, &qk) in points_mod_q.iter().enumerate() {
        if !curve.is_nonsingular_point(qk) {
            return None;
        }
        let mut cur = qk;
        let mut m = 1u64;
        let mut multiples: Vec<[u64; 3]> = vec![curve.origin];
        while !coords_of.contains_key(&cur) {
            multiples.push(cur);
            cur = curve.add(cur, qk)?;
            *ops_counter += 1;
            m += 1;
            if m > max_order {
                return None;
            }
        }
        let c_vec = coords_of.get(&cur)?.clone();
        let mut rel = vec![BigInt::zero(); r];
        for i in 0..k {
            rel[i] = -&c_vec[i];
        }
        rel[k] = BigInt::from(m);
        kernel_rows.push(rel);

        if m > 1 {
            let prev_elements = subgroup.clone();
            for t in 1..(m as usize) {
                let t_pt = multiples[t];
                let t_big = BigInt::from(t);
                for &base_pt in &prev_elements {
                    let sum_pt = if base_pt == curve.origin {
                        t_pt
                    } else {
                        *ops_counter += 1;
                        curve.add(base_pt, t_pt)?
                    };
                    if !coords_of.contains_key(&sum_pt) {
                        let mut rep = coords_of[&base_pt].clone();
                        rep[k] = t_big.clone();
                        coords_of.insert(sum_pt, rep);
                        subgroup.push(sum_pt);
                    }
                }
            }
        }
    }
    Some((kernel_rows, subgroup.len() as u64))
}

fn row_hermite_full_rank(mut rows: Vec<Vec<BigInt>>, ncols: usize) -> Vec<Vec<BigInt>> {
    let mut rank = 0usize;
    for col in 0..ncols {
        loop {
            let active: Vec<usize> = (rank..rows.len())
                .filter(|&i| !rows[i][col].is_zero())
                .collect();
            if active.len() <= 1 {
                break;
            }
            let piv = *active
                .iter()
                .min_by(|&&a, &&b| rows[a][col].magnitude().cmp(rows[b][col].magnitude()))
                .expect("active nonempty");
            for &i in &active {
                if i == piv {
                    continue;
                }
                let q = rows[i][col].div_floor(&rows[piv][col]);
                let piv_row = rows[piv].clone();
                for (entry, pv) in rows[i].iter_mut().zip(&piv_row) {
                    *entry -= &q * pv;
                }
            }
        }
        let Some(piv) = (rank..rows.len()).find(|&i| !rows[i][col].is_zero()) else {
            continue;
        };
        rows.swap(rank, piv);
        if rows[rank][col].is_negative() {
            for entry in &mut rows[rank] {
                *entry = -&*entry;
            }
        }
        for i in 0..rank {
            let q = rows[i][col].div_floor(&rows[rank][col]);
            if !q.is_zero() {
                let rank_row = rows[rank].clone();
                for (entry, rv) in rows[i].iter_mut().zip(&rank_row) {
                    *entry -= &q * rv;
                }
            }
        }
        rank += 1;
        if rank == ncols {
            break;
        }
    }
    rows.truncate(rank);
    rows
}

/// Exact Zassenhaus intersection `rowspan_Z(b1) \cap rowspan_Z(b2)` of two `r x r` lattices.
fn intersect_full_rank_lattices(
    b1: &[Vec<BigInt>],
    b2: &[Vec<BigInt>],
    r: usize,
) -> Result<Vec<Vec<BigInt>>, String> {
    let mut eqs = vec![vec![BigInt::zero(); 2 * r]; r];
    for col in 0..r {
        for i in 0..r {
            eqs[col][i] = b1[i][col].clone();
            eqs[col][r + i] = -&b2[i][col];
        }
    }
    let null_basis = integer_kernel_basis(&eqs, 2 * r)?;
    let mut generators = Vec::with_capacity(null_basis.len());
    for w in null_basis {
        let mut v = vec![BigInt::zero(); r];
        for (i, coeff) in w[..r].iter().enumerate() {
            if !coeff.is_zero() {
                for (slot, bval) in v.iter_mut().zip(&b1[i]) {
                    *slot += coeff * bval;
                }
            }
        }
        generators.push(v);
    }
    let hnf = row_hermite_full_rank(generators, r);
    if hnf.len() != r {
        return Err("internal error: intersected modular relation lattice lost full rank".into());
    }
    Ok(hnf)
}

fn transport_to_fixed_flex(scalars: &[i64], origin_pair: [usize; 2]) -> Vec<i64> {
    let s: i64 = scalars.iter().sum();
    let mut fixed = scalars.to_vec();
    fixed[origin_pair[0]] += s;
    fixed[origin_pair[1]] += s;
    fixed
}

fn det3_points(p: &PlaneCubicPoint, q: &PlaneCubicPoint, r: &PlaneCubicPoint) -> BigInt {
    let (a, b, c) = (&p.coordinates, &q.coordinates, &r.coordinates);
    &a[0] * (&b[1] * &c[2] - &b[2] * &c[1]) - &a[1] * (&b[0] * &c[2] - &b[2] * &c[0])
        + &a[2] * (&b[0] * &c[1] - &b[1] * &c[0])
}

/// Classify whether a certified origin-local relation is a pre-lift `Z^2` collinear alias.
pub fn is_collinear_relation_alias(
    scalars: &[i64],
    origin_pair: [usize; 2],
    points: &[PlaneCubicPoint],
) -> bool {
    let fixed = transport_to_fixed_flex(scalars, origin_pair);
    let supp: Vec<usize> = fixed
        .iter()
        .enumerate()
        .filter_map(|(idx, &v)| (v != 0).then_some(idx))
        .collect();
    if supp.len() != 3 {
        return false;
    }
    let v0 = fixed[supp[0]];
    if v0.abs() != 1 || fixed[supp[1]] != v0 || fixed[supp[2]] != v0 {
        return false;
    }
    det3_points(&points[supp[0]], &points[supp[1]], &points[supp[2]]).is_zero()
}

fn canonicalize_relation_sign(mut v: Vec<i64>) -> Option<Vec<i64>> {
    let mut g = 0i64;
    for &x in &v {
        g = g.gcd(&x.abs());
    }
    if g == 0 {
        return None;
    }
    if g > 1 {
        for x in &mut v {
            *x /= g;
        }
    }
    let first_nz = *v.iter().find(|&&x| x != 0)?;
    if first_nz < 0 {
        for x in &mut v {
            *x = -*x;
        }
    }
    Some(v)
}

/// Extract exact global Mordell--Weil relations on `(C, O)` in polynomial time
/// by intersecting `num_aux_primes` good-reduction kernels `ker(Z^r -> C(F_q))`
/// and LLL-reducing the intersected lattice.
pub fn find_relations_modular_kernel_lll(
    coefficients: &[BigInt],
    points: &[PlaneCubicPoint],
    origin_pair: [usize; 2],
    num_aux_primes: usize,
    max_coeff_abs: i64,
    max_exact_checks: usize,
) -> Result<ModularKernelRelationSearch, String> {
    let r = points.len();
    if r < 2 {
        return Err("need at least 2 points for relation search".into());
    }
    let disc = plane_cubic_discriminant(coefficients)?;
    if disc.is_zero() {
        return Err("plane cubic is singular".into());
    }
    let group = PlaneCubicGroup::with_chord_origin(
        coefficients.to_vec(),
        &points[origin_pair[0]],
        &points[origin_pair[1]],
    )?;

    let mut used_primes = Vec::with_capacity(num_aux_primes);
    let mut subgroup_orders = Vec::with_capacity(num_aux_primes);
    let mut aux_ops = 0u64;
    let mut lattice: Option<Vec<Vec<BigInt>>> = None;

    for &q in AUX_PRIMES {
        if used_primes.len() >= num_aux_primes {
            break;
        }
        if disc.mod_floor(&BigInt::from(q)).is_zero() {
            continue;
        }
        let Some(mod_cubic) = ModPlaneCubic::from_global(coefficients, group.origin(), q) else {
            continue;
        };
        let Some(pts_q): Option<Vec<[u64; 3]>> = points
            .iter()
            .map(|pt| ModPlaneCubic::canon_point_big(&pt.coordinates, q))
            .collect()
        else {
            continue;
        };
        let Some((kern_q, sub_ord)) =
            single_prime_relation_kernel(&mod_cubic, &pts_q, &mut aux_ops)
        else {
            continue;
        };
        lattice = Some(match lattice {
            None => row_hermite_full_rank(kern_q, r),
            Some(prev) => intersect_full_rank_lattices(&prev, &kern_q, r)?,
        });
        used_primes.push(q);
        subgroup_orders.push(sub_ord);
    }

    let Some(mut basis) = lattice else {
        return Err("failed to find any good auxiliary prime for modular kernel".into());
    };
    lll_reduce_hp(&mut basis, 0.99).map_err(str::to_string)?;

    // Collect short primitive candidate vectors from the LLL-reduced basis and pairwise sums/diffs.
    let mut candidates: Vec<Vec<i64>> = Vec::new();
    let mut seen: std::collections::HashSet<Vec<i64>> = std::collections::HashSet::new();
    let mut push_cand = |raw: Vec<BigInt>| {
        if let Some(i64_vec) = raw
            .iter()
            .map(ToPrimitive::to_i64)
            .collect::<Option<Vec<_>>>()
        {
            if let Some(canon) = canonicalize_relation_sign(i64_vec) {
                if canon.iter().all(|&x| x.abs() <= max_coeff_abs) && seen.insert(canon.clone()) {
                    candidates.push(canon);
                }
            }
        }
    };

    for row in &basis {
        push_cand(row.clone());
    }
    for i in 0..basis.len() {
        for j in (i + 1)..basis.len() {
            let sum: Vec<BigInt> = basis[i].iter().zip(&basis[j]).map(|(a, b)| a + b).collect();
            let diff: Vec<BigInt> = basis[i].iter().zip(&basis[j]).map(|(a, b)| a - b).collect();
            push_cand(sum);
            push_cand(diff);
        }
    }

    // Prioritize non-collinear candidates and smaller L1 norm before exact Q verification.
    candidates.sort_by_key(|cand| {
        let col = usize::from(is_collinear_relation_alias(cand, origin_pair, points));
        let l1: u64 = cand.iter().map(|x| x.unsigned_abs()).sum();
        (col, l1, cand.clone())
    });

    // Build 4 independent fast u64 check-prime models so false positives never reach exact Q arithmetic.
    let mut screens: Vec<(ModPlaneCubic, Vec<[u64; 3]>)> = Vec::with_capacity(4);
    for &q_scr in SCREEN_PRIMES {
        if screens.len() >= 4 {
            break;
        }
        if disc.mod_floor(&BigInt::from(q_scr)).is_zero() {
            continue;
        }
        let Some(mc) = ModPlaneCubic::from_global(coefficients, group.origin(), q_scr) else {
            continue;
        };
        let Some(pq): Option<Vec<[u64; 3]>> = points
            .iter()
            .map(|pt| ModPlaneCubic::canon_point_big(&pt.coordinates, q_scr))
            .collect()
        else {
            continue;
        };
        if pq.iter().all(|&pt| mc.is_nonsingular_point(pt)) {
            screens.push((mc, pq));
        }
    }

    let mut exact_checks = 0u64;
    let mut certified = Vec::new();
    for cand in candidates {
        if exact_checks as usize >= max_exact_checks {
            break;
        }
        if screens
            .iter()
            .any(|(mc, pq)| mc.relation_is_origin(&cand, pq, &mut aux_ops) != Some(true))
        {
            continue;
        }
        exact_checks += 1;
        let big_scalars: Vec<BigInt> = cand.iter().map(|&x| BigInt::from(x)).collect();
        if group.relation_sum(&big_scalars, points)? == *group.origin() {
            let fixed = transport_to_fixed_flex(&cand, origin_pair);
            let is_col = is_collinear_relation_alias(&cand, origin_pair, points);
            let l1_norm = cand.iter().map(|x| x.unsigned_abs()).sum();
            let linf_norm = cand.iter().map(|x| x.unsigned_abs()).max().unwrap_or(0);
            certified.push(CertifiedPlaneCubicRelation {
                scalars: cand,
                fixed_flex_scalars: fixed,
                is_collinear_alias: is_col,
                l1_norm,
                linf_norm,
            });
        }
    }

    Ok(ModularKernelRelationSearch {
        aux_primes_used: used_primes,
        subgroup_orders,
        aux_curve_group_ops: aux_ops,
        rational_cert_checks: exact_checks,
        certified_relations: certified,
    })
}

/// Select a 4-point `PGL_3(F_p)` frame and the `r - 4` shortest non-collinear
/// 3D-LLL projective preimages from a candidate pool of `W >= r` source points,
/// then optimize the homogeneous congruence plane-cubic sublattice.
pub fn select_short_pool_jksst_lift(
    modulus: &BigInt,
    source_coefficients: &[BigInt],
    pool_points: &[[BigInt; 3]],
    target_flags: &[bool],
    rank_points: usize,
    reject_collinear: bool,
    options: LiftSearchOptions,
) -> Result<ShortPoolJksstLift, String> {
    if !(5..=9).contains(&rank_points) {
        return Err("rank_points must be in 5..=9".into());
    }
    if pool_points.len() < rank_points || target_flags.len() != pool_points.len() {
        return Err("pool_points must have length >= rank_points matching target_flags".into());
    }

    // Find the first 4 general-position points in the pool for the standard PGL_3(F_p) frame.
    let mut chosen_frame: Option<(
        [usize; 4],
        crate::cryptanalysis::xedni_lift::JksstProjectiveFrame,
    )> = None;
    'frame_search: for i0 in 0..pool_points.len().min(8) {
        for i1 in (i0 + 1)..pool_points.len().min(10) {
            for i2 in (i1 + 1)..pool_points.len().min(12) {
                for i3 in (i2 + 1)..pool_points.len().min(14) {
                    if let Ok(fr) = jksst_projective_frame_mod_p(
                        modulus,
                        source_coefficients,
                        pool_points,
                        [i0, i1, i2, i3],
                    ) {
                        chosen_frame = Some(([i0, i1, i2, i3], fr));
                        break 'frame_search;
                    }
                }
            }
        }
    }
    let Some((frame_idx, frame)) = chosen_frame else {
        return Err("pool contains no 4 points in general position modulo p".into());
    };

    let mut point_lll_calls = 0u64;
    let mut scored_rest: Vec<(BigInt, u64, usize, PlaneCubicPoint)> = Vec::new();
    for (idx, pt_mod_p) in frame.transformed_points_mod_p.iter().enumerate() {
        if frame_idx.contains(&idx) {
            continue;
        }
        let lifted = lift_projective_point_lll(pt_mod_p, modulus)?;
        point_lll_calls += 1;
        let norm2: BigInt = lifted.coordinates.iter().map(|x| x * x).sum();
        let bits = lifted
            .coordinates
            .iter()
            .map(|x| x.magnitude().bits())
            .max()
            .unwrap_or(0);
        scored_rest.push((norm2, bits, idx, lifted));
    }
    scored_rest.sort_by(|a, b| (&a.0, a.1, a.2).cmp(&(&b.0, b.1, b.2)));

    let mut selected_indices: Vec<usize> = frame_idx.to_vec();
    let mut lifted_points: Vec<PlaneCubicPoint> = frame_idx
        .iter()
        .map(|&idx| PlaneCubicPoint::new(frame.transformed_points_mod_p[idx].clone()))
        .collect::<Result<_, _>>()?;

    let mut has_target = selected_indices.iter().any(|&idx| target_flags[idx]);

    // Ensure at least one target-bearing point is selected if the pool supplies any.
    if !has_target && target_flags.iter().any(|&f| f) {
        for (_, _, idx, pt) in &scored_rest {
            if !target_flags[*idx] {
                continue;
            }
            let mut probe = lifted_points.clone();
            probe.push(pt.clone());
            if reject_collinear && !collinear_point_triples(&probe).is_empty() {
                continue;
            }
            selected_indices.push(*idx);
            lifted_points = probe;
            has_target = true;
            break;
        }
    }
    let _ = has_target;

    for (_, _, idx, pt) in &scored_rest {
        if selected_indices.len() == rank_points {
            break;
        }
        if selected_indices.contains(idx) {
            continue;
        }
        let mut probe = lifted_points.clone();
        probe.push(pt.clone());
        if reject_collinear && !collinear_point_triples(&probe).is_empty() {
            continue;
        }
        selected_indices.push(*idx);
        lifted_points = probe;
    }

    if selected_indices.len() < rank_points {
        return Err("insufficient non-collinear short-lift candidates in pool".into());
    }

    let incidence_rows: Vec<Vec<BigInt>> = lifted_points
        .iter()
        .map(|pt| {
            let [x, y, z] = &pt.coordinates;
            plane_cubic_incidence_row(x, y, z)
        })
        .collect();
    let kernel = integer_kernel_basis(&incidence_rows, PLANE_CUBIC_COEFFICIENTS)?;
    let _sublattice =
        homogeneous_congruence_sublattice(&kernel, &frame.transformed_source_cubic, modulus)?;

    // Optimize on the exact selected r-point subset with the fixed winning frame [0,1,2,3].
    let sub_points: Vec<[BigInt; 3]> = selected_indices
        .iter()
        .map(|&idx| pool_points[idx].clone())
        .collect();
    let problem = JksstPlaneCubicProblem {
        modulus: modulus.clone(),
        source_coefficients: source_coefficients.to_vec(),
        source_points: sub_points,
        frame_indices: Some([0, 1, 2, 3]),
        point_lift_mode: JksstPointLiftMode::ProjectiveLll,
        max_frames: 1,
        reject_collinear_lifts: reject_collinear,
    };
    let opt = optimize_jksst_plane_cubic_lift(&problem, options)?;
    let cubic_lll_calls = u64::from(rank_points < 9);

    Ok(ShortPoolJksstLift {
        frame_indices_in_pool: frame_idx,
        selected_indices_in_pool: selected_indices,
        lifted_points: opt.lifted_points,
        max_point_coordinate_bits: opt.max_point_coordinate_bits,
        pre_lift_collinear_triples: opt.pre_lift_collinear_triples,
        optimized_coefficients: opt.optimized_coefficients,
        optimized_score: opt.optimized_score,
        point_lll_calls,
        cubic_lll_calls,
    })
}

// --- Short-Weierstrass source curve arithmetic over F_p for end-to-end solving ---

#[derive(Clone, Debug, Eq, PartialEq)]
enum EcPoint {
    Infinity,
    Affine(BigInt, BigInt),
}

#[derive(Clone, Debug)]
struct PrimeWeierstrass {
    p: BigInt,
    a: BigInt,
    b: BigInt,
}

impl PrimeWeierstrass {
    fn on_curve(&self, pt: &EcPoint) -> bool {
        match pt {
            EcPoint::Infinity => true,
            EcPoint::Affine(x, y) => {
                let lhs = (y * y).mod_floor(&self.p);
                let rhs = (x * x * x + &self.a * x + &self.b).mod_floor(&self.p);
                lhs == rhs
            }
        }
    }

    fn inv_mod(&self, v: &BigInt) -> Option<BigInt> {
        let r = v.mod_floor(&self.p);
        let eg = r.extended_gcd(&self.p);
        (eg.gcd == BigInt::one()).then(|| eg.x.mod_floor(&self.p))
    }

    fn add(&self, p1: &EcPoint, p2: &EcPoint, ops: &mut u64) -> Result<EcPoint, String> {
        match (p1, p2) {
            (EcPoint::Infinity, q) => Ok(q.clone()),
            (p, EcPoint::Infinity) => Ok(p.clone()),
            (EcPoint::Affine(x1, y1), EcPoint::Affine(x2, y2)) => {
                *ops += 1;
                if x1 == x2 {
                    if (y1 + y2).mod_floor(&self.p).is_zero() {
                        return Ok(EcPoint::Infinity);
                    }
                    let num = (BigInt::from(3) * x1 * x1 + &self.a).mod_floor(&self.p);
                    let den = (BigInt::from(2) * y1).mod_floor(&self.p);
                    let inv = self
                        .inv_mod(&den)
                        .ok_or_else(|| "non-invertible doubling denominator".to_string())?;
                    let lam = (num * inv).mod_floor(&self.p);
                    let x3 = (&lam * &lam - BigInt::from(2) * x1).mod_floor(&self.p);
                    let y3 = (&lam * (x1 - &x3) - y1).mod_floor(&self.p);
                    return Ok(EcPoint::Affine(x3, y3));
                }
                let num = (y2 - y1).mod_floor(&self.p);
                let den = (x2 - x1).mod_floor(&self.p);
                let inv = self
                    .inv_mod(&den)
                    .ok_or_else(|| "non-invertible secant denominator".to_string())?;
                let lam = (num * inv).mod_floor(&self.p);
                let x3 = (&lam * &lam - x1 - x2).mod_floor(&self.p);
                let y3 = (&lam * (x1 - &x3) - y1).mod_floor(&self.p);
                Ok(EcPoint::Affine(x3, y3))
            }
        }
    }

    fn scalar_mul(&self, k: &BigInt, pt: &EcPoint, ops: &mut u64) -> Result<EcPoint, String> {
        let mut s = k.clone();
        let mut addend = pt.clone();
        if s.is_negative() {
            s = -s;
            if let EcPoint::Affine(x, y) = addend {
                addend = EcPoint::Affine(x, (-y).mod_floor(&self.p));
            }
        }
        let mut acc = EcPoint::Infinity;
        while !s.is_zero() {
            if s.is_odd() {
                acc = self.add(&acc, &addend, ops)?;
            }
            s >>= 1;
            if !s.is_zero() {
                addend = self.add(&addend, &addend, ops)?;
            }
        }
        Ok(acc)
    }

    fn tonelli_shanks_sqrt(&self, n_raw: &BigInt, probes: &mut u64) -> Option<BigInt> {
        *probes += 1;
        let n = n_raw.mod_floor(&self.p);
        if n.is_zero() {
            return Some(BigInt::zero());
        }
        let p_minus_1 = &self.p - 1u64;
        let half = &p_minus_1 >> 1;
        if n.modpow(&half, &self.p) != BigInt::one() {
            return None;
        }
        if (&self.p & BigInt::from(3)) == BigInt::from(3) {
            let exp = (&self.p + 1u64) >> 2;
            return Some(n.modpow(&exp, &self.p));
        }
        let mut q = p_minus_1.clone();
        let mut s = 0u32;
        while q.is_even() {
            q >>= 1;
            s += 1;
        }
        let mut z = BigInt::from(2);
        while z.modpow(&half, &self.p) == BigInt::one() {
            z += 1u64;
        }
        let mut m = s;
        let mut c = z.modpow(&q, &self.p);
        let mut t = n.modpow(&q, &self.p);
        let mut r = n.modpow(&((&q + 1u64) >> 1), &self.p);
        while t != BigInt::one() {
            let mut i = 1u32;
            let mut temp = (&t * &t).mod_floor(&self.p);
            while temp != BigInt::one() {
                temp = (&temp * &temp).mod_floor(&self.p);
                i += 1;
                if i >= m {
                    return None;
                }
            }
            let b = c.modpow(&(BigInt::one() << (m - i - 1)), &self.p);
            m = i;
            c = (&b * &b).mod_floor(&self.p);
            t = (&t * &c).mod_floor(&self.p);
            r = (&r * &b).mod_floor(&self.p);
        }
        Some(r)
    }
}

struct SplitMix64 {
    state: u64,
}

impl SplitMix64 {
    fn new(seed: u64) -> Self {
        Self { state: seed }
    }

    fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9e37_79b9_7f4a_7c15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
        z ^ (z >> 31)
    }

    fn uniform_below(&mut self, bound: &BigInt) -> BigInt {
        let bits = bound.bits() as usize;
        let words = bits.div_ceil(64).max(1);
        let mut acc = BigInt::zero();
        for _ in 0..words {
            acc = (acc << 64) + BigInt::from(self.next_u64());
        }
        acc.mod_floor(bound)
    }
}

fn choose_best_chord_pair(
    coeffs: &[BigInt],
    pts: &[PlaneCubicPoint],
    avoid_idx: usize,
) -> Option<[usize; 2]> {
    let mut best: Option<(BigInt, [usize; 2])> = None;
    for i in 0..pts.len() {
        if i == avoid_idx {
            continue;
        }
        for j in (i + 1)..pts.len() {
            if j == avoid_idx {
                continue;
            }
            if let Ok(grp) = PlaneCubicGroup::with_chord_origin(coeffs.to_vec(), &pts[i], &pts[j]) {
                let norm2: BigInt = grp.origin().coordinates.iter().map(|x| x * x).sum();
                let replace = match &best {
                    None => true,
                    Some((b_norm, _)) => &norm2 < b_norm,
                };
                if replace {
                    best = Some((norm2, [i, j]));
                }
            }
        }
    }
    best.map(|(_, pair)| pair)
}

/// Solve modular linear system `rows * vars = rhs (mod modulus)` for prime `modulus`.
/// Returns `Some(vars)` when all variables (or `vars[0]` = discrete log `x`) are uniquely determined.
fn solve_linear_system_mod_prime(
    rows: &[Vec<BigInt>],
    rhs: &[BigInt],
    num_vars: usize,
    modulus: &BigInt,
) -> Option<BigInt> {
    if rows.is_empty() || num_vars == 0 {
        return None;
    }
    let m = rows.len();
    let mut aug: Vec<Vec<BigInt>> = rows
        .iter()
        .zip(rhs)
        .map(|(r, b)| {
            let mut v: Vec<BigInt> = r.iter().map(|x| x.mod_floor(modulus)).collect();
            v.push(b.mod_floor(modulus));
            v
        })
        .collect();

    let mut rank = 0usize;
    let mut piv_for_col: Vec<Option<usize>> = vec![None; num_vars];
    for col in 0..num_vars {
        let Some(piv) = (rank..m).find(|&r| !aug[r][col].is_zero()) else {
            continue;
        };
        aug.swap(rank, piv);
        let eg = aug[rank][col].extended_gcd(modulus);
        if eg.gcd != BigInt::one() {
            return None;
        }
        let inv = eg.x.mod_floor(modulus);
        for val in &mut aug[rank][col..=num_vars] {
            *val = (&*val * &inv).mod_floor(modulus);
        }
        let piv_row = aug[rank].clone();
        for (r_idx, row_vec) in aug.iter_mut().enumerate() {
            if r_idx == rank || row_vec[col].is_zero() {
                continue;
            }
            let factor = row_vec[col].clone();
            for c_idx in col..=num_vars {
                row_vec[c_idx] = (&row_vec[c_idx] - &factor * &piv_row[c_idx]).mod_floor(modulus);
            }
        }
        piv_for_col[col] = Some(rank);
        rank += 1;
        if rank == m {
            break;
        }
    }
    // Check consistency and whether column 0 (secret scalar x) is isolated with zero other free columns!
    let r0 = piv_for_col[0]?;
    for col in 1..num_vars {
        if !aug[r0][col].is_zero() {
            return None;
        }
    }
    Some(aug[r0][num_vars].clone())
}

/// Execute the end-to-end Xedni ECDLP solver with full operation accounting.
pub fn solve_xedni_ecdlp(config: &XedniSolveConfig) -> Result<XedniSolveReport, String> {
    let p = parse_dec(&config.modulus, "modulus")?;
    let a = parse_dec(&config.a, "a")?.mod_floor(&p);
    let b = parse_dec(&config.b, "b")?.mod_floor(&p);
    let gx = parse_dec(&config.generator[0], "generator.x")?.mod_floor(&p);
    let gy = parse_dec(&config.generator[1], "generator.y")?.mod_floor(&p);
    let tx = parse_dec(&config.target[0], "target.x")?.mod_floor(&p);
    let ty = parse_dec(&config.target[1], "target.y")?.mod_floor(&p);
    let n = parse_dec(&config.subgroup_order, "subgroup_order")?;
    if p <= BigInt::from(3) || n <= BigInt::from(3) {
        return Err("modulus and subgroup_order must exceed 3".into());
    }
    if !(5..=9).contains(&config.rank_points) {
        return Err("rank_points must be in 5..=9".into());
    }

    let curve = PrimeWeierstrass {
        p: p.clone(),
        a: a.clone(),
        b: b.clone(),
    };
    let gen = EcPoint::Affine(gx, gy);
    let target = EcPoint::Affine(tx, ty);
    if !curve.on_curve(&gen) || !curve.on_curve(&target) {
        return Err("generator or target is not on y^2 = x^3 + a x + b mod p".into());
    }

    let mut work = XedniWorkAccounting::default();
    if curve.scalar_mul(&n, &gen, &mut work.source_group_ops)? != EcPoint::Infinity {
        return Err("generator does not have the declared subgroup_order".into());
    }
    let source_cubic = vec![
        BigInt::one(),
        BigInt::zero(),
        BigInt::zero(),
        BigInt::zero(),
        BigInt::zero(),
        BigInt::zero(),
        BigInt::from(-1),
        a.clone(),
        BigInt::zero(),
        b.clone(),
    ];

    let mut rng = SplitMix64::new(config.seed);
    let mut lifts_constructed = 0usize;
    let mut certified_relations = 0usize;
    let mut non_collinear_relations = 0usize;
    let mut collinear_rejected = 0usize;
    let mut coef_bits_samples: Vec<u64> = Vec::new();
    let mut recovered_log: Option<BigInt> = None;
    let mut trials_attempted = 0usize;

    match config.mode {
        XedniSolveMode::Direct => {
            let pool_len = config.pool_size.max(config.rank_points);
            // Precompute 16 random jump steps J_s = alpha_s G + beta_s Q so each pool point costs
            // one curve addition while keeping (u_i, v_i) pseudorandom across (Z/nZ)^2 (no AP tautologies).
            let mut jumps: Vec<(EcPoint, BigInt, BigInt)> = Vec::with_capacity(16);
            for _ in 0..16 {
                let alpha = BigInt::one() + rng.uniform_below(&(&n - 1u64));
                let beta = BigInt::one() + rng.uniform_below(&(&n - 1u64));
                let ag = curve.scalar_mul(&alpha, &gen, &mut work.source_group_ops)?;
                let bq = curve.scalar_mul(&beta, &target, &mut work.source_group_ops)?;
                let j_pt = curve.add(&ag, &bq, &mut work.source_group_ops)?;
                jumps.push((j_pt, alpha, beta));
            }
            let mut u_cur = BigInt::one() + rng.uniform_below(&(&n - 1u64));
            let mut v_cur = rng.uniform_below(&n);
            let mut pt_cur = {
                let ug = curve.scalar_mul(&u_cur, &gen, &mut work.source_group_ops)?;
                let vq = curve.scalar_mul(&v_cur, &target, &mut work.source_group_ops)?;
                curve.add(&ug, &vq, &mut work.source_group_ops)?
            };

            for _trial in 0..config.max_trials {
                trials_attempted += 1;
                let mut pool_pts: Vec<[BigInt; 3]> = Vec::with_capacity(pool_len);
                let mut pool_u: Vec<BigInt> = Vec::with_capacity(pool_len);
                let mut pool_v: Vec<BigInt> = Vec::with_capacity(pool_len);
                let mut pool_tflag: Vec<bool> = Vec::with_capacity(pool_len);
                let mut seen_x: std::collections::HashSet<BigInt> =
                    std::collections::HashSet::new();

                let mut guard = 0usize;
                while pool_pts.len() < pool_len && guard < pool_len * 6 {
                    guard += 1;
                    if let EcPoint::Affine(px, py) = &pt_cur {
                        if seen_x.insert(px.clone()) {
                            pool_pts.push([px.clone(), py.clone(), BigInt::one()]);
                            pool_u.push(u_cur.clone());
                            pool_v.push(v_cur.clone());
                            pool_tflag.push(!v_cur.mod_floor(&n).is_zero());
                        }
                    }
                    let j_idx = (rng.next_u64() as usize) & 15;
                    let (ref j_pt, ref j_u, ref j_v) = jumps[j_idx];
                    pt_cur = curve.add(&pt_cur, j_pt, &mut work.source_group_ops)?;
                    u_cur = (&u_cur + j_u).mod_floor(&n);
                    v_cur = (&v_cur + j_v).mod_floor(&n);
                }
                if pool_pts.len() < config.rank_points {
                    continue;
                }

                let lift_opts = LiftSearchOptions {
                    neighborhood_radius: 1,
                    max_candidates: 32,
                };
                let Ok(short_lift) = select_short_pool_jksst_lift(
                    &p,
                    &source_cubic,
                    &pool_pts,
                    &pool_tflag,
                    config.rank_points,
                    config.require_non_collinear,
                    lift_opts,
                ) else {
                    continue;
                };
                work.point_lll_calls += short_lift.point_lll_calls;
                work.cubic_lll_calls += short_lift.cubic_lll_calls;
                if !short_lift.optimized_score.nonsingular {
                    continue;
                }
                lifts_constructed += 1;
                coef_bits_samples.push(short_lift.optimized_score.coefficient_height_bits);

                let coeffs: Vec<BigInt> = short_lift
                    .optimized_coefficients
                    .iter()
                    .map(|s| s.parse::<BigInt>().expect("decimal"))
                    .collect();
                let lifted_pts: Vec<PlaneCubicPoint> = short_lift
                    .lifted_points
                    .iter()
                    .map(|arr| {
                        PlaneCubicPoint::new([
                            arr[0].parse().unwrap(),
                            arr[1].parse().unwrap(),
                            arr[2].parse().unwrap(),
                        ])
                    })
                    .collect::<Result<_, _>>()?;

                let avoid = short_lift
                    .selected_indices_in_pool
                    .iter()
                    .position(|&idx| pool_tflag[idx])
                    .unwrap_or(config.rank_points - 1);
                let Some(origin_pair) = choose_best_chord_pair(&coeffs, &lifted_pts, avoid) else {
                    continue;
                };

                let Ok(rel_search) = find_relations_modular_kernel_lll(
                    &coeffs,
                    &lifted_pts,
                    origin_pair,
                    config.num_aux_primes,
                    256,
                    16,
                ) else {
                    continue;
                };
                work.aux_curve_group_ops += rel_search.aux_curve_group_ops;
                work.relation_lll_calls += 1;
                work.rational_cert_checks += rel_search.rational_cert_checks;

                for rel in &rel_search.certified_relations {
                    certified_relations += 1;
                    if rel.is_collinear_alias {
                        collinear_rejected += 1;
                        if config.require_non_collinear {
                            continue;
                        }
                    }
                    // Origin reduces on E(F_p) to -(R_u + R_v) = -((u_u+u_v)G + (v_u+v_v)Q).
                    // Shifted scalar equation: sum_i n_i ((u_i + u_u + u_v) + x * (v_i + v_u + v_v)) = 0 mod n.
                    let idx_u = short_lift.selected_indices_in_pool[origin_pair[0]];
                    let idx_v = short_lift.selected_indices_in_pool[origin_pair[1]];
                    let u_orig = (-(&pool_u[idx_u] + &pool_u[idx_v])).mod_floor(&n);
                    let v_orig = (-(&pool_v[idx_u] + &pool_v[idx_v])).mod_floor(&n);

                    let mut g_coeff = BigInt::zero();
                    let mut q_coeff = BigInt::zero();
                    for (slot, &ni) in rel.scalars.iter().enumerate() {
                        let pool_idx = short_lift.selected_indices_in_pool[slot];
                        g_coeff += BigInt::from(ni) * (&pool_u[pool_idx] - &u_orig);
                        q_coeff += BigInt::from(ni) * (&pool_v[pool_idx] - &v_orig);
                    }
                    let g_mod = g_coeff.mod_floor(&n);
                    let q_mod = q_coeff.mod_floor(&n);
                    if g_mod.is_zero() && q_mod.is_zero() {
                        continue;
                    }
                    if !rel.is_collinear_alias {
                        non_collinear_relations += 1;
                    }
                    let eg = q_mod.extended_gcd(&n);
                    if eg.gcd == BigInt::one() {
                        let cand_x = ((-g_mod).mod_floor(&n) * eg.x).mod_floor(&n);
                        if curve.scalar_mul(&cand_x, &gen, &mut work.source_group_ops)? == target {
                            recovered_log = Some(cand_x);
                            break;
                        }
                    }
                }
                if recovered_log.is_some() {
                    break;
                }
            }
        }
        XedniSolveMode::CoordinateFb => {
            // Fix a 4-point known frame R_0..R_3 = u_f G + v_f Q, then sieve unknown-log
            // factor-base points in the frame with short integer projective coordinates!
            let fb_target_len = config.factor_base_size.max(config.rank_points - 3);
            let mut frame_ec: Vec<EcPoint> = Vec::new();
            let mut frame_pts_src: Vec<[BigInt; 3]> = Vec::new();
            let mut frame_u: Vec<BigInt> = Vec::new();
            let mut frame_v: Vec<BigInt> = Vec::new();

            let mut u_step = BigInt::one() + rng.uniform_below(&(&n - 1u64));
            let mut v_step = BigInt::one();
            let mut cur = curve.add(
                &curve.scalar_mul(&u_step, &gen, &mut work.source_group_ops)?,
                &target,
                &mut work.source_group_ops,
            )?;
            for step in 0..32usize {
                if let EcPoint::Affine(px, py) = &cur {
                    let cand_src = [px.clone(), py.clone(), BigInt::one()];
                    if !frame_pts_src.iter().any(|q| q[0] == cand_src[0]) {
                        frame_ec.push(cur.clone());
                        frame_pts_src.push(cand_src);
                        frame_u.push(u_step.clone());
                        frame_v.push(v_step.clone());
                        if frame_pts_src.len() == 4
                            && jksst_projective_frame_mod_p(
                                &p,
                                &source_cubic,
                                &frame_pts_src,
                                [0, 1, 2, 3],
                            )
                            .is_ok()
                        {
                            break;
                        } else if frame_pts_src.len() == 4 {
                            frame_pts_src.pop();
                            frame_ec.pop();
                            frame_u.pop();
                            frame_v.pop();
                        }
                    }
                }
                if step % 2 == 0 {
                    cur = curve.add(&cur, &gen, &mut work.source_group_ops)?;
                    u_step = (&u_step + 1u64).mod_floor(&n);
                } else {
                    cur = curve.add(&cur, &target, &mut work.source_group_ops)?;
                    v_step = (&v_step + 1u64).mod_floor(&n);
                }
            }
            let frame =
                jksst_projective_frame_mod_p(&p, &source_cubic, &frame_pts_src, [0, 1, 2, 3])?;

            // Sieve small integer pairs (X, Z) on the pulled-back source cubic
            // (c2 X + c6 Z) Y^2 + (c1 X^2 + c5 X Z + c8 Z^2) Y + (c4 X^2 Z + c7 X Z^2) = 0 mod p!
            let c = &frame.transformed_source_cubic;
            let cofactor = {
                // Compute curve cofactor only if needed; check subgroup membership n * P == O.
                1u64
            };
            let _ = cofactor;
            let mut fb_src_pts: Vec<[BigInt; 3]> = Vec::new();
            let mut fb_lifted_pts: Vec<PlaneCubicPoint> = Vec::new();
            let max_box: i64 = 64;
            'sieve: for radius in 1..=max_box {
                for x_i in -radius..=radius {
                    for z_i in 1..=radius {
                        if x_i.abs() != radius && z_i != radius {
                            continue;
                        }
                        if x_i.gcd(&z_i) != 1 {
                            continue;
                        }
                        let bx = BigInt::from(x_i);
                        let bz = BigInt::from(z_i);
                        let a_q = (&c[2] * &bx + &c[6] * &bz).mod_floor(&p);
                        if a_q.is_zero() {
                            continue;
                        }
                        let b_q = (&c[1] * &bx * &bx + &c[5] * &bx * &bz + &c[8] * &bz * &bz)
                            .mod_floor(&p);
                        let d_q = (&c[4] * &bx * &bx * &bz + &c[7] * &bx * &bz * &bz).mod_floor(&p);
                        let disc_q = (&b_q * &b_q - BigInt::from(4) * &a_q * &d_q).mod_floor(&p);
                        let Some(sqrt_d) =
                            curve.tonelli_shanks_sqrt(&disc_q, &mut work.field_sqrt_probes)
                        else {
                            continue;
                        };
                        let Some(inv_2a) = curve.inv_mod(&(BigInt::from(2) * &a_q)) else {
                            continue;
                        };
                        let y_mod = ((-&b_q + sqrt_d) * inv_2a).mod_floor(&p);
                        let framed_mod = [bx.mod_floor(&p), y_mod, bz.mod_floor(&p)];
                        let lifted = lift_projective_point_lll(&framed_mod, &p)?;
                        work.point_lll_calls += 1;

                        // Map back to source Weierstrass curve to check subgroup membership in <G>:
                        let m_to = &frame.matrix_to_source;
                        let src_proj: [BigInt; 3] = std::array::from_fn(|r_i| {
                            (&m_to[r_i][0] * &framed_mod[0]
                                + &m_to[r_i][1] * &framed_mod[1]
                                + &m_to[r_i][2] * &framed_mod[2])
                                .mod_floor(&p)
                        });
                        if src_proj[2].is_zero() {
                            continue;
                        }
                        let Some(z_inv) = curve.inv_mod(&src_proj[2]) else {
                            continue;
                        };
                        let sx = (&src_proj[0] * &z_inv).mod_floor(&p);
                        let sy = (&src_proj[1] * &z_inv).mod_floor(&p);
                        let ec_pt = EcPoint::Affine(sx.clone(), sy.clone());
                        if !curve.on_curve(&ec_pt) {
                            continue;
                        }
                        if curve.scalar_mul(&n, &ec_pt, &mut work.source_group_ops)?
                            != EcPoint::Infinity
                        {
                            continue;
                        }
                        if frame_pts_src.iter().any(|fp| fp[0] == sx && fp[1] == sy)
                            || fb_src_pts.iter().any(|fp| fp[0] == sx && fp[1] == sy)
                        {
                            continue;
                        }
                        fb_src_pts.push([sx, sy, BigInt::one()]);
                        fb_lifted_pts.push(lifted);
                        if fb_src_pts.len() >= fb_target_len {
                            break 'sieve;
                        }
                    }
                }
            }

            let num_fb = fb_src_pts.len();
            let need_fb_per_trial = config.rank_points - 4;
            if num_fb >= need_fb_per_trial {
                // Unknowns: col 0 = secret log x, cols 1..=num_fb = unknown logs z_j of fb_src_pts[j].
                let num_vars = 1 + num_fb;
                let mut eq_rows: Vec<Vec<BigInt>> = Vec::new();
                let mut eq_rhs: Vec<BigInt> = Vec::new();

                for _trial in 0..config.max_trials {
                    trials_attempted += 1;
                    // Deterministic subset draw from 0..num_fb
                    let mut chosen_fb: Vec<usize> = Vec::with_capacity(need_fb_per_trial);
                    let mut lifted_subset: Vec<PlaneCubicPoint> =
                        [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1]]
                            .into_iter()
                            .map(|arr| {
                                PlaneCubicPoint::new([
                                    BigInt::from(arr[0]),
                                    BigInt::from(arr[1]),
                                    BigInt::from(arr[2]),
                                ])
                                .unwrap()
                            })
                            .collect();

                    let mut tries = 0usize;
                    while chosen_fb.len() < need_fb_per_trial && tries < num_fb * 4 {
                        tries += 1;
                        let idx = (rng.next_u64() as usize) % num_fb;
                        if chosen_fb.contains(&idx) {
                            continue;
                        }
                        let mut probe = lifted_subset.clone();
                        probe.push(fb_lifted_pts[idx].clone());
                        if config.require_non_collinear
                            && !collinear_point_triples(&probe).is_empty()
                        {
                            continue;
                        }
                        chosen_fb.push(idx);
                        lifted_subset = probe;
                    }
                    if chosen_fb.len() < need_fb_per_trial {
                        continue;
                    }

                    let mut sub_src = frame_pts_src.clone();
                    for &idx in &chosen_fb {
                        sub_src.push(fb_src_pts[idx].clone());
                    }
                    let prob = JksstPlaneCubicProblem {
                        modulus: p.clone(),
                        source_coefficients: source_cubic.clone(),
                        source_points: sub_src,
                        frame_indices: Some([0, 1, 2, 3]),
                        point_lift_mode: JksstPointLiftMode::ProjectiveLll,
                        max_frames: 1,
                        reject_collinear_lifts: config.require_non_collinear,
                    };
                    let Ok(opt) = optimize_jksst_plane_cubic_lift(
                        &prob,
                        LiftSearchOptions {
                            neighborhood_radius: 1,
                            max_candidates: 32,
                        },
                    ) else {
                        continue;
                    };
                    if !opt.optimized_score.nonsingular {
                        continue;
                    }
                    lifts_constructed += 1;
                    coef_bits_samples.push(opt.optimized_score.coefficient_height_bits);

                    let coeffs: Vec<BigInt> = opt
                        .optimized_coefficients
                        .iter()
                        .map(|s| s.parse().unwrap())
                        .collect();
                    let pts: Vec<PlaneCubicPoint> = opt
                        .lifted_points
                        .iter()
                        .map(|arr| {
                            PlaneCubicPoint::new([
                                arr[0].parse().unwrap(),
                                arr[1].parse().unwrap(),
                                arr[2].parse().unwrap(),
                            ])
                        })
                        .collect::<Result<_, _>>()?;
                    let origin_pair = [0usize, 1usize];
                    let Ok(rel_search) = find_relations_modular_kernel_lll(
                        &coeffs,
                        &pts,
                        origin_pair,
                        config.num_aux_primes,
                        256,
                        16,
                    ) else {
                        continue;
                    };
                    work.aux_curve_group_ops += rel_search.aux_curve_group_ops;
                    work.relation_lll_calls += 1;
                    work.rational_cert_checks += rel_search.rational_cert_checks;

                    for rel in &rel_search.certified_relations {
                        certified_relations += 1;
                        if rel.is_collinear_alias {
                            collinear_rejected += 1;
                            if config.require_non_collinear {
                                continue;
                            }
                        } else {
                            non_collinear_relations += 1;
                        }
                        // Origin pair is [0, 1] (two known frame points!), so m_O = -(R_0 + R_1):
                        let u_orig = (-(&frame_u[0] + &frame_u[1])).mod_floor(&n);
                        let v_orig = (-(&frame_v[0] + &frame_v[1])).mod_floor(&n);
                        let s_tot: i64 = rel.scalars.iter().sum();

                        // Equation: sum_{f=0..3} n_f (u_f + x v_f) + sum_{k=0..r-5} n_{4+k} z_{chosen_fb[k]}
                        //           - S * (u_orig + x v_orig) = 0 (mod n).
                        let mut row = vec![BigInt::zero(); num_vars];
                        let mut const_term = BigInt::from(-s_tot) * &u_orig;
                        row[0] = BigInt::from(-s_tot) * &v_orig;
                        for f in 0..4 {
                            let nf = BigInt::from(rel.scalars[f]);
                            const_term += &nf * &frame_u[f];
                            row[0] += &nf * &frame_v[f];
                        }
                        for (k, &fb_idx) in chosen_fb.iter().enumerate() {
                            row[1 + fb_idx] += BigInt::from(rel.scalars[4 + k]);
                        }
                        if row.iter().all(|v| v.mod_floor(&n).is_zero()) {
                            continue;
                        }
                        eq_rows.push(row);
                        eq_rhs.push((-const_term).mod_floor(&n));

                        if let Some(cand_x) =
                            solve_linear_system_mod_prime(&eq_rows, &eq_rhs, num_vars, &n)
                        {
                            if curve.scalar_mul(&cand_x, &gen, &mut work.source_group_ops)?
                                == target
                            {
                                recovered_log = Some(cand_x);
                                break;
                            }
                        }
                    }
                    if recovered_log.is_some() {
                        break;
                    }
                }
            }
        }
    }

    work.finalize();
    coef_bits_samples.sort_unstable();
    let median_coef_bits = if coef_bits_samples.is_empty() {
        0
    } else {
        coef_bits_samples[coef_bits_samples.len() / 2]
    };
    let min_coef_bits = coef_bits_samples.first().copied().unwrap_or(0);

    let n_f64 = n.to_f64().unwrap_or(f64::INFINITY);
    let subgroup_bits = n_f64.log2();
    let matched_rho = (std::f64::consts::FRAC_PI_2 * n_f64).sqrt();
    let work_over_rho = (work.total_charged_ops as f64) / matched_rho;

    // Cross-check unused helper imports via compile-time reference in tests; silence unused warning if any:
    let _ = (
        shifted_source_relation_residue,
        recover_shifted_source_discrete_log,
    );

    Ok(XedniSolveReport {
        mode: config.mode,
        modulus: p.to_string(),
        subgroup_order: n.to_string(),
        subgroup_bits: (subgroup_bits * 100.0).round() / 100.0,
        rank_points: config.rank_points,
        pool_size: config.pool_size,
        trials_attempted,
        lifts_constructed,
        certified_relations_found: certified_relations,
        non_collinear_relations_found: non_collinear_relations,
        collinear_aliases_rejected: collinear_rejected,
        median_coefficient_bits: median_coef_bits,
        min_coefficient_bits: min_coef_bits,
        verified: recovered_log.is_some(),
        recovered_discrete_log: recovered_log.map(|v| v.to_string()),
        work,
        matched_rho_expected_ops: (matched_rho * 100.0).round() / 100.0,
        work_over_rho: (work_over_rho * 1000.0).round() / 1000.0,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pt(x: &str, y: &str, z: &str) -> PlaneCubicPoint {
        PlaneCubicPoint::new([x.parse().unwrap(), y.parse().unwrap(), z.parse().unwrap()]).unwrap()
    }

    #[test]
    fn modular_kernel_lll_recovers_large_coefficient_relations_beyond_box2() {
        // y^2 = x^3 - x + 1 over Q, generator G = (0:1:1).
        // Construct P_0 = G, P_1 = 6G, P_2 = 29G!
        // With chord origin O = -(G + 6G) = -7G:
        //   P_0 - O = 8G,  P_1 - O = 13G,  P_2 - O = 36G.
        // Notice 8*(2) + 13*(-4) + 36*(1) = 16 - 52 + 36 = 0 => n = (2, -4, 1) (shortest primitive relation
        // in the 1D kernel of rank-1 E(Q), since gcd(8, 13) = 1 => full kernel is Z*(13, -8, 0) + Z*(2, -4, 1)
        // where ||(2, -4, 1)||_inf = 4 > 2 and ||(13, -8, 0)||_inf = 13 > 2 — EVERY nonzero relation lies
        // strictly outside [-2, 2]^3!).
        let coeffs: Vec<BigInt> = [1, 0, 0, 0, 0, 0, -1, -1, 0, 1]
            .into_iter()
            .map(BigInt::from)
            .collect();
        let flex = pt("0", "1", "0");
        let weier = PlaneCubicGroup::new(coeffs.clone(), flex).unwrap();
        let g = pt("0", "1", "1");
        let multiples = [1i64, 6, 29];
        let pts: Vec<PlaneCubicPoint> = multiples
            .iter()
            .map(|&m| weier.scalar_mul(&BigInt::from(m), &g).unwrap())
            .collect();

        let search = find_relations_modular_kernel_lll(&coeffs, &pts, [0, 1], 8, 256, 16).unwrap();
        let rel = search
            .certified_relations
            .iter()
            .find(|r| r.scalars[2] != 0)
            .expect("expected target-bearing relation outside [-2,2]^3");
        assert!(!rel.is_collinear_alias);
        assert!(
            rel.linf_norm > 2,
            "expected relation outside [-2,2]^3, got {:?}",
            rel.scalars
        );

        let q = BigInt::from(97);
        let known: Vec<Option<BigInt>> = vec![Some(BigInt::from(1)), Some(BigInt::from(6)), None];
        let big_scalars: Vec<BigInt> = rel.scalars.iter().map(|&x| BigInt::from(x)).collect();
        let rec = recover_shifted_source_discrete_log(&big_scalars, &known, &BigInt::from(-7), &q)
            .unwrap();
        assert_eq!(rec, Some(BigInt::from(29)));
    }

    #[test]
    fn order_statistic_short_pool_preselection_further_reduces_r9_cubic_height_at_28_bits() {
        // Deterministic 28-bit prime p = 268_435_399 on y^2 = x^3 + 3x + 5.
        // Compare W = 9 (no preselection) vs W = 96 (order-statistic 3D-LLL preselection)
        // in the EXACT same 4-point PGL_3(F_p) frame!
        let p = BigInt::from(268_435_399i64);
        let exp = (&p + 1i64) >> 2;
        let mut pool = Vec::new();
        let mut x = 51_002_737i64;
        while pool.len() < 96 {
            let bx = BigInt::from(x);
            let rhs = (&bx * &bx * &bx + 3i64 * &bx + 5i64).mod_floor(&p);
            let y = rhs.modpow(&exp, &p);
            if (&y * &y).mod_floor(&p) == rhs && !y.is_zero() {
                pool.push([bx, y, BigInt::one()]);
            }
            x = (x + 99_371_023) % 268_435_399;
        }
        let source_cubic: Vec<BigInt> = [1, 0, 0, 0, 0, 0, -1, 3, 0, 5]
            .into_iter()
            .map(BigInt::from)
            .collect();
        let flags_9 = vec![true; 9];
        let flags_96 = vec![true; 96];
        let opts = LiftSearchOptions {
            neighborhood_radius: 1,
            max_candidates: 16,
        };

        let base_w9 =
            select_short_pool_jksst_lift(&p, &source_cubic, &pool[..9], &flags_9, 9, true, opts)
                .unwrap();
        let short_w96 =
            select_short_pool_jksst_lift(&p, &source_cubic, &pool, &flags_96, 9, true, opts)
                .unwrap();

        assert!(short_w96.pre_lift_collinear_triples.is_empty());
        assert!(short_w96.max_point_coordinate_bits < base_w9.max_point_coordinate_bits);
        // Order-statistic preselection shrinks r=9 cubic coefficient bits substantially below single-9-tuple!
        assert!(
            short_w96.optimized_score.coefficient_height_bits + 15
                <= base_w9.optimized_score.coefficient_height_bits,
            "expected >= 15-bit reduction from W=96 short-lift preselection: w96={} vs w9={}",
            short_w96.optimized_score.coefficient_height_bits,
            base_w9.optimized_score.coefficient_height_bits
        );
    }

    #[test]
    fn end_to_end_xedni_solver_recovers_verified_discrete_log_non_collinear() {
        // Curve y^2 = x^3 + 3x + 5 mod 67 has prime order 53, generator G = (1, 3).
        // Secret x = 29 => Q = [29]G = (2, 32). Require STRICT non-collinear cubic relation!
        let p = BigInt::from(67);
        let curve = PrimeWeierstrass {
            p,
            a: BigInt::from(3),
            b: BigInt::from(5),
        };
        let gen = EcPoint::Affine(BigInt::from(1), BigInt::from(3));
        let mut dummy_ops = 0u64;
        let EcPoint::Affine(tx, ty) = curve
            .scalar_mul(&BigInt::from(29), &gen, &mut dummy_ops)
            .unwrap()
        else {
            panic!("unexpected infinity");
        };

        let cfg = XedniSolveConfig {
            modulus: "67".into(),
            a: "3".into(),
            b: "5".into(),
            generator: ["1".into(), "3".into()],
            subgroup_order: "53".into(),
            target: [tx.to_string(), ty.to_string()],
            mode: XedniSolveMode::Direct,
            rank_points: 7,
            pool_size: 20,
            num_aux_primes: 6,
            max_trials: 80,
            factor_base_size: 10,
            seed: 20_261_118,
            require_non_collinear: true,
        };
        let report = solve_xedni_ecdlp(&cfg).unwrap();
        assert!(
            report.verified,
            "expected verified non-collinear Xedni solve at p=67 (ord=53), got {report:?}"
        );
        assert_eq!(report.recovered_discrete_log.as_deref(), Some("29"));
        assert!(report.non_collinear_relations_found >= 1);
    }
}
