#!/usr/bin/env python3
"""Derive the rank-probe n=83 K600 producer from the rank-cut producer, exactly.

Input: `snapshots/r770/examples/koblitz_orbit_dlp_fast_online_logcache.rs`
(crypto 770f6a69 plus B's `ic_log_cache.patch`, restored and digest-checked
by `restore.py`).

1. `make_rankcut_source.py` is `koblitz-n83-rankcut-20261016`'s
   `make_online_source.py` (PR #970), verbatim, with its verbatim parents
   (`make_stacked_source.py`, `make_tablefilter_source.py`,
   `make_probepipe_source.py`, `make_combined_source.py`). Its derived text
   must hash to the rank-cut protocol's frozen `online_source_sha256`
   (`RANKCUT_SHA256` below). That is the rank-cut producer (arms cR / kR of
   run 38891404048, the current n = 83 baseline).
2. `rankprobe_edits`: counted, exact replacements in the wide module add two
   values to `KIC_RANK_SOLVE`, read only by the rank stage:

   * `s3` and `padd` (default `s3`): unchanged.
   * `frame`: the rank-cut loop (`padd`) computed in the target's Frobenius
     frame. The rank-cut loop forms, for every shift `s` and stored root
     `R_k`, the conjugate `R_{k,s} = phi^s(R_k)` in the polynomial basis
     (two normal-to-polynomial table maps per candidate) and adds it to the
     fixed target `T`. Because `phi` is an automorphism of E (E is defined
     over F_2), `T +- phi^s(R_k) = phi^s(T_s +- R_k)` with
     `T_s = phi^(-s)(T)`. `T_s` depends only on the target, so its
     polynomial-basis `x` and `y` (and the normal-basis `x(T_s) + a`) are
     tabulated once per rank attempt. Per state only the two roots' own
     `(x, y)` are needed; per candidate the loop computes
     `D = x(T_s) + x(R_k)`, one batched inversion,
     `lambda = (y(T_s) + y(R_k)) / D`, `lambda' = lambda + x(R_k) / D`,
     `x(T_s +- R_k) = lambda^2 + lambda + x(T_s) + x(R_k) + a` written in the
     normal basis, and applies `phi^s` as a rotation of the normal-basis
     word. The emitted partner words are the rank-cut loop's partner words,
     bit for bit, in the same order (the same y is recovered), so every
     canonical key, partner, shift and candidate index is the rank-cut
     loop's. The removed work is the two per-candidate maps (and the
     per-candidate rotations feeding them); the S3 input `x(R_{k,s})` is
     formed only at a root-table hit or at an exceptional input, where the
     rank-cut loop's hit resolution and S3 fallback run unchanged.
   * `frame_plant` (planted positive control): `frame`, plus the removed
     work redone: the rank-cut loop's whole key derivation (the
     per-candidate maps, its own batched inversion and partner formulas,
     and the canonical keys) on every candidate of every state, compared
     with the emitted keys field by field (a panic on any difference) and
     otherwise discarded.

   The summary records `rank_solve`, the rank-cut counters (`rank_padd_*`,
   which the frame loop shares: fallback states, exceptional inputs,
   resolved hits, swapped pairs) and `rank_frame_*` (frames built, planted
   inputs checked). Every other path (setup, index, online target scan,
   `s3`, `padd`) is the rank-cut producer's, byte for byte.

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_rankcut_source as rankcut  # noqa: E402  (koblitz-n83-rankcut-20261016, verbatim)

EXAMPLES = HERE / "snapshots" / "r770" / "examples"
OUTPUT = EXAMPLES / "koblitz_orbit_dlp_fast_online_rankprobe.rs"
# protocol.json "sources.online_source_sha256" of koblitz-n83-rankcut-20261016 (PR #970).
RANKCUT_SHA256 = "c390733ec3a96243d06bf0b121d61b1973f5e34b5e5a2767c3506364d1f8bc2f"
WIDE_START = rankcut.WIDE_START
WIDE_END = rankcut.WIDE_END
replace = rankcut.replace

HEAD_OLD = """// rank stage's partner roots by point addition, exact to the S3 loop.
"""
HEAD_NEW = HEAD_OLD + """// koblitz-n83-rankprobe-20261019: derived from the rank-cut producer by
// make_online_source.py; adds KIC_RANK_SOLVE=frame | frame_plant, the
// rank-cut loop in the target's Frobenius frame, exact to the rank-cut loop.
"""

SCRATCH_OLD = """        padd: PaddScratch128,
    }
"""
SCRATCH_NEW = """        padd: PaddScratch128,
        frame: FrameScratch128,
    }
"""

SCRATCH_INIT_OLD = """                padd: PaddScratch128::with_capacity(entries),
"""
SCRATCH_INIT_NEW = SCRATCH_INIT_OLD + """                frame: FrameScratch128::with_capacity(entries),
"""

RANKPROBE_CODE = r'''
    // koblitz-n83-rankprobe-20261019: the rank-cut loop in the target's
    // Frobenius frame (KIC_RANK_SOLVE=frame). `PIPE_FRAME_SWAPPED` emits
    // each pair in the other order; the tests use it to force the
    // exact-order resolution.
    const PIPE_FRAME: u8 = 8;
    const PIPE_FRAME_PLANT: u8 = 9;
    const PIPE_FRAME_SWAPPED: u8 = 10;
    const FRAME_ROOTS: usize = 2;

    static FRAME_BUILDS: AtomicU64 = AtomicU64::new(0);
    static FRAME_PLANT_CHECKED: AtomicU64 = AtomicU64::new(0);

    /// `KIC_RANK_SOLVE` values of this experiment; `None` defers to the
    /// rank-cut selector.
    fn rank_solve_frame_from_env() -> Option<(u8, &'static str)> {
        match std::env::var("KIC_RANK_SOLVE").as_deref() {
            Ok("frame") => Some((PIPE_FRAME, "frame")),
            Ok("frame_plant") => Some((PIPE_FRAME_PLANT, "frame_plant")),
            _ => None,
        }
    }

    /// Per-target frame and per-state scratch of [`scan_state128_frame`]:
    /// for every shift `s`, the polynomial-basis `x` and `y` of
    /// `T_s = phi^(-s)(T)` and the normal-basis `x(T_s) + a`.
    struct FrameScratch128 {
        target: Option<(u128, u128)>,
        x: Vec<u128>,
        y: Vec<u128>,
        normal_c: Vec<u128>,
        prefix: Vec<u128>,
        inverse: Vec<u128>,
        regular: Vec<bool>,
        pair_start: Vec<u32>,
        check: Vec<ProbeKey128>,
    }

    impl FrameScratch128 {
        fn with_capacity(entries: usize) -> Self {
            Self {
                target: None,
                x: Vec::with_capacity(entries),
                y: Vec::with_capacity(entries),
                normal_c: Vec::with_capacity(entries),
                prefix: Vec::with_capacity(entries),
                inverse: Vec::with_capacity(entries),
                regular: Vec::with_capacity(entries),
                pair_start: Vec::with_capacity(entries),
                check: Vec::with_capacity(2 * entries),
            }
        }
    }

    /// Tabulate the frame of target `(tx, ty)` unless it is already the
    /// scratch's: `x(T_s)`, `y(T_s)` (polynomial basis) and
    /// `x(T_s) + a` (normal basis) for `s = 0 .. n - 1`.
    fn frame_build128(frame: &mut FrameScratch128, basis: &NormalBasis128, a: u128, tx: u128, ty: u128) {
        if frame.target == Some((tx, ty)) {
            return;
        }
        FRAME_BUILDS.fetch_add(1, Ordering::Relaxed);
        let n = basis.n;
        let normal_x = basis.to_normal.apply(tx);
        let normal_y = basis.to_normal.apply(ty);
        let normal_a = basis.to_normal.apply(a);
        frame.x.clear();
        frame.y.clear();
        frame.normal_c.clear();
        for shift in 0..n {
            let back = (n - shift) % n;
            let xs = basis.rotate(normal_x, back);
            frame.x.push(basis.to_poly.apply(xs));
            frame.y.push(basis.to_poly.apply(basis.rotate(normal_y, back)));
            frame.normal_c.push(xs ^ normal_a);
        }
        frame.target = Some((tx, ty));
    }

    /// The polynomial-basis `(x, y)` of a point of E with normal-basis x
    /// `xn`: [`padd_root_y`]'s y (`y = x * HT(x + a + b / x^2)`) before its
    /// normal-basis map, and `None` exactly when [`padd_root_y`] is `None`.
    #[inline(always)]
    fn frame_root_xy(
        gf: &Gf2_128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        a: u128,
        xn: u128,
    ) -> Option<(u128, u128)> {
        let xp = basis.to_poly.apply(xn);
        if xp == 0 {
            return None;
        }
        let xi = invert128(gf, basis, xp);
        let rhs = xp ^ a ^ gf.mul(solver.b, gf.sqr(xi));
        if (rhs & solver.trace_mask).count_ones() & 1 == 1 {
            return None;
        }
        let u = solver.half_trace.apply(rhs);
        Some((xp, gf.mul(xp, u)))
    }

    /// The rank-cut loop's key derivation ([`scan_state128_padd`] up to its
    /// lookups), verbatim in its arithmetic, into `out`; the planted
    /// control's redone work. `false` when a root fails the curve check.
    #[inline(always)]
    #[allow(clippy::too_many_arguments)]
    fn rankcut_keys128<const C: u8>(
        gf: &Gf2_128,
        basis: &NormalBasis128,
        solver: &S3Solver128,
        a: u128,
        target: (u128, u128),
        state: &State128,
        inputs: &mut Vec<(u128, u128)>,
        pad: &mut PaddScratch128,
        out: &mut Vec<ProbeKey128>,
    ) -> bool {
        let n = gf.n;
        let (tx, ty) = target;
        let roots = state.normal_roots.len();
        let mut yn = [0u128; 2];
        for (k, &root) in state.normal_roots.iter().enumerate() {
            match padd_root_y(gf, basis, solver, a, root) {
                Some(y) => yn[k] = y,
                None => return false,
            }
        }
        inputs.clear();
        pad.ys.clear();
        pad.prefix.clear();
        pad.regular.clear();
        let mut product = 1u128;
        for shift in 0..n {
            for k in 0..roots {
                let xs = basis.to_poly.apply(basis.rotate(state.normal_roots[k], shift));
                let ys = basis.to_poly.apply(basis.rotate(yn[k], shift));
                let regular = xs != tx && xs != 0 && tx != 0;
                inputs.push((xs, tx));
                pad.ys.push(ys);
                pad.prefix.push(product);
                pad.regular.push(regular);
                if regular {
                    product = gf.mul(product, xs ^ tx);
                }
            }
        }
        let count = inputs.len();
        pad.inverse.clear();
        pad.inverse.resize(count, 0);
        let mut inverse = invert128(gf, basis, product);
        for i in (0..count).rev() {
            if pad.regular[i] {
                pad.inverse[i] = gf.mul(inverse, pad.prefix[i]);
                inverse = gf.mul(inverse, inputs[i].0 ^ tx);
            }
        }
        let normal_c = basis.to_normal.apply(tx ^ a);
        out.clear();
        for i in 0..count {
            let xs = inputs[i].0;
            let pair: [u128; 2] = if pad.regular[i] {
                let lambda = basis.to_normal.apply(gf.mul(ty ^ pad.ys[i], pad.inverse[i]));
                let lambda2 = lambda ^ basis.to_normal.apply(gf.mul(xs, pad.inverse[i]));
                let c = normal_c ^ basis.rotate(state.normal_roots[i % roots], (i / roots) as u32);
                let plus = basis.rotate(lambda, 1) ^ lambda ^ c;
                let minus = basis.rotate(lambda2, 1) ^ lambda2 ^ c;
                [minus, plus]
            } else {
                match solver.roots(gf, basis, xs, tx) {
                    Some([first, second]) => {
                        [basis.to_normal.apply(first), basis.to_normal.apply(second)]
                    }
                    None => continue,
                }
            };
            for partner in pair {
                let (canonical, partner_shift) = target_canonical::<C>(basis, partner);
                out.push(ProbeKey128 { canonical, partner, partner_shift, candidate: i as u32 });
            }
        }
        true
    }

    /// [`scan_state128_padd`] (`PIPE_PADD`) in the target's Frobenius frame:
    /// the same candidates (shift outer, stored root inner), the same
    /// partner words in the same order, so the same keys and probe
    /// positions, the same first hit and relation. At every root-table hit
    /// the candidate's S3 input is formed and the rank-cut loop's
    /// exact-order resolution runs unchanged.
    #[inline(always)]
    #[allow(clippy::too_many_arguments)]
    fn scan_state128_frame<const C: u8, const P: u8>(
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
                // The rank-cut loop's exceptional inputs: x(R_k)^(2^s) = x(T)
                // iff x(R_k) = x(T_s); x(R_k)^(2^s) = 0 iff x(R_k) = 0;
                // x(T) = 0 iff x(T_s) = 0.
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
        scan.keys.clear();
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
                    if P == PIPE_FRAME_SWAPPED { [plus, minus] } else { [minus, plus] }
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
                fr.pair_start.push(scan.keys.len() as u32);
                for partner in pair {
                    let (canonical, partner_shift) = target_canonical::<C>(basis, partner);
                    compact.prefetch(canonical);
                    scan.keys.push(ProbeKey128 {
                        canonical,
                        partner,
                        partner_shift,
                        candidate: i as u32,
                    });
                }
            }
        }
        if P == PIPE_FRAME_PLANT {
            // The removed work, redone and discarded: the rank-cut loop's
            // key derivation on every candidate, compared key by key.
            let complete = rankcut_keys128::<C>(
                gf, basis, solver, a, (tx, ty), state, &mut scan.inputs, &mut scan.padd, &mut fr.check,
            );
            assert!(complete, "a root the frame accepted failed the rank-cut curve check");
            assert_eq!(fr.check.len(), scan.keys.len(), "frame and rank-cut key counts differ");
            for (got, want) in scan.keys.iter().zip(&fr.check) {
                assert!(
                    black_box(got.canonical) == want.canonical
                        && got.partner == want.partner
                        && got.partner_shift == want.partner_shift
                        && got.candidate == want.candidate,
                    "frame keys differ from the rank-cut keys"
                );
            }
            FRAME_PLANT_CHECKED.fetch_add(count as u64, Ordering::Relaxed);
        }
        let first = *probes;
        let passes = split.filter_passes;
        let len = scan.keys.len();
        let mut position = 0usize;
        while position < len {
            *probes = first + position as u64 + 1;
            split.filter_passes = passes + position as u64 + 1;
            if compact.get(scan.keys[position].canonical).is_none() {
                position += 1;
                continue;
            }
            // First hit in this candidate's pair: form its S3 input and
            // evaluate the pair in the S3 order, at the S3 loop's probe
            // positions (the rank-cut loop's resolution).
            let candidate = scan.keys[position].candidate as usize;
            let shift = candidate / FRAME_ROOTS;
            let xs = basis.to_poly.apply(basis.rotate(state.normal_roots[candidate % FRAME_ROOTS], shift as u32));
            let start = fr.pair_start[candidate] as usize;
            let order = if fr.regular[candidate] {
                PADD_RESOLVED_HITS.fetch_add(1, Ordering::Relaxed);
                let exact = solver
                    .roots(gf, basis, xs, tx)
                    .expect("the S3 roots of a regular candidate");
                let emitted = [
                    basis.to_poly.apply(scan.keys[start].partner),
                    basis.to_poly.apply(scan.keys[start + 1].partner),
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
                let key = scan.keys[at];
                let Some(value) = compact.get(key.canonical) else {
                    continue;
                };
                let left_x = index.shifted[state.left as usize][shift];
                let right_x =
                    index.shifted[state.right as usize][(shift + state.relative as usize) % n as usize];
                let (left2, right2, relative2, stored_shift) = unpack(value);
                let left_shift2 = ((stored_shift + n - key.partner_shift) % n) as usize;
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
                        intermediates: [xs, basis.to_poly.apply(key.partner)],
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

    #[cfg(test)]
    mod rankprobe_tests {
        use super::*;

        fn small_instance(
            columns: usize,
        ) -> (FastBinaryCurve128, Gf2_128, NormalBasis128, S3Solver128, Base128, Vec<u128>) {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let (points, labels, reps, _) = construct_base128(&fast, &curve, b, columns, r);
            let mut by_x: HashMap<u128, Vec<usize>> = HashMap::new();
            for (i, point) in points.iter().enumerate() {
                by_x.entry(point.unwrap().0).or_default().push(i);
            }
            let reps: Vec<u128> = reps.iter().map(|p| p.unwrap()[0]).collect();
            let base = Base128 { points, labels, by_x, columns };
            let basis = NormalBasis128::new(&gf);
            let solver = S3Solver128::new(&gf, b);
            (fast, gf, basis, solver, base, reps)
        }

        /// phi^s(T_s +- R) = T +- phi^s(R) on random points, with the frame
        /// tabulated by `frame_build128` (the identity the loop relies on).
        #[test]
        fn frame_conjugates_commute_with_point_addition() {
            let (fast, gf, basis, _solver, base, _) = small_instance(9);
            let frob = |p: FastPoint128, s: u32| -> FastPoint128 {
                p.map(|(x, y)| {
                    (basis.to_poly.apply(basis.rotate(basis.to_normal.apply(x), s)),
                     basis.to_poly.apply(basis.rotate(basis.to_normal.apply(y), s)))
                })
            };
            let mut frame = FrameScratch128::with_capacity(2 * gf.n as usize);
            let mut seed = 0x9E37_79B9_7F4A_7C15u64;
            let mut checked = 0u64;
            for _ in 0..300 {
                seed = digest_mix64(seed);
                let r = base.points[(seed % base.points.len() as u64) as usize];
                seed = digest_mix64(seed);
                let t = fast.add(r, base.points[(seed % base.points.len() as u64) as usize]);
                let Some((tx, ty)) = t else { continue };
                frame_build128(&mut frame, &basis, fast.a, tx, ty);
                seed = digest_mix64(seed);
                let s = (seed % gf.n as u64) as u32;
                let ts = Some((frame.x[s as usize], frame.y[s as usize]));
                assert_eq!(frob(ts, s), t, "phi^s(T_s) = T");
                assert_eq!(frame.normal_c[s as usize],
                           basis.to_normal.apply(frame.x[s as usize]) ^ basis.to_normal.apply(fast.a));
                for sign in [false, true] {
                    let rr = if sign { FastBinaryCurve128::neg(r) } else { r };
                    assert_eq!(frob(fast.add(ts, rr), s), fast.add(t, frob(rr, s)));
                }
                checked += 1;
            }
            assert!(checked > 200);
        }

        /// The frame keys equal the rank-cut keys on random states of
        /// random points (the planted control's comparison, standalone).
        #[test]
        fn frame_keys_are_the_rankcut_keys() {
            let (fast, gf, basis, solver, base, _) = small_instance(9);
            let mut scan = StateScan128::new(gf.n);
            let mut seed = 0x0123_4567_89AB_CDEFu64;
            let mut checked = 0u64;
            for _ in 0..200 {
                let mut pick = || {
                    seed = digest_mix64(seed);
                    base.points[(seed % base.points.len() as u64) as usize]
                };
                let (p1, p2, t) = (pick(), pick(), fast.add(pick(), pick()));
                let (Some((x1, _)), Some((x2, _)), Some((tx, ty))) = (p1, p2, t) else { continue };
                if x1 == x2 {
                    continue;
                }
                let Some(roots) = solver.roots(&gf, &basis, x1, x2) else { continue };
                let state = State128 {
                    left: 0,
                    right: 0,
                    relative: 0,
                    normal_roots: [basis.to_normal.apply(roots[0]), basis.to_normal.apply(roots[1])],
                };
                let mut want = Vec::new();
                assert!(rankcut_keys128::<CANON_LIFT>(&gf, &basis, &solver, fast.a, (tx, ty), &state,
                                                       &mut scan.inputs, &mut scan.padd, &mut want));
                // The frame loop's key derivation, run through the planted
                // loop on an index-free path is covered by the next test; here
                // the keys are rebuilt from the frame directly.
                let mut frame = FrameScratch128::with_capacity(2 * gf.n as usize);
                frame_build128(&mut frame, &basis, fast.a, tx, ty);
                let (xk, yk): (Vec<u128>, Vec<u128>) = state.normal_roots.iter()
                    .map(|&root| frame_root_xy(&gf, &basis, &solver, fast.a, root).unwrap()).unzip();
                let mut got = Vec::new();
                for shift in 0..gf.n as usize {
                    for k in 0..FRAME_ROOTS {
                        let i = shift * FRAME_ROOTS + k;
                        let d = xk[k] ^ frame.x[shift];
                        assert!(d != 0 && xk[k] != 0 && frame.x[shift] != 0);
                        let inverse = invert128(&gf, &basis, d);
                        let lambda = basis.to_normal.apply(gf.mul(frame.y[shift] ^ yk[k], inverse));
                        let lambda2 = lambda ^ basis.to_normal.apply(gf.mul(xk[k], inverse));
                        let c = frame.normal_c[shift] ^ state.normal_roots[k];
                        let plus = basis.rotate(basis.rotate(lambda, 1) ^ lambda ^ c, shift as u32);
                        let minus = basis.rotate(basis.rotate(lambda2, 1) ^ lambda2 ^ c, shift as u32);
                        for partner in [minus, plus] {
                            let (canonical, partner_shift) = target_canonical::<CANON_LIFT>(&basis, partner);
                            got.push((canonical, partner, partner_shift, i as u32));
                        }
                    }
                }
                let want: Vec<_> = want.iter().map(|k| (k.canonical, k.partner, k.partner_shift, k.candidate)).collect();
                assert_eq!(got, want, "frame keys differ from the rank-cut keys");
                checked += 1;
            }
            assert!(checked > 100);
        }

        #[test]
        fn frame_loops_find_the_rankcut_relation_with_the_rankcut_probes() {
            let (fast, gf, basis, solver, base, reps) = small_instance(9);
            const FOLDED: IndexMode128 = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_SELECTED };
            let stack = build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, FOLDED);
            let unfolded =
                build_index128_stacked(&gf, &basis, &solver, &reps, TABLE_COMPACT, 28, IndexMode128::UNFOLDED);
            let mut seed = 0xA076_1D64_78BD_642Fu64;
            let mut solved = 0usize;
            let swapped_before = PADD_SWAPPED_PAIRS.load(Ordering::Relaxed);
            let checked_before = FRAME_PLANT_CHECKED.load(Ordering::Relaxed);
            let builds_before = FRAME_BUILDS.load(Ordering::Relaxed);
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
                            let want = run!($o, PIPE_COMPACT, index);
                            assert!(want.0.is_some(), "a planted four-point target decomposes");
                            assert_eq!(run!($o, PIPE_PADD, index), want, "the rank-cut loop differs from S3");
                            for got in [run!($o, PIPE_FRAME, index), run!($o, PIPE_FRAME_PLANT, index),
                                        run!($o, PIPE_FRAME_SWAPPED, index)] {
                                assert_eq!(got, want, "a frame loop differs from the rank-cut loop");
                            }
                            solved += 1;
                        }};
                    }
                    if order == ORDER_FEISTEL { compare!(ORDER_FEISTEL) } else { compare!(ORDER_LEFT_MAJOR) }
                }
            }
            assert!(solved >= 100);
            assert!(PADD_SWAPPED_PAIRS.load(Ordering::Relaxed) > swapped_before,
                    "the swapped loop must exercise the exact-order resolution");
            assert!(FRAME_PLANT_CHECKED.load(Ordering::Relaxed) > checked_before);
            assert!(FRAME_BUILDS.load(Ordering::Relaxed) > builds_before);
        }
    }

'''

SELECT_DOC_OLD = """    /// `P` picks the target scan's probe loop at compile time.
"""
SELECT_DOC_NEW = RANKPROBE_CODE + SELECT_DOC_OLD

SELECT_OLD = """        if P >= PIPE_PADD {
            return scan_state128_padd::<C, P>(
"""
SELECT_NEW = """        if P >= PIPE_FRAME {
            return scan_state128_frame::<C, P>(
                gf, fast, basis, solver, index, base, target, target_x, state, scan, probes, clock,
                split,
            );
        }
        if P >= PIPE_PADD {
            return scan_state128_padd::<C, P>(
"""

RANK_SOLVE_OLD = """        let (rank_solve, rank_solve_name) = rank_solve_from_env();
"""
RANK_SOLVE_NEW = """        // koblitz-n83-rankprobe-20261019: frame | frame_plant, else the rank-cut selector.
        let (rank_solve, rank_solve_name) = rank_solve_frame_from_env().unwrap_or_else(rank_solve_from_env);
"""

COUNTERS_OLD = """                        &PADD_SWAPPED_PAIRS, &PADD_PLANT_CHECKED] {
"""
COUNTERS_NEW = """                        &PADD_SWAPPED_PAIRS, &PADD_PLANT_CHECKED, &FRAME_BUILDS, &FRAME_PLANT_CHECKED] {
"""

RANK_MATCH_OLD = """                (_, _, PIPE_PADD_PLANT) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_PADD_PLANT),
"""
RANK_MATCH_NEW = RANK_MATCH_OLD + """                (_, _, PIPE_FRAME) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_FRAME),
                (_, _, PIPE_FRAME_PLANT) => rank_extract!(CANON_LIFT, ORDER_FEISTEL, PIPE_FRAME_PLANT),
"""

SUMMARY_OLD = """            "rank_padd_plant_checked_inputs":PADD_PLANT_CHECKED.load(Ordering::Relaxed),
"""
SUMMARY_NEW = SUMMARY_OLD + """            "rank_frame_builds":FRAME_BUILDS.load(Ordering::Relaxed),
            "rank_frame_plant_checked_inputs":FRAME_PLANT_CHECKED.load(Ordering::Relaxed),
"""


def rankprobe_edits(head, wide):
    head = replace(head, HEAD_OLD, HEAD_NEW)
    wide = replace(wide, SCRATCH_OLD, SCRATCH_NEW)
    wide = replace(wide, SCRATCH_INIT_OLD, SCRATCH_INIT_NEW)
    wide = replace(wide, SELECT_DOC_OLD, SELECT_DOC_NEW)
    wide = replace(wide, SELECT_OLD, SELECT_NEW)
    wide = replace(wide, RANK_SOLVE_OLD, RANK_SOLVE_NEW)
    wide = replace(wide, COUNTERS_OLD, COUNTERS_NEW)
    wide = replace(wide, RANK_MATCH_OLD, RANK_MATCH_NEW)
    wide = replace(wide, SUMMARY_OLD, SUMMARY_NEW)
    return head, wide


def rankcut_text():
    text = rankcut.derive(rankcut.stacked_text())
    digest = hashlib.sha256(text.encode()).hexdigest()
    if digest != RANKCUT_SHA256:
        raise ValueError("rank-cut derivation differs from koblitz-n83-rankcut-20261016's frozen producer: "
                         + digest)
    return text


def derive(text):
    head, rest = text.split(WIDE_START, 1)
    wide, tail = rest.split(WIDE_END, 1)
    head, wide = rankprobe_edits(head, wide)
    return head + WIDE_START + wide + WIDE_END + tail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = derive(rankcut_text())
    if args.check:
        if OUTPUT.read_text() != text:
            raise SystemExit("derived online source differs from " + str(OUTPUT))
    else:
        OUTPUT.write_text(text)
    print("online_source_sha256=" + hashlib.sha256(text.encode()).hexdigest())


if __name__ == "__main__":
    sys.exit(main())
