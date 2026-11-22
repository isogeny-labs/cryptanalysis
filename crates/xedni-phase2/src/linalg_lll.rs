//! Exact arbitrary-precision integer linear algebra, HNF saturation, modular
//! RREF, Zassenhaus lattice intersection, 2048-bit fixed-point LLL, and Babai CVP.

use num_bigint::BigInt;
use num_integer::Integer;
use num_rational::BigRational;
use num_traits::{One, Signed, ToPrimitive, Zero};

const HP_PREC: usize = 2048;

#[inline]
pub fn dot_bigint(a: &[BigInt], b: &[BigInt]) -> BigInt {
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

#[inline]
pub fn abs_bits(x: &BigInt) -> u64 {
    x.magnitude().bits()
}

#[inline]
pub fn max_vec_bits(v: &[BigInt]) -> u64 {
    v.iter().map(abs_bits).max().unwrap_or(0)
}

pub fn primitivize_vec(mut v: Vec<BigInt>) -> Vec<BigInt> {
    let g = v.iter().fold(BigInt::zero(), |acc, x| acc.gcd(x));
    if g > BigInt::one() {
        for x in &mut v {
            *x /= &g;
        }
    }
    if v.iter()
        .find(|x| !x.is_zero())
        .is_some_and(Signed::is_negative)
    {
        for x in &mut v {
            *x = -&*x;
        }
    }
    v
}

/// Exact fraction-free Bareiss determinant.
pub fn determinant_bareiss(mut matrix: Vec<Vec<BigInt>>) -> Result<BigInt, String> {
    let n = matrix.len();
    if n == 0 || matrix.iter().any(|row| row.len() != n) {
        return Err("determinant requires a nonempty square matrix".into());
    }
    if n == 1 {
        return Ok(matrix[0][0].clone());
    }
    let mut sign = BigInt::one();
    let mut previous_pivot = BigInt::one();
    for pivot_column in 0..n - 1 {
        let Some(pivot_row) = (pivot_column..n).find(|&row| !matrix[row][pivot_column].is_zero())
        else {
            return Ok(BigInt::zero());
        };
        if pivot_row != pivot_column {
            matrix.swap(pivot_row, pivot_column);
            sign = -sign;
        }
        let pivot = matrix[pivot_column][pivot_column].clone();
        for row in pivot_column + 1..n {
            for column in pivot_column + 1..n {
                let numerator = &matrix[row][column] * &pivot
                    - &matrix[row][pivot_column] * &matrix[pivot_column][column];
                let (quotient, remainder) = numerator.div_rem(&previous_pivot);
                if !remainder.is_zero() {
                    return Err("internal error: inexact Bareiss division".into());
                }
                matrix[row][column] = quotient;
            }
            matrix[row][pivot_column] = BigInt::zero();
        }
        previous_pivot = pivot;
    }
    Ok(sign * &matrix[n - 1][n - 1])
}

/// Exact rank over `Q` of an `nrows x ncols` integer matrix.
pub fn rank_over_q(rows: &[Vec<BigInt>], ncols: usize) -> Result<usize, String> {
    let kernel = integer_kernel_basis(rows, ncols)?;
    Ok(ncols.saturating_sub(kernel.len()))
}

/// Saturated integer basis of `{c in Z^ncols : rows * c = 0}` via unimodular column reduction.
pub fn integer_kernel_basis(
    rows: &[Vec<BigInt>],
    ncols: usize,
) -> Result<Vec<Vec<BigInt>>, String> {
    let nrows = rows.len();
    if rows.iter().any(|r| r.len() != ncols) {
        return Err("matrix row length mismatch".into());
    }
    let mut h: Vec<Vec<BigInt>> = rows.to_vec();
    let mut u: Vec<Vec<BigInt>> = (0..ncols)
        .map(|i| (0..ncols).map(|j| BigInt::from(i == j)).collect())
        .collect();
    let mut col = 0usize;
    for r in 0..nrows {
        if col >= ncols {
            break;
        }
        loop {
            let nonzero: Vec<usize> = (col..ncols).filter(|&j| !h[r][j].is_zero()).collect();
            if nonzero.len() <= 1 {
                break;
            }
            let pivot_col = *nonzero
                .iter()
                .min_by(|&&a, &&b| h[r][a].magnitude().cmp(h[r][b].magnitude()))
                .expect("nonempty");
            for &j in &nonzero {
                if j == pivot_col {
                    continue;
                }
                let q = h[r][j].div_floor(&h[r][pivot_col]);
                let q = if q.is_zero() {
                    if h[r][j].sign() == h[r][pivot_col].sign() {
                        BigInt::one()
                    } else {
                        BigInt::from(-1)
                    }
                } else {
                    q
                };
                for row_h in h.iter_mut().take(nrows) {
                    let delta = &q * &row_h[pivot_col];
                    row_h[j] -= delta;
                }
                for row_u in u.iter_mut().take(ncols) {
                    let delta = &q * &row_u[pivot_col];
                    row_u[j] -= delta;
                }
            }
        }
        let Some(pivot_col) = (col..ncols).find(|&j| !h[r][j].is_zero()) else {
            continue;
        };
        if pivot_col != col {
            for row_h in h.iter_mut().take(nrows) {
                row_h.swap(col, pivot_col);
            }
            for row_u in u.iter_mut().take(ncols) {
                row_u.swap(col, pivot_col);
            }
        }
        col += 1;
    }
    let mut basis = Vec::with_capacity(ncols.saturating_sub(col));
    for j in col..ncols {
        let vec: Vec<BigInt> = u.iter().take(ncols).map(|row_u| row_u[j].clone()).collect();
        if vec.iter().all(BigInt::is_zero) {
            return Err("internal error: zero unimodular kernel column".into());
        }
        if rows.iter().any(|row| !dot_bigint(row, &vec).is_zero()) {
            return Err("internal error: kernel column violates constraint".into());
        }
        basis.push(vec);
    }
    Ok(basis)
}

/// Row-Hermite basis of `rowspan_Z(rows)`.
pub fn row_hermite_basis(mut rows: Vec<Vec<BigInt>>, ncols: usize) -> Vec<Vec<BigInt>> {
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
pub fn intersect_full_rank_lattices(
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
    let hnf = row_hermite_basis(generators, r);
    if hnf.len() != r {
        return Err("internal error: intersected modular relation lattice lost full rank".into());
    }
    Ok(hnf)
}

#[inline]
fn hp_from_bigint(x: &BigInt, prec: usize) -> BigInt {
    x << prec
}

#[inline]
fn hp_mul(a: &BigInt, b: &BigInt, prec: usize) -> BigInt {
    (a * b) >> prec
}

#[inline]
fn hp_div(a: &BigInt, b: &BigInt, prec: usize) -> BigInt {
    if b.is_zero() {
        return BigInt::zero();
    }
    (a << prec) / b
}

fn hp_round(a: &BigInt, prec: usize) -> BigInt {
    let half: BigInt = BigInt::one() << (prec - 1);
    if a.is_negative() {
        let neg_a = -a.clone();
        -((&neg_a + &half) >> prec)
    } else {
        (a + &half) >> prec
    }
}

fn gram_schmidt_hp(basis: &[Vec<BigInt>], prec: usize) -> (Vec<BigInt>, Vec<Vec<BigInt>>) {
    let n = basis.len();
    let dim = if n > 0 { basis[0].len() } else { 0 };
    let mut bstar: Vec<Vec<BigInt>> = vec![vec![BigInt::zero(); dim]; n];
    let mut bstar_sq: Vec<BigInt> = vec![BigInt::zero(); n];
    let mut mu: Vec<Vec<BigInt>> = vec![vec![BigInt::zero(); n]; n];

    for i in 0..n {
        for k in 0..dim {
            bstar[i][k] = hp_from_bigint(&basis[i][k], prec);
        }
        for j in 0..i {
            if bstar_sq[j].is_zero() {
                continue;
            }
            let dot: BigInt = bstar[i]
                .iter()
                .zip(&bstar[j])
                .map(|(x, y)| hp_mul(x, y, prec))
                .sum();
            mu[i][j] = hp_div(&dot, &bstar_sq[j], prec);
            let mu_ij = mu[i][j].clone();
            let bstar_j = bstar[j].clone();
            for (slot, bjk) in bstar[i].iter_mut().zip(&bstar_j) {
                let sub = hp_mul(&mu_ij, bjk, prec);
                *slot -= sub;
            }
        }
        bstar_sq[i] = bstar[i].iter().map(|x| hp_mul(x, x, prec)).sum();
    }
    (bstar_sq, mu)
}

/// Fast exact stack-only LLL for `n <= 4, dim <= 4` when entries fit in `38` bits (`i128` exact).
fn try_lll_reduce_small_i128(basis: &mut [Vec<BigInt>], delta: f64) -> Option<()> {
    let n = basis.len();
    if n == 0 || n > 4 {
        return None;
    }
    let dim = basis[0].len();
    if dim == 0 || dim > 4 {
        return None;
    }
    let mut b = [[0i128; 4]; 4];
    for (i, row) in basis.iter().enumerate() {
        for (j, val) in row.iter().enumerate() {
            if abs_bits(val) > 38 {
                return None;
            }
            b[i][j] = val.to_i128()?;
        }
    }

    let gs = |mat: &[[i128; 4]; 4]| -> ([f64; 4], [[f64; 4]; 4]) {
        let mut bs = [[0.0f64; 4]; 4];
        let mut bsq = [0.0f64; 4];
        let mut mu = [[0.0f64; 4]; 4];
        for i in 0..n {
            for (slot, &val) in bs[i][..dim].iter_mut().zip(&mat[i][..dim]) {
                *slot = val as f64;
            }
            for j in 0..i {
                if bsq[j] <= 1e-18 {
                    continue;
                }
                let dot: f64 = bs[i][..dim]
                    .iter()
                    .zip(&bs[j][..dim])
                    .map(|(x, y)| x * y)
                    .sum();
                let m_ij = dot / bsq[j];
                mu[i][j] = m_ij;
                let bs_j = bs[j];
                for (slot, &bj) in bs[i][..dim].iter_mut().zip(&bs_j[..dim]) {
                    *slot -= m_ij * bj;
                }
            }
            bsq[i] = bs[i][..dim].iter().map(|x| x * x).sum();
        }
        (bsq, mu)
    };

    let (mut bsq, mut mu) = gs(&b);
    let mut k = 1usize;
    let mut guard = 0usize;
    while k < n {
        guard += 1;
        if guard > 4_000 {
            return None;
        }
        for j in (0..k).rev() {
            if mu[k][j].abs() > 0.500_000_1 {
                let q = mu[k][j].round() as i128;
                if q != 0 {
                    let bj = b[j];
                    for (slot, &bjc) in b[k][..dim].iter_mut().zip(&bj[..dim]) {
                        *slot = slot.checked_sub(q.checked_mul(bjc)?)?;
                    }
                    let qf = q as f64;
                    mu[k][j] -= qf;
                    let muj = mu[j];
                    for (slot, &mji) in mu[k][..j].iter_mut().zip(&muj[..j]) {
                        *slot -= qf * mji;
                    }
                }
            }
        }
        if bsq[k] >= (delta - mu[k][k - 1] * mu[k][k - 1]) * bsq[k - 1] {
            k += 1;
        } else {
            b.swap(k, k - 1);
            let (nbsq, nmu) = gs(&b);
            bsq = nbsq;
            mu = nmu;
            k = k.saturating_sub(1).max(1);
        }
    }

    for (i, row) in basis.iter_mut().enumerate() {
        for (j, slot) in row.iter_mut().enumerate() {
            *slot = BigInt::from(b[i][j]);
        }
    }
    Some(())
}

/// Adaptive high-precision fixed-point LLL reduction (`0.25 < delta < 1.0`, up to `2048`-bit precision).
pub fn lll_reduce_hp(basis: &mut [Vec<BigInt>], delta: f64) -> Result<(), &'static str> {
    if !(0.25 < delta && delta < 1.0) {
        return Err("delta must be in (1/4, 1)");
    }
    let n = basis.len();
    if n == 0 {
        return Ok(());
    }
    let dim = basis[0].len();
    if dim == 0 || basis.iter().any(|v| v.len() != dim) {
        return Err("basis vectors must be non-empty and uniform length");
    }
    if try_lll_reduce_small_i128(basis, delta).is_some() {
        return Ok(());
    }

    let max_b = basis.iter().map(|v| max_vec_bits(v)).max().unwrap_or(1) as usize;
    let prec = (max_b * (n + 2) / 2 + 128).clamp(160, HP_PREC);

    let max_iter = 500 * n * n * 8 + 10_000;
    let mut iter = 0usize;
    let delta_hp: BigInt = {
        let p = (delta * (1u64 << 53) as f64) as u64;
        let q = 1u64 << 53;
        (BigInt::from(p) << prec) / BigInt::from(q)
    };
    let half_hp: BigInt = BigInt::one() << (prec - 1);

    let (mut bstar_sq, mut mu) = gram_schmidt_hp(basis, prec);
    let mut k = 1usize;

    while k < n {
        iter += 1;
        if iter > max_iter {
            return Err("LLL exceeded iteration cap");
        }
        for j in (0..k).rev() {
            let mu_abs = if mu[k][j].is_negative() {
                -mu[k][j].clone()
            } else {
                mu[k][j].clone()
            };
            if mu_abs > half_hp {
                let q_bi = hp_round(&mu[k][j], prec);
                if q_bi.is_zero() {
                    continue;
                }
                let basis_j = basis[j].clone();
                for (bki, bji) in basis[k].iter_mut().zip(&basis_j) {
                    *bki -= &q_bi * bji;
                }
                let q_hp = hp_from_bigint(&q_bi, prec);
                mu[k][j] -= &q_hp;
                let mu_j = mu[j][..j].to_vec();
                for (mki, mji) in mu[k][..j].iter_mut().zip(&mu_j) {
                    let qmu = hp_mul(&q_hp, mji, prec);
                    *mki -= qmu;
                }
            }
        }
        let mu_sq = hp_mul(&mu[k][k - 1], &mu[k][k - 1], prec);
        let factor = &delta_hp - &mu_sq;
        let rhs = hp_mul(&factor, &bstar_sq[k - 1], prec);
        if bstar_sq[k] >= rhs {
            k += 1;
        } else {
            basis.swap(k, k - 1);
            let (new_bs, new_mu) = gram_schmidt_hp(basis, prec);
            bstar_sq = new_bs;
            mu = new_mu;
            k = k.saturating_sub(1).max(1);
        }
    }
    Ok(())
}

fn round_rational_nearest(r: &BigRational) -> BigInt {
    let num = r.numer();
    let den = r.denom();
    let doubled: BigInt = num * 2;
    let two_den: BigInt = den * 2;
    if doubled >= BigInt::zero() {
        (doubled + den) / two_den
    } else {
        let neg_num: BigInt = (-doubled) + den;
        let q: BigInt = neg_num / two_den;
        -q
    }
}

/// Exact `BigRational` Babai nearest-plane CVP returning a short representative of `particular + span_Z(basis)`.
pub fn babai_nearest_coset_rep(particular: &[BigInt], basis: &[Vec<BigInt>]) -> Vec<BigInt> {
    let dim = particular.len();
    let k = basis.len();
    if k == 0 {
        return particular.to_vec();
    }
    let mut bstar: Vec<Vec<BigRational>> = Vec::with_capacity(k);
    let mut bstar_sq: Vec<BigRational> = Vec::with_capacity(k);
    for (i, basis_row) in basis.iter().enumerate() {
        let mut bi: Vec<BigRational> = basis_row
            .iter()
            .map(|x| BigRational::from_integer(x.clone()))
            .collect();
        for j in 0..i {
            if bstar_sq[j].is_zero() {
                continue;
            }
            let dot: BigRational = (0..dim).map(|c| &bi[c] * &bstar[j][c]).sum();
            let mu = dot / &bstar_sq[j];
            for c in 0..dim {
                bi[c] -= &mu * &bstar[j][c];
            }
        }
        let sq: BigRational = (0..dim).map(|c| &bi[c] * &bi[c]).sum();
        bstar.push(bi);
        bstar_sq.push(sq);
    }

    let mut cur: Vec<BigInt> = particular.to_vec();
    for i in (0..k).rev() {
        if bstar_sq[i].is_zero() {
            continue;
        }
        let dot: BigRational = (0..dim)
            .map(|c| BigRational::from_integer(cur[c].clone()) * &bstar[i][c])
            .sum();
        let coeff = round_rational_nearest(&(dot / &bstar_sq[i]));
        if !coeff.is_zero() {
            for c in 0..dim {
                cur[c] -= &coeff * &basis[i][c];
            }
        }
    }
    cur
}

/// Modular inverse modulo prime `modulus`.
pub fn mod_inv_bigint(v: &BigInt, modulus: &BigInt) -> Result<BigInt, String> {
    let r = v.mod_floor(modulus);
    let eg = r.extended_gcd(modulus);
    if eg.gcd != BigInt::one() {
        return Err(format!("{r} is not invertible modulo {modulus}"));
    }
    Ok(eg.x.mod_floor(modulus))
}

/// Rank of `rows` over `F_p` (`modulus` prime).
pub fn rank_mod_prime(rows: &[Vec<BigInt>], ncols: usize, modulus: &BigInt) -> usize {
    if rows.is_empty() || ncols == 0 {
        return 0;
    }
    let m = rows.len();
    let mut mat: Vec<Vec<BigInt>> = rows
        .iter()
        .map(|r| r.iter().map(|x| x.mod_floor(modulus)).collect())
        .collect();
    let mut rank = 0usize;
    for col in 0..ncols {
        let Some(piv) = (rank..m).find(|&r| !mat[r][col].is_zero()) else {
            continue;
        };
        mat.swap(rank, piv);
        let Ok(inv) = mod_inv_bigint(&mat[rank][col], modulus) else {
            continue;
        };
        for v in &mut mat[rank][col..ncols] {
            *v = (&*v * &inv).mod_floor(modulus);
        }
        let piv_row = mat[rank].clone();
        for (r_idx, row_vec) in mat.iter_mut().enumerate() {
            if r_idx == rank || row_vec[col].is_zero() {
                continue;
            }
            let factor = row_vec[col].clone();
            for c_idx in col..ncols {
                row_vec[c_idx] = (&row_vec[c_idx] - &factor * &piv_row[c_idx]).mod_floor(modulus);
            }
        }
        rank += 1;
        if rank == m {
            break;
        }
    }
    rank
}

/// Solve `rows * vars = rhs (mod modulus)` for prime `modulus`; returns `vars[0]`
/// when column 0 is uniquely determined (eliminated from all free columns) and the system is consistent.
pub fn solve_var0_mod_prime(
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
        let inv = mod_inv_bigint(&aug[rank][col], modulus).ok()?;
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
    for row in &aug[rank..] {
        if !row[num_vars].is_zero() {
            return None;
        }
    }
    let r0 = piv_for_col[0]?;
    if aug[r0][1..num_vars].iter().any(|entry| !entry.is_zero()) {
        return None;
    }
    Some(aug[r0][num_vars].clone())
}

/// Construct an exact saturated `Z`-basis of the subspace-congruence sublattice
/// `{c in span_Z(kernel_basis) : exists mu in F_p^t, c = sum_j mu_j target_basis[j] (mod p)}`.
/// Also returns `has_nonzero_mod_p_solution` indicating whether any `c` in the sublattice is `!= 0 mod p`.
pub fn subspace_congruence_sublattice(
    kernel_basis: &[Vec<BigInt>],
    target_basis_mod_p: &[Vec<BigInt>],
    modulus: &BigInt,
) -> Result<(Vec<Vec<BigInt>>, bool), String> {
    let d = kernel_basis.len();
    if d == 0 {
        return Err("empty integer kernel".into());
    }
    let dim = kernel_basis[0].len();
    let t = target_basis_mod_p.len();
    if t == 0 {
        let mut scaled = Vec::with_capacity(d);
        for kvec in kernel_basis {
            scaled.push(kvec.iter().map(|x| x * modulus).collect());
        }
        return Ok((scaled, false));
    }

    let nvars = d + t;
    let mut mat = vec![vec![BigInt::zero(); nvars]; dim];
    for row in 0..dim {
        for (col, kvec) in kernel_basis.iter().enumerate() {
            mat[row][col] = kvec[row].mod_floor(modulus);
        }
        for (j, tvec) in target_basis_mod_p.iter().enumerate() {
            mat[row][d + j] = (-&tvec[row]).mod_floor(modulus);
        }
    }

    let mut pivot_cols = Vec::new();
    let mut rank = 0usize;
    for col in 0..nvars {
        let Some(piv) = (rank..dim).find(|&r| !mat[r][col].is_zero()) else {
            continue;
        };
        mat.swap(rank, piv);
        let inv = mod_inv_bigint(&mat[rank][col], modulus)?;
        for entry in &mut mat[rank][col..nvars] {
            *entry = (&*entry * &inv).mod_floor(modulus);
        }
        let piv_row = mat[rank].clone();
        for (r_idx, row_vec) in mat.iter_mut().enumerate() {
            if r_idx == rank || row_vec[col].is_zero() {
                continue;
            }
            let factor = row_vec[col].clone();
            for c_idx in col..nvars {
                row_vec[c_idx] = (&row_vec[c_idx] - &factor * &piv_row[c_idx]).mod_floor(modulus);
            }
        }
        pivot_cols.push(col);
        rank += 1;
        if rank == dim {
            break;
        }
    }

    let free_cols: Vec<usize> = (0..nvars).filter(|c| !pivot_cols.contains(c)).collect();
    let mut null_vectors = Vec::new();
    let mut has_nonzero_mod_p = false;
    for &free in &free_cols {
        let mut v = vec![BigInt::zero(); nvars];
        v[free] = BigInt::one();
        for (row_idx, &pcol) in pivot_cols.iter().enumerate() {
            v[pcol] = (-&mat[row_idx][free]).mod_floor(modulus);
        }
        // Check if sum_{j < d} v[j] * kernel_basis[j] != 0 mod p!
        let img_nonzero = (0..dim).any(|row| {
            let s: BigInt = kernel_basis
                .iter()
                .enumerate()
                .map(|(col, kvec)| &v[col] * &kvec[row])
                .sum();
            !s.mod_floor(modulus).is_zero()
        });
        if img_nonzero {
            has_nonzero_mod_p = true;
        }
        null_vectors.push(v);
    }

    let mut alpha_generators: Vec<Vec<BigInt>> = null_vectors
        .into_iter()
        .map(|v| v[..d].to_vec())
        .filter(|alpha| alpha.iter().any(|x| !x.is_zero()))
        .collect();
    for i in 0..d {
        let mut p_row = vec![BigInt::zero(); d];
        p_row[i] = modulus.clone();
        alpha_generators.push(p_row);
    }
    let alpha_basis = row_hermite_basis(alpha_generators, d);
    if alpha_basis.len() != d {
        return Err("internal error: congruence sublattice lost rank".into());
    }
    let mut sublattice = Vec::with_capacity(d);
    for alpha in alpha_basis {
        let mut vec = vec![BigInt::zero(); dim];
        for (coeff, kvec) in alpha.iter().zip(kernel_basis) {
            for (slot, val) in vec.iter_mut().zip(kvec) {
                *slot += coeff * val;
            }
        }
        sublattice.push(vec);
    }
    Ok((sublattice, has_nonzero_mod_p))
}
