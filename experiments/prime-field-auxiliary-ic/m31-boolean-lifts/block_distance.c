// Lower bound by independent restrictions to blocks of 16 canonical inputs.
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include "lift_table.h"

static uint32_t histogram[65536];
static uint8_t distance[65536];

static void measure(unsigned degree) {
    uint16_t monomials[16];
    unsigned count = 0;
    for (unsigned m = 0; m < 16; ++m) {
        if ((unsigned)__builtin_popcount(m) > degree) continue;
        uint16_t truth = 0;
        for (unsigned i = 0; i < 16; ++i)
            if ((i & m) == m) truth |= 1u << i;
        monomials[count++] = truth;
    }
    memset(distance, 16, sizeof(distance));
    uint16_t truth = 0;
    distance[0] = 0;
    for (unsigned i = 1; i < (1u << count); ++i) {
        truth ^= monomials[__builtin_ctz(i)];
        distance[truth] = 0;
    }
    // Hamming distance transform, relaxing each coordinate in both directions.
    for (unsigned bit = 1; bit < 65536; bit <<= 1) {
        for (unsigned v = 0; v < 65536; ++v) {
            if (v & bit) continue;
            uint8_t lo = distance[v], hi = distance[v | bit];
            if (lo > hi + 1) distance[v] = hi + 1;
            if (hi > lo + 1) distance[v | bit] = lo + 1;
        }
    }
    // Independently recognize zero-distance words by their Boolean ANF.
    // The edge inequalities certify lower bounds for every accepted word.
    for (unsigned v = 0; v < 65536; ++v) {
        unsigned coeff = v;
        const unsigned masks[] = {0x5555, 0x3333, 0x0f0f, 0x00ff};
        for (unsigned j = 0; j < 4; ++j) coeff ^= (coeff & masks[j]) << (1u << j);
        unsigned actual_degree = 0;
        for (unsigned m = 1; m < 16; ++m)
            if (coeff & (1u << m)) {
                unsigned weight = __builtin_popcount(m);
                if (weight > actual_degree) actual_degree = weight;
            }
        if ((distance[v] == 0) != (actual_degree <= degree)) abort();
        unsigned best = 17;
        for (unsigned bit = 1; bit < 65536; bit <<= 1) {
            unsigned neighbor = distance[v ^ bit];
            if (neighbor < best) best = neighbor;
        }
        if (distance[v] && distance[v] != best + 1) abort();
    }
    uint64_t errors = 0;
    for (unsigned v = 0; v < 65536; ++v) errors += (uint64_t)histogram[v] * distance[v];
    printf("%u,%" PRIu64 "\n",degree,errors);
}

int main(void) {
    uint64_t *squares = square_table();
    if (!squares) return EXIT_FAILURE;
    uint64_t positives = 0;
    // Omit the last, incomplete block. Every counted error is on a field element.
    for (uint32_t x = 0; x < P - 15; x += 16) {
        unsigned truth = 0;
        for (unsigned i = 0; i < 16; ++i) truth |= lifts(x+i,squares) << i;
        ++histogram[truth];
        positives += __builtin_popcount(truth);
    }
    for (uint32_t x = P-15; x < P; ++x) positives += lifts(x,squares);
    free(squares);
    if (positives != 1073752646) return EXIT_FAILURE;
    puts("degree,minimum_errors_lower_bound");
    for (unsigned degree = 0; degree < 4; ++degree) measure(degree);
    return 0;
}
