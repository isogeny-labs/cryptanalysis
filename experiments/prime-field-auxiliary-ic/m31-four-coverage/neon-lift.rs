// ARMv8 Advanced SIMD is available on the native Apple arm64 panel.
#[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
mod neon_lift {
    use super::{Points, M};
    use std::arch::aarch64::*;

    // The caller supplies canonical M31 words. Their sign bits are zero.
    #[target_feature(enable = "neon")]
    unsafe fn chain<const V: usize>(input: &[[u32; 4]; V]) -> [[u32; 4]; V] {
        let p = vdupq_n_u32(M::P as u32);
        let mut state = input.map(|row| unsafe { vld1q_u32(row.as_ptr()) });
        for _ in 0..29 {
            for v in &mut state {
                let signed = vreinterpretq_s32_u32(*v);
                // High half of the doubled signed product equals floor(v²/2³¹).
                let hi = vreinterpretq_u32_s32(vqdmulhq_s32(signed, signed));
                let lo = vandq_u32(vmulq_u32(*v, *v), p);
                let sum = vaddq_u32(hi, lo);
                *v = vminq_u32(sum, vsubq_u32(sum, p));
            }
        }
        state.map(|v| {
            let mut out = [0; 4];
            unsafe { vst1q_u32(out.as_mut_ptr(), v) };
            out
        })
    }

    pub(super) fn points<const V: usize>(xs: &[u64; 128], b: u64) -> Points {
        let mut out = Vec::with_capacity(128);
        assert_eq!(128 % (4 * V), 0);
        for chunk in xs.chunks_exact(4 * V) {
            let rhs: [[u32; 4]; V] = std::array::from_fn(|j| {
                std::array::from_fn(|k| {
                    let x = chunk[4 * j + k];
                    M::add(M::add(M::mul(M::sq(x), x), M::add(x, x)), b) as u32
                })
            });
            let y = unsafe { chain(&rhs) };
            for j in 0..V {
                for k in 0..4 {
                    let v = u64::from(y[j][k]);
                    if M::sq(v) == u64::from(rhs[j][k]) {
                        out.push((chunk[4 * j + k], v.min(M::sub(0, v))));
                    }
                }
            }
        }
        out
    }

    include!("paired-cubic.rs");

    pub(super) fn validate() {
        let mut seed = 2718281828u64;
        for i in 0..4096 {
            let input = [
                [0, 1, M::P as u32 - 1, M::P as u32 - 2],
                std::array::from_fn(|j| {
                    seed ^= seed << 13;
                    seed ^= seed >> 7;
                    seed ^= seed << 17;
                    if i < 31 {
                        ((1u64 << i) + j as u64 - 1) as u32
                    } else {
                        (seed % M::P) as u32
                    }
                }),
            ];
            let got = unsafe { chain(&input) };
            for (a, b) in input.iter().flatten().zip(got.iter().flatten()) {
                let mut x = u64::from(*a);
                for _ in 0..29 {
                    x = (x * x) % M::P;
                }
                assert_eq!(x, u64::from(*b));
            }
        }
    }
}
