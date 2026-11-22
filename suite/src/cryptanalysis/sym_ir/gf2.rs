//! Dense bit-vectors and bit-matrices over GF(2).
//!
//! # Bit ordering
//!
//! A *bit-vector* of length `n` is a `&[u64]` (or `Vec<u64>`) of
//! `ceil(n / 64)` words. Bit `i` lives in word `i / 64` at bit position
//! `i % 64` (least-significant bit first). Bits at positions `>= n` in the
//! last word are always kept at zero by every function in this module.
//!
//! A [`Gf2Matrix`] with `rows` rows and `cols` columns acts on bit-vectors of
//! length `cols` and produces bit-vectors of length `rows`:
//! `(M x)[i] = XOR_j (M[i][j] AND x[j])`.

/// Number of `u64` words needed to hold `bits` bits.
#[inline]
pub fn words_for(bits: usize) -> usize {
    bits.div_ceil(64)
}

/// Read bit `i` of a bit-vector.
#[inline]
pub fn get_bit(v: &[u64], i: usize) -> bool {
    (v[i / 64] >> (i % 64)) & 1 == 1
}

/// Write bit `i` of a bit-vector.
#[inline]
pub fn set_bit(v: &mut [u64], i: usize, b: bool) {
    let m = 1u64 << (i % 64);
    if b {
        v[i / 64] |= m;
    } else {
        v[i / 64] &= !m;
    }
}

/// Read `n <= 64` bits starting at bit `off`, returned in the low `n` bits
/// (bit `off` becomes bit 0 of the result).
#[inline]
pub fn get_bits(v: &[u64], off: usize, n: usize) -> u64 {
    debug_assert!(n <= 64);
    if n == 0 {
        return 0;
    }
    let w = off / 64;
    let s = off % 64;
    let mut x = v[w] >> s;
    if s != 0 && s + n > 64 {
        x |= v[w + 1] << (64 - s);
    }
    if n < 64 {
        x &= (1u64 << n) - 1;
    }
    x
}

/// Write the low `n <= 64` bits of `val` at bit offset `off`.
#[inline]
pub fn set_bits(v: &mut [u64], off: usize, n: usize, val: u64) {
    debug_assert!(n <= 64);
    if n == 0 {
        return;
    }
    let mask = if n == 64 { u64::MAX } else { (1u64 << n) - 1 };
    let val = val & mask;
    let w = off / 64;
    let s = off % 64;
    v[w] = (v[w] & !(mask << s)) | (val << s);
    if s != 0 && s + n > 64 {
        let hi = 64 - s;
        v[w + 1] = (v[w + 1] & !(mask >> hi)) | (val >> hi);
    }
}

/// Population count of a bit-vector.
pub fn weight(v: &[u64]) -> u32 {
    v.iter().map(|w| w.count_ones()).sum()
}

/// A dense `rows x cols` matrix over GF(2), stored row-major, one bit-vector
/// (see the [module docs](self)) per row.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Gf2Matrix {
    rows: usize,
    cols: usize,
    stride: usize,
    data: Vec<u64>,
}

impl Gf2Matrix {
    /// The all-zero `rows x cols` matrix.
    pub fn zero(rows: usize, cols: usize) -> Self {
        let stride = words_for(cols);
        Self {
            rows,
            cols,
            stride,
            data: vec![0; rows * stride],
        }
    }

    /// The `n x n` identity matrix.
    pub fn identity(n: usize) -> Self {
        let mut m = Self::zero(n, n);
        for i in 0..n {
            m.set(i, i, true);
        }
        m
    }

    /// Matrix of the bit permutation `perm`: output bit `i` equals input
    /// bit `perm[i]`, i.e. `M[i][perm[i]] = 1`. Panics if `perm` is not a
    /// permutation of `0..perm.len()`.
    pub fn from_permutation(perm: &[usize]) -> Self {
        let n = perm.len();
        let mut seen = vec![false; n];
        let mut m = Self::zero(n, n);
        for (i, &p) in perm.iter().enumerate() {
            assert!(p < n && !seen[p], "from_permutation: not a permutation");
            seen[p] = true;
            m.set(i, p, true);
        }
        m
    }

    /// Build a matrix from rows given as `bool` slices (all of equal length).
    pub fn from_bool_rows(rows: &[Vec<bool>]) -> Self {
        let cols = rows.first().map_or(0, |r| r.len());
        let mut m = Self::zero(rows.len(), cols);
        for (i, r) in rows.iter().enumerate() {
            assert_eq!(r.len(), cols, "from_bool_rows: ragged rows");
            for (j, &b) in r.iter().enumerate() {
                m.set(i, j, b);
            }
        }
        m
    }

    /// Number of rows (output length).
    pub fn rows(&self) -> usize {
        self.rows
    }

    /// Number of columns (input length).
    pub fn cols(&self) -> usize {
        self.cols
    }

    /// Entry `M[i][j]`.
    #[inline]
    pub fn get(&self, i: usize, j: usize) -> bool {
        debug_assert!(i < self.rows && j < self.cols);
        get_bit(&self.data[i * self.stride..(i + 1) * self.stride], j)
    }

    /// Set entry `M[i][j]`.
    #[inline]
    pub fn set(&mut self, i: usize, j: usize, b: bool) {
        debug_assert!(i < self.rows && j < self.cols);
        let s = self.stride;
        set_bit(&mut self.data[i * s..(i + 1) * s], j, b);
    }

    /// Row `i` as a bit-vector of length `cols`.
    pub fn row(&self, i: usize) -> &[u64] {
        &self.data[i * self.stride..(i + 1) * self.stride]
    }

    /// Matrix-vector product `M x` for a bit-vector `x` of length `cols`.
    /// Returns a bit-vector of length `rows`.
    pub fn mul_vec(&self, x: &[u64]) -> Vec<u64> {
        assert!(x.len() >= self.stride, "mul_vec: vector too short");
        let mut out = vec![0u64; words_for(self.rows)];
        for i in 0..self.rows {
            let r = self.row(i);
            let mut acc = 0u64;
            for (a, b) in r.iter().zip(x.iter()) {
                acc ^= a & b;
            }
            if acc.count_ones() & 1 == 1 {
                out[i / 64] |= 1u64 << (i % 64);
            }
        }
        out
    }

    /// Matrix product `self * other` (apply `other` first). Requires
    /// `self.cols() == other.rows()`.
    pub fn mul(&self, other: &Gf2Matrix) -> Gf2Matrix {
        assert_eq!(self.cols, other.rows, "mul: dimension mismatch");
        let mut out = Gf2Matrix::zero(self.rows, other.cols);
        for i in 0..self.rows {
            let mut acc = vec![0u64; other.stride];
            for k in 0..self.cols {
                if self.get(i, k) {
                    for (a, b) in acc.iter_mut().zip(other.row(k)) {
                        *a ^= b;
                    }
                }
            }
            let s = out.stride;
            out.data[i * s..(i + 1) * s].copy_from_slice(&acc);
        }
        out
    }

    /// Transpose.
    pub fn transpose(&self) -> Gf2Matrix {
        let mut t = Gf2Matrix::zero(self.cols, self.rows);
        for i in 0..self.rows {
            for j in 0..self.cols {
                if self.get(i, j) {
                    t.set(j, i, true);
                }
            }
        }
        t
    }

    /// Rank over GF(2) (Gaussian elimination on a copy).
    pub fn rank(&self) -> usize {
        let mut m = self.clone();
        let mut rank = 0;
        for col in 0..m.cols {
            let Some(p) = (rank..m.rows).find(|&r| m.get(r, col)) else {
                continue;
            };
            m.swap_rows(rank, p);
            for r in 0..m.rows {
                if r != rank && m.get(r, col) {
                    m.xor_row(r, rank);
                }
            }
            rank += 1;
            if rank == m.rows {
                break;
            }
        }
        rank
    }

    /// Inverse of a square matrix, or `None` if it is singular or not square.
    pub fn inverse(&self) -> Option<Gf2Matrix> {
        if self.rows != self.cols {
            return None;
        }
        let n = self.rows;
        let mut a = self.clone();
        let mut inv = Gf2Matrix::identity(n);
        for col in 0..n {
            let p = (col..n).find(|&r| a.get(r, col))?;
            a.swap_rows(col, p);
            inv.swap_rows(col, p);
            for r in 0..n {
                if r != col && a.get(r, col) {
                    a.xor_row(r, col);
                    inv.xor_row(r, col);
                }
            }
        }
        Some(inv)
    }

    /// If this matrix is a permutation matrix, return `perm` with
    /// `M[i][perm[i]] = 1` (the inverse of [`Gf2Matrix::from_permutation`]).
    pub fn as_permutation(&self) -> Option<Vec<usize>> {
        if self.rows != self.cols {
            return None;
        }
        let mut perm = Vec::with_capacity(self.rows);
        let mut seen = vec![false; self.cols];
        for i in 0..self.rows {
            if weight(self.row(i)) != 1 {
                return None;
            }
            let j = (0..self.cols).find(|&j| self.get(i, j))?;
            if seen[j] {
                return None;
            }
            seen[j] = true;
            perm.push(j);
        }
        Some(perm)
    }

    fn swap_rows(&mut self, a: usize, b: usize) {
        if a == b {
            return;
        }
        for k in 0..self.stride {
            self.data.swap(a * self.stride + k, b * self.stride + k);
        }
    }

    /// `row[dst] ^= row[src]`.
    fn xor_row(&mut self, dst: usize, src: usize) {
        for k in 0..self.stride {
            let v = self.data[src * self.stride + k];
            self.data[dst * self.stride + k] ^= v;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::SmallRng;
    use rand::{Rng, SeedableRng};

    fn random_matrix(rng: &mut SmallRng, r: usize, c: usize) -> Gf2Matrix {
        let mut m = Gf2Matrix::zero(r, c);
        for i in 0..r {
            for j in 0..c {
                m.set(i, j, rng.gen());
            }
        }
        m
    }

    #[test]
    fn get_set_bits_cross_word_boundary() {
        let mut v = vec![0u64; 3];
        set_bits(&mut v, 60, 12, 0xABC);
        assert_eq!(get_bits(&v, 60, 12), 0xABC);
        assert_eq!(get_bits(&v, 64, 8), 0xAB);
        set_bits(&mut v, 0, 64, u64::MAX);
        assert_eq!(get_bits(&v, 0, 64), u64::MAX);
        assert_eq!(
            get_bits(&v, 3, 64),
            0x1FFF_FFFF_FFFF_FFFF | (0b011u64 << 61)
        );
    }

    #[test]
    fn identity_and_permutation_act_as_expected() {
        let id = Gf2Matrix::identity(70);
        let x = vec![0xDEAD_BEEF_0123_4567u64, 0x2A];
        assert_eq!(id.mul_vec(&x), x);
        let perm: Vec<usize> = (0..70).map(|i| (i + 5) % 70).collect();
        let p = Gf2Matrix::from_permutation(&perm);
        let y = p.mul_vec(&x);
        for i in 0..70 {
            assert_eq!(get_bit(&y, i), get_bit(&x, perm[i]));
        }
        assert_eq!(p.as_permutation().unwrap(), perm);
        assert_eq!(p.rank(), 70);
    }

    #[test]
    fn inverse_rank_and_product_agree() {
        let mut rng = SmallRng::seed_from_u64(0x51F0_0001);
        let mut invertible = 0;
        for _ in 0..40 {
            let m = random_matrix(&mut rng, 37, 37);
            match m.inverse() {
                Some(inv) => {
                    invertible += 1;
                    assert_eq!(m.rank(), 37);
                    assert_eq!(m.mul(&inv), Gf2Matrix::identity(37));
                    assert_eq!(inv.mul(&m), Gf2Matrix::identity(37));
                    let x = vec![rng.gen::<u64>() & ((1 << 37) - 1)];
                    assert_eq!(inv.mul_vec(&m.mul_vec(&x)), x);
                }
                None => assert!(m.rank() < 37),
            }
        }
        assert!(invertible > 0, "no invertible sample in 40 draws");
    }

    #[test]
    fn rank_of_rectangular_and_dependent_rows() {
        let rows = vec![
            vec![true, false, true, true],
            vec![false, true, true, false],
            vec![true, true, false, true], // = row0 ^ row1
        ];
        let m = Gf2Matrix::from_bool_rows(&rows);
        assert_eq!(m.rank(), 2);
        assert_eq!(m.transpose().rank(), 2);
        assert!(Gf2Matrix::zero(3, 3).inverse().is_none());
        assert!(m.inverse().is_none());
    }

    #[test]
    fn mul_is_composition_of_mul_vec() {
        let mut rng = SmallRng::seed_from_u64(0x51F0_0002);
        let a = random_matrix(&mut rng, 20, 30);
        let b = random_matrix(&mut rng, 30, 25);
        let x = vec![rng.gen::<u64>() & ((1 << 25) - 1)];
        assert_eq!(a.mul(&b).mul_vec(&x), a.mul_vec(&b.mul_vec(&x)));
    }
}
