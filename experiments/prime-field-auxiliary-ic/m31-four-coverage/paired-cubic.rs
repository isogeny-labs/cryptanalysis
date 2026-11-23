// Positions 64 apart in this input are negatives. Each batch takes 16 pairs.
pub(super) fn paired_points<const SHARED: bool, const COMPACT: bool>(
    xs: &[u64; 128],
    b: u64,
    out: &mut Points,
) {
    let eval = |x| M::add(M::add(M::mul(M::sq(x), x), M::add(x, x)), b);
    let mut packed = [(0, 0); 128];
    let mut count = 0;
    for offset in (0..64).step_by(16) {
        let mut rhs = [[0; 4]; 8];
        for i in 0..16 {
            let first = eval(xs[offset + i]);
            let second = if SHARED {
                M::sub(M::add(b, b), first)
            } else {
                eval(xs[offset + 64 + i])
            };
            rhs[i / 4][i % 4] = first as u32;
            rhs[4 + i / 4][i % 4] = second as u32;
        }
        let roots = unsafe { chain(&rhs) };
        for j in 0..8 {
            for k in 0..4 {
                let y = u64::from(roots[j][k]);
                let index = offset + (j / 4) * 64 + (j % 4) * 4 + k;
                let point = (xs[index], y.min(M::sub(0, y)));
                let valid = M::sq(y) == u64::from(rhs[j][k]);
                if COMPACT {
                    packed[count] = point;
                    count += usize::from(valid);
                } else if valid {
                    out.push(point);
                }
            }
        }
    }
    if COMPACT {
        out.extend_from_slice(&packed[..count]);
    }
}

// Canonical M31 coordinates occupy 31 bits. Unsigned word order agrees with (x,y) order.
pub(super) fn sort_words(points: &mut [(u64, u64)]) {
    let mut words = [0u64; 128];
    let keys = &mut words[..points.len()];
    for (key, &(x, y)) in keys.iter_mut().zip(points.iter()) {
        *key = (x << 31) | y;
    }
    keys.sort_unstable();
    for (point, &key) in points.iter_mut().zip(keys.iter()) {
        *point = (key >> 31, key & M::P);
    }
}
