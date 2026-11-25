#[cfg(all(target_arch = "aarch64", target_feature = "neon", neon_products))]
mod neon_products_kernel {
    use super::F;
    use std::arch::aarch64::*;

    #[inline(always)]
    fn mul(a: uint32x4_t, b: uint32x4_t) -> uint32x4_t {
        // This module is compiled only with the NEON target feature.
        unsafe {
            let p = vdupq_n_u32(F::<31>::P as u32);
            let hi = vreinterpretq_u32_s32(vqdmulhq_s32(
                vreinterpretq_s32_u32(a),
                vreinterpretq_s32_u32(b),
            ));
            let sum = vaddq_u32(hi, vandq_u32(vmulq_u32(a, b), p));
            vminq_u32(sum, vsubq_u32(sum, p))
        }
    }

    #[cfg(neon_finish)]
    pub(super) fn finish(
        curve: super::Curve<31>,
        p: super::Point,
        reps: &[super::Point; 71],
        inverses: &[u32; 72],
        out: &mut [Option<super::Point>],
    ) {
        use super::Point;
        unsafe {
            let modulus = vdupq_n_u32(F::<31>::P as u32);
            let sub = |a, b| {
                let d = vsubq_u32(a, b);
                vminq_u32(d, vaddq_u32(d, modulus))
            };
            let x = vdupq_n_u32(p.x as u32);
            let y = vdupq_n_u32(p.y as u32);
            for (i, qs) in reps.chunks(4).enumerate() {
                let us: [u32; 4] = std::array::from_fn(|k| qs[k.min(qs.len() - 1)].x as u32);
                let vs: [u32; 4] = std::array::from_fn(|k| qs[k.min(qs.len() - 1)].y as u32);
                let u = vld1q_u32(us.as_ptr());
                let v = vld1q_u32(vs.as_ptr());
                let inverse = vld1q_u32(inverses.as_ptr().add(4 * i));
                for (sign, ordinate) in [v, sub(vdupq_n_u32(0), v)].into_iter().enumerate() {
                    let slope = mul(sub(ordinate, y), inverse);
                    let rx = sub(sub(mul(slope, slope), x), u);
                    let ry = sub(mul(slope, sub(x, rx)), y);
                    let mut ox = [0; 4];
                    let mut oy = [0; 4];
                    vst1q_u32(ox.as_mut_ptr(), rx);
                    vst1q_u32(oy.as_mut_ptr(), ry);
                    for (k, &q) in qs.iter().enumerate() {
                        out[8 * i + 2 * k + sign] = if q.x == p.x {
                            curve.add_inner(
                                Some(p),
                                Some(if sign == 0 { q } else { curve.neg_inner(q) }),
                            )
                        } else {
                            Some(Point {
                                x: u64::from(ox[k]),
                                y: u64::from(oy[k]),
                            })
                        };
                    }
                }
            }
        }
    }

    // Return the inverse of each nonzero entry. Zeros and the padded slot
    // have neutral products and are ignored by the affine caller.
    pub(super) fn reciprocals<const V: usize>(den: &[u32; 72]) -> [u32; 72] {
        unsafe {
            let one = vdupq_n_u32(1);
            let mut lane = [one; V];
            let mut prefix = [one; 18];
            let mut effective = [one; 18];
            for (i, block) in den.chunks_exact(4).enumerate() {
                let v = vld1q_u32(block.as_ptr());
                effective[i] = vmaxq_u32(v, one);
                prefix[i] = lane[i % V];
                lane[i % V] = mul(lane[i % V], effective[i]);
            }
            let mut prior = [[0u32; 4]; V];
            let mut scalars = lane.map(|v| {
                let mut s = [0; 4];
                vst1q_u32(s.as_mut_ptr(), v);
                s
            });
            let mut product = 1;
            for (j, s) in scalars.iter().enumerate() {
                for k in 0..4 {
                    prior[j][k] = product as u32;
                    product = F::<31>::mul(product, u64::from(s[k]));
                }
            }
            let mut carry = F::<31>::inv(product);
            for j in (0..V).rev() {
                for k in (0..4).rev() {
                    let s = scalars[j][k];
                    scalars[j][k] = F::<31>::mul(carry, u64::from(prior[j][k])) as u32;
                    carry = F::<31>::mul(carry, u64::from(s));
                }
                lane[j] = vld1q_u32(scalars[j].as_ptr());
            }
            let mut out = [0u32; 72];
            for (i, dest) in out.chunks_exact_mut(4).enumerate().rev() {
                vst1q_u32(dest.as_mut_ptr(), mul(lane[i % V], prefix[i]));
                lane[i % V] = mul(lane[i % V], effective[i]);
            }
            out
        }
    }
}
