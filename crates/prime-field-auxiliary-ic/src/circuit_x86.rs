//! Private runtime-dispatched kernels. All loads/stores cover padded tiles.
use super::FactorBase;
use crate::field::F;
use std::arch::x86_64::*;

trait Packed<const B: u32> {
    type V: Copy;
    const WIDTH: usize;
    fn splat(a: u64) -> Self::V;
    fn load(a: &[u64]) -> Self::V;
    fn store(a: &mut [u64], v: Self::V);
    fn add(a: Self::V, b: Self::V) -> Self::V;
    fn sub(a: Self::V, b: Self::V) -> Self::V;
    fn mul(a: Self::V, b: Self::V) -> Self::V;
}

macro_rules! arch {
    ($($body:tt)*) => {{
        // SAFETY: these private operations are called only from the guarded
        // target_feature entry points below, on complete padded slices.
        unsafe { $($body)* }
    }};
}

struct A256;
impl<const B: u32> Packed<B> for A256 {
    type V = __m256i;
    const WIDTH: usize = 4;
    #[inline(always)]
    fn splat(a: u64) -> Self::V {
        arch!(_mm256_set1_epi64x(a as i64))
    }
    #[inline(always)]
    fn load(a: &[u64]) -> Self::V {
        debug_assert!(a.len() >= 4);
        arch!(_mm256_loadu_si256(a.as_ptr().cast()))
    }
    #[inline(always)]
    fn store(a: &mut [u64], v: Self::V) {
        debug_assert!(a.len() >= 4);
        arch!(_mm256_storeu_si256(a.as_mut_ptr().cast(), v));
    }
    #[inline(always)]
    fn add(a: Self::V, b: Self::V) -> Self::V {
        arch! {
            let sum = _mm256_add_epi64(a, b);
            let p = _mm256_set1_epi64x(F::<B>::P as i64);
            let mask = _mm256_cmpgt_epi64(sum, _mm256_set1_epi64x((F::<B>::P - 1) as i64));
            _mm256_sub_epi64(sum, _mm256_and_si256(mask, p))
        }
    }
    #[inline(always)]
    fn sub(a: Self::V, b: Self::V) -> Self::V {
        arch! {
            let mask = _mm256_cmpgt_epi64(b, a);
            _mm256_add_epi64(_mm256_sub_epi64(a, b), _mm256_and_si256(mask, _mm256_set1_epi64x(F::<B>::P as i64)))
        }
    }
    #[inline(always)]
    fn mul(a: Self::V, b: Self::V) -> Self::V {
        arch! {
            let product = _mm256_mul_epu32(a, b);
            let p = _mm256_set1_epi64x(F::<B>::P as i64);
            let high = if B == 31 { _mm256_srli_epi64::<31>(product) }
                else if B == 19 { _mm256_srli_epi64::<19>(product) }
                else { _mm256_srl_epi64(product, _mm_cvtsi64_si128(i64::from(B))) };
            let folded = _mm256_add_epi64(_mm256_and_si256(product, p), high);
            let mask = _mm256_cmpgt_epi64(folded, _mm256_set1_epi64x((F::<B>::P - 1) as i64));
            _mm256_sub_epi64(folded, _mm256_and_si256(mask, p))
        }
    }
}

#[cfg(auxiliary_ic_avx512)]
struct A512;
#[cfg(auxiliary_ic_avx512)]
#[clippy::msrv = "1.89"]
impl<const B: u32> Packed<B> for A512 {
    type V = __m512i;
    const WIDTH: usize = 8;
    #[inline(always)]
    fn splat(a: u64) -> Self::V {
        arch!(_mm512_set1_epi64(a as i64))
    }
    #[inline(always)]
    fn load(a: &[u64]) -> Self::V {
        debug_assert!(a.len() >= 8);
        arch!(_mm512_loadu_si512(a.as_ptr().cast()))
    }
    #[inline(always)]
    fn store(a: &mut [u64], v: Self::V) {
        debug_assert!(a.len() >= 8);
        arch!(_mm512_storeu_si512(a.as_mut_ptr().cast(), v));
    }
    #[inline(always)]
    fn add(a: Self::V, b: Self::V) -> Self::V {
        arch! {
            let sum = _mm512_add_epi64(a, b);
            let p = _mm512_set1_epi64(F::<B>::P as i64);
            _mm512_mask_sub_epi64(sum, _mm512_cmp_epu64_mask::<5>(sum, p), sum, p)
        }
    }
    #[inline(always)]
    fn sub(a: Self::V, b: Self::V) -> Self::V {
        arch! {
            let difference = _mm512_sub_epi64(a, b);
            _mm512_mask_add_epi64(difference, _mm512_cmp_epu64_mask::<1>(a, b), difference, _mm512_set1_epi64(F::<B>::P as i64))
        }
    }
    #[inline(always)]
    fn mul(a: Self::V, b: Self::V) -> Self::V {
        arch! {
            let product = _mm512_mul_epu32(a, b);
            let p = _mm512_set1_epi64(F::<B>::P as i64);
            let high = if B == 31 { _mm512_srli_epi64::<31>(product) }
                else if B == 19 { _mm512_srli_epi64::<19>(product) }
                else { _mm512_srl_epi64(product, _mm_cvtsi64_si128(i64::from(B))) };
            let folded = _mm512_add_epi64(_mm512_and_si512(product, p), high);
            _mm512_mask_sub_epi64(folded, _mm512_cmp_epu64_mask::<5>(folded, p), folded, p)
        }
    }
}

#[inline(always)]
fn group<const B: u32, O: Packed<B>>(
    base: &FactorBase<B>,
    xs: &[u64],
    squares: &[u64],
    target: u64,
    target_squared: u64,
    output: &mut [u64],
) {
    let zero = O::splat(0);
    let mut d = [zero; 3];
    let mut c = [zero; 3];
    let mut h = [zero; 3];
    let tx = O::splat(target);
    let tx2 = O::splat(target_squared);
    let a = O::splat(base.curve.a);
    let b2 = O::splat(F::<B>::add(base.curve.b, base.curve.b));
    let b4 = O::splat(F::<B>::mul(4, base.curve.b));
    for k in 0..3 {
        let x = O::load(&xs[k * O::WIDTH..]);
        let x2 = O::load(&squares[k * O::WIDTH..]);
        let product = O::mul(x, tx);
        let sum = O::add(x, tx);
        let t = O::sub(product, a);
        d[k] = O::sub(O::add(x2, tx2), O::add(product, product));
        let mid = O::add(O::mul(sum, O::add(product, a)), b2);
        c[k] = O::add(mid, mid);
        h[k] = O::sub(O::mul(t, t), O::mul(b4, sum));
    }
    let first_r = base.maps[0].r;
    if first_r != 0 {
        let r = O::splat(first_r);
        let r2 = O::splat(F::<B>::sq(first_r));
        let twice_r = O::splat(F::<B>::add(first_r, first_r));
        for k in 0..3 {
            h[k] = O::add(O::sub(h[k], O::mul(r, c[k])), O::mul(r2, d[k]));
            c[k] = O::sub(c[k], O::mul(twice_r, d[k]));
        }
    }
    for (j, map) in base.centered.iter().enumerate() {
        let residue = O::splat(map.residue);
        let delta = O::splat(map.delta);
        let delta_squared = O::splat(map.delta_squared);
        let twice_delta = O::splat(map.twice_delta);
        let last = j + 1 == base.centered.len();
        for k in 0..3 {
            let bd = if map.residue == 1 {
                d[k]
            } else {
                O::mul(residue, d[k])
            };
            let nd = O::mul(h[k], d[k]);
            let diff = O::sub(h[k], bd);
            let cc = O::mul(c[k], c[k]);
            let norm = O::add(
                O::mul(diff, diff),
                if map.residue == 1 {
                    cc
                } else {
                    O::mul(residue, cc)
                },
            );
            let cd = O::mul(c[k], O::add(h[k], bd));
            if last {
                h[k] = O::add(O::add(norm, O::mul(delta, cd)), O::mul(delta_squared, nd));
            } else {
                c[k] = O::add(cd, O::mul(twice_delta, nd));
                h[k] = O::sub(O::add(norm, O::mul(delta, c[k])), O::mul(delta_squared, nd));
                d[k] = nd;
            }
        }
    }
    for k in 0..3 {
        O::store(&mut output[k * O::WIDTH..], h[k]);
    }
}

#[target_feature(enable = "avx2")]
pub(super) unsafe fn evaluate_avx2<const B: u32>(
    base: &FactorBase<B>,
    target: u64,
    target_squared: u64,
    output: &mut [u64],
) {
    for i in (0..base.xs.len()).step_by(12) {
        group::<B, A256>(
            base,
            &base.xs[i..],
            &base.squares[i..],
            target,
            target_squared,
            &mut output[i..],
        );
    }
}

#[cfg(auxiliary_ic_avx512)]
#[target_feature(enable = "avx512f")]
pub(super) unsafe fn evaluate_avx512<const B: u32>(
    base: &FactorBase<B>,
    target: u64,
    target_squared: u64,
    output: &mut [u64],
) {
    for i in (0..base.xs.len()).step_by(24) {
        group::<B, A512>(
            base,
            &base.xs[i..],
            &base.squares[i..],
            target,
            target_squared,
            &mut output[i..],
        );
    }
}
