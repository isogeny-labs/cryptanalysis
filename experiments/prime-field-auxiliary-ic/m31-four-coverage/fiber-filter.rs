struct FiberInput {
    xs: [u64; 128],
    keys: [u8; 128],
    exact: u128,
    group: usize,
}

fn inputs(seed: u64) -> (Vec<FiberInput>, [u128; 16]) {
    let matching = [10, 7, 6, 5, 2, 4, 13, 1, 15, 11, 3, 0, 14, 9, 8, 12];
    let mut groups = [0usize; 32];
    for (i, j) in matching.into_iter().enumerate() {
        groups[i] = i;
        groups[16 + j] = i;
    }
    let mut state = seed;
    let mut fibers = Vec::new();
    let mut paired = [0u128; 16];
    for (i, line) in include_str!("fiber-masks.csv").lines().skip(1).enumerate() {
        let mut fields = line.split(',');
        let _power = fields.next().unwrap();
        let terminal = fields.next().unwrap().parse::<u64>().unwrap();
        let exact = fields.next().unwrap().parse::<u128>().unwrap();
        let group = groups[i];
        paired[group] |= exact;
        let mut level = vec![terminal];
        for _ in 0..7 {
            let mut next = Vec::with_capacity(level.len() * 2);
            for parent in level {
                let child = M::pow(M::add(parent, 2), 1 << 29);
                assert_eq!(iterate(child, 1), parent);
                next.extend([child, M::sub(0, child)]);
            }
            level = next;
        }
        let mut xs: [u64; 128] = level.try_into().unwrap();
        for j in (1..128).rev() {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            xs.swap(j, state as usize % (j + 1));
        }
        let keys = xs.map(|x| branch_key(x) as u8);
        fibers.push(FiberInput {
            xs,
            keys,
            exact,
            group,
        });
    }
    (fibers, paired)
}

fn lift_list(xs: &[u64], out: &mut Points) {
    for block in xs.chunks(8) {
        let mut tail = [0; 8];
        let lanes = if block.len() == 8 {
            block
        } else {
            tail[..block.len()].copy_from_slice(block);
            &tail
        };
        let (rhs, y) = candidates::<8>(lanes, 14);
        for i in 0..block.len() {
            if M::sq(y[i]) == rhs[i] {
                out.push((block[i], y[i].min(M::sub(0, y[i]))));
            }
        }
    }
}

fn filtered<const DERIVE: bool>(f: &FiberInput, mask: u128, out: &mut Points) {
    let mut kept = [0; 128];
    let mut n = 0;
    for i in 0..128 {
        let key = if DERIVE {
            branch_key(f.xs[i])
        } else {
            u32::from(f.keys[i])
        };
        if mask >> key & 1 == 1 {
            kept[n] = f.xs[i];
            n += 1;
        }
    }
    lift_list(&kept[..n], out);
}

fn panel(fibers: &[FiberInput], pairs: &[u128; 16], method: char, out: &mut Points) {
    out.clear();
    for f in fibers {
        match method {
            'd' => lift_list(&f.xs, out),
            'p' => filtered::<false>(f, pairs[f.group], out),
            'e' => filtered::<false>(f, f.exact, out),
            'P' => filtered::<true>(f, pairs[f.group], out),
            'E' => filtered::<true>(f, f.exact, out),
            _ => panic!("invalid method"),
        }
    }
}

fn filter_bench(seed: u64, order: &str) {
    let (fibers, pairs) = inputs(seed);
    let curve = Curve::<31>::new(2, 14).unwrap();
    let mut expected = Vec::new();
    for f in &fibers {
        for (i, &x) in f.xs.iter().enumerate() {
            let point = curve.lift_x(x).unwrap();
            assert_eq!(point.is_some(), f.exact >> f.keys[i] & 1 == 1);
            if let Some(q) = point {
                expected.push((x, q.y()));
            }
        }
    }
    assert_eq!(expected.len(), 2063);
    let mut out = Vec::with_capacity(4096);
    for method in order.chars() {
        panel(&fibers, &pairs, method, &mut out);
        assert_eq!(out, expected);
        let start = Instant::now();
        for _ in 0..128 {
            panel(black_box(&fibers), black_box(&pairs), method, &mut out);
            black_box(out.as_slice());
        }
        println!("{method},{:.3}", start.elapsed().as_nanos() as f64 / 128.);
    }
}
