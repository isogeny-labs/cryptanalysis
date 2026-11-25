// Accept canonical inputs, keep internal words between -p and p-1.
#[target_feature(enable = "neon")]
unsafe fn signed_chain<const V: usize, const NEGATED: bool>(
    input: &[[u32; 4]; V],
) -> [[u32; 4]; V] {
    let p = vdupq_n_s32(M::P as i32);
    let mut state = input.map(|row| unsafe { vreinterpretq_s32_u32(vld1q_u32(row.as_ptr())) });
    for _ in 0..29 {
        for v in &mut state {
            let hi = vqdmulhq_s32(*v, *v);
            let product = vmulq_s32(*v, *v);
            *v = if NEGATED {
                // Clearing the product bits in p gives p - (v² mod 2³¹).
                vsubq_s32(vbicq_s32(p, product), hi)
            } else {
                #[cfg(register_bic)]
                {
                    let complement;
                    std::arch::asm!(
                        "bic {dst:v}.16b, {mask:v}.16b, {low:v}.16b",
                        dst = lateout(vreg) complement,
                        mask = in(vreg) p,
                        low = in(vreg) product,
                        options(pure, nomem, nostack, preserves_flags),
                    );
                    vsubq_s32(hi, complement)
                }
                #[cfg(not(register_bic))]
                { vaddq_s32(hi, vsubq_s32(vandq_s32(product, p), p)) }
            };
        }
    }
    state.map(|v| {
        let v = if NEGATED { vnegq_s32(v) } else { v };
        let canonical = vaddq_s32(v, vandq_s32(vshrq_n_s32::<31>(v), p));
        let mut out = [0; 4];
        unsafe { vst1q_u32(out.as_mut_ptr(), vreinterpretq_u32_s32(canonical)) };
        out
    })
}

pub(super) fn check_signed() {
    let mut seed = 0x7ff0_61c9_e615_u64;
    for j in 0..4096 {
        let input: [[u32; 4]; 8] = std::array::from_fn(|i| {
            std::array::from_fn(|k| {
                seed ^= seed << 13;
                seed ^= seed >> 7;
                seed ^= seed << 17;
                match j {
                    0 => [0, 1, 2, M::P as u32 - 1][k],
                    1..=30 => (((1u64 << j) + M::P + (4 * i + k) as u64 - 16) % M::P) as u32,
                    _ => (seed % M::P) as u32,
                }
            })
        });
        let got = unsafe { signed_chain::<8, false>(&input) };
        assert_eq!(got, unsafe { signed_chain::<8, true>(&input) });
        for (a, b) in input.into_iter().flatten().zip(got.into_iter().flatten()) {
            let mut x = u64::from(a);
            for _ in 0..29 {
                x = x * x % M::P;
            }
            assert_eq!(x, u64::from(b));
        }
    }
}
