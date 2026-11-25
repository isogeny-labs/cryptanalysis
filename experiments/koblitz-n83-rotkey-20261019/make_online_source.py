#!/usr/bin/env python3
"""Derive the rotation-key n=83 K600 producer from the rank-probe producer, exactly.

Input: `snapshots/r770/examples/koblitz_orbit_dlp_fast_online_logcache.rs`
(crypto 770f6a69 plus B's `ic_log_cache.patch`, restored and digest-checked
by `restore.py`).

1. `make_rankprobe_source.py` is `koblitz-n83-rankprobe-20261019`'s
   `make_online_source.py` (PR #980), verbatim, with its verbatim parents
   (`make_rankcut_source.py`, `make_stacked_source.py`,
   `make_tablefilter_source.py`, `make_probepipe_source.py`,
   `make_combined_source.py`). Its derived text must hash to the rank-probe
   protocol's frozen `online_source_sha256` (`RANKPROBE_SHA256` below,
   `d4394df3...`). That is the rank-probe producer (arms cP / kP of run
   39214027289, the current n = 83 baseline).
2. `rotkey_edits`: counted, exact replacements in the wide module add two
   values to `KIC_RANK_SOLVE`, read only by the rank stage:

   * `s3`, `padd`, `frame`, `frame_plant`: unchanged.
   * `rotkey`: the rank-probe loop (`frame`) with its probe key replaced.
     The frame loop keys every partner word v by its least rotation
     (lift_scan, `(min_s rotl(v, s), s)`) and looks that up in the 16-byte
     compact root table. `rotkey` keys v by rotkey(v) = v^83 in the ring
     R = F2[X]/(X^83 + 1), in which a normal-basis word is an element and
     the Frobenius is multiplication by X. (X^s v)^83 = v^83, so the key is
     rotation invariant; it is also COMPLETE: X^83 + 1 = (X + 1) Phi_83
     with Phi_83 irreducible over F2 (2 has order 82 mod 83), so
     R = F2 x F_{2^82} and v^83 = w^83 forces v = X^s w (the 83rd roots of
     unity of F_{2^82} are the powers of X). So rotkey(v) = rotkey(w) iff
     lift_scan(v).0 = lift_scan(w).0: there are no false hits and no
     merged classes, by algebra, and the build records the measured
     collision count on the stored set (compact entries minus rotation-key
     entries). At the start of the rank stage, inside its timed interval,
     a second 16-byte table with the compact table's slot count is filled
     from the compact table: key rotkey(c) for every stored canonical word
     c, the same packed value. Because rotkey is injective on canonical
     words, it is the same key -> value map. The probe loop computes
     rotkey of every partner word of the state in one batch (carry-less
     multiplication, pclmulqdq: 5 squarings and 3 multiplications in R),
     prefetches the rotation-key slot, and looks it up. lift_scan runs only
     at a rotation-key hit, where it supplies the partner shift, and every
     such hit is verified against the compact table (panic unless the
     canonical lookup returns the same value). So every probe sees the hit
     status of the frame loop, the first hit, the exact-order resolution,
     the relation and the probe count are the frame loop's.
   * `rotkey_plant` (planted positive control): `rotkey`, plus on every
     probe the removed work redone: lift_scan of the partner word, its
     compact-table lookup, and rotkey of the canonical word, checked equal
     to the emitted key and to the rotation-key lookup (panic on any
     difference), otherwise discarded.

   The summary records `rank_solve`, the rank-cut and frame counters and
   `rank_rotkey_*` (tables built, build ms, compact and rotation-key
   entries, collisions, the kernel, verified hits, planted probes checked).
   Every other path (setup, index, online target scan, `s3`, `padd`,
   `frame`) is the rank-probe producer's, byte for byte.

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_rankprobe_source as rankprobe  # noqa: E402  (koblitz-n83-rankprobe-20261019, verbatim)

EXAMPLES = HERE / "snapshots" / "r770" / "examples"
OUTPUT = EXAMPLES / "koblitz_orbit_dlp_fast_online_rotkey.rs"
# protocol.json "sources.online_source_sha256" of koblitz-n83-rankprobe-20261019 (PR #980).
RANKPROBE_SHA256 = "d4394df35d065afbfb05022eac3006492239cc64b94de16fba501322cb578bb5"
WIDE_START = rankprobe.WIDE_START
WIDE_END = rankprobe.WIDE_END
replace = rankprobe.replace

HEAD_OLD = """// rank-cut loop in the target's Frobenius frame, exact to the rank-cut loop.
"""
HEAD_NEW = HEAD_OLD + """// koblitz-n83-rotkey-20261019: derived from the rank-probe producer by
// make_online_source.py; adds KIC_RANK_SOLVE=rotkey | rotkey_plant, the
// frame loop probing a rotation-invariant key (v^83 in F2[X]/(X^83+1)),
// lift_scan only at a hit, exact to the frame loop.
"""

INDEX_FIELD_OLD = """        fold: Option<Fold128>,
"""
INDEX_FIELD_NEW = INDEX_FIELD_OLD + """        // koblitz-n83-rotkey-20261019: the rank stage's rotation-key table,
        // built from `compact` at the start of an in-process rank stage.
        rotkey: std::cell::OnceCell<CompactRootTable128>,
"""

INDEX_INIT_OLD = """            filter_build_ms,
            fold,
"""
INDEX_INIT_NEW = INDEX_INIT_OLD + """            rotkey: std::cell::OnceCell::new(),
"""

SCRATCH_OLD = """        frame: FrameScratch128,
"""
SCRATCH_NEW = SCRATCH_OLD + """        rot: Vec<RotProbe128>,
"""

SCRATCH_INIT_OLD = """                frame: FrameScratch128::with_capacity(entries),
"""
SCRATCH_INIT_NEW = SCRATCH_INIT_OLD + """                rot: Vec::with_capacity(2 * entries),
"""

ROTKEY_CODE = r'''
    // ── koblitz-n83-rotkey-20261019: the rotation-invariant probe key ──
    //
    // R = F2[X]/(X^83 + 1). A normal-basis word v (bit i = coefficient of
    // beta^(2^i)) is read as an element of R; the Frobenius rotates the word,
    // which is multiplication by X^(+-1) in R. rotkey(v) = v^83 in R:
    // * invariant: (X^s v)^83 = X^(83 s) v^83 = v^83;
    // * complete: X^83 + 1 = (X + 1) Phi_83 (coprime factors) and Phi_83 is
    //   irreducible over F2 because 2 has order 82 mod 83, so
    //   R = F2 x F_{2^82}. v^83 = w^83 gives the same parity (a^83 = a in
    //   F2) and xi^83 = eta^83 in F_{2^82}; so xi = eta = 0 or xi / eta is an
    //   83rd root of unity, and those are exactly the powers of X (X has
    //   order 83 in F_{2^82}^*). Hence v = X^s w.
    // So rotkey(v) = rotkey(w) iff v and w are rotations of each other iff
    // their lift_scan canonical words are equal. Keys are 83-bit, so they
    // fit the compact slot's key field.
    const PIPE_ROTKEY: u8 = 11;
    const PIPE_ROTKEY_PLANT: u8 = 12;
    const ROTKEY_N: u32 = 83;
    const ROTKEY_MASK: u128 = (1u128 << ROTKEY_N) - 1;

    static ROTKEY_BUILDS: AtomicU64 = AtomicU64::new(0);
    static ROTKEY_BUILD_NS: AtomicU64 = AtomicU64::new(0);
    static ROTKEY_COMPACT_ENTRIES: AtomicU64 = AtomicU64::new(0);
    static ROTKEY_TABLE_ENTRIES: AtomicU64 = AtomicU64::new(0);
    static ROTKEY_HIT_VERIFIES: AtomicU64 = AtomicU64::new(0);
    static ROTKEY_PLANT_CHECKED: AtomicU64 = AtomicU64::new(0);

    /// `KIC_RANK_SOLVE` values of this experiment; `None` defers to the
    /// rank-probe selector.
    fn rank_solve_rotkey_from_env() -> Option<(u8, &'static str)> {
        match std::env::var("KIC_RANK_SOLVE").as_deref() {
            Ok("rotkey") => Some((PIPE_ROTKEY, "rotkey")),
            Ok("rotkey_plant") => Some((PIPE_ROTKEY_PLANT, "rotkey_plant")),
            _ => None,
        }
    }

    /// One partner probe of the rotation-key loop.
    #[derive(Clone, Copy)]
    struct RotProbe128 {
        key: u128,
        partner: u128,
        candidate: u32,
    }

    /// Reference product in R: shifted XORs (tests and the portable path).
    fn rotkey_mul_soft(a: u128, b: u128) -> u128 {
        let rotl = |v: u128, s: u32| -> u128 {
            if s == 0 { v } else { ((v << s) | (v >> (ROTKEY_N - s))) & ROTKEY_MASK }
        };
        let mut product = 0u128;
        for i in 0..ROTKEY_N {
            if (a >> i) & 1 == 1 {
                product ^= rotl(b, i);
            }
        }
        product
    }

    /// v^83 in R by the chain v^2, v^3, v^5, v^10, v^20, v^40, v^80, v^83.
    fn rotkey_soft(v: u128) -> u128 {
        let v = v & ROTKEY_MASK;
        let v2 = rotkey_mul_soft(v, v);
        let v3 = rotkey_mul_soft(v2, v);
        let mut t = rotkey_mul_soft(v3, v2);
        for _ in 0..4 {
            t = rotkey_mul_soft(t, t);
        }
        rotkey_mul_soft(t, v3)
    }

    /// Reduce the 165-bit product (q0, q1, q2) mod X^83 + 1: the bits at
    /// 83 and up fold onto 0 and up (they are below 2^82, one fold).
    #[inline(always)]
    fn rotkey_fold3(q0: u64, q1: u64, q2: u64) -> (u64, u64) {
        let h0 = (q1 >> 19) | (q2 << 45);
        let h1 = q2 >> 19;
        (q0 ^ h0, (q1 & 0x7_FFFF) ^ h1)
    }

    #[cfg(target_arch = "x86_64")]
    mod rotkey_clmul {
        use std::arch::x86_64::*;

        #[inline(always)]
        unsafe fn cl(a: u64, b: u64) -> __m128i {
            _mm_clmulepi64_si128(_mm_cvtsi64_si128(a as i64), _mm_cvtsi64_si128(b as i64), 0)
        }

        #[inline(always)]
        unsafe fn lo(v: __m128i) -> u64 {
            _mm_cvtsi128_si64(v) as u64
        }

        #[inline(always)]
        unsafe fn hi(v: __m128i) -> u64 {
            _mm_extract_epi64(v, 1) as u64
        }

        /// Product in R of (a0 + a1 2^64)(b0 + b1 2^64), a1, b1 < 2^19,
        /// three carry-less multiplications (Karatsuba).
        #[inline(always)]
        unsafe fn mul(a: (u64, u64), b: (u64, u64)) -> (u64, u64) {
            let p00 = cl(a.0, b.0);
            let p11 = cl(a.1, b.1);
            let pm = cl(a.0 ^ a.1, b.0 ^ b.1);
            let mid = _mm_xor_si128(_mm_xor_si128(pm, p00), p11);
            super::rotkey_fold3(lo(p00), hi(p00) ^ lo(mid), hi(mid) ^ lo(p11))
        }

        /// Square in R: two carry-less squarings (no cross term in char 2).
        #[inline(always)]
        unsafe fn sqr(a: (u64, u64)) -> (u64, u64) {
            let p00 = cl(a.0, a.0);
            let p11 = cl(a.1, a.1);
            super::rotkey_fold3(lo(p00), hi(p00), lo(p11))
        }

        /// v^83 in R, the same chain as `rotkey_soft`.
        #[inline(always)]
        pub(super) unsafe fn key(v: u128) -> u128 {
            let x = (v as u64, ((v >> 64) as u64) & 0x7_FFFF);
            let x2 = sqr(x);
            let x3 = mul(x2, x);
            let mut t = mul(x3, x2);
            for _ in 0..4 {
                t = sqr(t);
            }
            let k = mul(t, x3);
            (k.0 as u128) | ((k.1 as u128) << 64)
        }

        /// Keys of a batch of probes, each followed by the prefetch of its
        /// home slot; independent keys overlap in the out-of-order core.
        #[target_feature(enable = "pclmulqdq,sse2,sse4.1")]
        pub(super) unsafe fn fill(probes: &mut [super::RotProbe128], table: &super::CompactRootTable128) {
            for probe in probes.iter_mut() {
                probe.key = key(probe.partner);
                table.prefetch(probe.key);
            }
        }

        #[target_feature(enable = "pclmulqdq,sse2,sse4.1")]
        pub(super) unsafe fn one(v: u128) -> u128 {
            key(v)
        }
    }

    /// The kernel the rank stage uses: carry-less multiplication when the
    /// CPU has it (the protocol's gate requires it), else the reference.
    fn rotkey_kernel() -> &'static str {
        #[cfg(target_arch = "x86_64")]
        {
            if is_x86_feature_detected!("pclmulqdq") && is_x86_feature_detected!("sse4.1") {
                return "pclmulqdq";
            }
        }
        "soft"
    }

    #[inline(always)]
    fn rotkey_fill(probes: &mut [RotProbe128], table: &CompactRootTable128, clmul: bool) {
        #[cfg(target_arch = "x86_64")]
        {
            if clmul {
                // SAFETY: `clmul` is true only when the CPU reports
                // pclmulqdq and SSE4.1 (`rotkey_kernel`).
                unsafe { rotkey_clmul::fill(probes, table) };
                return;
            }
        }
        let _ = clmul;
        for probe in probes.iter_mut() {
            probe.key = rotkey_soft(probe.partner);
            table.prefetch(probe.key);
        }
    }

    fn rotkey_one(v: u128, clmul: bool) -> u128 {
        #[cfg(target_arch = "x86_64")]
        {
            if clmul {
                // SAFETY: as in `rotkey_fill`.
                return unsafe { rotkey_clmul::one(v) };
            }
        }
        let _ = clmul;
        rotkey_soft(v)
    }

    /// The rotation-key table of `compact`: the same slot count (so the same
    /// load factor), key rotkey(c) for every stored canonical word c, the
    /// same packed value. Keys are computed in batches by the probe kernel.
    fn rotkey_table128(compact: &CompactRootTable128, clmul: bool) -> CompactRootTable128 {
        let mut table = CompactRootTable128 { slots: vec![0; compact.slots.len()], shift: compact.shift, len: 0 };
        let mut batch: Vec<RotProbe128> = Vec::with_capacity(256);
        let mut values: Vec<u64> = Vec::with_capacity(256);
        let flush = |table: &mut CompactRootTable128, batch: &mut Vec<RotProbe128>, values: &mut Vec<u64>| {
            rotkey_fill(batch, table, clmul);
            for (probe, &value) in batch.iter().zip(values.iter()) {
                table.insert_if_absent(probe.key, value);
            }
            batch.clear();
            values.clear();
        };
        for &word in &compact.slots {
            if word == 0 {
                continue;
            }
            batch.push(RotProbe128 { key: 0, partner: word & COMPACT_KEY_MASK, candidate: 0 });
            values.push(CompactRootTable128::expand(word));
            if batch.len() == 256 {
                flush(&mut table, &mut batch, &mut values);
            }
        }
        flush(&mut table, &mut batch, &mut values);
        table
    }

    /// Build `index.rotkey` once (inside the caller's timed interval) and
    /// record its counters; `compact.len - rotkey.len` is the number of
    /// stored classes whose keys collided (0 by the completeness argument).
    fn rotkey_install(index: &Index128, clmul: bool) {
        let compact = index.compact.as_ref().expect("the compact root table");
        let started = Instant::now();
        let table = rotkey_table128(compact, clmul);
        ROTKEY_BUILD_NS.fetch_add(started.elapsed().as_nanos() as u64, Ordering::Relaxed);
        ROTKEY_BUILDS.fetch_add(1, Ordering::Relaxed);
        ROTKEY_COMPACT_ENTRIES.store(compact.len as u64, Ordering::Relaxed);
        ROTKEY_TABLE_ENTRIES.store(table.len as u64, Ordering::Relaxed);
        assert!(index.rotkey.set(table).is_ok(), "the rotation-key table is built once");
    }

    /// [`scan_state128_frame`] (`PIPE_FRAME`) probing the rotation key: the
    /// same candidates, partner words and order, so the same probe
    /// positions; each probe looks up rotkey(partner) in `index.rotkey`,
    /// which holds the compact table's map under the rotation key, so it
    /// hits exactly when the frame loop's canonical lookup hits. lift_scan
    /// runs only at a hit, for the partner shift, and the hit is verified
    /// against the compact table. The frame loop's exact-order resolution
    /// then runs unchanged.
    #[inline(always)]
    #[allow(clippy::too_many_arguments)]
    fn scan_state128_rotkey<const C: u8, const P: u8>(
        gf: &Gf2_128,
        fast: &FastBinaryCurve128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        index: &Index128,
        base: &Base128,
        target: FastPoint128,
        target_x: u128,
        state: &State128,
        scan: &mut StateScan128,
        probes: &mut u64,
        clock: &mut PhaseClock,
        split: &mut ExtractSplit,
    ) -> Option<Relation128> {
        let n = gf.n;
        let compact = index.compact.as_ref().expect("the compact root table");
        let rk = index.rotkey.get().expect("the rank stage's rotation-key table");
        let clmul = ROTKEY_CLMUL.load(Ordering::Relaxed) != 0;
        let (tx, ty) = target.expect("a target point");
        debug_assert_eq!(tx, target_x);
        let a = fast.a;
        assert_eq!(state.normal_roots.len(), FRAME_ROOTS);
        let mut xk = [0u128; FRAME_ROOTS];
        let mut yk = [0u128; FRAME_ROOTS];
        for (k, &root) in state.normal_roots.iter().enumerate() {
            match frame_root_xy(gf, basis, solver, a, root) {
                Some((x, y)) => {
                    xk[k] = x;
                    yk[k] = y;
                }
                None => {
                    PADD_FALLBACK_STATES.fetch_add(1, Ordering::Relaxed);
                    return scan_state128_filtered::<C, PIPE_COMPACT>(
                        gf, fast, basis, solver, index, base, target, target_x, state, scan,
                        probes, clock, split,
                    );
                }
            }
        }
        frame_build128(&mut scan.frame, basis, a, tx, ty);
        let fr = &mut scan.frame;
        fr.prefix.clear();
        fr.regular.clear();
        let mut product = 1u128;
        for shift in 0..n as usize {
            let xt = fr.x[shift];
            for k in 0..FRAME_ROOTS {
                let regular = xk[k] != xt && xk[k] != 0 && xt != 0;
                fr.prefix.push(product);
                fr.regular.push(regular);
                if regular {
                    product = gf.mul(product, xk[k] ^ xt);
                }
            }
        }
        let count = fr.regular.len();
        split.root_calls += count as u64;
        fr.inverse.clear();
        fr.inverse.resize(count, 0);
        // A product of non-zero field elements is non-zero.
        let mut inverse = invert128(gf, basis, product);
        for i in (0..count).rev() {
            if fr.regular[i] {
                fr.inverse[i] = gf.mul(inverse, fr.prefix[i]);
                inverse = gf.mul(inverse, xk[i % FRAME_ROOTS] ^ fr.x[i / FRAME_ROOTS]);
            }
        }
        let rot = &mut scan.rot;
        rot.clear();
        fr.pair_start.clear();
        for shift in 0..n as usize {
            for k in 0..FRAME_ROOTS {
                let i = shift * FRAME_ROOTS + k;
                let pair: [u128; 2] = if fr.regular[i] {
                    let inverse = fr.inverse[i];
                    let lambda = basis.to_normal.apply(gf.mul(fr.y[shift] ^ yk[k], inverse));
                    let lambda2 = lambda ^ basis.to_normal.apply(gf.mul(xk[k], inverse));
                    let c = fr.normal_c[shift] ^ state.normal_roots[k];
                    // x(T_s +- R_k) in the normal basis, then phi^s.
                    let plus = basis.rotate(basis.rotate(lambda, 1) ^ lambda ^ c, shift as u32);
                    let minus = basis.rotate(basis.rotate(lambda2, 1) ^ lambda2 ^ c, shift as u32);
                    [minus, plus]
                } else {
                    PADD_IRREGULAR_INPUTS.fetch_add(1, Ordering::Relaxed);
                    let xs = basis.to_poly.apply(basis.rotate(state.normal_roots[k], shift as u32));
                    match solver.roots(gf, basis, xs, tx) {
                        Some([first, second]) => {
                            [basis.to_normal.apply(first), basis.to_normal.apply(second)]
                        }
                        None => {
                            fr.pair_start.push(u32::MAX);
                            continue;
                        }
                    }
                };
                fr.pair_start.push(rot.len() as u32);
                for partner in pair {
                    rot.push(RotProbe128 { key: 0, partner, candidate: i as u32 });
                }
            }
        }
        // The rotation keys of the whole state in one batch, each with the
        // prefetch of its home slot.
        rotkey_fill(rot, rk, clmul);
        if P == PIPE_ROTKEY_PLANT {
            // The removed work, redone and discarded: lift_scan of every
            // partner, its canonical lookup and the key of the canonical
            // word, compared with the emitted key and its lookup.
            for probe in rot.iter() {
                let (canonical, _) = target_canonical::<C>(basis, probe.partner);
                assert!(
                    black_box(rotkey_one(canonical, clmul)) == probe.key,
                    "the rotation key differs on the canonical rotation"
                );
                assert!(
                    rk.get(probe.key) == compact.get(canonical),
                    "the rotation-key lookup differs from the canonical lookup"
                );
            }
            ROTKEY_PLANT_CHECKED.fetch_add(rot.len() as u64, Ordering::Relaxed);
        }
        let first = *probes;
        let passes = split.filter_passes;
        let len = rot.len();
        let mut position = 0usize;
        while position < len {
            *probes = first + position as u64 + 1;
            split.filter_passes = passes + position as u64 + 1;
            if rk.get(rot[position].key).is_none() {
                position += 1;
                continue;
            }
            // First hit in this candidate's pair: form its S3 input and
            // evaluate the pair in the S3 order, at the S3 loop's probe
            // positions (the rank-cut loop's resolution).
            let candidate = rot[position].candidate as usize;
            let shift = candidate / FRAME_ROOTS;
            let xs = basis.to_poly.apply(basis.rotate(state.normal_roots[candidate % FRAME_ROOTS], shift as u32));
            let start = fr.pair_start[candidate] as usize;
            let order = if fr.regular[candidate] {
                PADD_RESOLVED_HITS.fetch_add(1, Ordering::Relaxed);
                let exact = solver
                    .roots(gf, basis, xs, tx)
                    .expect("the S3 roots of a regular candidate");
                let emitted = [
                    basis.to_poly.apply(rot[start].partner),
                    basis.to_poly.apply(rot[start + 1].partner),
                ];
                if emitted == exact {
                    [start, start + 1]
                } else {
                    assert_eq!([emitted[1], emitted[0]], exact,
                               "frame partners differ from the S3 roots");
                    PADD_SWAPPED_PAIRS.fetch_add(1, Ordering::Relaxed);
                    [start + 1, start]
                }
            } else {
                [start, start + 1]
            };
            for (rank, &at) in order.iter().enumerate() {
                let exact_position = start + rank;
                if at < position {
                    // Emitted before this hit and already looked up: a miss.
                    continue;
                }
                *probes = first + exact_position as u64 + 1;
                split.filter_passes = passes + exact_position as u64 + 1;
                let probe = rot[at];
                let Some(value) = rk.get(probe.key) else {
                    continue;
                };
                // Exact canonicalization only at a hit, for the partner
                // shift; the hit is verified against the compact table.
                let (canonical, partner_shift) = target_canonical::<C>(basis, probe.partner);
                ROTKEY_HIT_VERIFIES.fetch_add(1, Ordering::Relaxed);
                assert!(compact.get(canonical) == Some(value), "a rotation-key hit is not a canonical hit");
                let left_x = index.shifted[state.left as usize][shift];
                let right_x =
                    index.shifted[state.right as usize][(shift + state.relative as usize) % n as usize];
                let (left2, right2, relative2, stored_shift) = unpack(value);
                let left_shift2 = ((stored_shift + n - partner_shift) % n) as usize;
                let right_shift2 = (left_shift2 + relative2) % n as usize;
                let codes = [
                    left_x,
                    right_x,
                    index.shifted[left2][left_shift2],
                    index.shifted[right2][right_shift2],
                ];
                split.pdp += clock.lap();
                let lifted = lift128(fast, base, &codes, target);
                split.relation_check += clock.lap();
                split.relation_checks += 1;
                if let Some(point_indices) = lifted {
                    return Some(Relation128 {
                        point_indices,
                        x_codes: codes,
                        intermediates: [xs, basis.to_poly.apply(probe.partner)],
                        probes: *probes,
                    });
                }
            }
            position = start + 2;
        }
        *probes = first + len as u64;
        split.filter_passes = passes + len as u64;
        None
    }

    /// 1 when the rank stage runs the carry-less kernel (set with the table).
    static ROTKEY_CLMUL: AtomicU64 = AtomicU64::new(0);

    #[cfg(test)]
    mod rotkey_tests {
        use super::*;

        /// v^n in F2[X]/(X^n + 1) for n <= 64, square and multiply.
        fn small_key(v: u64, n: u32) -> u64 {
            let mask = if n == 64 { u64::MAX } else { (1u64 << n) - 1 };
            let rotl = |v: u64, s: u32| if s == 0 { v } else { ((v << s) | (v >> (n - s))) & mask };
            let mul = |a: u64, b: u64| (0..n).filter(|i| (a >> i) & 1 == 1).fold(0u64, |p, i| p ^ rotl(b, i));
            let (mut result, mut power, mut e) = (1u64, v & mask, n);
            while e > 0 {
                if e & 1 == 1 {
                    result = mul(result, power);
                }
                power = mul(power, power);
                e >>= 1;
            }
            result
        }

        fn necklace(v: u64, n: u32) -> u64 {
            let mask = (1u64 << n) - 1;
            (0..n).map(|s| if s == 0 { v } else { ((v << s) | (v >> (n - s))) & mask }).min().unwrap()
        }

        /// Exhaustive: v^n separates the rotation classes exactly when 2 is
        /// a primitive root mod n (n = 11, 13, 19: complete), and merges
        /// classes when it is not (n = 7, 17: the negative control showing
        /// the irreducibility of Phi_n is what the argument uses).
        #[test]
        fn rotation_key_is_complete_exactly_when_two_is_primitive() {
            for (n, complete) in [(7u32, false), (11, true), (13, true), (17, false), (19, true)] {
                let mut by_key: HashMap<u64, u64> = HashMap::new();
                let mut merged = 0u64;
                for v in 0..(1u64 << n) {
                    let class = necklace(v, n);
                    let key = small_key(v, n);
                    assert_eq!(key, small_key(class, n), "the key is not rotation invariant (n = {n})");
                    match by_key.insert(key, class) {
                        Some(other) if other != class => merged += 1,
                        _ => {}
                    }
                }
                assert_eq!(merged == 0, complete, "n = {n}: {merged} merged classes");
            }
        }

        #[test]
        fn rotation_key_kernel_matches_the_reference_and_is_invariant() {
            let gf = Gf2_128::new(&KoblitzCurve::new(1, 83).unwrap().curve.irreducible);
            let basis = NormalBasis128::new(&gf);
            assert_eq!(basis.n, ROTKEY_N);
            let clmul = rotkey_kernel() == "pclmulqdq";
            let mut seed = 0x5851_F42D_4C95_7F2Du64;
            for trial in 0..2000u64 {
                seed = digest_mix64(seed.wrapping_add(trial));
                let hi = digest_mix64(seed ^ 0xA5A5);
                let v = (((hi as u128) << 64) | seed as u128) & ROTKEY_MASK;
                let key = rotkey_soft(v);
                assert!(key <= ROTKEY_MASK);
                assert_eq!(rotkey_one(v, clmul), key, "kernel differs from the reference");
                let s = (seed % ROTKEY_N as u64) as u32;
                assert_eq!(rotkey_soft(basis.rotate(v, s)), key, "not invariant under rotation");
                let (canonical, _) = super::super::lift2::lift_scan_wide(v, basis.n);
                assert_eq!(rotkey_one(canonical, clmul), key, "differs on the canonical rotation");
            }
            for v in [0u128, 1, ROTKEY_MASK, 3, 1u128 << 82] {
                assert_eq!(rotkey_one(v, clmul), rotkey_soft(v));
            }
            let mut probes: Vec<RotProbe128> = (0..300u64)
                .map(|i| RotProbe128 { key: 0, partner: (digest_mix64(i) as u128 * 0x9E37) & ROTKEY_MASK, candidate: 0 })
                .collect();
            let table = CompactRootTable128::with_capacity(8);
            rotkey_fill(&mut probes, &table, clmul);
            assert!(probes.iter().all(|p| p.key == rotkey_soft(p.partner)));
        }

        #[test]
        fn rotation_key_loops_find_the_frame_relation_with_the_frame_probes() {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let (points, labels, reps, _) = construct_base128(&fast, &curve, b, 9, r);
            let mut by_x: HashMap<u128, Vec<usize>> = HashMap::new();
            for (i, point) in points.iter().enumerate() {
                by_x.entry(point.unwrap().0).or_default().push(i);
            }
            let reps: Vec<u128> = reps.iter().map(|p| p.unwrap()[0]).collect();
            let base = Base128 { points, labels, by_x, columns: 9 };
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            let clmul = rotkey_kernel() == "pclmulqdq";
            ROTKEY_CLMUL.store(clmul as u64, Ordering::Relaxed);
            const FOLDED: IndexMode128 = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_SELECTED };
            let stack = build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, FOLDED);
            let unfolded =
                build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, IndexMode128::UNFOLDED);
            for index in [&stack, &unfolded] {
                rotkey_install(index, clmul);
                let compact = index.compact.as_ref().unwrap();
                let rk = index.rotkey.get().unwrap();
                assert_eq!(rk.len, compact.len, "a stored class collided under the rotation key");
                for &word in compact.slots.iter().filter(|&&w| w != 0) {
                    let canonical = word & COMPACT_KEY_MASK;
                    assert_eq!(rk.get(rotkey_soft(canonical)), compact.get(canonical));
                }
            }
            let mut seed = 0xA076_1D64_78BD_642Fu64;
            let mut solved = 0usize;
            let verifies_before = ROTKEY_HIT_VERIFIES.load(Ordering::Relaxed);
            let checked_before = ROTKEY_PLANT_CHECKED.load(Ordering::Relaxed);
            for trial in 0..40u64 {
                let mut pick = || {
                    seed = digest_mix64(seed.wrapping_add(trial));
                    (seed % base.points.len() as u64) as usize
                };
                let mut target = base.points[pick()];
                for _ in 0..3 {
                    target = fast.add(target, base.points[pick()]);
                }
                let Some((tx, ty)) = target else { continue };
                let start = digest_mix64((tx ^ ty.rotate_left(29)) as u64) as usize;
                macro_rules! run {
                    ($o:expr, $p:expr, $index:expr) => {{
                        let mut clock = PhaseClock::start();
                        let mut split = ExtractSplit::default();
                        let relation = extract128::<CANON_LIFT, { $o }, { $p }>(
                            &gf, &fast, &basis, &solver, $index, &base, target, start, &mut clock,
                            &mut split,
                        );
                        (relation.map(|r| ((r.point_indices, r.x_codes, r.intermediates), r.probes)),
                         split.root_calls, split.relation_checks)
                    }};
                }
                for (order, index) in [(ORDER_FEISTEL, &stack), (ORDER_LEFT_MAJOR, &stack), (ORDER_FEISTEL, &unfolded)] {
                    macro_rules! compare {
                        ($o:expr) => {{
                            let want = run!($o, PIPE_FRAME, index);
                            assert!(want.0.is_some(), "a planted four-point target decomposes");
                            assert_eq!(run!($o, PIPE_COMPACT, index), want, "the frame loop differs from S3");
                            for got in [run!($o, PIPE_ROTKEY, index), run!($o, PIPE_ROTKEY_PLANT, index)] {
                                assert_eq!(got, want, "a rotation-key loop differs from the frame loop");
                            }
                            solved += 1;
                        }};
                    }
                    if order == ORDER_FEISTEL { compare!(ORDER_FEISTEL) } else { compare!(ORDER_LEFT_MAJOR) }
                }
            }
            assert!(solved >= 100);
            assert!(ROTKEY_HIT_VERIFIES.load(Ordering::Relaxed) > verifies_before);
            assert!(ROTKEY_PLANT_CHECKED.load(Ordering::Relaxed) > checked_before);
        }
    }

'''

SELECT_DOC_OLD = """    /// `P` picks the target scan's probe loop at compile time.
"""
SELECT_DOC_NEW = ROTKEY_CODE + SELECT_DOC_OLD

SELECT_OLD = """        if P >= PIPE_FRAME {
            return scan_state128_frame::<C, P>(
"""
SELECT_NEW = """        if P >= PIPE_ROTKEY {
            return scan_state128_rotkey::<C, P>(
                gf, fast, basis, solver, index, base, target, target_x, state, scan, probes, clock,
                split,
            );
        }
        if P >= PIPE_FRAME {
            return scan_state128_frame::<C, P>(
"""

RANK_SOLVE_OLD = """        let (rank_solve, rank_solve_name) = rank_solve_frame_from_env().unwrap_or_else(rank_solve_from_env);
"""
RANK_SOLVE_NEW = """        // koblitz-n83-rotkey-20261019: rotkey | rotkey_plant, else the rank-probe selector.
        let (rank_solve, rank_solve_name) = rank_solve_rotkey_from_env()
            .or_else(rank_solve_frame_from_env)
            .unwrap_or_else(rank_solve_from_env);
"""

COUNTERS_OLD = """                        &PADD_SWAPPED_PAIRS, &PADD_PLANT_CHECKED, &FRAME_BUILDS, &FRAME_PLANT_CHECKED] {
"""
COUNTERS_NEW = """                        &PADD_SWAPPED_PAIRS, &PADD_PLANT_CHECKED, &FRAME_BUILDS, &FRAME_PLANT_CHECKED,
                        &ROTKEY_BUILDS, &ROTKEY_BUILD_NS, &ROTKEY_COMPACT_ENTRIES, &ROTKEY_TABLE_ENTRIES,
                        &ROTKEY_HIT_VERIFIES, &ROTKEY_PLANT_CHECKED, &ROTKEY_CLMUL] {
"""

RANK_START_OLD = """        let rank_started = Instant::now();
"""
RANK_START_NEW = RANK_START_OLD + """        // koblitz-n83-rotkey-20261019: the rotation-key table, inside the
        // rank-stage interval (charged to the rank stage).
        let rotkey_kernel_name = rotkey_kernel();
        if rank_loop >= PIPE_ROTKEY && cached_log_table.is_none() {
            assert_eq!(gf.n, ROTKEY_N, "the rotation key is the n = 83 ring's");
            let clmul = rotkey_kernel_name == "pclmulqdq";
            ROTKEY_CLMUL.store(clmul as u64, Ordering::Relaxed);
            rotkey_install(&index, clmul);
        }
"""

RANK_MATCH_OLD = """                (_, _, PIPE_FRAME_PLANT) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_FRAME_PLANT),
"""
RANK_MATCH_NEW = RANK_MATCH_OLD + """                (_, _, PIPE_ROTKEY) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_ROTKEY),
                (_, _, PIPE_ROTKEY_PLANT) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_ROTKEY_PLANT),
"""

SUMMARY_OLD = """            "rank_frame_plant_checked_inputs":FRAME_PLANT_CHECKED.load(Ordering::Relaxed),
"""
SUMMARY_NEW = SUMMARY_OLD + """            "rank_rotkey_builds":ROTKEY_BUILDS.load(Ordering::Relaxed),
            "rank_rotkey_build_ms":ROTKEY_BUILD_NS.load(Ordering::Relaxed) as f64 / 1e6,
            "rank_rotkey_compact_entries":ROTKEY_COMPACT_ENTRIES.load(Ordering::Relaxed),
            "rank_rotkey_table_entries":ROTKEY_TABLE_ENTRIES.load(Ordering::Relaxed),
            "rank_rotkey_collisions":ROTKEY_COMPACT_ENTRIES.load(Ordering::Relaxed)
                - ROTKEY_TABLE_ENTRIES.load(Ordering::Relaxed),
            "rank_rotkey_kernel":rotkey_kernel_name,
            "rank_rotkey_clmul":ROTKEY_CLMUL.load(Ordering::Relaxed),
            "rank_rotkey_hit_verifies":ROTKEY_HIT_VERIFIES.load(Ordering::Relaxed),
            "rank_rotkey_plant_checked_probes":ROTKEY_PLANT_CHECKED.load(Ordering::Relaxed),
"""


def rotkey_edits(head, wide):
    head = replace(head, HEAD_OLD, HEAD_NEW)
    wide = replace(wide, INDEX_FIELD_OLD, INDEX_FIELD_NEW)
    wide = replace(wide, INDEX_INIT_OLD, INDEX_INIT_NEW)
    wide = replace(wide, SCRATCH_OLD, SCRATCH_NEW)
    wide = replace(wide, SCRATCH_INIT_OLD, SCRATCH_INIT_NEW)
    wide = replace(wide, SELECT_DOC_OLD, SELECT_DOC_NEW)
    wide = replace(wide, SELECT_OLD, SELECT_NEW)
    wide = replace(wide, RANK_SOLVE_OLD, RANK_SOLVE_NEW)
    wide = replace(wide, COUNTERS_OLD, COUNTERS_NEW)
    wide = replace(wide, RANK_START_OLD, RANK_START_NEW)
    wide = replace(wide, RANK_MATCH_OLD, RANK_MATCH_NEW)
    wide = replace(wide, SUMMARY_OLD, SUMMARY_NEW)
    return head, wide


def rankprobe_text():
    text = rankprobe.derive(rankprobe.rankcut_text())
    digest = hashlib.sha256(text.encode()).hexdigest()
    if digest != RANKPROBE_SHA256:
        raise ValueError("rank-probe derivation differs from koblitz-n83-rankprobe-20261019's frozen producer: "
                         + digest)
    return text


def derive(text):
    head, rest = text.split(WIDE_START, 1)
    wide, tail = rest.split(WIDE_END, 1)
    head, wide = rotkey_edits(head, wide)
    return head + WIDE_START + wide + WIDE_END + tail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = derive(rankprobe_text())
    if args.check:
        if OUTPUT.read_text() != text:
            raise SystemExit("derived online source differs from " + str(OUTPUT))
    else:
        OUTPUT.write_text(text)
    print("online_source_sha256=" + hashlib.sha256(text.encode()).hexdigest())


if __name__ == "__main__":
    sys.exit(main())
