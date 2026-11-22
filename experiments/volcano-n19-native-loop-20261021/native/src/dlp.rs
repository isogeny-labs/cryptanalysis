//! tau.sage's TauCurve, generator, tauEigen and tauDlp, in native code.
//!
//! Each function names the Sage line it reproduces. The semantics kept exactly:
//! the factor base V' (x in span{1, z, ..., z^5} on E), the orbit representatives
//! (smallest encoding in each Frobenius orbit, y by Sage's lift_x), the table
//! x -> (point, column, e, sign), the generator of run.sage `generator(cur, 'E0')`,
//! the target draws `al, be = rng.randrange(1, p), rng.randrange(1, p)` from
//! CPython's MT19937, `rng.shuffle(shifts)` on the one persistent shift list,
//! the per-shift variety from the v3 solve (Sage's order), the first sign
//! combination (1, 1), (1, -1), (-1, 1), (-1, -1) that reaches R, the counters
//! targets / gb_calls / spurious, the matrix rows (column -> sum sign lambda^e
//! in insertion order), `M.left_kernel().basis()` (the reduced echelon basis of
//! the left kernel, which is unique) and the first basis vector with B != 0.

use crate::curve::{Field, Pt};
use crate::pyrand::PyRandom;
use crate::v3::Ctx;

pub const N_BITS: u32 = 19;
pub const K: u32 = 6;
pub const MODULUS: u64 = 854355; // run.sage MODULUS, bit i = z^i (Sage F.modulus() in every v3 binding check)
pub const ORDER: u64 = 523492;
pub const COFACTOR: u64 = 4;
pub const P_ORD: u64 = ORDER / COFACTOR; // 130873
pub const EXTRA: usize = 10;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct BaseEntry {
    pub pt: (u64, u64),
    pub col: usize,
    pub e: u32,
    pub sign: i64,
}

pub struct Setup {
    pub f: Field,
    pub ctx: Ctx,
    /// base[x] for x < 2^k (tau.sage cur.base; None: x not in V' or not on E)
    pub base: Vec<Option<BaseEntry>>,
    pub reps: Vec<(u64, u64)>,
    pub p: Pt,
    pub v_points: usize,
}

pub type Rel = [(usize, i64, u32); 2];

#[derive(Default)]
pub struct Stats {
    pub targets: u64,
    pub gb_calls: u64,
    pub spurious: u64,
    pub relations: usize,
    pub log: Option<u64>,
    pub recovered: bool,
    pub lambda: u64,
    pub relation_cpu_s: f64,
    pub linalg_cpu_s: f64,
}

/// One target of the relation loop, for the planted arm's comparison with Sage.
pub struct TargetRec {
    pub al: u64,
    pub be: u64,
    pub r: Pt,
    pub shifts: Vec<u32>,
    pub calls: u64,
    pub rel: Option<Rel>,
}

#[derive(Default)]
pub struct Trace {
    pub targets: Vec<TargetRec>,
    pub used_cols: Vec<usize>,
    pub kernel_basis: Vec<Vec<u64>>,
    pub kernel_index: Option<usize>,
}

pub fn modpow(mut b: u64, mut e: u64, m: u64) -> u64 {
    let mut r = 1u64 % m;
    b %= m;
    while e > 0 {
        if e & 1 == 1 {
            r = r * b % m;
        }
        b = b * b % m;
        e >>= 1;
    }
    r
}

fn modinv(a: u64, p: u64) -> u64 {
    assert!(a % p != 0);
    modpow(a, p - 2, p)
}

/// sqrt mod an odd prime (Tonelli-Shanks); None if a is a non-residue.
fn sqrt_mod(a: u64, p: u64) -> Option<u64> {
    let a = a % p;
    if a == 0 {
        return Some(0);
    }
    if modpow(a, (p - 1) / 2, p) != 1 {
        return None;
    }
    let (mut q, mut s) = (p - 1, 0u32);
    while q % 2 == 0 {
        q /= 2;
        s += 1;
    }
    let mut z = 2u64;
    while modpow(z, (p - 1) / 2, p) != p - 1 {
        z += 1;
    }
    let (mut m, mut c, mut t, mut r) = (s, modpow(z, q, p), modpow(a, q, p), modpow(a, (q + 1) / 2, p));
    while t != 1 {
        let mut i = 0;
        let mut tt = t;
        while tt != 1 {
            tt = tt * tt % p;
            i += 1;
        }
        let b = modpow(c, 1 << (m - i - 1), p);
        m = i;
        c = b * b % p;
        t = t * c % p;
        r = r * b % p;
    }
    Some(r)
}

impl Setup {
    /// TauCurve(TauField(19, MODULUS, 6), ORDER, COFACTOR), the native solve context and
    /// P = generator(cur, 'E0'): the arm's setup interval.
    pub fn new() -> Setup {
        let f = Field::new(N_BITS, MODULUS);
        let ctx = Ctx::new(MODULUS, N_BITS, K, 1).expect("tau6 context");
        let n = N_BITS;
        // base = {x: E(x, x * halfTraceTau(x + 1/x^2))} over c = 1 .. 2^k - 1 with trace 0
        let mut basept: Vec<Option<(u64, u64)>> = vec![None; 1 << K];
        for c in 1..(1u64 << K) {
            let x = c; // fromBits: sum z^i over the bits of c
            let rhs = x ^ f.inv(f.sq(x));
            if f.trace(rhs) == 0 {
                basept[c as usize] = Some((x, f.mul(x, f.half_trace(rhs))));
            }
        }
        let orbit_min = |x: u64| -> u64 {
            let mut m = x;
            let mut t = x;
            for _ in 1..n {
                t = f.sq(t);
                m = m.min(t);
            }
            m
        };
        // reps: for x in sorted(base, key=enc), rx = min(orbit, key=enc), first seen -> new column,
        // with E(rx, lift_x(rx)[1])
        let mut reps: Vec<(u64, u64)> = vec![];
        let mut rep_of: Vec<(u64, usize)> = vec![];
        for x in 0..(1u64 << K) {
            if basept[x as usize].is_none() {
                continue;
            }
            let rx = orbit_min(x);
            if !rep_of.iter().any(|&(r, _)| r == rx) {
                rep_of.push((rx, reps.len()));
                let ys = f.lift_x_all(rx);
                reps.push(ys[0]);
            }
        }
        // base[x] = (P, col, e, +-1) with tau^e(rep) == +-P, first e
        let mut base: Vec<Option<BaseEntry>> = vec![None; 1 << K];
        for x in 0..(1u64 << K) {
            let pt = match basept[x as usize] {
                None => continue,
                Some(v) => v,
            };
            let rx = orbit_min(x);
            let col = rep_of.iter().find(|&&(r, _)| r == rx).unwrap().1;
            let rp = Some(reps[col]);
            let mut found = None;
            for e in 0..n {
                let t = f.frob(rp, e);
                if t == Some(pt) {
                    found = Some(BaseEntry { pt, col, e, sign: 1 });
                    break;
                }
                if t == f.neg(Some(pt)) {
                    found = Some(BaseEntry { pt, col, e, sign: -1 });
                    break;
                }
            }
            base[x as usize] = Some(found.expect("x in base"));
        }
        let v_points = base.iter().filter(|b| b.is_some()).count();
        // run.sage generator(cur, 'E0')
        let mut rng = PyRandom::from_str_seed("gen:E0");
        let p = loop {
            let x = rng.randrange(1, 1 << N_BITS);
            let pts = f.lift_x_all(x);
            if !pts.is_empty() {
                let pp = f.mul_pt(COFACTOR, Some(pts[0]));
                if pp.is_some() {
                    break pp;
                }
            }
        };
        Setup { f, ctx, base, reps, p, v_points }
    }

    /// tauEigen(cur, G): the root lambda of t^2 + t + 2 mod p with lambda G = tau(G).
    pub fn tau_eigen(&self, g: Pt) -> u64 {
        let p = P_ORD;
        let d = sqrt_mod(p - 7, p).expect("-7 is a square mod p");
        let inv2 = modinv(2, p);
        let roots = [(p - 1 + d) % p * inv2 % p, (2 * p - 1 - d) % p * inv2 % p];
        let tg = self.f.frob(g, 1);
        let ok: Vec<u64> = roots.iter().cloned().filter(|&l| self.f.mul_pt(l, g) == tg).collect();
        assert!(ok.len() == 1, "exactly one Frobenius eigenvalue");
        ok[0]
    }

    /// tau.sage tauRelation (with the v3 native variety), counters updated in place.
    fn relation(&self, r: Pt, stats: &mut Stats, shifts: &[u32], buf: &mut [u32], calls: &mut u64) -> Option<Rel> {
        let f = &self.f;
        let n = N_BITS;
        let (xr, _) = r.unwrap();
        let mask = (1u32 << K) - 1;
        for &j in shifts {
            let c = self.ctx.solve(xr, j, buf);
            assert!(c <= buf.len());
            stats.gb_calls += 1;
            *calls += 1;
            for &key in &buf[..c] {
                let (ub, wb) = ((key & mask) as usize, (key >> K) as usize);
                let (b1, b2) = match (self.base[ub], self.base[wb]) {
                    (Some(b1), Some(b2)) => (b1, b2),
                    _ => {
                        stats.spurious += 1;
                        continue;
                    }
                };
                let p1 = Some(b1.pt);
                let t2 = f.frob(Some(b2.pt), j);
                for s1 in [1i64, -1] {
                    for s2 in [1i64, -1] {
                        let a = if s1 == 1 { p1 } else { f.neg(p1) };
                        let b = if s2 == 1 { t2 } else { f.neg(t2) };
                        if f.add(a, b) == r {
                            return Some([(b1.col, s1 * b1.sign, b1.e), (b2.col, s2 * b2.sign, (j + b2.e) % n)]);
                        }
                    }
                }
                stats.spurious += 1;
            }
        }
        None
    }

    /// tau.sage tauDlp(cur, P, Q, rng, extra=10). `clock` reads process CPU time.
    pub fn tau_dlp(&self, q: Pt, seed: &str, rels: &mut Vec<Rel>, mut trace: Option<&mut Trace>, clock: &dyn Fn() -> f64)
                   -> Stats {
        let p = P_ORD;
        let h = COFACTOR;
        let n = N_BITS;
        let pp = self.p;
        let lam = self.tau_eigen(pp);
        let ncol = self.reps.len();
        let mut st = Stats { lambda: lam, ..Default::default() };
        let mut rng = PyRandom::from_str_seed(seed);
        let mut rows: Vec<Vec<(usize, u64)>> = vec![];
        let mut rhs: Vec<(u64, u64)> = vec![];
        let mut shifts: Vec<u32> = (0..n).collect();
        let mut buf = vec![0u32; 1 << (2 * K)];
        let lam_pow: Vec<u64> = (0..n).map(|e| modpow(lam, e as u64, p)).collect();
        let c0 = clock();
        while rows.len() < ncol + EXTRA {
            st.targets += 1;
            let al = rng.randrange(1, p);
            let be = rng.randrange(1, p);
            let r = self.f.add(self.f.mul_pt(al, pp), self.f.mul_pt(be, q));
            if r.is_none() {
                if let Some(t) = trace.as_deref_mut() {
                    t.targets.push(TargetRec { al, be, r, shifts: vec![], calls: 0, rel: None });
                }
                continue;
            }
            rng.shuffle(&mut shifts);
            let mut calls = 0u64;
            let rel = self.relation(r, &mut st, &shifts, &mut buf, &mut calls);
            if let Some(t) = trace.as_deref_mut() {
                t.targets.push(TargetRec { al, be, r, shifts: shifts.clone(), calls, rel });
            }
            let rel = match rel {
                None => continue,
                Some(v) => v,
            };
            // row[col] = row.get(col, Fp(0)) + sign * Fp(lam)^e
            let mut row: Vec<(usize, u64)> = vec![];
            for &(col, sign, e) in &rel {
                let v = if sign == 1 { lam_pow[e as usize] } else { (p - lam_pow[e as usize]) % p };
                match row.iter_mut().find(|(c, _)| *c == col) {
                    Some(x) => x.1 = (x.1 + v) % p,
                    None => row.push((col, v)),
                }
            }
            rows.push(row);
            rhs.push((h * al % p, h * be % p));
            rels.push(rel);
        }
        let c1 = clock();
        // used = sorted columns; M[i, idx[c]] += v; s from the first left-kernel basis vector with B != 0
        let mut used: Vec<usize> = rows.iter().flat_map(|r| r.iter().map(|&(c, _)| c)).collect();
        used.sort_unstable();
        used.dedup();
        let m = rows.len();
        let mut mat = vec![vec![0u64; used.len()]; m];
        for (i, r) in rows.iter().enumerate() {
            for &(c, v) in r {
                let j = used.binary_search(&c).unwrap();
                mat[i][j] = (mat[i][j] + v) % p;
            }
        }
        let basis = left_kernel_echelon(&mat, used.len(), p);
        let mut s = None;
        let mut idx = None;
        for (bi, v) in basis.iter().enumerate() {
            let mut a = 0u64;
            let mut bc = 0u64;
            for i in 0..m {
                a = (a + v[i] * rhs[i].0) % p;
                bc = (bc + v[i] * rhs[i].1) % p;
            }
            if bc != 0 {
                s = Some((p - a) % p * modinv(bc, p) % p);
                idx = Some(bi);
                break;
            }
        }
        st.relations = rows.len();
        st.log = s;
        st.recovered = match s {
            Some(sv) => self.f.mul_pt(sv, pp) == q,
            None => false,
        };
        st.relation_cpu_s = c1 - c0;
        st.linalg_cpu_s = clock() - c1;
        if let Some(t) = trace {
            t.used_cols = used;
            t.kernel_basis = basis;
            t.kernel_index = idx;
        }
        st
    }
}

/// Reduced row echelon form over GF(p), in place; returns the pivot columns.
pub fn rref(a: &mut [Vec<u64>], ncols: usize, p: u64) -> Vec<usize> {
    let mut piv = vec![];
    let mut r = 0usize;
    for c in 0..ncols {
        if r == a.len() {
            break;
        }
        let sel = match (r..a.len()).find(|&i| a[i][c] != 0) {
            None => continue,
            Some(s) => s,
        };
        a.swap(r, sel);
        let inv = modinv(a[r][c], p);
        for x in a[r].iter_mut() {
            *x = *x * inv % p;
        }
        for i in 0..a.len() {
            if i != r && a[i][c] != 0 {
                let fct = a[i][c];
                let (src, dst) = if i < r {
                    let (lo, hi) = a.split_at_mut(r);
                    (&hi[0], &mut lo[i])
                } else {
                    let (lo, hi) = a.split_at_mut(i);
                    (&lo[r], &mut hi[0])
                };
                for (d, s) in dst.iter_mut().zip(src.iter()) {
                    *d = (*d + p - fct * s % p) % p;
                }
            }
        }
        piv.push(c);
        r += 1;
    }
    piv
}

/// Sage's `M.left_kernel().basis()` for M (m x ncols) over GF(p): the reduced
/// echelon basis of {v : v M = 0}. Rows of [M | I] are reduced on the M part;
/// the identity part of the zero rows spans the left kernel; that span is then
/// put in reduced echelon form (unique for the space).
pub fn left_kernel_echelon(mat: &[Vec<u64>], ncols: usize, p: u64) -> Vec<Vec<u64>> {
    let m = mat.len();
    let mut aug: Vec<Vec<u64>> = (0..m)
        .map(|i| {
            let mut r = mat[i].clone();
            r.extend((0..m).map(|t| (t == i) as u64));
            r
        })
        .collect();
    let piv = rref(&mut aug, ncols, p);
    let rank = piv.len();
    let mut ker: Vec<Vec<u64>> = aug[rank..].iter().map(|r| r[ncols..].to_vec()).collect();
    let kp = rref(&mut ker, m, p);
    ker.truncate(kp.len());
    ker
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn kernel_is_kernel_and_echelon() {
        let p = P_ORD;
        let mut st = 7u64;
        let mut nxt = || {
            st = st.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            (st >> 33) % p
        };
        for (m, c) in [(39usize, 29usize), (12, 5), (5, 9), (8, 8)] {
            let mat: Vec<Vec<u64>> = (0..m).map(|_| (0..c).map(|_| if nxt() % 3 == 0 { nxt() } else { 0 }).collect()).collect();
            let b = left_kernel_echelon(&mat, c, p);
            let mut t = mat.clone();
            let rank = rref(&mut t, c, p).len();
            assert_eq!(b.len(), m - rank);
            for v in &b {
                for j in 0..c {
                    let s = (0..m).fold(0u64, |a, i| (a + v[i] * mat[i][j]) % p);
                    assert_eq!(s, 0);
                }
            }
            // reduced echelon: leading entry 1, strictly increasing, zero elsewhere in its column
            let leads: Vec<usize> = b.iter().map(|v| v.iter().position(|&x| x != 0).unwrap()).collect();
            for (k, &l) in leads.iter().enumerate() {
                assert_eq!(b[k][l], 1);
                if k > 0 {
                    assert!(l > leads[k - 1]);
                }
                for (k2, v) in b.iter().enumerate() {
                    if k2 != k {
                        assert_eq!(v[l], 0);
                    }
                }
            }
        }
    }

    #[test]
    fn setup_matches_archive() {
        let s = Setup::new();
        assert_eq!(s.reps.len(), 29);
        assert_eq!(s.v_points, 33);
        // archived P (volcano-ic/rho-arm-20261014/results/runtime-info.json) and lambda
        let px = (1 << 16) | (1 << 15) | (1 << 14) | (1 << 13) | (1 << 12) | (1 << 11) | (1 << 10) | (1 << 9)
            | (1 << 8) | (1 << 7) | (1 << 4) | (1 << 2) | 1;
        let py = (1 << 18) | (1 << 13) | (1 << 12) | (1 << 11) | (1 << 8) | (1 << 5) | (1 << 3) | 1;
        assert_eq!(s.p, Some((px, py)));
        assert_eq!(s.tau_eigen(s.p), 41811);
    }

    #[test]
    fn archived_instance_0() {
        // run 38520305068 tau6 instance 0 (rho-arm-20261014 results/arms.jsonl, Sage).
        let s = Setup::new();
        let q = s.f.mul_pt(crate::testvec::ARCH0_SCALAR, s.p);
        let mut rels = vec![];
        let st = s.tau_dlp(q, crate::testvec::ARCH0_SEED, &mut rels, None, &|| 0.0);
        assert_eq!((st.targets, st.gb_calls, st.spurious, st.relations as u64, st.log),
                   crate::testvec::ARCH0_COUNTS);
        assert!(st.recovered);
    }
}
