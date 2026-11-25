#define _POSIX_C_SOURCE 200809L
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

enum { QUERIES = 65536, REPEATS = 128, ROUNDS = 16 };
struct query { uint32_t x, slot; };
static struct query inputs[QUERIES];
static uint8_t outputs[QUERIES];

static uint64_t now_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts)) abort();
    return (uint64_t)ts.tv_sec * 1000000000 + ts.tv_nsec;
}

static void direct(uint32_t bits) {
    for (size_t i = 0; i < QUERIES; ++i)
        outputs[i] = (bits >> inputs[i].slot) & 1;
}

static void corrected(uint32_t bits) {
    for (size_t i = 0; i < QUERIES; ++i) {
        unsigned bit = (bits >> (inputs[i].slot & 15)) & 1;
        outputs[i] = bit ^ __builtin_parity(inputs[i].x & UINT32_C(0x441080));
    }
}

int main(void) {
    uint32_t roots[32], direct_bits = 0, state = 1;
    for (unsigned i = 0; i < 32; ++i) {
        unsigned label;
        if (scanf("%" SCNu32 " %u", &roots[i], &label) != 2 || label > 1) return 1;
        direct_bits |= (uint32_t)label << i;
    }
    for (size_t i = 0; i < QUERIES; ++i) {
        state = state * UINT32_C(1664525) + UINT32_C(1013904223);
        unsigned slot = state >> 27;
        inputs[i] = (struct query){roots[slot], slot};
    }
    puts("round,arm,ns_per_label");
    for (int round = -1; round < ROUNDS; ++round) {
        for (unsigned order = 0; order < 2; ++order) {
            unsigned arm = ((unsigned)round & 1u) ^ order;
            uint64_t start = now_ns();
            for (unsigned k = 0; k < REPEATS; ++k) {
                if (arm) corrected(0x84c3); else direct(direct_bits);
                __asm__ volatile("" : : "r"(outputs) : "memory");
            }
            uint64_t elapsed = now_ns() - start;
            for (size_t i = 0; i < QUERIES; ++i)
                if (outputs[i] != ((direct_bits >> inputs[i].slot) & 1)) return 2;
            printf("%d,%u,%.6f\n", round, arm, (double)elapsed / (QUERIES * REPEATS));
        }
    }
}
