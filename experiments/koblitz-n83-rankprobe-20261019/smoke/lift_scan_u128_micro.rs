// Local diagnostic: rustc -C opt-level=3 --edition 2021 smoke/lift_scan_u128_micro.rs (from the experiment directory).
#[path = "../lift2/src/lib.rs"]
#[allow(dead_code)]
mod lift2;
use std::hint::black_box;
use std::time::Instant;
const N: u32 = 83;
const MASK: u128 = (1u128 << 83) - 1;
#[inline(always)] fn rotl(x: u128, s: u32) -> u128 { ((x << s) | (x >> (N - s))) & MASK }
#[inline(always)] fn lift_u128(x: u128) -> (u128, u32) {
    if x == 0 || x == MASK { return (x, 0); }
    let z = !x & MASK;
    let mut pow = [0u128; 7];
    pow[0] = z;
    pow[1] = pow[0] & rotl(pow[0], 1);
    pow[2] = pow[1] & rotl(pow[1], 2);
    pow[3] = pow[2] & rotl(pow[2], 4);
    pow[4] = pow[3] & rotl(pow[3], 8);
    pow[5] = pow[4] & rotl(pow[4], 16);
    pow[6] = pow[5] & rotl(pow[5], 32);
    let mut run = z;
    macro_rules! lift { ($k:expr) => {{ let next = pow[$k] & rotl(run, 1 << $k); let m = lift2::barrier(0u64.wrapping_sub((next != 0) as u64)) as i64 as i128 as u128; run = (next & m) | (run & !m); }}; }
    lift!(6); lift!(5); lift!(4); lift!(3); lift!(2); lift!(1); lift!(0);
    let mut best = MASK; let mut best_shift = 0u32;
    let mut rem = run;
    while rem != 0 {
        let p = rem.trailing_zeros();
        rem &= rem - 1;
        let s = N - 1 - p;
        let v = rotl(x, s);
        if v < best || (v == best && s < best_shift) { best = v; best_shift = s; }
    }
    (best, best_shift)
}
fn main() {
    let mut seed = 0x1234_5678u64;
    let mut next = || { seed ^= seed << 13; seed ^= seed >> 7; seed ^= seed << 17; seed };
    let data: Vec<u128> = (0..1 << 16).map(|_| ((next() as u128) | ((next() as u128) << 64)) & MASK).collect();
    for &v in &data { assert_eq!(lift_u128(v), lift2::lift_scan_wide(v, 83)); assert_eq!(lift_u128(v), lift2::full_scan_u128(v, 83)); }
    for round in 0..5 {
        let t = Instant::now(); let mut acc = 0u128;
        for _ in 0..50 { for &v in &data { let (c, s) = lift2::lift_scan_wide(black_box(v), 83); acc ^= c ^ s as u128; } }
        let a = t.elapsed().as_nanos() as f64 / (50.0 * data.len() as f64);
        let t = Instant::now();
        for _ in 0..50 { for &v in &data { let (c, s) = lift_u128(black_box(v)); acc ^= c ^ s as u128; } }
        let b = t.elapsed().as_nanos() as f64 / (50.0 * data.len() as f64);
        println!("round {round}: lift2 {a:.1} ns, u128 {b:.1} ns  ({})", acc & 1);
    }
}
