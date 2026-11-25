#[inline(always)]
unsafe fn reduced_sum(a: uint32x4_t, b: uint32x4_t) -> uint32x4_t {
    let p = vdupq_n_u32(M::P as u32);
    let sum = vaddq_u32(a, b);
    vminq_u32(sum, vsubq_u32(sum, p))
}

#[inline(always)]
unsafe fn product4(a: uint32x4_t, b: uint32x4_t) -> uint32x4_t {
    let high = vreinterpretq_u32_s32(vqdmulhq_s32(
        vreinterpretq_s32_u32(a),
        vreinterpretq_s32_u32(b),
    ));
    let low = vandq_u32(vmulq_u32(a, b), vdupq_n_u32(M::P as u32));
    reduced_sum(high, low)
}

fn vector_roots(xs: &[u64; 128], b: u64, offset: usize) -> ([[u32; 4]; 16], [[u32; 4]; 16]) {
    let mut rhs = [[0u32; 4]; 16];
    unsafe {
        let bv = vdupq_n_u32(b as u32);
        let p = vdupq_n_u32(M::P as u32);
        for j in 0..8 {
            let ptr = xs.as_chunks::<4>().0[offset / 4 + j].as_ptr();
            let x = vcombine_u32(vmovn_u64(vld1q_u64(ptr)), vmovn_u64(vld1q_u64(ptr.add(2))));
            let odd = product4(x, reduced_sum(product4(x, x), vdupq_n_u32(2)));
            vst1q_u32(rhs[j].as_mut_ptr(), reduced_sum(bv, odd));
            vst1q_u32(rhs[8 + j].as_mut_ptr(), reduced_sum(bv, vsubq_u32(p, odd)));
        }
        (rhs, signed_chain::<16, false>(&rhs))
    }
}

unsafe fn classify4(rhs: &[u32; 4], roots: &[u32; 4], out: &mut [u64; 4]) -> (u64, u64) {
    let r = vld1q_u32(rhs.as_ptr());
    let y = vld1q_u32(roots.as_ptr());
    let ok = vceqq_u32(product4(y, y), r);
    let other = vorrq_u32(vmvnq_u32(ok), vceqzq_u32(r));
    let ord = vminq_u32(y, vsubq_u32(vdupq_n_u32(M::P as u32), y));
    vst1q_u64(out.as_mut_ptr(), vmovl_u32(vget_low_u32(ord)));
    vst1q_u64(out.as_mut_ptr().add(2), vmovl_high_u32(ord));
    let bits = vld1q_u32([1, 2, 4, 8].as_ptr());
    (
        u64::from(vaddvq_u32(vandq_u32(ok, bits))),
        u64::from(vaddvq_u32(vandq_u32(other, bits))),
    )
}

// Each mask bit emits exactly one coordinate in canonical rank order.
pub(super) fn vector_tables(xs: &[u64; 128], b: u64, mut emit: impl FnMut(usize, (u64, u64))) {
    let pairs = ordered_pairs::<true>(xs);
    let mut ord = [0; 128];
    let mut masks = [[0u64; 2]; 2];
    for offset in [0, 32] {
        let (rhs, roots) = vector_roots(&pairs, b, offset);
        for j in 0..16 {
            let side = j / 8;
            let start = offset + 4 * (j % 8);
            let index = 64 * side + start;
            let (left, right) = unsafe {
                classify4(
                    &rhs[j],
                    &roots[j],
                    &mut ord.as_chunks_mut::<4>().0[index / 4],
                )
            };
            masks[0][side] |= left << start;
            masks[1][side ^ 1] |= right << start;
        }
    }
    for (table, sides) in masks.into_iter().enumerate() {
        for (side, mut mask) in sides.into_iter().enumerate() {
            if side == 1 {
                mask = mask.reverse_bits();
            }
            while mask != 0 {
                let bit = mask.trailing_zeros() as usize;
                let i = if side == 0 { bit } else { 127 - bit };
                emit(table, (pairs[i], ord[i ^ (64 * table)]));
                mask &= mask - 1;
            }
        }
    }
}

pub(super) fn fixed_tables(
    xs: &[u64; 128],
    b: u64,
    out: &mut [[(u64, u64); 128]; 2],
) -> [usize; 2] {
    let mut counts = [0; 2];
    vector_tables(xs, b, |table, point| {
        out[table][counts[table]] = point;
        counts[table] += 1;
    });
    counts
}

pub(super) fn checked_lanes(xs: &[u64], terminal: u64) -> bool {
    assert_eq!(xs.len() % 4, 0);
    unsafe {
        let mut valid = vdupq_n_u32(u32::MAX);
        for chunk in xs.as_chunks::<4>().0 {
            let ptr = chunk.as_ptr();
            let mut x = vcombine_u32(vmovn_u64(vld1q_u64(ptr)), vmovn_u64(vld1q_u64(ptr.add(2))));
            for _ in 0..7 {
                x = reduced_sum(product4(x, x), vdupq_n_u32(M::P as u32 - 2));
            }
            valid = vandq_u32(valid, vceqq_u32(x, vdupq_n_u32(terminal as u32)));
        }
        vminvq_u32(valid) == u32::MAX
    }
}

// Sorted coordinates have matching negative coordinates in reverse order.
pub(super) fn base_lift(xs: &[u64; 128]) -> Points {
    let mut mask = [0u64; 2];
    let mut ord = [0u64; 128];
    for offset in [0, 32] {
        let (rhs, roots) = vector_roots(xs, 14, offset);
        for j in 0..16 {
            let side = j / 8;
            let start = offset + 4 * (j % 8);
            let index = 64 * side + start;
            let (valid, _) = unsafe {
                classify4(
                    &rhs[j],
                    &roots[j],
                    &mut ord.as_chunks_mut::<4>().0[index / 4],
                )
            };
            mask[side] |= valid << start;
        }
    }
    let mut out = Points::with_capacity(128);
    for (side, mut bits) in mask.into_iter().enumerate() {
        if side == 1 {
            bits = bits.reverse_bits();
        }
        while bits != 0 {
            let bit = bits.trailing_zeros() as usize;
            let i = 64 * side + bit;
            out.push((xs[i], ord[if side == 0 { i } else { 64 + (63 - bit) }]));
            bits &= bits - 1;
        }
    }
    out
}
