#[path = "../lift2/src/lib.rs"]
mod lift2;
use std::hint::black_box;
use std::time::Instant;
use std::arch::x86_64::*;

const N: u32 = 83;
const M83: u128 = (1u128 << 83) - 1;

// software reference: cyclic product in F2[X]/(X^83+1)
fn cmul_ref(a: u128, b: u128) -> u128 {
    let mut r = 0u128;
    for i in 0..83 { if (a >> i) & 1 == 1 { r ^= ((b << i) | (b >> (83 - i))) & M83; } }
    // careful: (b<<i) may exceed bits; rotate within 83 bits
    r
}
fn rotl83(v: u128, s: u32) -> u128 { if s == 0 { v } else { ((v << s) | (v >> (83 - s))) & M83 } }
fn cmul_ref2(a: u128, b: u128) -> u128 {
    let mut r = 0u128;
    for i in 0..83 { if (a >> i) & 1 == 1 { r ^= rotl83(b, i); } }
    r
}
fn key_ref(x: u128) -> u128 {
    let x2 = cmul_ref2(x, x); let x3 = cmul_ref2(x2, x); let x5 = cmul_ref2(x3, x2);
    let mut t = x5; for _ in 0..4 { t = cmul_ref2(t, t); } // x^80
    cmul_ref2(t, x3)
}

#[inline(always)]
unsafe fn clmul(a: u64, b: u64) -> u128 {
    let r = _mm_clmulepi64_si128(_mm_set_epi64x(0, a as i64), _mm_set_epi64x(0, b as i64), 0);
    let lo = _mm_cvtsi128_si64(r) as u64; let hi = _mm_extract_epi64(r, 1) as u64;
    (lo as u128) | ((hi as u128) << 64)
}
#[inline(always)]
unsafe fn fold(lo: u128, hi: u128) -> u128 {
    // product P = lo + hi*2^128, deg < 165; reduce mod X^83+1
    let low = lo & M83;
    let high = (lo >> 83) | (hi << 45); // bits 83..
    (low ^ high) & M83 // high < 2^82, no second fold
}
#[inline(always)]
unsafe fn cmul(a: u128, b: u128) -> u128 {
    let (a0, a1) = (a as u64, (a >> 64) as u64); let (b0, b1) = (b as u64, (b >> 64) as u64);
    let p00 = clmul(a0, b0); let p11 = clmul(a1, b1);
    let mid = clmul(a0, b1) ^ clmul(a1, b0);
    let lo = p00 ^ (mid << 64); let hi = p11 ^ (mid >> 64);
    fold(lo, hi)
}
#[inline(always)]
unsafe fn csqr(a: u128) -> u128 {
    let p00 = clmul(a as u64, a as u64); let p11 = clmul((a >> 64) as u64, (a >> 64) as u64);
    fold(p00, p11)
}
#[inline(always)]
unsafe fn key(x: u128) -> u128 {
    let x2 = csqr(x); let x3 = cmul(x2, x); let x5 = cmul(x3, x2);
    let x80 = csqr(csqr(csqr(csqr(x5))));
    cmul(x80, x3)
}
#[target_feature(enable = "pclmulqdq,sse4.1")]
unsafe fn keys_batch(src: &[u128], dst: &mut [u128]) { for (s, d) in src.iter().zip(dst.iter_mut()) { *d = key(*s); } }
#[target_feature(enable = "pclmulqdq,sse4.1")]
unsafe fn keys_chain(x0: u128, reps: usize) -> u128 { let mut x = x0; for _ in 0..reps { x = key(x) ^ 1; } x }

#[inline(always)]
unsafe fn cl(a: u64, b: u64) -> __m128i { _mm_clmulepi64_si128(_mm_cvtsi64_si128(a as i64), _mm_cvtsi64_si128(b as i64), 0) }
#[inline(always)]
unsafe fn lo64(v: __m128i) -> u64 { _mm_cvtsi128_si64(v) as u64 }
#[inline(always)]
unsafe fn hi64(v: __m128i) -> u64 { _mm_extract_epi64(v, 1) as u64 }
// product of (a0,a1),(b0,b1) with a1,b1 < 2^19 via Karatsuba, folded mod X^83+1
#[inline(always)]
unsafe fn kmul(a0: u64, a1: u64, b0: u64, b1: u64) -> (u64, u64) {
    let p00 = cl(a0, b0); let p11 = cl(a1, b1); let pm = cl(a0 ^ a1, b0 ^ b1);
    let mid = _mm_xor_si128(_mm_xor_si128(pm, p00), p11);
    // P = p00 + mid<<64 + p11<<128 ; limbs q0,q1,q2
    let q0 = lo64(p00); let q1 = hi64(p00) ^ lo64(mid); let q2 = hi64(mid) ^ lo64(p11);
    fold3(q0, q1, q2)
}
#[inline(always)]
fn fold3(q0: u64, q1: u64, q2: u64) -> (u64, u64) {
    // low83 = q0, q1 & (2^19-1); high = P>>83 = (q1>>19 | q2<<45, q2>>19)
    let h0 = (q1 >> 19) | (q2 << 45); let h1 = q2 >> 19;
    (q0 ^ h0, (q1 & 0x7FFFF) ^ h1)
}
#[inline(always)]
unsafe fn ksqr(a0: u64, a1: u64) -> (u64, u64) {
    let p00 = cl(a0, a0); let p11 = cl(a1, a1);
    fold3(lo64(p00), hi64(p00), lo64(p11))
}
#[inline(always)]
unsafe fn key2(x: u128) -> u128 {
    let (x0, x1) = (x as u64, (x >> 64) as u64);
    let (s0, s1) = ksqr(x0, x1);
    let (t0, t1) = kmul(s0, s1, x0, x1); // x^3
    let (f0, f1) = kmul(t0, t1, s0, s1); // x^5
    let (mut e0, mut e1) = (f0, f1);
    for _ in 0..4 { let r = ksqr(e0, e1); e0 = r.0; e1 = r.1; }
    let (k0, k1) = kmul(e0, e1, t0, t1);
    (k0 as u128) | ((k1 as u128) << 64)
}
#[target_feature(enable = "pclmulqdq,sse4.1")]
unsafe fn keys2_batch(src: &[u128], dst: &mut [u128]) { for (s, d) in src.iter().zip(dst.iter_mut()) { *d = key2(*s); } }

fn lift_batch(src: &[u128], dst: &mut [u128]) { for (s, d) in src.iter().zip(dst.iter_mut()) { *d = lift2::lift_scan_wide(*s, N).0; } }

fn build_bench() {
    let slots_n: usize = 1 << 26;
    let mut s = 0x9E3779B97F4A7C15u64;
    let mut rnd = || { s ^= s << 13; s ^= s >> 7; s ^= s << 17; s };
    let shift = 128 - slots_n.trailing_zeros();
    let slot = |k: u128| (k.wrapping_mul(0x9E37_79B9_7F4A_7C15_9E37_79B9_7F4A_7C15) >> shift) as usize;
    let mask = slots_n - 1;
    let t = Instant::now();
    let mut a = vec![0u128; slots_n];
    for _ in 0..29_878_182u64 {
        let k = (((rnd() as u128) << 64) | rnd() as u128) & M83;
        let mut h = slot(k);
        while a[h] != 0 { h = (h + 1) & mask; }
        a[h] = (1u128 << 127) | k;
    }
    println!("first build {:.2} s", t.elapsed().as_secs_f64());
    for mode in 0..3 {
        let t = Instant::now();
        let mut b = vec![0u128; slots_n];
        let mut batch: Vec<(u128, u128)> = Vec::with_capacity(256);
        let mut n = 0usize;
        let mut flush = |b: &mut Vec<u128>, batch: &mut Vec<(u128,u128)>| {
            let mut keys = vec![0u128; batch.len()];
            let src: Vec<u128> = batch.iter().map(|x| x.0).collect();
            unsafe { keys2_batch(&src, &mut keys) };
            if mode >= 1 { for &k in &keys { unsafe { std::arch::x86_64::_mm_prefetch(b.as_ptr().wrapping_add(slot(k)) as *const i8, std::arch::x86_64::_MM_HINT_T0); } } }
            for (&k, &(_, v)) in keys.iter().zip(batch.iter()) {
                let mut h = slot(k);
                while b[h] != 0 { h = (h + 1) & mask; }
                b[h] = v | k;
            }
            batch.clear();
        };
        let bs = if mode == 2 { 16 } else { 256 };
        for &w in &a { if w != 0 { batch.push((w & M83, w & !M83)); n += 1; if batch.len() == bs { flush(&mut b, &mut batch); } } }
        flush(&mut b, &mut batch);
        println!("mode {} rebuild {:.2} s ({} entries)", mode, t.elapsed().as_secs_f64(), n);
        black_box(&b);
    }
    // mode 3: keys in batches into a temp word array with a bucket histogram, counting-sort scatter, then insert in bucket order
    for bits in [8u32, 12] {
        let t = Instant::now();
        let nb = 1usize << bits;
        let bshift = slots_n.trailing_zeros() - bits;
        let mut words: Vec<u128> = Vec::with_capacity(29_878_182);
        let mut src: Vec<u128> = Vec::with_capacity(256);
        let mut keys = vec![0u128; 256];
        let mut counts = vec![0usize; nb + 1];
        let mut emit = |src: &mut Vec<u128>, words: &mut Vec<u128>, counts: &mut Vec<usize>| {
            let m = src.len();
            let k: Vec<u128> = src.iter().map(|w| w & M83).collect();
            unsafe { keys2_batch(&k, &mut keys[..m]) };
            for i in 0..m { let w = (src[i] & !M83) | keys[i]; counts[(slot(keys[i]) >> bshift) + 1] += 1; words.push(w); }
            src.clear();
        };
        for &w in &a { if w != 0 { src.push(w); if src.len() == 256 { emit(&mut src, &mut words, &mut counts); } } }
        emit(&mut src, &mut words, &mut counts);
        for i in 0..nb { counts[i + 1] += counts[i]; }
        let mut sorted = vec![0u128; words.len()];
        let mut pos = counts.clone();
        for &w in &words { let bk = slot(w & M83) >> bshift; sorted[pos[bk]] = w; pos[bk] += 1; }
        drop(words);
        let t2 = t.elapsed().as_secs_f64();
        let mut b = vec![0u128; slots_n];
        for &w in &sorted { let k = w & M83; let mut h = slot(k); while b[h] != 0 { h = (h + 1) & mask; } b[h] = w; }
        println!("mode 3 bits {} rebuild {:.2} s (sort part {:.2})", bits, t.elapsed().as_secs_f64(), t2);
        black_box(&b);
    }
}
fn main() {
    if std::env::args().nth(1).as_deref() == Some("build") { build_bench(); return; }
    assert!(is_x86_feature_detected!("pclmulqdq"));
    let mut s = 0x1234_5678_9abc_def0u64;
    let mut rnd = || { s ^= s << 13; s ^= s >> 7; s ^= s << 17; s };
    let words: Vec<u128> = (0..4096).map(|_| (((rnd() as u128) << 64) | rnd() as u128) & M83).collect();
    // correctness
    for &w in words.iter().take(300) {
        let k = unsafe { let mut d=[0u128]; keys_batch(&[w], &mut d); d[0] };
        assert_eq!(k, key_ref(w));
        let r = (rnd() % 83) as u32;
        let k2 = unsafe { let mut d=[0u128]; keys_batch(&[rotl83(w, r)], &mut d); d[0] };
        assert_eq!(k, k2, "invariance");
        let k3 = unsafe { let mut d=[0u128]; keys2_batch(&[w], &mut d); d[0] }; assert_eq!(k3, k);
    }
    let _ = cmul_ref;
    println!("correctness ok");
    let mut dst = vec![0u128; words.len()];
    let rounds = 15; let reps = 200;
    let mut tk2 = vec![]; let mut tk = vec![]; let mut tl = vec![]; let mut tc = vec![];
    for _ in 0..rounds {
        let t = Instant::now(); for _ in 0..reps { unsafe { keys_batch(black_box(&words), &mut dst) }; black_box(&dst); }
        tk.push(t.elapsed().as_nanos() as f64 / (reps * words.len()) as f64);
        let t = Instant::now(); for _ in 0..reps { unsafe { keys2_batch(black_box(&words), &mut dst) }; black_box(&dst); }
        tk2.push(t.elapsed().as_nanos() as f64 / (reps * words.len()) as f64);
        let t = Instant::now(); for _ in 0..reps { lift_batch(black_box(&words), &mut dst); black_box(&dst); }
        tl.push(t.elapsed().as_nanos() as f64 / (reps * words.len()) as f64);
        let t = Instant::now(); black_box(unsafe { keys_chain(black_box(words[0]), reps * 1000) });
        tc.push(t.elapsed().as_nanos() as f64 / (reps * 1000) as f64);
    }
    tk2.sort_by(|a, b| a.partial_cmp(b).unwrap()); println!("key2 (karatsuba,u64) ns/word median {:.2} min {:.2}", tk2[7], tk2[0]);
    for v in [&mut tk, &mut tl, &mut tc] { v.sort_by(|a, b| a.partial_cmp(b).unwrap()); }
    println!("key batch ns/word median {:.2} (min {:.2} max {:.2})", tk[7], tk[0], tk[14]);
    println!("lift_scan ns/word median {:.2} (min {:.2} max {:.2})", tl[7], tl[0], tl[14]);
    println!("key latency chain ns/word median {:.2}", tc[7]);
}
