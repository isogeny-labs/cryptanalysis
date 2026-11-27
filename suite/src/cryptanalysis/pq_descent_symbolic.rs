//! # Symbolic Weil descent of the summation polynomials.
//!
//! [`pq_descent`](crate::cryptanalysis::pq_descent) builds the boolean
//! system of a Weil descent from a **truth table**: it evaluates
//! `S_{m+1}` at every one of the `2^{m·n'}` points of `V^m` and
//! Möbius-transforms the bits into algebraic normal forms.  That is
//! exact and simple, and it caps the subspace dimension at `n' = 8`
//! for two summands and `n' = 5` for three, because the table is the
//! whole enumeration the descent exists to avoid.
//!
//! This module builds the same system **symbolically**.  Each abscissa
//! is the linear form `x_i = Σ_k v_{i,k} e_k` over the subspace basis,
//! and the summation polynomial is expanded in the ring
//! `F_{2^n}[v] / (v² − v)` term by term, exactly as the evaluating
//! functions compute it: a polynomial here is a map from a boolean
//! monomial (a 64-bit mask over the `v`'s) to its `F_{2^n}`
//! coefficient, and the ring's two facts do all the work —
//!
//! - **squaring is linear**: `(Σ c_M M)² = Σ c_M² M`, because `M² = M`
//!   and every cross term carries a factor of two;
//! - **multiplication is a union**: `M · N = M ∪ N`.
//!
//! The descended system is then read off one bit at a time: equation
//! `j` is the set of monomials whose coefficient has bit `j` set.
//! `S_3` comes out quadratic in `2n'` variables with at most
//! `n'² + 2n' + 1` monomials, whatever `n'`; `S_4` comes out of degree
//! at most six in `3n'` variables, since its resultant form is a
//! product of two cubics.  The only cap left is the monomial mask:
//! `m·n' ≤ 64` variables.
//!
//! The two constructions must agree monomial for monomial — the
//! algebraic normal form of a boolean function is unique — and the
//! test suite checks that they do, on random curves, at every
//! dimension the truth table can still reach.

use crate::cryptanalysis::fx_hash::MaskMap;
use crate::cryptanalysis::pq_groebner_f2::{mono_key, F2BoolMono, F2BoolPoly};
use crate::cryptanalysis::semaev_decomp::Gf2;

/// The most boolean variables a system may have: one bit of a
/// [`F2BoolMono`] mask per variable.
pub const MAX_VARS: u32 = 64;

/// The largest subspace dimension this descent will take at `summands`
/// summands: `⌊64 / m⌋`.
pub fn max_n_prime(summands: u32) -> u32 {
    match summands {
        2 | 3 => MAX_VARS / summands,
        _ => 0,
    }
}

// ── F_{2^n}[v] / (v² − v) ──────────────────────────────────────────

/// A polynomial over `F_{2^n}` in boolean variables: monomial mask to
/// non-zero coefficient.  Keyed with the mask hasher: every operation here
/// accumulates by XOR, so the map's iteration order never reaches a result.
#[derive(Clone, Debug, Default)]
pub struct FieldBoolPoly {
    terms: MaskMap<u64>,
}

impl FieldBoolPoly {
    /// The constant `c`.
    pub fn constant(c: u64) -> Self {
        let mut p = Self::default();
        if c != 0 {
            p.terms.insert(0, c);
        }
        p
    }

    /// The linear form `Σ_k v_{offset + k} · basis[k]`.
    pub fn linear(offset: u32, basis: &[u64]) -> Self {
        let mut p = Self::default();
        for (k, &e) in basis.iter().enumerate() {
            if e != 0 {
                p.terms.insert(1u64 << (offset + k as u32), e);
            }
        }
        p
    }

    fn add_term(&mut self, mask: u64, coeff: u64) {
        if coeff == 0 {
            return;
        }
        match self.terms.get_mut(&mask) {
            Some(c) => {
                *c ^= coeff;
                if *c == 0 {
                    self.terms.remove(&mask);
                }
            }
            None => {
                self.terms.insert(mask, coeff);
            }
        }
    }

    pub fn add(&self, other: &Self) -> Self {
        let mut out = self.clone();
        for (&m, &c) in &other.terms {
            out.add_term(m, c);
        }
        out
    }

    /// `M · N = M ∪ N` in the boolean ring.
    pub fn mul(&self, other: &Self, gf: &Gf2) -> Self {
        let mut out = Self::default();
        for (&ma, &ca) in &self.terms {
            for (&mb, &cb) in &other.terms {
                out.add_term(ma | mb, gf.mul(ca, cb));
            }
        }
        out
    }

    /// `(Σ c_M M)² = Σ c_M² M`: the Frobenius on the coefficients.
    pub fn sqr(&self, gf: &Gf2) -> Self {
        Self {
            terms: self.terms.iter().map(|(&m, &c)| (m, gf.sqr(c))).collect(),
        }
    }

    pub fn scale(&self, c: u64, gf: &Gf2) -> Self {
        let mut out = Self::default();
        for (&m, &a) in &self.terms {
            out.add_term(m, gf.mul(a, c));
        }
        out
    }

    pub fn len(&self) -> usize {
        self.terms.len()
    }

    pub fn is_empty(&self) -> bool {
        self.terms.is_empty()
    }

    /// Evaluate at a point of `{0,1}^vars`, as a field element.
    pub fn eval(&self, point: u64) -> u64 {
        self.terms
            .iter()
            .filter(|(&m, _)| point & m == m)
            .fold(0u64, |acc, (_, &c)| acc ^ c)
    }

    /// The `n` boolean coordinate polynomials: equation `j` holds the
    /// monomials whose coefficient has bit `j` set.
    ///
    /// The terms are sorted once into canonical (descending) order and dealt
    /// out in that order, so each equation's list is already canonical —
    /// its masks are distinct, being keys of one map — and is taken as is,
    /// instead of `n` separate sorts of about half the terms each.
    pub fn split(&self, n: u32, n_vars: usize) -> Vec<F2BoolPoly> {
        let mut keyed: Vec<(u128, u64)> = self
            .terms
            .iter()
            .map(|(&m, &c)| (mono_key(F2BoolMono::from_mask(m)), c))
            .collect();
        keyed.sort_unstable_by_key(|a| std::cmp::Reverse(a.0));
        let mut monos: Vec<Vec<F2BoolMono>> = (0..n).map(|_| Vec::new()).collect();
        for &(key, c) in &keyed {
            let m = F2BoolMono::from_mask(!(key as u64));
            let mut bits = c;
            while bits != 0 {
                let j = bits.trailing_zeros();
                if j < n {
                    monos[j as usize].push(m);
                }
                bits &= bits - 1;
            }
        }
        monos
            .into_iter()
            .map(|terms| F2BoolPoly { terms, n_vars })
            .collect()
    }

    /// Split a polynomial whose coefficients lie in `span(basis)` into that
    /// basis's coordinates instead of the ambient field coordinates.  This
    /// is an invertible row-space change on the equality `self = 0` and
    /// therefore generates the same Boolean ideal without redundant ambient
    /// coordinate equations.
    fn split_in_basis(&self, basis: &[u64], n_vars: usize) -> Result<Vec<F2BoolPoly>, String> {
        let mut rebased = Self::default();
        for (&mask, &coefficient) in &self.terms {
            let coordinates = coordinates_in_basis(coefficient, basis).ok_or_else(|| {
                "a product-constraint coefficient escaped its declared field subspace".to_string()
            })?;
            rebased.add_term(mask, coordinates);
        }
        Ok(rebased.split(basis.len() as u32, n_vars))
    }
}

// ── The summation polynomials, on words ────────────────────────────

/// `S_3(x_1, x_2, x_3) = (x_1 + x_2)² x_3² + x_1 x_2 x_3 + (x_1 x_2)² + b`
/// on `Gf2` words, the same formula
/// [`binary_semaev_s3`](crate::cryptanalysis::binary_semaev::binary_semaev_s3)
/// evaluates.
pub fn semaev_s3_word(gf: &Gf2, b: u64, x1: u64, x2: u64, x3: u64) -> u64 {
    let sum12_sq = gf.sqr(x1 ^ x2);
    let prod12 = gf.mul(x1, x2);
    gf.mul(sum12_sq, gf.sqr(x3)) ^ gf.mul(prod12, x3) ^ gf.sqr(prod12) ^ b
}

/// `S_4 = Res_X(S_3(x_1, x_2, X), S_3(x_3, x_4, X))` on `Gf2` words,
/// the same resultant formula
/// [`binary_semaev_s4`](crate::cryptanalysis::binary_semaev::binary_semaev_s4)
/// evaluates: with `S_3(x_i, x_j, X) = A X² + B X + C`,
/// `Res = (A_1 C_2 + A_2 C_1)² + (A_1 B_2 + A_2 B_1)(B_1 C_2 + B_2 C_1)`.
pub fn semaev_s4_word(gf: &Gf2, b: u64, x1: u64, x2: u64, x3: u64, x4: u64) -> u64 {
    let (a1, b1, c1) = s3_in_x3_word(gf, b, x1, x2);
    let (a2, b2, c2) = s3_in_x3_word(gf, b, x3, x4);
    let t1 = gf.sqr(gf.mul(a1, c2) ^ gf.mul(a2, c1));
    let t2 = gf.mul(
        gf.mul(a1, b2) ^ gf.mul(a2, b1),
        gf.mul(b1, c2) ^ gf.mul(b2, c1),
    );
    t1 ^ t2
}

fn s3_in_x3_word(gf: &Gf2, b: u64, x1: u64, x2: u64) -> (u64, u64, u64) {
    let a = gf.sqr(x1 ^ x2);
    let bb = gf.mul(x1, x2);
    let c = gf.sqr(bb) ^ b;
    (a, bb, c)
}

// ── The descent ────────────────────────────────────────────────────

/// A descended system: `n` boolean equations in `m·n'` variables, with
/// bit `i·n' + k` of a point standing for `v_{i,k}`, exactly as the
/// truth-table descent numbers them.
#[derive(Clone, Debug)]
pub struct SymbolicDescent {
    pub n: u32,
    pub n_prime: u32,
    pub summands: u32,
    pub n_vars: usize,
    pub equations: Vec<F2BoolPoly>,
    pub v_basis: Vec<u64>,
    /// Monomials of the polynomial over `F_{2^n}` before it was split
    /// into coordinates: the size of the symbolic object.
    pub field_monomials: usize,
}

impl SymbolicDescent {
    /// The abscissae a solution names, one word per summand.
    pub fn lift(&self, v: u64) -> Vec<u64> {
        let np = self.n_prime as usize;
        (0..self.summands as usize)
            .map(|i| {
                (0..np)
                    .filter(|&k| (v >> (i * np + k)) & 1 == 1)
                    .fold(0u64, |acc, k| acc ^ self.v_basis[k])
            })
            .collect()
    }
}

/// Product edge lifted in every cubic link of a left-chained `S_3`
/// presentation.  For a link `S_3(x_a, x_b, x_c)`, the auxiliary is
/// constrained to the selected product and the remaining equation is
/// quadratic after Weil descent.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ChainEdgeLift {
    Ab,
    AbCompressed,
    Ac,
    Bc,
}

impl ChainEdgeLift {
    pub fn parse(name: &str) -> Result<Self, String> {
        match name {
            "edge-ab" => Ok(Self::Ab),
            "edge-ab-compressed" => Ok(Self::AbCompressed),
            "edge-ac" => Ok(Self::Ac),
            "edge-bc" => Ok(Self::Bc),
            other => Err(format!(
                "unknown chained S3 presentation `{other}`; use edge-ab, edge-ab-compressed, edge-ac or edge-bc"
            )),
        }
    }

    pub fn name(self) -> &'static str {
        match self {
            Self::Ab => "edge-ab",
            Self::AbCompressed => "edge-ab-compressed",
            Self::Ac => "edge-ac",
            Self::Bc => "edge-bc",
        }
    }
}

/// A left chain of `S_3` links with one product lift on every link whose
/// three abscissae are unknown.  The final target-anchored link stays in its
/// already-quadratic direct form.
#[derive(Clone, Debug)]
pub struct ChainEdgeDescent {
    pub n_prime: u32,
    pub summands: u32,
    pub n_vars: usize,
    pub equations: Vec<F2BoolPoly>,
    pub v_basis: Vec<u64>,
    /// Field bases used for the lifted products, in chain order.  The
    /// compressed leaf-product arm uses the exact product space `V·V` for
    /// the first link; the matched controls use the full field.
    pub lift_bases: Vec<Vec<u64>>,
    pub field_monomials: usize,
    pub edge: ChainEdgeLift,
}

impl ChainEdgeDescent {
    /// The factor-base abscissae named by a solution.  Intermediate and
    /// product-lift variables follow the leaf variables and are intentionally
    /// omitted here.
    pub fn lift(&self, v: u64) -> Vec<u64> {
        let np = self.n_prime as usize;
        (0..self.summands as usize)
            .map(|i| {
                (0..np)
                    .filter(|&k| (v >> (i * np + k)) & 1 == 1)
                    .fold(0u64, |acc, k| acc ^ self.v_basis[k])
            })
            .collect()
    }
}

/// Coordinates of `word` in an independent field basis, or `None` when the
/// word is outside its span.
fn coordinates_in_basis(mut word: u64, basis: &[u64]) -> Option<u64> {
    let mut pivots = [(0u64, 0u64); 64];
    for (i, &element) in basis.iter().enumerate() {
        let mut row = element;
        let mut coordinates = 1u64 << i;
        while row != 0 {
            let pivot = (63 - row.leading_zeros()) as usize;
            if pivots[pivot].0 == 0 {
                pivots[pivot] = (row, coordinates);
                break;
            }
            row ^= pivots[pivot].0;
            coordinates ^= pivots[pivot].1;
        }
    }
    let mut coordinates = 0u64;
    while word != 0 {
        let pivot = (63 - word.leading_zeros()) as usize;
        if pivots[pivot].0 == 0 {
            return None;
        }
        word ^= pivots[pivot].0;
        coordinates ^= pivots[pivot].1;
    }
    Some(coordinates)
}

/// A deterministic basis for the span of all pairwise products of two field
/// subspaces. Each inserted row is reduced against earlier pivots, so the
/// returned words are independent and span exactly the product space.
fn product_space_basis(gf: &Gf2, left: &[u64], right: &[u64]) -> Vec<u64> {
    let mut pivots = [0u64; 64];
    let mut basis = Vec::new();
    for &a in left {
        for &b in right {
            let mut word = gf.mul(a, b);
            while word != 0 {
                let pivot = (63 - word.leading_zeros()) as usize;
                if pivots[pivot] == 0 {
                    pivots[pivot] = word;
                    basis.push(word);
                    break;
                }
                word ^= pivots[pivot];
            }
        }
    }
    basis
}

/// Build the support-aware chained presentation used by the ECC2K-130
/// mixed-edge lead.  Variables are ordered as all factor-base leaves, all
/// full-field intermediates, then the coordinates of each lifted product in
/// its declared field basis.
pub fn descend_chain_edge(
    gf: &Gf2,
    curve_b: u64,
    x_r: u64,
    v_basis: &[u64],
    summands: u32,
    edge: ChainEdgeLift,
) -> Result<ChainEdgeDescent, String> {
    if !(2..=9).contains(&summands) {
        return Err(format!(
            "the chained S3 descent takes 2..=9 summands, not {summands}"
        ));
    }
    let np = v_basis.len() as u32;
    let cubic_links = summands - 2;
    let full_basis: Vec<u64> = (0..gf.n).map(|j| 1u64 << j).collect();
    let lift_bases: Vec<Vec<u64>> = (0..cubic_links)
        .map(|link| {
            if edge == ChainEdgeLift::AbCompressed {
                let left = if link == 0 { v_basis } else { &full_basis };
                product_space_basis(gf, left, v_basis)
            } else {
                full_basis.clone()
            }
        })
        .collect();
    let lift_vars: u32 = lift_bases.iter().map(|basis| basis.len() as u32).sum();
    let n_vars = summands * np + cubic_links * gf.n + lift_vars;
    if np == 0 || lift_bases.iter().any(Vec::is_empty) || n_vars > MAX_VARS {
        return Err(format!(
            "the {} chained descent needs {summands}·{np} + {cubic_links}·{} + {lift_vars} = {n_vars} boolean variables; the monomial mask holds {MAX_VARS}",
            edge.name(),
            gf.n
        ));
    }

    let leaves: Vec<FieldBoolPoly> = (0..summands)
        .map(|i| FieldBoolPoly::linear(i * np, v_basis))
        .collect();
    let intermediate_offset = summands * np;
    let lift_offset = intermediate_offset + cubic_links * gf.n;
    let mut lift_offsets = Vec::with_capacity(cubic_links as usize);
    let mut next_lift_offset = lift_offset;
    for basis in &lift_bases {
        lift_offsets.push(next_lift_offset);
        next_lift_offset += basis.len() as u32;
    }
    let mut parts = Vec::with_capacity((2 * cubic_links + 1) as usize);
    let mut current = leaves[0].clone();

    for k in 1..summands {
        let link = k - 1;
        let last = k == summands - 1;
        let next = if last {
            FieldBoolPoly::constant(x_r)
        } else {
            FieldBoolPoly::linear(intermediate_offset + link * gf.n, &full_basis)
        };
        let leaf = &leaves[k as usize];
        if last {
            parts.push((s3_poly(gf, curve_b, &current, leaf, &next), None));
        } else {
            let lifted =
                FieldBoolPoly::linear(lift_offsets[link as usize], &lift_bases[link as usize]);
            let (product, square_one, square_two, remaining) = match edge {
                ChainEdgeLift::Ab | ChainEdgeLift::AbCompressed => (
                    current.mul(leaf, gf),
                    current.mul(&next, gf).sqr(gf),
                    leaf.mul(&next, gf).sqr(gf),
                    &next,
                ),
                ChainEdgeLift::Ac => (
                    current.mul(&next, gf),
                    current.mul(leaf, gf).sqr(gf),
                    leaf.mul(&next, gf).sqr(gf),
                    leaf,
                ),
                ChainEdgeLift::Bc => (
                    leaf.mul(&next, gf),
                    current.mul(leaf, gf).sqr(gf),
                    current.mul(&next, gf).sqr(gf),
                    &current,
                ),
            };
            parts.push((lifted.add(&product), Some(link as usize)));
            parts.push((
                lifted
                    .sqr(gf)
                    .add(&square_one)
                    .add(&square_two)
                    .add(&lifted.mul(remaining, gf))
                    .add(&FieldBoolPoly::constant(curve_b)),
                None,
            ));
        }
        current = next;
    }

    let field_monomials = parts.iter().map(|(part, _)| part.len()).sum();
    let mut equations = Vec::with_capacity(parts.len() * gf.n as usize);
    for (part, product_link) in &parts {
        if let Some(link) = product_link {
            equations.extend(part.split_in_basis(&lift_bases[*link], n_vars as usize)?);
        } else {
            equations.extend(part.split(gf.n, n_vars as usize));
        }
    }
    Ok(ChainEdgeDescent {
        n_prime: np,
        summands,
        n_vars: n_vars as usize,
        equations,
        v_basis: v_basis.to_vec(),
        lift_bases,
        field_monomials,
        edge,
    })
}

/// Descend `S_{m+1}(x_1, …, x_m, x_R) = 0` with every `x_i` in the span
/// of `v_basis`, for `summands ∈ {2, 3}`.  Fails only on a dimension
/// the monomial mask cannot hold.
pub fn descend(
    gf: &Gf2,
    b: u64,
    x_r: u64,
    v_basis: &[u64],
    summands: u32,
) -> Result<SymbolicDescent, String> {
    let n_prime = v_basis.len() as u32;
    if !(2..=3).contains(&summands) {
        return Err(format!(
            "the symbolic descent takes 2 or 3 summands, not {summands}"
        ));
    }
    if n_prime == 0 || n_prime > max_n_prime(summands) {
        return Err(format!(
            "a subspace of dimension {n_prime} at {summands} summands needs {} boolean variables; \
             the monomial mask holds {MAX_VARS}",
            n_prime * summands
        ));
    }
    let n_vars = (summands * n_prime) as usize;
    #[cfg(feature = "s3-direct-coefficients")]
    if summands == 2 {
        let (equations, field_monomials) = s3_direct_equations(gf, b, x_r, v_basis);
        return Ok(SymbolicDescent {
            n: gf.n,
            n_prime,
            summands,
            n_vars,
            equations,
            v_basis: v_basis.to_vec(),
            field_monomials,
        });
    }
    let poly = match summands {
        2 => s3_symbolic(gf, b, x_r, v_basis),
        _ => s4_symbolic(gf, b, x_r, v_basis),
    };
    Ok(SymbolicDescent {
        n: gf.n,
        n_prime,
        summands,
        n_vars,
        equations: poly.split(gf.n, n_vars),
        v_basis: v_basis.to_vec(),
        field_monomials: poly.len(),
    })
}

/// The balanced representation split of `S_5` (four summands):
///
/// ```text
/// S_3(x_1, x_2, u) = 0,   S_3(x_3, x_4, w) = 0,   S_3(u, w, x_R) = 0
/// ```
///
/// with `x_1..x_4` in the span of `v_basis` (`n'` bits each) and the two
/// intermediates `u, w` restricted to the span of `inter_basis` (`ℓ'`
/// bits each).  Variables are numbered `x_1, …, x_4, u, w`, `n'` bits for
/// each `x_i` then `ℓ'` for each intermediate; [`SplitDescent::lift`]
/// returns the four summand abscissae.
///
/// This is the representation technique of Delaplace–May (2019) in the
/// binary Weil-descent setting: the intermediate `P_1 + P_2` is kept only
/// when its abscissa lies in a structured subset.  With `inter_basis`
/// spanning all of `F_{2^n}` it is the plain chained descent of `S_5`
/// (the control); with `ℓ' < n` it fixes `n − ℓ'` linear conditions on
/// each intermediate, i.e. the hybrid approach on the intermediates.
/// `3n` equations in `4n' + 2ℓ'` unknowns, at most cubic (squaring is
/// linear, so `S_3`'s `x_1 x_2 x_3` is the only cubic term).
pub fn descend_split4(
    gf: &Gf2,
    b: u64,
    x_r: u64,
    v_basis: &[u64],
    inter_basis: &[u64],
) -> Result<SplitDescent, String> {
    let np = v_basis.len() as u32;
    let nl = inter_basis.len() as u32;
    let n_vars = 4 * np + 2 * nl;
    if np == 0 || nl == 0 || n_vars > MAX_VARS {
        return Err(format!(
            "the split descent needs 4·{np} + 2·{nl} = {n_vars} boolean variables; \
             the monomial mask holds {MAX_VARS}"
        ));
    }
    let x: Vec<FieldBoolPoly> = (0..4)
        .map(|i| FieldBoolPoly::linear(i * np, v_basis))
        .collect();
    let u = FieldBoolPoly::linear(4 * np, inter_basis);
    let w = FieldBoolPoly::linear(4 * np + nl, inter_basis);
    let xr = FieldBoolPoly::constant(x_r);
    let parts = [
        s3_poly(gf, b, &x[0], &x[1], &u),
        s3_poly(gf, b, &x[2], &x[3], &w),
        s3_poly(gf, b, &u, &w, &xr),
    ];
    let mut equations = Vec::with_capacity(3 * gf.n as usize);
    let mut field_monomials = 0;
    for p in &parts {
        field_monomials += p.len();
        equations.extend(p.split(gf.n, n_vars as usize));
    }
    Ok(SplitDescent {
        n_prime: np,
        inter_dim: nl,
        n_vars: n_vars as usize,
        equations,
        v_basis: v_basis.to_vec(),
        field_monomials,
    })
}

/// `S_3(p, q, r) = (p + q)² r² + p q r + (p q)² + b` on boolean-ring
/// polynomials, term for term [`semaev_s3_word`].
fn s3_poly(
    gf: &Gf2,
    b: u64,
    p: &FieldBoolPoly,
    q: &FieldBoolPoly,
    r: &FieldBoolPoly,
) -> FieldBoolPoly {
    let pq = p.mul(q, gf);
    let t1 = p.add(q).sqr(gf).mul(&r.sqr(gf), gf);
    let t2 = pq.mul(r, gf);
    let t3 = pq.sqr(gf).add(&FieldBoolPoly::constant(b));
    t1.add(&t2).add(&t3)
}

/// A descended split system ([`descend_split4`]).
#[derive(Clone, Debug)]
pub struct SplitDescent {
    pub n_prime: u32,
    pub inter_dim: u32,
    pub n_vars: usize,
    pub equations: Vec<F2BoolPoly>,
    pub v_basis: Vec<u64>,
    pub field_monomials: usize,
}

impl SplitDescent {
    /// The four summand abscissae a solution names.
    pub fn lift(&self, v: u64) -> Vec<u64> {
        let np = self.n_prime as usize;
        (0..4)
            .map(|i| {
                (0..np)
                    .filter(|&k| (v >> (i * np + k)) & 1 == 1)
                    .fold(0u64, |acc, k| acc ^ self.v_basis[k])
            })
            .collect()
    }
}

/// Direct coefficients of the same quadratic S3 polynomial. All cross masks
/// precede the linear masks; within each degree ascending masks are canonical.
#[cfg(any(test, feature = "s3-direct-coefficients"))]
fn s3_direct_equations(gf: &Gf2, b: u64, x_r: u64, basis: &[u64]) -> (Vec<F2BoolPoly>, usize) {
    let np = basis.len();
    let n_vars = 2 * np;
    let capacity = (np * np + 2 * np).div_ceil(2);
    let mut equations: Vec<F2BoolPoly> = (0..gf.n)
        .map(|_| F2BoolPoly {
            terms: Vec::with_capacity(capacity),
            n_vars,
        })
        .collect();
    let mut count = 0;
    let mut emit = |mask: u64, coefficient: u64| {
        if coefficient == 0 {
            return;
        }
        count += 1;
        let monomial = F2BoolMono::from_mask(mask);
        let mut bits = coefficient;
        while bits != 0 {
            let bit = bits.trailing_zeros();
            if bit < gf.n {
                equations[bit as usize].terms.push(monomial);
            }
            bits &= bits - 1;
        }
    };
    let squares: Vec<u64> = basis.iter().map(|&v| gf.sqr(v)).collect();
    let mut cross = vec![0u64; np * np];
    // One coefficient per unordered basis pair, used for both cross masks.
    for j in 0..np {
        for i in 0..=j {
            let product = if i == j {
                squares[i]
            } else {
                gf.mul(basis[i], basis[j])
            };
            let coefficient = gf.mul(product, x_r) ^ gf.sqr(product);
            cross[j * np + i] = coefficient;
            cross[i * np + j] = coefficient;
        }
    }
    for j in 0..np {
        for i in 0..np {
            emit((1u64 << i) | (1u64 << (np + j)), cross[j * np + i]);
        }
    }
    let x_r_squared = gf.sqr(x_r);
    let linear: Vec<u64> = squares.iter().map(|&v| gf.mul(v, x_r_squared)).collect();
    for offset in [0, np] {
        for (i, &coefficient) in linear.iter().enumerate() {
            emit(1u64 << (offset + i), coefficient);
        }
    }
    emit(0, b);
    (equations, count)
}

/// `S_3(x_1, x_2, x_R)` with `x_1`, `x_2` linear forms, term for term
/// the formula [`semaev_s3_word`] evaluates.
fn s3_symbolic(gf: &Gf2, b: u64, x_r: u64, v_basis: &[u64]) -> FieldBoolPoly {
    let np = v_basis.len() as u32;
    let x1 = FieldBoolPoly::linear(0, v_basis);
    let x2 = FieldBoolPoly::linear(np, v_basis);
    let sum12_sq = x1.add(&x2).sqr(gf);
    let prod12 = x1.mul(&x2, gf);
    let t1 = sum12_sq.scale(gf.sqr(x_r), gf);
    let t2 = prod12.scale(x_r, gf);
    let t3 = prod12.sqr(gf).add(&FieldBoolPoly::constant(b));
    t1.add(&t2).add(&t3)
}

/// `S_4(x_1, x_2, x_3, x_R)` with `x_1`, `x_2`, `x_3` linear forms,
/// term for term the resultant [`semaev_s4_word`] evaluates.
fn s4_symbolic(gf: &Gf2, b: u64, x_r: u64, v_basis: &[u64]) -> FieldBoolPoly {
    let np = v_basis.len() as u32;
    let x1 = FieldBoolPoly::linear(0, v_basis);
    let x2 = FieldBoolPoly::linear(np, v_basis);
    let x3 = FieldBoolPoly::linear(2 * np, v_basis);
    let x4 = FieldBoolPoly::constant(x_r);
    let bconst = FieldBoolPoly::constant(b);
    let s3_in_x3 = |p: &FieldBoolPoly, q: &FieldBoolPoly| {
        let a = p.add(q).sqr(gf);
        let bb = p.mul(q, gf);
        let c = bb.sqr(gf).add(&bconst);
        (a, bb, c)
    };
    let (a1, b1, c1) = s3_in_x3(&x1, &x2);
    let (a2, b2, c2) = s3_in_x3(&x3, &x4);
    let t1 = a1.mul(&c2, gf).add(&a2.mul(&c1, gf)).sqr(gf);
    let left = a1.mul(&b2, gf).add(&a2.mul(&b1, gf));
    let right = b1.mul(&c2, gf).add(&b2.mul(&c1, gf));
    t1.add(&left.mul(&right, gf))
}

// ── Tests ──────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::ic_boundary::random_binary_instance;
    use crate::cryptanalysis::ic_descent_degrees::curve_of;
    use crate::cryptanalysis::pq_descent::{weil_descend_s3, weil_descend_s4};
    use rand::rngs::StdRng;
    use rand::{Rng, SeedableRng};

    #[test]
    fn split4_equations_are_the_three_s3_words_bit_for_bit() {
        let mut rng = StdRng::seed_from_u64(0x5917_2026_1120);
        for n in [11u32, 17, 21] {
            let irr =
                crate::cryptanalysis::koblitz_index_calculus::find_irreducible_sparse(n).unwrap();
            let gf = Gf2::new(&irr);
            for (np, nl) in [(3usize, 2usize), (4, 5), (5, 11)] {
                let v_basis: Vec<u64> = (0..np).map(|_| rng.gen::<u64>() & gf.mask).collect();
                let i_basis: Vec<u64> = (0..nl).map(|_| rng.gen::<u64>() & gf.mask).collect();
                let b = rng.gen::<u64>() & gf.mask;
                let x_r = rng.gen::<u64>() & gf.mask;
                let sys = descend_split4(&gf, b, x_r, &v_basis, &i_basis).unwrap();
                assert_eq!(sys.equations.len(), 3 * n as usize);
                let span = |bits: u64, basis: &[u64]| {
                    (0..basis.len())
                        .filter(|&k| (bits >> k) & 1 == 1)
                        .fold(0u64, |acc, k| acc ^ basis[k])
                };
                for _ in 0..200 {
                    let v = rng.gen::<u64>() & ((1u64 << sys.n_vars) - 1);
                    let xs = sys.lift(v);
                    let u = span(v >> (4 * np), &i_basis);
                    let w = span(v >> (4 * np + nl), &i_basis);
                    let words = [
                        semaev_s3_word(&gf, b, xs[0], xs[1], u),
                        semaev_s3_word(&gf, b, xs[2], xs[3], w),
                        semaev_s3_word(&gf, b, u, w, x_r),
                    ];
                    for (part, word) in words.iter().enumerate() {
                        for j in 0..n as usize {
                            assert_eq!(
                                sys.equations[part * n as usize + j].eval(v),
                                ((word >> j) & 1) as u32,
                                "n={n} np={np} nl={nl} part={part} bit={j}"
                            );
                        }
                    }
                }
            }
        }
    }

    #[test]
    fn chained_edge_lifts_are_exact_quadratic_presentations() {
        let mut rng = StdRng::seed_from_u64(0xED6E_2026_1127);
        for (n, np, summands) in [(11u32, 3u32, 3u32), (13, 3, 4)] {
            let irr =
                crate::cryptanalysis::koblitz_index_calculus::find_irreducible_sparse(n).unwrap();
            let gf = Gf2::new(&irr);
            let basis: Vec<u64> = (0..np).map(|j| 1u64 << j).collect();
            let leaf_mask = (1u64 << np) - 1;
            let cubic_links = summands - 2;
            for edge in [
                ChainEdgeLift::Ab,
                ChainEdgeLift::AbCompressed,
                ChainEdgeLift::Ac,
                ChainEdgeLift::Bc,
            ] {
                for _ in 0..80 {
                    let leaves: Vec<u64> = (0..summands)
                        .map(|_| rng.gen::<u64>() & leaf_mask)
                        .collect();
                    let intermediates: Vec<u64> = (0..cubic_links)
                        .map(|_| rng.gen::<u64>() & gf.mask)
                        .collect();
                    let x_r = rng.gen::<u64>() & gf.mask;
                    let curve_b = rng.gen::<u64>() & gf.mask;
                    let sys =
                        descend_chain_edge(&gf, curve_b, x_r, &basis, summands, edge).unwrap();
                    assert!(sys
                        .equations
                        .iter()
                        .all(|p| p.terms.iter().all(|t| t.degree() <= 2)));

                    let intermediate_offset = summands * np;
                    let lift_offset = intermediate_offset + cubic_links * n;
                    let mut assignment = 0u64;
                    for (i, &x) in leaves.iter().enumerate() {
                        assignment |= x << (i as u32 * np);
                    }
                    let mut words = Vec::new();
                    let mut next_lift_offset = lift_offset;
                    for link in 0..cubic_links {
                        let a = if link == 0 {
                            leaves[0]
                        } else {
                            intermediates[link as usize - 1]
                        };
                        let b = leaves[link as usize + 1];
                        let c = intermediates[link as usize];
                        let w = match edge {
                            ChainEdgeLift::Ab | ChainEdgeLift::AbCompressed => gf.mul(a, b),
                            ChainEdgeLift::Ac => gf.mul(a, c),
                            ChainEdgeLift::Bc => gf.mul(b, c),
                        };
                        assignment |= c << (intermediate_offset + link * n);
                        let lift_basis = &sys.lift_bases[link as usize];
                        assignment |=
                            coordinates_in_basis(w, lift_basis).unwrap() << next_lift_offset;
                        next_lift_offset += lift_basis.len() as u32;
                        words.push(semaev_s3_word(&gf, curve_b, a, b, c));
                    }
                    let final_a = intermediates.last().copied().unwrap_or(leaves[0]);
                    words.push(semaev_s3_word(
                        &gf,
                        curve_b,
                        final_a,
                        *leaves.last().unwrap(),
                        x_r,
                    ));

                    assert_eq!(sys.lift(assignment), leaves);
                    if cubic_links > 0 {
                        let corrupted_lift = assignment ^ (1u64 << lift_offset);
                        assert!(sys.equations[..sys.lift_bases[0].len()]
                            .iter()
                            .any(|equation| equation.eval(corrupted_lift) != 0));
                    }
                    let mut equation_offset = 0usize;
                    for link in 0..cubic_links as usize {
                        let constraint_dimension = sys.lift_bases[link].len();
                        for j in 0..constraint_dimension {
                            assert_eq!(sys.equations[equation_offset + j].eval(assignment), 0);
                        }
                        let residual = equation_offset + constraint_dimension;
                        for j in 0..n as usize {
                            assert_eq!(
                                sys.equations[residual + j].eval(assignment),
                                ((words[link] >> j) & 1) as u32,
                                "n={n} m={summands} edge={} link={link} bit={j}",
                                edge.name()
                            );
                        }
                        equation_offset = residual + n as usize;
                    }
                    for j in 0..n as usize {
                        assert_eq!(
                            sys.equations[equation_offset + j].eval(assignment),
                            ((words.last().unwrap() >> j) & 1) as u32
                        );
                    }
                }
            }
        }
    }

    #[test]
    fn direct_s3_matches_generic_coefficients_in_canonical_order() {
        let mut rng = StdRng::seed_from_u64(0x5333_2026_1115);
        for n in [7, 15, 31, 53, 63] {
            let irr =
                crate::cryptanalysis::koblitz_index_calculus::find_irreducible_sparse(n).unwrap();
            let gf = Gf2::new(&irr);
            for np in [1usize, 2, 4, 8, 16, 24, 32] {
                for variant in 0..4 {
                    let mut basis: Vec<u64> = (0..np).map(|_| rng.gen::<u64>() & gf.mask).collect();
                    if variant == 1 {
                        basis.fill(0);
                    }
                    if variant == 2 {
                        basis.fill(1);
                    }
                    let x_r = if variant == 3 {
                        0
                    } else {
                        rng.gen::<u64>() & gf.mask
                    };
                    let b = rng.gen::<u64>() & gf.mask;
                    let reference = s3_symbolic(&gf, b, x_r, &basis);
                    let expected = reference.split(n, 2 * np);
                    let (actual, count) = s3_direct_equations(&gf, b, x_r, &basis);
                    assert_eq!(count, reference.len(), "field monomial count n={n} np={np}");
                    assert_eq!(actual.len(), expected.len());
                    for (a, e) in actual.iter().zip(&expected) {
                        assert_eq!(a.n_vars, e.n_vars);
                        assert_eq!(
                            a.terms, e.terms,
                            "ordered coefficients n={n} np={np} variant={variant}"
                        );
                    }
                }
            }
        }
    }

    fn standard_basis(n_prime: u32) -> Vec<u64> {
        (0..n_prime).map(|k| 1u64 << k).collect()
    }

    fn sorted_masks(p: &F2BoolPoly) -> Vec<u64> {
        let mut v: Vec<u64> = p.terms.iter().map(|t| t.mask).collect();
        v.sort_unstable();
        v
    }

    /// **`split` lists every equation as `from_monos` does**, term for
    /// term: one sort of the whole polynomial, dealt out by coefficient
    /// bit, leaves each equation in canonical order (the descent checks
    /// below compare the equations only as sets of monomials).
    #[test]
    fn split_lists_each_equation_in_canonical_order() {
        let mut rng = StdRng::seed_from_u64(29);
        for trial in 0..300u32 {
            // Every fourth polynomial reaches past the 57 variables a
            // packed key covers; coefficient bits at or past `n` are
            // dropped.
            let span = if trial % 4 == 3 {
                u64::MAX
            } else {
                (1u64 << (1 + trial % 40)) - 1
            };
            let n = 1 + trial % 64;
            let mut p = FieldBoolPoly::default();
            for _ in 0..rng.gen_range(0..400) {
                p.add_term(rng.gen::<u64>() & rng.gen::<u64>() & span, rng.gen());
            }
            let expected: Vec<F2BoolPoly> = (0..n)
                .map(|j| {
                    let monos = p
                        .terms
                        .iter()
                        .filter(|&(_, &c)| (c >> j) & 1 == 1)
                        .map(|(&m, _)| F2BoolMono::from_mask(m))
                        .collect();
                    F2BoolPoly::from_monos(monos, 64)
                })
                .collect();
            assert_eq!(p.split(n, 64), expected, "trial {trial}");
        }
    }

    /// **The word formulas agree with the `F2mElement` ones**, so a
    /// descent checked against them is checked against the
    /// repository's summation polynomials.
    #[test]
    fn the_word_formulas_are_the_repository_formulas() {
        use crate::cryptanalysis::binary_semaev::{binary_semaev_s3, binary_semaev_s4};
        let inst = random_binary_instance(11, 5, 1 << 20).expect("a curve at n = 11");
        let curve = curve_of(&inst).unwrap();
        let gf = &inst.gf;
        let mut rng = StdRng::seed_from_u64(3);
        for _ in 0..64 {
            let xs: Vec<u64> = (0..4).map(|_| rng.gen::<u64>() & gf.mask).collect();
            let es: Vec<_> = xs.iter().map(|&x| gf.to_element(x)).collect();
            let s3 = binary_semaev_s3(&es[0], &es[1], &es[2], &curve.b, &curve.irreducible);
            assert_eq!(
                gf.from_element(&s3),
                semaev_s3_word(gf, inst.b, xs[0], xs[1], xs[2])
            );
            let s4 = binary_semaev_s4(&es[0], &es[1], &es[2], &es[3], &curve.b, &curve.irreducible);
            assert_eq!(
                gf.from_element(&s4),
                semaev_s4_word(gf, inst.b, xs[0], xs[1], xs[2], xs[3])
            );
        }
    }

    /// **The symbolic descent is the truth-table descent, monomial for
    /// monomial**, at every dimension the truth table can still reach:
    /// the algebraic normal form of a boolean function is unique, so
    /// the two constructions of the same function must coincide
    /// exactly.  This is the cross-check `AGENTS.md` asks of anything
    /// that replaces a measured oracle.
    #[test]
    fn the_symbolic_descent_is_the_truth_table_descent() {
        let mut rng = StdRng::seed_from_u64(11);
        for &(n, seed) in &[(7u32, 1u64), (9, 2), (11, 3), (13, 4)] {
            let inst = random_binary_instance(n, seed, 1 << 20).expect("a curve");
            let curve = curve_of(&inst).unwrap();
            let gf = &inst.gf;
            for n_prime in 2..=5u32 {
                let words = standard_basis(n_prime);
                let elems: Vec<_> = words.iter().map(|&w| gf.to_element(w)).collect();
                for _ in 0..3 {
                    let x_r = rng.gen::<u64>() & gf.mask;
                    let x_r_el = gf.to_element(x_r);

                    let table = weil_descend_s3(&curve, &x_r_el, &elems);
                    let sym = descend(gf, inst.b, x_r, &words, 2).unwrap();
                    assert_eq!(sym.n_vars, table.n_vars);
                    assert_eq!(sym.equations.len(), table.equations.len());
                    for (j, (a, b)) in sym.equations.iter().zip(&table.equations).enumerate() {
                        assert_eq!(
                            sorted_masks(a),
                            sorted_masks(b),
                            "S3 descent at n = {n}, n' = {n_prime}, equation {j} differs"
                        );
                    }

                    if n_prime <= 4 {
                        let table = weil_descend_s4(&curve, &x_r_el, &elems);
                        let sym = descend(gf, inst.b, x_r, &words, 3).unwrap();
                        assert_eq!(sym.n_vars, table.n_vars);
                        for (j, (a, b)) in sym.equations.iter().zip(&table.equations).enumerate() {
                            assert_eq!(
                                sorted_masks(a),
                                sorted_masks(b),
                                "S4 descent at n = {n}, n' = {n_prime}, equation {j} differs"
                            );
                        }
                    }
                }
            }
        }
    }

    /// **Past the truth table's reach the descent still evaluates
    /// correctly**: at `n' = 12` (24 variables) every equation, at
    /// random points of the subspace, gives the bit of `S_3` it stands
    /// for, and the lift inverts the encoding.
    #[test]
    fn the_descent_evaluates_correctly_past_the_old_cap() {
        let inst = random_binary_instance(17, 9, 1 << 20).expect("a curve at n = 17");
        let gf = &inst.gf;
        let words = standard_basis(12);
        let mut rng = StdRng::seed_from_u64(23);
        let x_r = rng.gen::<u64>() & gf.mask;
        let sys = descend(gf, inst.b, x_r, &words, 2).unwrap();
        assert_eq!(sys.n_vars, 24);
        assert!(sys
            .equations
            .iter()
            .all(|e| e.terms.iter().all(|t| t.degree() <= 2)));
        for _ in 0..2000 {
            let v = rng.gen::<u64>() & ((1u64 << 24) - 1);
            let xs = sys.lift(v);
            let direct = semaev_s3_word(gf, inst.b, xs[0], xs[1], x_r);
            for (j, eq) in sys.equations.iter().enumerate() {
                assert_eq!(
                    eq.eval(v) as u64,
                    (direct >> j) & 1,
                    "equation {j} at {v:#x}"
                );
            }
        }
        // Three summands at a dimension the truth table could not hold.
        let words = standard_basis(7);
        let sys = descend(gf, inst.b, x_r, &words, 3).unwrap();
        assert_eq!(sys.n_vars, 21);
        assert!(sys
            .equations
            .iter()
            .all(|e| e.terms.iter().all(|t| t.degree() <= 6)));
        for _ in 0..500 {
            let v = rng.gen::<u64>() & ((1u64 << 21) - 1);
            let xs = sys.lift(v);
            let direct = semaev_s4_word(gf, inst.b, xs[0], xs[1], xs[2], x_r);
            for (j, eq) in sys.equations.iter().enumerate() {
                assert_eq!(
                    eq.eval(v) as u64,
                    (direct >> j) & 1,
                    "S4 equation {j} at {v:#x}"
                );
            }
        }
    }

    /// The only cap left is the monomial mask, and it is refused, not
    /// asserted.
    #[test]
    fn the_cap_is_the_monomial_mask() {
        let inst = random_binary_instance(9, 1, 1 << 20).unwrap();
        assert_eq!(max_n_prime(2), 32);
        assert_eq!(max_n_prime(3), 21);
        assert!(descend(&inst.gf, inst.b, 3, &standard_basis(33), 2).is_err());
        assert!(descend(&inst.gf, inst.b, 3, &standard_basis(22), 3).is_err());
        assert!(descend(&inst.gf, inst.b, 3, &standard_basis(4), 4).is_err());
    }

    /// **`split` returns what the base revision's `split` returned**,
    /// equation for equation and term for term, on the polynomials the
    /// descent actually splits (`S_3` and `S_4` over random curves and
    /// bases) and on random ones with `n` up to and past the 64
    /// coefficient bits.  The reference is the base revision's body and
    /// its `from_monos`, copied verbatim.
    #[test]
    fn split_matches_the_base_revision() {
        fn base_from_monos(mut monos: Vec<F2BoolMono>, n_vars: usize) -> F2BoolPoly {
            monos.sort_unstable_by_key(|m| std::cmp::Reverse(mono_key(*m)));
            let mut out: Vec<F2BoolMono> = Vec::with_capacity(monos.len());
            for m in monos {
                if out.last() == Some(&m) {
                    out.pop(); // 1 + 1 = 0
                } else {
                    out.push(m);
                }
            }
            F2BoolPoly { terms: out, n_vars }
        }
        fn base_split(p: &FieldBoolPoly, n: u32, n_vars: usize) -> Vec<F2BoolPoly> {
            let mut monos: Vec<Vec<F2BoolMono>> = (0..n).map(|_| Vec::new()).collect();
            for (&m, &c) in &p.terms {
                let mut bits = c;
                while bits != 0 {
                    let j = bits.trailing_zeros();
                    if j < n {
                        monos[j as usize].push(F2BoolMono::from_mask(m));
                    }
                    bits &= bits - 1;
                }
            }
            monos
                .into_iter()
                .map(|ms| base_from_monos(ms, n_vars))
                .collect()
        }
        let mut rng = StdRng::seed_from_u64(0x5011);
        for &(n, seed) in &[(7u32, 1u64), (11, 2), (17, 3), (23, 4), (31, 5)] {
            // This compares field-polynomial splitting, not curve orders.
            // Retain every field/dimension without enumerating a 31-bit curve.
            let irr =
                crate::cryptanalysis::koblitz_index_calculus::find_irreducible_sparse(n).unwrap();
            let gf = &Gf2::new(&irr);
            let b = (StdRng::seed_from_u64(seed).gen::<u64>() & gf.mask) | 2;
            for np in [1u32, 2, 3, 5, 6, 9, 16] {
                let basis: Vec<u64> = (0..np).map(|_| rng.gen::<u64>() & gf.mask).collect();
                let x_r = rng.gen::<u64>() & gf.mask;
                let s3 = s3_symbolic(gf, b, x_r, &basis);
                let n_vars = 2 * np as usize;
                assert_eq!(s3.split(gf.n, n_vars), base_split(&s3, gf.n, n_vars));
                if np <= 6 {
                    let s4 = s4_symbolic(gf, b, x_r, &basis);
                    let n_vars = 3 * np as usize;
                    assert_eq!(s4.split(gf.n, n_vars), base_split(&s4, gf.n, n_vars));
                }
            }
        }
        for trial in 0..400u32 {
            let span = match trial % 5 {
                0 => u64::MAX,
                1 => (1u64 << 58) - 1,
                _ => (1u64 << (1 + trial % 57)) - 1,
            };
            let n = trial % 71;
            let mut p = FieldBoolPoly::default();
            for _ in 0..rng.gen_range(0..600) {
                p.add_term(rng.gen::<u64>() & rng.gen::<u64>() & span, rng.gen());
            }
            assert_eq!(p.split(n, 64), base_split(&p, n, 64), "trial {trial}");
        }
    }
}
