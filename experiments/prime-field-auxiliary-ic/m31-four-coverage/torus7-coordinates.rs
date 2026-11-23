type M = F<31>;

fn iterate(mut x: u64, n: usize) -> u64 {
    for _ in 0..n {
        x = M::sub(M::sq(x), 2);
    }
    x
}

fn roots() -> [u64; 128] {
    let t = (0..black_box(4096))
        .find(|&v| iterate(v, 30) == M::P - 2)
        .unwrap();
    let step = iterate(t, 24);
    let delta = M::mul(M::sub(M::sq(t), 4), M::sub(M::sq(step), 4));
    let sqrt = M::pow(delta, 1 << 29);
    assert_eq!(M::sq(sqrt), delta);
    let mut xs = [0; 128];
    xs[0] = t;
    xs[1] = M::mul(M::add(M::mul(t, step), sqrt), 1 << 30);
    for i in 2..128 {
        xs[i] = M::sub(M::mul(step, xs[i - 1]), xs[i - 2]);
    }
    xs.sort_unstable();
    let value = iterate(t, 7);
    assert!(xs.windows(2).all(|w| w[0] < w[1]));
    assert!(xs.iter().all(|&x| iterate(x, 7) == value));
    xs
}

type Points = Vec<(u64, u64)>;

fn candidates<const W: usize>(chunk: &[u64], b: u64) -> ([u64; W], [u64; W]) {
    let rhs: [u64; W] = std::array::from_fn(|i| {
        let x = chunk[i];
        M::add(M::add(M::mul(M::sq(x), x), M::add(x, x)), b)
    });
    let mut y = rhs;
    for _ in 0..29 {
        for v in &mut y {
            *v = M::sq(*v);
        }
    }
    (rhs, y)
}

fn on_curve<const W: usize>(xs: &[u64; 128], b: u64) -> Points {
    let mut out = Vec::with_capacity(128);
    for chunk in xs.chunks_exact(W) {
        let (rhs, y) = candidates::<W>(chunk, b);
        for i in 0..W {
            if M::sq(y[i]) == rhs[i] {
                out.push((chunk[i], y[i].min(M::sub(0, y[i]))));
            }
        }
    }
    out
}
fn interleaved<const W: usize>(xs: &[u64; 128]) -> Points {
    on_curve::<W>(xs, 14)
}

fn build(width: usize, curve: Curve<31>) -> Vec<(u64, u64)> {
    let xs = roots();
    match width {
        0 => {
            let mut out = Vec::with_capacity(128);
            for x in xs {
                if let Some(q) = curve.lift_x(x).unwrap() {
                    out.push((x, q.y()));
                }
            }
            out
        }
        1 => interleaved::<1>(&xs),
        4 => interleaved::<4>(&xs),
        8 => interleaved::<8>(&xs),
        16 => interleaved::<16>(&xs),
        32 => interleaved::<32>(&xs),
        _ => panic!("unsupported lane count"),
    }
}
