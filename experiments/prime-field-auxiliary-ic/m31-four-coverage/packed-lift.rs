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
        let (rhs, roots) = paired_roots::<V>(xs, b, offset);
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

#[inline(always)]
fn paired_roots<const V: usize>(
    xs: &[u64; 128],
    b: u64,
    offset: usize,
) -> ([[u32; 4]; V], [[u32; 4]; V]) {
    let mut rhs = [[0; 4]; V];
    for i in 0..2 * V {
        let x = xs[offset + i];
        let value = M::add(M::add(M::mul(M::sq(x), x), M::add(x, x)), b);
        rhs[i / 4][i % 4] = value as u32;
        rhs[V / 2 + i / 4][i % 4] = M::sub(M::add(b, b), value) as u32;
    }
    let roots = unsafe { signed_chain::<V, false>(&rhs) };
    (rhs, roots)
}

// Both outputs receive the common zero-root case. Each input otherwise contributes to one side.
pub(super) fn dual_packed<const V: usize, const MASKED: bool>(
    xs: &[u64; 128],
    b: u64,
    base: &mut Points,
    twist: &mut Points,
) {
    const {
        assert!(V >= 2 && V <= 32 && V.is_power_of_two());
    }
    let mut left = [0; 128];
    let mut right = [0; 128];
    let (mut nl, mut nr) = (0, 0);
    for offset in (0..64).step_by(2 * V) {
        let (rhs, roots) = paired_roots::<V>(xs, b, offset);
        for j in 0..V {
            let first = offset + (j / (V / 2)) * 64 + 4 * (j % (V / 2));
            for k in 0..4 {
                let x = xs[first + k];
                let r = u64::from(rhs[j][k]);
                let y = u64::from(roots[j][k]);
                let ordinate = y.min(M::sub(0, y));
                let base_key = (x << 31) | ordinate;
                let twist_key = (M::sub(0, x) << 31) | ordinate;
                let positive = M::sq(y) == r;
                if MASKED {
                    left[nl] = base_key;
                    right[nr] = twist_key;
                    nl += usize::from(positive);
                    nr += usize::from(!positive || r == 0);
                } else {
                    if positive {
                        left[nl] = base_key;
                        nl += 1;
                    }
                    if !positive || r == 0 {
                        right[nr] = twist_key;
                        nr += 1;
                    }
                }
            }
        }
    }
    for (keys, out) in [(&mut left[..nl], base), (&mut right[..nr], twist)] {
        keys.sort_unstable();
        out.extend(keys.iter().map(|&key| (key >> 31, key & M::P)));
    }
}

#[inline(always)]
fn ordered_pairs<const NETWORK: bool>(xs: &[u64; 128]) -> [u64; 128] {
    let mut pairs = [0u64; 128];
    for i in 0..64 {
        pairs[i] = xs[i].min(M::P - xs[i]);
    }
    if NETWORK {
        let mut keys = std::array::from_fn::<u32, 64, _>(|i| pairs[i] as u32);
        network_sort(&mut keys);
        for i in 0..64 {
            pairs[i] = u64::from(keys[i]);
        }
    } else {
        pairs[..64].sort_unstable();
    }
    for i in 0..64 {
        pairs[64 + i] = M::P - pairs[i];
    }
    pairs
}

// The public fiber has 64 distinct nonzero sign pairs.
pub(super) fn dual_ordered<const NETWORK: bool>(
    xs: &[u64; 128],
    b: u64,
    base: &mut Points,
    twist: &mut Points,
) {
    let pairs = ordered_pairs::<NETWORK>(xs);
    let mut pos = [u64::MAX; 128];
    let mut neg = [u64::MAX; 128];
    for offset in [0, 32] {
        let (rhs, roots) = paired_roots::<16>(&pairs, b, offset);
        for j in 0..16 {
            let first = offset + (j / 8) * 64 + 4 * (j % 8);
            for k in 0..4 {
                let i = first + k;
                let y = u64::from(roots[j][k]);
                let r = u64::from(rhs[j][k]);
                let ok = M::sq(y) == r;
                let ord = y.min(M::sub(0, y));
                if ok {
                    pos[i] = ord;
                }
                if !ok || r == 0 {
                    neg[i ^ 64] = ord;
                }
            }
        }
    }
    for i in (0..64).chain((64..128).rev()) {
        if pos[i] != u64::MAX {
            base.push((pairs[i], pos[i]));
        }
        if neg[i] != u64::MAX {
            twist.push((pairs[i], neg[i]));
        }
    }
}

#[inline(always)]
fn stage<const K: usize, const J: usize>(keys: &mut [u32; 64]) {
    for chunk in (0..64).step_by(2 * J) {
        for i in chunk..chunk + J {
            let a = keys[i];
            let b = keys[i + J];
            if i & K == 0 {
                keys[i] = a.min(b);
                keys[i + J] = a.max(b);
            } else {
                keys[i] = a.max(b);
                keys[i + J] = a.min(b);
            }
        }
    }
}
fn network_sort(keys: &mut [u32; 64]) {
    stage::<2, 1>(keys);
    stage::<4, 2>(keys);
    stage::<4, 1>(keys);
    stage::<8, 4>(keys);
    stage::<8, 2>(keys);
    stage::<8, 1>(keys);
    stage::<16, 8>(keys);
    stage::<16, 4>(keys);
    stage::<16, 2>(keys);
    stage::<16, 1>(keys);
    stage::<32, 16>(keys);
    stage::<32, 8>(keys);
    stage::<32, 4>(keys);
    stage::<32, 2>(keys);
    stage::<32, 1>(keys);
    stage::<64, 32>(keys);
    stage::<64, 16>(keys);
    stage::<64, 8>(keys);
    stage::<64, 4>(keys);
    stage::<64, 2>(keys);
    stage::<64, 1>(keys);
}

pub(super) fn dual_routes<const MASK: bool>(
    xs: &[u64; 128],
    b: u64,
    base: &mut Points,
    twist: &mut Points,
) {
    let pairs = ordered_pairs::<true>(xs);
    let mut ord = [0u64; 128];
    let mut flags = [0u8; 128];
    let mut base_masks = [0u64; 2];
    let mut twist_masks = [0u64; 2];
    for offset in [0, 32] {
        let (rhs, roots) = paired_roots::<16>(&pairs, b, offset);
        for j in 0..16 {
            let side = j / 8;
            let start = offset + 4 * (j % 8);
            let mut left = 0;
            let mut right = 0;
            for k in 0..4 {
                let i = 64 * side + start + k;
                let y = u64::from(roots[j][k]);
                let r = u64::from(rhs[j][k]);
                let positive = M::sq(y) == r;
                let negative = !positive || r == 0;
                ord[i] = y.min(M::sub(0, y));
                if MASK {
                    left |= u64::from(positive) << k;
                    right |= u64::from(negative) << k;
                } else {
                    flags[i] = u8::from(positive) + 2 * u8::from(negative);
                }
            }
            if MASK {
                base_masks[side] |= left << start;
                twist_masks[side ^ 1] |= right << start;
            }
        }
    }
    if MASK {
        for (out, masks, flip) in [(base, base_masks, 0), (twist, twist_masks, 64)] {
            for (side, mut mask) in masks.into_iter().enumerate() {
                if side == 1 {
                    mask = mask.reverse_bits();
                }
                while mask != 0 {
                    let bit = mask.trailing_zeros() as usize;
                    let i = if side == 0 { bit } else { 127 - bit };
                    out.push((pairs[i], ord[i ^ flip]));
                    mask &= mask - 1;
                }
            }
        }
    } else {
        for (out, flip, flag) in [(base, 0, 1), (twist, 64, 2)] {
            let mut n = out.len();
            out.resize(n + 128, (0, 0));
            for i in (0..64).chain((64..128).rev()) {
                out[n] = (pairs[i], ord[i ^ flip]);
                n += usize::from(flags[i ^ flip] & flag != 0);
            }
            out.truncate(n);
        }
    }
}
