// V four-word NEON vectors per root chain, evenly split between x and -x.
pub(super) fn packed_lift<const V: usize, const UNCONDITIONAL: bool>(
    xs: &[u64; 128],
    b: u64,
    out: &mut Points,
) {
    const {
        assert!(V >= 2 && V <= 32 && V.is_power_of_two());
    }
    let mut keys = [0u64; 128];
    let mut n = 0;
    for offset in (0..64).step_by(2 * V) {
        let mut rhs = [[0; 4]; V];
        for i in 0..2 * V {
            let x = xs[offset + i];
            let value = M::add(M::add(M::mul(M::sq(x), x), M::add(x, x)), b);
            rhs[i / 4][i % 4] = value as u32;
            rhs[V / 2 + i / 4][i % 4] = M::sub(M::add(b, b), value) as u32;
        }
        let roots = unsafe { signed_chain::<V, false>(&rhs) };
        for j in 0..V {
            let first = offset + (j / (V / 2)) * 64 + 4 * (j % (V / 2));
            for k in 0..4 {
                let y = u64::from(roots[j][k]);
                let key = (xs[first + k] << 31) | y.min(M::sub(0, y));
                let valid = M::sq(y) == u64::from(rhs[j][k]);
                if UNCONDITIONAL {
                    keys[n] = key;
                    n += usize::from(valid);
                } else if valid {
                    keys[n] = key;
                    n += 1;
                }
            }
        }
    }
    keys[..n].sort_unstable();
    out.extend(keys[..n].iter().map(|&key| (key >> 31, key & M::P)));
}
