//! Native per-relation solve for the n = 19 tau-orbit dim-6 index calculus
//! (`experiments/volcano-ic/tau.sage`, arm `tau6`).
//!
//! The baseline builds, for each target x-coordinate xR and each Frobenius
//! shift j, the Boolean system `TauField.system(j, xR, b)` in the 2k
//! variables u_0..u_{k-1}, w_0..w_{k-1} and asks PolyBoRi for its variety.
//! Coordinate by coordinate that system is the third summation polynomial
//!
//!   S3(x1, x2, xR) = (x1 x2)^2 + xR^2 (x1^2 + x2^2) + xR x1 x2 + b = 0
//!
//! over GF(2^n), with x1 = sum u_i z^i and x2 = sigma^j(sum w_l z^l)
//! (sigma = squaring). Its variety over F_2 is therefore exactly the set of
//! (u, w) in F_2^k x F_2^k with S3 = 0. This file enumerates that set.
//!
//! For fixed u, S3 = a x2^2 + c x2 + d with a = (x1 + xR)^2, c = xR x1,
//! d = c^2 + b, and x2 -> a x2^2 + c x2 is F_2-linear. With
//! Y_l = sigma^j(z^l) the condition is sum_l w_l g_l = d, g_l = a Y_l^2 + c Y_l,
//! checked for all 2^k w by a Gray-code walk. Nothing is pruned: every
//! (u, w) is decided, so the output is the whole variety.
//!
//! Output order: ascending in u, then in w (each solution is written as
//! u | w << k). The order matters only when a system has two or more
//! solutions (see ../smoke/multi_survey.json and multi_calls.json).

#![allow(clippy::missing_safety_doc)]

pub const MAX_N: u32 = 31;
pub const MAX_K: u32 = 8;

pub struct Ctx {
    n: u32,
    k: u32,
    modulus: u64,
    b: u64,
    /// y[j * k + l] = sigma^j(z^l), y2[j * k + l] = sigma^(j+1)(z^l).
    y: Vec<u64>,
    y2: Vec<u64>,
    /// zy[(j * k + i) * k + l] = z^i sigma^j(z^l); zy2[...] = z^(2i) sigma^(j+1)(z^l);
    /// z2[i] = z^(2i). They make every per-u quantity linear in the bits of u.
    zy: Vec<u64>,
    zy2: Vec<u64>,
    z2: Vec<u64>,
}

#[inline]
pub fn gf_mul(a: u64, b: u64, n: u32, modulus: u64) -> u64 {
    // Carry-less product (at most 2n - 1 bits), then reduce from the top.
    let mut r = 0u64;
    let mut bb = b;
    let mut i = 0;
    while bb != 0 {
        if bb & 1 != 0 {
            r ^= a << i;
        }
        bb >>= 1;
        i += 1;
    }
    let mut bit = 2 * n;
    while bit > n {
        bit -= 1;
        if (r >> bit) & 1 != 0 {
            r ^= modulus << (bit - n);
        }
    }
    r
}

impl Ctx {
    pub fn new(modulus: u64, n: u32, k: u32, b: u64) -> Option<Ctx> {
        if n < 2 || n > MAX_N || k == 0 || k > MAX_K || k > n || (modulus >> n) != 1 || b >> n != 0 {
            return None;
        }
        let mut y = vec![0u64; (n * k) as usize];
        let mut y2 = vec![0u64; (n * k) as usize];
        for l in 0..k {
            let mut v = 1u64 << l; // z^l, l < k <= n
            for j in 0..n {
                y[(j * k + l) as usize] = v;
                v = gf_mul(v, v, n, modulus);
                y2[(j * k + l) as usize] = v;
            }
        }
        let kk = k as usize;
        let mut zy = vec![0u64; n as usize * kk * kk];
        let mut zy2 = vec![0u64; n as usize * kk * kk];
        let z2: Vec<u64> = (0..k).map(|i| gf_mul(1 << i, 1 << i, n, modulus)).collect();
        for j in 0..n as usize {
            for i in 0..kk {
                for l in 0..kk {
                    zy[(j * kk + i) * kk + l] = gf_mul(1 << i, y[j * kk + l], n, modulus);
                    zy2[(j * kk + i) * kk + l] = gf_mul(z2[i], y2[j * kk + l], n, modulus);
                }
            }
        }
        Some(Ctx { n, k, modulus, b, y, y2, zy, zy2, z2 })
    }

    #[inline]
    fn mul(&self, a: u64, b: u64) -> u64 {
        gf_mul(a, b, self.n, self.modulus)
    }

    /// Every (u, w) with S3(x1(u), sigma^j(x2(w)), xr) = 0, as u | (w << k),
    /// ascending in u, then in w. Returns the count (all of them are
    /// written when cap allows; the count is returned either way).
    ///
    /// a = u^2 + xr^2, c = xr u and d = (xr u)^2 + b are affine in the bits
    /// of u, so g_l(u) = a Y_l^2 + c Y_l and d(u) are too: 49 field
    /// multiplications per call build their increments, then a Gray-code walk
    /// over u (and, inside it, over w) decides all 2^(2k) pairs with XORs.
    pub fn solve(&self, xr: u64, j: u32, out: &mut [u32]) -> usize {
        let k = self.k as usize;
        let jj = (j % self.n) as usize;
        let y2s = &self.y2[jj * k..jj * k + k];
        let zy = &self.zy[jj * k * k..(jj + 1) * k * k];
        let zy2 = &self.zy2[jj * k * k..(jj + 1) * k * k];
        let xr2 = self.mul(xr, xr);
        let mut dg = [[0u64; MAX_K as usize]; MAX_K as usize];
        let mut dd = [0u64; MAX_K as usize];
        let mut g = [0u64; MAX_K as usize];
        for i in 0..k {
            for l in 0..k {
                dg[i][l] = zy2[i * k + l] ^ self.mul(xr, zy[i * k + l]);
            }
            dd[i] = self.mul(xr2, self.z2[i]);
        }
        for l in 0..k {
            g[l] = self.mul(xr2, y2s[l]); // u = 0: a = xr^2, c = 0
        }
        let mut d = self.b;
        let mut keys: [u32; 1 << (2 * MAX_K)] = [0; 1 << (2 * MAX_K)];
        let mut nk = 0usize;
        let mut u = 0u32;
        for tu in 0u32..(1u32 << k) {
            if tu != 0 {
                let i = tu.trailing_zeros() as usize;
                u ^= 1 << i;
                for l in 0..k {
                    g[l] ^= dg[i][l];
                }
                d ^= dd[i];
            }
            let mut acc = 0u64;
            let mut w = 0u32;
            if acc == d {
                keys[nk] = u << k;
                nk += 1;
            }
            for t in 1u32..(1u32 << k) {
                let l = t.trailing_zeros() as usize;
                acc ^= g[l];
                w ^= 1 << l;
                if acc == d {
                    keys[nk] = (u << k) | w;
                    nk += 1;
                }
            }
        }
        let keys = &mut keys[..nk];
        keys.sort_unstable();
        let mask = (1u32 << k) - 1;
        for (idx, &key) in keys.iter().enumerate() {
            if idx < out.len() {
                out[idx] = (key >> k) | ((key & mask) << k);
            }
        }
        nk
    }

    /// The direct form (per u: a, c, d and g_l by multiplication). Tests only.
    pub fn solve_direct(&self, xr: u64, j: u32, out: &mut [u32]) -> usize {
        let k = self.k as usize;
        let base = (j % self.n) as usize * k;
        let ys = &self.y[base..base + k];
        let y2s = &self.y2[base..base + k];
        let mut count = 0usize;
        let mut g = [0u64; MAX_K as usize];
        let mut ws: [u32; 1 << MAX_K] = [0; 1 << MAX_K];
        for u in 0u64..(1u64 << k) {
            let x1 = u; // sum u_i z^i with i < k
            let s = x1 ^ xr;
            let a = self.mul(s, s);
            let c = self.mul(xr, x1);
            let d = self.mul(c, c) ^ self.b;
            for l in 0..k {
                g[l] = self.mul(a, y2s[l]) ^ self.mul(c, ys[l]);
            }
            // Gray-code walk over all 2^k w.
            let mut acc = 0u64;
            let mut w = 0u32;
            let mut nw = 0usize;
            if acc == d {
                ws[nw] = 0;
                nw += 1;
            }
            for t in 1u32..(1u32 << k) {
                let l = t.trailing_zeros() as usize;
                acc ^= g[l];
                w ^= 1 << l;
                if acc == d {
                    ws[nw] = w;
                    nw += 1;
                }
            }
            ws[..nw].sort_unstable();
            for &wv in &ws[..nw] {
                if count < out.len() {
                    out[count] = (u as u32) | (wv << k);
                }
                count += 1;
            }
        }
        count
    }
}

/// Independent reference: evaluate S3 directly on every (u, w), with
/// sigma^j(x2) by repeated squaring. Used by the tests and the selftest.
pub fn solve_bruteforce(modulus: u64, n: u32, k: u32, b: u64, xr: u64, j: u32) -> Vec<u32> {
    let mul = |a: u64, c: u64| gf_mul(a, c, n, modulus);
    let mut out = Vec::new();
    for u in 0u64..(1 << k) {
        for w in 0u64..(1 << k) {
            let mut x2 = w;
            for _ in 0..(j % n) {
                x2 = mul(x2, x2);
            }
            let x1 = u;
            let m = mul(x1, x2);
            let xr2 = mul(xr, xr);
            let f = mul(m, m) ^ mul(xr2, mul(x1, x1) ^ mul(x2, x2)) ^ mul(xr, m) ^ b;
            if f == 0 {
                out.push((u as u32) | ((w as u32) << k));
            }
        }
    }
    out
}

#[no_mangle]
pub extern "C" fn tau6_new(modulus: u64, n: u32, k: u32, b: u64) -> *mut Ctx {
    match Ctx::new(modulus, n, k, b) {
        Some(c) => Box::into_raw(Box::new(c)),
        None => std::ptr::null_mut(),
    }
}

#[no_mangle]
pub unsafe extern "C" fn tau6_free(ctx: *mut Ctx) {
    if !ctx.is_null() {
        drop(Box::from_raw(ctx));
    }
}

/// Writes up to `cap` solutions to `out`; returns the total count, or -1 on
/// a bad argument.
#[no_mangle]
pub unsafe extern "C" fn tau6_solve(ctx: *const Ctx, xr: u64, j: u32, out: *mut u32, cap: u32) -> i64 {
    if ctx.is_null() || (out.is_null() && cap != 0) {
        return -1;
    }
    let c = &*ctx;
    if xr >> c.n != 0 {
        return -1;
    }
    let slice: &mut [u32] = if cap == 0 { &mut [] } else { std::slice::from_raw_parts_mut(out, cap as usize) };
    c.solve(xr, j, slice) as i64
}

/// The brute-force reference through the C ABI (selftest only).
#[no_mangle]
pub unsafe extern "C" fn tau6_solve_bruteforce(ctx: *const Ctx, xr: u64, j: u32, out: *mut u32, cap: u32) -> i64 {
    if ctx.is_null() || (out.is_null() && cap != 0) {
        return -1;
    }
    let c = &*ctx;
    let v = solve_bruteforce(c.modulus, c.n, c.k, c.b, xr, j);
    for (i, s) in v.iter().enumerate().take(cap as usize) {
        *out.add(i) = *s;
    }
    v.len() as i64
}

#[cfg(test)]
mod tests {
    use super::*;

    // run.sage MODULUS: z^19 + z^18 + z^16 + z^11 + z^8 + z^6 + z^4 + z + 1.
    const MODULUS: u64 = (1 << 19) | (1 << 18) | (1 << 16) | (1 << 11) | (1 << 8) | (1 << 6) | (1 << 4) | (1 << 1) | 1;

    #[test]
    fn mul_is_field_mul() {
        // z^19 reduces to the low terms of the modulus.
        assert_eq!(gf_mul(1 << 18, 1 << 1, 19, MODULUS), MODULUS ^ (1 << 19));
        // x^(2^19) = x.
        let mut x = 0x5a5a5u64 & ((1 << 19) - 1);
        let x0 = x;
        for _ in 0..19 {
            x = gf_mul(x, x, 19, MODULUS);
        }
        assert_eq!(x, x0);
    }

    #[test]
    fn solve_equals_bruteforce() {
        let ctx = Ctx::new(MODULUS, 19, 6, 1).unwrap();
        let mut st = 0x1234_5678_9abc_def0u64;
        let mut buf = vec![0u32; 4096];
        let mut nonempty = 0;
        for _ in 0..400 {
            st ^= st << 13;
            st ^= st >> 7;
            st ^= st << 17;
            let xr = st & ((1 << 19) - 1);
            let j = ((st >> 32) % 19) as u32;
            let nsol = ctx.solve(xr, j, &mut buf);
            let want = solve_bruteforce(MODULUS, 19, 6, 1, xr, j);
            assert_eq!(&buf[..nsol], &want[..], "xr {xr} j {j}");
            let mut buf2 = vec![0u32; 4096];
            let n2 = ctx.solve_direct(xr, j, &mut buf2);
            assert_eq!(&buf2[..n2], &want[..], "direct xr {xr} j {j}");
            if nsol > 0 {
                nonempty += 1;
            }
        }
        assert!(nonempty > 0);
    }

    #[test]
    fn two_solution_systems() {
        // Shift-0 systems with the swap pair (found by the local survey).
        let ctx = Ctx::new(MODULUS, 19, 6, 1).unwrap();
        let mut buf = vec![0u32; 4096];
        for &(xr, a, b) in &[(66302u64, 46u32, 49u32), (283919, 18, 28), (295497, 36, 37), (320460, 8, 18)] {
            let nsol = ctx.solve(xr, 0, &mut buf);
            assert_eq!(&buf[..nsol], &[a | (b << 6), b | (a << 6)], "xr {xr}");
            assert_eq!(&buf[..nsol], &solve_bruteforce(MODULUS, 19, 6, 1, xr, 0)[..]);
        }
    }
}
