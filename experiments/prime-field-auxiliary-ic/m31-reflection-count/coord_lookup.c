#define _POSIX_C_SOURCE 200809L
#include <arm_neon.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

enum { N = 32, SLOTS = 64, QUERIES = 16384, REPEATS = 12, ROUNDS = 15 };
static const uint32_t prime = UINT32_C(2147483647);
static uint32_t keys[N], tags[N], sorted[N], linear[SLOTS], perfect[SLOTS];
static uint32_t wider[256], wider_multiplier;
static uint32_t inputs[QUERIES];
static uint8_t answers[QUERIES], outputs[QUERIES];

static uint64_t nanos(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts))
        abort();
    return (uint64_t)ts.tv_sec * UINT64_C(1000000000) + ts.tv_nsec;
}
static uint32_t hash(uint32_t x, uint32_t multiplier) { return (x * multiplier) >> 26; }
static uint8_t unpack(uint32_t e, uint32_t x) {
    return e != UINT32_MAX && (e >> 1) == x ? 1 + (e & 1) : 0;
}
static uint8_t by_binary(uint32_t x) {
    size_t lo = 0, hi = N;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if ((sorted[mid] >> 1) < x)
            lo = mid + 1;
        else
            hi = mid;
    }
    return lo < N ? unpack(sorted[lo], x) : 0;
}
static uint8_t by_linear(uint32_t x) {
    unsigned i = hash(x, UINT32_C(2654435761));
    while (linear[i] != UINT32_MAX && (linear[i] >> 1) != x)
        i = (i + 1) & (SLOTS - 1);
    return unpack(linear[i], x);
}
static unsigned address(uint32_t x, uint32_t k, unsigned shift) { return (x * k) >> shift; }
static void decode(unsigned arm) {
    if (arm == 1) {
        for (unsigned i = 0; i < QUERIES; i += 4) {
            uint32x4_t x = vld1q_u32(&inputs[i]);
            uint32x4_t tag = vdupq_n_u32(0);
            for (unsigned j = 0; j < N; ++j)
                tag = vorrq_u32(
                    tag, vandq_u32(vceqq_u32(x, vdupq_n_u32(keys[j])), vdupq_n_u32(tags[j])));
            uint8x8_t bytes = vmovn_u16(vcombine_u16(vmovn_u32(tag), vdup_n_u16(0)));
            uint32_t packed = vget_lane_u32(vreinterpret_u32_u8(bytes), 0);
            memcpy(&outputs[i], &packed, sizeof(packed));
        }
    } else if (arm == 0) {
        for (unsigned i = 0; i < QUERIES; ++i)
            outputs[i] = by_binary(inputs[i]);
    } else if (arm == 2) {
        for (unsigned i = 0; i < QUERIES; ++i)
            outputs[i] = by_linear(inputs[i]);
    } else if (arm == 3) {
        for (unsigned i = 0; i < QUERIES; ++i) {
            uint32_t x = inputs[i];
            outputs[i] = unpack(perfect[hash(x, 59649)], x);
        }
    } else {
        for (unsigned i = 0; i < QUERIES; ++i) {
            uint32_t x = inputs[i];
            outputs[i] = unpack(wider[address(x, wider_multiplier, 24)], x);
        }
    }
}
static int compare(const void *a, const void *b) {
    uint32_t x = *(const uint32_t *)a, y = *(const uint32_t *)b;
    return (x > y) - (x < y);
}
static uint32_t next(uint32_t *state) {
    *state = *state * UINT32_C(1664525) + UINT32_C(1013904223);
    return *state;
}
static uint8_t reference(uint32_t x) {
    for (unsigned j = 0; j < N; ++j)
        if (keys[j] == x)
            return tags[j];
    return 0;
}
static void populate(unsigned mode, uint32_t seed) {
    for (unsigned i = 0; i < QUERIES; ++i) {
        uint32_t r = next(&seed);
        uint32_t x = keys[r >> 27];
        if (mode != 0 && (mode == 2 || (i & 1))) {
            // Force a hit in an occupied hash slot for half of the misses.
            uint32_t base = x;
            do {
                x = next(&seed) >> 1;
            } while (x == prime || reference(x) ||
                     ((i & 2) && hash(x, 59649) != hash(base, 59649)));
        }
        inputs[i] = x;
        answers[i] = reference(x);
    }
}
static uint32_t build_table(unsigned arm, uint32_t *out) {
    uint32_t multiplier = arm == 0 ? UINT32_C(2654435761) : 59649;
    unsigned shift = arm == 3 ? 24 : 26;
    unsigned slots = arm == 3 ? 256 : SLOTS;
    if (arm >= 2) {
        for (multiplier = 1; multiplier != 0; multiplier += 2) {
            uint64_t used[4] = {0};
            unsigned j;
            for (j = 0; j < N; ++j) {
                unsigned h = address(keys[j], multiplier, shift);
                uint64_t bit = UINT64_C(1) << (h & 63);
                if (used[h >> 6] & bit)
                    break;
                used[h >> 6] |= bit;
            }
            if (j == N)
                break;
            if (multiplier == UINT32_MAX)
                return 0;
        }
    }
    for (unsigned i = 0; i < slots; ++i)
        out[i] = UINT32_MAX;
    for (unsigned j = 0; j < N; ++j) {
        unsigned i = address(keys[j], multiplier, shift);
        if (arm == 0) {
            while (out[i] != UINT32_MAX)
                i = (i + 1) & (SLOTS - 1);
        } else if (out[i] != UINT32_MAX)
            return 0;
        out[i] = 2 * keys[j] + tags[j] - 1;
    }
    return multiplier;
}

static void resolve(unsigned arm, const uint32_t *table, uint32_t multiplier,
                    const uint32_t *queries, unsigned count, uint8_t *result) {
    unsigned shift = arm == 3 ? 24 : 26;
    for (unsigned j = 0; j < count; ++j) {
        uint32_t x = queries[j];
        unsigned i = address(x, multiplier, shift);
        if (arm == 0) {
            while (table[i] != UINT32_MAX && (table[i] >> 1) != x)
                i = (i + 1) & (SLOTS - 1);
        }
        result[j] = unpack(table[i], x);
    }
}

static int charged_panel(uint32_t seed) {
    uint32_t out[256];
    const unsigned sizes[] = {32, 128, 512, 2048, 8192};
    populate(1, seed);
    puts("seed,count,round,arm,ns_per_build_and_batch");
    for (size_t n = 0; n < sizeof(sizes) / sizeof(sizes[0]); ++n) {
        unsigned count = sizes[n];
        unsigned repeats = 65536 / count;
        for (int round = -1; round < 12; ++round) {
            for (unsigned j = 0; j < 2; ++j) {
                unsigned arm = ((unsigned)round + seed + j) & 1 ? 3 : 0;
                uint64_t start = nanos();
                for (unsigned k = 0; k < repeats; ++k) {
                    uint32_t multiplier = build_table(arm, out);
                    if (!multiplier)
                        return 8;
                    resolve(arm, out, multiplier, inputs, count, outputs);
                    __asm__ volatile("" : : "r"(out), "r"(outputs) : "memory");
                }
                uint64_t elapsed = nanos() - start;
                if (memcmp(outputs, answers, count))
                    return 9;
                printf("%" PRIu32 ",%u,%d,%u,%.3f\n", seed, count, round, arm,
                       (double)elapsed / repeats);
            }
        }
    }
    return 0;
}

static int setup_panel(void) {
    uint32_t out[256];
    uint8_t result[N];
    puts("round,arm,repeats,ns_per_build_and_32_lookups");
    for (int round = -1; round < 12; ++round) {
        for (unsigned j = 0; j < 4; ++j) {
            unsigned arm = (unsigned)(round + 4 + (int)j) % 4;
            unsigned repeats = arm == 2 ? 4 : 2048;
            uint64_t start = nanos();
            for (unsigned k = 0; k < repeats; ++k) {
                uint32_t multiplier = build_table(arm, out);
                resolve(arm, out, multiplier, keys, N, result);
                if (!multiplier || (arm == 2 && multiplier != 59649) ||
                    (arm == 3 && multiplier != 49))
                    return 4;
                __asm__ volatile("" : : "r"(out), "r"(result) : "memory");
            }
            uint64_t elapsed = nanos() - start;
            for (unsigned i = 0; i < N; ++i)
                if (result[i] != tags[i])
                    return 5;
            printf("%d,%u,%u,%.3f\n", round, arm, repeats, (double)elapsed / repeats);
        }
    }
    return 0;
}
int main(int argc, char **argv) {
    uint32_t seed = argc > 1 ? (uint32_t)strtoul(argv[argc - 1], NULL, 10) : 1;
    for (unsigned i = 0; i < SLOTS; ++i)
        perfect[i] = linear[i] = UINT32_MAX;
    for (unsigned j = 0; j < N; ++j) {
        uint32_t x, bit;
        if (scanf("%" SCNu32 " %" SCNu32, &x, &bit) != 2 || x >= prime || bit > 1)
            return 1;
        uint32_t e = 2 * x + bit;
        keys[j] = x;
        tags[j] = bit + 1;
        sorted[j] = e;
        if (argc > 1 && argv[1][0] == '-')
            continue;
        unsigned h = hash(x, 59649);
        if (perfect[h] != UINT32_MAX)
            return 2;
        perfect[h] = e;
        h = hash(x, UINT32_C(2654435761));
        while (linear[h] != UINT32_MAX)
            h = (h + 1) & (SLOTS - 1);
        linear[h] = e;
    }
    if (argc == 2 && !strcmp(argv[1], "--setup"))
        return setup_panel();
    if (argc == 3 && !strcmp(argv[1], "--charged"))
        return charged_panel(seed);
    wider_multiplier = build_table(3, wider);
    if (!wider_multiplier)
        return 6;
    qsort(sorted, N, sizeof(*sorted), compare);
    for (unsigned i = 0; i < QUERIES; ++i) {
        uint32_t x = i < N       ? keys[i]
                     : i < 2 * N ? (keys[i - N] ^ 1u)
                                 : (i & 1 ? UINT32_MAX - i / 2 : prime + i / 2);
        inputs[i] = x;
        answers[i] = reference(x);
    }
    for (unsigned arm = 0; arm < 5; ++arm) {
        decode(arm);
        if (memcmp(outputs, answers, sizeof(outputs)))
            return 7;
    }
    puts("seed,mode,hits,round,arm,ns_per_coordinate");
    for (unsigned mode = 0; mode < 3; ++mode) {
        populate(mode, seed);
        unsigned hits = 0;
        for (unsigned i = 0; i < QUERIES; ++i)
            hits += answers[i] != 0;
        for (int round = -1; round < ROUNDS; ++round) {
            for (unsigned pos = 0; pos < 5; ++pos) {
                unsigned arm = ((seed & 1 ? pos : 4 - pos) + (unsigned)(round + 5) + seed) % 5;
                uint64_t start = nanos();
                for (unsigned k = 0; k < REPEATS; ++k) {
                    decode(arm);
                    __asm__ volatile("" : : "r"(outputs) : "memory");
                }
                uint64_t elapsed = nanos() - start;
                for (unsigned i = 0; i < QUERIES; ++i)
                    if (outputs[i] != answers[i])
                        return 3;
                printf("%" PRIu32 ",%u,%u,%d,%u,%.6f\n", seed, mode, hits, round, arm,
                       (double)elapsed / (QUERIES * REPEATS));
            }
        }
    }
}
