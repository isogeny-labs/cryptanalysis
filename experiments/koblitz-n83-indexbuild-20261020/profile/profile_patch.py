"""Scratch-only: patch a COPY of the derived producer with an index-build profiler (diagnostic)."""
import sys
from pathlib import Path
src = Path(sys.argv[1]).read_text()
out = Path(sys.argv[2])
ANCHOR = "    // ── koblitz-n83-stacked-20261016: the folded root index on every layout ──\n"
assert src.count(ANCHOR) == 1
PROF = r'''
    fn prof_faults() -> (i64, i64) {
        let mut usage = std::mem::MaybeUninit::<libc::rusage>::uninit();
        unsafe { libc::getrusage(libc::RUSAGE_SELF, usage.as_mut_ptr()) };
        let u = unsafe { usage.assume_init() };
        (u.ru_minflt as i64, u.ru_majflt as i64)
    }

    fn prof_huge_zeroed(len: usize, advise: bool) -> Vec<u128> {
        let v = vec![0u128; len];
        if advise {
            let p = v.as_ptr() as usize;
            let start = (p + (1 << 21) - 1) & !((1usize << 21) - 1);
            let end = (p + len * 16) & !((1usize << 21) - 1);
            if end > start {
                let rc = unsafe { libc::madvise(start as *mut libc::c_void, end - start, libc::MADV_HUGEPAGE) };
                assert_eq!(rc, 0, "madvise");
            }
        }
        v
    }

    fn prof_table(entries: usize, huge: bool) -> CompactRootTable128 {
        let slots = (entries * 2).next_power_of_two().max(16);
        CompactRootTable128 { slots: prof_huge_zeroed(slots, huge), shift: 128 - slots.trailing_zeros(), len: 0 }
    }

    fn prof_batched_states(gf: &Gf2_128, basis: &NormalBasis128, solver: &S3Solver128,
                           shifted: &[Vec<u128>], fold: &Fold128, rows_per_batch: usize) -> Vec<State128> {
        let n = gf.n as usize;
        let width = shifted.len();
        let mut states = Vec::with_capacity(fold.stored());
        let mut batch = RootBatch128::with_capacity(n * rows_per_batch);
        let mut inputs: Vec<(u128, u128)> = Vec::with_capacity(n * rows_per_batch);
        let mut meta: Vec<(u16, u16, u16)> = Vec::with_capacity(n * rows_per_batch);
        let mut rows = 0usize;
        let flush = |inputs: &mut Vec<(u128, u128)>, meta: &mut Vec<(u16, u16, u16)>, batch: &mut RootBatch128, states: &mut Vec<State128>| {
            batch.solve(gf, basis, solver, inputs);
            for (&(l, r, rel), result) in meta.iter().zip(&batch.results) {
                let roots = result.expect("the state fold needs every state regular");
                states.push(State128 { left: l, right: r, relative: rel,
                    normal_roots: [basis.to_normal.apply(roots[0]), basis.to_normal.apply(roots[1])] });
            }
            inputs.clear();
            meta.clear();
        };
        for left in 0..width {
            for right in left..width {
                for relative in 0..n {
                    if left == right && 2 * relative > n { continue; }
                    inputs.push((shifted[left][0], shifted[right][relative]));
                    meta.push((left as u16, right as u16, relative as u16));
                }
                rows += 1;
                if rows % rows_per_batch == 0 { flush(&mut inputs, &mut meta, &mut batch, &mut states); }
            }
        }
        if !inputs.is_empty() { flush(&mut inputs, &mut meta, &mut batch, &mut states); }
        states
    }


    fn prof_selftest_lanes(len: usize, key: u64) -> bool {
        let permutation = ScanPermutation::new(len, key);
        let mut seen = vec![0u64; len.div_ceil(64)];
        let mut visited = 0usize;
        let domain = permutation.domain;
        let mut index = 0u64;
        while index + 8 <= domain {
            let mut images = [0u64; 8];
            for lane in 0..8 { images[lane] = permutation.apply(index + lane as u64); }
            for &image in &images {
                if image >= domain { return false; }
                if image < len as u64 {
                    let (word, bit) = ((image / 64) as usize, image % 64);
                    if seen[word] >> bit & 1 == 1 { return false; }
                    seen[word] |= 1 << bit;
                    visited += 1;
                }
            }
            index += 8;
        }
        while index < domain {
            let image = permutation.apply(index);
            if image >= domain { return false; }
            if image < len as u64 {
                let (word, bit) = ((image / 64) as usize, image % 64);
                if seen[word] >> bit & 1 == 1 { return false; }
                seen[word] |= 1 << bit;
                visited += 1;
            }
            index += 1;
        }
        visited == len
    }

    fn prof_candidate(gf: &Gf2_128, basis: &NormalBasis128, solver: &S3Solver128, shifted: &[Vec<u128>], fold: &Fold128,
                      rows: usize, pf: usize, memory: &str) -> (Vec<State128>, CompactRootTable128) {
        let states = prof_batched_states(gf, basis, solver, shifted, fold, rows);
        let mut t = prof_table(states.len() * 2, memory == "huge");
        if memory == "prefault" { let len = t.slots.len(); let p = t.slots.as_mut_ptr(); let mut i = 0; while i < len { unsafe { std::ptr::write_volatile(p.add(i), 0) }; i += 256; } }
        let total = states.len() * 2;
        let mut ring = vec![(0u128, 0u32); pf.next_power_of_two().max(1)];
        let m = ring.len() - 1;
        let root_at = |i: usize| states[i >> 1].normal_roots[i & 1];
        for i in 0..pf.min(total) { let k = index_canonical128(basis, INDEX_CANON_LIFT, root_at(i)); t.prefetch(k.0); ring[i & m] = k; }
        for i in 0..total {
            let (c, s) = if pf == 0 { index_canonical128(basis, INDEX_CANON_LIFT, root_at(i)) } else { ring[i & m] };
            if pf > 0 && i + pf < total { let k = index_canonical128(basis, INDEX_CANON_LIFT, root_at(i + pf)); t.prefetch(k.0); ring[(i + pf) & m] = k; }
            let st = &states[i >> 1];
            t.insert_if_absent(c, pack(st.left, st.right, st.relative, s));
        }
        (states, t)
    }

    fn profile_index128(gf: &Gf2_128, basis: &NormalBasis128, solver: &S3Solver128, reps: &[u128]) {
        let n = gf.n as usize;
        let mut out = serde_json::Map::new();
        let which: Vec<String> = std::env::var("KIC_INDEX_PROFILE").unwrap().split(',').map(String::from).collect();
        let on = |name: &str| which.iter().any(|w| w == "all" || w == name);
        macro_rules! timed {
            ($name:expr, $body:expr) => {{
                let f0 = prof_faults();
                let t = Instant::now();
                let v = $body;
                let e = ms(t.elapsed());
                let f1 = prof_faults();
                out.insert($name.to_string(), json!({"ms": e, "minflt": f1.0 - f0.0, "majflt": f1.1 - f0.1}));
                eprintln!("PROFILE {} {:.1} ms minflt {}", $name, e, f1.0 - f0.0);
                v
            }};
        }
        if let Ok(spec) = std::env::var("KIC_INDEX_CANDIDATE") {
            // spec: rows,pf,memory  -> full candidate build, then baseline build, compare, print ms
            let parts: Vec<&str> = spec.split(',').collect();
            let (rows, pf, memory) = (parts[0].parse().unwrap(), parts[1].parse().unwrap(), parts[2]);
            let shifted: Vec<Vec<u128>> = reps.iter().map(|&code| { let mut row = Vec::with_capacity(n); let mut value = code;
                for _ in 0..n { row.push(value); value = gf.sqr(value); } row }).collect();
            let fold = Fold128::new(reps.len(), n, false);
            let f0 = prof_faults(); let t = Instant::now();
            let (cs, ct) = prof_candidate(gf, basis, solver, &shifted, &fold, rows, pf, memory);
            let cand_ms = ms(t.elapsed()); let f1 = prof_faults();
            let check = std::env::var("KIC_INDEX_CHECK").is_ok();
            let mut equal = None;
            let mut base_ms = None;
            if check {
                let t = Instant::now();
                let mode = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_LIFT };
                let states = folded_states128(gf, basis, solver, &shifted, &fold, mode);
                let mut table = CompactRootTable128::with_capacity(states.len() * 2);
                for state in &states { for &root in &state.normal_roots {
                    let (c, s) = index_canonical128(basis, mode.canon, root);
                    table.insert_if_absent(c, pack(state.left, state.right, state.relative, s)); } }
                base_ms = Some(ms(t.elapsed()));
                equal = Some(table.slots == ct.slots && table.len == ct.len && states.len() == cs.len() &&
                    states.iter().zip(&cs).all(|(x, y)| x.left == y.left && x.right == y.right && x.relative == y.relative && x.normal_roots == y.normal_roots));
            }
            let len = fold.logical();
            let t = Instant::now(); let a = scan_permutation_selftest(len, 0x0123_4567_89AB_CDEF) && scan_permutation_selftest(len, 0xFEDC_BA98_7654_3210); let st_ms = ms(t.elapsed());
            let t = Instant::now(); let b = prof_selftest_lanes(len, 0x0123_4567_89AB_CDEF) && prof_selftest_lanes(len, 0xFEDC_BA98_7654_3210); let sl_ms = ms(t.elapsed());
            println!("{}", json!({"spec": spec, "candidate_index_ms": cand_ms, "candidate_minflt": f1.0 - f0.0, "baseline_index_ms": base_ms, "equal": equal,
                "selftest_full_ms": st_ms, "selftest_lanes_ms": sl_ms, "selftest_equal": a == b && a}));
            return;
        }
        let total = Instant::now();
        let shifted: Vec<Vec<u128>> = timed!("shifted", reps.iter().map(|&code| {
            let mut row = Vec::with_capacity(n); let mut value = code;
            for _ in 0..n { row.push(value); value = gf.sqr(value); } row }).collect());
        let fold = Fold128::new(reps.len(), n, false);
        let mode = IndexMode128 { fold: true, plant: false, canon: INDEX_CANON_LIFT };
        let states = timed!("states_baseline", folded_states128(gf, basis, solver, &shifted, &fold, mode));
        let width = shifted.len();
        let mut table = timed!("table_alloc_baseline", CompactRootTable128::with_capacity(states.len() * 2));
        timed!("table_insert_canon_baseline", for state in &states { for &root in &state.normal_roots {
            let (c, s) = index_canonical128(basis, mode.canon, root);
            table.insert_if_absent(c, pack(state.left, state.right, state.relative, s)); } });
        out.insert("baseline_index_ms_total".into(), json!(ms(total.elapsed())));
        if on("parts") {
            timed!("solve_only", { let mut acc = 0u128;
                for left in 0..width { for right in left..width { for relative in 0..n {
                    if left == right && 2 * relative > n { continue; }
                    let r = solver.roots(gf, basis, shifted[left][0], shifted[right][relative]).unwrap();
                    acc ^= black_box(r[0]) ^ r[1]; } } } black_box(acc) });
            timed!("prepare_only", { let mut acc = 0u128;
                for left in 0..width { for right in left..width { for relative in 0..n {
                    if left == right && 2 * relative > n { continue; }
                    let p = solver.prepare(gf, shifted[left][0], black_box(shifted[right][relative]));
                    acc ^= black_box(p.denominator) ^ p.ps; } } } black_box(acc) });
            timed!("prepare_invert_only", { let mut acc = 0u128;
                for left in 0..width { for right in left..width { for relative in 0..n {
                    if left == right && 2 * relative > n { continue; }
                    let p = solver.prepare(gf, shifted[left][0], black_box(shifted[right][relative]));
                    acc ^= invert128(gf, basis, black_box(p.denominator)); } } } black_box(acc) });
            timed!("to_normal_only", { let mut acc = 0u128; for s in &states {
                acc ^= basis.to_normal.apply(black_box(s.normal_roots[0])) ^ basis.to_normal.apply(black_box(s.normal_roots[1])); } black_box(acc) });
            timed!("states_push_only", { let mut v: Vec<State128> = Vec::new(); for s in &states {
                v.push(State128 { left: s.left, right: s.right, relative: s.relative, normal_roots: black_box(s.normal_roots) }); } black_box(v.len()) });
        }
        if on("batch") {
            for rows in [1usize, 4, 16] {
                let b = timed!(format!("states_batched_rows{rows}"), prof_batched_states(gf, basis, solver, &shifted, &fold, rows));
                assert_eq!(b.len(), states.len());
                assert!(b.iter().zip(&states).all(|(x, y)| x.left == y.left && x.right == y.right && x.relative == y.relative && x.normal_roots == y.normal_roots), "batched states differ");
            }
        }
        let keys: Vec<(u128, u32)> = timed!("canon_only", { let mut k = Vec::with_capacity(states.len() * 2);
            for s in &states { for &root in &s.normal_roots { k.push(index_canonical128(basis, mode.canon, root)); } } k });
        let packed: Vec<u64> = states.iter().flat_map(|s| { let v = pack(s.left, s.right, s.relative, 0); [v, v] }).collect();
        let value = |i: usize| packed[i] | ((keys[i].1 as u64) << 48);
        if on("insert") {
            for (name, huge, pf, prefault) in [("insert_only", false, 0usize, false), ("insert_only_prefaulted", false, 0, true),
                                     ("insert_only_huge", true, 0, false), ("insert_prefetch8", false, 8, false),
                                     ("insert_prefetch16", false, 16, false), ("insert_prefetch32", false, 32, false),
                                     ("insert_prefetch16_huge", true, 16, false), ("insert_prefetch32_huge", true, 32, false)] {
                let mut t = timed!(format!("{name}:alloc"), prof_table(states.len() * 2, huge));
                if prefault { timed!(format!("{name}:prefault"), { let len = t.slots.len(); let mut i = 0; while i < len { t.slots[i] = black_box(0); i += 256; } }); }
                timed!(name, { let total = keys.len();
                    for i in 0..total {
                        if pf > 0 && i + pf < total { t.prefetch(keys[i + pf].0); }
                        t.insert_if_absent(keys[i].0, value(i)); } });
                assert!(t.slots == table.slots, "{name} layout differs");
            }
        }
        if on("pipeline") {
            for pf in [16usize, 32] {
                let mut t = timed!(format!("pipeline{pf}:alloc"), prof_table(states.len() * 2, true));
                timed!(format!("pipeline{pf}_canon_prefetch_huge"), {
                    let total = states.len() * 2;
                    let mut ring = vec![(0u128, 0u32); pf.next_power_of_two()];
                    let m = ring.len() - 1;
                    let root_at = |i: usize| states[i >> 1].normal_roots[i & 1];
                    for i in 0..pf.min(total) { let k = index_canonical128(basis, mode.canon, root_at(i)); t.prefetch(k.0); ring[i & m] = k; }
                    for i in 0..total {
                        let (c, s) = ring[i & m];
                        if i + pf < total { let k = index_canonical128(basis, mode.canon, root_at(i + pf)); t.prefetch(k.0); ring[(i + pf) & m] = k; }
                        let st = &states[i >> 1];
                        t.insert_if_absent(c, pack(st.left, st.right, st.relative, s));
                    } });
                assert!(t.slots == table.slots, "pipeline layout differs");
            }
        }
        if on("selftest") {
            let len = fold.logical();
            for (i, key) in [0x0123_4567_89AB_CDEFu64, 0xFEDC_BA98_7654_3210u64].into_iter().enumerate() {
                let ok = timed!(format!("selftest_full_key{i}"), scan_permutation_selftest(len, key)); assert!(ok);
                let ok = timed!(format!("selftest_inverse_key{i}"), scan_inverse_selftest(len, key)); assert!(ok);
            }
        }
        out.insert("stored_states".into(), json!(states.len()));
        out.insert("table_slots".into(), json!(table.slots.len()));
        out.insert("table_entries".into(), json!(table.len));
        println!("{}", serde_json::Value::Object(out));
    }

'''
src = src.replace(ANCHOR, PROF + ANCHOR)
CALL = "        let index_started = Instant::now();\n        let (index_mode, index_canon_name) = index_mode_from_env();\n"
assert src.count(CALL) == 1
src = src.replace(CALL, "        if std::env::var(\"KIC_INDEX_PROFILE\").is_ok() { profile_index128(&gf, &basis, &solver, &reps); std::process::exit(0); }\n" + CALL)
out.write_text(src)
