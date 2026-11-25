#pragma once
#include <stdint.h>
#include <stdlib.h>
#define P UINT32_C(2147483647)

static unsigned lifts(uint32_t x, const uint64_t *squares) {
    uint64_t xx = (uint64_t)x * x % P;
    uint32_t rhs = (xx * x + 2ULL * x + 14) % P;
    return (unsigned)((squares[rhs / 64] >> (rhs % 64)) & 1);
}

static uint64_t *square_table(void) {
    uint64_t *squares = calloc((size_t)P / 64 + 1, sizeof(*squares));
    if (!squares) return NULL;
    for (uint32_t y = 0; y <= P / 2; ++y) {
        uint32_t square = (uint64_t)y * y % P;
        squares[square / 64] |= UINT64_C(1) << (square % 64);
    }

    return squares;
}
