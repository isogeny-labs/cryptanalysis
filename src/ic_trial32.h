/* Private fixed-divisor scans for bounded rational IC trial integers. */
#ifndef CA_IC_TRIAL32_H
#define CA_IC_TRIAL32_H

#include <stdint.h>

typedef uint32_t (*ca_ic_scan32_fn)(uint32_t, const uint32_t *, const uint32_t *, uint32_t,
                                    uint32_t);

static inline uint32_t ca_ic_scan32_portable(uint32_t value, const uint32_t *inverse,
                                             const uint32_t *limit, uint32_t start, uint32_t stop)
{
    uint32_t i = start;
    for (; stop - i >= 4; i += 4) {
        unsigned hit = (unsigned)((uint32_t)(value * inverse[i]) <= limit[i]) |
                       ((unsigned)((uint32_t)(value * inverse[i + 1]) <= limit[i + 1]) << 1) |
                       ((unsigned)((uint32_t)(value * inverse[i + 2]) <= limit[i + 2]) << 2) |
                       ((unsigned)((uint32_t)(value * inverse[i + 3]) <= limit[i + 3]) << 3);
        if (hit) return i + (uint32_t)__builtin_ctz(hit);
    }
    for (; i < stop; ++i)
        if ((uint32_t)(value * inverse[i]) <= limit[i]) break;
    return i;
}

#if defined(__x86_64__) && (defined(__GNUC__) || defined(__clang__))
#    include <immintrin.h>

__attribute__((target("avx2"))) static uint32_t ca_ic_scan32_avx2(uint32_t value,
                                                                  const uint32_t *inverse,
                                                                  const uint32_t *limit,
                                                                  uint32_t start, uint32_t stop)
{
    const __m256i v = _mm256_set1_epi32((int32_t)value);
    const __m256i sign = _mm256_set1_epi32(INT32_MIN);
    uint32_t i = start;
    for (; stop - i >= 8; i += 8) {
        __m256i inv = _mm256_loadu_si256((const __m256i *)(inverse + i));
        __m256i lim = _mm256_loadu_si256((const __m256i *)(limit + i));
        __m256i product = _mm256_mullo_epi32(v, inv);
        __m256i miss =
            _mm256_cmpgt_epi32(_mm256_xor_si256(product, sign), _mm256_xor_si256(lim, sign));
        uint32_t hit = ~(uint32_t)_mm256_movemask_epi8(miss);
        if (hit) return i + (uint32_t)__builtin_ctz(hit) / 4;
    }
    return ca_ic_scan32_portable(value, inverse, limit, i, stop);
}
#endif

#if defined(__aarch64__)
#    include <arm_neon.h>

static uint32_t ca_ic_scan32_neon(uint32_t value, const uint32_t *inverse, const uint32_t *limit,
                                  uint32_t start, uint32_t stop)
{
    uint32x4_t v = vdupq_n_u32(value);
    uint32_t i = start;
    for (; stop - i >= 4; i += 4) {
        uint32x4_t product = vmulq_u32(v, vld1q_u32(inverse + i));
        uint32x4_t miss = vcgtq_u32(product, vld1q_u32(limit + i));
        if (vminvq_u32(miss) != UINT32_MAX) {
            if (!vgetq_lane_u32(miss, 0)) return i;
            if (!vgetq_lane_u32(miss, 1)) return i + 1;
            if (!vgetq_lane_u32(miss, 2)) return i + 2;
            return i + 3;
        }
    }
    return ca_ic_scan32_portable(value, inverse, limit, i, stop);
}
#endif

static inline ca_ic_scan32_fn ca_ic_scan32_select(void)
{
#if defined(__x86_64__) && (defined(__GNUC__) || defined(__clang__))
    if (__builtin_cpu_supports("avx2")) return ca_ic_scan32_avx2;
#elif defined(__aarch64__)
    return ca_ic_scan32_neon;
#endif
    return ca_ic_scan32_portable;
}

#endif
