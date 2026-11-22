"""Scratch-only: patch a COPY of the index-build producer (bc6a31c7...) with a round-2 profiler.

LOCAL DIAGNOSTIC. The patched copy is never committed as a producer. With
`KIC_INDEX_PROFILE2=1` the process loads its base exactly as the producer
does, then (instead of the online flow):

* builds the producer's index with the producer's own functions
  (`build_index128_stacked`, compact layout, folded, lift) and times it;
* times each component of that build alone: the batched state loop split
  into prepare / Montgomery products and inversion / finish / to_normal and
  push, the canonicalization alone, the prefetched insert alone from
  precomputed keys, and the producer's pipeline;
* times candidate variants and asserts that every one reproduces the
  producer's output: C7 canonicalizers (keys and shifts equal to lift_scan on
  every root), the C6 bucketed insert (slot words equal), the pipeline with a
  C7 canonicalizer (slot words equal), and the branch-free S3 self-test
  (verdict equal);
* prints one JSON line.
"""
import sys
from pathlib import Path

src = Path(sys.argv[1]).read_text()
out = Path(sys.argv[2])
ANCHOR = "    // ── koblitz-n83-stacked-20261016: the folded root index on every layout ──\n"
assert src.count(ANCHOR) == 1
PROF = r'''
    fn p2_faults() -> i64 {
        let mut usage = std::mem::MaybeUninit::<libc::rusage>::uninit();
        unsafe { libc::getrusage(libc::RUSAGE_SELF, usage.as_mut_ptr()) };
        let u = unsafe { usage.assume_init() };
        u.ru_minflt as i64
    }

    const P2_N: u32 = 83;
    const P2_MASK: u128 = (1u128 << 83) - 1;

    #[inline(always)]
    fn p2_rotl(v: u128, s: u32) -> u128 {
        if s == 0 { v } else { ((v << s) | (v >> (P2_N - s))) & P2_MASK }
    }

    #[inline(always)]
    fn p2_pick(v: u128, mut tops: u128) -> (u128, u32) {
        let mut best = P2_MASK;
        let mut best_shift = 0u32;
        while tops != 0 {
            let p = tops.trailing_zeros();
            tops &= tops - 1;
            let s = P2_N - 1 - p;
            let r = p2_rotl(v, s);
            if r < best || (r == best && s < best_shift) {
                best = r;
                best_shift = s;
            }
        }
        (best, best_shift)
    }

    /// C7a: linear run finder, z <- z & rotl(z, 1) until the next is zero.
    #[inline(always)]
    fn p2_canon_linear(v: u128) -> (u128, u32) {
        if v == 0 || v == P2_MASK { return (v, 0); }
        let mut z = !v & P2_MASK;
        loop {
            let next = z & p2_rotl(z, 1);
            if next == 0 { break; }
            z = next;
        }
        p2_pick(v, z)
    }

    /// C7b: ten select steps without a jump, then the loop.
    #[inline(always)]
    fn p2_canon_linear_sel(v: u128) -> (u128, u32) {
        if v == 0 || v == P2_MASK { return (v, 0); }
        let mut z = !v & P2_MASK;
        for _ in 0..10 {
            let next = z & p2_rotl(z, 1);
            let keep = super::lift2::barrier(0u64.wrapping_sub((next != 0) as u64)) as u128;
            let keep = keep | (keep << 64);
            z = (next & keep) | (z & !keep);
        }
        loop {
            let next = z & p2_rotl(z, 1);
            if next == 0 { break; }
            z = next;
        }
        p2_pick(v, z)
    }

    /// C7c: lift_scan's own longest_runs, eight words before their candidates.
    #[inline(always)]
    fn p2_lift_lanes8(xs: &[u128; 8]) -> [(u128, u32); 8] {
        type L = super::lift2::F83;
        let runs: [(super::lift2::W2, u32); 8] = std::array::from_fn(|j| L::longest_runs(L::from_u128(xs[j])));
        std::array::from_fn(|j| {
            let v = xs[j];
            if v == 0 || v == P2_MASK { return (v, 0); }
            p2_pick(v, L::to_u128(runs[j].0))
        })
    }

    /// C7d: the linear run finder on eight words in lock step (per-word selects, one shared exit test).
    #[inline(always)]
    fn p2_linear_lanes8(xs: &[u128; 8]) -> [(u128, u32); 8] {
        let mut z: [u128; 8] = std::array::from_fn(|j| !xs[j] & P2_MASK);
        loop {
            let next: [u128; 8] = std::array::from_fn(|j| z[j] & p2_rotl(z[j], 1));
            let mut any = 0u128;
            for j in 0..8 {
                let keep = super::lift2::barrier(0u64.wrapping_sub((next[j] != 0) as u64)) as u128;
                let keep = keep | (keep << 64);
                z[j] = (next[j] & keep) | (z[j] & !keep);
                any |= next[j];
            }
            if any == 0 { break; }
        }
        std::array::from_fn(|j| {
            let v = xs[j];
            if v == 0 || v == P2_MASK { return (v, 0); }
            p2_pick(v, z[j])
        })
    }

    fn p2_check_canon(name: &str, roots: &[u128], want: &[(u128, u32)], got: &mut [(u128, u32)], f: impl Fn(u128) -> (u128, u32)) -> (f64, bool) {
        let t = Instant::now();
        for (g, &r) in got.iter_mut().zip(roots) { *g = f(black_box(r)); }
        let e = ms(t.elapsed());
        let ok = &got[..roots.len()] == want;
        eprintln!("PROFILE2 canon {name} {e:.1} ms equal {ok}");
        (e, ok)
    }

    /// C9: the same roots from fewer products. With s = l + r, u = 1/l + 1/r:
    /// the parent's q = p/a = p * (1/s)^2 and d = c*a/ps = c * u^2.
    #[inline(always)]
    fn p2_states_c9_body(gf: &Gf2_128, basis: &NormalBasis128, solver: &S3Solver128, shifted: &[Vec<u128>],
                         inv_shifted: &[Vec<u128>], fold: &Fold128) -> Vec<State128> {
        let n = gf.n as usize;
        let width = shifted.len();
        let mut states = Vec::with_capacity(fold.stored());
        let mut rels: Vec<usize> = Vec::with_capacity(n);
        let mut sums = vec![0u128; n];
        let mut prefix = vec![0u128; n];
        let mut inv_sum = vec![0u128; n];
        let mut reg: Vec<usize> = Vec::with_capacity(n);
        for left in 0..width { for right in left..width {
            let l = shifted[left][0];
            let il = inv_shifted[left][0];
            rels.clear(); reg.clear();
            for relative in 0..n {
                if left == right && 2 * relative > n { continue; }
                let r = shifted[right][relative];
                let k = rels.len();
                rels.push(relative);
                if l != 0 && r != 0 && l != r { sums[k] = l ^ r; reg.push(k); }
            }
            if !reg.is_empty() {
                let mut acc = [1u128; 4];
                for (t, &k) in reg.iter().enumerate() { let j = t & 3; prefix[k] = acc[j]; acc[j] = gf.mul(acc[j], sums[k]); }
                let a01 = gf.mul(acc[0], acc[1]);
                let a23 = gf.mul(acc[2], acc[3]);
                let it = invert128(gf, basis, gf.mul(a01, a23));
                let i01 = gf.mul(it, a23);
                let i23 = gf.mul(it, a01);
                let mut lane = [gf.mul(i01, acc[1]), gf.mul(i01, acc[0]), gf.mul(i23, acc[3]), gf.mul(i23, acc[2])];
                for (t, &k) in reg.iter().enumerate().rev() { let j = t & 3; inv_sum[k] = gf.mul(lane[j], prefix[k]); lane[j] = gf.mul(lane[j], sums[k]); }
            }
            let mut ri = 0usize;
            for (k, &relative) in rels.iter().enumerate() {
                let r = shifted[right][relative];
                let roots = if ri < reg.len() && reg[ri] == k {
                    ri += 1;
                    let ir = inv_shifted[right][relative];
                    let p = gf.mul(l, r);
                    let ps = solver.square.apply(p);
                    let c = ps ^ solver.b;
                    let u2 = solver.square.apply(il ^ ir);
                    let d = gf.mul(c, u2);
                    if (d & solver.trace_mask).count_ones() & 1 == 1 { None } else {
                        let q = gf.mul(p, solver.square.apply(inv_sum[k]));
                        let first = gf.mul(q, solver.half_trace.apply(d));
                        Some([first, first ^ q])
                    }
                } else {
                    s3_x_roots_128(gf, solver.b, l, r)
                };
                let roots = roots.expect("the state fold needs every state regular");
                states.push(State128 { left: left as u16, right: right as u16, relative: relative as u16,
                    normal_roots: [basis.to_normal.apply(roots[0]), basis.to_normal.apply(roots[1])] });
            }
        } }
        states
    }

    fn p2_states_c9(gf: &Gf2_128, basis: &NormalBasis128, solver: &S3Solver128, shifted: &[Vec<u128>],
                    inv_shifted: &[Vec<u128>], fold: &Fold128) -> Vec<State128> {
        p2_states_c9_body(gf, basis, solver, shifted, inv_shifted, fold)
    }

    /// C8: the same body compiled with the carry-less multiply enabled, so the field products inline.
    #[target_feature(enable = "pclmulqdq")]
    unsafe fn p2_states_c9_tf(gf: &Gf2_128, basis: &NormalBasis128, solver: &S3Solver128, shifted: &[Vec<u128>],
                              inv_shifted: &[Vec<u128>], fold: &Fold128) -> Vec<State128> {
        p2_states_c9_body(gf, basis, solver, shifted, inv_shifted, fold)
    }

    #[target_feature(enable = "pclmulqdq")]
    unsafe fn p2_states_parent_tf(gf: &Gf2_128, basis: &NormalBasis128, solver: &S3Solver128, shifted: &[Vec<u128>],
                                  fold: &Fold128) -> Vec<State128> {
        let n = gf.n as usize;
        let width = shifted.len();
        let mut states = Vec::with_capacity(fold.stored());
        let mut prepared: Vec<PreparedRoot128> = Vec::with_capacity(n);
        let mut prefixes = vec![0u128; n]; let mut inverses = vec![0u128; n];
        let mut rels: Vec<u16> = Vec::with_capacity(n);
        for left in 0..width { for right in left..width {
            prepared.clear(); rels.clear();
            for relative in 0..n {
                if left == right && 2 * relative > n { continue; }
                prepared.push(solver.prepare(gf, shifted[left][0], shifted[right][relative]));
                rels.push(relative as u16);
            }
            let mut product = 1u128;
            for (k, p) in prepared.iter().enumerate() { if p.denominator != 0 { prefixes[k] = product; product = gf.mul(product, p.denominator); } }
            let mut ip = invert128(gf, basis, product);
            for k in (0..prepared.len()).rev() { if prepared[k].denominator != 0 { inverses[k] = gf.mul(ip, prefixes[k]); ip = gf.mul(ip, prepared[k].denominator); } else { inverses[k] = 0; } }
            for (k, p) in prepared.iter().enumerate() {
                let roots = solver.finish(gf, *p, inverses[k]).unwrap();
                states.push(State128 { left: left as u16, right: right as u16, relative: rels[k],
                    normal_roots: [basis.to_normal.apply(roots[0]), basis.to_normal.apply(roots[1])] });
            }
        } }
        states
    }

    fn p2_selftest_branchfree(len: usize, key: u64) -> bool {
        let permutation = ScanPermutation::new(len, key);
        let domain = permutation.domain;
        let words = len.div_ceil(64);
        let mut seen = vec![0u64; words + 1];
        let mut visited = 0u64;
        let mut bad = 0u64;
        let mut index = 0u64;
        while index + 8 <= domain {
            let images: [u64; 8] = std::array::from_fn(|lane| permutation.apply(index + lane as u64));
            for image in images {
                bad |= (image >= domain) as u64;
                let inr = (image < len as u64) as u64;
                let word = if inr == 1 { (image / 64) as usize } else { words };
                let bit = 1u64 << (image % 64);
                let old = seen[word];
                bad |= ((old & bit) != 0) as u64 & inr;
                seen[word] = old | (bit & 0u64.wrapping_sub(inr));
                visited += inr;
            }
            index += 8;
        }
        while index < domain {
            let image = permutation.apply(index);
            bad |= (image >= domain) as u64;
            let inr = (image < len as u64) as u64;
            let word = if inr == 1 { (image / 64) as usize } else { words };
            let bit = 1u64 << (image % 64);
            let old = seen[word];
            bad |= ((old & bit) != 0) as u64 & inr;
            seen[word] = old | (bit & 0u64.wrapping_sub(inr));
            visited += inr;
            index += 1;
        }
        bad == 0 && visited == len as u64
    }

    /// C6: home-bucketed insert with the left-to-right spill carry.
    fn p2_bucketed(words: &[u128], log2_buckets: u32, slots_len: usize) -> (Vec<u128>, usize, u64, f64, f64) {
        let t = Instant::now();
        let shift = 128 - slots_len.trailing_zeros();
        let bucket_bits = slots_len.trailing_zeros() - log2_buckets;
        let buckets = 1usize << log2_buckets;
        let home = |w: u128| ((w & COMPACT_KEY_MASK).wrapping_mul(0x9E37_79B9_7F4A_7C15_9E37_79B9_7F4A_7C15) >> shift) as usize;
        let mut counts = vec![0usize; buckets + 1];
        for &w in words { counts[(home(w) >> bucket_bits) + 1] += 1; }
        for b in 0..buckets { counts[b + 1] += counts[b]; }
        let mut fill = counts.clone();
        let mut bw = vec![0u128; words.len()];
        let mut bi = vec![0u32; words.len()];
        for (i, &w) in words.iter().enumerate() {
            let b = home(w) >> bucket_bits;
            let at = fill[b];
            bw[at] = w;
            bi[at] = i as u32;
            fill[b] = at + 1;
        }
        let part_ms = ms(t.elapsed());
        let t = Instant::now();
        let mut slots = vec![0u128; slots_len];
        let mask = slots_len - 1;
        let mut len = 0usize;
        let mut carry_in: Vec<(u32, u128, usize)> = Vec::new(); // (index, word, entry slot)
        let mut carry_out: Vec<(u32, u128, usize)> = Vec::new();
        let mut spills = 0u64;
        for b in 0..buckets {
            let end = (b + 1) << bucket_bits;
            let mut ci = 0usize;
            let items = counts[b]..counts[b + 1];
            let mut place = |w: u128, start: usize, idx: u32, slots: &mut Vec<u128>, len: &mut usize, out: &mut Vec<(u32, u128, usize)>| {
                let key = w & COMPACT_KEY_MASK;
                let mut s = start;
                loop {
                    if s == end { out.push((idx, w, s & mask)); return; }
                    let stored = slots[s];
                    if stored == 0 { slots[s] = w; *len += 1; return; }
                    if stored & COMPACT_KEY_MASK == key { return; }
                    s += 1;
                }
            };
            for at in items {
                while ci < carry_in.len() && carry_in[ci].0 < bi[at] {
                    let (idx, w, s) = carry_in[ci];
                    place(w, s, idx, &mut slots, &mut len, &mut carry_out);
                    ci += 1;
                }
                place(bw[at], home(bw[at]), bi[at], &mut slots, &mut len, &mut carry_out);
            }
            while ci < carry_in.len() {
                let (idx, w, s) = carry_in[ci];
                place(w, s, idx, &mut slots, &mut len, &mut carry_out);
                ci += 1;
            }
            spills += carry_out.len() as u64;
            std::mem::swap(&mut carry_in, &mut carry_out);
            carry_out.clear();
        }
        assert!(carry_in.is_empty(), "wrap spill: the profile does not implement the wrap pass");
        let ins_ms = ms(t.elapsed());
        (slots, len, spills, part_ms, ins_ms)
    }

    /// Interleaved repeated timing (KIC_INDEX_PROFILE2=bench): the insert pipelines on one
    /// pre-faulted, re-zeroed table, and the state loops, in rotated order.
    fn bench2_index128(gf: &Gf2_128, basis: &NormalBasis128, solver: &S3Solver128, reps: &[u128]) {
        let n = gf.n as usize;
        let mode = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_LIFT };
        let index = build_index128_stacked(gf, basis, solver, reps, TABLE_COMPACT, 28, mode);
        let reference = index.compact.as_ref().unwrap().slots.clone();
        let states = &index.states;
        let shifted = index.shifted.clone();
        let fold = Fold128::new(reps.len(), n, false);
        let rounds: usize = std::env::var("KIC_BENCH_ROUNDS").ok().and_then(|v| v.parse().ok()).unwrap_or(5);
        let mut table = CompactRootTable128::with_capacity(states.len() * 2);
        let mut res: std::collections::BTreeMap<String, Vec<f64>> = Default::default();
        let names = ["pipe32_lift", "pipe32_linear", "block32_lift", "block32_linear", "block64_linear", "pipe32_linear_lanes8"];
        for round in 0..rounds {
            for v in 0..names.len() {
                let name = names[(v + round) % names.len()];
                table.slots.iter_mut().for_each(|w| *w = 0);
                table.len = 0;
                let total = states.len() * 2;
                let root_at = |i: usize| states[i >> 1].normal_roots[i & 1];
                let t = Instant::now();
                match name {
                    "pipe32_lift" | "pipe32_linear" => {
                        let f: fn(u128) -> (u128, u32) = if name == "pipe32_lift" { |r| super::lift2::lift_scan_wide(r, 83) } else { p2_canon_linear };
                        let mut ahead = [(0u128, 0u32); 32];
                        for i in 0..32.min(total) { let key = f(root_at(i)); table.prefetch(key.0); ahead[i] = key; }
                        for i in 0..total {
                            let (c, s) = ahead[i % 32];
                            if i + 32 < total { let key = f(root_at(i + 32)); table.prefetch(key.0); ahead[i % 32] = key; }
                            let st = &states[i >> 1];
                            table.insert_if_absent(c, pack(st.left, st.right, st.relative, s));
                        }
                    }
                    "pipe32_linear_lanes8" => {
                        // keys for roots [i+32, i+40) computed eight at a time
                        let mut ring = [(0u128, 0u32); 64];
                        let fill8 = |ring: &mut [(u128, u32); 64], table: &CompactRootTable128, start: usize| {
                            if start + 8 <= total {
                                let xs: [u128; 8] = std::array::from_fn(|j| root_at(start + j));
                                let o = p2_linear_lanes8(&xs);
                                for j in 0..8 { table.prefetch(o[j].0); ring[(start + j) % 64] = o[j]; }
                            } else {
                                for k in start..total { let key = p2_canon_linear(root_at(k)); table.prefetch(key.0); ring[k % 64] = key; }
                            }
                        };
                        let mut filled = 0usize;
                        while filled < 32.min(total) { fill8(&mut ring, &table, filled); filled += 8; }
                        for i in 0..total {
                            if i % 8 == 0 && filled < total && filled == i + 32 { fill8(&mut ring, &table, filled); filled += 8; }
                            let (c, s) = ring[i % 64];
                            let st = &states[i >> 1];
                            table.insert_if_absent(c, pack(st.left, st.right, st.relative, s));
                        }
                    }
                    _ => {
                        let block = if name == "block64_linear" { 64 } else { 32 };
                        let f: fn(u128) -> (u128, u32) = if name == "block32_lift" { |r| super::lift2::lift_scan_wide(r, 83) } else { p2_canon_linear };
                        let mut buf = vec![(0u128, 0u32); 2 * block];
                        let fill = |buf: &mut [(u128, u32)], table: &CompactRootTable128, start: usize| {
                            for (k, slot) in buf.iter_mut().enumerate() { if start + k < total { let key = f(root_at(start + k)); table.prefetch(key.0); *slot = key; } }
                        };
                        fill(&mut buf[..block], &table, 0);
                        let mut start = 0usize;
                        let mut cur = 0usize;
                        while start < total {
                            let next = start + block;
                            let (a, b) = buf.split_at_mut(block);
                            let (now, ahead) = if cur == 0 { (a, b) } else { (b, a) };
                            if next < total { fill(ahead, &table, next); }
                            for k in 0..block.min(total - start) {
                                let (c, s) = now[k];
                                let st = &states[(start + k) >> 1];
                                table.insert_if_absent(c, pack(st.left, st.right, st.relative, s));
                            }
                            start = next;
                            cur ^= 1;
                        }
                    }
                }
                let e = ms(t.elapsed());
                assert!(table.slots == reference, "{name} layout differs");
                eprintln!("BENCH2 round {round} {name} {e:.1} ms");
                res.entry(name.to_string()).or_default().push(e);
            }
            let inv_shifted: Vec<Vec<u128>> = shifted.iter().map(|row| {
                let mut out = Vec::with_capacity(n);
                let mut v = if row[0] == 0 { 0 } else { invert128(gf, basis, row[0]) };
                for _ in 0..n { out.push(v); v = gf.sqr(v); }
                out }).collect();
            let order: [&str; 2] = if round % 2 == 0 { ["states_producer", "states_c9"] } else { ["states_c9", "states_producer"] };
            for name in order {
                let t = Instant::now();
                let got = if name == "states_c9" { p2_states_c9(gf, basis, solver, &shifted, &inv_shifted, &fold) } else { folded_states128(gf, basis, solver, &shifted, &fold, mode) };
                let e = ms(t.elapsed());
                assert!(got.len() == states.len() && got.iter().zip(states).all(|(x, y)| (x.left, x.right, x.relative, x.normal_roots) == (y.left, y.right, y.relative, y.normal_roots)));
                drop(got);
                eprintln!("BENCH2 round {round} {name} {e:.1} ms");
                res.entry(name.to_string()).or_default().push(e);
            }
            for name in ["selftest_producer", "selftest_branchfree"] {
                let len = fold.logical();
                let t = Instant::now();
                let ok = [0x0123_4567_89AB_CDEFu64, 0xFEDC_BA98_7654_3210u64].iter().all(|&k| if name == "selftest_producer" { scan_permutation_selftest(len, k) } else { p2_selftest_branchfree(len, k) });
                let e = ms(t.elapsed());
                assert!(ok);
                eprintln!("BENCH2 round {round} {name} {e:.1} ms");
                res.entry(name.to_string()).or_default().push(e);
            }
        }
        println!("{}", json!({"bench": res, "rounds": rounds, "stored_states": states.len()}));
    }

    fn profile2_index128(gf: &Gf2_128, basis: &NormalBasis128, solver: &S3Solver128, reps: &[u128]) {
        let n = gf.n as usize;
        let mut out = serde_json::Map::new();
        macro_rules! timed {
            ($name:expr, $body:expr) => {{
                let f0 = p2_faults();
                let t = Instant::now();
                let v = $body;
                let e = ms(t.elapsed());
                let f1 = p2_faults();
                out.insert($name.to_string(), json!({"ms": e, "minflt": f1 - f0}));
                eprintln!("PROFILE2 {} {:.1} ms minflt {}", $name, e, f1 - f0);
                v
            }};
        }
        let mode = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_LIFT };
        let index = timed!("producer_index_build", build_index128_stacked(gf, basis, solver, reps, TABLE_COMPACT, 28, mode));
        let reference = index.compact.as_ref().unwrap();
        let shifted = index.shifted.clone();
        let fold = Fold128::new(reps.len(), n, false);
        let states = timed!("producer_state_loop", folded_states128(gf, basis, solver, &shifted, &fold, mode));
        let width = shifted.len();
        // State loop split (the producer's batched loop, phase by phase).
        {
            let mut t_prep = std::time::Duration::ZERO; let mut t_inv = std::time::Duration::ZERO; let mut t_fin = std::time::Duration::ZERO; let mut t_push = std::time::Duration::ZERO;
            let mut got: Vec<State128> = Vec::with_capacity(fold.stored());
            let mut prepared: Vec<PreparedRoot128> = Vec::with_capacity(n);
            let mut prefixes = vec![0u128; n]; let mut inverses = vec![0u128; n];
            let mut results: Vec<Option<[u128; 2]>> = Vec::with_capacity(n);
            let mut rels: Vec<u16> = Vec::with_capacity(n);
            let all = Instant::now();
            for left in 0..width { for right in left..width {
                let t0 = Instant::now();
                prepared.clear(); rels.clear(); results.clear();
                for relative in 0..n {
                    if left == right && 2 * relative > n { continue; }
                    prepared.push(solver.prepare(gf, shifted[left][0], shifted[right][relative]));
                    rels.push(relative as u16);
                }
                let t1 = Instant::now();
                let mut product = 1u128;
                for (k, p) in prepared.iter().enumerate() { if p.denominator != 0 { prefixes[k] = product; product = gf.mul(product, p.denominator); } }
                let mut ip = invert128(gf, basis, product);
                for k in (0..prepared.len()).rev() { if prepared[k].denominator != 0 { inverses[k] = gf.mul(ip, prefixes[k]); ip = gf.mul(ip, prepared[k].denominator); } else { inverses[k] = 0; } }
                let t2 = Instant::now();
                for (k, p) in prepared.iter().enumerate() { results.push(solver.finish(gf, *p, inverses[k])); }
                let t3 = Instant::now();
                for (&relative, roots) in rels.iter().zip(&results) {
                    let roots = roots.unwrap();
                    got.push(State128 { left: left as u16, right: right as u16, relative,
                        normal_roots: [basis.to_normal.apply(roots[0]), basis.to_normal.apply(roots[1])] });
                }
                let t4 = Instant::now();
                t_prep += t1 - t0; t_inv += t2 - t1; t_fin += t3 - t2; t_push += t4 - t3;
            } }
            let total = ms(all.elapsed());
            let same = got.len() == states.len() && got.iter().zip(&states).all(|(x, y)| (x.left, x.right, x.relative, x.normal_roots) == (y.left, y.right, y.relative, y.normal_roots));
            assert!(same, "state split differs");
            out.insert("state_split".into(), json!({"total_ms": total, "prepare_ms": ms(t_prep), "montgomery_invert_ms": ms(t_inv),
                "finish_ms": ms(t_fin), "to_normal_push_ms": ms(t_push)}));
            eprintln!("PROFILE2 state split {total:.1} prep {:.1} inv {:.1} fin {:.1} push {:.1}", ms(t_prep), ms(t_inv), ms(t_fin), ms(t_push));
        }
        // C9 and C8: state-loop variants, each equal to the producer's states.
        {
            let inv_shifted: Vec<Vec<u128>> = shifted.iter().map(|row| {
                let mut out = Vec::with_capacity(n);
                let mut v = if row[0] == 0 { 0 } else { invert128(gf, basis, row[0]) };
                for k in 0..n { assert!(row[k] == 0 || gf.mul(row[k], v) == 1); out.push(v); v = gf.sqr(v); }
                out }).collect();
            let same = |got: &[State128]| got.len() == states.len() && got.iter().zip(&states).all(|(x, y)| (x.left, x.right, x.relative, x.normal_roots) == (y.left, y.right, y.relative, y.normal_roots));
            for rep in 0..2 {
                let got = timed!(format!("states_producer_rep{rep}"), folded_states128(gf, basis, solver, &shifted, &fold, mode));
                assert!(same(&got)); drop(got);
                let got = timed!(format!("states_parent_tf_rep{rep}"), unsafe { p2_states_parent_tf(gf, basis, solver, &shifted, &fold) });
                assert!(same(&got), "parent_tf differs"); drop(got);
                let got = timed!(format!("states_c9_rep{rep}"), p2_states_c9(gf, basis, solver, &shifted, &inv_shifted, &fold));
                assert!(same(&got), "c9 differs"); drop(got);
                let got = timed!(format!("states_c9_tf_rep{rep}"), unsafe { p2_states_c9_tf(gf, basis, solver, &shifted, &inv_shifted, &fold) });
                assert!(same(&got), "c9_tf differs"); drop(got);
            }
        }
        let roots: Vec<u128> = states.iter().flat_map(|s| s.normal_roots).collect();
        let keys: Vec<(u128, u32)> = timed!("canon_lift_scan_only", roots.iter().map(|&r| index_canonical128(basis, INDEX_CANON_LIFT, black_box(r))).collect());
        // C7: candidate canonicalizers, each checked on every root.
        let mut canon = serde_json::Map::new();
        let mut got = vec![(0u128, 0u32); roots.len()];
        let mut runs: std::collections::BTreeMap<&str, Vec<(f64, bool)>> = Default::default();
        for _ in 0..3 {
            runs.entry("lift_scan").or_default().push(p2_check_canon("lift_scan", &roots, &keys, &mut got, |r| super::lift2::lift_scan_wide(r, 83)));
            runs.entry("linear").or_default().push(p2_check_canon("linear", &roots, &keys, &mut got, p2_canon_linear));
            runs.entry("linear_sel10").or_default().push(p2_check_canon("linear_sel10", &roots, &keys, &mut got, p2_canon_linear_sel));
            runs.entry("full_scan_1of16").or_default().push(p2_check_canon("full_scan", &roots[..roots.len() / 16], &keys[..roots.len() / 16], &mut got, |r| basis.canonical(r)));
            let t = Instant::now();
            let chunks = roots.len() / 8;
            for c in 0..chunks { let o = p2_lift_lanes8(roots[8 * c..8 * c + 8].try_into().unwrap()); got[8 * c..8 * c + 8].copy_from_slice(&o); }
            for i in 8 * chunks..roots.len() { got[i] = super::lift2::lift_scan_wide(roots[i], 83); }
            let e = ms(t.elapsed());
            let ok = got == keys;
            eprintln!("PROFILE2 canon lift_lanes8 {e:.1} ms equal {ok}");
            runs.entry("lift_lanes8").or_default().push((e, ok));
        }
        for _ in 0..3 {
            let t = Instant::now();
            let chunks = roots.len() / 8;
            for c in 0..chunks { let o = p2_linear_lanes8(roots[8 * c..8 * c + 8].try_into().unwrap()); got[8 * c..8 * c + 8].copy_from_slice(&o); }
            for i in 8 * chunks..roots.len() { got[i] = p2_canon_linear(roots[i]); }
            let e = ms(t.elapsed());
            let ok = got == keys;
            eprintln!("PROFILE2 canon linear_lanes8 {e:.1} ms equal {ok}");
            runs.entry("linear_lanes8").or_default().push((e, ok));
        }
        for (name, v) in runs {
            canon.insert(name.into(), json!({"ms": v.iter().map(|x| x.0).collect::<Vec<_>>(), "equal": v.iter().all(|x| x.1)}));
        }
        drop(got);
        out.insert("canon".into(), serde_json::Value::Object(canon));
        let words: Vec<u128> = keys.iter().enumerate().map(|(i, &(k, s))| {
            let st = &states[i >> 1];
            COMPACT_OCCUPIED | CompactRootTable128::compress(pack(st.left, st.right, st.relative, s)) | k
        }).collect();
        // Insert alone from precomputed keys, with and without the 32-ahead prefetch.
        for pf in [0usize, 32] {
            let mut t = timed!(format!("insert_only_pf{pf}:alloc"), CompactRootTable128::with_capacity(states.len() * 2));
            timed!(format!("insert_only_pf{pf}"), { let total = keys.len();
                for i in 0..total {
                    if pf > 0 && i + pf < total { t.prefetch(keys[i + pf].0); }
                    let st = &states[i >> 1];
                    t.insert_if_absent(keys[i].0, pack(st.left, st.right, st.relative, keys[i].1)); } });
            assert!(t.slots == reference.slots, "insert_only layout differs");
        }
        // The producer's pipeline, and the same pipeline with C7 canonicalizers.
        for variant in ["lift_scan", "linear", "linear_sel10"] {
            let f: fn(u128) -> (u128, u32) = match variant { "lift_scan" => |r| super::lift2::lift_scan_wide(r, 83), "linear" => p2_canon_linear, _ => p2_canon_linear_sel };
            let mut slots = CompactRootTable128::with_capacity(states.len() * 2);
            timed!(format!("pipeline32_{variant}"), {
                let total = states.len() * 2;
                let root_at = |i: usize| states[i >> 1].normal_roots[i & 1];
                let mut ahead = [(0u128, 0u32); 32];
                for i in 0..32.min(total) { let key = f(root_at(i)); slots.prefetch(key.0); ahead[i] = key; }
                for i in 0..total {
                    let (c, s) = ahead[i % 32];
                    if i + 32 < total { let key = f(root_at(i + 32)); slots.prefetch(key.0); ahead[i % 32] = key; }
                    let st = &states[i >> 1];
                    slots.insert_if_absent(c, pack(st.left, st.right, st.relative, s));
                } });
            assert!(slots.slots == reference.slots, "pipeline {variant} layout differs");
        }
        // Fault cost alone: read then write one word per 4 KiB page of a fresh table.
        {
            let mut t = CompactRootTable128::with_capacity(states.len() * 2);
            timed!("touch_read_write_per_page", { let len = t.slots.len(); let mut i = 0; let mut acc = 0u128;
                while i < len { acc ^= black_box(t.slots[i]); t.slots[i] = black_box(0); i += 256; } black_box(acc) });
        }
        // Blocked pipeline: canonicalize (and prefetch) block b + 1, then insert block b, in root order.
        for variant in ["lift_scan", "linear"] {
            for block in [32usize, 64, 128] {
                let f: fn(u128) -> (u128, u32) = match variant { "lift_scan" => |r| super::lift2::lift_scan_wide(r, 83), _ => p2_canon_linear };
                let mut slots = CompactRootTable128::with_capacity(states.len() * 2);
                timed!(format!("pipeline_block{block}_{variant}"), {
                    let total = states.len() * 2;
                    let root_at = |i: usize| states[i >> 1].normal_roots[i & 1];
                    let mut buf = vec![(0u128, 0u32); 2 * block];
                    let fill = |buf: &mut [(u128, u32)], slots: &CompactRootTable128, start: usize| {
                        for (k, slot) in buf.iter_mut().enumerate() { if start + k < total { let key = f(root_at(start + k)); slots.prefetch(key.0); *slot = key; } }
                    };
                    fill(&mut buf[..block], &slots, 0);
                    let mut start = 0usize;
                    let mut cur = 0usize;
                    while start < total {
                        let next = start + block;
                        let (a, b) = buf.split_at_mut(block);
                        let (now, ahead) = if cur == 0 { (a, b) } else { (b, a) };
                        if next < total { fill(ahead, &slots, next); }
                        for k in 0..block.min(total - start) {
                            let (c, s) = now[k];
                            let st = &states[(start + k) >> 1];
                            slots.insert_if_absent(c, pack(st.left, st.right, st.relative, s));
                        }
                        start = next;
                        cur ^= 1;
                    } });
                assert!(slots.slots == reference.slots, "block pipeline layout differs");
            }
        }
        // C6: bucketed insert from precomputed words.
        let mut c6 = serde_json::Map::new();
        for lb in [10u32, 12, 14] {
            let f0 = p2_faults();
            let (slots, len, spills, part_ms, ins_ms) = p2_bucketed(&words, lb, reference.slots.len());
            let f1 = p2_faults();
            let ok = slots == reference.slots && len == reference.len;
            eprintln!("PROFILE2 c6 buckets 2^{lb} partition {part_ms:.1} insert {ins_ms:.1} spills {spills} equal {ok}");
            c6.insert(format!("log2_buckets_{lb}"), json!({"partition_ms": part_ms, "insert_ms": ins_ms, "spills": spills, "equal": ok, "minflt": f1 - f0}));
            assert!(ok, "C6 layout differs");
        }
        out.insert("c6_bucketed".into(), serde_json::Value::Object(c6));
        // Self-test: the producer's lanes8 against the branch-free variant, and apply alone.
        let len = fold.logical();
        for (i, key) in [0x0123_4567_89AB_CDEFu64, 0xFEDC_BA98_7654_3210u64].into_iter().enumerate() {
            let a = timed!(format!("selftest_producer_key{i}"), scan_permutation_selftest(len, key));
            let b = timed!(format!("selftest_branchfree_key{i}"), p2_selftest_branchfree(len, key));
            assert!(a && b);
            let p = ScanPermutation::new(len, key);
            timed!(format!("selftest_apply_only_key{i}"), { let mut acc = 0u64; let mut idx = 0u64;
                while idx + 8 <= p.domain { let im: [u64; 8] = std::array::from_fn(|l| p.apply(idx + l as u64)); for x in im { acc = acc.wrapping_add(x); } idx += 8; } black_box(acc) });
        }
        out.insert("stored_states".into(), json!(states.len()));
        out.insert("table_slots".into(), json!(reference.slots.len()));
        out.insert("table_entries".into(), json!(reference.len));
        println!("{}", serde_json::Value::Object(out));
    }

'''
src = src.replace(ANCHOR, PROF + ANCHOR)
CALL = "        let index_started = Instant::now();\n        let (index_mode, index_canon_name) = index_mode_from_env();\n"
assert src.count(CALL) == 1
src = src.replace(CALL, "        if std::env::var(\"KIC_INDEX_PROFILE2\").as_deref() == Ok(\"bench\") { bench2_index128(&gf, &basis, &solver, &reps); std::process::exit(0); }\n        if std::env::var(\"KIC_INDEX_PROFILE2\").is_ok() { profile2_index128(&gf, &basis, &solver, &reps); std::process::exit(0); }\n" + CALL)
out.write_text(src)
